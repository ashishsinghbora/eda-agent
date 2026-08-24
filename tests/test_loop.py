"""Unit tests for the autonomous VerificationLoop and diagnostic repair mechanism."""

from pathlib import Path
import pytest
from eda_agent.generators.repair_loop import VerificationLoop
from eda_agent.generators.testbench_generator import TestbenchGenerator
from eda_agent.generators.llm_client import BaseLLMClient
from eda_agent.runners.simulation_runner import FailureType, SimulationRunner


def test_diagnostics_categorization():
    """Verify categorization of various simulation errors."""
    # Syntax error
    diag_syntax = SimulationRunner.diagnose_failure(
        stdout="",
        stderr="File 'test_tb.py', line 12\n    dut.a = \n            ^\nSyntaxError: invalid syntax",
        exit_code=1
    )
    assert diag_syntax.failure_type == FailureType.SYNTAX_ERROR
    assert diag_syntax.line_number == 12

    # Timeout
    diag_timeout = SimulationRunner.diagnose_failure(
        stdout="",
        stderr="Simulation timed out after 120 seconds",
        exit_code=-1
    )
    assert diag_timeout.failure_type == FailureType.TIMEOUT

    # Compilation error
    diag_comp = SimulationRunner.diagnose_failure(
        stdout="/usr/bin/iverilog: error: Unknown module port foo",
        stderr="make: *** [Makefile:20: sim] Error 1",
        exit_code=2
    )
    assert diag_comp.failure_type == FailureType.COMPILATION_ERROR

    # Assertion error
    diag_assert = SimulationRunner.diagnose_failure(
        stdout="Traceback (most recent call last):\n  File 'test.py', line 45\nAssertionError: 0 != 255",
        stderr="",
        exit_code=1
    )
    assert diag_assert.failure_type == FailureType.ASSERTION_ERROR


def test_end_to_end_verification_loop_alu():
    """Verify autonomous end-to-end verification loop on alu_8bit.v."""
    alu_path = Path("examples/rtl/alu_8bit.v")
    sim_dir = Path("examples/sim")

    loop = VerificationLoop()
    result = loop.run(
        rtl_file=alu_path,
        sim_dir=sim_dir,
        max_retries=3,
        clean=True
    )

    assert result.success is True
    assert result.module_name == "alu_8bit"
    assert result.attempts >= 1
    assert Path(result.testbench_path).is_file()
    assert result.final_sim_result.success is True
    assert result.final_sim_result.report is not None
    assert result.final_sim_result.report.failures == 0


def test_closed_loop_repair_behavior():
    """Verify that a broken initial testbench is diagnosed and repaired by the loop."""
    class FailingFirstLLMClient(BaseLLMClient):
        def __init__(self):
            self.call_count = 0

        def generate(self, prompt: str, system_prompt=None) -> str:
            self.call_count += 1
            if self.call_count == 1:
                # Deliberately broken testbench with assertion failure on first try
                return """```python
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer, RisingEdge

@cocotb.test()
async def test_broken_attempt(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.rst_n.value = 0
    await Timer(20, unit="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    # Deliberate assertion failure to test repair loop
    assert False, "Deliberate test failure for repair loop test"
```"""
            else:
                # Repaired working testbench on subsequent try
                from eda_agent.generators.llm_client import RuleBasedLLMClient
                return RuleBasedLLMClient().generate(prompt, system_prompt)

    custom_client = FailingFirstLLMClient()
    generator = TestbenchGenerator(llm_client=custom_client)
    loop = VerificationLoop(generator=generator)

    alu_path = Path("examples/rtl/alu_8bit.v")
    sim_dir = Path("examples/sim")

    result = loop.run(
        rtl_file=alu_path,
        sim_dir=sim_dir,
        max_retries=3,
        clean=True
    )

    # Must succeed after repair (2 attempts)
    assert result.success is True
    assert result.attempts == 2
    assert len(result.iterations) == 2
    assert result.iterations[0].sim_result.success is False
    assert result.iterations[0].sim_result.diagnostics.failure_type == FailureType.ASSERTION_ERROR
    assert result.iterations[1].sim_result.success is True
