"""Unit tests for STAAnalyzer and timing log diagnostics."""

from pathlib import Path
import pytest
from eda_agent.analyzers.sta_analyzer import STAAnalyzer, TimingReport, TimingPath


def test_parse_timing_violations():
    """Verify parsing of timing report containing setup violations."""
    log_path = Path("examples/logs/openroad_sta_violated.log")
    assert log_path.is_file(), "openroad_sta_violated.log must exist"

    report = STAAnalyzer.parse_file(log_path)
    assert isinstance(report, TimingReport)

    assert report.wns_setup == -0.45
    assert report.tns_setup == -2.85
    assert report.has_setup_violation is True
    assert report.is_clean is False

    assert len(report.setup_paths) == 2
    p1 = report.setup_paths[0]
    assert p1.startpoint == "reg_a[7]"
    assert p1.endpoint == "reg_result[7]"
    assert p1.slack == -0.45
    assert p1.is_violated is True

    # Check recommendations & diff suggestions
    assert len(report.recommendations) > 0
    assert "SETUP VIOLATION" in report.recommendations[0]
    assert len(report.actionable_diffs) > 0
    assert "Suggested Pipeline Stage" in report.actionable_diffs[0]


def test_parse_clean_timing():
    """Verify parsing of clean timing report."""
    log_path = Path("examples/logs/openroad_sta_clean.log")
    assert log_path.is_file(), "openroad_sta_clean.log must exist"

    report = STAAnalyzer.parse_file(log_path)
    assert report.wns_setup == 0.65
    assert report.tns_setup == 0.0
    assert report.has_setup_violation is False
    assert report.is_clean is True

    assert len(report.setup_paths) == 1
    assert report.setup_paths[0].is_violated is False
    assert "All timing constraints met" in report.recommendations[0]


def test_parse_hold_violation_string():
    """Verify parsing of hold timing violations."""
    log_str = """
    Startpoint: reg_fast[0]
    Endpoint: reg_capture[0]
    Path Type: min (Hold)
    Path Group: clk

       0.05   slack (VIOLATED)
    ---------------------------------------------------------
              -0.12   slack (VIOLATED)
    """
    report = STAAnalyzer.parse_string(log_str)
    assert report.has_hold_violation is True
    assert len(report.hold_paths) == 1
    assert report.hold_paths[0].slack == -0.12


def test_file_not_found():
    """Verify error on non-existent file."""
    with pytest.raises(FileNotFoundError):
        STAAnalyzer.parse_file("non_existent_timing.log")
