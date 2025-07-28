"""
Export Intermediate Representation (IR) components to structured JSON files.
This module supports exporting selected components for downstream semantic mapping.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
from datetime import datetime
from enum import Enum

from .models import (
    IRProject, IRController, IRProgram, IRRoutine, IRTag, IRDataType,
    IRFunctionBlock, TagScope, RoutineType
)

logger = logging.getLogger(__name__)


class ExportComponent(Enum):
    """Components that can be exported."""
    TAGS = "tags"
    CONTROL_FLOW = "control_flow"
    DATA_TYPES = "data_types"
    FUNCTION_BLOCKS = "function_blocks"
    INTERACTIONS = "interactions"
    ROUTINES = "routines"
    PROGRAMS = "programs"
    SEMANTIC = "semantic"  # New semantic analysis component
    CFG = "cfg" # New CFG analysis component


class ControlFlowAnalyzer:
    """Analyzes control flow in routines and programs."""
    
    def __init__(self):
        self.branch_keywords = {
            'IF', 'THEN', 'ELSE', 'ELSIF', 'END_IF',
            'CASE', 'OF', 'END_CASE',
            'FOR', 'TO', 'DO', 'END_FOR',
            'WHILE', 'END_WHILE',
            'REPEAT', 'UNTIL', 'END_REPEAT'
        }
        
        self.action_keywords = {
            ':=', '=', 'SET', 'RESET', 'TON', 'TOF', 'CTU', 'CTD'
        }
    
    def analyze_routine_control_flow(self, routine: IRRoutine) -> Dict[str, Any]:
        """Analyze control flow in a single routine."""
        if routine.routine_type == RoutineType.ST:
            return self._analyze_st_control_flow(routine.content)
        elif routine.routine_type == RoutineType.RLL:
            return self._analyze_ladder_control_flow(routine.content)
        elif routine.routine_type == RoutineType.FBD:
            return self._analyze_fbd_control_flow(routine.content)
        else:
            return {"type": "unknown", "content": routine.content}
    
    def _analyze_st_control_flow(self, content: str) -> Dict[str, Any]:
        """Analyze Structured Text control flow."""
        lines = content.split('\n')
        control_flow = []
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('//'):
                continue
                
            # Detect IF-THEN-ELSE structures
            if line.upper().startswith('IF '):
                condition = line[3:].strip()
                if condition.endswith('THEN'):
                    condition = condition[:-4].strip()
                control_flow.append({
                    "type": "branch",
                    "condition": condition,
                    "actions": []
                })
            elif line.upper().startswith('ELSIF '):
                condition = line[6:].strip()
                if condition.endswith('THEN'):
                    condition = condition[:-4].strip()
                control_flow.append({
                    "type": "branch",
                    "condition": condition,
                    "actions": []
                })
            elif line.upper() == 'ELSE':
                control_flow.append({
                    "type": "branch",
                    "condition": "else",
                    "actions": []
                })
            elif line.upper() in ['END_IF', 'END_CASE', 'END_FOR', 'END_WHILE', 'END_REPEAT']:
                continue
            elif ':' in line and any(keyword in line.upper() for keyword in self.action_keywords):
                # This is likely an assignment or action
                if control_flow:
                    control_flow[-1]["actions"].append(line.strip())
                else:
                    control_flow.append({
                        "type": "action",
                        "actions": [line.strip()]
                    })
        
        return {
            "type": "structured_text",
            "control_flow": control_flow
        }
    
    def _analyze_ladder_control_flow(self, content: str) -> Dict[str, Any]:
        """Analyze Ladder Logic control flow."""
        # Simplified ladder analysis - extract rung conditions and outputs
        lines = content.split('\n')
        control_flow = []
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('//'):
                continue
            
            # Look for rung patterns (simplified)
            if '|' in line and '--' in line:
                # This looks like a ladder rung
                parts = line.split('--')
                if len(parts) >= 2:
                    condition = parts[0].replace('|', '').strip()
                    action = parts[1].replace('|', '').strip()
                    control_flow.append({
                        "type": "rung",
                        "condition": condition,
                        "actions": [action] if action else []
                    })
        
        return {
            "type": "ladder_logic",
            "control_flow": control_flow
        }
    
    def _analyze_fbd_control_flow(self, content: str) -> Dict[str, Any]:
        """Analyze Function Block Diagram control flow."""
        # Enhanced FBD analysis - parse function blocks and connections
        control_flow = []
        
        try:
            # Parse FBD content as XML
            import xml.etree.ElementTree as ET
            from io import StringIO
            
            # Wrap content in a root element if it's not already XML
            if not content.strip().startswith('<'):
                return {
                    "type": "function_block_diagram",
                    "content": content,
                    "note": "FBD content not in XML format"
                }
            
            # Parse the FBD XML content
            root = ET.fromstring(f"<root>{content}</root>")
            
            # Extract function blocks
            function_blocks = {}
            for fb_elem in root.findall('.//AddOnInstruction'):
                fb_id = fb_elem.get('ID')
                fb_name = fb_elem.get('Name', 'Unknown')
                fb_operand = fb_elem.get('Operand', 'Unknown')
                visible_pins = fb_elem.get('VisiblePins', '').split()
                
                function_blocks[fb_id] = {
                    "name": fb_name,
                    "operand": fb_operand,
                    "visible_pins": visible_pins
                }
            
            # Extract connections/wires
            connections = []
            for wire_elem in root.findall('.//Wire'):
                from_id = wire_elem.get('FromID')
                to_id = wire_elem.get('ToID')
                to_param = wire_elem.get('ToParam')
                
                connections.append({
                    "from_id": from_id,
                    "to_id": to_id,
                    "to_param": to_param
                })
            
            # Extract input references
            input_refs = {}
            for iref_elem in root.findall('.//IRef'):
                ref_id = iref_elem.get('ID')
                operand = iref_elem.get('Operand', 'Unknown')
                
                input_refs[ref_id] = operand
            
            # Build control flow from connections
            for connection in connections:
                from_id = connection['from_id']
                to_id = connection['to_id']
                to_param = connection['to_param']
                
                # Get source and destination info
                source = input_refs.get(from_id, f"Input_{from_id}")
                dest_fb = function_blocks.get(to_id, {})
                dest_name = dest_fb.get('name', f"Block_{to_id}")
                dest_operand = dest_fb.get('operand', 'Unknown')
                
                control_flow.append({
                    "type": "fbd_connection",
                    "source": source,
                    "destination": {
                        "block": dest_name,
                        "instance": dest_operand,
                        "parameter": to_param
                    },
                    "connection_type": "data_flow"
                })
            
            # Group by function blocks for better structure
            fb_groups = {}
            for fb_id, fb_info in function_blocks.items():
                fb_connections = [conn for conn in connections if conn['to_id'] == fb_id]
                fb_inputs = {}
                
                for conn in fb_connections:
                    param = conn['to_param']
                    source = input_refs.get(conn['from_id'], f"Input_{conn['from_id']}")
                    fb_inputs[param] = source
                
                fb_groups[fb_info['operand']] = {
                    "block_type": fb_info['name'],
                    "inputs": fb_inputs,
                    "visible_pins": fb_info['visible_pins']
                }
            
            return {
                "type": "function_block_diagram",
                "control_flow": control_flow,
                "function_blocks": fb_groups,
                "total_blocks": len(function_blocks),
                "total_connections": len(connections)
            }
            
        except Exception as e:
            return {
                "type": "function_block_diagram",
                "content": content,
                "error": f"FBD parsing error: {str(e)}",
                "note": "FBD control flow analysis requires detailed parsing of block connections"
            }


class InteractionAnalyzer:
    """Analyzes cross-program and cross-controller interactions."""
    
    def __init__(self):
        self.tag_references: Dict[str, Set[str]] = {}
        self.program_tags: Dict[str, Set[str]] = {}
    
    def analyze_interactions(self, ir_project: IRProject) -> Dict[str, Any]:
        """Analyze interactions between programs and controllers."""
        # Build tag reference maps
        self._build_tag_maps(ir_project)
        
        interactions = []
        
        # Analyze cross-program interactions
        for program in ir_project.programs:
            program_tags = self.program_tags.get(program.name, set())
            
            for other_program in ir_project.programs:
                if program.name == other_program.name:
                    continue
                    
                other_tags = self.program_tags.get(other_program.name, set())
                shared_tags = program_tags.intersection(other_tags)
                
                if shared_tags:
                    interactions.append({
                        "source": f"{ir_project.controller.name}.{program.name}",
                        "target": f"{ir_project.controller.name}.{other_program.name}",
                        "via": list(shared_tags),
                        "type": "cross_program"
                    })
        
        # Analyze controller-level tag usage
        controller_tags = {tag.name for tag in ir_project.controller.tags}
        for program in ir_project.programs:
            program_tags = self.program_tags.get(program.name, set())
            used_controller_tags = program_tags.intersection(controller_tags)
            
            if used_controller_tags:
                interactions.append({
                    "source": f"{ir_project.controller.name}.{program.name}",
                    "target": f"{ir_project.controller.name}",
                    "via": list(used_controller_tags),
                    "type": "program_to_controller"
                })
        
        return {
            "interactions": interactions,
            "summary": {
                "total_interactions": len(interactions),
                "cross_program_interactions": len([i for i in interactions if i["type"] == "cross_program"]),
                "program_controller_interactions": len([i for i in interactions if i["type"] == "program_to_controller"])
            }
        }
    
    def _build_tag_maps(self, ir_project: IRProject):
        """Build maps of tag references and program ownership."""
        # Initialize maps
        self.tag_references.clear()
        self.program_tags.clear()
        
        # Map controller tags
        for tag in ir_project.controller.tags:
            self.tag_references[tag.name] = set()
        
        # Map program tags and analyze references
        for program in ir_project.programs:
            program_tag_names = set()
            
            # Add program's own tags
            for tag in program.tags:
                program_tag_names.add(tag.name)
                self.tag_references[tag.name] = set()
            
            # Add local variables
            for tag in program.local_variables:
                program_tag_names.add(tag.name)
                self.tag_references[tag.name] = set()
            
            # Analyze routine content for tag references
            for routine in program.routines:
                self._analyze_routine_references(routine, program.name)
            
            self.program_tags[program.name] = program_tag_names
    
    def _analyze_routine_references(self, routine: IRRoutine, program_name: str):
        """Analyze tag references in routine content."""
        content = routine.content.lower()
        
        # Simple pattern matching for tag references
        # This is a simplified approach - in practice, you'd want proper parsing
        for tag_name in self.tag_references.keys():
            if tag_name.lower() in content:
                self.tag_references[tag_name].add(program_name)


class SemanticAnalyzer:
    """Analyze semantic aspects of IR including tag usage and dependencies."""
    
    def __init__(self):
        # Known control flow patterns for annotations
        self.control_patterns = {
            "shutdown_trigger": [
                "HMI_PLANT.STOP", "HMI_PLANT.SHUTDOWN", "EMERGENCY_STOP"
            ],
            "start_trigger": [
                "HMI_PLANT.START", "HMI_PLANT.RUN", "AUTO_START"
            ],
            "alarm_condition": [
                "HMI_ALARM", "FAULT", "TRIP", "HIGH_LEVEL", "LOW_LEVEL"
            ],
            "permissive_check": [
                "PERMISSIVE", "SAFE", "READY", "ENABLED"
            ]
        }
    
    def analyze_tag_usage(self, ir_project: IRProject) -> Dict[str, Any]:
        """Analyze tag usage patterns across routines."""
        tag_summary = {}
        
        for program in ir_project.programs:
            for routine in program.routines:
                routine_name = routine.name
                inputs = set()
                outputs = set()
                internal = set()
                
                # Analyze ST content for tag usage
                if routine.content:
                    usage = self._analyze_st_tag_usage(routine.content)
                    inputs.update(usage['inputs'])
                    outputs.update(usage['outputs'])
                    internal.update(usage['internal'])
                
                # Analyze control flow for additional tag usage
                if hasattr(routine, 'control_flow') and routine.control_flow:
                    cf_usage = self._analyze_control_flow_tag_usage(routine.control_flow)
                    inputs.update(cf_usage['inputs'])
                    outputs.update(cf_usage['outputs'])
                
                tag_summary[routine_name] = {
                    "inputs": list(inputs),
                    "outputs": list(outputs),
                    "internal": list(internal)
                }
        
        return tag_summary
    
    def _analyze_st_tag_usage(self, content: str) -> Dict[str, Set[str]]:
        """Analyze ST content for tag usage patterns."""
        inputs = set()
        outputs = set()
        internal = set()
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('//'):
                continue
            
            # Look for assignments (LHS = RHS)
            if ':=' in line:
                parts = line.split(':=')
                if len(parts) == 2:
                    lhs = parts[0].strip()
                    rhs = parts[1].strip().rstrip(';')
                    
                    # LHS is output
                    tag = self._extract_tag_from_expression(lhs)
                    if tag:
                        outputs.add(tag)
                    
                    # RHS is input
                    rhs_tags = self._extract_tags_from_expression(rhs)
                    inputs.update(rhs_tags)
            
            # Look for conditions in IF statements
            elif line.upper().startswith('IF '):
                condition = line[3:].strip()
                if condition.endswith('THEN'):
                    condition = condition[:-4].strip()
                
                condition_tags = self._extract_tags_from_expression(condition)
                inputs.update(condition_tags)
        
        # Find internal tags (used as both input and output)
        internal = inputs.intersection(outputs)
        inputs = inputs - internal
        outputs = outputs - internal
        
        return {
            "inputs": inputs,
            "outputs": outputs,
            "internal": internal
        }
    
    def _analyze_control_flow_tag_usage(self, control_flow: Dict[str, Any]) -> Dict[str, Set[str]]:
        """Analyze control flow structure for tag usage."""
        inputs = set()
        outputs = set()
        
        if control_flow.get('type') == 'structured_text':
            for flow_item in control_flow.get('control_flow', []):
                if flow_item.get('type') == 'branch':
                    # Condition tags are inputs
                    condition = flow_item.get('condition', '')
                    if condition and condition != 'else':
                        condition_tags = self._extract_tags_from_expression(condition)
                        inputs.update(condition_tags)
                    
                    # Action tags are outputs
                    for action in flow_item.get('actions', []):
                        action_tags = self._extract_tags_from_expression(action)
                        outputs.update(action_tags)
        
        return {
            "inputs": inputs,
            "outputs": outputs,
            "internal": set()
        }
    
    def _extract_tag_from_expression(self, expr: str) -> Optional[str]:
        """Extract a single tag from an expression."""
        # Simple tag extraction - look for word patterns
        import re
        # Match patterns like: TagName, TagName.Field, TagName[Index], DI_TAG, AI_TAG, etc.
        tag_pattern = r'\b[A-Z][A-Z0-9_]*(\.[A-Z][A-Z0-9_]*)*(\[[^\]]*\])?\b'
        matches = re.findall(tag_pattern, expr)
        if matches:
            return matches[0][0]  # Return first match
        return None
    
    def _extract_tags_from_expression(self, expr: str) -> Set[str]:
        """Extract all tags from an expression."""
        import re
        tags = set()
        
        # Match patterns like: TagName, TagName.Field, TagName[Index], DI_TAG, AI_TAG, etc.
        tag_pattern = r'\b[A-Z][A-Z0-9_]*(\.[A-Z][A-Z0-9_]*)*(\[[^\]]*\])?\b'
        matches = re.findall(tag_pattern, expr)
        
        for match in matches:
            if match[0]:  # First group contains the tag name
                # Clean up the tag name (remove array indices, etc.)
                tag_name = match[0]
                # Remove array indices if present
                if '[' in tag_name:
                    tag_name = tag_name.split('[')[0]
                tags.add(tag_name)
        
        return tags
    
    def analyze_interdependencies(self, ir_project: IRProject) -> List[Dict[str, str]]:
        """Analyze inter-routine data dependencies."""
        dependencies = []
        
        # Build tag usage map
        tag_writers = {}  # tag -> list of routines that write to it
        tag_readers = {}  # tag -> list of routines that read from it
        
        for program in ir_project.programs:
            for routine in program.routines:
                routine_name = routine.name
                
                # Get tag usage for this routine
                usage = self._analyze_st_tag_usage(routine.content) if routine.content else {"inputs": set(), "outputs": set(), "internal": set()}
                
                # Track writers
                for tag in usage['outputs']:
                    if tag not in tag_writers:
                        tag_writers[tag] = []
                    tag_writers[tag].append(routine_name)
                
                # Track readers
                for tag in usage['inputs']:
                    if tag not in tag_readers:
                        tag_readers[tag] = []
                    tag_readers[tag].append(routine_name)
        
        # Find dependencies
        for tag in set(tag_writers.keys()) & set(tag_readers.keys()):
            writers = tag_writers[tag]
            readers = tag_readers[tag]
            
            for writer in writers:
                for reader in readers:
                    if writer != reader:  # Don't include self-dependencies
                        dependencies.append({
                            "writer": writer,
                            "reader": reader,
                            "tag": tag
                        })
        
        return dependencies
    
    def analyze_control_flow_annotations(self, ir_project: IRProject) -> Dict[str, List[Dict[str, str]]]:
        """Analyze control flow for semantic annotations."""
        annotations = {}
        
        for program in ir_project.programs:
            for routine in program.routines:
                routine_name = routine.name
                routine_annotations = []
                
                if routine.content:
                    # Analyze ST content for patterns
                    st_annotations = self._analyze_st_annotations(routine.content)
                    routine_annotations.extend(st_annotations)
                
                if routine_annotations:
                    annotations[routine_name] = routine_annotations
        
        return annotations
    
    def _analyze_st_annotations(self, content: str) -> List[Dict[str, str]]:
        """Analyze ST content for control flow annotations."""
        annotations = []
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('//'):
                continue
            
            # Check for control patterns
            for event_type, patterns in self.control_patterns.items():
                for pattern in patterns:
                    if pattern.lower() in line.lower():
                        annotations.append({
                            "condition": line,
                            "event": event_type
                        })
                        break
        
        return annotations


class CFGAnalyzer:
    """Analyze control flow graphs and data flow for ST routines."""
    
    def __init__(self):
        self.block_counter = 0
    
    def analyze_cfg(self, ir_project: IRProject) -> Dict[str, Any]:
        """Generate control flow graphs for all routines."""
        cfg_data = {}
        
        for program in ir_project.programs:
            for routine in program.routines:
                if routine.content:
                    routine_cfg = self._build_routine_cfg(routine)
                    if routine_cfg:
                        cfg_data[routine.name] = routine_cfg
        
        return cfg_data
    
    def _build_routine_cfg(self, routine: IRRoutine) -> Dict[str, Any]:
        """Build control flow graph for a single routine."""
        if not routine.content:
            return None
        
        # Parse ST content into basic blocks
        blocks = self._parse_st_into_blocks(routine.content)
        
        # Build control flow graph
        cfg = {
            "blocks": blocks,
            "entry": "entry" if blocks else None
        }
        
        return cfg
    
    def _parse_st_into_blocks(self, content: str) -> List[Dict[str, Any]]:
        """Parse ST content into basic blocks with control flow."""
        blocks = []
        lines = content.split('\n')
        
        # Create entry block
        entry_block = {
            "block_id": "entry",
            "instructions": [],
            "successors": []
        }
        
        current_block = entry_block
        block_stack = []  # For nested control structures
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('//'):
                continue
            
            # Handle different ST constructs
            if self._is_control_structure(line):
                # End current block and start new control block
                if current_block["instructions"]:
                    blocks.append(current_block)
                
                control_block = self._create_control_block(line)
                blocks.append(control_block)
                
                # Update successors
                if blocks:
                    prev_block = blocks[-2] if len(blocks) > 1 else entry_block
                    prev_block["successors"].append(control_block["block_id"])
                
                current_block = control_block
                block_stack.append(control_block)
                
            elif self._is_end_structure(line):
                # End control structure
                if block_stack:
                    control_block = block_stack.pop()
                    # Add successor to next block
                    if blocks:
                        control_block["successors"].append(f"b{len(blocks) + 1}")
                
                # Create next block
                next_block = {
                    "block_id": f"b{len(blocks) + 1}",
                    "instructions": [],
                    "successors": []
                }
                blocks.append(next_block)
                current_block = next_block
                
            else:
                # Regular instruction
                current_block["instructions"].append(line)
        
        # Add final block if it has instructions
        if current_block["instructions"]:
            blocks.append(current_block)
        
        # Add data flow analysis to each block
        for block in blocks:
            block.update(self._analyze_block_data_flow(block))
        
        return blocks
    
    def _is_control_structure(self, line: str) -> bool:
        """Check if line starts a control structure."""
        line_upper = line.upper()
        return (line_upper.startswith('IF ') or 
                line_upper.startswith('FOR ') or 
                line_upper.startswith('WHILE ') or
                line_upper.startswith('CASE '))
    
    def _is_end_structure(self, line: str) -> bool:
        """Check if line ends a control structure."""
        line_upper = line.upper()
        return (line_upper == 'END_IF' or 
                line_upper == 'END_FOR' or 
                line_upper == 'END_WHILE' or
                line_upper == 'END_CASE')
    
    def _create_control_block(self, line: str) -> Dict[str, Any]:
        """Create a control flow block."""
        self.block_counter += 1
        block_id = f"b{self.block_counter}"
        
        if line.upper().startswith('IF '):
            # Extract condition
            condition = line[3:].strip()
            if condition.endswith('THEN'):
                condition = condition[:-4].strip()
            
            return {
                "block_id": block_id,
                "type": "branch",
                "condition": condition,
                "true_successor": f"b{self.block_counter + 1}",
                "false_successor": f"b{self.block_counter + 2}",
                "instructions": [],
                "successors": []
            }
        else:
            # Other control structures
            return {
                "block_id": block_id,
                "type": "control",
                "condition": line,
                "instructions": [],
                "successors": []
            }
    
    def _analyze_block_data_flow(self, block: Dict[str, Any]) -> Dict[str, List[str]]:
        """Analyze data flow (defs/uses) for a block."""
        defs = set()
        uses = set()
        
        for instruction in block.get("instructions", []):
            # Analyze assignment (defs)
            if ':=' in instruction:
                parts = instruction.split(':=')
                if len(parts) == 2:
                    lhs = parts[0].strip()
                    rhs = parts[1].strip().rstrip(';')
                    
                    # LHS is a def
                    tag = self._extract_tag_from_expression(lhs)
                    if tag:
                        defs.add(tag)
                    
                    # RHS tags are uses
                    rhs_tags = self._extract_tags_from_expression(rhs)
                    uses.update(rhs_tags)
            
            # Analyze condition (uses)
            condition = block.get("condition", "")
            if condition:
                condition_tags = self._extract_tags_from_expression(condition)
                uses.update(condition_tags)
        
        return {
            "defs": list(defs),
            "uses": list(uses)
        }
    
    def _extract_tag_from_expression(self, expr: str) -> Optional[str]:
        """Extract a single tag from an expression."""
        import re
        # Match patterns like: TagName, TagName.Field, TagName[Index]
        tag_pattern = r'\b[A-Z][A-Z0-9_]*(\.[A-Z][A-Z0-9_]*)*(\[[^\]]*\])?\b'
        matches = re.findall(tag_pattern, expr)
        if matches:
            return matches[0][0]  # Return first match
        return None
    
    def _extract_tags_from_expression(self, expr: str) -> Set[str]:
        """Extract all tags from an expression."""
        import re
        tags = set()
        
        # Match patterns like: TagName, TagName.Field, TagName[Index]
        tag_pattern = r'\b[A-Z][A-Z0-9_]*(\.[A-Z][A-Z0-9_]*)*(\[[^\]]*\])?\b'
        matches = re.findall(tag_pattern, expr)
        
        for match in matches:
            if match[0]:  # First group contains the tag name
                # Clean up the tag name (remove array indices, etc.)
                tag_name = match[0]
                # Remove array indices if present
                if '[' in tag_name:
                    tag_name = tag_name.split('[')[0]
                tags.add(tag_name)
        
        return tags
    
    def analyze_inter_routine_dataflow(self, ir_project: IRProject) -> List[Dict[str, str]]:
        """Analyze cross-routine data flow via shared tags."""
        dataflow = []
        
        # Build tag usage map per routine
        routine_tag_usage = {}
        
        for program in ir_project.programs:
            for routine in program.routines:
                routine_name = routine.name
                defs = set()
                uses = set()
                
                if routine.content:
                    # Analyze routine content for defs/uses
                    lines = routine.content.split('\n')
                    for line in lines:
                        line = line.strip()
                        if not line or line.startswith('//'):
                            continue
                        
                        # Analyze assignments (defs)
                        if ':=' in line:
                            parts = line.split(':=')
                            if len(parts) == 2:
                                lhs = parts[0].strip()
                                rhs = parts[1].strip().rstrip(';')
                                
                                # LHS is a def
                                tag = self._extract_tag_from_expression(lhs)
                                if tag:
                                    defs.add(tag)
                                
                                # RHS tags are uses
                                rhs_tags = self._extract_tags_from_expression(rhs)
                                uses.update(rhs_tags)
                
                routine_tag_usage[routine_name] = {
                    "defs": defs,
                    "uses": uses
                }
        
        # Find cross-routine data flow
        routines = list(routine_tag_usage.keys())
        for i, routine1 in enumerate(routines):
            for routine2 in routines[i+1:]:
                defs1 = routine_tag_usage[routine1]["defs"]
                uses2 = routine_tag_usage[routine2]["uses"]
                defs2 = routine_tag_usage[routine2]["defs"]
                uses1 = routine_tag_usage[routine1]["uses"]
                
                # Check if routine1 writes to tags that routine2 reads
                shared_tags = defs1 & uses2
                for tag in shared_tags:
                    dataflow.append({
                        "source": routine1,
                        "target": routine2,
                        "tag": tag,
                        "type": "write_to_read"
                    })
                
                # Check if routine2 writes to tags that routine1 reads
                shared_tags = defs2 & uses1
                for tag in shared_tags:
                    dataflow.append({
                        "source": routine2,
                        "target": routine1,
                        "tag": tag,
                        "type": "write_to_read"
                    })
        
        return dataflow 


class GraphExporter:
    """Export CFG and data flow graphs to DOT and GraphML formats."""
    
    def __init__(self):
        self.node_counter = 0
    
    def export_cfg_to_dot(self, cfg_data: Dict[str, Any], output_path: str) -> str:
        """Export control flow graph to DOT format."""
        dot_content = []
        dot_content.append("digraph CFG {")
        dot_content.append("  rankdir=TB;")
        dot_content.append("  node [shape=box, style=filled, fillcolor=lightblue];")
        dot_content.append("  edge [color=black];")
        dot_content.append("")
        
        for routine_name, routine_cfg in cfg_data.get("cfg", {}).items():
            # Add subgraph for each routine
            dot_content.append(f"  subgraph cluster_{routine_name.replace(' ', '_')} {{")
            dot_content.append(f"    label=\"{routine_name}\";")
            dot_content.append("    style=filled;")
            dot_content.append("    color=lightgrey;")
            dot_content.append("")
            
            blocks = routine_cfg.get("blocks", [])
            for block in blocks:
                block_id = block.get("block_id", "")
                block_type = block.get("type", "instruction")
                
                # Create node label
                if block_type == "branch":
                    condition = block.get("condition", "")
                    label = f"{block_id}\\nIF: {condition}"
                    color = "lightgreen"
                elif block_type == "control":
                    condition = block.get("condition", "")
                    label = f"{block_id}\\n{condition}"
                    color = "lightyellow"
                else:
                    instructions = block.get("instructions", [])
                    # Truncate instructions for display
                    if len(instructions) > 3:
                        display_instructions = instructions[:3] + ["..."]
                    else:
                        display_instructions = instructions
                    label = f"{block_id}\\n" + "\\n".join(display_instructions)
                    color = "lightblue"
                
                # Add data flow info
                defs = block.get("defs", [])
                uses = block.get("uses", [])
                if defs or uses:
                    label += f"\\nDefs: {', '.join(defs[:3])}"
                    if len(defs) > 3:
                        label += "..."
                    label += f"\\nUses: {', '.join(uses[:3])}"
                    if len(uses) > 3:
                        label += "..."
                
                dot_content.append(f"    \"{routine_name}_{block_id}\" [label=\"{label}\", fillcolor=\"{color}\"];")
            
            # Add edges
            for block in blocks:
                block_id = block.get("block_id", "")
                successors = block.get("successors", [])
                
                for successor in successors:
                    dot_content.append(f"    \"{routine_name}_{block_id}\" -> \"{routine_name}_{successor}\";")
                
                # Add conditional edges
                if block.get("type") == "branch":
                    true_succ = block.get("true_successor")
                    false_succ = block.get("false_successor")
                    if true_succ:
                        dot_content.append(f"    \"{routine_name}_{block_id}\" -> \"{routine_name}_{true_succ}\" [label=\"true\"];")
                    if false_succ:
                        dot_content.append(f"    \"{routine_name}_{block_id}\" -> \"{routine_name}_{false_succ}\" [label=\"false\"];")
            
            dot_content.append("  }")
            dot_content.append("")
        
        dot_content.append("}")
        
        # Write to file
        with open(output_path, 'w') as f:
            f.write('\n'.join(dot_content))
        
        return '\n'.join(dot_content)
    
    def export_dataflow_to_dot(self, cfg_data: Dict[str, Any], output_path: str) -> str:
        """Export inter-routine data flow to DOT format."""
        dot_content = []
        dot_content.append("digraph DataFlow {")
        dot_content.append("  rankdir=LR;")
        dot_content.append("  node [shape=box, style=filled, fillcolor=lightcoral];")
        dot_content.append("  edge [color=red];")
        dot_content.append("")
        
        # Add routine nodes
        routines = set()
        for routine_name in cfg_data.get("cfg", {}).keys():
            routines.add(routine_name)
        
        for routine in routines:
            dot_content.append(f"  \"{routine}\" [label=\"{routine}\"];")
        
        dot_content.append("")
        
        # Add data flow edges
        dataflow = cfg_data.get("inter_routine_dataflow", [])
        for flow in dataflow:
            source = flow.get("source", "")
            target = flow.get("target", "")
            tag = flow.get("tag", "")
            flow_type = flow.get("type", "write_to_read")
            
            edge_label = f"{tag}\\n({flow_type})"
            dot_content.append(f"  \"{source}\" -> \"{target}\" [label=\"{edge_label}\"];")
        
        dot_content.append("}")
        
        # Write to file
        with open(output_path, 'w') as f:
            f.write('\n'.join(dot_content))
        
        return '\n'.join(dot_content)
    
    def export_cfg_to_graphml(self, cfg_data: Dict[str, Any], output_path: str) -> str:
        """Export control flow graph to GraphML format."""
        graphml_content = []
        graphml_content.append('<?xml version="1.0" encoding="UTF-8"?>')
        graphml_content.append('<graphml xmlns="http://graphml.graphdrawing.org/xmlns"')
        graphml_content.append('         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"')
        graphml_content.append('         xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns')
        graphml_content.append('         http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">')
        graphml_content.append('')
        
        # Define attributes
        graphml_content.append('  <key id="label" for="node" attr.name="label" attr.type="string"/>')
        graphml_content.append('  <key id="type" for="node" attr.name="type" attr.type="string"/>')
        graphml_content.append('  <key id="routine" for="node" attr.name="routine" attr.type="string"/>')
        graphml_content.append('  <key id="defs" for="node" attr.name="defs" attr.type="string"/>')
        graphml_content.append('  <key id="uses" for="node" attr.name="uses" attr.type="string"/>')
        graphml_content.append('  <key id="tag" for="edge" attr.name="tag" attr.type="string"/>')
        graphml_content.append('  <key id="flow_type" for="edge" attr.name="flow_type" attr.type="string"/>')
        graphml_content.append('')
        
        # Start graph
        graphml_content.append('  <graph id="cfg" edgedefault="directed">')
        graphml_content.append('')
        
        # Add nodes
        node_id = 0
        for routine_name, routine_cfg in cfg_data.get("cfg", {}).items():
            blocks = routine_cfg.get("blocks", [])
            for block in blocks:
                block_id = block.get("block_id", "")
                block_type = block.get("type", "instruction")
                
                # Create node label
                if block_type == "branch":
                    condition = block.get("condition", "")
                    label = f"{block_id} - IF: {condition}"
                elif block_type == "control":
                    condition = block.get("condition", "")
                    label = f"{block_id} - {condition}"
                else:
                    instructions = block.get("instructions", [])
                    label = f"{block_id} - {len(instructions)} instructions"
                
                defs = block.get("defs", [])
                uses = block.get("uses", [])
                
                graphml_content.append(f'    <node id="n{node_id}">')
                graphml_content.append(f'      <data key="label">{label}</data>')
                graphml_content.append(f'      <data key="type">{block_type}</data>')
                graphml_content.append(f'      <data key="routine">{routine_name}</data>')
                graphml_content.append(f'      <data key="defs">{",".join(defs)}</data>')
                graphml_content.append(f'      <data key="uses">{",".join(uses)}</data>')
                graphml_content.append(f'    </node>')
                node_id += 1
        
        graphml_content.append('')
        
        # Add edges (simplified - just show connections between blocks)
        edge_id = 0
        for routine_name, routine_cfg in cfg_data.get("cfg", {}).items():
            blocks = routine_cfg.get("blocks", [])
            for block in blocks:
                block_id = block.get("block_id", "")
                successors = block.get("successors", [])
                
                for successor in successors:
                    graphml_content.append(f'    <edge id="e{edge_id}" source="n{edge_id}" target="n{edge_id + 1}">')
                    graphml_content.append(f'      <data key="tag">control_flow</data>')
                    graphml_content.append(f'      <data key="flow_type">successor</data>')
                    graphml_content.append(f'    </edge>')
                    edge_id += 1
        
        graphml_content.append('  </graph>')
        graphml_content.append('</graphml>')
        
        # Write to file
        with open(output_path, 'w') as f:
            f.write('\n'.join(graphml_content))
        
        return '\n'.join(graphml_content)
    
    def export_dataflow_to_graphml(self, cfg_data: Dict[str, Any], output_path: str) -> str:
        """Export inter-routine data flow to GraphML format."""
        graphml_content = []
        graphml_content.append('<?xml version="1.0" encoding="UTF-8"?>')
        graphml_content.append('<graphml xmlns="http://graphml.graphdrawing.org/xmlns"')
        graphml_content.append('         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"')
        graphml_content.append('         xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns')
        graphml_content.append('         http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">')
        graphml_content.append('')
        
        # Define attributes
        graphml_content.append('  <key id="label" for="node" attr.name="label" attr.type="string"/>')
        graphml_content.append('  <key id="tag" for="edge" attr.name="tag" attr.type="string"/>')
        graphml_content.append('  <key id="flow_type" for="edge" attr.name="flow_type" attr.type="string"/>')
        graphml_content.append('')
        
        # Start graph
        graphml_content.append('  <graph id="dataflow" edgedefault="directed">')
        graphml_content.append('')
        
        # Add routine nodes
        routines = set()
        for routine_name in cfg_data.get("cfg", {}).keys():
            routines.add(routine_name)
        
        node_id = 0
        routine_nodes = {}
        for routine in routines:
            graphml_content.append(f'    <node id="n{node_id}">')
            graphml_content.append(f'      <data key="label">{routine}</data>')
            graphml_content.append(f'    </node>')
            routine_nodes[routine] = f"n{node_id}"
            node_id += 1
        
        graphml_content.append('')
        
        # Add data flow edges
        dataflow = cfg_data.get("inter_routine_dataflow", [])
        edge_id = 0
        for flow in dataflow:
            source = flow.get("source", "")
            target = flow.get("target", "")
            tag = flow.get("tag", "")
            flow_type = flow.get("type", "write_to_read")
            
            if source in routine_nodes and target in routine_nodes:
                graphml_content.append(f'    <edge id="e{edge_id}" source="{routine_nodes[source]}" target="{routine_nodes[target]}">')
                graphml_content.append(f'      <data key="tag">{tag}</data>')
                graphml_content.append(f'      <data key="flow_type">{flow_type}</data>')
                graphml_content.append(f'    </edge>')
                edge_id += 1
        
        graphml_content.append('  </graph>')
        graphml_content.append('</graphml>')
        
        # Write to file
        with open(output_path, 'w') as f:
            f.write('\n'.join(graphml_content))
        
        return '\n'.join(graphml_content)


def export_ir_to_json(
    ir_project: IRProject,
    output_path: str,
    include: Optional[List[str]] = None,
    pretty_print: bool = True
) -> Dict[str, Any]:
    """
    Export selected components of the IR to JSON format.
    
    Args:
        ir_project: The IR project to export
        output_path: Path to the output JSON file
        include: List of components to include (tags, control_flow, data_types, etc.)
        pretty_print: Whether to format JSON with indentation
        
    Returns:
        Dictionary containing the exported data
    """
    if include is None:
        include = ["tags", "control_flow"]
    
    # Convert string components to enum values
    export_components = []
    for component in include:
        try:
            export_components.append(ExportComponent(component))
        except ValueError:
            logger.warning(f"Unknown export component: {component}")
    
    # Initialize export data
    export_data = {
        "metadata": {
            "export_time": datetime.now().isoformat(),
            "source_controller": ir_project.controller.name,
            "exported_components": include,
            "total_programs": len(ir_project.programs),
            "total_routines": sum(len(p.routines) for p in ir_project.programs)
        }
    }
    
    # Export tags
    if ExportComponent.TAGS in export_components:
        export_data["tags"] = _export_tags(ir_project)
    
    # Export data types
    if ExportComponent.DATA_TYPES in export_components:
        export_data["data_types"] = _export_data_types(ir_project)
    
    # Export function blocks
    if ExportComponent.FUNCTION_BLOCKS in export_components:
        export_data["function_blocks"] = _export_function_blocks(ir_project)
    
    # Export control flow
    if ExportComponent.CONTROL_FLOW in export_components:
        export_data["control_flow"] = _export_control_flow(ir_project)
    
    # Export routines
    if ExportComponent.ROUTINES in export_components:
        export_data["routines"] = _export_routines(ir_project)
    
    # Export programs
    if ExportComponent.PROGRAMS in export_components:
        export_data["programs"] = _export_programs(ir_project)
    
    # Export interactions
    if ExportComponent.INTERACTIONS in export_components:
        analyzer = InteractionAnalyzer()
        export_data["interactions"] = analyzer.analyze_interactions(ir_project)
    
    # Export semantic analysis
    if ExportComponent.SEMANTIC in export_components:
        export_data["semantic"] = _export_semantic(ir_project)
    
    # Export CFG analysis
    if ExportComponent.CFG in export_components:
        export_data["cfg"] = _export_cfg(ir_project)
    
    # Write to file
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        if pretty_print:
            json.dump(export_data, f, indent=2, default=str)
        else:
            json.dump(export_data, f, default=str)
    
    logger.info(f"Exported IR to {output_path}")
    return export_data


def _export_tags(ir_project: IRProject) -> Dict[str, Any]:
    """Export tag information."""
    controller_tags = []
    for tag in ir_project.controller.tags:
        controller_tags.append({
            "name": tag.name,
            "data_type": tag.data_type,
            "scope": tag.scope.value,
            "value": tag.value,
            "description": tag.description,
            "external_access": tag.external_access,
            "radix": tag.radix,
            "constant": tag.constant,
            "alias_for": tag.alias_for,
            "array_dimensions": tag.array_dimensions,
            "initial_value": tag.initial_value,
            "user_defined_type": tag.user_defined_type
        })
    
    program_tags = {}
    for program in ir_project.programs:
        program_tags[program.name] = []
        for tag in program.tags:
            program_tags[program.name].append({
                "name": tag.name,
                "data_type": tag.data_type,
                "scope": tag.scope.value,
                "value": tag.value,
                "description": tag.description,
                "external_access": tag.external_access,
                "radix": tag.radix,
                "constant": tag.constant,
                "alias_for": tag.alias_for,
                "array_dimensions": tag.array_dimensions,
                "initial_value": tag.initial_value,
                "user_defined_type": tag.user_defined_type
            })
    
    return {
        "controller_tags": controller_tags,
        "program_tags": program_tags,
        "summary": {
            "total_controller_tags": len(controller_tags),
            "total_program_tags": sum(len(tags) for tags in program_tags.values())
        }
    }


def _export_data_types(ir_project: IRProject) -> Dict[str, Any]:
    """Export data type information."""
    data_types = []
    for dt in ir_project.controller.data_types:
        members = []
        for member in dt.members:
            members.append({
                "name": member.name,
                "data_type": member.data_type,
                "description": member.description,
                "radix": member.radix,
                "external_access": member.external_access,
                "array_dimensions": member.array_dimensions,
                "initial_value": member.initial_value
            })
        
        data_types.append({
            "name": dt.name,
            "base_type": dt.base_type,
            "members": members,
            "description": dt.description,
            "is_enum": dt.is_enum,
            "enum_values": dt.enum_values
        })
    
    return {
        "data_types": data_types,
        "summary": {
            "total_data_types": len(data_types)
        }
    }


def _export_function_blocks(ir_project: IRProject) -> Dict[str, Any]:
    """Export function block information."""
    function_blocks = []
    for fb in ir_project.controller.function_blocks:
        parameters = []
        for param in fb.parameters:
            parameters.append({
                "name": param.name,
                "data_type": param.data_type,
                "parameter_type": param.parameter_type,
                "description": param.description,
                "required": param.required,
                "array_dimensions": param.array_dimensions,
                "initial_value": param.initial_value
            })
        
        local_variables = []
        for var in fb.local_variables:
            local_variables.append({
                "name": var.name,
                "data_type": var.data_type,
                "parameter_type": var.parameter_type,
                "description": var.description,
                "required": var.required,
                "array_dimensions": var.array_dimensions,
                "initial_value": var.initial_value
            })
        
        function_blocks.append({
            "name": fb.name,
            "description": fb.description,
            "parameters": parameters,
            "local_variables": local_variables,
            "implementation": fb.implementation
        })
    
    return {
        "function_blocks": function_blocks,
        "summary": {
            "total_function_blocks": len(function_blocks)
        }
    }


def _export_control_flow(ir_project: IRProject) -> Dict[str, Any]:
    """Export control flow information."""
    analyzer = ControlFlowAnalyzer()
    
    routines = {}
    for program in ir_project.programs:
        routines[program.name] = {}
        for routine in program.routines:
            routines[program.name][routine.name] = {
                "type": routine.routine_type.value,
                "description": routine.description,
                "control_flow": analyzer.analyze_routine_control_flow(routine)
            }
    
    return {
        "routines": routines,
        "summary": {
            "total_programs": len(routines),
            "total_routines": sum(len(r) for r in routines.values())
        }
    }


def _export_routines(ir_project: IRProject) -> Dict[str, Any]:
    """Export routine information."""
    routines = {}
    for program in ir_project.programs:
        routines[program.name] = []
        for routine in program.routines:
            local_vars = []
            for var in routine.local_variables:
                local_vars.append({
                    "name": var.name,
                    "data_type": var.data_type,
                    "scope": var.scope.value,
                    "value": var.value,
                    "description": var.description
                })
            
            parameters = []
            for param in routine.parameters:
                parameters.append({
                    "name": param.name,
                    "data_type": param.data_type,
                    "parameter_type": param.parameter_type,
                    "description": param.description,
                    "required": param.required
                })
            
            routines[program.name].append({
                "name": routine.name,
                "type": routine.routine_type.value,
                "description": routine.description,
                "content": routine.content,
                "local_variables": local_vars,
                "parameters": parameters,
                "return_type": routine.return_type
            })
    
    return {
        "routines": routines,
        "summary": {
            "total_programs": len(routines),
            "total_routines": sum(len(r) for r in routines.values())
        }
    }


def _export_programs(ir_project: IRProject) -> Dict[str, Any]:
    """Export program information."""
    programs = []
    for program in ir_project.programs:
        routine_names = [r.name for r in program.routines]
        
        programs.append({
            "name": program.name,
            "description": program.description,
            "main_routine": program.main_routine,
            "routines": routine_names,
            "tag_count": len(program.tags),
            "local_variable_count": len(program.local_variables)
        })
    
    return {
        "programs": programs,
        "summary": {
            "total_programs": len(programs)
        }
    }


def _export_semantic(ir_project: IRProject) -> Dict[str, Any]:
    """Export semantic analysis including tag usage, dependencies, and annotations."""
    analyzer = SemanticAnalyzer()
    
    # Analyze tag usage
    tag_summary = analyzer.analyze_tag_usage(ir_project)
    
    # Analyze inter-routine dependencies
    interdependencies = analyzer.analyze_interdependencies(ir_project)
    
    # Analyze control flow annotations
    control_flow_annotations = analyzer.analyze_control_flow_annotations(ir_project)
    
    # Calculate summary statistics
    total_routines = sum(len(program.routines) for program in ir_project.programs)
    total_dependencies = len(interdependencies)
    total_annotations = sum(len(annotations) for annotations in control_flow_annotations.values())
    
    return {
        "tag_summary": tag_summary,
        "interdependencies": interdependencies,
        "control_flow_annotations": control_flow_annotations,
        "summary": {
            "total_routines": total_routines,
            "total_dependencies": total_dependencies,
            "total_annotations": total_annotations
        }
    }


def _export_cfg(ir_project: IRProject) -> Dict[str, Any]:
    """Export control flow graph analysis."""
    analyzer = CFGAnalyzer()
    
    # Generate CFG for all routines
    cfg_data = analyzer.analyze_cfg(ir_project)
    
    # Analyze inter-routine data flow
    inter_routine_dataflow = analyzer.analyze_inter_routine_dataflow(ir_project)
    
    # Calculate summary statistics
    total_blocks = sum(len(cfg.get("blocks", [])) for cfg in cfg_data.values())
    total_dataflow_edges = len(inter_routine_dataflow)
    
    return {
        "cfg": cfg_data,
        "inter_routine_dataflow": inter_routine_dataflow,
        "summary": {
            "total_routines_with_cfg": len(cfg_data),
            "total_blocks": total_blocks,
            "total_dataflow_edges": total_dataflow_edges
        }
    } 


def export_cfg_to_graphs(cfg_data: Dict[str, Any], output_dir: str = "out") -> Dict[str, str]:
    """Export CFG data to DOT and GraphML formats."""
    exporter = GraphExporter()
    output_files = {}
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Export CFG to DOT
    cfg_dot_path = f"{output_dir}/cfg.dot"
    exporter.export_cfg_to_dot(cfg_data, cfg_dot_path)
    output_files["cfg_dot"] = cfg_dot_path
    
    # Export data flow to DOT
    dataflow_dot_path = f"{output_dir}/dataflow.dot"
    exporter.export_dataflow_to_dot(cfg_data, dataflow_dot_path)
    output_files["dataflow_dot"] = dataflow_dot_path
    
    # Export CFG to GraphML
    cfg_graphml_path = f"{output_dir}/cfg.graphml"
    exporter.export_cfg_to_graphml(cfg_data, cfg_graphml_path)
    output_files["cfg_graphml"] = cfg_graphml_path
    
    # Export data flow to GraphML
    dataflow_graphml_path = f"{output_dir}/dataflow.graphml"
    exporter.export_dataflow_to_graphml(cfg_data, dataflow_graphml_path)
    output_files["dataflow_graphml"] = dataflow_graphml_path
    
    return output_files 