"""
OpenPLC ST Parser

This module provides parsing capabilities for OpenPLC .st files,
converting them to the Intermediate Representation format for
mixed-platform multi-PLC analysis.
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .models import (
    IRProject, IRController, IRProgram, IRRoutine, 
    IRTag, IRDataType, TagScope, IRFunctionBlock, RoutineType, DataType
)

logger = logging.getLogger(__name__)


@dataclass
class OpenPLCVariable:
    """Represents a variable declaration in OpenPLC ST."""
    name: str
    data_type: str
    initial_value: Optional[str] = None
    scope: str = "VAR"  # VAR, VAR_INPUT, VAR_OUTPUT, etc.


class OpenPLCParser:
    """Parser for OpenPLC .st files to Intermediate Representation."""
    
    def __init__(self):
        self.source_type = "openplc"
    
    def parse(self, path: Path) -> IRProject:
        """
        Parse an OpenPLC .st file and convert to IR.
        
        Args:
            path: Path to the OpenPLC .st file
            
        Returns:
            IRProject with OpenPLC content
        """
        logger.info(f"Parsing OpenPLC file: {path}")
        
        # Read the file content
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract controller name from filename
        controller_name = self._extract_controller_name(path)
        
        # Parse variables
        variables = self._parse_variables(content)
        logger.info(f"Found {len(variables)} variables")
        
        # Parse routines
        routines = self._parse_routines(content)
        
        # Create IR objects
        controller = self._create_controller(controller_name, variables)
        program = self._create_program(controller_name, routines)
        
        # Create IR project
        ir_project = IRProject(
            controller=controller,
            programs=[program],
            source_type=self.source_type
        )
        
        logger.info(f"Parsed OpenPLC file: {len(variables)} variables, {len(routines)} routines")
        return ir_project
    
    def _extract_controller_name(self, path: Path) -> str:
        """Extract controller name from filename."""
        # Remove .st extension and use as controller name
        return path.stem
    
    def _parse_variables(self, content: str) -> List[OpenPLCVariable]:
        """Parse variable declarations from OpenPLC ST content."""
        variables = []
        
        # Match VAR blocks (both standalone and inside PROGRAM blocks)
        var_patterns = [
            r'VAR\s*([^E]*?END_VAR)',
            r'VAR_INPUT\s*([^E]*?END_VAR)',
            r'VAR_OUTPUT\s*([^E]*?END_VAR)',
            r'VAR_IN_OUT\s*([^E]*?END_VAR)',
            r'VAR_GLOBAL\s*([^E]*?END_VAR)'
        ]
        
        for pattern in var_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                var_block = match.group(1).strip()
                scope = self._extract_scope_from_pattern(pattern)
                logger.info(f"Found {scope} block: {var_block[:50]}...")
                block_vars = self._parse_variable_block(var_block, scope)
                logger.info(f"Parsed {len(block_vars)} variables from {scope} block")
                variables.extend(block_vars)
        
        # Fallback: try simpler pattern
        if not variables:
            logger.info("Trying fallback VAR pattern")
            fallback_matches = re.findall(r'VAR.*?END_VAR', content, re.DOTALL | re.IGNORECASE)
            for var_block in fallback_matches:
                # Extract content between VAR and END_VAR
                content_match = re.search(r'VAR\s*(.*?)\s*END_VAR', var_block, re.DOTALL | re.IGNORECASE)
                if content_match:
                    var_content = content_match.group(1).strip()
                    logger.info(f"Found VAR block with content: {var_content[:50]}...")
                    block_vars = self._parse_variable_block(var_content, 'VAR')
                    logger.info(f"Parsed {len(block_vars)} variables from fallback VAR block")
                    variables.extend(block_vars)
        
        return variables
    
    def _extract_scope_from_pattern(self, pattern: str) -> str:
        """Extract scope from regex pattern."""
        if 'VAR_INPUT' in pattern:
            return 'VAR_INPUT'
        elif 'VAR_OUTPUT' in pattern:
            return 'VAR_OUTPUT'
        elif 'VAR_IN_OUT' in pattern:
            return 'VAR_IN_OUT'
        elif 'VAR_GLOBAL' in pattern:
            return 'VAR_GLOBAL'
        else:
            return 'VAR'
    
    def _parse_variable_block(self, var_block: str, scope: str) -> List[OpenPLCVariable]:
        """Parse individual variable declarations within a VAR block."""
        variables = []
        
        # Split by semicolon and process each declaration
        declarations = var_block.split(';')
        
        for decl in declarations:
            decl = decl.strip()
            if not decl:
                continue
            
            # Match variable declaration patterns
            # Format: variable_name [AT hardware_address] : data_type [:= initial_value]
            var_pattern = r'(\w+)(?:\s+AT\s+[^:]+)?\s*:\s*(\w+(?:\s*\[\s*\d+\s*\]|\s*\[\s*\d+\s*\.\.\s*\d+\s*\])?)\s*(?::=?\s*([^;]+))?'
            match = re.match(var_pattern, decl)
            
            if match:
                name = match.group(1).strip()
                data_type = match.group(2).strip()
                initial_value = match.group(3).strip() if match.group(3) else None
                
                variable = OpenPLCVariable(
                    name=name,
                    data_type=data_type,
                    initial_value=initial_value,
                    scope=scope
                )
                variables.append(variable)
        
        return variables
    
    def _parse_routines(self, content: str) -> List[Dict[str, Any]]:
        """Parse routines from OpenPLC ST content."""
        routines = []
        
        # Look for PROGRAM blocks
        program_pattern = r'PROGRAM\s+(\w+)\s*([^END_PROGRAM]*?)END_PROGRAM'
        program_matches = re.finditer(program_pattern, content, re.IGNORECASE | re.DOTALL)
        
        for match in program_matches:
            program_name = match.group(1)
            program_content = match.group(2).strip()
            
            # Create a routine for the program
            routine = {
                'name': program_name,
                'content': program_content,
                'type': 'ST',
                'language': 'ST'
            }
            routines.append(routine)
        
        # Look for FUNCTION blocks
        function_pattern = r'FUNCTION\s+(\w+)\s*:\s*(\w+)\s*([^END_FUNCTION]*?)END_FUNCTION'
        function_matches = re.finditer(function_pattern, content, re.IGNORECASE | re.DOTALL)
        
        for match in function_matches:
            function_name = match.group(1)
            return_type = match.group(2)
            function_content = match.group(3).strip()
            
            # Create a routine for the function
            routine = {
                'name': function_name,
                'content': function_content,
                'type': 'ST',
                'language': 'ST',
                'return_type': return_type
            }
            routines.append(routine)
        
        # If no PROGRAM or FUNCTION blocks found, treat entire content as main routine
        if not routines:
            # Remove VAR blocks to get just the control logic
            logic_content = self._extract_control_logic(content)
            if logic_content.strip():
                routine = {
                    'name': 'Main',
                    'content': logic_content,
                    'type': 'ST',
                    'language': 'ST'
                }
                routines.append(routine)
        
        return routines
    
    def _extract_control_logic(self, content: str) -> str:
        """Extract control logic by removing VAR blocks."""
        # Remove all VAR blocks
        var_pattern = r'VAR\s*[^END_VAR]*?END_VAR'
        logic_content = re.sub(var_pattern, '', content, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove VAR_INPUT, VAR_OUTPUT, etc. blocks
        var_input_pattern = r'VAR_INPUT\s*[^END_VAR]*?END_VAR'
        logic_content = re.sub(var_input_pattern, '', logic_content, flags=re.IGNORECASE | re.DOTALL)
        
        var_output_pattern = r'VAR_OUTPUT\s*[^END_VAR]*?END_VAR'
        logic_content = re.sub(var_output_pattern, '', logic_content, flags=re.IGNORECASE | re.DOTALL)
        
        var_global_pattern = r'VAR_GLOBAL\s*[^END_VAR]*?END_VAR'
        logic_content = re.sub(var_global_pattern, '', logic_content, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove PROGRAM and FUNCTION blocks
        program_pattern = r'PROGRAM\s+\w+\s*[^END_PROGRAM]*?END_PROGRAM'
        logic_content = re.sub(program_pattern, '', logic_content, flags=re.IGNORECASE | re.DOTALL)
        
        function_pattern = r'FUNCTION\s+\w+\s*:\s*\w+\s*[^END_FUNCTION]*?END_FUNCTION'
        logic_content = re.sub(function_pattern, '', logic_content, flags=re.IGNORECASE | re.DOTALL)
        
        return logic_content.strip()
    
    def _create_controller(self, controller_name: str, variables: List[OpenPLCVariable]) -> IRController:
        """Create IRController from OpenPLC variables."""
        # Convert OpenPLC variables to IR tags
        tags = []
        
        for var in variables:
            # Map OpenPLC data types to IR data types
            ir_data_type = self._map_data_type(var.data_type)
            
            # Map OpenPLC scope to IR scope
            ir_scope = self._map_scope(var.scope)
            
            tag = IRTag(
                name=var.name,
                data_type=ir_data_type,
                scope=ir_scope,
                description=f"OpenPLC variable: {var.name}",
                initial_value=var.initial_value
            )
            tags.append(tag)
        
        return IRController(
            name=controller_name,
            tags=tags,
            source_type=self.source_type
        )
    
    def _create_program(self, program_name: str, routines: List[Dict[str, Any]]) -> IRProgram:
        """Create IRProgram from OpenPLC routines."""
        # Convert routine dictionaries to IRRoutine objects
        ir_routines = []
        
        for routine_dict in routines:
            routine = IRRoutine(
                name=routine_dict['name'],
                routine_type=RoutineType.ST,
                content=routine_dict['content']
            )
            ir_routines.append(routine)
        
        return IRProgram(
            name=program_name,
            routines=ir_routines,
            source_type=self.source_type
        )
    
    def _map_data_type(self, openplc_type: str) -> str:
        """Map OpenPLC data types to string representation."""
        # Basic type mapping - return string values
        type_mapping = {
            'BOOL': 'BOOL',
            'INT': 'INT',
            'REAL': 'REAL',
            'STRING': 'STRING',
            'TIME': 'TIME',
            'DINT': 'DINT',
            'SINT': 'SINT',
            'LINT': 'LINT',
            'UINT': 'UINT',
            'UDINT': 'UDINT',
            'USINT': 'USINT',
            'ULINT': 'ULINT',
            'LREAL': 'LREAL',
            'WORD': 'WORD',
            'DWORD': 'DWORD',
            'LWORD': 'LWORD',
            'BYTE': 'BYTE',
            'CHAR': 'CHAR'
        }
        
        # Check for array types
        if '[' in openplc_type:
            base_type = openplc_type.split('[')[0].strip()
            if base_type in type_mapping:
                return type_mapping[base_type]
        
        # Return mapped type or default to STRING
        return type_mapping.get(openplc_type.upper(), 'STRING')
    
    def _map_scope(self, openplc_scope: str) -> TagScope:
        """Map OpenPLC scope to IR scope."""
        scope_mapping = {
            'VAR': TagScope.PROGRAM,
            'VAR_INPUT': TagScope.PROGRAM,
            'VAR_OUTPUT': TagScope.PROGRAM,
            'VAR_IN_OUT': TagScope.PROGRAM,
            'VAR_GLOBAL': TagScope.CONTROLLER
        }
        
        return scope_mapping.get(openplc_scope, TagScope.PROGRAM) 