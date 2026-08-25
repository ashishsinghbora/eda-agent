"""Hardware-Centric Simulation Log Diagnostic & Human Translator."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from eda_agent.core import DiagnosticProcessor
from eda_agent.schemas import ModuleSpec


class HardwareFailureDiagnosis(BaseModel):
    """Hardware engineering translation of a simulation failure or assertion violation."""
    timestamp_ns: float = Field(default=0.0, description="Simulation timestamp in nanoseconds when failure occurred")
    clock_cycle: Optional[int] = Field(default=None, description="Calculated clock cycle index")
    clock_period_ns: float = Field(default=10.0, description="Clock period used for cycle calculation")
    fsm_state: Optional[str] = Field(default=None, description="Active FSM state, opcode, or transaction phase")
    violating_signals: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Signals with expected vs actual values: {'sig': {'expected': X, 'actual': Y}}"
    )
    failing_assertion: Optional[str] = Field(default=None, description="Assertion condition or check that failed")
    raw_error: str = Field(default="", description="Original raw error snippet or stack trace")
    engineering_summary: str = Field(description="Plain-English explanation of the failure in digital design terms")
    hardware_diagnosis: str = Field(description="Hardware root-cause analysis and recommended RTL fix")


class HumanDiagnosticsTranslator(DiagnosticProcessor):
    """Translates simulator errors and assertion failures into digital hardware engineering diagnostics."""

    @classmethod
    def translate(
        cls,
        raw_log: str,
        dut_spec: Optional[ModuleSpec] = None,
        clock_period_ns: float = 10.0,
    ) -> HardwareFailureDiagnosis:
        """Parse raw simulator logs and produce a hardware engineering diagnosis."""
        # 1. Extract simulation timestamp
        timestamp_ns = cls._extract_timestamp(raw_log)

        # 2. Compute clock cycle number
        clock_cycle = int(timestamp_ns / clock_period_ns) if clock_period_ns > 0 else None

        # 3. Detect FSM state or active opcode
        fsm_state = cls._extract_fsm_state(raw_log, dut_spec)

        # 4. Extract violating signals and values
        violating_signals = cls._extract_violating_signals(raw_log)

        # 5. Extract failing assertion
        assertion_msg = cls._extract_assertion_message(raw_log)

        # 6. Synthesize engineering summary and root-cause analysis
        summary, diagnosis = cls._synthesize_narrative(
            timestamp_ns=timestamp_ns,
            clock_cycle=clock_cycle,
            fsm_state=fsm_state,
            violating_signals=violating_signals,
            assertion_msg=assertion_msg,
            dut_spec=dut_spec
        )

        return HardwareFailureDiagnosis(
            timestamp_ns=timestamp_ns,
            clock_cycle=clock_cycle,
            clock_period_ns=clock_period_ns,
            fsm_state=fsm_state,
            violating_signals=violating_signals,
            failing_assertion=assertion_msg,
            raw_error=assertion_msg or raw_log[:300],
            engineering_summary=summary,
            hardware_diagnosis=diagnosis
        )

    @classmethod
    def _extract_timestamp(cls, log: str) -> float:
        """Extract simulation time from cocotb / simulator log lines (e.g., '1241.00ns', 'time: 250 ns')."""
        m = re.search(r'([0-9]+\.?[0-9]*)\s*ns\s+(?:INFO|ERROR|WARNING|CRITICAL)', log)
        if m:
            return float(m.group(1))

        m_alt = re.search(r'(?:SIM TIME|sim time|time|at)\s*[:=]?\s*([0-9]+\.?[0-9]*)\s*(?:ns)?', log, re.IGNORECASE)
        if m_alt:
            return float(m_alt.group(1))

        return 0.0

    @classmethod
    def _extract_fsm_state(cls, log: str, dut_spec: Optional[ModuleSpec]) -> Optional[str]:
        """Detect active state machine state, opcode, or transaction phase."""
        if dut_spec and dut_spec.fsm_states:
            for st in dut_spec.fsm_states:
                if re.search(r'\b' + re.escape(st.name) + r'\b', log):
                    return st.name

        # Opcode detection
        m_op = re.search(r'(?:Op|Opcode|opcode|OP_)\s*[:=]?\s*([0-9]+|[A-Z_]+)', log)
        if m_op:
            return f"Opcode: {m_op.group(1)}"

        # State detection
        m_state = re.search(r'(?:state|STATE|fsm_state)\s*[:=]?\s*([0-9A-Za-z_]+)', log)
        if m_state:
            return f"State: {m_state.group(1)}"

        return None

    @classmethod
    def _extract_violating_signals(cls, log: str) -> Dict[str, Dict[str, Any]]:
        """Extract signal mismatch details from assertion error strings."""
        signals: Dict[str, Dict[str, Any]] = {}

        # Pattern: "Expected result=0x5, got 0x0" / "expected 255, got 0"
        m_exp_got = re.findall(r'expected\s+([a-zA-Z_0-9$]+)?\s*[:=]?\s*([0-9a-fx]+),\s*got\s*([0-9a-fx]+)', log, re.IGNORECASE)
        for sig, exp, act in m_exp_got:
            sig_name = sig if sig else "output"
            signals[sig_name] = {"expected": exp, "actual": act}

        # Pattern: "A=0xff, B=0x01"
        m_inputs = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(0x[0-9a-fA-F]+|\d+)\b', log)
        for sig, val in m_inputs:
            if sig.lower() not in ("expected", "got", "line", "unit", "sim", "time"):
                if sig not in signals:
                    signals[sig] = {"value": val}

        # Pattern: "dut.wfull is 1, expected 0"
        m_dut_sig = re.findall(r'dut\.([a-zA-Z_0-9$]+)\s+is\s+([0-9a-fx]+),\s*expected\s+([0-9a-fx]+)', log, re.IGNORECASE)
        for sig, act, exp in m_dut_sig:
            signals[sig] = {"expected": exp, "actual": act}

        return signals

    @classmethod
    def _extract_assertion_message(cls, log: str) -> Optional[str]:
        """Extract the core assertion failure message."""
        m_assert = re.search(r'AssertionError:\s*([^\n]+)', log)
        if m_assert:
            return m_assert.group(1).strip()

        m_fail = re.search(r'Assertion\s+([a-zA-Z_0-9$]+)\s+violated:\s*([^\n]+)', log, re.IGNORECASE)
        if m_fail:
            return f"{m_fail.group(1)}: {m_fail.group(2).strip()}"

        return None

    @classmethod
    def _synthesize_narrative(
        cls,
        timestamp_ns: float,
        clock_cycle: Optional[int],
        fsm_state: Optional[str],
        violating_signals: Dict[str, Dict[str, Any]],
        assertion_msg: Optional[str],
        dut_spec: Optional[ModuleSpec]
    ) -> tuple[str, str]:
        """Synthesize digital hardware engineer narrative summary and root cause."""
        cycle_str = f"at Clock Cycle #{clock_cycle} " if clock_cycle is not None else ""
        time_str = f"at T = {timestamp_ns:.2f} ns"

        module_name = dut_spec.name if dut_spec else "RTL module"

        # Summary
        if assertion_msg:
            summary = f"Assertion failure in `{module_name}` {cycle_str}({time_str}). Violation: {assertion_msg}"
        else:
            summary = f"Simulation discrepancy observed in `{module_name}` {cycle_str}({time_str})."

        # Diagnosis
        diag_lines = []
        if fsm_state:
            diag_lines.append(f"Active Transaction / FSM Context: `{fsm_state}`.")

        if violating_signals:
            mismatches = []
            for sig, data in violating_signals.items():
                if "expected" in data and "actual" in data:
                    mismatches.append(f"Signal `{sig}`: Expected `{data['expected']}`, observed `{data['actual']}`")
                elif "value" in data:
                    mismatches.append(f"Input `{sig}` was `{data['value']}`")
            if mismatches:
                diag_lines.append("Signal Breakdown: " + "; ".join(mismatches) + ".")

        diag_lines.append(
            "Hardware Root-Cause: Output combinational settling delay or register state update did not match expected behavioral transfer. "
            "Inspect combinational sensitivity list and synchronous reset deassertion."
        )

        diagnosis = " ".join(diag_lines)
        return summary, diagnosis
