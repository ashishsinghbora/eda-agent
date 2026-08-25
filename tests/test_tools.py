"""Unit tests for deterministic tool wrappers (Verilator, Yosys, Cocotb)."""

from pathlib import Path
import pytest

from eda_agent.tools.base import BaseTool, ToolResult
from eda_agent.tools.verilator_linter import LintDiagnostic, LintReport, LintSeverity, VerilatorLinter
from eda_agent.tools.synthesis_checker import SynthesisChecker, SynthesisReport
from eda_agent.tools.sim_runner import SimRunner


def test_base_tool_path_resolution():
    """Verify tool runner locates executables."""
    assert BaseTool.get_extended_path() is not None
    # python executable should be found
    py = BaseTool.find_binary("python3")
    assert py is not None


def test_verilator_linter_parsing():
    """Verify parsing of standard Verilator lint warnings."""
    sample_verilator_output = """
%Warning-WIDTHEXPAND: /path/to/alu.v:34:15: Operator ADD expects 8 bits on LHS, but RHS is 9 bits.
%Warning-BLKSEQ: /path/to/alu.v:50:8: Blocking assignment '=' in sequential block
%Error: /path/to/alu.v:60:2: syntax error, unexpected endmodule
"""
    report = VerilatorLinter.parse_verilator_output(sample_verilator_output)
    assert isinstance(report, LintReport)
    assert report.total_errors == 1
    assert report.total_warnings == 2
    assert report.success is False

    d_blkseq = next(d for d in report.diagnostics if d.code == "BLKSEQ")
    assert d_blkseq.line == 50
    assert d_blkseq.column == 8
    assert d_blkseq.severity == LintSeverity.WARNING
    assert "non-blocking" in (d_blkseq.suggestion or "")


def test_verilator_linter_clean_code():
    """Verify clean linting on synthesizable ALU RTL."""
    alu_path = Path("examples/rtl/alu_8bit.v")
    report = VerilatorLinter.lint_file(alu_path, top_module="alu_8bit")
    assert isinstance(report, LintReport)
    assert report.total_errors == 0


def test_synthesis_checker_clean_code():
    """Verify synthesis check on synthesizable ALU RTL."""
    alu_path = Path("examples/rtl/alu_8bit.v")
    report = SynthesisChecker.check_file(alu_path, top_module="alu_8bit")
    assert isinstance(report, SynthesisReport)
    assert report.top_module == "alu_8bit"
    assert report.cell_count > 0
    assert len(report.errors) == 0


def test_synthesis_checker_yosys_log_parsing():
    """Verify parsing of Yosys synthesis logs and cell counts."""
    sample_yosys_log = """
=== alu_8bit ===
   Number of wires:                 42
   Number of wire bits:            110
   Number of public wires:          42
   Number of public wire bits:     110
   Number of memories:               0
   Number of memory bits:            0
   Number of processes:              0
   Number of cells:                 35
     $_DFF_P_                       11
     $_NAND_                         8
     $_OR_                          12
     $_XOR_                          4

   Chip area for top module 'alu_8bit': 120.0
"""
    report = SynthesisChecker.parse_yosys_output(sample_yosys_log, "alu_8bit")
    assert report.success is True
    assert report.cell_count == 35
    assert report.dff_count == 11
    assert report.latch_count == 0
    assert report.wire_count == 42
    assert report.cells_by_type["$_DFF_P_"] == 11
    assert report.cells_by_type["$_NAND_"] == 8


def test_sim_runner_fifo():
    """Verify simulation runner on async FIFO."""
    res = SimRunner.run(
        work_dir="examples/sim",
        toplevel="fifo_async",
        module="test_fifo_async",
        clean=True
    )
    assert res.success is True
    assert res.exit_code == 0
    assert res.report is not None
    assert res.report.failures == 0
