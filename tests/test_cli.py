"""Unit tests for EDA-Agent Click CLI commands."""

from pathlib import Path
import pytest
from click.testing import CliRunner

from eda_agent.cli import main


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_cli_help(runner: CliRunner):
    """Verify top-level CLI help command."""
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "EDA-Agent" in result.output
    assert "generate" in result.output
    assert "lint" in result.output
    assert "verify" in result.output
    assert "triage-log" in result.output
    assert "synth" in result.output


def test_cli_info(runner: CliRunner):
    """Verify info command displays environment metrics."""
    result = runner.invoke(main, ["info"])
    assert result.exit_code == 0
    assert "EDA-Agent Environment Information" in result.output
    assert "Python Version" in result.output


def test_cli_parse(runner: CliRunner):
    """Verify parse command extracts module interfaces."""
    alu_path = "examples/rtl/alu_8bit.v"
    result = runner.invoke(main, ["parse", alu_path])
    assert result.exit_code == 0
    assert "alu_8bit" in result.output
    assert "opcode" in result.output


def test_cli_generate(runner: CliRunner, tmp_path: Path):
    """Verify generate command creates testbench."""
    alu_path = "examples/rtl/alu_8bit.v"
    out_file = tmp_path / "test_alu_gen.py"

    result = runner.invoke(main, ["generate", alu_path, "-o", str(out_file)])
    assert result.exit_code == 0
    assert out_file.is_file()
    assert "@cocotb.test()" in out_file.read_text(encoding="utf-8")


def test_cli_lint(runner: CliRunner):
    """Verify lint command runs linter and supports JSON output."""
    alu_path = "examples/rtl/alu_8bit.v"
    result = runner.invoke(main, ["lint", alu_path, "-j"])
    assert result.exit_code == 0
    assert "total_errors" in result.output
    assert "diagnostics" in result.output


def test_cli_synth(runner: CliRunner):
    """Verify synth command runs synthesis check and supports JSON."""
    alu_path = "examples/rtl/alu_8bit.v"
    result = runner.invoke(main, ["synth", alu_path, "-j"])
    assert result.exit_code == 0
    assert "cell_count" in result.output
    assert "dff_count" in result.output


def test_cli_triage_log(runner: CliRunner, tmp_path: Path):
    """Verify triage-log command parses error traces."""
    sim_log = tmp_path / "sim_error.log"
    sim_log.write_text(
        "1240.00ns ERROR AssertionError: Op 0: A=0xff, B=0x01: Expected result=0x00, got 0x100\n",
        encoding="utf-8"
    )

    result = runner.invoke(main, ["triage-log", str(sim_log), "-r", "examples/rtl/alu_8bit.v"])
    assert result.exit_code == 0
    assert "Simulation Failure Triage" in result.output
    assert "Hardware Root-Cause" in result.output


def test_cli_assert(runner: CliRunner, tmp_path: Path):
    """Verify assert command generates SVA and cocotb checks."""
    out_file = tmp_path / "asserts.sv"
    result = runner.invoke(main, [
        "assert",
        "examples/rtl/fifo_async.v",
        "-s", "ready drops low when valid is asserted and fifo is full",
        "-o", str(out_file)
    ])
    assert result.exit_code == 0
    assert "p_ready_drops_low" in result.output
    assert out_file.is_file()


def test_cli_analyze_timing(runner: CliRunner):
    """Verify analyze-timing command parses STA reports."""
    log_path = "examples/logs/openroad_sta_violated.log"
    result = runner.invoke(main, ["analyze-timing", log_path])
    assert result.exit_code == 0
    assert "Static Timing Analysis (STA) Summary" in result.output
    assert "-0.450" in result.output
