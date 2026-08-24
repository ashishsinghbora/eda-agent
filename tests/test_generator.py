"""Unit tests for Testbench Generator and Prompts."""

from pathlib import Path
import pytest
from eda_agent.parsers.verilog_parser import VerilogParser
from eda_agent.generators.testbench_generator import TestbenchGenerator
from eda_agent.runners.simulation_runner import FailureType, SimulationDiagnostics


def test_generator_prompt_building():
    """Verify prompt formatting with ModuleSpec."""
    alu_path = Path("examples/rtl/alu_8bit.v")
    mod = VerilogParser.parse_file(alu_path)[0]

    generator = TestbenchGenerator()
    prompt = generator.build_generation_prompt(mod)

    assert "alu_8bit" in prompt
    assert "DATA_WIDTH" in prompt
    assert "clk" in prompt
    assert "rst_n" in prompt
    assert "opcode" in prompt
    assert "OP_ADD" in prompt


def test_python_code_extraction():
    """Verify clean extraction of Python code from markdown."""
    markdown_text = """
    Here is the generated testbench:
    ```python
    import cocotb
    @cocotb.test()
    async def test_sample(dut):
        pass
    ```
    Good luck!
    """
    code = TestbenchGenerator.extract_python_code(markdown_text)
    assert code.startswith("import cocotb")
    assert "def test_sample" in code
    assert "Here is the generated" not in code
    assert "```" not in code


def test_generate_alu_testbench():
    """Verify synthesis of ALU testbench."""
    alu_path = Path("examples/rtl/alu_8bit.v")
    mod = VerilogParser.parse_file(alu_path)[0]

    generator = TestbenchGenerator()
    code = generator.generate(mod)

    assert "@cocotb.test()" in code
    assert "test_alu_8bit_reset" in code
    assert "test_alu_8bit_functional" in code
    assert "test_alu_8bit_corner_cases" in code
    assert "Clock(dut.clk" in code


def test_repair_prompt_building():
    """Verify construction of repair prompt with diagnostics."""
    alu_path = Path("examples/rtl/alu_8bit.v")
    mod = VerilogParser.parse_file(alu_path)[0]

    diagnostics = SimulationDiagnostics(
        failure_type=FailureType.ASSERTION_ERROR,
        error_summary="AssertionError: Expected 255, got 0",
        failing_testcase="test_alu_functional",
        stack_trace="Traceback: ... line 42 in reader ... AssertionError: 0 != 255"
    )

    generator = TestbenchGenerator()
    repair_prompt = generator.build_repair_prompt(
        spec=mod,
        broken_code="def broken_test(): pass",
        diagnostics=diagnostics
    )

    assert "ASSERTION_ERROR" in repair_prompt
    assert "AssertionError: Expected 255, got 0" in repair_prompt
    assert "test_alu_functional" in repair_prompt
    assert "broken_test" in repair_prompt
