"""Unit tests for ResultsAnalyzer."""

import tempfile
from pathlib import Path
import pytest
from eda_agent.analyzers.coverage_analyzer import ResultsAnalyzer


SAMPLE_XML = """<?xml version="1.0" encoding="utf-8"?>
<testsuites name="results">
  <testsuite name="all" package="all">
    <testcase name="test_case_1" classname="test_mod" time="0.01" sim_time_ns="100.0" />
    <testcase name="test_case_2" classname="test_mod" time="0.02" sim_time_ns="200.0" />
  </testsuite>
</testsuites>
"""

SAMPLE_FAIL_XML = """<?xml version="1.0" encoding="utf-8"?>
<testsuites name="results">
  <testsuite name="all" package="all">
    <testcase name="test_pass" classname="test_mod" time="0.01" sim_time_ns="100.0" />
    <testcase name="test_fail" classname="test_mod" time="0.02" sim_time_ns="200.0">
      <failure message="Assertion Error: 1 != 0" type="Failure" />
    </testcase>
  </testsuite>
</testsuites>
"""


def test_parse_passing_xml():
    with tempfile.NamedTemporaryFile("w", suffix=".xml", delete=False) as f:
        f.write(SAMPLE_XML)
        f_path = f.name

    report = ResultsAnalyzer.parse_results_xml(f_path)
    assert report.tests == 2
    assert report.passed == 2
    assert report.failures == 0
    assert report.errors == 0
    assert report.pass_rate_percent == 100.0


def test_parse_failing_xml():
    with tempfile.NamedTemporaryFile("w", suffix=".xml", delete=False) as f:
        f.write(SAMPLE_FAIL_XML)
        f_path = f.name

    report = ResultsAnalyzer.parse_results_xml(f_path)
    assert report.tests == 2
    assert report.passed == 1
    assert report.failures == 1
    assert report.pass_rate_percent == 50.0
    assert report.test_cases[1].passed is False
    assert "Assertion Error" in (report.test_cases[1].failure_message or "")



with tempfile.NamedTemporaryFile("w", suffix=".xml", delete=False) as f:
    f.write(SAMPLE_XML)
    f_path = f.name
    report = ResultsAnalyzer.parse_results_xml(f_path)
