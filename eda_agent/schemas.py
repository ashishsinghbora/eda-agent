"""Pydantic data schemas for RTL hardware module metadata and specs."""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class PortDirection(str, Enum):
    """Port direction enumeration."""
    INPUT = "input"
    OUTPUT = "output"
    INOUT = "inout"


class PortSpec(BaseModel):
    """Specification of an RTL module interface port."""
    name: str = Field(description="Port signal name")
    direction: PortDirection = Field(description="Direction of signal (input, output, inout)")
    width: str = Field(default="1", description="Bit width expression (e.g. '1', '8', '[DATA_WIDTH-1:0]')")
    port_type: str = Field(default="wire", description="HDL type (wire, reg, logic, etc.)")
    is_clock: bool = Field(default=False, description="Whether this port is a clock signal")
    is_reset: bool = Field(default=False, description="Whether this port is a reset signal")
    clock_domain: Optional[str] = Field(default=None, description="Inferred clock domain for this port")
    description: Optional[str] = Field(default=None, description="Optional docstring/comment description")

    @property
    def is_bus(self) -> bool:
        """Return True if port bit-width is greater than 1 bit."""
        return self.width != "1" and self.width != ""


class ParameterSpec(BaseModel):
    """Specification of a module parameter or generic."""
    name: str = Field(description="Parameter name")
    default_value: Optional[str] = Field(default=None, description="Default parameter value if specified")
    param_type: Optional[str] = Field(default=None, description="Type/width of parameter (e.g. integer, [31:0])")
    description: Optional[str] = Field(default=None, description="Optional description")


class StateSpec(BaseModel):
    """Specification of an FSM state, opcode, or RTL symbolic constant."""
    name: str = Field(description="State or constant identifier name")
    value: Optional[str] = Field(default=None, description="Assigned binary/hex/integer constant value")
    encoding_type: str = Field(default="localparam", description="Definition mechanism ('localparam', 'enum', 'define', 'parameter')")
    group: Optional[str] = Field(default=None, description="Detected category/group (e.g. 'FSM_STATE', 'OPCODE')")


# Alias for convenience
FSMStateSpec = StateSpec


class ModuleSpec(BaseModel):
    """Comprehensive specification and metadata of an RTL module."""
    name: str = Field(description="Verilog/SystemVerilog module name")
    parameters: List[ParameterSpec] = Field(default_factory=list, description="Module parameters")
    ports: List[PortSpec] = Field(default_factory=list, description="Module interface ports")
    constants: List[StateSpec] = Field(default_factory=list, description="Extracted local constants and parameters")
    fsm_states: List[StateSpec] = Field(default_factory=list, description="Extracted FSM states and opcode definitions")
    source_file: Optional[str] = Field(default=None, description="Source file path where module was defined")

    def get_port(self, name: str) -> Optional[PortSpec]:
        """Find a port by name."""
        for port in self.ports:
            if port.name == name:
                return port
        return None

    def get_param(self, name: str) -> Optional[ParameterSpec]:
        """Find a parameter by name."""
        for param in self.parameters:
            if param.name == name:
                return param
        return None

    def get_clock_ports(self) -> List[PortSpec]:
        """Get all ports identified as clocks."""
        return [p for p in self.ports if p.is_clock]

    def get_reset_ports(self) -> List[PortSpec]:
        """Get all ports identified as resets."""
        return [p for p in self.ports if p.is_reset]

    def get_inputs(self) -> List[PortSpec]:
        """Get all input ports."""
        return [p for p in self.ports if p.direction == PortDirection.INPUT]

    def get_outputs(self) -> List[PortSpec]:
        """Get all output ports."""
        return [p for p in self.ports if p.direction == PortDirection.OUTPUT]

    def get_inouts(self) -> List[PortSpec]:
        """Get all inout (bidirectional) ports."""
        return [p for p in self.ports if p.direction == PortDirection.INOUT]

    def to_dict(self) -> Dict:
        """Export model dump as dictionary."""
        return self.model_dump()
