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
        type_pattern = r'TYPE\s+"([^"]+)"\s*VERSION\s*:\s*[^;]*?STRUCT\s*(.*?)END_STRUCT;?\s*END_TYPE'
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
        
        # Parse DATA_BLOCK definitions
        db_pattern = r'DATA_BLOCK\s+"([^"]+)"\s*{.*?}.*?VERSION\s*:\s*[^;]*?NON_RETAIN\s*"([^"]+)"\s*BEGIN\s*(.*?)END_DATA_BLOCK'
        db_matches = re.finditer(db_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for match in db_matches:
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
        
        return variables
    
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
        
        # If no ORGANIZATION_BLOCK found, treat the entire content as a main routine
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
        """Map Siemens data types to standard types."""
        type_mapping = {
            'Bool': 'BOOL',
            'Int': 'INT',
            'Word': 'WORD',
            'DWord': 'DWORD',
            'Real': 'REAL',
            'String': 'STRING',
            'Time': 'TIME',
            'Date': 'DATE',
            'TimeOfDay': 'TIME_OF_DAY',
            'DateAndTime': 'DATE_AND_TIME',
            'LDT': 'DATE_AND_TIME',  # Local Date Time
            'DInt': 'DINT',
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