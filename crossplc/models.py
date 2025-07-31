"""
Data models for L5X to ST conversion.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union, Set
from enum import Enum
from ordered_set import OrderedSet


class DataType(Enum):
    """Standard IEC 61131-3 data types."""
    BOOL = "BOOL"
    SINT = "SINT"
    INT = "INT"
    DINT = "DINT"
    LINT = "LINT"
    USINT = "USINT"
    UINT = "UINT"
    UDINT = "UDINT"
    ULINT = "ULINT"
    REAL = "REAL"
    LREAL = "LREAL"
    TIME = "TIME"
    DATE = "DATE"
    TIME_OF_DAY = "TIME_OF_DAY"
    DATE_AND_TIME = "DATE_AND_TIME"
    STRING = "STRING"
    BYTE = "BYTE"
    WORD = "WORD"
    DWORD = "DWORD"
    LWORD = "LWORD"


class RoutineType(Enum):
    """Routine types."""
    ST = "ST"
    RLL = "RLL"
    FBD = "FBD"
    SFC = "SFC"
    LAD = "LAD"


class TagScope(Enum):
    """Tag scope types."""
    CONTROLLER = "Controller"
    PROGRAM = "Program"


@dataclass
class TagInfo:
    """Information about a tag."""
    name: str
    data_type: str
    scope: TagScope
    value: Optional[str] = None
    description: Optional[str] = None
    external_access: Optional[str] = None
    radix: Optional[str] = None
    constant: bool = False
    alias_for: Optional[str] = None


@dataclass
class DataTypeInfo:
    """Information about a user-defined data type."""
    name: str
    base_type: Optional[str] = None
    members: List['DataTypeMember'] = field(default_factory=list)
    description: Optional[str] = None


@dataclass
class DataTypeMember:
    """Member of a user-defined data type."""
    name: str
    data_type: str
    description: Optional[str] = None
    radix: Optional[str] = None
    external_access: Optional[str] = None


@dataclass
class FunctionBlockInfo:
    """Information about a function block."""
    name: str
    description: Optional[str] = None
    parameters: List['FunctionBlockParameter'] = field(default_factory=list)
    local_variables: List['FunctionBlockParameter'] = field(default_factory=list)


@dataclass
class FunctionBlockParameter:
    """Parameter of a function block."""
    name: str
    data_type: str
    parameter_type: str  # Input, Output, InOut
    description: Optional[str] = None
    required: bool = True


@dataclass
class RoutineInfo:
    """Information about a routine."""
    name: str
    routine_type: RoutineType
    content: str
    description: Optional[str] = None
    local_variables: List[TagInfo] = field(default_factory=list)


@dataclass
class ProgramInfo:
    """Information about a program."""
    name: str
    description: Optional[str] = None
    main_routine: Optional[str] = None
    routines: List[RoutineInfo] = field(default_factory=list)
    tags: List[TagInfo] = field(default_factory=list)


@dataclass
class ControllerInfo:
    """Information about a controller."""
    name: str
    description: Optional[str] = None
    tags: List[TagInfo] = field(default_factory=list)
    data_types: List[DataTypeInfo] = field(default_factory=list)
    function_blocks: List[FunctionBlockInfo] = field(default_factory=list)


@dataclass
class L5XProject:
    """Complete L5X project information."""
    controller: ControllerInfo
    programs: List[ProgramInfo] = field(default_factory=list)
    modules: List[Any] = field(default_factory=list)  # TODO: Define module structure
    tasks: List[Any] = field(default_factory=list)    # TODO: Define task structure


# Intermediate Representation Models
@dataclass
class IRTag:
    """Intermediate representation of a tag."""
    name: str
    data_type: str
    scope: TagScope
    value: Optional[str] = None
    description: Optional[str] = None
    external_access: Optional[str] = None
    radix: Optional[str] = None
    constant: bool = False
    alias_for: Optional[str] = None
    array_dimensions: Optional[List[int]] = None
    initial_value: Optional[str] = None
    user_defined_type: Optional[str] = None


@dataclass
class IRDataType:
    """Intermediate representation of a data type."""
    name: str
    base_type: Optional[str] = None
    members: List['IRDataTypeMember'] = field(default_factory=list)
    description: Optional[str] = None
    is_enum: bool = False
    enum_values: List[str] = field(default_factory=list)


@dataclass
class IRDataTypeMember:
    """Intermediate representation of a data type member."""
    name: str
    data_type: str
    description: Optional[str] = None
    radix: Optional[str] = None
    external_access: Optional[str] = None
    array_dimensions: Optional[List[int]] = None
    initial_value: Optional[str] = None


@dataclass
class IRFunctionBlock:
    """Intermediate representation of a function block."""
    name: str
    description: Optional[str] = None
    parameters: List['IRFunctionBlockParameter'] = field(default_factory=list)
    local_variables: List['IRFunctionBlockParameter'] = field(default_factory=list)
    implementation: Optional[str] = None


@dataclass
class IRFunctionBlockParameter:
    """Intermediate representation of a function block parameter."""
    name: str
    data_type: str
    parameter_type: str  # Input, Output, InOut
    description: Optional[str] = None
    required: bool = True
    array_dimensions: Optional[List[int]] = None
    initial_value: Optional[str] = None


@dataclass
class IRRoutine:
    """Intermediate representation of a routine."""
    name: str
    routine_type: RoutineType
    content: str
    description: Optional[str] = None
    local_variables: List[IRTag] = field(default_factory=list)
    parameters: List[IRFunctionBlockParameter] = field(default_factory=list)
    return_type: Optional[str] = None


@dataclass
class IRProgram:
    """Intermediate representation of a program."""
    name: str
    description: Optional[str] = None
    main_routine: Optional[str] = None
    routines: List[IRRoutine] = field(default_factory=list)
    tags: List[IRTag] = field(default_factory=list)
    local_variables: List[IRTag] = field(default_factory=list)
    source_type: Optional[str] = None  # "rockwell", "openplc", etc.


@dataclass
class IRController:
    """Intermediate representation of a controller."""
    name: str
    description: Optional[str] = None
    tags: List[IRTag] = field(default_factory=list)
    data_types: List[IRDataType] = field(default_factory=list)
    function_blocks: List[IRFunctionBlock] = field(default_factory=list)
    global_variables: List[IRTag] = field(default_factory=list)
    source_type: Optional[str] = None  # "rockwell", "openplc", etc.
    fsm: Optional['IRStateMachine'] = None  # Derived FSM from control flow


@dataclass
class IRProject:
    """Complete intermediate representation of an L5X project."""
    controller: IRController
    programs: List[IRProgram] = field(default_factory=list)
    modules: List[Any] = field(default_factory=list)
    tasks: List[Any] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_type: Optional[str] = None  # "rockwell", "openplc", etc.


# Conversion tracking models
@dataclass
class ConversionMetadata:
    """Metadata about the conversion process."""
    source_file: str
    conversion_time: str
    converter_version: str
    original_components: Dict[str, int] = field(default_factory=dict)
    converted_components: Dict[str, int] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class ComponentMapping:
    """Mapping between original and converted components."""
    original_name: str
    converted_name: str
    component_type: str
    conversion_notes: Optional[str] = None


@dataclass
class RoundTripInfo:
    """Information for round-trip conversion tracking."""
    original_project: IRProject
    converted_project: IRProject
    metadata: ConversionMetadata
    component_mappings: List[ComponentMapping] = field(default_factory=list)
    fidelity_score: Optional[float] = None


@dataclass
class STFile:
    """Represents a Structured Text file."""
    struct_decs: str
    func_decs: str
    var_decs: str
    prog_block: str
    description: str
    
    def __str__(self) -> str:
        return f"{self.struct_decs}\n{self.func_decs}\n{self.var_decs}\n{self.prog_block}"
    
    def add_st_content(self, st_file: 'STFile') -> None:
        self.struct_decs += st_file.struct_decs
        self.func_decs += st_file.func_decs
        self.var_decs += st_file.var_decs
        self.prog_block += st_file.prog_block


@dataclass
class CompilerState:
    fbd_timers: List[str] = field(default_factory=list)
    data_types: Dict[str, str] = field(default_factory=dict)
    fbd_types: Dict[str, Dict[str, str]] = field(default_factory=dict)
    struct_names: Set[str] = field(default_factory=set)
    var_names: OrderedSet = field(default_factory=OrderedSet)
    fbd_names: Set[str] = field(default_factory=set)
    fbd_origin: Dict[str, str] = field(default_factory=dict)
    var_origin: Dict[str, str] = field(default_factory=dict)
    struct_origin: Dict[str, str] = field(default_factory=dict)
    msgs_to_initialize: List[str] = field(default_factory=list)
    local_vars_to_remove: List[str] = field(default_factory=list)
    current_controller: int = 1
    appended_reserved_words: List[str] = field(default_factory=list)
    def reset_for_new_controller(self) -> None:
        self.current_controller += 1
        self.appended_reserved_words.clear()
    def add_variable(self, var_name: str, data_type: str, origin: str) -> None:
        var_name_lower = var_name.lower()
        if var_name_lower not in self.var_names:
            self.var_names.add(var_name_lower)
            self.data_types[var_name_lower] = data_type
            self.var_origin[var_name_lower] = origin
    def add_struct(self, struct_name: str, origin: str) -> None:
        if struct_name not in self.struct_names:
            self.struct_names.add(struct_name)
            self.struct_origin[struct_name] = origin
    def add_function(self, func_name: str, origin: str) -> None:
        if func_name not in self.fbd_names:
            self.fbd_names.add(func_name)
            self.fbd_origin[func_name] = origin


@dataclass
class Instruction:
    name: str
    parameters: List[str] = field(default_factory=list)
    description: Optional[str] = None


@dataclass
class DataType:
    name: str
    base_type: str
    description: Optional[str] = None
    members: Optional[Dict[str, str]] = None


@dataclass
class Tag:
    name: str
    data_type: str
    description: Optional[str] = None
    value: Optional[str] = None
    scope: str = "local"


@dataclass
class FunctionBlock:
    name: str
    inputs: List[Dict[str, str]] = field(default_factory=list)
    outputs: List[Dict[str, str]] = field(default_factory=list)
    variables: List[Dict[str, str]] = field(default_factory=list)
    code: List[str] = field(default_factory=list)
    description: Optional[str] = None


# FSM-related data models
@dataclass
class FSMTransition:
    """Represents a transition in a finite state machine."""
    from_state: str
    to_state: str
    guard: Optional[str] = None
    actions: List[str] = field(default_factory=list)
    description: Optional[str] = None


@dataclass
class FSMState:
    """Represents a state in a finite state machine."""
    name: str
    description: Optional[str] = None
    is_initial: bool = False
    is_final: bool = False
    continuous_dynamics: Optional[str] = None  # For hybrid automata
    invariants: List[str] = field(default_factory=list)


@dataclass
class IRStateMachine:
    """Intermediate representation of a finite state machine."""
    name: str
    states: List[FSMState] = field(default_factory=list)
    transitions: List[FSMTransition] = field(default_factory=list)
    state_variable: Optional[str] = None
    description: Optional[str] = None
    source_type: Optional[str] = None  # "rockwell", "siemens", "fischertechnik_txt", etc.
    is_implicit: bool = False  # True if inferred from boolean flags; False if explicit state variable


@dataclass
class CrossControllerFSM:
    """Represents a composite FSM across multiple controllers."""
    name: str
    controllers: List[str] = field(default_factory=list)
    linked_transitions: List[Dict[str, Any]] = field(default_factory=list)
    shared_tags: List[str] = field(default_factory=list)
    handshake_logic: List[Dict[str, Any]] = field(default_factory=list)
    description: Optional[str] = None 