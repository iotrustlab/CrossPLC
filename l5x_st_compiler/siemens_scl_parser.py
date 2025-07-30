"""
Siemens SCL Parser

Parses Siemens SCL files and PLCTags.xml into Intermediate Representation format.
SCL (Structured Control Language) is Siemens' implementation of IEC 61131-3 Structured Text.
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass

from .models import (
    IRProject, IRController, IRProgram, IRRoutine, 
    IRTag, IRDataType, TagScope, IRFunctionBlock, RoutineType, DataType
)

logger = logging.getLogger(__name__)

@dataclass
class SCLVariable:
    """Represents a variable in SCL."""
    name: str
    data_type: str
    scope: str
    initial_value: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None


class SiemensSCLParser:
    """Parser for Siemens SCL files and PLCTags.xml."""
    
    def __init__(self):
        self.source_type = "siemens"
    
    def parse(self, scl_path: Path, tags_xml_path: Optional[Path] = None) -> IRProject:
        """Parse Siemens SCL file and optional PLCTags.xml into IR."""
        logger.info(f"Parsing Siemens SCL file: {scl_path}")
        
        # Read SCL content
        content = scl_path.read_text(encoding='utf-8', errors='ignore')
        
        # Extract controller name from filename
        controller_name = self._extract_controller_name(scl_path)
        
        # Parse SCL content
        variables = self._parse_scl_variables(content)
        routines = self._parse_scl_routines(content)
        
        # Parse PLCTags.xml if provided
        if tags_xml_path and tags_xml_path.exists():
            logger.info(f"Parsing PLCTags.xml: {tags_xml_path}")
            xml_variables = self._parse_plctags_xml(tags_xml_path)
            variables.extend(xml_variables)
        
        logger.info(f"Parsed Siemens SCL file: {len(variables)} variables, {len(routines)} routines")
        
        # Create controller
        controller = self._create_controller(controller_name, variables)
        
        # Create program
        program = self._create_program("Main", routines)
        
        # Create IR project
        ir_project = IRProject(
            controller=controller,
            programs=[program],
            source_type=self.source_type
        )
        
        return ir_project
    
    def _extract_controller_name(self, scl_path: Path) -> str:
        """Extract controller name from SCL file path."""
        # Try to extract from path structure (e.g., TP, IM)
        parent_dir = scl_path.parent.name
        if parent_dir in ['TP', 'IM']:
            return f"Siemens_{parent_dir}"
        
        # Fallback to filename without extension
        return scl_path.stem
    
    def _parse_scl_variables(self, content: str) -> List[SCLVariable]:
        """Parse variable declarations from SCL content."""
        variables = []
        
        # Parse TYPE definitions (user-defined data types)
        type_pattern = r'TYPE\s+"([^"]+)"\s*TITLE\s*=\s*[^;]*?VERSION\s*:\s*[^;]*?STRUCT\s*(.*?)END_STRUCT;?\s*END_TYPE'
        type_matches = re.finditer(type_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for match in type_matches:
            type_name = match.group(1)
            type_content = match.group(2)
            
            # Parse members of the type
            member_pattern = r'(\w+)\s*:\s*([^;]+?)(?:\s*:=\s*([^;]+))?;'
            member_matches = re.finditer(member_pattern, type_content)
            
            for member_match in member_matches:
                member_name = member_match.group(1)
                member_type = member_match.group(2).strip()
                member_value = member_match.group(3) if member_match.group(3) else None
                
                # Handle array types
                if '[' in member_type:
                    base_type = member_type.split('[')[0].strip()
                    member_type = base_type
                
                # Handle user-defined types
                if member_type.startswith('"') and member_type.endswith('"'):
                    member_type = member_type[1:-1]  # Remove quotes
                
                variable = SCLVariable(
                    name=f"{type_name}.{member_name}",
                    data_type=member_type,
                    scope="TYPE",
                    initial_value=member_value,
                    description=f"Member of {type_name}"
                )
                variables.append(variable)
        
        # Fallback: Parse TYPE definitions without TITLE
        type_fallback_pattern = r'TYPE\s+"([^"]+)"\s*VERSION\s*:\s*[^;]*?STRUCT\s*(.*?)END_STRUCT;?\s*END_TYPE'
        type_fallback_matches = re.finditer(type_fallback_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for match in type_fallback_matches:
            type_name = match.group(1)
            type_content = match.group(2)
            
            # Parse members of the type
            member_pattern = r'(\w+)\s*:\s*([^;]+?)(?:\s*:=\s*([^;]+))?;'
            member_matches = re.finditer(member_pattern, type_content)
            
            for member_match in member_matches:
                member_name = member_match.group(1)
                member_type = member_match.group(2).strip()
                member_value = member_match.group(3) if member_match.group(3) else None
                
                # Handle array types
                if '[' in member_type:
                    base_type = member_type.split('[')[0].strip()
                    member_type = base_type
                
                # Handle user-defined types
                if member_type.startswith('"') and member_type.endswith('"'):
                    member_type = member_type[1:-1]  # Remove quotes
                
                variable = SCLVariable(
                    name=f"{type_name}.{member_name}",
                    data_type=member_type,
                    scope="TYPE",
                    initial_value=member_value,
                    description=f"Member of {type_name}"
                )
                variables.append(variable)
        
        # Parse DATA_BLOCK definitions
        db_pattern = r'DATA_BLOCK\s+"([^"]+)"\s*TITLE\s*=\s*[^;]*?{.*?}.*?VERSION\s*:\s*[^;]*?NON_RETAIN\s*STRUCT\s*(.*?)END_STRUCT'
        db_matches = re.finditer(db_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for match in db_matches:
            db_name = match.group(1)
            db_struct_content = match.group(2)
            
            # Parse STRUCT members
            struct_member_pattern = r'(\w+)\s*:\s*([^;]+?)(?:\s*:=\s*([^;]+))?;'
            struct_matches = re.finditer(struct_member_pattern, db_struct_content)
            
            for struct_match in struct_matches:
                member_name = struct_match.group(1)
                member_type = struct_match.group(2).strip()
                member_value = struct_match.group(3) if struct_match.group(3) else None
                
                # Handle array types
                member_type = self._clean_data_type(member_type)
                
                variable = SCLVariable(
                    name=f"{db_name}.{member_name}",
                    data_type=member_type,
                    scope="DATA_BLOCK",
                    initial_value=member_value,
                    description=f"Member of data block {db_name}"
                )
                variables.append(variable)
        
        # Fallback: Parse DATA_BLOCK without STRUCT (simple format)
        db_simple_pattern = r'DATA_BLOCK\s+"([^"]+)"\s*{.*?}.*?VERSION\s*:\s*[^;]*?NON_RETAIN\s*"([^"]+)"\s*BEGIN\s*(.*?)END_DATA_BLOCK'
        db_simple_matches = re.finditer(db_simple_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for match in db_simple_matches:
            db_name = match.group(1)
            db_type = match.group(2)
            db_content = match.group(3)
            
            # Create a variable for the data block
            variable = SCLVariable(
                name=db_name,
                data_type=db_type,
                scope="DATA_BLOCK",
                description=f"Siemens data block: {db_name}"
            )
            variables.append(variable)
        
        # Parse FUNCTION_BLOCK definitions and their variables
        fb_pattern = r'FUNCTION_BLOCK\s+"([^"]+)"\s*TITLE\s*=\s*[^;]*?{.*?}.*?VERSION\s*:\s*[^;]*?VAR_INPUT\s*(.*?)END_VAR'
        fb_matches = re.finditer(fb_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for match in fb_matches:
            fb_name = match.group(1)
            var_input_content = match.group(2)
            
            # Parse VAR_INPUT variables
            var_pattern = r'(\w+)\s*:\s*([^;]+?)(?:\s*:=\s*([^;]+))?;'
            var_matches = re.finditer(var_pattern, var_input_content)
            
            for var_match in var_matches:
                var_name = var_match.group(1)
                var_type = var_match.group(2).strip()
                var_value = var_match.group(3) if var_match.group(3) else None
                
                # Skip Siemens-specific attributes
                if var_name.startswith('S7_'):
                    continue
                
                # Handle array types and complex types
                var_type = self._clean_data_type(var_type)
                
                # Skip if it's just an attribute
                if var_type == "ATTRIBUTE":
                    continue
                
                variable = SCLVariable(
                    name=f"{fb_name}.{var_name}",
                    data_type=var_type,
                    scope="FUNCTION_BLOCK_INPUT",
                    initial_value=var_value,
                    description=f"Input variable of {fb_name}"
                )
                variables.append(variable)
        
        # Parse VAR_OUTPUT sections
        fb_output_pattern = r'FUNCTION_BLOCK\s+"([^"]+)"\s*TITLE\s*=\s*[^;]*?{.*?}.*?VERSION\s*:\s*[^;]*?VAR_OUTPUT\s*(.*?)END_VAR'
        fb_output_matches = re.finditer(fb_output_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for match in fb_output_matches:
            fb_name = match.group(1)
            var_output_content = match.group(2)
            
            # Parse VAR_OUTPUT variables
            var_pattern = r'(\w+)\s*:\s*([^;]+?)(?:\s*:=\s*([^;]+))?;'
            var_matches = re.finditer(var_pattern, var_output_content)
            
            for var_match in var_matches:
                var_name = var_match.group(1)
                var_type = var_match.group(2).strip()
                var_value = var_match.group(3) if var_match.group(3) else None
                
                # Skip Siemens-specific attributes
                if var_name.startswith('S7_'):
                    continue
                
                var_type = self._clean_data_type(var_type)
                
                # Skip if it's just an attribute
                if var_type == "ATTRIBUTE":
                    continue
                
                variable = SCLVariable(
                    name=f"{fb_name}.{var_name}",
                    data_type=var_type,
                    scope="FUNCTION_BLOCK_OUTPUT",
                    initial_value=var_value,
                    description=f"Output variable of {fb_name}"
                )
                variables.append(variable)
        
        # Parse VAR sections (local variables)
        fb_var_pattern = r'FUNCTION_BLOCK\s+"([^"]+)"\s*TITLE\s*=\s*[^;]*?{.*?}.*?VERSION\s*:\s*[^;]*?VAR\s*(.*?)END_VAR'
        fb_var_matches = re.finditer(fb_var_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for match in fb_var_matches:
            fb_name = match.group(1)
            var_content = match.group(2)
            
            # Parse VAR variables
            var_pattern = r'(\w+)\s*:\s*([^;]+?)(?:\s*:=\s*([^;]+))?;'
            var_matches = re.finditer(var_pattern, var_content)
            
            for var_match in var_matches:
                var_name = var_match.group(1)
                var_type = var_match.group(2).strip()
                var_value = var_match.group(3) if var_match.group(3) else None
                
                # Skip Siemens-specific attributes
                if var_name.startswith('S7_'):
                    continue
                
                var_type = self._clean_data_type(var_type)
                
                # Skip if it's just an attribute
                if var_type == "ATTRIBUTE":
                    continue
                
                variable = SCLVariable(
                    name=f"{fb_name}.{var_name}",
                    data_type=var_type,
                    scope="FUNCTION_BLOCK_LOCAL",
                    initial_value=var_value,
                    description=f"Local variable of {fb_name}"
                )
                variables.append(variable)
        
        # Parse VAR_TEMP sections (temporary variables)
        fb_temp_pattern = r'FUNCTION_BLOCK\s+"([^"]+)"\s*TITLE\s*=\s*[^;]*?{.*?}.*?VERSION\s*:\s*[^;]*?VAR_TEMP\s*(.*?)END_VAR'
        fb_temp_matches = re.finditer(fb_temp_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for match in fb_temp_matches:
            fb_name = match.group(1)
            temp_content = match.group(2)
            
            # Parse VAR_TEMP variables
            var_pattern = r'(\w+)\s*:\s*([^;]+?)(?:\s*:=\s*([^;]+))?;'
            var_matches = re.finditer(var_pattern, temp_content)
            
            for var_match in var_matches:
                var_name = var_match.group(1)
                var_type = var_match.group(2).strip()
                var_value = var_match.group(3) if var_match.group(3) else None
                
                var_type = self._clean_data_type(var_type)
                
                variable = SCLVariable(
                    name=f"{fb_name}.{var_name}",
                    data_type=var_type,
                    scope="FUNCTION_BLOCK_TEMP",
                    initial_value=var_value,
                    description=f"Temporary variable of {fb_name}"
                )
                variables.append(variable)
        
        # Parse VAR_IN_OUT sections (in-out variables)
        fb_inout_pattern = r'FUNCTION_BLOCK\s+"([^"]+)"\s*TITLE\s*=\s*[^;]*?{.*?}.*?VERSION\s*:\s*[^;]*?VAR_IN_OUT\s*(.*?)END_VAR'
        fb_inout_matches = re.finditer(fb_inout_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for match in fb_inout_matches:
            fb_name = match.group(1)
            inout_content = match.group(2)
            
            # Parse VAR_IN_OUT variables
            var_pattern = r'(\w+)\s*:\s*([^;]+?)(?:\s*:=\s*([^;]+))?;'
            var_matches = re.finditer(var_pattern, inout_content)
            
            for var_match in var_matches:
                var_name = var_match.group(1)
                var_type = var_match.group(2).strip()
                var_value = var_match.group(3) if var_match.group(3) else None
                
                var_type = self._clean_data_type(var_type)
                
                variable = SCLVariable(
                    name=f"{fb_name}.{var_name}",
                    data_type=var_type,
                    scope="FUNCTION_BLOCK_INOUT",
                    initial_value=var_value,
                    description=f"In-out variable of {fb_name}"
                )
                variables.append(variable)
        
        # Parse CONST sections (constants)
        fb_const_pattern = r'FUNCTION_BLOCK\s+"([^"]+)"\s*TITLE\s*=\s*[^;]*?{.*?}.*?VERSION\s*:\s*[^;]*?CONST\s*(.*?)END_CONST'
        fb_const_matches = re.finditer(fb_const_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for match in fb_const_matches:
            fb_name = match.group(1)
            const_content = match.group(2)
            
            # Parse CONST variables
            var_pattern = r'(\w+)\s*:=\s*([^;]+?);'
            var_matches = re.finditer(var_pattern, const_content)
            
            for var_match in var_matches:
                var_name = var_match.group(1)
                var_value = var_match.group(2).strip()
                
                variable = SCLVariable(
                    name=f"{fb_name}.{var_name}",
                    data_type="CONST",
                    scope="FUNCTION_BLOCK_CONST",
                    initial_value=var_value,
                    description=f"Constant of {fb_name}"
                )
                variables.append(variable)
        
        return variables
    
    def _clean_data_type(self, data_type: str) -> str:
        """Clean and standardize data type strings."""
        # Remove comments
        if '//' in data_type:
            data_type = data_type.split('//')[0].strip()
        
        # Handle array types
        if '[' in data_type:
            base_type = data_type.split('[')[0].strip()
            return base_type
        
        # Handle user-defined types (quoted)
        if data_type.startswith('"') and data_type.endswith('"'):
            return data_type[1:-1]
        
        # Handle AT references (hardware mapping)
        if ' AT ' in data_type:
            base_type = data_type.split(' AT ')[0].strip()
            return base_type
        
        # Handle Siemens-specific attributes (S7_HMI_*, etc.)
        if data_type.startswith('S7_') or data_type.startswith('= '):
            return "ATTRIBUTE"
        
        # Handle complex type definitions with attributes
        if '{' in data_type and '}' in data_type:
            # Extract the actual type from complex definitions
            # Example: "S7_HMI_Accessible := 'False'; S7_HMI_Visible := 'False'} : Byte"
            parts = data_type.split('} : ')
            if len(parts) > 1:
                return parts[1].strip()
            else:
                return "COMPLEX_TYPE"
        
        return data_type.strip()
    
    def _parse_scl_routines(self, content: str) -> List[Dict[str, Any]]:
        """Parse routine definitions from SCL content."""
        routines = []
        
        # Parse ORGANIZATION_BLOCK (main program)
        ob_pattern = r'ORGANIZATION_BLOCK\s+"([^"]+)"\s*TITLE\s*=\s*"([^"]*)"\s*{.*?}.*?VERSION\s*:\s*[^;]*?BEGIN\s*(.*?)END_ORGANIZATION_BLOCK'
        ob_matches = re.finditer(ob_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for match in ob_matches:
            ob_name = match.group(1)
            ob_title = match.group(2)
            ob_content = match.group(3)
            
            routine = {
                'name': ob_name,
                'routine_type': 'ST',  # SCL is essentially ST
                'content': ob_content.strip(),
                'description': ob_title
            }
            routines.append(routine)
        
        # Parse FUNCTION_BLOCK (function blocks)
        fb_pattern = r'FUNCTION_BLOCK\s+"([^"]+)"\s*TITLE\s*=\s*[^;]*?{.*?}.*?VERSION\s*:\s*[^;]*?BEGIN\s*(.*?)END_FUNCTION_BLOCK'
        fb_matches = re.finditer(fb_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for match in fb_matches:
            fb_name = match.group(1)
            fb_content = match.group(2)
            
            routine = {
                'name': fb_name,
                'routine_type': 'ST',  # SCL is essentially ST
                'content': fb_content.strip(),
                'description': f'Siemens SCL function block: {fb_name}'
            }
            routines.append(routine)
        
        # Parse FUNCTION (functions)
        func_pattern = r'FUNCTION\s+"([^"]+)"\s*:\s*([^;]*?)\s*TITLE\s*=\s*[^;]*?{.*?}.*?VERSION\s*:\s*[^;]*?BEGIN\s*(.*?)END_FUNCTION'
        func_matches = re.finditer(func_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for match in func_matches:
            func_name = match.group(1)
            func_return_type = match.group(2).strip()
            func_content = match.group(3)
            
            routine = {
                'name': func_name,
                'routine_type': 'ST',  # SCL is essentially ST
                'content': func_content.strip(),
                'description': f'Siemens SCL function: {func_name} -> {func_return_type}'
            }
            routines.append(routine)
        
        # If no ORGANIZATION_BLOCK or FUNCTION_BLOCK found, treat the entire content as a main routine
        if not routines:
            routine = {
                'name': 'Main',
                'routine_type': 'ST',
                'content': content,
                'description': 'Siemens SCL main program'
            }
            routines.append(routine)
        
        return routines
    
    def _parse_plctags_xml(self, xml_path: Path) -> List[SCLVariable]:
        """Parse PLCTags.xml file to extract I/O variables."""
        variables = []
        
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            for tag_elem in root.findall('.//Tag'):
                tag_name = tag_elem.text
                tag_type = tag_elem.get('type', 'Unknown')
                tag_addr = tag_elem.get('addr', '')
                tag_remark = tag_elem.get('remark', '')
                
                # Map Siemens types to standard types
                mapped_type = self._map_siemens_data_type(tag_type)
                
                variable = SCLVariable(
                    name=tag_name,
                    data_type=mapped_type,
                    scope="I/O",
                    description=tag_remark,
                    address=tag_addr
                )
                variables.append(variable)
                
        except Exception as e:
            logger.warning(f"Error parsing PLCTags.xml: {e}")
        
        return variables
    
    def _map_siemens_data_type(self, siemens_type: str) -> str:
        """Map Siemens data types to standard types based on SCL grammar."""
        type_mapping = {
            # Basic types from SCL grammar
            'BOOL': 'BOOL',
            'BYTE': 'BYTE',
            'CHAR': 'CHAR',
            'STRING': 'STRING',
            'WORD': 'WORD',
            'DWORD': 'DWORD',
            'INT': 'INT',
            'DINT': 'DINT',
            'REAL': 'REAL',
            'S5TIME': 'TIME',
            'TIME': 'TIME',
            'Date': 'DATE',
            'TIME_OF_DAY': 'TIME_OF_DAY',
            'DATE_AND_TIME': 'DATE_AND_TIME',
            
            # Siemens-specific variations
            'Bool': 'BOOL',
            'Int': 'INT',
            'Word': 'WORD',
            'DWord': 'DWORD',
            'Real': 'REAL',
            'String': 'STRING',
            'TimeOfDay': 'TIME_OF_DAY',
            'DateAndTime': 'DATE_AND_TIME',
            'LDT': 'DATE_AND_TIME',  # Local Date Time
            'LInt': 'LINT',
            'UInt': 'UINT',
            'UDInt': 'UDINT',
            'ULInt': 'ULINT',
            'LReal': 'LREAL',
            'Byte': 'BYTE',
            'Char': 'CHAR'
        }
        
        return type_mapping.get(siemens_type, siemens_type.upper())
    
    def _create_controller(self, controller_name: str, variables: List[SCLVariable]) -> IRController:
        """Create IR controller from SCL variables."""
        tags = []
        
        for var in variables:
            # Map scope
            scope = self._map_scope(var.scope)
            
            # Create IR tag
            tag = IRTag(
                name=var.name,
                data_type=var.data_type,
                scope=scope,
                value=var.initial_value,
                description=var.description,
                external_access=var.address
            )
            tags.append(tag)
        
        return IRController(
            name=controller_name,
            tags=tags,
            source_type=self.source_type
        )
    
    def _create_program(self, program_name: str, routines: List[Dict[str, Any]]) -> IRProgram:
        """Create IR program from SCL routines."""
        ir_routines = []
        
        for routine_dict in routines:
            routine = IRRoutine(
                name=routine_dict['name'],
                routine_type=RoutineType.ST,
                content=routine_dict['content'],
                description=routine_dict.get('description')
            )
            ir_routines.append(routine)
        
        return IRProgram(
            name=program_name,
            routines=ir_routines,
            source_type=self.source_type
        )
    
    def _map_scope(self, scl_scope: str) -> TagScope:
        """Map SCL scope to IR scope."""
        scope_mapping = {
            'TYPE': TagScope.CONTROLLER,
            'DATA_BLOCK': TagScope.CONTROLLER,
            'I/O': TagScope.CONTROLLER
        }
        return scope_mapping.get(scl_scope, TagScope.CONTROLLER) 