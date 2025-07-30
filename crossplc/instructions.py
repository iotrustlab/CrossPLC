"""Instruction processors for converting L5X instructions to Structured Text."""

from typing import List, Optional
from .models import CompilerState
from .constants import UNIMPLEMENTED_TYPES


def process_equ(params: List[str]) -> str:
    """Process EQU (Equal) instruction."""
    if len(params) >= 2:
        return f"{params[0]} = {params[1]}"
    return ""


def process_neq(params: List[str]) -> str:
    """Process NEQ (Not Equal) instruction."""
    if len(params) >= 2:
        return f"{params[0]} <> {params[1]}"
    return ""


def process_xic(params: List[str]) -> str:
    """Process XIC (Examine If Closed) instruction."""
    if params:
        return f"{params[0]} = 1"
    return ""


def process_xio(params: List[str]) -> str:
    """Process XIO (Examine If Open) instruction."""
    if params:
        return f"{params[0]} = 0"
    return ""


def process_ote(params: List[str], condition: str = "") -> str:
    """Process OTE (Output Energize) instruction."""
    if params:
        if condition:
            return f"IF {condition} THEN\n\t{params[0]} := 1;\nEND_IF;"
        else:
            return f"{params[0]} := 1;"
    return ""


def process_otl(params: List[str]) -> str:
    """Process OTL (Output Latch) instruction."""
    if params:
        return f"{params[0]} := 1;"
    return ""


def process_otu(params: List[str]) -> str:
    """Process OTU (Output Unlatch) instruction."""
    if params:
        return f"{params[0]} := 0;"
    return ""


def process_clr(params: List[str]) -> str:
    """Process CLR (Clear) instruction."""
    if params:
        return f"{params[0]} := 0;"
    return ""


def process_nop(params: List[str]) -> str:
    """Process NOP (No Operation) instruction."""
    return "(*NOP*)"


def process_ton(params: List[str], enable: str = "") -> str:
    """Process TON (Timer On) instruction."""
    if len(params) >= 3:
        timer_name = params[0]
        preset = params[1]
        accumulated = params[2]
        
        if enable:
            return f"""IF {enable} THEN
    {timer_name}.IN := 1;
    {timer_name}.PT := {preset};
    {timer_name}.Q := {timer_name}.ET >= {timer_name}.PT;
    {accumulated} := {timer_name}.ET;
ELSE
    {timer_name}.IN := 0;
    {timer_name}.ET := 0;
    {timer_name}.Q := 0;
    {accumulated} := 0;
END_IF;"""
        else:
            return f"{timer_name}.IN := 1; {timer_name}.PT := {preset}; {accumulated} := {timer_name}.ET;"
    return ""


def process_mov(params: List[str]) -> str:
    """Process MOV (Move) instruction."""
    if len(params) >= 2:
        return f"{params[1]} := {params[0]};"
    return ""


def process_cop(params: List[str]) -> str:
    """Process COP (Copy) instruction."""
    if len(params) >= 2:
        return f"{params[1]} := {params[0]};"
    return ""


def process_msg(params: List[str]) -> str:
    """Process MSG (Message) instruction."""
    if params:
        return f"(*MSG instruction: {params[0]}*)"
    return ""


def process_mul(params: List[str]) -> str:
    """Process MUL (Multiply) instruction."""
    if len(params) >= 3:
        return f"{params[2]} := {params[0]} * {params[1]};"
    return ""


def process_gsv(params: List[str]) -> str:
    """Process GSV (Get System Value) instruction."""
    if len(params) >= 4:
        class_name = params[0]
        instance_name = params[1]
        attribute_name = params[2]
        destination = params[3]
        return f"{destination} := {class_name}.{instance_name}.{attribute_name};"
    return ""


def process_ssv(params: List[str]) -> str:
    """Process SSV (Set System Value) instruction."""
    if len(params) >= 4:
        class_name = params[0]
        instance_name = params[1]
        attribute_name = params[2]
        source = params[3]
        return f"{class_name}.{instance_name}.{attribute_name} := {source};"
    return ""


def process_jsr(params: List[str], prj, tab: str) -> str:
    """Process JSR (Jump to Subroutine) instruction."""
    if params:
        routine_name = params[0]
        # This would need to be implemented to call the actual routine
        return f"{tab}(*JSR to {routine_name}*)"
    return ""


def process_function(func: str, params: List[str]) -> str:
    """Process a generic function call."""
    if func.upper() == "EQU":
        return process_equ(params)
    elif func.upper() == "NEQ":
        return process_neq(params)
    elif func.upper() == "XIC":
        return process_xic(params)
    elif func.upper() == "XIO":
        return process_xio(params)
    elif func.upper() == "OTE":
        return process_ote(params)
    elif func.upper() == "OTL":
        return process_otl(params)
    elif func.upper() == "OTU":
        return process_otu(params)
    elif func.upper() == "CLR":
        return process_clr(params)
    elif func.upper() == "NOP":
        return process_nop(params)
    elif func.upper() == "TON":
        return process_ton(params)
    elif func.upper() == "MOV":
        return process_mov(params)
    elif func.upper() == "COP":
        return process_cop(params)
    elif func.upper() == "MSG":
        return process_msg(params)
    elif func.upper() == "MUL":
        return process_mul(params)
    elif func.upper() == "GSV":
        return process_gsv(params)
    elif func.upper() == "SSV":
        return process_ssv(params)
    elif func.upper() == "JSR":
        return process_jsr(params, None, "")
    else:
        # Generic function call
        param_str = ", ".join(params) if params else ""
        return f"{func}({param_str});"


def process_sequential_function_calls(sequence: List[str]) -> str:
    """Process a sequence of function calls."""
    if not sequence:
        return ""
    
    # Join multiple function calls with semicolons
    return "; ".join(sequence)


def process_rung_instructions(text: str) -> List[str]:
    """Process rung instructions and return a list of ST statements."""
    # Split by common instruction separators
    instructions = []
    
    # This is a simplified version - the original has more complex parsing
    # Split by common patterns
    parts = text.split(';')
    for part in parts:
        part = part.strip()
        if part:
            instructions.append(part)
    
    return instructions


def process_instruction_list(instr_list: List[str], prj, tab: str) -> str:
    """Process a list of instructions and convert to ST."""
    result = []
    
    for instr in instr_list:
        # Parse the instruction
        if '(' in instr and ')' in instr:
            # Function call
            func_name = instr[:instr.find('(')].strip()
            params_str = instr[instr.find('(')+1:instr.rfind(')')]
            params = [p.strip() for p in params_str.split(',') if p.strip()]
            
            st_instr = process_function(func_name, params)
            if st_instr:
                result.append(f"{tab}{st_instr}")
        else:
            # Simple assignment or other instruction
            result.append(f"{tab}{instr};")
    
    return "\n".join(result)


def process_rung(rung_text: str, prj, tab: str) -> str:
    """Process a single rung and convert to ST."""
    # Format the rung text
    rung_text = rung_text.strip()
    
    # Handle MSG commands specially
    if "MSG" in rung_text:
        return f"{tab}(*MSG command commented out*)"
    
    # Parse the rung into instructions
    instructions = process_rung_instructions(rung_text)
    
    # Convert to ST
    return process_instruction_list(instructions, prj, tab)


def process_fbd(fbd, prj, tab: str) -> str:
    """Process a Function Block Diagram and convert to ST."""
    # This is a simplified version - FBD processing is complex
    result = []
    
    # Process FBD elements
    for element in fbd:
        if hasattr(element, 'text'):
            result.append(f"{tab}{element.text}")
    
    return "\n".join(result)


def process_routine(routine, prj, tab: str) -> str:
    """Process a routine and convert to ST."""
    result = []
    
    # Process rungs in the routine
    for rung in routine.rungs:
        rung_text = rung.text if hasattr(rung, 'text') else str(rung)
        st_rung = process_rung(rung_text, prj, tab)
        if st_rung:
            result.append(st_rung)
    
    return "\n".join(result)


def process_routines(routines, prj) -> str:
    """Process multiple routines and convert to ST."""
    result = []
    
    for routine_name, routine in routines.items():
        if routine_name != "MainProgram":
            result.append(f"(*Routine: {routine_name}*)")
            st_routine = process_routine(routine, prj, "\t")
            result.append(st_routine)
    
    return "\n".join(result) 