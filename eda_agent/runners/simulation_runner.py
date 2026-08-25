"""Advanced simulation runner with error categorization and diagnostics."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from eda_agent.analyzers.coverage_analyzer import ResultsAnalyzer, TestSuiteReport
from eda_agent.analyzers.human_diagnostics import HardwareFailureDiagnosis, HumanDiagnosticsTranslator


class FailureType(str, Enum):
    """Categorized simulation failure modes."""
    NONE = "NONE"
    ASSERTION_ERROR = "ASSERTION_ERROR"
    TIMEOUT = "TIMEOUT"
    COMPILATION_ERROR = "COMPILATION_ERROR"
    SYNTAX_ERROR = "SYNTAX_ERROR"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    UNKNOWN_FAILURE = "UNKNOWN_FAILURE"


class SimulationDiagnostics(BaseModel):
    """Diagnostic details parsed from a failed simulation run."""
    failure_type: FailureType = FailureType.NONE
    error_summary: str = ""
    failing_testcase: Optional[str] = None
    stack_trace: Optional[str] = None
    line_number: Optional[int] = None
    human_diagnosis: Optional[HardwareFailureDiagnosis] = None
    raw_stderr: str = ""
    raw_stdout: str = ""


class SimulationResult(BaseModel):
    """Structured result of a simulation run including diagnostics."""
    success: bool
    exit_code: int
    duration_seconds: float
    report: Optional[TestSuiteReport] = None
    diagnostics: Optional[SimulationDiagnostics] = None
    stdout: str = ""
    stderr: str = ""
    results_xml_path: Optional[str] = None
    waveform_path: Optional[str] = None


class SimulationCommand(ABC):
    """Polymorphic command builder for local simulation backends."""

    @abstractmethod
    def build(self, clean: bool = False) -> List[str]:
        """Return the executable command for a simulation operation."""


class MakeSimulationCommand(SimulationCommand):
    """Build GNU Make commands used by the cocotb simulation Makefile."""

    def build(self, clean: bool = False) -> List[str]:
        return ["make", "clean"] if clean else ["make"]


class SimulationRunner:
    """Runner for cocotb simulations with automated failure diagnosis."""

    command: SimulationCommand = MakeSimulationCommand()

    @classmethod
    def run(
        cls,
        work_dir: str | Path,
        toplevel: Optional[str] = None,
        module: Optional[str] = None,
        simulator: str = "icarus",
        waves: bool = True,
        clean: bool = False,
        timeout: int = 120,
        extra_env: Optional[Dict[str, str]] = None,
    ) -> SimulationResult:
        """Execute a cocotb simulation and return structured results and diagnostics."""
        work_path = Path(work_dir).resolve()
        if not work_path.exists():
            raise FileNotFoundError(f"Simulation directory does not exist: {work_path}")

        env = os.environ.copy()
        py_bin_dir = str(Path(sys.executable).parent)
        user_local_bin = str(Path.home() / ".local" / "bin")
        current_path = env.get("PATH", "")
        env["PATH"] = os.pathsep.join((py_bin_dir, user_local_bin, current_path))
        env["COCOTB_IGNORE_PYTHON_REQUIRES"] = "1"
        env["SIM"] = simulator
        env["WAVES"] = "1" if waves else "0"

        if toplevel:
            env["TOPLEVEL"] = toplevel
            env["SIM_BUILD"] = f"sim_build_{toplevel}"
        if module:
            env["MODULE"] = module
            env["COCOTB_TEST_MODULES"] = module
        if extra_env:
            env.update(extra_env)

        start_time = time.time()

        try:
            executable = cls.command.build()[0]
            if shutil.which(executable, path=env["PATH"]) is None:
                raise FileNotFoundError(executable)

            if clean:
                subprocess.run(
                    cls.command.build(clean=True),
                    cwd=str(work_path),
                    env=env,
                    capture_output=True,
                    text=True,
                )

            proc = subprocess.run(
                cls.command.build(),
                cwd=str(work_path),
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            duration = round(time.time() - start_time, 3)
            stdout = proc.stdout
            stderr = proc.stderr
            exit_code = proc.returncode

        except subprocess.TimeoutExpired as exc:
            duration = round(time.time() - start_time, 3)
            stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = f"Simulation timed out after {timeout} seconds."
            exit_code = -1

        except FileNotFoundError as exc:
            duration = round(time.time() - start_time, 3)
            missing_command = exc.filename or cls.command.build()[0]
            stdout = ""
            stderr = (
                f"Unable to start simulation: '{missing_command}' was not found on PATH. "
                "Install GNU Make and Icarus Verilog, then restart the EDA-Agent server."
            )
            exit_code = 127

        # Search for results.xml
        candidates = [
            work_path / f"sim_build_{toplevel}" / "results.xml" if toplevel else None,
            work_path / "results.xml",
            work_path / "sim_build" / "results.xml",
        ]
        results_xml = next((p for p in candidates if p and p.exists()), None)

        # Search for waveform file (.fst or .vcd)
        vcd_candidates = [
            work_path / f"sim_build_{toplevel}" / f"{toplevel}.fst" if toplevel else None,
            work_path / f"sim_build_{toplevel}" / "dump.fst" if toplevel else None,
            work_path / f"sim_build_{toplevel}" / "dump.vcd" if toplevel else None,
            work_path / "dump.vcd",
            work_path / "sim_build" / "dump.vcd",
        ]
        waveform_file = next((p for p in vcd_candidates if p and p.exists()), None)

        report = None
        if results_xml and results_xml.exists():
            try:
                report = ResultsAnalyzer.parse_results_xml(results_xml)
            except Exception:
                report = None

        success = (exit_code == 0) and (report is not None and report.failures == 0 and report.errors == 0)

        diagnostics = None
        if not success:
            diagnostics = cls.diagnose_failure(stdout=stdout, stderr=stderr, report=report, exit_code=exit_code)

        return SimulationResult(
            success=success,
            exit_code=exit_code,
            duration_seconds=duration,
            report=report,
            diagnostics=diagnostics,
            stdout=stdout,
            stderr=stderr,
            results_xml_path=str(results_xml) if results_xml else None,
            waveform_path=str(waveform_file) if waveform_file else None,
        )

    @classmethod
    def diagnose_failure(
        cls,
        stdout: str,
        stderr: str,
        report: Optional[TestSuiteReport] = None,
        exit_code: int = 0
    ) -> SimulationDiagnostics:
        """Analyze simulation logs and reports to identify failure types and tracebacks."""
        combined_logs = f"{stdout}\n{stderr}"

        # 1. Timeout detection
        if exit_code == -1 or "Simulation timed out" in stderr or "timed out" in combined_logs.lower():
            return SimulationDiagnostics(
                failure_type=FailureType.TIMEOUT,
                error_summary="Simulation exceeded timeout threshold (potential deadlock or hang).",
                raw_stderr=stderr,
                raw_stdout=stdout
            )

        # Missing make/simulator binaries on local development machines.
        if "was not found on PATH" in combined_logs:
            return SimulationDiagnostics(
                failure_type=FailureType.COMPILATION_ERROR,
                error_summary=stderr.strip(),
                raw_stderr=stderr,
                raw_stdout=stdout
            )

        # 2. Syntax errors in testbench
        syntax_match = re.search(r'SyntaxError:\s*(.*)', combined_logs)
        if syntax_match:
            line_m = re.search(r'line\s+(\d+)', combined_logs)
            return SimulationDiagnostics(
                failure_type=FailureType.SYNTAX_ERROR,
                error_summary=f"Python Syntax Error: {syntax_match.group(1)}",
                line_number=int(line_m.group(1)) if line_m else None,
                stack_trace=cls._extract_traceback(combined_logs),
                raw_stderr=stderr,
                raw_stdout=stdout
            )

        # 3. Verilog/Icarus compilation errors
        if "error: " in combined_logs or "iverilog:" in combined_logs or "syntax error" in combined_logs.lower():
            comp_errors = [line for line in combined_logs.splitlines() if "error:" in line.lower()]
            summary = "\n".join(comp_errors[:5]) if comp_errors else "RTL or Simulation Makefile compilation failed."
            return SimulationDiagnostics(
                failure_type=FailureType.COMPILATION_ERROR,
                error_summary=summary,
                raw_stderr=stderr,
                raw_stdout=stdout
            )

        human_diag = HumanDiagnosticsTranslator.translate(combined_logs)

        # 4. Assertion errors from test suite report or logs
        if report and (report.failures > 0 or report.errors > 0):
            for tc in report.test_cases:
                if not tc.passed:
                    if tc.failure_type == "Error":
                        fail_type = FailureType.RUNTIME_ERROR
                    else:
                        fail_type = FailureType.ASSERTION_ERROR

                    return SimulationDiagnostics(
                        failure_type=fail_type,
                        error_summary=tc.failure_message or f"Test {tc.name} failed.",
                        failing_testcase=tc.name,
                        stack_trace=cls._extract_traceback(combined_logs),
                        human_diagnosis=human_diag,
                        raw_stderr=stderr,
                        raw_stdout=stdout
                    )

        assertion_m = re.search(r'AssertionError:\s*(.*)', combined_logs)
        if assertion_m:
            return SimulationDiagnostics(
                failure_type=FailureType.ASSERTION_ERROR,
                error_summary=f"Assertion Failed: {assertion_m.group(1)}",
                stack_trace=cls._extract_traceback(combined_logs),
                human_diagnosis=human_diag,
                raw_stderr=stderr,
                raw_stdout=stdout
            )

        # 5. Generic Python Runtime Error / Exception
        traceback_str = cls._extract_traceback(combined_logs)
        if traceback_str:
            exc_lines = [l for l in traceback_str.strip().splitlines() if ":" in l]
            summary = exc_lines[-1] if exc_lines else "Python runtime exception occurred."
            return SimulationDiagnostics(
                failure_type=FailureType.RUNTIME_ERROR,
                error_summary=summary,
                stack_trace=traceback_str,
                human_diagnosis=human_diag,
                raw_stderr=stderr,
                raw_stdout=stdout
            )

        return SimulationDiagnostics(
            failure_type=FailureType.UNKNOWN_FAILURE,
            error_summary="Simulation exited with non-zero status without recognized error signature.",
            human_diagnosis=human_diag,
            raw_stderr=stderr,
            raw_stdout=stdout
        )

    @staticmethod
    def _extract_traceback(logs: str) -> Optional[str]:
        """Extract Python exception traceback block from output logs."""
        match = re.search(r'(Traceback \(most recent call last\):[\s\S]*?(?:[a-zA-Z_]\w*Error:[^\n]+|Exception:[^\n]+))', logs)
        if match:
            return match.group(1).strip()
        return None


# Backwards compatibility alias
CocotbRunner = SimulationRunner
