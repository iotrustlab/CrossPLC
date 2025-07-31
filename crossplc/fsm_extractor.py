"""
Finite State Machine (FSM) extraction from control flow IR.

This module implements Hybrid Finite State Abstraction (HFSA) by analyzing
control flow graphs to identify state machines encoded in industrial control logic.
"""

import re
import logging
import yaml
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path

from .models import (
    IRProject, IRController, IRProgram, IRRoutine, IRTag, 
    IRStateMachine, FSMState, FSMTransition, CrossControllerFSM
)

logger = logging.getLogger(__name__)


@dataclass
class FSMConfig:
    """Configuration for FSM extraction hints."""
    state_var: Optional[str] = None
    physical_vars: List[str] = field(default_factory=list)
    plant_dynamics: Dict[str, str] = field(default_factory=dict)
    explicit_states: List[str] = field(default_factory=list)
    transition_hints: Dict[str, List[str]] = field(default_factory=dict)
    expected_states: Dict[str, List[str]] = field(default_factory=dict)
    expected_transitions: Dict[str, List[Dict[str, str]]] = field(default_factory=dict)


class FSMExtractor:
    """Extracts finite state machines from control flow IR using structural analysis."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize FSM extractor with optional configuration.
        
        Args:
            config_path: Optional path to FSM configuration YAML file
        """
        self.config = self._load_config(config_path) if config_path else FSMConfig()
        
        # Common state variable candidates (but not hardcoded)
        self.state_var_candidates = [
            "mode", "state", "step", "status", "currentState", "newState", 
            "current_state", "new_state", "phase", "stage", "status"
        ]
        
        # Generic control flow patterns for FSM inference
        self.control_flow_patterns = {
            'if_guard': r'IF\s+([^=]+)\s*[=!<>]+\s*([^)]+)',
            'case_guard': r'CASE\s+(\w+)',
            'assignment': r'(\w+)\s*[:=]\s*([^;]+)',
            'function_call': r'(\w+)\s*\(\s*([^)]*)\s*\)',
            'loop_guard': r'WHILE\s+([^)]+)',
            'for_guard': r'FOR\s+([^)]+)'
        }
        
        # Generic input/output patterns (not domain-specific)
        self.io_patterns = {
            'input_check': r'(\w+)\s*[=!<>]+\s*([^;]+)',  # Any variable comparison
            'output_set': r'(\w+)\s*[:=]\s*(TRUE|FALSE|1|0|ON|OFF|OPEN|CLOSE)',  # Any output assignment
            'variable_assignment': r'(\w+)\s*[:=]\s*([^;]+)'  # Any variable assignment
        }
    
    def _load_config(self, config_path: Path) -> FSMConfig:
        """Load FSM configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Extract controller-specific config
            controller_config = config_data.get('controllers', {}).get('default', {})
            
            return FSMConfig(
                state_var=controller_config.get('state_var'),
                physical_vars=controller_config.get('physical_vars', []),
                plant_dynamics=controller_config.get('plant_dynamics', {}),
                explicit_states=controller_config.get('explicit_states', []),
                transition_hints=controller_config.get('transition_hints', {}),
                expected_states=controller_config.get('expected_states', {}),
                expected_transitions=controller_config.get('expected_transitions', {})
            )
        except Exception as e:
            logger.warning(f"Could not load FSM config from {config_path}: {e}")
            return FSMConfig()
    
    def extract_fsm_from_project(self, project: IRProject) -> Optional[IRStateMachine]:
        """
        Extract FSM from a project's control flow IR using structural analysis.
        
        Args:
            project: IRProject with control flow data
            
        Returns:
            IRStateMachine if found, None otherwise
        """
        # Get control flow data from project
        cfg_data = self._extract_control_flow_from_project(project)
        if not cfg_data:
            return None
        
        # Identify state variable using structural analysis
        state_var = self._identify_state_variable_structural(cfg_data)
        if not state_var:
            logger.info("No state variable identified in control flow")
            return None
        
        # Extract states and transitions
        states = self._extract_states_structural(cfg_data, state_var)
        transitions = self._extract_transitions_structural(cfg_data, state_var)
        
        if not states:
            logger.info("No states found in control flow")
            return None
        
        # Determine if FSM is implicit or explicit
        is_implicit = self._is_implicit_fsm(cfg_data, state_var)
        
        # Validate against expected behavior if config provided
        validation_result = self._validate_fsm_against_expected(states, transitions, state_var)
        
        return IRStateMachine(
            name=f"FSM_{state_var}",
            states=states,
            transitions=transitions,
            state_variable=state_var,
            description=f"Extracted FSM for state variable {state_var}",
            source_type=project.controller.source_type,
            is_implicit=is_implicit
        )
    
    def _extract_control_flow_from_project(self, project: IRProject) -> Dict[str, Any]:
        """Extract control flow data from project IR."""
        cfg_data = {
            'routines': [],
            'control_flow': [],
            'tags': [],
            'assignments': [],
            'guards': [],
            'inputs': [],
            'outputs': []
        }
        
        # Extract from programs and routines
        for program in project.programs:
            for routine in program.routines:
                cfg_data['routines'].append({
                    'name': routine.name,
                    'content': routine.content,
                    'type': routine.routine_type.value
                })
                
                # Extract assignments, guards, inputs, and outputs
                self._extract_control_flow_elements(routine.content, cfg_data)
        
        # Extract from controller tags
        for tag in project.controller.tags:
            cfg_data['tags'].append({
                'name': tag.name,
                'data_type': tag.data_type,
                'description': tag.description,
                'value': tag.value
            })
        
        return cfg_data
    
    def _extract_control_flow_elements(self, content: str, cfg_data: Dict[str, Any]):
        """Extract control flow elements from routine content."""
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Extract assignments
            assignment_match = re.search(r'(\w+)\s*[:=]\s*([^;]+)', line)
            if assignment_match:
                var_name = assignment_match.group(1)
                value = assignment_match.group(2).strip()
                cfg_data['assignments'].append({
                    'variable': var_name,
                    'value': value,
                    'line': line
                })
            
            # Extract guards (IF, CASE, WHILE conditions)
            for pattern_name, pattern in self.control_flow_patterns.items():
                matches = re.findall(pattern, line, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        cfg_data['guards'].append({
                            'pattern': pattern_name,
                            'variables': list(match),
                            'line': line
                        })
                    else:
                        cfg_data['guards'].append({
                            'pattern': pattern_name,
                            'variables': [match],
                            'line': line
                        })
            
            # Extract input checks (any variable comparison)
            for pattern_name, pattern in self.io_patterns.items():
                matches = re.findall(pattern, line, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        cfg_data['inputs'].append({
                            'type': pattern_name,
                            'variable': match[0],
                            'value': match[1],
                            'line': line
                        })
            
            # Extract output assignments
            output_match = re.search(r'(\w+)\s*[:=]\s*(TRUE|FALSE|1|0|ON|OFF|OPEN|CLOSE)', line, re.IGNORECASE)
            if output_match:
                cfg_data['outputs'].append({
                    'variable': output_match.group(1),
                    'value': output_match.group(2),
                    'line': line
                })
    
    def _identify_state_variable_structural(self, cfg_data: Dict[str, Any]) -> Optional[str]:
        """Identify state variable using structural analysis."""
        content = self._extract_content_from_cfg(cfg_data)
        
        # Use config hint if provided
        if self.config.state_var:
            if self._is_state_variable_structural(cfg_data, self.config.state_var):
                return self.config.state_var
        
        # Analyze control flow structure to find state variables
        state_candidates = self._find_state_variable_candidates(cfg_data)
        
        # Score candidates based on structural evidence
        scored_candidates = []
        for candidate in state_candidates:
            score = self._score_state_variable_candidate(cfg_data, candidate)
            if score > 0:
                scored_candidates.append((candidate, score))
        
        # Return the highest scoring candidate
        if scored_candidates:
            scored_candidates.sort(key=lambda x: x[1], reverse=True)
            return scored_candidates[0][0]
        
        return None
    
    def _find_state_variable_candidates(self, cfg_data: Dict[str, Any]) -> Set[str]:
        """Find potential state variables using structural analysis."""
        candidates = set()
        
        # Look for variables used in guards
        for guard in cfg_data['guards']:
            for var in guard['variables']:
                if self._is_valid_variable_name(var):
                    candidates.add(var)
        
        # Look for variables that are assigned values
        for assignment in cfg_data['assignments']:
            var = assignment['variable']
            if self._is_valid_variable_name(var):
                candidates.add(var)
        
        # Look for variables that control outputs
        for output in cfg_data['outputs']:
            var = output['variable']
            if self._is_valid_variable_name(var):
                candidates.add(var)
        
        return candidates
    
    def _is_valid_variable_name(self, var: str) -> bool:
        """Check if a variable name is valid (not a literal, number, etc.)."""
        # Remove quotes and clean up
        var = var.strip().strip('"\'')
        
        # Must be alphanumeric and start with letter
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', var):
            return False
        
        # Must not be a common literal
        literals = ['TRUE', 'FALSE', 'ON', 'OFF', 'OPEN', 'CLOSE', 'IDLE', 'FAULT']
        if var.upper() in literals:
            return False
        
        return True
    
    def _score_state_variable_candidate(self, cfg_data: Dict[str, Any], candidate: str) -> int:
        """Score a state variable candidate based on structural evidence."""
        score = 0
        
        # Variables used in multiple guards get higher score
        guard_count = sum(1 for guard in cfg_data['guards'] if candidate in guard['variables'])
        score += guard_count * 2
        
        # Variables that are assigned values get score
        assignment_count = sum(1 for assignment in cfg_data['assignments'] if assignment['variable'] == candidate)
        score += assignment_count
        
        # Variables that control outputs get higher score
        output_count = sum(1 for output in cfg_data['outputs'] if output['variable'] == candidate)
        score += output_count * 3
        
        # Variables with state-like values get higher score
        state_like_values = ['idle', 'fault', 'running', 'stopped', 'error', 'init', 
                           'fill', 'drain', 'heat', 'cool', 'open', 'close', 'on', 'off']
        
        for assignment in cfg_data['assignments']:
            if assignment['variable'] == candidate:
                value = assignment['value'].lower().strip('"\'')
                if value in state_like_values:
                    score += 2
        
        return score
    
    def _is_state_variable_structural(self, cfg_data: Dict[str, Any], var_name: str) -> bool:
        """Check if a variable is likely a state variable using structural analysis."""
        score = self._score_state_variable_candidate(cfg_data, var_name)
        return score >= 3  # Require at least 3 points of evidence
    
    def _extract_content_from_cfg(self, cfg_data: Dict[str, Any]) -> str:
        """Extract text content from control flow graph."""
        content_parts = []
        
        if 'routines' in cfg_data:
            for routine in cfg_data['routines']:
                if 'content' in routine:
                    content_parts.append(routine['content'])
        
        if 'control_flow' in cfg_data:
            for flow in cfg_data['control_flow']:
                if 'content' in flow:
                    content_parts.append(flow['content'])
        
        return '\n'.join(content_parts)
    
    def _extract_states_structural(self, cfg_data: Dict[str, Any], state_var: str) -> List[FSMState]:
        """Extract states using structural analysis."""
        states = []
        state_values = set()
        
        # Extract states from assignments
        for assignment in cfg_data['assignments']:
            if assignment['variable'] == state_var:
                value = assignment['value'].strip().strip('"\'')
                if self._is_valid_state_value(value):
                    state_values.add(value)
        
        # Extract states from guards
        for guard in cfg_data['guards']:
            if state_var in guard['variables']:
                # Look for state values in guard conditions
                for var in guard['variables']:
                    if var != state_var and self._is_valid_state_value(var):
                        state_values.add(var)
        
        # Add explicit states from config
        if self.config.explicit_states:
            state_values.update(self.config.explicit_states)
        
        # Create FSM states
        for state_name in state_values:
            state = FSMState(
                name=state_name,
                description=f"State: {state_name}",
                is_initial=self._is_initial_state(state_name),
                is_final=self._is_final_state(state_name)
            )
            states.append(state)
        
        return states
    
    def _is_valid_state_value(self, value: str) -> bool:
        """Check if a value looks like a state name."""
        value = value.lower().strip('"\'')
        
        # Must be alphanumeric
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            return False
        
        # Must not be a number only
        if value.isdigit():
            return False
        
        return True
    
    def _is_initial_state(self, state_name: str) -> bool:
        """Check if a state is likely initial."""
        state_lower = state_name.lower()
        return state_lower in ['idle', 'init', 'ready', 'false', '0', 'off']
    
    def _is_final_state(self, state_name: str) -> bool:
        """Check if a state is likely final."""
        state_lower = state_name.lower()
        return state_lower in ['fault', 'error', 'stopped', 'true', '1', 'on']
    
    def _extract_transitions_structural(self, cfg_data: Dict[str, Any], state_var: str) -> List[FSMTransition]:
        """Extract transitions using structural analysis."""
        transitions = []
        
        # Look for IF statements that assign to state variable
        for guard in cfg_data['guards']:
            if guard['pattern'] == 'if_guard':
                # Find corresponding assignment
                for assignment in cfg_data['assignments']:
                    if assignment['variable'] == state_var:
                        # This could be a transition
                        to_state = assignment['value'].strip().strip('"\'')
                        if self._is_valid_state_value(to_state):
                            transition = FSMTransition(
                                from_state="UNKNOWN",  # Will be inferred
                                to_state=to_state,
                                guard=guard['line'],
                                actions=[assignment['line']]
                            )
                            transitions.append(transition)
        
        # Infer from_state based on context
        self._infer_transition_sources(transitions, cfg_data)
        
        return transitions
    
    def _infer_transition_sources(self, transitions: List[FSMTransition], cfg_data: Dict[str, Any]):
        """Infer the source states for transitions based on context."""
        # This is a simplified approach - in practice, you'd need more sophisticated
        # control flow analysis to determine the exact source states
        for transition in transitions:
            if transition.from_state == "UNKNOWN":
                # Try to infer from context - this is a placeholder
                transition.from_state = "CURRENT_STATE"
    
    def _is_implicit_fsm(self, cfg_data: Dict[str, Any], state_var: str) -> bool:
        """Determine if FSM is implicit (boolean flags) or explicit (state variables)."""
        # Check for boolean patterns in assignments
        for assignment in cfg_data['assignments']:
            if assignment['variable'] == state_var:
                value = assignment['value'].lower().strip('"\'')
                if value in ['true', 'false', '1', '0', 'on', 'off']:
                    return True
        
        return False
    
    def _validate_fsm_against_expected(self, states: List[FSMState], transitions: List[FSMTransition], state_var: str) -> Dict[str, Any]:
        """Validate extracted FSM against expected behavior from config."""
        validation_result = {
            'valid': True,
            'missing_states': [],
            'unexpected_states': [],
            'missing_transitions': [],
            'unexpected_transitions': []
        }
        
        if not self.config.expected_states:
            return validation_result
        
        # Check expected states
        expected_states = self.config.expected_states.get(state_var, [])
        actual_states = [state.name for state in states]
        
        for expected_state in expected_states:
            if expected_state not in actual_states:
                validation_result['missing_states'].append(expected_state)
                validation_result['valid'] = False
        
        for actual_state in actual_states:
            if actual_state not in expected_states:
                validation_result['unexpected_states'].append(actual_state)
        
        return validation_result


class CrossControllerFSMExtractor:
    """Extracts composite FSMs across multiple controllers."""
    
    def __init__(self):
        self.fsm_extractor = FSMExtractor()
    
    def extract_cross_controller_fsm(self, projects: List[IRProject]) -> CrossControllerFSM:
        """Extract composite FSM from multiple controllers."""
        controller_fsms = []
        shared_tags = set()
        
        # Extract FSMs from each controller
        for project in projects:
            if project.controller:
                fsm = self.fsm_extractor.extract_fsm_from_project(project)
                if fsm:
                    project.controller.fsm = fsm
                    controller_fsms.append(fsm)
                
                # Collect shared tags
                for tag in project.controller.tags:
                    shared_tags.add(tag.name)
        
        # Find linked transitions based on shared tags
        linked_transitions = self._find_linked_transitions(controller_fsms, shared_tags)
        
        return CrossControllerFSM(
            name="Composite_FSM",
            controllers=[project.controller.name for project in projects if project.controller],
            linked_transitions=linked_transitions,
            shared_tags=list(shared_tags),
            description="Composite FSM across multiple controllers"
        )
    
    def _find_linked_transitions(self, fsms: List[IRStateMachine], 
                                 shared_tags: Set[str]) -> List[Dict[str, Any]]:
        """Find transitions that are linked across controllers via shared tags."""
        linked = []
        
        for i, fsm1 in enumerate(fsms):
            for j, fsm2 in enumerate(fsms):
                if i != j:
                    for transition1 in fsm1.transitions:
                        for transition2 in fsm2.transitions:
                            if self._transitions_are_linked(transition1, transition2, shared_tags):
                                linked.append({
                                    "controller1": fsm1.name,
                                    "controller2": fsm2.name,
                                    "transition1": transition1.to_state,
                                    "transition2": transition2.to_state,
                                    "shared_tags": list(shared_tags)
                                })
        
        return linked
    
    def _transitions_are_linked(self, t1: FSMTransition, t2: FSMTransition, 
                                 shared_tags: Set[str]) -> bool:
        """Check if two transitions are linked via shared tags."""
        # Simple heuristic: check if transitions use shared tags
        t1_tags = self._extract_tags_from_transition(t1)
        t2_tags = self._extract_tags_from_transition(t2)
        
        return bool(t1_tags & t2_tags & shared_tags)
    
    def _extract_tags_from_transition(self, transition: FSMTransition) -> Set[str]:
        """Extract tag names from a transition."""
        tags = set()
        
        if transition.guard:
            # Extract tag names from guard condition
            tag_pattern = r'\b(\w+)\b'
            matches = re.findall(tag_pattern, transition.guard)
            tags.update(matches)
        
        for action in transition.actions:
            # Extract tag names from actions
            tag_pattern = r'\b(\w+)\b'
            matches = re.findall(tag_pattern, action)
            tags.update(matches)
        
        return tags 