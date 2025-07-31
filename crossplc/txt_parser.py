"""
Fischertechnik TXT Parser

Parses Fischertechnik TXT C++ control logic into Intermediate Representation format.
Based on patterns found in the txt_training_factory repository.
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from datetime import datetime

from .models import (
    IRProject, IRController, IRProgram, IRRoutine, 
    IRTag, IRDataType, TagScope, IRFunctionBlock, RoutineType, DataType
)

logger = logging.getLogger(__name__)

@dataclass
class TXTTag:
    """Represents a TXT control logic tag (input/output/internal)."""
    name: str
    tag_type: str  # 'input', 'output', 'internal'
    data_type: str
    description: Optional[str] = None
    initial_value: Optional[str] = None

@dataclass
class TXTInstruction:
    """Represents a TXT control logic instruction."""
    instruction_type: str  # 'assignment', 'function_call', 'conditional', 'loop', 'sleep', 'motor_control'
    content: str
    line_number: int
    description: Optional[str] = None

class TXTParser:
    """Parser for Fischertechnik TXT C++ control logic."""
    
    def __init__(self):
        self.source_type = "fischertechnik_txt"
        
        # TXT-specific control logic patterns from the repository
        self.input_patterns = [
            r'isSwitchPressed\s*\(\s*([^)]+)\s*\)',
            r'pT->pTArea->ftX1in\.uni\[([^\]]+)\]',
            r'read_sensor\s*\(\s*([^)]+)\s*\)',
            r'get_input\s*\(\s*([^)]+)\s*\)'
        ]
        
        self.output_patterns = [
            r'setMotorOff\s*\(\s*\)',
            r'setMotorLeft\s*\(\s*\)',
            r'setMotorRight\s*\(\s*\)',
            r'pT->pTArea->ftX1out\.duty\[([^\]]+)\]\s*=\s*([^;]+)',
            r'set_output\s*\(\s*([^,]+)\s*,\s*([^)]+)\s*\)',
            r'setSpeed\s*\(\s*([^)]+)\s*\)'
        ]
        
        self.sleep_patterns = [
            r'std::this_thread::sleep_for\s*\(\s*std::chrono::milliseconds\s*\(\s*([^)]+)\s*\)\s*\)',
            r'sleep\s*\(\s*([^)]+)\s*\)',
            r'time\.sleep\s*\(\s*([^)]+)\s*\)'
        ]
        
        self.control_flow_patterns = [
            r'if\s*\(([^)]+)\)',
            r'while\s*\(([^)]+)\)',
            r'for\s*\(([^)]+)\)',
            r'switch\s*\(([^)]+)\)',
            r'case\s+([^:]+):',
            r'FSM_TRANSITION\s*\(\s*([^,]+)\s*,\s*[^)]*\)'
        ]
        
        self.state_patterns = [
            r'IDLE',
            r'FAULT',
            r'INIT',
            r'FETCH_WP',
            r'STORE_WP',
            r'CALIB_HBW',
            r'RUNNING',
            r'STOPPED',
            r'ERROR'
        ]
        
        self.motor_control_patterns = [
            r'setMotorOff\s*\(\s*\)',
            r'setMotorLeft\s*\(\s*\)',
            r'setMotorRight\s*\(\s*\)',
            r'setSpeed\s*\(\s*([^)]+)\s*\)'
        ]
    
    def parse_txt_file(self, filepath: str) -> IRProject:
        """Parse a TXT C++ control logic file into IR."""
        logger.info(f"Parsing TXT control logic file: {filepath}")
        
        file_path = Path(filepath)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        # Parse the content
        return self._parse_content(content, file_path.name)
    
    def _parse_content(self, content: str, filename: str) -> IRProject:
        """Parse TXT control logic content into IR."""
        tags = []
        instructions = []
        
        # Extract tags from content
        tags.extend(self._extract_input_tags(content))
        tags.extend(self._extract_output_tags(content))
        tags.extend(self._extract_internal_tags(content))
        
        # Extract instructions
        instructions.extend(self._extract_instructions(content))
        
        # Create IR project
        controller = self._create_controller(filename, tags)
        program = self._create_program("Main", instructions, tags)
        
        return IRProject(
            controller=controller,
            programs=[program],
            source_type=self.source_type
        )
    
    def _extract_input_tags(self, content: str) -> List[TXTTag]:
        """Extract input tags from TXT control logic content."""
        tags = []
        
        for pattern in self.input_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                tag_name = match.group(1).strip()
                # Clean up tag name
                tag_name = re.sub(r'["\']', '', tag_name)
                
                tag = TXTTag(
                    name=tag_name,
                    tag_type="input",
                    data_type="BOOL",  # Default to BOOL for inputs
                    description=f"TXT input tag: {tag_name}"
                )
                tags.append(tag)
        
        return tags
    
    def _extract_output_tags(self, content: str) -> List[TXTTag]:
        """Extract output tags from TXT control logic content."""
        tags = []
        
        for pattern in self.output_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                if 'set_output' in pattern:
                    tag_name = match.group(1).strip()
                    tag_value = match.group(2).strip()
                elif 'setMotor' in pattern:
                    tag_name = f"motor_{len(tags)}"
                    tag_value = "0"  # Default value
                elif 'setSpeed' in pattern:
                    tag_name = f"speed_{len(tags)}"
                    tag_value = match.group(1).strip()
                else:
                    tag_name = match.group(1).strip()
                    tag_value = match.group(2).strip()
                
                # Clean up tag name
                tag_name = re.sub(r'["\']', '', tag_name)
                
                tag = TXTTag(
                    name=tag_name,
                    tag_type="output",
                    data_type="BOOL",  # Default to BOOL for outputs
                    description=f"TXT output tag: {tag_name}",
                    initial_value=tag_value
                )
                tags.append(tag)
        
        return tags
    
    def _extract_internal_tags(self, content: str) -> List[TXTTag]:
        """Extract internal variables/tags from TXT control logic content."""
        tags = []
        
        # Look for variable declarations and assignments
        var_patterns = [
            r'(\w+)\s*=\s*([^;]+);',  # C++ assignment
            r'(\w+)\s*:\s*([^;]+);',  # Type declaration
            r'int\s+(\w+)\s*=\s*([^;]+);',  # int declaration
            r'bool\s+(\w+)\s*=\s*([^;]+);',  # bool declaration
            r'std::string\s+(\w+)\s*=\s*([^;]+);',  # string declaration
        ]
        
        for pattern in var_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                var_name = match.group(1).strip()
                var_value = match.group(2).strip()
                
                # Skip common keywords and function names
                if var_name in ['if', 'while', 'for', 'switch', 'case', 'return', 'break', 'continue']:
                    continue
                
                # Determine data type
                data_type = self._infer_data_type(var_value)
                
                tag = TXTTag(
                    name=var_name,
                    tag_type="internal",
                    data_type=data_type,
                    description=f"TXT internal variable: {var_name}",
                    initial_value=var_value
                )
                tags.append(tag)
        
        return tags
    
    def _infer_data_type(self, value: str) -> str:
        """Infer data type from value."""
        value = value.strip()
        
        if value.lower() in ['true', 'false']:
            return "BOOL"
        elif value.isdigit():
            return "INT"
        elif re.match(r'\d+\.\d+', value):
            return "REAL"
        elif value.startswith('"') or value.startswith("'"):
            return "STRING"
        else:
            return "BOOL"  # Default to BOOL
    
    def _extract_instructions(self, content: str) -> List[TXTInstruction]:
        """Extract TXT control logic instructions."""
        instructions = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('//') or line.startswith('#'):
                continue
            
            # Detect instruction types
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in self.input_patterns):
                instructions.append(TXTInstruction(
                    instruction_type="input_read",
                    content=line,
                    line_number=line_num,
                    description="TXT input reading operation"
                ))
            elif any(re.search(pattern, line, re.IGNORECASE) for pattern in self.output_patterns):
                instructions.append(TXTInstruction(
                    instruction_type="output_set",
                    content=line,
                    line_number=line_num,
                    description="TXT output setting operation"
                ))
            elif any(re.search(pattern, line, re.IGNORECASE) for pattern in self.motor_control_patterns):
                instructions.append(TXTInstruction(
                    instruction_type="motor_control",
                    content=line,
                    line_number=line_num,
                    description="TXT motor control operation"
                ))
            elif any(re.search(pattern, line, re.IGNORECASE) for pattern in self.sleep_patterns):
                instructions.append(TXTInstruction(
                    instruction_type="sleep",
                    content=line,
                    line_number=line_num,
                    description="TXT timing/sleep operation"
                ))
            elif any(re.search(pattern, line, re.IGNORECASE) for pattern in self.control_flow_patterns):
                instructions.append(TXTInstruction(
                    instruction_type="control_flow",
                    content=line,
                    line_number=line_num,
                    description="TXT control flow statement"
                ))
            elif '=' in line and not line.startswith('//'):
                instructions.append(TXTInstruction(
                    instruction_type="assignment",
                    content=line,
                    line_number=line_num,
                    description="TXT variable assignment"
                ))
            elif '(' in line and ')' in line:
                instructions.append(TXTInstruction(
                    instruction_type="function_call",
                    content=line,
                    line_number=line_num,
                    description="TXT function call"
                ))
        
        return instructions
    
    def _create_controller(self, controller_name: str, tags: List[TXTTag]) -> IRController:
        """Create IR controller from TXT tags."""
        ir_tags = []
        
        for tag in tags:
            ir_tag = IRTag(
                name=tag.name,
                data_type=tag.data_type,
                scope=TagScope.CONTROLLER,
                description=tag.description,
                initial_value=tag.initial_value
            )
            ir_tags.append(ir_tag)
        
        return IRController(
            name=controller_name,
            tags=ir_tags,
            source_type=self.source_type
        )
    
    def _create_program(self, program_name: str, instructions: List[TXTInstruction], tags: List[TXTTag]) -> IRProgram:
        """Create IR program from TXT instructions."""
        # Generate routine content
        content_lines = []
        
        # Add tag declarations
        input_tags = [tag for tag in tags if tag.tag_type == "input"]
        output_tags = [tag for tag in tags if tag.tag_type == "output"]
        internal_tags = [tag for tag in tags if tag.tag_type == "internal"]
        
        if input_tags:
            content_lines.append("// TXT Input Tags:")
            for tag in input_tags:
                content_lines.append(f"//   {tag.name}: {tag.data_type}")
            content_lines.append("")
        
        if output_tags:
            content_lines.append("// TXT Output Tags:")
            for tag in output_tags:
                content_lines.append(f"//   {tag.name}: {tag.data_type}")
            content_lines.append("")
        
        if internal_tags:
            content_lines.append("// TXT Internal Variables:")
            for tag in internal_tags:
                content_lines.append(f"//   {tag.name}: {tag.data_type}")
            content_lines.append("")
        
        # Add instructions
        content_lines.append("// TXT Control Logic Instructions:")
        for instruction in instructions:
            content_lines.append(f"// Line {instruction.line_number}: {instruction.content}")
        
        routine_content = "\n".join(content_lines)
        
        routine = IRRoutine(
            name=program_name,
            routine_type=RoutineType.ST,  # Use ST as closest equivalent
            content=routine_content,
            description=f"Fischertechnik TXT control logic program with {len(instructions)} instructions"
        )
        
        return IRProgram(
            name=program_name,
            routines=[routine],
            source_type=self.source_type
        ) 