"""Comprehensive unit tests for RTL Parser & Metadata Extractor."""

from pathlib import Path
import pytest
from eda_agent.parsers.verilog_parser import VerilogParser
from eda_agent.schemas import ModuleSpec, ParameterSpec, PortDirection, PortSpec, StateSpec


def test_parse_fifo_async():
    """Verify parsing of fifo_async.v with ModuleSpec schema."""
    fifo_path = Path("examples/rtl/fifo_async.v")
    assert fifo_path.is_file(), "examples/rtl/fifo_async.v must exist"

    modules = VerilogParser.parse_file(fifo_path)
    assert len(modules) == 1

    mod = modules[0]
    assert isinstance(mod, ModuleSpec)
    assert mod.name == "fifo_async"
    assert mod.source_file is not None

    # Parameter extraction
    param_dict = {p.name: p for p in mod.parameters}
    assert "DATA_WIDTH" in param_dict
    assert param_dict["DATA_WIDTH"].default_value == "8"
    assert "ADDR_WIDTH" in param_dict
    assert param_dict["ADDR_WIDTH"].default_value == "4"

    # Port extraction
    port_dict = {p.name: p for p in mod.ports}
    assert len(port_dict) == 10

    # Clock & Reset ports
    assert port_dict["wclk"].is_clock is True
    assert port_dict["rclk"].is_clock is True
    assert port_dict["wrst_n"].is_reset is True
    assert port_dict["rrst_n"].is_reset is True

    # Clock domain inference
    assert port_dict["wdata"].clock_domain == "wclk"
    assert port_dict["winc"].clock_domain == "wclk"
    assert port_dict["wfull"].clock_domain == "wclk"
    assert port_dict["rdata"].clock_domain == "rclk"
    assert port_dict["rinc"].clock_domain == "rclk"
    assert port_dict["rempty"].clock_domain == "rclk"

    # Directions & Widths
    assert port_dict["wdata"].direction == PortDirection.INPUT
    assert port_dict["wdata"].width == "DATA_WIDTH-1:0"
    assert port_dict["wdata"].is_bus is True
    assert port_dict["wfull"].direction == PortDirection.OUTPUT
    assert port_dict["wfull"].is_bus is False

    # ModuleSpec helper methods
    clocks = mod.get_clock_ports()
    assert len(clocks) == 2
    assert {c.name for c in clocks} == {"wclk", "rclk"}

    resets = mod.get_reset_ports()
    assert len(resets) == 2
    assert {r.name for r in resets} == {"wrst_n", "rrst_n"}

    inputs = mod.get_inputs()
    outputs = mod.get_outputs()
    assert len(inputs) == 7
    assert len(outputs) == 3

    assert mod.get_port("nonexistent") is None
    assert mod.get_param("nonexistent") is None


def test_parse_alu_8bit():
    """Verify parsing of alu_8bit.v and opcode/constant extraction."""
    alu_path = Path("examples/rtl/alu_8bit.v")
    assert alu_path.is_file(), "examples/rtl/alu_8bit.v must exist"

    modules = VerilogParser.parse_file(alu_path)
    assert len(modules) == 1

    mod = modules[0]
    assert mod.name == "alu_8bit"

    # Parameters
    assert len(mod.parameters) == 1
    assert mod.parameters[0].name == "DATA_WIDTH"
    assert mod.parameters[0].default_value == "8"

    # Ports
    port_dict = {p.name: p for p in mod.ports}
    assert port_dict["clk"].is_clock is True
    assert port_dict["rst_n"].is_reset is True
    assert port_dict["a"].width == "DATA_WIDTH-1:0"
    assert port_dict["b"].width == "DATA_WIDTH-1:0"
    assert port_dict["opcode"].width == "2:0"
    assert port_dict["result"].direction == PortDirection.OUTPUT
    assert port_dict["result"].width == "DATA_WIDTH-1:0"
    assert port_dict["zero"].direction == PortDirection.OUTPUT
    assert port_dict["carry"].direction == PortDirection.OUTPUT
    assert port_dict["overflow"].direction == PortDirection.OUTPUT

    # Clock domain inference for single clock
    assert port_dict["a"].clock_domain == "clk"
    assert port_dict["result"].clock_domain == "clk"

    # Opcodes / Constants extraction
    fsm_dict = {s.name: s for s in mod.fsm_states}
    expected_opcodes = [
        "OP_ADD", "OP_SUB", "OP_AND", "OP_OR",
        "OP_XOR", "OP_SHL", "OP_SHR", "OP_NOT"
    ]
    for op in expected_opcodes:
        assert op in fsm_dict, f"Expected opcode {op} to be extracted"
        assert fsm_dict[op].encoding_type == "localparam"
        assert fsm_dict[op].group == "OPCODE"


def test_parse_fsm_state_machine():
    """Verify extraction of FSM states defined via localparam."""
    code = """
    module fsm_controller (
        input  wire clk,
        input  wire rst_n,
        input  wire start,
        output reg  ready
    );
        localparam S_IDLE   = 3'b000;
        localparam S_FETCH  = 3'b001;
        localparam S_DECODE = 3'b010;
        localparam S_EXEC   = 3'b011;
        localparam S_DONE   = 3'b100;

        reg [2:0] state, next_state;
    endmodule
    """
    modules = VerilogParser.parse_string(code)
    assert len(modules) == 1
    mod = modules[0]

    assert mod.name == "fsm_controller"
    assert len(mod.fsm_states) == 5

    state_names = [s.name for s in mod.fsm_states]
    assert state_names == ["S_IDLE", "S_FETCH", "S_DECODE", "S_EXEC", "S_DONE"]
    assert all(s.group == "FSM_STATE" for s in mod.fsm_states)


def test_parse_systemverilog_enum_fsm():
    """Verify extraction of SystemVerilog enum states."""
    code = """
    module sv_fsm (
        input  logic clk,
        input  logic rst_n
    );
        typedef enum logic [1:0] {
            STATE_INIT  = 2'b00,
            STATE_RUN   = 2'b01,
            STATE_ERROR = 2'b10
        } state_t;
    endmodule
    """
    modules = VerilogParser.parse_string(code)
    assert len(modules) == 1
    mod = modules[0]

    assert mod.name == "sv_fsm"
    assert len(mod.fsm_states) == 3
    state_dict = {s.name: s.value for s in mod.fsm_states}
    assert state_dict["STATE_INIT"] == "2'b00"
    assert state_dict["STATE_RUN"] == "2'b01"
    assert state_dict["STATE_ERROR"] == "2'b10"


def test_parse_non_ansi_style():
    """Verify parsing of traditional non-ANSI Verilog-1995 style declarations."""
    code = """
    module legacy_counter (clk, reset, enable, count);
        parameter WIDTH = 8;
        input clk;
        input reset;
        input enable;
        output [WIDTH-1:0] count;
        wire clk, reset, enable;
        reg [WIDTH-1:0] count;
    endmodule
    """
    modules = VerilogParser.parse_string(code)
    assert len(modules) == 1
    mod = modules[0]

    assert mod.name == "legacy_counter"
    assert len(mod.parameters) == 1
    assert mod.parameters[0].name == "WIDTH"
    assert mod.parameters[0].default_value == "8"

    port_dict = {p.name: p for p in mod.ports}
    assert port_dict["clk"].is_clock is True
    assert port_dict["reset"].is_reset is True
    assert port_dict["enable"].direction == PortDirection.INPUT
    assert port_dict["count"].direction == PortDirection.OUTPUT
    assert port_dict["count"].width == "WIDTH-1:0"


def test_schema_serialization():
    """Verify ModuleSpec serialization to and from dictionary."""
    fifo_path = Path("examples/rtl/fifo_async.v")
    mod = VerilogParser.parse_file(fifo_path)[0]

    data = mod.to_dict()
    assert isinstance(data, dict)
    assert data["name"] == "fifo_async"
    assert len(data["ports"]) == 10

    # Reconstruct from dict
    reconstructed = ModuleSpec.model_validate(data)
    assert reconstructed.name == mod.name
    assert len(reconstructed.ports) == len(mod.ports)
