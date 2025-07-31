"""
CrossPLC: A cross-vendor semantic toolkit for programmable logic controller (PLC) codebases.

Supports:
- L5X/L5K import from Rockwell Studio 5000
- OpenPLC ST and Siemens SCL parsing
- Intermediate Representation (IR) unification
- Multi-PLC semantic dependency analysis
- Translation to IEC 61131-3 ST and formal logics (dL, STL)
- Fidelity scoring and interactive querying
"""

from .l5x2st import L5X2STConverter
from .st2l5x import ST2L5XConverter
from .ir_converter import IRConverter
from .l5k_overlay import L5KOverlay
from .export_ir import export_ir_to_json
from .query import InteractiveIRQuery
from .project_ir import ProjectIR
from .openplc_parser import OpenPLCParser
from .siemens_scl_parser import SiemensSCLParser
from .siemens_lad_parser import SiemensLADParser
from .txt_parser import TXTParser

__version__ = "2.0.0"
__all__ = [
    "L5X2STConverter",
    "ST2L5XConverter", 
    "IRConverter",
    "L5KOverlay",
    "export_ir_to_json",
    "InteractiveIRQuery",
    "ProjectIR",
    "OpenPLCParser",
    "SiemensSCLParser",
    "SiemensLADParser",
    "TXTParser"
] 