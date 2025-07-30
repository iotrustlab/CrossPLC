"""
Siemens LAD/FBD Parser

Parses Siemens Ladder Logic (LAD) and Function Block Diagram (FBD) projects
into Intermediate Representation format.
"""

import re
import logging
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
import xml.etree.ElementTree as ET

from .models import (
    IRProject, IRController, IRProgram, IRRoutine, 
    IRTag, IRDataType, TagScope, IRFunctionBlock, RoutineType, DataType
)

logger = logging.getLogger(__name__)

@dataclass
class LADBlock:
    """Represents a LAD/FBD logic block."""
    id: str
    type: str
    inputs: List[str]
    outputs: List[str]
    language: str  # 'LAD' or 'FBD'
    description: Optional[str] = None

@dataclass
class LADConnection:
    """Represents a connection between LAD/FBD blocks."""
    from_block: str
    from_pin: str
    to_block: str
    to_pin: str

class SiemensLADParser:
    """Parser for Siemens LAD/FBD projects."""
    
    def __init__(self):
        self.source_type = "siemens_lad"
    
    def detect_language_type(self, xml_file: str) -> str:
        """Detect language type from XML metadata."""
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # Look for language indicators in XML
            xml_content = ET.tostring(root, encoding='unicode')
            
            if 'LAD' in xml_content.upper() or 'LADDER' in xml_content.upper():
                return 'LAD'
            elif 'FBD' in xml_content.upper() or 'FUNCTION_BLOCK' in xml_content.upper():
                return 'FBD'
            elif 'SCL' in xml_content.upper() or 'STRUCTURED_TEXT' in xml_content.upper():
                return 'SCL'
            else:
                # Default to LAD for unknown types
                return 'LAD'
                
        except Exception as e:
            logger.warning(f"Error detecting language type for {xml_file}: {e}")
            return 'LAD'
    
    def extract_lad_blocks(self, xml_file: str) -> List[Dict]:
        """Extract LAD/FBD blocks from XML file."""
        blocks = []
        
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # Try to find block elements in the XML
            # This is a simplified approach - real implementation would need
            # to understand the specific Siemens XML schema
            
            # Look for common Siemens block patterns
            xml_content = ET.tostring(root, encoding='unicode')
            
            # Extract potential blocks using regex patterns
            # This is a basic implementation - would need enhancement for real projects
            
            # Look for block-like structures
            block_patterns = [
                r'<(\w+)Block[^>]*>',
                r'<(\w+)Function[^>]*>',
                r'<(\w+)Timer[^>]*>',
                r'<(\w+)Counter[^>]*>'
            ]
            
            for pattern in block_patterns:
                matches = re.finditer(pattern, xml_content, re.IGNORECASE)
                for i, match in enumerate(matches):
                    block_type = match.group(1)
                    
                    # Create a basic block representation
                    block = {
                        "id": f"B{i+1}",
                        "type": block_type.upper(),
                        "inputs": ["IN"],  # Default inputs
                        "outputs": ["OUT"],  # Default outputs
                        "language": self.detect_language_type(xml_file)
                    }
                    blocks.append(block)
            
            # If no blocks found, create a placeholder
            if not blocks:
                block = {
                    "id": "B1",
                    "type": "UNKNOWN",
                    "inputs": ["IN"],
                    "outputs": ["OUT"],
                    "language": self.detect_language_type(xml_file)
                }
                blocks.append(block)
                
        except Exception as e:
            logger.warning(f"Error extracting LAD blocks from {xml_file}: {e}")
            # Create a fallback block
            block = {
                "id": "B1",
                "type": "ERROR",
                "inputs": ["IN"],
                "outputs": ["OUT"],
                "language": "LAD"
            }
            blocks.append(block)
        
        return blocks
    
    def parse_project(self, project_path: Path) -> IRProject:
        """Parse a Siemens LAD/FBD project into IR."""
        logger.info(f"Parsing Siemens LAD/FBD project: {project_path}")
        
        # Extract project if it's a .zap file
        if project_path.suffix.lower().startswith('.zap'):
            with tempfile.TemporaryDirectory() as temp_dir:
                extract_dir = Path(temp_dir)
                self._extract_zap_project(project_path, extract_dir)
                return self._parse_extracted_project(extract_dir, project_path.name)
        else:
            return self._parse_extracted_project(project_path, project_path.name)
    
    def _extract_zap_project(self, zap_file: Path, extract_dir: Path):
        """Extract a .zap project file."""
        import zipfile
        with zipfile.ZipFile(zap_file, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
    
    def _parse_extracted_project(self, extract_dir: Path, project_name: str) -> IRProject:
        """Parse an extracted Siemens project."""
        blocks = []
        connections = []
        
        # Look for XML files that might contain program blocks
        xml_files = list(extract_dir.glob("**/*.xml"))
        
        for xml_file in xml_files:
            # Skip system and log files
            if any(skip_dir in str(xml_file) for skip_dir in ['System', 'Logs', 'XRef', 'Vci']):
                continue
            
            try:
                file_blocks = self.extract_lad_blocks(str(xml_file))
                blocks.extend(file_blocks)
                
                # Extract connections (simplified)
                file_connections = self._extract_connections(str(xml_file))
                connections.extend(file_connections)
                
            except Exception as e:
                logger.warning(f"Error parsing {xml_file}: {e}")
        
        # Create IR project
        controller = self._create_controller(project_name, blocks)
        program = self._create_program("Main", blocks, connections)
        
        return IRProject(
            controller=controller,
            programs=[program],
            source_type=self.source_type
        )
    
    def _extract_connections(self, xml_file: str) -> List[LADConnection]:
        """Extract connections between blocks."""
        connections = []
        
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # This is a simplified implementation
            # Real implementation would need to understand Siemens connection XML schema
            
            # Look for connection patterns in XML
            xml_content = ET.tostring(root, encoding='unicode')
            
            # Basic connection pattern matching
            connection_patterns = [
                r'<Connection[^>]*from="([^"]+)"[^>]*to="([^"]+)"',
                r'<Wire[^>]*from="([^"]+)"[^>]*to="([^"]+)"'
            ]
            
            for pattern in connection_patterns:
                matches = re.finditer(pattern, xml_content, re.IGNORECASE)
                for match in matches:
                    from_block = match.group(1)
                    to_block = match.group(2)
                    
                    connection = LADConnection(
                        from_block=from_block,
                        from_pin="OUT",
                        to_block=to_block,
                        to_pin="IN"
                    )
                    connections.append(connection)
                    
        except Exception as e:
            logger.warning(f"Error extracting connections from {xml_file}: {e}")
        
        return connections
    
    def _create_controller(self, controller_name: str, blocks: List[Dict]) -> IRController:
        """Create IR controller from LAD blocks."""
        tags = []
        
        # Extract I/O from blocks
        for block in blocks:
            for input_pin in block.get('inputs', []):
                tag = IRTag(
                    name=f"{block['id']}.{input_pin}",
                    data_type="BOOL",
                    scope=TagScope.CONTROLLER,
                    description=f"Input {input_pin} of {block['type']} block {block['id']}"
                )
                tags.append(tag)
            
            for output_pin in block.get('outputs', []):
                tag = IRTag(
                    name=f"{block['id']}.{output_pin}",
                    data_type="BOOL",
                    scope=TagScope.CONTROLLER,
                    description=f"Output {output_pin} of {block['type']} block {block['id']}"
                )
                tags.append(tag)
        
        return IRController(
            name=controller_name,
            tags=tags,
            source_type=self.source_type
        )
    
    def _create_program(self, program_name: str, blocks: List[Dict], connections: List[LADConnection]) -> IRProgram:
        """Create IR program from LAD blocks and connections."""
        # Create a simple routine representation
        routine_content = self._generate_routine_content(blocks, connections)
        
        routine = IRRoutine(
            name=program_name,
            routine_type=RoutineType.LAD,  # New type for LAD
            content=routine_content,
            description=f"Siemens LAD/FBD program with {len(blocks)} blocks"
        )
        
        return IRProgram(
            name=program_name,
            routines=[routine],
            source_type=self.source_type
        )
    
    def _generate_routine_content(self, blocks: List[Dict], connections: List[LADConnection]) -> str:
        """Generate a text representation of the LAD/FBD program."""
        content_lines = []
        
        for block in blocks:
            content_lines.append(f"Block {block['id']}: {block['type']}")
            content_lines.append(f"  Inputs: {', '.join(block.get('inputs', []))}")
            content_lines.append(f"  Outputs: {', '.join(block.get('outputs', []))}")
            content_lines.append("")
        
        if connections:
            content_lines.append("Connections:")
            for conn in connections:
                content_lines.append(f"  {conn.from_block}.{conn.from_pin} -> {conn.to_block}.{conn.to_pin}")
        
        return "\n".join(content_lines) 