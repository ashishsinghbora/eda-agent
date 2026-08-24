"""EDA-Agent: Open-Source EDA Verification & Testbench Framework."""

from .schemas import (
    FSMStateSpec,
    ModuleSpec,
    ParameterSpec,
    PortDirection,
    PortSpec,
    StateSpec,
)
from .parsers.verilog_parser import RTLParser, VerilogParser

__version__ = "0.1.0"

__all__ = [
    "ModuleSpec",
    "ParameterSpec",
    "PortDirection",
    "PortSpec",
    "StateSpec",
    "FSMStateSpec",
    "VerilogParser",
    "RTLParser",
    "__version__",
]
