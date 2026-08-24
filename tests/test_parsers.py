"""Unit tests for VerilogParser."""

from pathlib import Path
import pytest
from eda_agent.parsers.verilog_parser import VerilogParser


def test_parse_fifo_async():
    """Verify parsing of fifo_async.v."""
    fifo_path = Path("examples/rtl/fifo_async.v")
    assert fifo_path.exists(), "fifo_async.v must exist"

    modules = VerilogParser.parse_file(fifo_path)
    assert len(modules) == 1

    mod = modules[0]
    assert mod.name == "fifo_async"

    # Check parameters
    param_dict = {p.name: p.default_value for p in mod.parameters}
    assert "DATA_WIDTH" in param_dict
    assert param_dict["DATA_WIDTH"] == "8"
    assert "ADDR_WIDTH" in param_dict
    assert param_dict["ADDR_WIDTH"] == "4"

    # Check ports
    port_dict = {p.name: p for p in mod.ports}
    assert "wclk" in port_dict
    assert port_dict["wclk"].direction == "input"
    assert port_dict["wclk"].is_clock is True

    assert "wrst_n" in port_dict
    assert port_dict["wrst_n"].direction == "input"
    assert port_dict["wrst_n"].is_reset is True

    assert "wfull" in port_dict
    assert port_dict["wfull"].direction == "output"

    assert "rdata" in port_dict
    assert port_dict["rdata"].direction == "output"
    assert port_dict["rdata"].width == "DATA_WIDTH-1:0"


def test_parse_alu_8bit():
    """Verify parsing of alu_8bit.v."""
    alu_path = Path("examples/rtl/alu_8bit.v")
    assert alu_path.exists(), "alu_8bit.v must exist"

    modules = VerilogParser.parse_file(alu_path)
    assert len(modules) == 1

    mod = modules[0]
    assert mod.name == "alu_8bit"

    port_dict = {p.name: p for p in mod.ports}
    assert "clk" in port_dict
    assert port_dict["clk"].is_clock is True

    assert "rst_n" in port_dict
    assert port_dict["rst_n"].is_reset is True

    assert "opcode" in port_dict
    assert port_dict["opcode"].width == "2:0"
