"""Unit tests for Natural Language Assertion Engine and Human Diagnostics Translator."""

from pathlib import Path
import pytest

from eda_agent.generators.assertion_generator import AssertionGenerator, GeneratedAssertion
from eda_agent.analyzers.human_diagnostics import HumanDiagnosticsTranslator, HardwareFailureDiagnosis
from eda_agent.parsers.verilog_parser import VerilogParser


def test_nl_assertion_generator_ready_drop():
    """Verify SVA and cocotb synthesis for 'ready drops low when valid is asserted and fifo is full'."""
    fifo_path = Path("examples/rtl/fifo_async.v")
    mod = VerilogParser.parse_file(fifo_path)[0]

    generator = AssertionGenerator()
    spec = "ready drops low when valid is asserted and fifo is full"
    result = generator.generate(spec_text=spec, module_spec=mod)

    assert isinstance(result, GeneratedAssertion)
    assert "p_ready_drops_low" in result.property_name
    assert "disable iff (!wrst_n)" in result.sva_code
    assert "@(posedge wclk)" in result.sva_code
    assert "(valid && wfull) |-> (!ready)" in result.sva_code

    # Cocotb
    assert "async def check_p_ready" in result.cocotb_code
    assert "RisingEdge(dut.wclk)" in result.cocotb_code
    assert "dut.ready.value" in result.cocotb_code


def test_nl_assertion_generator_multicycle():
    """Verify multi-cycle delay assertion: 'ack must assert 2 cycles after req rises'."""
    alu_path = Path("examples/rtl/alu_8bit.v")
    mod = VerilogParser.parse_file(alu_path)[0]

    generator = AssertionGenerator()
    spec = "ack must assert 2 cycles after req rises"
    result = generator.generate(spec_text=spec, module_spec=mod)

    assert "$rose(req) |-> ##2 ack" in result.sva_code
    assert "curr_req == 1" in result.cocotb_code
    assert "for _ in range(2):" in result.cocotb_code


def test_nl_assertion_generator_onehot():
    """Verify one-hot assertion synthesis."""
    generator = AssertionGenerator()
    spec = "grant must be one-hot encoded"
    result = generator.generate(spec_text=spec)

    assert "$onehot0(grant)" in result.sva_code
    assert "is_onehot = (val & (val - 1) == 0)" in result.cocotb_code


def test_human_diagnostics_translation():
    """Verify translation of raw simulation logs into hardware engineering terms."""
    raw_sim_log = """
    1241.00ns INFO     cocotb.regression                  running test_alu_8bit.test_alu_8bit_functional (2/3)
    1241.00ns ERROR    cocotb.regression                  Test failed with exception:
    Traceback (most recent call last):
      File "/home/zx0/project/examples/sim/test_alu_8bit.py", line 95, in test_alu_8bit_functional
        assert act_res == exp_res, (
               ^^^^^^^^^^^^^^^^^^
    AssertionError: Op 0: A=0xff, B=0x01: Expected result=0x0, got 0x100
    """

    alu_path = Path("examples/rtl/alu_8bit.v")
    mod = VerilogParser.parse_file(alu_path)[0]

    diag = HumanDiagnosticsTranslator.translate(
        raw_log=raw_sim_log,
        dut_spec=mod,
        clock_period_ns=10.0
    )

    assert isinstance(diag, HardwareFailureDiagnosis)
    assert diag.timestamp_ns == 1241.0
    assert diag.clock_cycle == 124
    assert diag.clock_period_ns == 10.0
    assert "Opcode: 0" in (diag.fsm_state or "")
    assert "result" in diag.violating_signals
    assert diag.violating_signals["result"]["expected"] == "0x0"
    assert diag.violating_signals["result"]["actual"] == "0x100"

    # Engineering summary
    assert "Clock Cycle #124" in diag.engineering_summary
    assert "T = 1241.00 ns" in diag.engineering_summary
    assert "Hardware Root-Cause" in diag.hardware_diagnosis
