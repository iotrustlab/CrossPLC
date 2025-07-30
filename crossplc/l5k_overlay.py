"""
L5K Overlay for L5X-ST Compiler

This module provides support for parsing L5K files (Allen Bradley full ASCII export format)
and extracting missing project-level context such as:
- Global and controller-scoped tag declarations
- Task/program execution mapping
- Module configurations
- Default values for tags
- Program-to-task bindings

This information is injected into the existing IR (Intermediate Representation) used during L5X parsing.
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path

from .models import (
    IRProject, IRController, IRProgram, IRRoutine, IRTag, IRDataType,
    IRDataTypeMember, IRFunctionBlock, IRFunctionBlockParameter,
    TagScope, RoutineType
)

logger = logging.getLogger(__name__)


@dataclass
class L5KTag:
    """Represents a tag from L5K file."""
    name: str
    data_type: str
    scope: str = "Controller"  # Controller or Program
    value: Optional[str] = None
    description: Optional[str] = None
    external_access: Optional[str] = None
    radix: Optional[str] = None
    constant: bool = False
    alias_for: Optional[str] = None
    array_dimensions: Optional[List[int]] = None
    initial_value: Optional[str] = None


@dataclass
class L5KTask:
    """Represents a task from L5K file."""
    name: str
    task_type: str  # CONTINUOUS, PERIODIC, EVENT
    priority: int = 10
    watchdog: int = 500
    interval: Optional[str] = None  # For periodic tasks
    description: Optional[str] = None


@dataclass
class L5KProgram:
    """Represents a program from L5K file."""
    name: str
    main_routine: Optional[str] = None
    task_name: Optional[str] = None
    description: Optional[str] = None
    tags: List[L5KTag] = field(default_factory=list)


@dataclass
class L5KModule:
    """Represents a module from L5K file."""
    name: str
    module_type: str
    slot: int
    description: Optional[str] = None
    configuration: Dict[str, Any] = field(default_factory=dict)


class L5KOverlay:
    """Parses L5K files and extracts project-level context."""
    
    def __init__(self, l5k_file_path: str):
        """
        Initialize the L5K overlay parser.
        
        Args:
            l5k_file_path: Path to the L5K file
        """
        self.l5k_file_path = Path(l5k_file_path)
        self.content: str = ""
        self.tags: List[L5KTag] = []
        self.tasks: List[L5KTask] = []
        self.programs: List[L5KProgram] = []
        self.modules: List[L5KModule] = []
        
        if not self.l5k_file_path.exists():
            raise FileNotFoundError(f"L5K file not found: {l5k_file_path}")
        
        self._load_content()
        self._parse_content()
    
    def _load_content(self) -> None:
        """Load the L5K file content."""
        try:
            with open(self.l5k_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                self.content = f.read()
            logger.info(f"Loaded L5K file: {self.l5k_file_path}")
        except Exception as e:
            logger.error(f"Error loading L5K file: {e}")
            raise
    
    def _parse_content(self) -> None:
        """Parse the L5K content and extract all sections."""
        logger.info("Parsing L5K content...")
        
        # Parse tags
        self._parse_tags()
        
        # Parse tasks
        self._parse_tasks()
        
        # Parse programs
        self._parse_programs()
        
        # Parse modules
        self._parse_modules()
        
        logger.info(f"Parsed {len(self.tags)} tags, {len(self.tasks)} tasks, "
                   f"{len(self.programs)} programs, {len(self.modules)} modules")
    
    def _parse_tags(self) -> None:
        """Parse TAG sections from L5K content."""
        # Pattern to match TAG blocks in real L5K format
        # TAG blocks are enclosed in TAG ... END_TAG
        tag_block_pattern = r'TAG\s+(.*?)END_TAG'
        
        matches = re.finditer(tag_block_pattern, self.content, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            tag_block = match.group(1).strip()
            
            # Parse individual tag definitions within the block
            # Each tag is on a line: tag_name : data_type (attributes) := value;
            tag_lines = tag_block.split('\n')
            
            for line in tag_lines:
                line = line.strip()
                if not line or line.startswith('--'):
                    continue
                
                # Parse tag definition
                tag_info = self._parse_tag_line(line)
                if tag_info:
                    self.tags.append(tag_info)
    
    def _parse_tag_line(self, line: str) -> Optional[L5KTag]:
        """Parse a single tag line from L5K format."""
        try:
            # Pattern: tag_name : data_type (attributes) := value;
            # Example: System_Ready : BOOL (RADIX := Decimal) := FALSE;
            
            # Extract tag name and definition
            tag_match = re.match(r'(\w+)\s*:\s*(.+?);', line)
            if not tag_match:
                return None
            
            tag_name = tag_match.group(1)
            tag_def = tag_match.group(2).strip()
            
            # Extract data type and array dimensions
            # Handle both simple types and array types
            data_type_match = re.match(r'(\w+)(?:\s*\[([^\]]+)\])?', tag_def)
            if not data_type_match:
                return None
            
            data_type = data_type_match.group(1).upper()
            array_def = data_type_match.group(2)
            
            # Parse array dimensions if present
            array_dimensions = None
            if array_def:
                array_dimensions = self._parse_array_dimensions(array_def)
            
            # Extract attributes in parentheses
            attributes = {}
            attr_match = re.search(r'\(([^)]+)\)', tag_def)
            if attr_match:
                attr_text = attr_match.group(1)
                # Parse attributes like "RADIX := Decimal, ExternalAccess := Read Only"
                # Handle quoted values properly
                attr_pairs = re.findall(r'(\w+)\s*:=\s*([^,]+?)(?=\s*,\s*\w+\s*:=|$)', attr_text)
                for key, value in attr_pairs:
                    attributes[key.strip().upper()] = value.strip()
            
            # Extract initial value - look for := value at the end
            initial_value = None
            # First, remove the attributes part to avoid confusion
            clean_line = re.sub(r'\([^)]*\)', '', line)
            value_match = re.search(r':=\s*([^;]+?)(?=\s*;|$)', clean_line)
            if value_match:
                initial_value = value_match.group(1).strip()
            
            # Extract description from attributes
            description = attributes.get('DESCRIPTION', None)
            if description and description.startswith('"') and description.endswith('"'):
                description = description[1:-1]  # Remove quotes
            
            # Extract external access
            external_access = attributes.get('EXTERNALACCESS', None)
            if external_access and external_access.startswith('"') and external_access.endswith('"'):
                external_access = external_access[1:-1]  # Remove quotes
            
            # Extract radix
            radix = attributes.get('RADIX', None)
            
            # Check if constant
            constant = 'CONSTANT' in tag_def.upper()
            
            # Check if alias
            alias_for = attributes.get('ALIAS_FOR', None)
            if alias_for and alias_for.startswith('"') and alias_for.endswith('"'):
                alias_for = alias_for[1:-1]  # Remove quotes
            
            return L5KTag(
                name=tag_name,
                data_type=data_type,
                value=initial_value,
                description=description,
                external_access=external_access,
                radix=radix,
                constant=constant,
                alias_for=alias_for,
                array_dimensions=array_dimensions,
                initial_value=initial_value
            )
            
        except Exception as e:
            logger.warning(f"Error parsing tag line '{line}': {e}")
            return None
    
    def _parse_tag_definition(self, name: str, definition: str) -> Optional[L5KTag]:
        """Parse individual tag definition."""
        try:
            # Extract data type and other properties
            # Common patterns: "BOOL", "DINT", "REAL", "STRING", etc.
            data_type_pattern = r'(\w+)(?:\s*\[([^\]]+)\])?'
            data_type_match = re.search(data_type_pattern, definition)
            
            if not data_type_match:
                logger.warning(f"Could not parse data type for tag {name}: {definition}")
                return None
            
            data_type = data_type_match.group(1).upper()
            array_def = data_type_match.group(2)
            
            # Parse array dimensions if present
            array_dimensions = None
            if array_def:
                array_dimensions = self._parse_array_dimensions(array_def)
            
            # Check for initial value
            initial_value = None
            value_match = re.search(r':=\s*([^;]+)', definition)
            if value_match:
                initial_value = value_match.group(1).strip()
            
            # Check for description
            description = None
            desc_match = re.search(r'DESCRIPTION\s*=\s*"([^"]*)"', definition, re.IGNORECASE)
            if desc_match:
                description = desc_match.group(1)
            
            # Check for external access
            external_access = None
            if 'EXTERNAL_ACCESS' in definition.upper():
                external_match = re.search(r'EXTERNAL_ACCESS\s*=\s*"([^"]*)"', definition, re.IGNORECASE)
                if external_match:
                    external_access = external_match.group(1)
            
            # Check for radix
            radix = None
            if 'RADIX' in definition.upper():
                radix_match = re.search(r'RADIX\s*=\s*"([^"]*)"', definition, re.IGNORECASE)
                if radix_match:
                    radix = radix_match.group(1)
            
            # Check if constant
            constant = 'CONSTANT' in definition.upper()
            
            # Check if alias
            alias_for = None
            if 'ALIAS_FOR' in definition.upper():
                alias_match = re.search(r'ALIAS_FOR\s*=\s*"([^"]*)"', definition, re.IGNORECASE)
                if alias_match:
                    alias_for = alias_match.group(1)
            
            return L5KTag(
                name=name,
                data_type=data_type,
                value=initial_value,
                description=description,
                external_access=external_access,
                radix=radix,
                constant=constant,
                alias_for=alias_for,
                array_dimensions=array_dimensions,
                initial_value=initial_value
            )
            
        except Exception as e:
            logger.warning(f"Error parsing tag {name}: {e}")
            return None
    
    def _parse_array_dimensions(self, array_def: str) -> List[int]:
        """Parse array dimensions from array definition."""
        try:
            # Remove spaces and split by comma
            dimensions = [int(d.strip()) for d in array_def.split(',')]
            return dimensions
        except Exception as e:
            logger.warning(f"Error parsing array dimensions '{array_def}': {e}")
            return []
    
    def _parse_tasks(self) -> None:
        """Parse TASK sections from L5K content and build program-to-task mapping."""
        # Pattern to match TASK blocks in real L5K format
        # TASK blocks are enclosed in TASK ... END_TASK
        task_block_pattern = r'TASK\s+(\w+)\s*\((.*?)\)\s*(.*?)END_TASK'
        self.program_to_task = {}  # program name -> task name
        matches = re.finditer(task_block_pattern, self.content, re.IGNORECASE | re.DOTALL)
        for match in matches:
            task_name = match.group(1)
            task_params = match.group(2).strip()
            task_content = match.group(3).strip()
            # Find scheduled programs (lines ending with ;)
            for line in task_content.splitlines():
                prog = line.strip().rstrip(';')
                if prog:
                    self.program_to_task[prog] = task_name
            task_info = self._parse_task_definition(task_name, task_params, task_content)
            if task_info:
                self.tasks.append(task_info)
    
    def _parse_task_definition(self, name: str, params: str, content: str) -> Optional[L5KTask]:
        """Parse individual task definition."""
        try:
            # Extract task type from parameters
            task_type = "CONTINUOUS"  # Default
            if "PERIODIC" in params.upper():
                task_type = "PERIODIC"
            elif "EVENT" in params.upper():
                task_type = "EVENT"
            # Extract priority
            priority = 10  # Default
            priority_match = re.search(r'Priority\s*:=\s*(\d+)', params, re.IGNORECASE)
            if priority_match:
                priority = int(priority_match.group(1))
            # Extract watchdog
            watchdog = 500  # Default
            watchdog_match = re.search(r'Watchdog\s*:=\s*(\d+)', params, re.IGNORECASE)
            if watchdog_match:
                watchdog = int(watchdog_match.group(1))
            # Extract rate for periodic tasks
            interval = None
            if task_type == "PERIODIC":
                rate_match = re.search(r'Rate\s*:=\s*(\d+)', params, re.IGNORECASE)
                if rate_match:
                    rate = int(rate_match.group(1))
                    interval = f"T#{rate}ms"
            return L5KTask(
                name=name,
                task_type=task_type,
                priority=priority,
                watchdog=watchdog,
                interval=interval,
                description=None
            )
        except Exception as e:
            logger.warning(f"Error parsing task {name}: {e}")
            return None
    
    def _parse_program_definition(self, name: str, params: str, content: str) -> Optional[L5KProgram]:
        """Parse individual program definition."""
        try:
            # Extract main routine
            main_routine = None
            main_routine_match = re.search(r'MAIN\s*:=\s*"([^"]*)"', params, re.IGNORECASE)
            if main_routine_match:
                main_routine = main_routine_match.group(1)
            # Use the program_to_task mapping
            task_name = getattr(self, 'program_to_task', {}).get(name)
            # Also check if there's a TASK parameter in the program definition
            if not task_name:
                task_match = re.search(r'TASK\s*:=\s*"([^"]*)"', params, re.IGNORECASE)
                if task_match:
                    task_name = task_match.group(1)
            return L5KProgram(
                name=name,
                main_routine=main_routine,
                task_name=task_name,
                description=None
            )
        except Exception as e:
            logger.warning(f"Error parsing program {name}: {e}")
            return None
    
    def _parse_programs(self) -> None:
        """Parse PROGRAM sections from L5K content."""
        # Pattern to match PROGRAM blocks in real L5K format
        # PROGRAM blocks are enclosed in PROGRAM ... END_PROGRAM
        program_block_pattern = r'PROGRAM\s+(\w+)\s*\((.*?)\)\s*(.*?)END_PROGRAM'
        matches = re.finditer(program_block_pattern, self.content, re.IGNORECASE | re.DOTALL)
        for match in matches:
            program_name = match.group(1)
            program_params = match.group(2).strip()
            program_content = match.group(3).strip()
            program_info = self._parse_program_definition(program_name, program_params, program_content)
            if program_info:
                self.programs.append(program_info)
    
    def _parse_modules(self) -> None:
        """Parse MODULE sections from L5K content."""
        # Pattern to match MODULE blocks in real L5K format
        # MODULE blocks are enclosed in MODULE ... END_MODULE
        module_block_pattern = r'MODULE\s+(\w+)\s*\((.*?)\)\s*(.*?)END_MODULE'
        
        matches = re.finditer(module_block_pattern, self.content, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            module_name = match.group(1)
            module_params = match.group(2).strip()
            module_content = match.group(3).strip()
            
            module_info = self._parse_module_definition(module_name, module_params, module_content)
            if module_info:
                self.modules.append(module_info)
    
    def _parse_module_definition(self, name: str, params: str, content: str) -> Optional[L5KModule]:
        """Parse individual module definition."""
        try:
            # Extract module type from parameters
            module_type = "UNKNOWN"
            # Look for CatalogNumber parameter which contains the actual module type
            catalog_match = re.search(r'CatalogNumber\s*:=\s*"([^"]*)"', params, re.IGNORECASE)
            if catalog_match:
                module_type = catalog_match.group(1)
            else:
                # Fallback to Parent parameter
                parent_match = re.search(r'Parent\s*:=\s*"([^"]*)"', params, re.IGNORECASE)
                if parent_match:
                    parent = parent_match.group(1)
                    # Extract module type from parent or name
                    if "CONTROLLER" in name.upper():
                        module_type = "Controller"
                    elif "RIO" in name.upper():
                        module_type = "Remote I/O"
                    elif "EN" in name.upper():
                        module_type = "Ethernet"
                    else:
                        module_type = parent
            
            # Extract slot (not always present in L5K)
            slot = 0
            slot_match = re.search(r'Slot\s*:=\s*(\d+)', params, re.IGNORECASE)
            if slot_match:
                slot = int(slot_match.group(1))
            
            # Extract configuration parameters
            configuration = {}
            config_matches = re.finditer(r'(\w+)\s*:=\s*([^,]+)', params, re.IGNORECASE)
            for config_match in config_matches:
                param_name = config_match.group(1).strip()
                param_value = config_match.group(2).strip()
                if param_name not in ['Slot']:  # Skip already parsed parameters
                    configuration[param_name] = param_value
            
            return L5KModule(
                name=name,
                module_type=module_type,
                slot=slot,
                description=None,
                configuration=configuration
            )
            
        except Exception as e:
            logger.warning(f"Error parsing module {name}: {e}")
            return None
    
    def apply_to_ir(self, ir_project: IRProject) -> IRProject:
        """
        Apply L5K overlay data to an existing IR project.
        
        Args:
            ir_project: The IR project to augment
            
        Returns:
            Augmented IR project
        """
        logger.info("Applying L5K overlay to IR project...")
        
        # Create a copy of the IR project to avoid modifying the original
        augmented_project = self._deep_copy_ir_project(ir_project)
        
        # Apply tags
        self._apply_tags_to_ir(augmented_project)
        
        # Apply tasks
        self._apply_tasks_to_ir(augmented_project)
        
        # Apply programs
        self._apply_programs_to_ir(augmented_project)
        
        # Apply modules
        self._apply_modules_to_ir(augmented_project)
        
        # Update metadata
        augmented_project.metadata['l5k_overlay_applied'] = True
        augmented_project.metadata['l5k_source_file'] = str(self.l5k_file_path)
        augmented_project.metadata['l5k_tags_added'] = len(self.tags)
        augmented_project.metadata['l5k_tasks_added'] = len(self.tasks)
        augmented_project.metadata['l5k_programs_added'] = len(self.programs)
        augmented_project.metadata['l5k_modules_added'] = len(self.modules)
        
        logger.info("L5K overlay applied successfully")
        return augmented_project
    
    def _deep_copy_ir_project(self, ir_project: IRProject) -> IRProject:
        """Create a deep copy of the IR project."""
        # This is a simplified deep copy - in production, consider using copy.deepcopy
        return IRProject(
            controller=ir_project.controller,
            programs=ir_project.programs.copy(),
            modules=ir_project.modules.copy(),
            tasks=ir_project.tasks.copy(),
            metadata=ir_project.metadata.copy()
        )
    
    def _apply_tags_to_ir(self, ir_project: IRProject) -> None:
        """Apply L5K tags to IR project."""
        for l5k_tag in self.tags:
            # Check if tag already exists in controller
            existing_tag = next(
                (tag for tag in ir_project.controller.tags if tag.name == l5k_tag.name),
                None
            )
            
            if existing_tag is None:
                # Convert L5K tag to IR tag
                ir_tag = IRTag(
                    name=l5k_tag.name,
                    data_type=l5k_tag.data_type,
                    scope=TagScope.CONTROLLER if l5k_tag.scope == "Controller" else TagScope.PROGRAM,
                    value=l5k_tag.value,
                    description=l5k_tag.description,
                    external_access=l5k_tag.external_access,
                    radix=l5k_tag.radix,
                    constant=l5k_tag.constant,
                    alias_for=l5k_tag.alias_for,
                    array_dimensions=l5k_tag.array_dimensions,
                    initial_value=l5k_tag.initial_value
                )
                
                ir_project.controller.tags.append(ir_tag)
                logger.debug(f"Added L5K tag to IR: {l5k_tag.name}")
            else:
                # Update existing tag with L5K information
                self._merge_tag_info(existing_tag, l5k_tag)
                logger.debug(f"Updated existing tag with L5K info: {l5k_tag.name}")
    
    def _merge_tag_info(self, ir_tag: IRTag, l5k_tag: L5KTag) -> None:
        """Merge L5K tag information into existing IR tag."""
        # Only update fields that are not already set in IR tag
        if not ir_tag.description and l5k_tag.description:
            ir_tag.description = l5k_tag.description
        
        if not ir_tag.external_access and l5k_tag.external_access:
            ir_tag.external_access = l5k_tag.external_access
        
        if not ir_tag.radix and l5k_tag.radix:
            ir_tag.radix = l5k_tag.radix
        
        if not ir_tag.initial_value and l5k_tag.initial_value:
            ir_tag.initial_value = l5k_tag.initial_value
        
        if not ir_tag.array_dimensions and l5k_tag.array_dimensions:
            ir_tag.array_dimensions = l5k_tag.array_dimensions
    
    def _apply_tasks_to_ir(self, ir_project: IRProject) -> None:
        """Apply L5K tasks to IR project."""
        for l5k_task in self.tasks:
            # Create task representation (simplified for now)
            task_info = {
                'name': l5k_task.name,
                'type': l5k_task.task_type,
                'priority': l5k_task.priority,
                'watchdog': l5k_task.watchdog,
                'interval': l5k_task.interval,
                'description': l5k_task.description
            }
            
            # Check if task already exists
            existing_task = next(
                (task for task in ir_project.tasks if task.get('name') == l5k_task.name),
                None
            )
            
            if existing_task is None:
                ir_project.tasks.append(task_info)
                logger.debug(f"Added L5K task to IR: {l5k_task.name}")
            else:
                # Update existing task
                existing_task.update(task_info)
                logger.debug(f"Updated existing task with L5K info: {l5k_task.name}")
    
    def _apply_programs_to_ir(self, ir_project: IRProject) -> None:
        """Apply L5K programs to IR project."""
        for l5k_program in self.programs:
            # Find existing program in IR
            existing_program = next(
                (prog for prog in ir_project.programs if prog.name == l5k_program.name),
                None
            )
            
            if existing_program is None:
                # Create new program
                ir_program = IRProgram(
                    name=l5k_program.name,
                    description=l5k_program.description,
                    main_routine=l5k_program.main_routine
                )
                ir_project.programs.append(ir_program)
                logger.debug(f"Added L5K program to IR: {l5k_program.name}")
            else:
                # Update existing program
                if not existing_program.description and l5k_program.description:
                    existing_program.description = l5k_program.description
                
                if not existing_program.main_routine and l5k_program.main_routine:
                    existing_program.main_routine = l5k_program.main_routine
                
                logger.debug(f"Updated existing program with L5K info: {l5k_program.name}")
    
    def _apply_modules_to_ir(self, ir_project: IRProject) -> None:
        """Apply L5K modules to IR project."""
        for l5k_module in self.modules:
            # Create module representation
            module_info = {
                'name': l5k_module.name,
                'type': l5k_module.module_type,
                'slot': l5k_module.slot,
                'description': l5k_module.description,
                'configuration': l5k_module.configuration
            }
            
            # Check if module already exists
            existing_module = next(
                (mod for mod in ir_project.modules if mod.get('name') == l5k_module.name),
                None
            )
            
            if existing_module is None:
                ir_project.modules.append(module_info)
                logger.debug(f"Added L5K module to IR: {l5k_module.name}")
            else:
                # Update existing module
                existing_module.update(module_info)
                logger.debug(f"Updated existing module with L5K info: {l5k_module.name}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of parsed L5K data."""
        return {
            'source_file': str(self.l5k_file_path),
            'tags_count': len(self.tags),
            'tasks_count': len(self.tasks),
            'programs_count': len(self.programs),
            'modules_count': len(self.modules),
            'tags': [tag.name for tag in self.tags],
            'tasks': [task.name for task in self.tasks],
            'programs': [prog.name for prog in self.programs],
            'modules': [mod.name for mod in self.modules]
        } 