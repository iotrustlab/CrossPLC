"""Ladder Logic to Structured Text translation module."""

import re
from typing import List, Dict, Any, Optional


class LLFunc:
    """Ladder Logic Function class for processing Rockwell instructions."""
    
    def __init__(self, fname: str, params: str):
        self.fname = fname
        self.params = params.split(",") if params else []
        
        # Clean up parameters
        self.params = [p.strip() for p in self.params if p.strip()]
        
        # Check if function is conditional
        if fname in CONDITIONAL_FUNCTIONS:
            self.conditional = True
        else:
            self.conditional = False


# Function mappings
CONDITIONAL_FUNCTIONS = {
    "EQU": "equ", "NEQ": "neq", "XIC": "xic", "XIO": "xio",
    "GRT": "grt", "GEQ": "geq", "LES": "les", "LEQ": "leq"
}

REGULAR_FUNCTIONS = {
    "COP": "cop", "CLR": "clr", "GSV": "gsv", "JSR": "jsr",
    "MOV": "mov", "MSG": "msg", "MUL": "mul", "NOP": "nop",
    "OTE": "ote", "OTL": "otl", "OTU": "otu", "SSV": "ssv",
    "TON": "ton", "TOF": "tof", "TONR": "tonr", "RES": "res",
    "CTU": "ctu", "CTD": "ctd", "CTUD": "ctud",
    "ADD": "add", "SUB": "sub", "DIV": "div", "MOD": "mod",
    "SQR": "sqr", "ABS": "abs",
    "OSR": "osr", "OSF": "osf", "RTRIG": "rtrig", "FTRIG": "ftrig",
    "BTD": "btd", "DTB": "dtb", "FRD": "frd", "TOD": "tod"
}


def xic(params: List[str]) -> str:
    """XIC: examine if bit is on."""
    if not params:
        return "(FALSE)"
    
    conditions = []
    for p in params:
        conditions.append(f"({p} = 1)")
    
    return "(" + " AND ".join(conditions) + ")"


def xio(params: List[str]) -> str:
    """XIO: examine if bit is off."""
    if not params:
        return "(FALSE)"
    
    conditions = []
    for p in params:
        conditions.append(f"({p} = 0)")
    
    return "(" + " AND ".join(conditions) + ")"


def equ(params: List[str]) -> str:
    """EQU: equal comparison."""
    if len(params) != 2:
        return "(FALSE)"
    return f"({params[0]} = {params[1]})"


def neq(params: List[str]) -> str:
    """NEQ: not equal comparison."""
    if len(params) != 2:
        return "(FALSE)"
    return f"({params[0]} <> {params[1]})"


def ote(params: List[str], condition: bool = True) -> str:
    """OTE: output energize - sets or clears a data bit."""
    if len(params) != 1:
        return "// ERROR: OTE requires exactly 1 parameter"
    
    value = "1" if condition else "0"
    return f"{params[0]} := {value};"


def otl(params: List[str]) -> str:
    """OTL: output latch - sets data bit true."""
    if len(params) != 1:
        return "// ERROR: OTL requires exactly 1 parameter"
    return f"{params[0]} := 1;"


def otu(params: List[str]) -> str:
    """OTU: output unlatch - clears data bit."""
    if len(params) != 1:
        return "// ERROR: OTU requires exactly 1 parameter"
    return f"{params[0]} := 0;"


def clr(params: List[str]) -> str:
    """CLR: clear all bits of destination."""
    if len(params) != 1:
        return "// ERROR: CLR requires exactly 1 parameter"
    return f"{params[0]} := 0;"


def nop(params: List[str]) -> str:
    """NOP: no operation."""
    return "// NOP instruction"


def gsv(params: List[str]) -> str:
    """GSV: get system value."""
    if len(params) != 4:
        return "// ERROR: GSV requires exactly 4 parameters"
    
    parts = []
    if params[0] != "?":
        parts.append(f"ClassName := {params[0]}")
    if params[1] != "?":
        parts.append(f"InstanceName := {params[1]}")
    if params[2] != "?":
        parts.append(f"AttributeName := {params[2]}")
    if params[3] != "?":
        parts.append(f"Dest := {params[3]}")
    
    return f"GSV({', '.join(parts)});"


def ssv(params: List[str]) -> str:
    """SSV: set system value."""
    if len(params) != 4:
        return "// ERROR: SSV requires exactly 4 parameters"
    return f"SSV({params[0]}, {params[1]}, {params[2]}, {params[3]});"


def jsr(params: List[str], routine_name: str = "") -> str:
    """JSR: jump to subroutine."""
    if len(params) != 1:
        return "// ERROR: JSR requires exactly 1 parameter"
    
    routine = params[0]
    return f"// JSR to {routine} routine\n// TODO: Process {routine} routine content"


def ton(params: List[str], enable: bool = True) -> str:
    """TON: timer on delay."""
    if len(params) != 2:
        return "// ERROR: TON requires exactly 2 parameters"
    
    timer_name = params[0]
    preset_value = params[1]
    enable_str = "TRUE" if enable else "FALSE"
    
    return f"{timer_name}.PRE := {preset_value};\n{timer_name}.TimerEnable := {enable_str};\nTONR({timer_name});"


def mov(params: List[str]) -> str:
    """MOV: move instruction - same as assignment in ST."""
    if len(params) != 2:
        return "// ERROR: MOV requires exactly 2 parameters"
    return f"{params[1]} := {params[0]};"


def cop(params: List[str]) -> str:
    """COP: copy file instruction."""
    if len(params) != 3:
        return "// ERROR: COP requires exactly 3 parameters"
    return f"COP({params[0]}, {params[1]}, {params[2]});"


def msg(params: List[str]) -> str:
    """MSG: message instruction - commented out for now."""
    if len(params) != 1:
        return "// ERROR: MSG requires exactly 1 parameter"
    return f"// MSG({params[0]}) - commented out"


def mul(params: List[str]) -> str:
    """MUL: multiplication instruction."""
    if len(params) != 3:
        return "// ERROR: MUL requires exactly 3 parameters"
    return f"{params[2]} := {params[0]} * {params[1]};"


# Additional comparison functions
def grt(params: List[str]) -> str:
    """GRT: greater than comparison."""
    if len(params) != 2:
        return "(FALSE)"
    return f"({params[0]} > {params[1]})"


def geq(params: List[str]) -> str:
    """GEQ: greater than or equal comparison."""
    if len(params) != 2:
        return "(FALSE)"
    return f"({params[0]} >= {params[1]})"


def les(params: List[str]) -> str:
    """LES: less than comparison."""
    if len(params) != 2:
        return "(FALSE)"
    return f"({params[0]} < {params[1]})"


def leq(params: List[str]) -> str:
    """LEQ: less than or equal comparison."""
    if len(params) != 2:
        return "(FALSE)"
    return f"({params[0]} <= {params[1]})"


# Timer functions
def tof(params: List[str], enable: bool = True) -> str:
    """TOF: timer off delay."""
    if len(params) != 2:
        return "// ERROR: TOF requires exactly 2 parameters"
    
    timer_name = params[0]
    preset_value = params[1]
    enable_str = "TRUE" if enable else "FALSE"
    
    return f"{timer_name}.PRE := {preset_value};\n{timer_name}.TimerEnable := {enable_str};\nTOFR({timer_name});"


def tonr(params: List[str], enable: bool = True) -> str:
    """TONR: timer on delay retentive."""
    if len(params) != 2:
        return "// ERROR: TONR requires exactly 2 parameters"
    
    timer_name = params[0]
    preset_value = params[1]
    enable_str = "TRUE" if enable else "FALSE"
    
    return f"{timer_name}.PRE := {preset_value};\n{timer_name}.TimerEnable := {enable_str};\nTONR({timer_name});"


def res(params: List[str]) -> str:
    """RES: reset timer/counter."""
    if len(params) != 1:
        return "// ERROR: RES requires exactly 1 parameter"
    return f"{params[0]}.Reset := 1;"


# Counter functions
def ctu(params: List[str], enable: bool = True) -> str:
    """CTU: counter up."""
    if len(params) != 3:
        return "// ERROR: CTU requires exactly 3 parameters"
    
    counter_name = params[0]
    preset_value = params[1]
    reset_condition = params[2]
    enable_str = "TRUE" if enable else "FALSE"
    
    return f"{counter_name}.PRE := {preset_value};\n{counter_name}.CU := {enable_str};\n{counter_name}.RES := {reset_condition};\nCTU({counter_name});"


def ctd(params: List[str], enable: bool = True) -> str:
    """CTD: counter down."""
    if len(params) != 3:
        return "// ERROR: CTD requires exactly 3 parameters"
    
    counter_name = params[0]
    preset_value = params[1]
    reset_condition = params[2]
    enable_str = "TRUE" if enable else "FALSE"
    
    return f"{counter_name}.PRE := {preset_value};\n{counter_name}.CD := {enable_str};\n{counter_name}.RES := {reset_condition};\nCTD({counter_name});"


def ctud(params: List[str], enable: bool = True) -> str:
    """CTUD: counter up/down."""
    if len(params) != 4:
        return "// ERROR: CTUD requires exactly 4 parameters"
    
    counter_name = params[0]
    preset_value = params[1]
    up_condition = params[2]
    down_condition = params[3]
    enable_str = "TRUE" if enable else "FALSE"
    
    return f"{counter_name}.PRE := {preset_value};\n{counter_name}.CU := {up_condition};\n{counter_name}.CD := {down_condition};\nCTUD({counter_name});"


# Math functions
def add(params: List[str]) -> str:
    """ADD: addition instruction."""
    if len(params) != 3:
        return "// ERROR: ADD requires exactly 3 parameters"
    return f"{params[2]} := {params[0]} + {params[1]};"


def sub(params: List[str]) -> str:
    """SUB: subtraction instruction."""
    if len(params) != 3:
        return "// ERROR: SUB requires exactly 3 parameters"
    return f"{params[2]} := {params[0]} - {params[1]};"


def div(params: List[str]) -> str:
    """DIV: division instruction."""
    if len(params) != 3:
        return "// ERROR: DIV requires exactly 3 parameters"
    return f"{params[2]} := {params[0]} / {params[1]};"


def mod(params: List[str]) -> str:
    """MOD: modulo instruction."""
    if len(params) != 3:
        return "// ERROR: MOD requires exactly 3 parameters"
    return f"{params[2]} := {params[0]} MOD {params[1]};"


def sqr(params: List[str]) -> str:
    """SQR: square root instruction."""
    if len(params) != 2:
        return "// ERROR: SQR requires exactly 2 parameters"
    return f"{params[1]} := SQRT({params[0]});"


def abs(params: List[str]) -> str:
    """ABS: absolute value instruction."""
    if len(params) != 2:
        return "// ERROR: ABS requires exactly 2 parameters"
    return f"{params[1]} := ABS({params[0]});"


# One-shot and trigger functions
def osr(params: List[str]) -> str:
    """OSR: one shot rising."""
    if len(params) != 2:
        return "// ERROR: OSR requires exactly 2 parameters"
    return f"OSR({params[0]}, {params[1]});"


def osf(params: List[str]) -> str:
    """OSF: one shot falling."""
    if len(params) != 2:
        return "// ERROR: OSF requires exactly 2 parameters"
    return f"OSF({params[0]}, {params[1]});"


def rtrig(params: List[str]) -> str:
    """RTRIG: rising trigger."""
    if len(params) != 1:
        return "// ERROR: RTRIG requires exactly 1 parameter"
    return f"RTRIG({params[0]});"


def ftrig(params: List[str]) -> str:
    """FTRIG: falling trigger."""
    if len(params) != 1:
        return "// ERROR: FTRIG requires exactly 1 parameter"
    return f"FTRIG({params[0]});"


# Data conversion functions
def btd(params: List[str]) -> str:
    """BTD: binary to decimal."""
    if len(params) != 2:
        return "// ERROR: BTD requires exactly 2 parameters"
    return f"{params[1]} := BCD_TO_INT({params[0]});"


def dtb(params: List[str]) -> str:
    """DTB: decimal to binary."""
    if len(params) != 2:
        return "// ERROR: DTB requires exactly 2 parameters"
    return f"{params[1]} := INT_TO_BCD({params[0]});"


def frd(params: List[str]) -> str:
    """FRD: from real to decimal."""
    if len(params) != 2:
        return "// ERROR: FRD requires exactly 2 parameters"
    return f"{params[1]} := REAL_TO_INT({params[0]});"


def tod(params: List[str]) -> str:
    """TOD: to decimal."""
    if len(params) != 2:
        return "// ERROR: TOD requires exactly 2 parameters"
    return f"{params[1]} := INT_TO_REAL({params[0]});"


# Function dictionaries
CONDITIONAL_FUNCTIONS_IMPL = {
    "EQU": equ, "NEQ": neq, "XIC": xic, "XIO": xio,
    "GRT": grt, "GEQ": geq, "LES": les, "LEQ": leq
}

REGULAR_FUNCTIONS_IMPL = {
    "COP": cop, "CLR": clr, "GSV": gsv, "JSR": jsr,
    "MOV": mov, "MSG": msg, "MUL": mul, "NOP": nop,
    "OTE": ote, "OTL": otl, "OTU": otu, "SSV": ssv,
    "TON": ton, "TOF": tof, "TONR": tonr, "RES": res,
    "CTU": ctu, "CTD": ctd, "CTUD": ctud,
    "ADD": add, "SUB": sub, "DIV": div, "MOD": mod,
    "SQR": sqr, "ABS": abs,
    "OSR": osr, "OSF": osf, "RTRIG": rtrig, "FTRIG": ftrig,
    "BTD": btd, "DTB": dtb, "FRD": frd, "TOD": tod
}


def format_rung_text(text: str) -> str:
    """Format rung text to separate function calls with semicolons."""
    formatted = text.replace(' ', '')
    start = 0
    
    # Replace commas that separate function calls with semicolons
    offset = formatted.find("(")
    while offset != -1:
        formatted = (formatted[:start] + 
                    formatted[start:offset].replace(",", ";").replace('[', '<').replace(']', '>') + 
                    formatted[offset:])
        start = formatted[offset:].find(")") + offset
        offset = formatted[start:].find("(")
        if offset != -1:
            offset = offset + start
    
    if start != -1:
        formatted = formatted[:start] + formatted[start:].replace(']', '>')
    
    return formatted


def process_function(func: str, params: str) -> LLFunc:
    """Process a function call and return LLFunc object."""
    return LLFunc(func, params)


def process_sequential_function_calls(sequence: str) -> List[LLFunc]:
    """Process sequential function calls in a sequence."""
    tokenized = sequence.replace(' ', '').replace("(", ' ').replace(")", ' ').split()
    
    func_list = []
    if len(tokenized) == 1:
        func_list.append(process_function(tokenized[0].replace(',', '').replace(' ', ''), ""))
    else:
        for i in range(0, len(tokenized) - 1, 2):
            func_list.append(process_function(
                tokenized[i].replace(',', '').replace(' ', ''),
                tokenized[i + 1]
            ))
    
    return func_list


def process_rung_instructions(text: str) -> List[List[List[LLFunc]]]:
    """Process rung instructions and return structured instruction list."""
    instr_list = []
    tokenized = text.replace(' ', '').replace('<', ' ').replace('>', ' ').split(' ')
    
    for block in tokenized:
        seq_blocks = block.split(";")
        disj_list = []
        for sequence in seq_blocks:
            flist = process_sequential_function_calls(sequence)
            if flist:
                disj_list.append(flist)
        if disj_list:
            instr_list.append(disj_list)
    
    return instr_list


def process_instruction_list(instr_list: List[List[List[LLFunc]]], tab: str = "") -> str:
    """Process instruction list and convert to ST code."""
    s = ""
    current_tab = tab
    
    # Check if there is a conditional rung
    if len(instr_list) > 1:
        s = "IF ("
        i = 0
        for flist in instr_list[0]:
            j = 0
            for f in flist:
                if not f.conditional:
                    s += "// ERROR: Non-conditional instruction at beginning of rung\n"
                    continue
                
                if f.fname in CONDITIONAL_FUNCTIONS_IMPL:
                    s += CONDITIONAL_FUNCTIONS_IMPL[f.fname](f.params)
                else:
                    s += f"// Unknown conditional function: {f.fname}\n"
                
                j += 1
                if j < len(flist):
                    s += " AND "
            i += 1
            if i < len(instr_list[0]):
                s += " OR "
        s += ") THEN\n"
        current_tab = tab + "\t"
    
    # Process regular instructions
    instruction_index = 1 if len(instr_list) > 1 else 0
    if instruction_index < len(instr_list):
        for flist in instr_list[instruction_index]:
            conditional_func_list = []
            
            for f in flist:
                if f.conditional:
                    conditional_func_list.append(f)
                else:
                    # Handle conditional functions within regular statements
                    if conditional_func_list:
                        s += current_tab + "IF ("
                        i = 0
                        for cf in conditional_func_list:
                            if cf.fname in CONDITIONAL_FUNCTIONS_IMPL:
                                s += CONDITIONAL_FUNCTIONS_IMPL[cf.fname](cf.params)
                            else:
                                s += f"// Unknown conditional function: {cf.fname}"
                            i += 1
                            if i < len(conditional_func_list):
                                s += " AND "
                        s += ") THEN\n"
                        current_tab = current_tab + "\t"
                    
                    # Process regular function
                    if f.fname in REGULAR_FUNCTIONS_IMPL:
                        if f.fname == "OTE":
                            s += current_tab + REGULAR_FUNCTIONS_IMPL[f.fname](f.params, True) + "\n"
                        elif f.fname == "TON":
                            s += current_tab + REGULAR_FUNCTIONS_IMPL[f.fname](f.params, True) + "\n"
                        elif f.fname == "JSR":
                            s += current_tab + REGULAR_FUNCTIONS_IMPL[f.fname](f.params) + "\n"
                        else:
                            s += current_tab + REGULAR_FUNCTIONS_IMPL[f.fname](f.params) + "\n"
                    else:
                        s += current_tab + f"// Unknown function: {f.fname}({', '.join(f.params)})\n"
                    
                    # Handle OTE else clause
                    if conditional_func_list and f.fname == "OTE":
                        s += current_tab.replace("\t", "", 1) + "ELSE\n"
                        s += current_tab + REGULAR_FUNCTIONS_IMPL[f.fname](f.params, False) + "\n"
                    
                    if conditional_func_list:
                        current_tab = current_tab.replace("\t", "", 1)
                        s += current_tab + "END_IF;\n"
                        conditional_func_list = []
    
    if len(instr_list) > 1:
        s += "END_IF;\n"
    
    return s


def process_rung(rung_text: str) -> str:
    """Process a single rung and convert to ST code."""
    # Format the rung text
    formatted_text = format_rung_text(rung_text)
    
    # Process the instructions
    instr_list = process_rung_instructions(formatted_text)
    
    # Convert to ST code
    st_code = process_instruction_list(instr_list)
    
    return st_code


def translate_ladder_to_st(ladder_text: str) -> str:
    """Main function to translate ladder logic text to Structured Text."""
    try:
        return process_rung(ladder_text)
    except Exception as e:
        return f"// Error translating ladder logic: {e}\n// Original: {ladder_text}" 