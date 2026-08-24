"""Analyzer for Cocotb simulation results and coverage."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field


class TestCaseResult(BaseModel):
    """Result of an individual test case."""
    name: str
    classname: str
    time: float = 0.0
    sim_time_ns: float = 0.0
    passed: bool = True
    failure_message: Optional[str] = None
    failure_type: Optional[str] = None


class TestSuiteReport(BaseModel):
    """Aggregated report of a simulation test suite."""
    name: str
    tests: int = 0
    passed: int = 0
    failures: int = 0
    errors: int = 0
    skipped: int = 0
    total_time: float = 0.0
    test_cases: List[TestCaseResult] = Field(default_factory=list)

    @property
    def pass_rate_percent(self) -> float:
        """Calculate pass rate percentage."""
        if self.tests == 0:
            return 0.0
        return round((self.passed / self.tests) * 100.0, 2)


class ResultsAnalyzer:
    """Parser and analyzer for cocotb simulation results."""

    @classmethod
    def parse_results_xml(cls, xml_path: str | Path) -> TestSuiteReport:
        """Parse cocotb results.xml file into structured TestSuiteReport."""
        path = Path(xml_path)
        if not path.is_file():
            raise FileNotFoundError(f"Results XML file not found at: {xml_path}")

        tree = ET.parse(path)
        root = tree.getroot()

        # Check if root is testsuite or testsuites
        if root.tag == "testsuites":
            suite = root.find("testsuite")
            if suite is None:
                suite = root
        else:
            suite = root

        name = suite.attrib.get("name", "cocotb_suite")
        test_cases: List[TestCaseResult] = []

        failures_count = 0
        errors_count = 0
        skipped_count = 0
        total_time = 0.0

        for tc_elem in suite.findall("testcase"):
            tc_name = tc_elem.attrib.get("name", "unknown")
            tc_class = tc_elem.attrib.get("classname", "")
            tc_time = float(tc_elem.attrib.get("time", 0.0))
            sim_time = float(tc_elem.attrib.get("sim_time_ns", 0.0))
            total_time += tc_time

            failure = tc_elem.find("failure")
            error = tc_elem.find("error")
            skipped = tc_elem.find("skipped")

            is_pass = (failure is None and error is None and skipped is None)
            fail_msg = None
            fail_type = None

            if failure is not None:
                failures_count += 1
                fail_msg = failure.attrib.get("message", failure.text or "")
                fail_type = failure.attrib.get("type", "Failure")
            elif error is not None:
                errors_count += 1
                fail_msg = error.attrib.get("message", error.text or "")
                fail_type = error.attrib.get("type", "Error")
            elif skipped is not None:
                skipped_count += 1

            test_cases.append(TestCaseResult(
                name=tc_name,
                classname=tc_class,
                time=tc_time,
                sim_time_ns=sim_time,
                passed=is_pass,
                failure_message=fail_msg,
                failure_type=fail_type
            ))

        total_tests = int(suite.attrib.get("tests", len(test_cases)))
        if "failures" in suite.attrib:
            failures_count = int(suite.attrib["failures"])
        if "errors" in suite.attrib:
            errors_count = int(suite.attrib["errors"])
        if "skipped" in suite.attrib:
            skipped_count = int(suite.attrib["skipped"])
        if "time" in suite.attrib:
            total_time = float(suite.attrib["time"])

        passed_count = total_tests - failures_count - errors_count - skipped_count

        return TestSuiteReport(
            name=name,
            tests=total_tests,
            passed=passed_count,
            failures=failures_count,
            errors=errors_count,
            skipped=skipped_count,
            total_time=round(total_time, 4),
            test_cases=test_cases
        )
