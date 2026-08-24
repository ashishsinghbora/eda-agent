"""Unit tests for CocotbRunner."""

from pathlib import Path
import pytest
from eda_agent.runners.cocotb_runner import CocotbRunner


def test_cocotb_runner_fifo():
    """Test running fifo simulation via CocotbRunner."""
    result = CocotbRunner.run_make(
        work_dir="examples/sim",
        toplevel="fifo_async",
        module="test_fifo_async",
        clean=True
    )
    assert result.success is True
    assert result.exit_code == 0
    assert result.results_xml_path is not None
    assert Path(result.results_xml_path).exists()
