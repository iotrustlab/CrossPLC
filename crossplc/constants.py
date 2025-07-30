"""Constants used throughout the L5X-ST compiler."""

from typing import Dict, List, Set

# Comparison Operators
COMPARISON_OPERATORS = ["<=", ">=", "=", "<>", "<", ">"]

# Logical Operators
LOGICAL_OPERATORS = ["NOT", "AND", "&", "XOR", "OR"]

# Arithmetic Operators
ARITHMETIC_OPERATORS = ["-", "+", "**", "*", "/", "MOD"]

# Functions that need special handling for input/output
INOUT_FUNCS_TO_BE_REPLACED = ["SCL", "ALM"]

# Duplicate function block names
DUPLICATE_FBDS = ["Duty2_FBD"]

# Main Program name used for current configuration
MAIN_PROGRAM = "MainProgram"

# RIO Channel data headers
RIO_CHANNELS = ["RIO1:", "RIO2:", "RIO3:", "RIO4:", "RIO5:", "RIO6:"]

# Bit access helper variable name
BIT_ACCESS_HELPER = "bit_access_helper"

# Reserved words mapping
RESERVED_WORDS: Dict[str, str] = {
    "ON": "ON1",
    "type": "TYPE1",
    "EN": "EN1",
    "SCALE": "scl1",
    "alm": "alarm1",
    "Alarm": "alert",
    "ALARM": "alert",
    "TON": "TON1",
    "R_TRIG": "R_TRIG1",
    "TO": "TO1",
    # These were misspelled words that added inconsistency in struct declarations:
    "SHUTODWN1": "SHUTDOWN1",
    "SHUTODWN2": "SHUTDOWN2",
    "SHUTODWN3": "SHUTDOWN3",
    "SHUTODWN4": "SHUTDOWN4",
    "SHUTODWN5": "SHUTDOWN5",
    "SHUTDOWN": "Shutdown",
    "status": "Status",
    "STATUS": "Status",
    "HTY": "Hty",
    "AVL": "Avl"
}

# Unimplemented data types mapping
UNIMPLEMENTED_TYPES: Dict[str, str] = {
    "BIT": "BOOL",
    "TIMER": "TIME"  # This may not be correct, but it's not used
}

# Auxiliary functions definitions
AUXILIARY_FUNCTIONS: Dict[str, str] = {
    "SETD: BOOL": """FUNCTION SETD : BOOL
    VAR_INPUT
        SD : DOMINANT_SET;
    END_VAR
    SETD := SD.Out;
    IF SD.EnableIn THEN
        IF SD.Set THEN
            SETD:= 1;
        ELSE
            IF SD.Reset THEN
                SETD := 0;
            END_IF;
        END_IF;
    END_IF;
END_FUNCTION""",
    
    "SCL: SCALE": """FUNCTION SCL: SCALE
    VAR_INPUT
        scale1  :  SCALE ;
    END_VAR
    SCL := scale1;
    SCL.Out := (scale1.In -scale1.InRawMin) * ((scale1.InEUMax - scale1.InEUMin)/(scale1.InRawMax - scale1.InRawMin)) + scale1.InEUMin;
END_FUNCTION""",
    
    "ALM: ALARM": """FUNCTION ALM: ALARM
    VAR_INPUT
        alm1  :  ALARM ;
    END_VAR
    ALM := alm1;

    (* High-high to Low-low Alarms*)
    (*HHAlarm*)
    IF (alm1.HHAlarm = FALSE) AND (alm1.In >= alm1.HHLimit) THEN
        ALM.HHAlarm := TRUE;
    ELSIF (alm1.HHAlarm = TRUE) AND (alm1.In < (alm1.HHLimit-alm1.Deadband)) THEN
        ALM.HHAlarm := FALSE;
    END_IF;

    (*HAlarm*)
    IF (alm1.HAlarm = FALSE) AND (alm1.In >= alm1.HLimit) THEN
        ALM.HAlarm := TRUE;
    ELSIF (alm1.HAlarm = TRUE) AND (alm1.In < (alm1.HLimit-alm1.Deadband)) THEN
        ALM.HAlarm := FALSE;
    END_IF;

    (*LLAlarm*)
    IF (alm1.LLAlarm = FALSE) AND (alm1.In <= alm1.LLLimit) THEN
        ALM.LLAlarm := TRUE;
    ELSIF (alm1.LLAlarm= TRUE) AND (alm1.In > (alm1.LLLimit+alm1.Deadband)) THEN
        ALM.LLAlarm := FALSE;
    END_IF;

    (*LAlarm*)
    IF (alm1.LAlarm = FALSE) AND (alm1.In <= alm1.LLimit) THEN
        ALM.LAlarm := TRUE;
    ELSIF (alm1.LAlarm = TRUE) AND (alm1.In > (alm1.LLimit+alm1.Deadband)) THEN
        ALM.LAlarm := FALSE;
    END_IF;
    (*TODO: Implement ROC alarms*)
END_FUNCTION""",
    
    "OSRI: BOOL": """FUNCTION OSRI :BOOL
    VAR_INPUT    
        EnableIn  :  BOOL ;
        InputBit  :  BOOL ;
    END_VAR
    OSRI := 0;
    IF InputBit THEN
        InputBit := 1;
        OSRI := 1;
    END_IF;
END_FUNCTION""",
    
    "MSG: MESSAGE": """(*The MSG instruction transfers elements of data.*)
FUNCTION MSG: MESSAGE
    VAR_INPUT
        Msg1  :  MESSAGE ;
    END_VAR
    (*Clear the prescan bits*)
    MSG := Msg1;
    MSG.EW := 0;
    MSG.ST := 0;
    MSG.DN := 0;
    MSG.ER := 0;

    (*Main flow*)
    IF MSG.EN1 = 1 OR (MSG.EW = 0 AND MSG.ST = 0) THEN
        IF MSG.EN1 = 0 THEN
            MSG.EW := 0;
            MSG.ST := 0;
            MSG.TO1 := 0;
            MSG.DN := 0;
            MSG.ER := 0;
        END_IF;

        IF MSG.EW = 0 AND MSG.ST = 0 AND MSG.DN = 0 AND MSG.ER = 0 THEN
            (*TODO: implement block transfer command (BTC)*)
            (*If BTC and (not (module path valid) OR not (module connection))*)
            MSG.ER := 1;
            (*ELSE*)
            MSG.EW := 0;
            MSG.ST := 0;
            MSG.TO1 := 0;
            MSG.DN := 0;
            MSG.ER := 0;
            MSG.EN1 := 1;
            (*TODO: Execute message request*)
            MSG.EW := 1;
        END_IF;
    (*ELSE, .EN1 bit = 0 AND (EW OR ST = 1)*)
    ELSE
        MSG.EN1 := 1;
    END_IF;
END_FUNCTION"""
}

# Auxiliary struct definitions
AUXILIARY_STRUCTS: Dict[str, str] = {
    "DOMINANT_SET": """TYPE  DOMINANT_SET :
    STRUCT
        EnableIn: BOOL;
        Set : BOOL;
        Reset: BOOL;
        EnableOut : BOOL;
        Out : BOOL;
        OutNot : BOOL;
    END_STRUCT;
END_TYPE""",
    
    "MESSAGE": """TYPE MESSAGE:
    STRUCT
        FLAGS : INT;
        ERR: INT;
        EXERR: INT;
        REQ_LEN: INT;
        DN_LEN: INT;
        EW: BOOL;
        ER: BOOL;
        DN: BOOL;
        ST: BOOL;
        EN1: BOOL;
        TO1: BOOL;
        EN_CC: BOOL;
        ERR_SRC: SINT;
        DestinationLink: INT;
        DestinationNode: INT;
        SourceLink: INT;
        Class: INT;
        Attribute: INT;
        Instance: DINT;
        LocalIndex: DINT;
        Channel: SINT;
        Rack: SINT;
        Group: SINT;
        Slot: SINT;
        Path: STRING;
        RemoteIndex: DINT;
        RemoteElement: STRING;
        UnconnectedTimeOut: DINT;
        ConnectionRate: DINT;
        TimeoutMultiplier: SINT;
        ConnectedFlag: UINT;
        Description: STRING;
        MessageType: STRING;
        LocalElement: STRING;
        AttributeNumber: UINT;
        LargePacketUsage: BOOL;
        TargetObject: STRING;
        CommTypeCode: USINT;
        RequestedLength: INT;
        ConnectionPath: STRING;
        CacheConnections: BOOL;
        DestinationTag: STRING;
        ObjectType: UINT;
        ServiceCode : UINT;
    END_STRUCT;
END_TYPE"""
}

# Hard-coded Configuration
CONFIGURATION = """CONFIGURATION Config0
    RESOURCE Res0 ON PLC
        TASK Task1(INTERVAL := T#1s,PRIORITY := 0);
        PROGRAM Inst0 WITH Task1 : prog0;
    END_RESOURCE
END_CONFIGURATION"""

# L5X Tag Types
L5X_TAG_TYPES = {
    'Base': 'Base',
    'Alias': 'Alias',
    'Produced': 'Produced',
    'Consumed': 'Consumed'
}

# L5X Data Types
L5X_DATA_TYPES = {
    'BOOL': 'BOOL',
    'SINT': 'SINT',
    'INT': 'INT',
    'DINT': 'DINT',
    'LINT': 'LINT',
    'USINT': 'USINT',
    'UINT': 'UINT',
    'UDINT': 'UDINT',
    'ULINT': 'ULINT',
    'REAL': 'REAL',
    'LREAL': 'LREAL',
    'TIME': 'TIME',
    'DATE': 'DATE',
    'TOD': 'TOD',
    'DT': 'DT',
    'STRING': 'STRING',
    'BYTE': 'BYTE',
    'WORD': 'WORD',
    'DWORD': 'DWORD',
    'LWORD': 'LWORD'
}

# L5X Instructions
L5X_INSTRUCTIONS = {
    'XIC': 'XIC',
    'XIO': 'XIO',
    'OTE': 'OTE',
    'OTL': 'OTL',
    'OTU': 'OTU',
    'TON': 'TON',
    'TOF': 'TOF',
    'CTU': 'CTU',
    'CTD': 'CTD',
    'CTUD': 'CTUD',
    'MOV': 'MOV',
    'ADD': 'ADD',
    'SUB': 'SUB',
    'MUL': 'MUL',
    'DIV': 'DIV',
    'COP': 'COP',
    'CPS': 'CPS',
    'FLL': 'FLL',
    'FOR': 'FOR',
    'NXT': 'NXT',
    'JMP': 'JMP',
    'LBL': 'LBL',
    'JSR': 'JSR',
    'SBR': 'SBR',
    'RET': 'RET',
    'END': 'END'
}

# ST Data Types
ST_DATA_TYPES = {
    'BOOL': 'BOOL',
    'SINT': 'SINT',
    'INT': 'INT',
    'DINT': 'DINT',
    'LINT': 'LINT',
    'USINT': 'USINT',
    'UINT': 'UINT',
    'UDINT': 'UDINT',
    'ULINT': 'ULINT',
    'REAL': 'REAL',
    'LREAL': 'LREAL',
    'TIME': 'TIME',
    'DATE': 'DATE',
    'TOD': 'TOD',
    'DT': 'DT',
    'STRING': 'STRING',
    'BYTE': 'BYTE',
    'WORD': 'WORD',
    'DWORD': 'DWORD',
    'LWORD': 'LWORD'
}

# ST Instructions
ST_INSTRUCTIONS = {
    'XIC': 'IF',
    'XIO': 'IF NOT',
    'OTE': ':=',
    'OTL': ':= TRUE',
    'OTU': ':= FALSE',
    'TON': 'TON',
    'TOF': 'TOF',
    'CTU': 'CTU',
    'CTD': 'CTD',
    'CTUD': 'CTUD',
    'MOV': ':=',
    'ADD': '+',
    'SUB': '-',
    'MUL': '*',
    'DIV': '/',
    'COP': ':=',
    'CPS': ':=',
    'FLL': ':=',
    'FOR': 'FOR',
    'NXT': 'END_FOR',
    'JMP': 'GOTO',
    'LBL': 'LABEL',
    'JSR': 'CALL',
    'SBR': 'FUNCTION',
    'RET': 'RETURN',
    'END': 'END_IF'
} 