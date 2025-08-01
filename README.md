# CrossPLC: A Cross-Vendor Translation and Semantic Analysis Framework for PLC Logic

A modern Python 3 implementation for translating, analyzing, and unifying control logic across Rockwell, Siemens, and OpenPLC ecosystems. This project provides **complete round-trip conversion**, **IR validation**, **L5K overlay support**, **semantic analysis**, **control flow graph analysis**, and **multi-PLC analysis** across multiple vendor platforms.

> **⚠️ Work in Progress**: The FSM extraction feature is currently under development and validation. The generic structural analysis approach is experimental and may require refinement for production use.

## Features

### Cross-Vendor Support
- **Rockwell Automation**: Convert `.L5X` and `.L5K` files to/from Structured Text
- **OpenPLC**: Parse and analyze OpenPLC `.st` files
- **Siemens**: Parse and analyze Siemens `.scl`, `.udt`, and `.db` files
- **Fischertechnik TXT**: Parse and analyze TXT C++ control logic (`.cpp`, `.h`, `.hpp`) files
- **Unified IR**: Common Intermediate Representation across all platforms
- **Mixed-Platform Analysis**: Analyze projects using multiple vendor platforms together

### L5X to Structured Text (L5X2ST)
- Convert single L5X files to ST format
- Convert entire directories of L5X files to consolidated ST
- Handle multiple PLCs with proper variable renaming
- Support for Function Block Diagrams (FBD)
- Support for Ladder Logic (RLL)
- Automatic type conversion and reserved word handling
- Message instruction handling
- Timer function block support
- **IR validation mode** with guardrails
- **L5K overlay support** for enhanced project context

### Structured Text to L5X (ST2L5X)
- Convert ST files back to L5X format
- Generate proper L5X XML structure
- Support for variable declarations
- Support for function declarations
- Support for struct declarations
- **IR validation mode** with fidelity scoring

### L5K Overlay System
- **Enhanced Project Context**: Extract missing project-level information from L5K files
- **Global and Controller Tags**: Complete tag definitions with data types and initial values
- **Task and Program Mapping**: Execution order and program-to-task bindings
- **Module Configurations**: Hardware module settings and I/O configurations
- **User-Defined Data Types**: Complete UDT definitions with nested structures
- **Initial Tag Values**: Default values for all tags in the project

### IR Export and Analysis
- **Component Export**: Export tags, control flow, data types, function blocks, interactions, routines, programs
- **Semantic Analysis**: Tag usage summary, inter-routine dependencies, control flow annotations
- **Interactive Querying API**: Programmatic access to IR components with search and analysis
- **Control Flow Analysis**: Extract and analyze control flow structures from routines
- **Cross-Program Interaction Detection**: Identify dependencies between programs and controllers

### Control Flow Graph (CFG) Analysis
- **Static Analysis**: Similar to Angr, IDA Pro, or Ghidra for PLC code
- **Basic Block Analysis**: Parse ST routines into basic blocks with instructions
- **Data Flow Analysis**: Track defs (writes) and uses (reads) per block
- **Cross-Routine Data Flow**: Detect shared tag dependencies between routines
- **Industry Terminology**: Treat routines as functions, tags as symbols
- **Graph Export**: DOT and GraphML formats for visualization

### Multi-PLC Analysis
- **Cross-PLC Dependencies**: Detect tags written by one PLC and read by others
- **Shared Tag Analysis**: Identify communication patterns between multiple PLCs
- **Conflict Detection**: Find naming conflicts and data type mismatches across PLCs
- **L5K Overlay Integration**: Enhanced context with task and program mapping
- **Distributed Control Analysis**: Understand system-wide communication patterns
- **Mixed-Platform Support**: Analyze Rockwell L5X and OpenPLC ST files together
- **Detailed Component Export**: Export specific IR components with `--include` option

### OpenPLC Integration
- **OpenPLC ST Parser**: Parse OpenPLC `.st` files into IR format
- **Hardware I/O Mapping**: Support for `AT %IW0`, `AT %QX0.4` syntax
- **Variable Declarations**: Handle multiple VAR blocks within PROGRAM sections
- **Data Type Mapping**: Map OpenPLC types (BOOL, INT, REAL) to IR format
- **Mixed-Platform Analysis**: Analyze Rockwell + OpenPLC systems together
- **Source Type Tracking**: Identify "rockwell" vs "openplc" sources
- **Controller Metadata**: Track source type, overlay status, validity

### Siemens SCL Integration
- **Siemens SCL Parser**: Parse Siemens SCL files (`.scl`, `.udt`, `.db`) into IR format
- **Official Grammar Compliance**: Based on official Siemens SCL grammar specification
- **Complete Block Support**: FUNCTION_BLOCK, FUNCTION, ORGANIZATION_BLOCK, DATA_BLOCK, TYPE
- **Variable Declaration Sections**: VAR_INPUT, VAR_OUTPUT, VAR, VAR_TEMP, VAR_IN_OUT, CONST
- **Data Block Support**: Parse `.db` files with STRUCT definitions and initialization
- **User-Defined Types**: Parse `.udt` files with STRUCT members
- **Siemens-Specific Handling**: Filter Siemens attributes (S7_HMI_*, etc.)
- **Complex Type Support**: Handle array types, STRUCT definitions, AT references
- **Mixed-Platform Analysis**: Analyze Rockwell + OpenPLC + Siemens systems together
- **Source Type Tracking**: Identify "rockwell", "openplc", "siemens" sources
- **Project Structure Analysis**: Complete Siemens SCL project analysis

### Siemens LAD/FBD Integration
- **Siemens LAD/FBD Parser**: Parse Siemens LAD/FBD projects (`.zap15`, `.zap16`, `.zap17`, `.zap18`) into IR format
- **Project Structure Analysis**: Extract program blocks, connections, and I/O mappings from Siemens TIA Portal projects
- **Block Type Detection**: Automatically detect LAD (Ladder Logic), FBD (Function Block Diagram), and SCL languages
- **XML Block Parsing**: Parse Siemens XML program blocks to extract logic elements and connections
- **Connection Analysis**: Extract wire connections and signal flow between blocks
- **I/O Tag Extraction**: Identify input and output tags from block interfaces
- **Mixed-Platform Analysis**: Analyze Rockwell + OpenPLC + Siemens LAD/FBD systems together
- **Source Type Tracking**: Identify "rockwell", "openplc", "siemens_lad" sources
- **Project Extraction**: Handle compressed `.zap` files and extract program structure
- **Structural IR Generation**: Create IR representation of LAD/FBD program structure

### Fischertechnik TXT Integration
- **TXT C++ Parser**: Parse Fischertechnik TXT C++ control logic (`.cpp`, `.h`, `.hpp`) into IR format
- **Industrial Testbed Support**: Designed for Fischertechnik TXT training factory and similar industrial testbeds
- **Motor Control Patterns**: Extract `setMotorOff()`, `setMotorLeft()`, `setMotorRight()`, `setSpeed()` patterns
- **Sensor Reading Patterns**: Parse `isSwitchPressed()`, `read_sensor()`, `get_input()` function calls
- **I/O Mapping**: Extract `pT->pTArea->ftX1in.uni[]` and `pT->pTArea->ftX1out.duty[]` patterns
- **State Machine Analysis**: Detect FSM patterns with `FSM_TRANSITION()` macros and state enums
- **Timing Control**: Parse `std::this_thread::sleep_for()` and other timing patterns
- **Mixed-Platform Analysis**: Analyze Rockwell + OpenPLC + Siemens + TXT systems together
- **Source Type Tracking**: Identify "rockwell", "openplc", "siemens", "fischertechnik_txt" sources
- **Control Logic Extraction**: Extract control flow, assignments, function calls, and motor control operations

### Finite State Machine (FSM) Extraction
- **Hybrid Finite State Abstraction (HFSA)**: Extract FSMs from control flow IR using structural analysis
- **Generic State Variable Detection**: Automatically identify state variables using control flow structure (variables in IF/CASE guards, assignments, output controls)
- **Structural Analysis**: Infer FSMs based on control flow patterns, not hardcoded domain-specific patterns
- **Cross-Domain Compatibility**: Works across any industrial system (water treatment, manufacturing, chemical plants, etc.)
- **Configuration-Driven**: Optional YAML configuration for state variable hints and expected behavior
- **Multi-Controller FSM**: Support for cross-controller FSM mapping and analysis
- **FSM Visualization**: Generate DOT/GraphML files for FSM visualization
- **JSON Export**: Export FSMs in structured JSON format for downstream analysis
- **Guard Condition Extraction**: Parse IF statements, CASE statements, and control flow conditions
- **Action Tracking**: Extract assignments, function calls, and control actions
- **State Classification**: Identify initial, final, and intermediate states
- **Cross-Platform Support**: Works with Rockwell L5X, Siemens SCL, and Fischertechnik TXT
- **Validation Support**: Compare extracted FSMs against expected behavior from configuration

### Advanced Features
- **Complete Round-Trip Conversion**: L5X ↔ ST ↔ L5X with validation
- **Intermediate Representation (IR)**: Internal data model for validation
- **Fidelity Scoring**: Quantitative measurement of conversion quality
- **Guardrail Validation**: Optional `--use-ir` flag for enhanced validation
- **Industrial-Grade Reliability**: Handles complex Rockwell automation projects
- **Metadata Comparison**: Tools to analyze differences between overlay and non-overlay conversions
- **Graph Visualization**: Export control flow and data flow graphs for analysis

## Installation

### Prerequisites
- Python 3.8 or higher
- pip

### Install from source
```bash
git clone <repository-url>
cd l5x2ST
pip install -e .
```

### Install dependencies
```bash
pip install -r requirements.txt
```

## Usage

### Command Line Interface

#### Convert L5X to ST
```bash
# Convert single file
python -m crossplc.cli l5x2st -i project.L5X -o output.st

# With IR validation (recommended)
python -m crossplc.cli l5x2st -i project.L5X -o output.st --use-ir

# With verbose output
python -m crossplc.cli l5x2st -i project.L5X -o output.st -v
```

#### Convert L5X to ST with L5K Overlay
```bash
# Convert with L5K overlay for enhanced context
python -m crossplc.cli l5x2st -i project.L5X -o output.st --l5k-overlay project.L5K

# With IR validation and L5K overlay
python -m crossplc.cli l5x2st -i project.L5X -o output.st --l5k-overlay project.L5K --use-ir

# With verbose output and overlay
python -m crossplc.cli l5x2st -i project.L5X -o output.st --l5k-overlay project.L5K -v
```

#### Validate L5K Overlay Differences
```bash
# Compare IR with and without L5K overlay
python examples/validate_l5k_overlay_diff.py -i project.L5X -l project.L5K

# Generate JSON report
python examples/validate_l5k_overlay_diff.py -i project.L5X -l project.L5K --json

# Compare multiple projects
python examples/validate_l5k_overlay_diff.py -i project1.L5X -l project1.L5K -i project2.L5X -l project2.L5K
```

#### Convert ST to L5X
```bash
# Convert single file
python -m crossplc.cli st2l5x -i program.st -o output.L5X

# With IR validation (recommended)
python -m crossplc.cli st2l5x -i program.st -o output.L5X --use-ir

# With verbose output
python -m crossplc.cli st2l5x -i program.st -o output.L5X -v
```

#### Export IR Components
```bash
# Export basic IR components (tags and control flow)
python -m crossplc.cli export-ir -i P1.L5X -o out/ir_dump.json --include tags,control_flow

# Export all IR components
python -m crossplc.cli export-ir -i P1.L5X -o out/ir_full.json --include tags,control_flow,data_types,function_blocks,interactions,routines,programs

# Export with verbose output
python -m crossplc.cli export-ir -i P1.L5X -o out/ir_dump.json --include tags,control_flow -v

# Export specific components only
python -m crossplc.cli export-ir -i P1.L5X -o out/tags_only.json --include tags

# Export semantic analysis
python -m crossplc.cli export-ir -i P1.L5X -o out/ir_semantic.json --include semantic

# Export control flow graph (CFG)
python -m crossplc.cli export-ir -i P1.L5X -o out/ir_cfg.json --mode cfg

# Export CFG with graph visualization
python -m crossplc.cli export-ir -i P1.L5X -o out/ir_cfg.json --mode cfg --export-graphs

#### Multi-PLC Analysis
```bash
# Analyze entire directory of PLCs
python -m crossplc.cli analyze-multi -d ./swatfiles -o interdependence.json -v

# Analyze specific PLC pairs with L5K overlays
python -m crossplc.cli analyze-multi \
  --l5x P1.L5X --l5k P1.L5K \
  --l5x P2.L5X --l5k P2.L5K \
  -o test_pairing.json

# Require L5K overlays for all PLCs
python -m crossplc.cli analyze-multi -d ./swatfiles --require-overlay -o strict.json

# Analyze with detailed component export
python -m crossplc.cli analyze-multi \
  --l5x P1.L5X --st openplc.st \
  -o detailed.json \
  --include tags,control_flow,controllers,shared_tags

# Export specific components only
python -m crossplc.cli analyze-multi \
  --st controller.st \
  -o tags_only.json \
  --include tags
```

#### OpenPLC Integration
```bash
# Analyze OpenPLC ST files
python -m crossplc.cli analyze-multi --st controller.st -o openplc.json

# Mixed Rockwell + OpenPLC analysis
python -m crossplc.cli analyze-multi \
  --l5x P1.L5X --l5k P1.L5K \
  --st openplc_controller.st \
  -o mixed_analysis.json

# Directory analysis with OpenPLC files
python -m crossplc.cli analyze-multi -d ./mixed_project -o analysis.json

# Detailed component export for OpenPLC
python -m crossplc.cli analyze-multi \
  --st controller.st \
  -o detailed.json \
  --include tags,control_flow,controllers
```

#### Siemens SCL Integration
```bash
# Analyze Siemens SCL files
python -m crossplc.cli analyze-multi --scl main.scl -o siemens.json

# Analyze Siemens UDT files
python -m crossplc.cli analyze-multi --scl types.udt -o udt.json

# Analyze Siemens DB files
python -m crossplc.cli analyze-multi --scl data.db -o db.json

# Complete Siemens project analysis
python -m crossplc.cli analyze-multi -d /path/to/siemens/project -o siemens_project.json

# Mixed three-platform analysis
python -m crossplc.cli analyze-multi \
  --l5x rockwell.L5X --st openplc.st --scl siemens.scl \
  -o three_platform.json

# Siemens with detailed component export
python -m crossplc.cli analyze-multi \
  --scl main.scl --scl data.db \
  -o detailed_siemens.json \
  --include tags,control_flow,controllers

#### Fischertechnik TXT Integration
```bash
# Parse TXT C++ control logic
python3 -m crossplc.cli parse-txt -i txt_training_factory/TxtSmartFactoryLib/src/TxtHighBayWarehouseRun.cpp -o txt_output.json -v

# Multi-platform analysis with TXT files
python3 -m crossplc.cli analyze-multi --cpp txt_training_factory/TxtSmartFactoryLib/src/TxtHighBayWarehouseRun.cpp -o multi_analysis.json -v

# Extract FSM from TXT control logic (generic structural analysis)
python3 extract_fsm_multi.py txt_training_factory/TxtSmartFactoryLib/src/TxtHighBayWarehouseRun.cpp fsm_output.json fsm_config.yaml

# Visualize extracted FSM
python3 visualize_fsm.py fsm_output.json fsm_visualization.svg
```

#### Generic FSM Extraction (Work in Progress)
```bash
# Extract FSM using structural analysis (no hardcoded patterns)
python3 extract_fsm_multi.py sampledata/swatfiles fsm_swatfiles_output.json fsm_config.yaml

# Extract FSM from any industrial system
python3 extract_fsm_multi.py <input_file_or_dir> <output_file> [config_file]

# Cross-domain FSM extraction
python3 extract_fsm_multi.py examples/sample_txt_control.cpp fsm_manufacturing_output.json fsm_config.yaml
```

#### Siemens LAD/FBD Integration
```bash
# Explore Siemens LAD/FBD project structure
python -m crossplc.cli explore-lad -i project.zap16 -o lad_structure.json

# Analyze Siemens LAD/FBD projects
python -m crossplc.cli analyze-multi --l5x project.zap15 -o lad_analysis.json

# Analyze multiple Siemens LAD/FBD projects
python -m crossplc.cli analyze-multi \
  --l5x timer.zap15 --l5x pid.zap16 \
  -o multi_lad.json

# Mixed platform analysis with LAD/FBD
python -m crossplc.cli analyze-multi \
  --l5x rockwell.L5X --l5x siemens_lad.zap16 --scl siemens_scl.scl \
  -o mixed_platform.json

# LAD/FBD with detailed component export
python -m crossplc.cli analyze-multi \
  --l5x project.zap16 \
  -o detailed_lad.json \
  --include tags,control_flow,controllers
```

### Python API

#### L5X to ST Conversion
```python
from crossplc import L5X2STConverter

converter = L5X2STConverter()

# Convert single file
converter.convert_file("project.L5X", "output.st")

# Parse and get STFile object
st_file = converter.parse_l5x_file("project.L5X")
print(str(st_file))
```

#### L5K Overlay Integration
```python
from crossplc import L5X2STConverter
from crossplc import L5KOverlay

# Load L5K overlay for enhanced context
overlay = L5KOverlay()
overlay.load_l5k_file("project.L5K")

# Convert with overlay
converter = L5X2STConverter()
st_file = converter.parse_l5x_file("project.L5X", overlay=overlay)
print(str(st_file))
```

#### IR Validation and Round-Trip
```python
from crossplc import IRConverter
from crossplc import L5X2STConverter, ST2L5XConverter

# Load and validate L5X
ir_converter = IRConverter()
l5x2st = L5X2STConverter()
st2l5x = ST2L5XConverter()

# Round-trip with validation
original_project = l5x2st.parse_l5x_file("project.L5X")
original_ir = ir_converter.l5x_to_ir(original_project)

# Convert to ST and back
st_content = str(original_project)
final_l5x = st2l5x.convert_st_to_l5x(st_content, "")
final_project = l5x2st.parse_l5x_file("final.L5X")
final_ir = ir_converter.l5x_to_ir(final_project)

# Calculate fidelity score
fidelity_score = ir_converter.calculate_fidelity_score(original_ir, final_ir)
print(f"Round-trip fidelity: {fidelity_score:.2%}")
```

#### IR Comparison and Analysis
```python
from crossplc import IRConverter
from crossplc import L5KOverlay

# Compare IR with and without overlay
ir_converter = IRConverter()
overlay = L5KOverlay()
overlay.load_l5k_file("project.L5K")

# Generate IR without overlay
ir_without = ir_converter.l5x_to_ir("project.L5X")

# Generate IR with overlay
ir_with = ir_converter.l5x_to_ir("project.L5X", overlay=overlay)

# Analyze differences
diff_report = ir_converter.compare_ir(ir_without, ir_with)
print(f"Tags added: {diff_report['tags_added']}")
print(f"Tasks added: {diff_report['tasks_added']}")
print(f"Modules added: {diff_report['modules_added']}")
```

#### IR Export and Querying
```python
from l5x_st_compiler import IRConverter, export_ir_to_json, InteractiveIRQuery
import l5x

# Load L5X project and convert to IR
project = l5x.Project("project.L5X")
ir_converter = IRConverter()
ir_project = ir_converter.l5x_to_ir(project)

# Export IR components to JSON
export_data = export_ir_to_json(
    ir_project=ir_project,
    output_path="ir_export.json",
    include=["tags", "control_flow", "data_types", "interactions"],
    pretty_print=True
)

# Interactive querying
query = InteractiveIRQuery(ir_project)

# Find tags by prefix
lit_tags = query.find_tags_by_prefix("LIT")
print(f"Found {len(lit_tags)} tags with prefix 'LIT'")

# Get control flow for a routine
control_flow = query.get_control_flow("MainRoutine", "MainProgram")
if control_flow:
    print(f"Control flow type: {control_flow['type']}")

# Get tag dependencies
dependencies = query.get_dependencies("P101")
print(f"Tag P101 referenced by: {dependencies['referenced_by']}")

# Get project summary
summary = query.get_project_summary()
print(f"Project has {summary['tags']['total_tags']} total tags")

#### Semantic Analysis
```python
from crossplc.export_ir import export_ir_to_json

# Export semantic analysis
export_data = export_ir_to_json(
    ir_project=ir_project,
    output_path="semantic_analysis.json",
    include=["semantic"],
    pretty_print=True
)

# Access semantic analysis results
semantic = export_data.get("semantic", {})
tag_summary = semantic.get("tag_summary", {})
interdependencies = semantic.get("interdependencies", [])
annotations = semantic.get("control_flow_annotations", {})
```

#### Control Flow Graph Analysis
```python
from crossplc.export_ir import export_ir_to_json, export_cfg_to_graphs

# Export CFG analysis
export_data = export_ir_to_json(
    ir_project=ir_project,
    output_path="cfg_analysis.json",
    include=["cfg"],
    pretty_print=True
)

# Export graphs for visualization
cfg_data = export_data.get("cfg", {})
graph_files = export_cfg_to_graphs(cfg_data, "out")

# Access generated files
print(f"CFG DOT: {graph_files['cfg_dot']}")
print(f"Data Flow DOT: {graph_files['dataflow_dot']}")
print(f"CFG GraphML: {graph_files['cfg_graphml']}")
print(f"Data Flow GraphML: {graph_files['dataflow_graphml']}")
```

#### Multi-PLC Analysis
```python
from crossplc.project_ir import ProjectIR
from pathlib import Path

# Load multiple PLCs with L5K overlays
l5x_files = [Path("P1.L5X"), Path("P2.L5X"), Path("P3.L5X")]
l5k_overlays = {
    "P1": Path("P1.L5K"),
    "P2": Path("P2.L5K"),
    "P3": Path("P3.L5K")
}

# Create multi-PLC analysis
project_ir, missing_overlays = ProjectIR.from_files(l5x_files, l5k_overlays)

# Find cross-PLC dependencies
dependencies = project_ir.find_cross_plc_dependencies()
for dep in dependencies:
    print(f"{dep.tag}: {dep.writer} → {dep.readers}")

# Detect conflicts
conflicts = project_ir.detect_conflicting_tags()
for conflict in conflicts:
    print(f"Conflict in {conflict.tag}: {conflict.conflict_type}")

# Export analysis
summary = project_ir.export_summary(Path("interdependence.json"))
print(f"Found {len(summary['shared_tags'])} shared tags")
print(f"Found {len(summary['conflicting_tags'])} conflicts")
```

#### OpenPLC Integration
```python
from crossplc.openplc_parser import OpenPLCParser
from crossplc.project_ir import ProjectIR
from pathlib import Path

# Parse OpenPLC ST file
parser = OpenPLCParser()
ir_project = parser.parse(Path("controller.st"))

# Access OpenPLC-specific information
print(f"Controller: {ir_project.controller.name}")
print(f"Source type: {ir_project.source_type}")
print(f"Tags: {len(ir_project.controller.tags)}")

# Mixed-platform analysis
project_ir = ProjectIR.from_files([
    Path("P1.L5X"),  # Rockwell
    Path("controller.st")  # OpenPLC
])

# Export mixed analysis with detailed components
summary = project_ir.export_summary(
    Path("mixed_analysis.json"),
    include_components=["tags", "control_flow", "controllers", "shared_tags"]
)

# Access controller metadata
for controller in summary.get("controllers", []):
    print(f"{controller['name']}: {controller['source']} platform")

# Access detailed components
detailed = summary.get("detailed_components", {})
for plc_name, components in detailed.items():
    print(f"{plc_name}: {list(components.keys())} components available")
```

#### Siemens SCL Integration
```python
from crossplc.siemens_scl_parser import SiemensSCLParser
from crossplc.project_ir import ProjectIR
from pathlib import Path

# Parse Siemens SCL file
parser = SiemensSCLParser()
ir_project = parser.parse(Path("main.scl"))

# Access Siemens-specific information
print(f"Controller: {ir_project.controller.name}")
print(f"Source type: {ir_project.source_type}")
print(f"Tags: {len(ir_project.controller.tags)}")

# Parse Siemens UDT file
udt_project = parser.parse(Path("types.udt"))
print(f"UDT variables: {len(udt_project.controller.tags)}")

# Parse Siemens DB file
db_project = parser.parse(Path("data.db"))
print(f"DB variables: {len(db_project.controller.tags)}")

# Complete Siemens project analysis
project_ir = ProjectIR.from_files([
    Path("main.scl"),      # Main program
    Path("functions.scl"), # Function blocks
    Path("data.db"),       # Data block
    Path("types.udt")      # User-defined types
])

# Mixed three-platform analysis
project_ir = ProjectIR.from_files([
    Path("P1.L5X"),        # Rockwell
    Path("controller.st"),  # OpenPLC
    Path("main.scl"),      # Siemens
    Path("data.db")        # Siemens DB
])

# Export mixed analysis with detailed components
summary = project_ir.export_summary(
    Path("three_platform_analysis.json"),
    include_components=["tags", "control_flow", "controllers", "shared_tags"]
)

# Access controller metadata by platform
for controller in summary.get("controllers", []):
    print(f"{controller['name']}: {controller['source']} platform")

# Access Siemens-specific components
detailed = summary.get("detailed_components", {})
for plc_name, components in detailed.items():
    if "siemens" in plc_name.lower():
        print(f"Siemens {plc_name}: {list(components.keys())} components")
```

#### Siemens LAD/FBD Integration
```python
from crossplc.siemens_lad_parser import SiemensLADParser
from crossplc.project_ir import ProjectIR
from pathlib import Path

# Parse Siemens LAD/FBD project
parser = SiemensLADParser()
ir_project = parser.parse_project(Path("project.zap16"))

# Access LAD/FBD-specific information
print(f"Controller: {ir_project.controller.name}")
print(f"Source type: {ir_project.source_type}")
print(f"Tags: {len(ir_project.controller.tags)}")

# Explore project structure
for program in ir_project.programs:
    print(f"Program: {program.name}")
    for routine in program.routines:
        print(f"  Routine: {routine.name} ({routine.routine_type.value})")
        print(f"  Content: {routine.content[:100]}...")

# Analyze multiple LAD/FBD projects
project_ir = ProjectIR.from_files([
    Path("timer.zap15"),      # Timer project
    Path("pid.zap16"),        # PID project
    Path("motor.zap17")       # Motor control project
])

# Mixed platform analysis with LAD/FBD
project_ir = ProjectIR.from_files([
    Path("P1.L5X"),           # Rockwell
    Path("controller.st"),     # OpenPLC
    Path("main.scl"),         # Siemens SCL
    Path("project.zap16")     # Siemens LAD/FBD
])

# Export mixed analysis with detailed components
summary = project_ir.export_summary(
    Path("mixed_platform_analysis.json"),
    include_components=["tags", "control_flow", "controllers", "shared_tags"]
)

# Access controller metadata by platform
for controller in summary.get("controllers", []):
    print(f"{controller['name']}: {controller['source']} platform")

# Access LAD/FBD-specific components
detailed = summary.get("detailed_components", {})
for plc_name, components in detailed.items():
    if "siemens_lad" in plc_name.lower():
        print(f"Siemens LAD/FBD {plc_name}: {list(components.keys())} components")

# TXT C++ Control Logic Analysis
from crossplc.txt_parser import TXTParser
from crossplc.project_ir import ProjectIR
from pathlib import Path

# Parse TXT C++ control logic
parser = TXTParser()
ir_project = parser.parse_txt_file("control_logic.cpp")

# Access TXT-specific information
print(f"Controller: {ir_project.controller.name}")
print(f"Source type: {ir_project.source_type}")
print(f"Tags: {len(ir_project.controller.tags)}")

# Explore TXT control logic
for program in ir_project.programs:
    print(f"Program: {program.name}")
    for routine in program.routines:
        print(f"  Routine: {routine.name} ({routine.routine_type.value})")
        print(f"  Content: {routine.content[:100]}...")

# Analyze multiple TXT projects
project_ir = ProjectIR.from_files([
    Path("hbw_control.cpp"),    # High-Bay Warehouse
    Path("vgr_control.cpp"),    # Vacuum Gripper Robot
    Path("mpo_control.cpp")     # Multi-Processing Station
])

# Mixed platform analysis with TXT
project_ir = ProjectIR.from_files([
    Path("P1.L5X"),             # Rockwell
    Path("controller.st"),       # OpenPLC
    Path("main.scl"),           # Siemens SCL
    Path("project.zap16"),      # Siemens LAD/FBD
    Path("txt_control.cpp")     # Fischertechnik TXT
])

# Export mixed analysis with TXT components
summary = project_ir.export_summary(
    Path("mixed_platform_analysis.json"),
    include_components=["tags", "control_flow", "controllers", "shared_tags"]
)

# Access TXT-specific components
detailed = summary.get("detailed_components", {})
for plc_name, components in detailed.items():
    if "fischertechnik_txt" in plc_name.lower():
        print(f"TXT {plc_name}: {list(components.keys())} components")
```
```

## Project Structure

```
CrossPLC/
├── crossplc/                 # Main package
│   ├── __init__.py           # Package initialization
│   ├── constants.py          # Constants and configurations
│   ├── models.py             # Data models and IR classes
│   ├── utils.py              # Utility functions
│   ├── instructions.py       # Instruction processors
│   ├── ladder_logic.py       # Ladder logic translator
│   ├── fbd_translator.py     # FBD to ST translator
│   ├── ir_converter.py       # IR conversion system
│   ├── l5k_overlay.py        # L5K file parser and overlay system
│   ├── export_ir.py          # IR export and analysis system
│   ├── query.py              # Interactive IR querying API
│   ├── project_ir.py         # Multi-PLC analysis system
│   ├── openplc_parser.py     # OpenPLC ST parser
│   ├── siemens_scl_parser.py # Siemens SCL parser
│   ├── siemens_lad_parser.py # Siemens LAD/FBD parser
│   ├── txt_parser.py         # Fischertechnik TXT parser
│   ├── fsm_extractor.py     # Generic FSM extraction (work in progress)
│   ├── l5x2st.py            # L5X to ST converter
│   ├── st2l5x.py            # ST to L5X converter
│   └── cli.py               # Command-line interface
├── examples/                 # Example scripts
│   ├── basic_usage.py       # Basic usage examples
│   ├── complex_st_example.py # Complex ST example
│   ├── ir_roundtrip_test.py # IR round-trip testing
│   ├── ir_export_example.py # IR export and querying examples
│   ├── graph_export_example.py # CFG graph export examples
│   ├── l5x_compare.py       # L5X comparison tool
│   ├── l5x_roundtrip_test.py # L5X round-trip testing
│   ├── l5k_overlay_example.py # L5K overlay usage examples
│   ├── validate_l5k_overlay_diff.py # Overlay difference analysis
│   ├── validation_test.py   # Comprehensive validation
│   ├── extract_fsm_multi.py # Multi-format FSM extraction script
│   ├── visualize_fsm.py     # FSM visualization script
│   ├── test_openplc.st      # OpenPLC test file
│   ├── test_siemens.scl     # Siemens SCL test file
│   └── sample_txt_control.cpp # TXT C++ test file
├── tests/                    # Test suite
│   ├── __init__.py
│   ├── test_l5x2st.py       # Tests for L5X2ST converter
│   └── test_l5k_overlay.py  # Tests for L5K overlay system
├── requirements.txt          # Python dependencies
├── setup.py                  # Package setup
├── pytest.ini               # Pytest configuration
└── README.md                # This file
```

## Development

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=l5x_st_compiler

# Run specific test file
pytest tests/test_l5x2st.py

# Run with verbose output
pytest -v

# Run L5K overlay tests
pytest tests/test_l5k_overlay.py

# Run validation test suite
python examples/validation_test.py

# Test L5K overlay functionality
python examples/l5k_overlay_example.py

# Validate overlay differences
python examples/validate_l5k_overlay_diff.py -i sampledata/swatfiles/P1.L5X -l sampledata/swatfiles/P1.L5K
```

### Code Quality
```bash
# Format code with black
black l5x_st_compiler/

# Lint with flake8
flake8 l5x_st_compiler/

# Type checking with mypy
mypy l5x_st_compiler/
```

### Building and Installing
```bash
# Install in development mode
pip install -e .

# Build distribution
python setup.py sdist bdist_wheel

# Install from distribution
pip install dist/l5x-st-compiler-2.0.0.tar.gz
```

## Key Improvements Over Original

### Code Quality
- **Python 3 Support**: Full Python 3.8+ compatibility
- **Type Hints**: Comprehensive type annotations
- **Modular Design**: Clean separation of concerns
- **Error Handling**: Proper exception handling and user feedback
- **Documentation**: Comprehensive docstrings and comments

### Architecture
- **Object-Oriented**: Proper class-based design
- **State Management**: Centralized compiler state
- **Configuration**: Externalized constants and settings
- **Extensibility**: Easy to add new features and processors
- **IR System**: Intermediate representation for validation

### Testing
- **Unit Tests**: Comprehensive test coverage
- **Mock Support**: Proper mocking for external dependencies
- **Test Configuration**: Pytest configuration and markers
- **CI/CD Ready**: Structured for continuous integration
- **Validation Suite**: Comprehensive round-trip testing

### Features
- **Bidirectional Conversion**: Both L5X→ST and ST→L5X
- **CLI Interface**: User-friendly command-line tools with IR validation
- **API Support**: Programmatic access to converters
- **IR Validation**: Guardrail system for conversion quality
- **Fidelity Scoring**: Quantitative measurement of round-trip accuracy
- **L5K Overlay**: Enhanced project context from L5K files
- **Metadata Analysis**: Tools for comparing conversion differences

## Analysis Features

### Semantic Analysis
The semantic analysis system provides higher-level understanding of PLC code:

- **Tag Usage Summary**: Classify tags as inputs, outputs, or internal based on usage patterns
- **Inter-Routine Dependencies**: Detect data flow between routines based on shared tag reads/writes
- **Control Flow Annotations**: Rule-based annotations for control flow branches (e.g., "shutdown_trigger")
- **Export Format**: JSON output with `tag_summary`, `interdependencies`, and `control_flow_annotations`

### Control Flow Graph (CFG) Analysis
The CFG analysis provides static analysis capabilities similar to reverse engineering tools:

- **Basic Block Analysis**: Parse ST routines into basic blocks with single entry/exit points
- **Data Flow Analysis**: Track defs (writes) and uses (reads) for each block
- **Cross-Routine Data Flow**: Detect shared tag dependencies between different routines
- **Industry Terminology**: Treat routines as functions, tags as symbols, HMI/RIO/UDT fields as named memory references
- **Graph Export**: DOT and GraphML formats for visualization with Graphviz, Gephi, or NetworkX

### Multi-PLC Analysis
The multi-PLC analysis system is designed for distributed control systems:

- **Cross-PLC Dependencies**: Detect tags written by one PLC and read by others
- **Shared Tag Analysis**: Identify communication patterns between multiple PLCs
- **Conflict Detection**: Find naming conflicts and data type mismatches across PLCs
- **L5K Overlay Integration**: Enhanced context with task and program mapping
- **Distributed Control Analysis**: Understand system-wide communication patterns

## L5K Overlay System

The L5K overlay system enhances L5X to ST conversion by extracting additional project context from L5K files. This provides:

### Enhanced Context
- **Global Tags**: Controller-scoped tags with complete definitions
- **Task Definitions**: Execution order and timing information
- **Program Mappings**: Which programs run in which tasks
- **Module Configurations**: Hardware I/O settings and configurations
- **User-Defined Data Types**: Complete UDT definitions with nested structures
- **Initial Values**: Default values for all tags in the project

### Benefits
- **More Complete ST Output**: Includes system-level context and configurations
- **Better Round-Trip Fidelity**: Preserves more project metadata
- **Enhanced Debugging**: Complete tag definitions with initial values
- **System Integration**: Task and program execution information
- **Hardware Context**: Module configurations and I/O settings

### Usage Examples
```bash
# Basic overlay usage
python -m crossplc.cli l5x2st -i project.L5X -o output.st --l5k-overlay project.L5K

# Compare with and without overlay
python examples/validate_l5k_overlay_diff.py -i project.L5X -l project.L5K

### Analysis Examples
```bash
# Semantic analysis
python -m crossplc.cli export-ir -i P1.L5X -o semantic.json --include semantic

# CFG analysis with graph export
python -m crossplc.cli export-ir -i P1.L5X -o cfg.json --mode cfg --export-graphs

# Multi-PLC analysis
python -m crossplc.cli analyze-multi -d ./swatfiles -o interdependence.json -v

# Run example scripts
python examples/ir_export_example.py
python examples/graph_export_example.py
```
```

## Supported Instructions

### Currently Supported Categories
- **Bit Instructions**: XIC, XIO, OTE, OTL, OTU, ONS, OSR, OSF, OSRI, OSFI
- **Timer Instructions**: TON, TONR, TOF, TOFR, RTO, RTOR
- **Counter Instructions**: CTU, CTD, CTUD, RES
- **Compare Instructions**: EQ, NE, GT, GE, LT, LE, CMP, LIMIT, MEQ
- **Math Instructions**: ADD, SUB, MUL, DIV, MOD, SQR, SQRT, ABS, NEG
- **Data Conversion**: TOD, FRD, DTD, DTR, ROUND, TRUNC
- **Control Instructions**: JMP, JSR, RET, FOR, NEXT, WHILE, REPEAT, IF, CASE
- **Message Instructions**: MSG
- **System Instructions**: GSV, SSV

## Dependencies

### Core Dependencies
- `l5x>=0.1.0`: L5X file parser
- `ordered-set>=4.0.0`: Ordered set implementation
- `lxml>=4.6.0`: XML processing
- `click>=8.0.0`: CLI framework

### Development Dependencies
- `pytest>=6.0.0`: Testing framework
- `pytest-cov>=2.10.0`: Coverage reporting
- `black>=21.0.0`: Code formatting
- `flake8>=3.8.0`: Code linting
- `mypy>=0.800`: Type checking

## Limitations and TODOs

### Current Limitations
- Some complex FBD structures may not convert perfectly
- Message instruction handling is simplified
- Limited support for advanced motion instructions

### Planned Improvements
- [ ] Enhanced FBD processing with more complex structures
- [ ] Better message instruction handling
- [ ] Support for more advanced motion instructions
- [ ] Performance optimizations for large projects
- [ ] Better error reporting and diagnostics
- [ ] Enhanced Siemens SCL grammar compliance
- [ ] Support for more Siemens-specific data types
- [ ] Siemens PLCTags.xml integration improvements

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Original L5X parser and converter code
- Rockwell Automation for L5X format and instruction documentation
- IEC 61131-3 standard for Structured Text specification

## Support

For issues, questions, or contributions, please use the project's issue tracker or contact the maintainers.