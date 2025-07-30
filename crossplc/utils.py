"""Utility functions for the L5X-ST compiler."""

import re
import logging
from typing import List, Tuple, Optional, Dict, Any
from .constants import (
    COMPARISON_OPERATORS, LOGICAL_OPERATORS, ARITHMETIC_OPERATORS,
    RESERVED_WORDS, UNIMPLEMENTED_TYPES, BIT_ACCESS_HELPER
)
from .models import DataType, Tag, FunctionBlock, Instruction
from .instructions import process_routine
import xml.etree.ElementTree as ET
from .ladder_logic import translate_ladder_to_st
from .fbd_translator import translate_fbd_to_st

logger = logging.getLogger(__name__)


def format_rung_text(text: str) -> str:
    """Format rung text by removing extra whitespace and normalizing."""
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    return text


def format_time_line(line: str, tab: str) -> str:
    """Format a time line with proper indentation."""
    # Extract time value and format it
    time_match = re.search(r'T#(\d+)([mshd])', line)
    if time_match:
        value, unit = time_match.groups()
        return f"{tab}{value}{unit}"
    return line


def replace_bit_accesses(st_line: str) -> str:
    """Replace bit accesses with DWORD operations."""
    # Pattern to match bit access like "variable.bit"
    bit_pattern = r'(\w+)\.(\w+)'
    
    def replace_bit(match):
        var_name, bit_name = match.groups()
        # Create a DWORD operation for bit access
        return f"{BIT_ACCESS_HELPER}.{bit_name}"
    
    return re.sub(bit_pattern, replace_bit, st_line)


def replace_reserved_words(st_line: str) -> str:
    """Replace reserved words with their safe alternatives."""
    for reserved, replacement in RESERVED_WORDS.items():
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(reserved) + r'\b'
        st_line = re.sub(pattern, replacement, st_line, flags=re.IGNORECASE)
    return st_line


def replace_func_calls(st_line: str) -> str:
    """Replace function calls with their ST equivalents."""
    # This is a simplified version - the original has more complex logic
    # Pattern to match function calls
    func_pattern = r'(\w+)\s*\(([^)]*)\)'
    
    def replace_func(match):
        func_name, params = match.groups()
        # Handle specific function replacements
        if func_name.upper() == 'TON':
            return f"{func_name}_TIMER({params})"
        return match.group(0)
    
    return re.sub(func_pattern, replace_func, st_line)


def replace_booleans(st_line: str) -> str:
    """Replace boolean expressions with proper ST syntax."""
    # Replace common boolean patterns
    replacements = [
        (r'\bTRUE\b', '1'),
        (r'\bFALSE\b', '0'),
        (r'\btrue\b', '1'),
        (r'\bfalse\b', '0'),
    ]
    
    for pattern, replacement in replacements:
        st_line = re.sub(pattern, replacement, st_line)
    
    return st_line


def fix_mismatched_binary_expr(tokenized: List[str], oper: str) -> List[str]:
    """Fix mismatched binary expressions by adding proper type conversions."""
    # This is a simplified version of the original complex logic
    result = []
    i = 0
    
    while i < len(tokenized):
        if tokenized[i] == oper and i > 0 and i < len(tokenized) - 1:
            # Check if we need to add type conversion
            left = tokenized[i - 1]
            right = tokenized[i + 1]
            
            # Add type conversion if needed
            if oper in ['+', '-', '*', '/']:
                # For arithmetic operations, ensure proper types
                if left.isdigit() and '.' not in left:
                    tokenized[i - 1] = f"{left}.0"
                if right.isdigit() and '.' not in right:
                    tokenized[i + 1] = f"{right}.0"
        
        result.append(tokenized[i])
        i += 1
    
    return result


def fix_type_mismatches(st_line: str) -> str:
    """Fix type mismatches in ST code."""
    # Pattern to match assignments that might have type mismatches
    assignment_pattern = r'(\w+)\s*:=\s*(\d+)'
    
    def fix_assignment(match):
        var_name, value = match.groups()
        # If it's a real variable being assigned an integer, convert to float
        if value.isdigit() and not value.endswith('.0'):
            return f"{var_name} := {value}.0"
        return match.group(0)
    
    return re.sub(assignment_pattern, fix_assignment, st_line)


def fix_multiline_comments(st_line: str) -> str:
    """Fix multiline comments by converting them to single-line comments."""
    # Replace (* ... *) with (* ... *)
    # This is a simplified version - the original has more complex logic
    return st_line


def replace_sequence(orig: str, target: str) -> str:
    """Replace a sequence in the original string with the target."""
    return orig.replace(target, '')


def replace_renamed_vars(st_line: str, renamed_vars: dict) -> str:
    """Replace renamed variables in ST code."""
    for old_name, new_name in renamed_vars.items():
        pattern = r'\b' + re.escape(old_name) + r'\b'
        st_line = re.sub(pattern, new_name, st_line)
    return st_line


def format_ST_line(line: str) -> str:
    """Format a single ST line with proper indentation and syntax."""
    # Remove extra whitespace
    line = re.sub(r'\s+', ' ', line.strip())
    
    # Add proper spacing around operators
    operators = COMPARISON_OPERATORS + LOGICAL_OPERATORS + ARITHMETIC_OPERATORS
    for op in operators:
        line = line.replace(op, f" {op} ")
    
    # Clean up multiple spaces
    line = re.sub(r'\s+', ' ', line)
    
    return line


def decrement_tab(tab: str) -> str:
    """Decrement tab indentation."""
    if tab.endswith('\t'):
        return tab[:-1]
    return tab


def process_params(params: str, vartype: str) -> str:
    """Process parameters for function calls."""
    if not params:
        return ""
    
    # Split parameters and process each one
    param_list = [p.strip() for p in params.split(',')]
    processed_params = []
    
    for param in param_list:
        # Handle different parameter types
        if vartype == "BOOL":
            processed_params.append(f"({param} = 1)")
        else:
            processed_params.append(param)
    
    return ", ".join(processed_params)


def initialize_messages(tags) -> str:
    """Initialize message variables."""
    init_code = "\n\t(*Initialize Messages*)\n"
    
    # This is a simplified version - the original has more complex logic
    for tag_name in tags:
        tag = tags[tag_name]
        if tag.getAttribute('DataType') == 'MESSAGE':
            init_code += f"\t{tag_name}.EN1 := 0;\n"
            init_code += f"\t{tag_name}.EW := 0;\n"
            init_code += f"\t{tag_name}.ST := 0;\n"
            init_code += f"\t{tag_name}.DN := 0;\n"
            init_code += f"\t{tag_name}.ER := 0;\n"
    
    return init_code


def clean_identifier(identifier: str) -> str:
    """Clean and sanitize an identifier for ST code."""
    # Remove any non-alphanumeric characters except underscores
    cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', identifier)
    # Ensure it doesn't start with a number
    if cleaned and cleaned[0].isdigit():
        cleaned = f"var_{cleaned}"
    return cleaned


def sanitize_identifier(identifier: str) -> str:
    """Sanitize an identifier to be ST-compatible."""
    # Replace reserved words
    if identifier.upper() in RESERVED_WORDS:
        return RESERVED_WORDS[identifier.upper()]
    
    # Clean the identifier
    return clean_identifier(identifier)


def get_base_data_type(data_type: str) -> str:
    """Get the base data type from a complex data type."""
    # Remove array dimensions and other modifiers
    base_type = re.sub(r'\[.*?\]', '', data_type)
    base_type = re.sub(r'<.*?>', '', base_type)
    return base_type.strip()


def get_data_type_info(name: str, data_type_data: Any) -> Optional[DataType]:
    """Extract data type information from L5X data."""
    try:
        print(f"DEBUG: get_data_type_info called with name={name}, data_type={type(data_type_data)}")
        
        # Try to get data type information
        if hasattr(data_type_data, 'get'):
            base_type = data_type_data.get('DataType', 'UNKNOWN')
            description = data_type_data.get('Description', '')
        else:
            # If it's not a dict-like object, try to convert to string
            base_type = str(data_type_data)
            description = ''
        
        # Clean the name and base type
        clean_name = sanitize_identifier(name)
        clean_base_type = get_base_data_type(base_type)
        
        return DataType(
            name=clean_name,
            base_type=clean_base_type,
            description=description
        )
    except Exception as e:
        print(f"DEBUG: Exception in get_data_type_info: {e}")
        return None


def extract_tag_info(name: str, tag_data: Any) -> Optional[Tag]:
    """Extract tag information from L5X data."""
    try:
        print(f"DEBUG: extract_tag_info called with name={name}, tag_data={type(tag_data)}")
        
        # For l5x.tag.Tag objects, access attributes directly
        if hasattr(tag_data, 'data_type'):
            data_type = tag_data.data_type
            print(f"DEBUG: extract_tag_info: data_type={data_type}")
        elif hasattr(tag_data, 'get'):
            # Fallback for dict-like objects
            data_type = tag_data.get('DataType', 'UNKNOWN')
            print(f"DEBUG: extract_tag_info: data_type from get={data_type}")
        else:
            # If it's not a dict-like object, try to convert to string
            data_type = str(tag_data)
            print(f"DEBUG: extract_tag_info: data_type from str={data_type}")
        
        # Get description if available
        if hasattr(tag_data, 'description'):
            description = tag_data.description
        elif hasattr(tag_data, 'get'):
            description = tag_data.get('Description', '')
        else:
            description = ''
        
        # Get value if available
        try:
            if hasattr(tag_data, 'value'):
                value = tag_data.value
            elif hasattr(tag_data, 'get'):
                value = tag_data.get('Value', '')
            else:
                value = ''
            
            # Handle hex values and other special formats
            if isinstance(value, str) and value.startswith("'$") and value.endswith("'"):
                # Hex value like '$00$00$00$1E' - convert to decimal
                hex_str = value[2:-1].replace('$', '')  # Remove '$' and quotes
                try:
                    value = str(int(hex_str, 16))
                except ValueError:
                    # If conversion fails, keep original value
                    pass
        except Exception as e:
            print(f"DEBUG: extract_tag_info: Error getting value: {e}")
            value = ''
        
        # Clean the name and data type
        clean_name = sanitize_identifier(name)
        clean_data_type = get_base_data_type(str(data_type))
        
        print(f"DEBUG: extract_tag_info: clean_name={clean_name}, clean_data_type={clean_data_type}")
        
        return Tag(
            name=clean_name,
            data_type=clean_data_type,
            description=description,
            value=value
        )
    except Exception as e:
        logger.error(f"Error extracting tag info: {e}")
        print(f"DEBUG: Exception in extract_tag_info: {e}")
        return None


def extract_function_block_info(name: str, routine_data: Any) -> Optional[FunctionBlock]:
    """Extract function block information from L5X routine data."""
    try:
        print(f"DEBUG: extract_function_block_info called with name={name}, routine_data={type(routine_data)}")
        
        # Try to get routine information
        if hasattr(routine_data, 'get'):
            description = routine_data.get('Description', '')
            # Extract variables, inputs, outputs from routine data
            variables = []
            inputs = []
            outputs = []
            code = []
            
            # This is a simplified extraction - the actual implementation would be more complex
            if hasattr(routine_data, 'items'):
                for key, value in routine_data.items():
                    if key == 'Variables':
                        # Process variables
                        pass
                    elif key == 'RLLContent':
                        # Process ladder logic content
                        pass
        else:
            description = ''
            variables = []
            inputs = []
            outputs = []
            code = []
        
        # Clean the name
        clean_name = sanitize_identifier(name)
        
        return FunctionBlock(
            name=clean_name,
            inputs=inputs,
            outputs=outputs,
            variables=variables,
            code=code,
            description=description
        )
    except Exception as e:
        print(f"DEBUG: Exception in extract_function_block_info: {e}")
        return None


def extract_instruction_info(instruction_data: Any) -> Optional[Instruction]:
    """Extract instruction information from L5X data."""
    try:
        print(f"DEBUG: extract_instruction_info called with instruction_data={type(instruction_data)}")
        
        # Try to get instruction information
        if hasattr(instruction_data, 'get'):
            name = instruction_data.get('Name', 'UNKNOWN')
            description = instruction_data.get('Description', '')
            parameters = []
            
            # Extract parameters if available
            if hasattr(instruction_data, 'items'):
                for key, value in instruction_data.items():
                    if key.startswith('Parameter'):
                        parameters.append(str(value))
        else:
            name = str(instruction_data)
            description = ''
            parameters = []
        
        # Clean the name
        clean_name = sanitize_identifier(name)
        
        return Instruction(
            name=clean_name,
            parameters=parameters,
            description=description
        )
    except Exception as e:
        print(f"DEBUG: Exception in extract_instruction_info: {e}")
        return None


def parse_function_call(text: str) -> Tuple[str, List[str]]:
    """Parse a function call and return function name and parameters."""
    # Pattern to match function calls: function_name(param1, param2, ...)
    match = re.match(r'(\w+)\s*\(([^)]*)\)', text)
    if match:
        func_name = match.group(1)
        params_str = match.group(2)
        # Split parameters by comma, but be careful about nested parentheses
        params = [p.strip() for p in params_str.split(',') if p.strip()]
        return func_name, params
    return text, []


def is_numeric(value: str) -> bool:
    """Check if a string represents a numeric value."""
    try:
        float(value)
        return True
    except ValueError:
        return False


def get_data_type(value: str) -> str:
    """Determine the data type of a value."""
    if is_numeric(value):
        if '.' in value:
            return 'REAL'
        else:
            return 'INT'
    elif value.upper() in ['TRUE', 'FALSE', '1', '0']:
        return 'BOOL'
    else:
        return 'STRING'


def _extract_data_types(project: Any) -> List[DataType]:
    """Extract data type definitions from project."""
    data_types = []
    try:
        print(f"DEBUG: _extract_data_types: project={project}")
        print(f"DEBUG: _extract_data_types: project dir={dir(project)}")
        
        # Based on original code: prj.datatypes
        if hasattr(project, 'datatypes'):
            print(f"DEBUG: _extract_data_types: found datatypes attribute")
            datatypes_dict = project.datatypes
            print(f"DEBUG: _extract_data_types: datatypes_dict type={type(datatypes_dict)}")
            if hasattr(datatypes_dict, 'names'):
                print(f"DEBUG: _extract_data_types: datatypes names={datatypes_dict.names}")
                
                # Extract each data type
                for dt_name in datatypes_dict.names:
                    try:
                        dt_data = datatypes_dict[dt_name]
                        print(f"DEBUG: _extract_data_types: processing {dt_name}, type={type(dt_data)}")
                        
                        # Extract members from the data type
                        members = {}
                        if hasattr(dt_data, 'child_elements') and len(dt_data.child_elements) > 0:
                            for child in dt_data.child_elements[0].childNodes:
                                if hasattr(child, 'attributes') and hasattr(child.attributes, 'get'):
                                    var_name = child.attributes.get('Name', '')
                                    var_type = child.attributes.get('DataType', '')
                                    if var_name and var_type:
                                        members[var_name] = var_type
                                        print(f"DEBUG: _extract_data_types: {dt_name}.{var_name}: {var_type}")
                        
                        if members:
                            data_type = DataType(
                                name=dt_name,
                                base_type="STRUCT",  # User-defined types are typically structs
                                members=members,
                                description=f"User-defined data type {dt_name}"
                            )
                            data_types.append(data_type)
                            print(f"DEBUG: _extract_data_types: added {dt_name} with {len(members)} members")
                    except Exception as e:
                        print(f"DEBUG: _extract_data_types: Error processing {dt_name}: {e}")
            elif hasattr(datatypes_dict, 'keys'):
                print(f"DEBUG: _extract_data_types: datatypes keys={list(datatypes_dict.keys())}")
        
        # Also check for addons (from original code)
        if hasattr(project, 'addons'):
            print(f"DEBUG: _extract_data_types: found addons attribute")
            addons_dict = project.addons
            print(f"DEBUG: _extract_data_types: addons_dict type={type(addons_dict)}")
            if hasattr(addons_dict, 'names'):
                print(f"DEBUG: _extract_data_types: addons names={addons_dict.names}")
        
    except Exception as e:
        logger.error(f"Error extracting data types: {e}")
        print(f"DEBUG: Exception in _extract_data_types: {e}")
    
    print(f"DEBUG: Extracted {len(data_types)} data types")
    return data_types


def _extract_function_blocks(project: Any) -> List[FunctionBlock]:
    """Extract function block definitions from project."""
    function_blocks = []
    try:
        print(f"DEBUG: _extract_function_blocks: project={project}")
        
        # Based on original code: prj.addons
        if hasattr(project, 'addons'):
            print(f"DEBUG: _extract_function_blocks: found addons attribute")
            addons_dict = project.addons
            print(f"DEBUG: _extract_function_blocks: addons_dict type={type(addons_dict)}")
            if hasattr(addons_dict, 'names'):
                print(f"DEBUG: _extract_function_blocks: addons names={addons_dict.names}")
                
                # Extract each function block
                for fb_name in addons_dict.names:
                    try:
                        fb_data = addons_dict[fb_name]
                        print(f"DEBUG: _extract_function_blocks: processing {fb_name}, type={type(fb_data)}")
                        
                        # Extract parameters
                        parameters = {}
                        params_section = fb_data.get_child_element("Parameters")
                        if params_section and hasattr(params_section, 'childNodes'):
                            for child in params_section.childNodes:
                                if hasattr(child, 'attributes') and hasattr(child.attributes, 'get'):
                                    param_name = child.attributes.get('Name', '')
                                    param_type = child.attributes.get('DataType', '')
                                    param_usage = child.attributes.get('Usage', '')
                                    
                                    if param_name and param_type:
                                        parameters[param_name] = {
                                            'type': param_type,
                                            'usage': param_usage
                                        }
                        
                        # Extract local tags
                        local_tags = {}
                        local_tags_section = fb_data.get_child_element("LocalTags")
                        if local_tags_section and hasattr(local_tags_section, 'childNodes'):
                            for tag in local_tags_section.childNodes:
                                if hasattr(tag, 'attributes') and hasattr(tag.attributes, 'get'):
                                    tag_name = tag.attributes.get('Name', '')
                                    tag_type = tag.attributes.get('DataType', '')
                                    if tag_name and tag_type:
                                        local_tags[tag_name] = tag_type
                        
                        # Extract routine logic (if available)
                        routine_logic = ""
                        routines_section = fb_data.get_child_element("Routines")
                        if routines_section and hasattr(routines_section, 'childNodes'):
                            for routine in routines_section.childNodes:
                                if routine.nodeName == 'Routine':
                                    routine_name = routine.attributes.get('Name', '')
                                    if routine_name == 'Logic':
                                        # Try to extract the logic content
                                        logic_section = routine.childNodes[0]
                                        if logic_section is not None:
                                            routine_logic = ET.tostring(logic_section, encoding='unicode')
                        
                        # Convert parameters to the expected format
                        inputs = []
                        outputs = []
                        variables = []
                        
                        for param_name, param_info in parameters.items():
                            param_dict = {'name': param_name, 'type': param_info['type']}
                            if param_info['usage'] == 'Input':
                                inputs.append(param_dict)
                            elif param_info['usage'] == 'Output':
                                outputs.append(param_dict)
                            else:  # InOut or other
                                inputs.append(param_dict)
                        
                        # Convert local tags to variables
                        for tag_name, tag_type in local_tags.items():
                            variables.append({'name': tag_name, 'type': tag_type})
                        
                        # Convert logic to code list
                        code = []
                        if routine_logic:
                            code = [routine_logic]
                        
                        function_block = FunctionBlock(
                            name=fb_name,
                            inputs=inputs,
                            outputs=outputs,
                            variables=variables,
                            code=code,
                            description=f"Function block {fb_name}"
                        )
                        function_blocks.append(function_block)
                        print(f"DEBUG: _extract_function_blocks: added {fb_name} with {len(inputs)} inputs, {len(outputs)} outputs, {len(variables)} vars, {len(code)} code lines")
                    except Exception as e:
                        print(f"DEBUG: _extract_function_blocks: Error processing {fb_name}: {e}")
            elif hasattr(addons_dict, 'keys'):
                print(f"DEBUG: _extract_function_blocks: addons keys={list(addons_dict.keys())}")
        
    except Exception as e:
        logger.error(f"Error extracting function blocks: {e}")
        print(f"DEBUG: Exception in _extract_function_blocks: {e}")
    
    print(f"DEBUG: Extracted {len(function_blocks)} function blocks")
    return function_blocks


def _extract_program_logic(project: Any) -> str:
    """Extract program logic from the main routine."""
    program_logic = ""
    try:
        print(f"DEBUG: _extract_program_logic: project={project}")
        
        # Based on original code: prj.programs[main_program].routines[prj.programs[main_program].main_routine_name]
        if hasattr(project, 'programs'):
            programs_dict = project.programs
            print(f"DEBUG: _extract_program_logic: programs_dict type={type(programs_dict)}")
            if hasattr(programs_dict, 'names'):
                print(f"DEBUG: _extract_program_logic: programs names={programs_dict.names}")
                
                # Look for main program (from original code: main_program = "MainProgram")
                main_program_name = "MainProgram"
                if main_program_name in programs_dict.names:
                    print(f"DEBUG: _extract_program_logic: found main program {main_program_name}")
                    main_program = programs_dict[main_program_name]
                    
                    if hasattr(main_program, 'routines'):
                        routines = main_program.routines
                        print(f"DEBUG: _extract_program_logic: routines type={type(routines)}")
                        if hasattr(routines, 'names'):
                            print(f"DEBUG: _extract_program_logic: routines names={routines.names}")
                            
                            # Get main routine name
                            if hasattr(main_program, 'main_routine_name'):
                                main_routine_name = main_program.main_routine_name
                                print(f"DEBUG: _extract_program_logic: main_routine_name={main_routine_name}")
                                
                                if main_routine_name in routines.names:
                                    print(f"DEBUG: _extract_program_logic: found main routine {main_routine_name}")
                                    main_routine = routines[main_routine_name]
                                    
                                    # Process the main routine
                                    routine_code = process_routine(main_routine, project, "")
                                    if routine_code:
                                        program_logic = routine_code
                                        print(f"DEBUG: _extract_program_logic: extracted {len(routine_code)} characters of code")
                                    else:
                                        print(f"DEBUG: _extract_program_logic: no code extracted from main routine")
                                else:
                                    print(f"DEBUG: _extract_program_logic: main routine {main_routine_name} not found in routines")
                            else:
                                print(f"DEBUG: _extract_program_logic: no main_routine_name attribute found")
                        else:
                            print(f"DEBUG: _extract_program_logic: routines has no names attribute")
                    else:
                        print(f"DEBUG: _extract_program_logic: main program has no routines attribute")
                else:
                    print(f"DEBUG: _extract_program_logic: main program {main_program_name} not found")
            else:
                print(f"DEBUG: _extract_program_logic: programs has no names attribute")
        
    except Exception as e:
        logger.error(f"Error extracting program logic: {e}")
        print(f"DEBUG: Exception in _extract_program_logic: {e}")
    
    print(f"DEBUG: Extracted program logic: {len(program_logic)} characters")
    return program_logic


def extract_data_types_from_xml(project) -> list:
    """Extract user-defined data types from the raw XML in the L5X project."""
    data_types = []
    try:
        root = getattr(project, 'element', None)
        if root is None and hasattr(project, 'controller'):
            root = getattr(project.controller, 'element', None)
        if root is None:
            print("DEBUG: No root element found in project or controller.")
            return data_types
        # Find the DataTypes section (case-insensitive)
        for dt_section in root.findall('.//DataTypes'):
            for dt in dt_section.findall('DataType'):
                name = dt.get('Name')
                base_type = dt.get('Family', 'STRUCT')  # Default to STRUCT
                members = {}
                struct = dt.find('Members')
                if struct is not None:
                    for member in struct.findall('Member'):
                        m_name = member.get('Name')
                        m_type = member.get('DataType')
                        if m_name and m_type:
                            members[m_name] = m_type
                data_type = DataType(
                    name=name,
                    base_type=base_type,
                    members=members,
                    description=f"User-defined data type {name}"
                )
                data_types.append(data_type)
                print(f"DEBUG: Extracted DataType: {name} with {len(members)} members")
    except Exception as e:
        print(f"DEBUG: Exception in extract_data_types_from_xml: {e}")
    return data_types


def extract_function_blocks_from_xml(project) -> list:
    """Extract Add-On Instructions (function blocks) from the raw XML in the L5X project."""
    function_blocks = []
    try:
        root = getattr(project, 'element', None)
        if root is None and hasattr(project, 'controller'):
            root = getattr(project.controller, 'element', None)
        if root is None:
            print("DEBUG: No root element found in project or controller.")
            return function_blocks
        
        # Find the AddOnInstructionDefinitions section
        for aoi_section in root.findall('.//AddOnInstructionDefinitions'):
            for aoi in aoi_section.findall('AddOnInstructionDefinition'):
                name = aoi.get('Name')
                description = aoi.get('Description', f"Add-On Instruction {name}")
                
                # Extract parameters
                parameters = {}
                params_section = aoi.find('Parameters')
                if params_section is not None:
                    for param in params_section.findall('Parameter'):
                        param_name = param.get('Name')
                        param_type = param.get('DataType')
                        param_usage = param.get('Usage', 'Input')  # Input, Output, InOut
                        if param_name and param_type:
                            parameters[param_name] = {
                                'type': param_type,
                                'usage': param_usage
                            }
                
                # Extract local tags
                local_tags = {}
                local_tags_section = aoi.find('LocalTags')
                if local_tags_section is not None:
                    for tag in local_tags_section.findall('Tag'):
                        tag_name = tag.get('Name')
                        tag_type = tag.get('DataType')
                        if tag_name and tag_type:
                            local_tags[tag_name] = tag_type
                
                # Extract routine logic (if available)
                routine_logic = ""
                routines_section = aoi.find('Routines')
                if routines_section is not None:
                    for routine in routines_section.findall('Routine'):
                        routine_name = routine.get('Name')
                        if routine_name == 'Logic':
                            # Try to extract the logic content
                            logic_section = routine.find('RLLContent')
                            if logic_section is not None:
                                routine_logic = ET.tostring(logic_section, encoding='unicode')
                
                # Convert parameters to the expected format
                inputs = []
                outputs = []
                variables = []
                
                for param_name, param_info in parameters.items():
                    param_dict = {'name': param_name, 'type': param_info['type']}
                    if param_info['usage'] == 'Input':
                        inputs.append(param_dict)
                    elif param_info['usage'] == 'Output':
                        outputs.append(param_dict)
                    else:  # InOut or other
                        inputs.append(param_dict)
                
                # Convert local tags to variables
                for tag_name, tag_type in local_tags.items():
                    variables.append({'name': tag_name, 'type': tag_type})
                
                # Convert logic to code list
                code = []
                if routine_logic:
                    code = [routine_logic]
                
                function_block = FunctionBlock(
                    name=name,
                    inputs=inputs,
                    outputs=outputs,
                    variables=variables,
                    code=code,
                    description=description
                )
                function_blocks.append(function_block)
                print(f"DEBUG: Extracted FunctionBlock: {name} with {len(parameters)} parameters, {len(local_tags)} local tags")
                
    except Exception as e:
        print(f"DEBUG: Exception in extract_function_blocks_from_xml: {e}")
    return function_blocks


def extract_program_logic_from_xml(project) -> str:
    """Extract program logic (routines) from the raw XML in the L5X project."""
    program_logic = ""
    try:
        root = getattr(project, 'element', None)
        if root is None and hasattr(project, 'controller'):
            root = getattr(project.controller, 'element', None)
        if root is None:
            print("DEBUG: No root element found in project or controller.")
            return program_logic
        
        # Find the Programs section and look for MainProgram
        for programs_section in root.findall('.//Programs'):
            for program in programs_section.findall('Program'):
                program_name = program.get('Name')
                if program_name == 'MainProgram':
                    print(f"DEBUG: Found MainProgram: {program_name}")
                    
                    # Find routines in this program
                    routines_section = program.find('Routines')
                    if routines_section is not None:
                        for routine in routines_section.findall('Routine'):
                            routine_name = routine.get('Name', 'Unknown')
                            routine_type = routine.get('Type', 'Unknown')
                            print(f"DEBUG: Processing routine: {routine_name} ({routine_type})")
                            
                            # Extract content based on routine type
                            if routine_type == 'RLL':
                                # Extract ladder logic rungs
                                rll_content = routine.find('RLLContent')
                                if rll_content is not None:
                                    rungs = rll_content.findall('Rung')
                                    print(f"DEBUG: Found {len(rungs)} rungs in {routine_name}")
                                    
                                    # Add routine header
                                    program_logic += f"\n// Routine: {routine_name} (Ladder Logic)\n"
                                    
                                    for i, rung in enumerate(rungs):
                                        rung_number = rung.get('Number', 'Unknown')
                                        rung_text_elem = rung.find('Text')
                                        
                                        if rung_text_elem is not None:
                                            cdata_content = rung_text_elem.find('CDATAContent')
                                            if cdata_content is not None and cdata_content.text:
                                                rung_text = cdata_content.text.strip()
                                                print(f"DEBUG: Rung {rung_number} text: {rung_text[:50]}...")
                                                
                                                # Translate ladder logic to ST
                                                st_code = translate_ladder_to_st(rung_text)
                                                program_logic += f"\n// Rung {rung_number}\n{st_code}\n"
                                            else:
                                                print(f"DEBUG: Rung {rung_number} has no CDATAContent text")
                                                program_logic += f"\n// Rung {rung_number} - No content\n"
                                        else:
                                            print(f"DEBUG: Rung {rung_number} has no Text element")
                                            program_logic += f"\n// Rung {rung_number} - No text element\n"
                                            
                            elif routine_type == 'ST':
                                # Extract structured text lines
                                st_content = routine.find('STContent')
                                if st_content is not None:
                                    lines = st_content.findall('Line')
                                    print(f"DEBUG: Found {len(lines)} lines in {routine_name}")
                                    
                                    # Add routine header
                                    program_logic += f"\n// Routine: {routine_name} (Structured Text)\n"
                                    
                                    for i, line in enumerate(lines):
                                        line_number = line.get('Number', 'Unknown')
                                        cdata_content = line.find('CDATAContent')
                                        
                                        if cdata_content is not None and cdata_content.text:
                                            line_text = cdata_content.text.strip()
                                            print(f"DEBUG: Line {line_number} text: {line_text[:50]}...")
                                            program_logic += f"{line_text}\n"
                                        else:
                                            print(f"DEBUG: Line {line_number} has no CDATAContent text")
                                            program_logic += f"// Line {line_number} - No content\n"
                                            
                            elif routine_type == 'FBD':
                                # Extract function block diagram content
                                routine_child = routine.find('FBDContent')
                                if routine_child is not None:
                                    print(f"DEBUG: Found FBD content in {routine_name}")
                                    
                                    # Translate FBD to ST
                                    fbd_st_code = translate_fbd_to_st(routine_child)
                                    program_logic += f"\n// Routine: {routine_name} (Function Block Diagram)\n{fbd_st_code}\n"
                                else:
                                    print(f"DEBUG: {routine_name} has no FBDContent")
                                    program_logic += f"\n// Routine: {routine_name} (FBD) - No content\n"
                            else:
                                print(f"DEBUG: Unknown routine type: {routine_type}")
                                program_logic += f"\n// Routine: {routine_name} (Unknown type: {routine_type})\n"
                    else:
                        print("DEBUG: No Routines section found in MainProgram")
        else:
            print("DEBUG: MainProgram not found")
            
    except Exception as e:
        print(f"DEBUG: Error extracting program logic: {e}")
        program_logic += f"\n// Error extracting program logic: {e}\n"
    
    return program_logic 