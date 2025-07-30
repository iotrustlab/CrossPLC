"""
Function Block Diagram (FBD) to Structured Text (ST) Translator

This module translates Rockwell FBD programs to ST code by parsing the XML structure
and converting the graphical connections to equivalent ST statements.
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple, Optional, Set
import logging

logger = logging.getLogger(__name__)


class FBDTranslator:
    """Translates FBD (Function Block Diagram) to Structured Text."""
    
    def __init__(self):
        self.input_refs: Dict[str, str] = {}  # ID -> Operand
        self.output_refs: Dict[str, str] = {}  # ID -> Operand
        self.function_blocks: Dict[str, Dict] = {}  # ID -> FB info
        self.wires: List[Dict] = []  # Wire connections
        self.execution_order: List[str] = []  # Execution order of FBs
        
    def parse_fbd_content(self, fbd_content: ET.Element) -> str:
        """Parse FBD content and convert to ST code."""
        try:
            # Clear previous data
            self.input_refs.clear()
            self.output_refs.clear()
            self.function_blocks.clear()
            self.wires.clear()
            self.execution_order.clear()
            
            # Parse all sheets in the FBD
            sheets = fbd_content.findall('Sheet')
            st_code = []
            
            for sheet_num, sheet in enumerate(sheets, 1):
                logger.debug(f"Processing FBD Sheet {sheet_num}")
                sheet_code = self._parse_sheet(sheet, sheet_num)
                if sheet_code:
                    st_code.append(f"// Sheet {sheet_num}")
                    st_code.append(sheet_code)
            
            return "\n".join(st_code) if st_code else "// No FBD content to translate"
            
        except Exception as e:
            logger.error(f"Error parsing FBD content: {e}")
            return f"// ERROR: Failed to parse FBD content - {e}"
    
    def _parse_sheet(self, sheet: ET.Element, sheet_num: int) -> str:
        """Parse a single FBD sheet."""
        try:
            # Parse all elements
            self._parse_input_refs(sheet)
            self._parse_output_refs(sheet)
            self._parse_function_blocks(sheet)
            self._parse_wires(sheet)
            
            # Determine execution order
            self._determine_execution_order()
            
            # Generate ST code
            return self._generate_st_code()
            
        except Exception as e:
            logger.error(f"Error parsing FBD sheet {sheet_num}: {e}")
            return f"// ERROR: Failed to parse FBD sheet {sheet_num} - {e}"
    
    def _parse_input_refs(self, sheet: ET.Element):
        """Parse input references (IRef elements)."""
        for iref in sheet.findall('IRef'):
            ref_id = iref.get('ID')
            operand = iref.get('Operand', '')
            if ref_id and operand:
                self.input_refs[ref_id] = operand
                logger.debug(f"Input ref {ref_id}: {operand}")
    
    def _parse_output_refs(self, sheet: ET.Element):
        """Parse output references (ORef elements)."""
        for oref in sheet.findall('ORef'):
            ref_id = oref.get('ID')
            operand = oref.get('Operand', '')
            if ref_id and operand:
                self.output_refs[ref_id] = operand
                logger.debug(f"Output ref {ref_id}: {operand}")
    
    def _parse_function_blocks(self, sheet: ET.Element):
        """Parse function blocks (AddOnInstruction elements)."""
        for fb in sheet.findall('AddOnInstruction'):
            fb_id = fb.get('ID')
            fb_name = fb.get('Name', '')
            fb_operand = fb.get('Operand', '')
            
            if fb_id and fb_name:
                fb_info = {
                    'name': fb_name,
                    'operand': fb_operand,
                    'inputs': {},
                    'outputs': {},
                    'visible_pins': fb.get('VisiblePins', '').split()
                }
                
                # Parse input/output parameters
                for param in fb.findall('InOutParameter'):
                    param_name = param.get('Name', '')
                    argument = param.get('Argument', '')
                    if param_name and argument:
                        fb_info['inputs'][param_name] = argument
                
                self.function_blocks[fb_id] = fb_info
                logger.debug(f"Function block {fb_id}: {fb_name} ({fb_operand})")
    
    def _parse_wires(self, sheet: ET.Element):
        """Parse wire connections."""
        for wire in sheet.findall('Wire'):
            from_id = wire.get('FromID')
            to_id = wire.get('ToID')
            from_param = wire.get('FromParam')
            to_param = wire.get('ToParam')
            
            if from_id and to_id:
                wire_info = {
                    'from_id': from_id,
                    'to_id': to_id,
                    'from_param': from_param,
                    'to_param': to_param
                }
                self.wires.append(wire_info)
                logger.debug(f"Wire: {from_id} -> {to_id} ({from_param} -> {to_param})")
    
    def _determine_execution_order(self):
        """Determine the execution order of function blocks based on wire connections."""
        # Create dependency graph
        dependencies = {}
        for fb_id in self.function_blocks:
            dependencies[fb_id] = set()
        
        # Add dependencies based on wires
        for wire in self.wires:
            from_id = wire['from_id']
            to_id = wire['to_id']
            
            # If wire goes from a function block to another function block
            if from_id in self.function_blocks and to_id in self.function_blocks:
                dependencies[to_id].add(from_id)
        
        # Topological sort to determine execution order
        visited = set()
        temp_visited = set()
        
        def visit(fb_id):
            if fb_id in temp_visited:
                logger.warning(f"Circular dependency detected involving {fb_id}")
                return
            if fb_id in visited:
                return
            
            temp_visited.add(fb_id)
            
            for dep in dependencies.get(fb_id, []):
                if dep in self.function_blocks:
                    visit(dep)
            
            temp_visited.remove(fb_id)
            visited.add(fb_id)
            self.execution_order.append(fb_id)
        
        # Visit all function blocks
        for fb_id in self.function_blocks:
            if fb_id not in visited:
                visit(fb_id)
        
        logger.debug(f"Execution order: {self.execution_order}")
    
    def _generate_st_code(self) -> str:
        """Generate Structured Text code from parsed FBD elements."""
        st_lines = []
        
        # Process function blocks in execution order
        for fb_id in self.execution_order:
            fb_info = self.function_blocks[fb_id]
            fb_code = self._generate_fb_code(fb_id, fb_info)
            if fb_code:
                st_lines.append(fb_code)
        
        # Process output assignments
        output_assignments = self._generate_output_assignments()
        if output_assignments:
            st_lines.extend(output_assignments)
        
        return "\n".join(st_lines)
    
    def _generate_fb_code(self, fb_id: str, fb_info: Dict) -> str:
        """Generate ST code for a function block."""
        fb_name = fb_info['name']
        fb_operand = fb_info['operand']
        
        # Build parameter list
        params = []
        for wire in self.wires:
            if wire['to_id'] == fb_id and wire['to_param']:
                # Find the source value
                source_value = self._get_source_value(wire['from_id'], wire['from_param'])
                if source_value:
                    params.append(f"{wire['to_param']} := {source_value}")
        
        # Generate function block call
        if params:
            param_str = ", ".join(params)
            return f"{fb_operand}({param_str});"
        else:
            return f"{fb_operand}();"
    
    def _get_source_value(self, from_id: str, from_param: Optional[str]) -> Optional[str]:
        """Get the source value for a wire connection."""
        # Check if it's an input reference
        if from_id in self.input_refs:
            return self.input_refs[from_id]
        
        # Check if it's an output reference
        if from_id in self.output_refs:
            return self.output_refs[from_id]
        
        # Check if it's a function block output
        if from_id in self.function_blocks:
            fb_info = self.function_blocks[from_id]
            if from_param and from_param in fb_info['inputs']:
                return fb_info['inputs'][from_param]
            elif from_param:
                # Return the function block name with the parameter
                return f"{fb_info['operand']}.{from_param}"
        
        logger.warning(f"Unknown source ID: {from_id}")
        return None
    
    def _generate_output_assignments(self) -> List[str]:
        """Generate output assignments from function blocks to output references."""
        assignments = []
        
        for wire in self.wires:
            if wire['from_id'] in self.function_blocks and wire['to_id'] in self.output_refs:
                fb_id = wire['from_id']
                output_ref = self.output_refs[wire['to_id']]
                fb_info = self.function_blocks[fb_id]
                
                if wire['from_param']:
                    source = f"{fb_info['operand']}.{wire['from_param']}"
                    assignments.append(f"{output_ref} := {source};")
        
        return assignments


def translate_fbd_to_st(fbd_content: ET.Element) -> str:
    """Main function to translate FBD content to ST code."""
    translator = FBDTranslator()
    return translator.parse_fbd_content(fbd_content) 