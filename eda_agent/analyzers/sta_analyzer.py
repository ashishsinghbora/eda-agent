"""Static Timing Analysis (STA) log parser and structural RTL repair advisor."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field, computed_field


class TimingPath(BaseModel):
    """Represents an individual critical timing path from STA report."""
    startpoint: str = Field(description="Launch register or primary input")
    endpoint: str = Field(description="Capture register or primary output")
    path_type: str = Field(default="setup", description="'setup' (max) or 'hold' (min)")
    clock: Optional[str] = Field(default=None, description="Clock domain")
    slack: float = Field(description="Path slack in nanoseconds (negative indicates violation)")
    arrival_time: float = Field(default=0.0, description="Data arrival time in ns")
    required_time: float = Field(default=0.0, description="Data required time in ns")
    is_violated: bool = Field(default=False, description="True if slack < 0")
    critical_signals: List[str] = Field(default_factory=list, description="Intermediate signals along critical path")


class TimingReport(BaseModel):
    """Aggregated Static Timing Analysis (STA) metrics and diagnostics."""
    wns_setup: float = Field(default=0.0, description="Worst Negative Slack for Setup (ns)")
    tns_setup: float = Field(default=0.0, description="Total Negative Slack for Setup (ns)")
    wns_hold: float = Field(default=0.0, description="Worst Negative Slack for Hold (ns)")
    tns_hold: float = Field(default=0.0, description="Total Negative Slack for Hold (ns)")
    setup_paths: List[TimingPath] = Field(default_factory=list, description="Parsed setup paths")
    hold_paths: List[TimingPath] = Field(default_factory=list, description="Parsed hold paths")
    recommendations: List[str] = Field(default_factory=list, description="Recommended architectural RTL fixes")
    actionable_diffs: List[str] = Field(default_factory=list, description="Suggested Verilog diff snippets")

    @computed_field
    @property
    def has_setup_violation(self) -> bool:
        """Return True if setup timing is violated."""
        return self.wns_setup < -0.001 or any(p.is_violated for p in self.setup_paths)

    @computed_field
    @property
    def has_hold_violation(self) -> bool:
        """Return True if hold timing is violated."""
        return self.wns_hold < -0.001 or any(p.is_violated for p in self.hold_paths)

    @computed_field
    @property
    def is_clean(self) -> bool:
        """Return True if all setup and hold timing constraints are met."""
        return not self.has_setup_violation and not self.has_hold_violation


class STAAnalyzer:
    """Parser for OpenROAD, OpenSTA, and Yosys timing reports with RTL repair advisor."""

    @classmethod
    def parse_file(cls, file_path: str | Path) -> TimingReport:
        """Parse an STA timing report from file."""
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Timing log file not found: {file_path}")
        content = path.read_text(encoding="utf-8")
        return cls.parse_string(content)

    @classmethod
    def parse_string(cls, content: str) -> TimingReport:
        """Parse timing metrics and critical paths from raw log content."""
        wns_setup = cls._extract_metric(content, [
            r'Worst\s+Negative\s+Slack\s*\(WNS\)\s*:\s*([+-]?\d+\.?\d*)',
            r'Setup\s+WNS\s*:\s*([+-]?\d+\.?\d*)',
            r'wns_max\s*[:=]?\s*([+-]?\d+\.?\d*)',
            r'wns\s*[:=]?\s*([+-]?\d+\.?\d*)',
        ], default=0.0)

        tns_setup = cls._extract_metric(content, [
            r'Total\s+Negative\s+Slack\s*\(TNS\)\s*:\s*([+-]?\d+\.?\d*)',
            r'Setup\s+TNS\s*:\s*([+-]?\d+\.?\d*)',
            r'tns_max\s*[:=]?\s*([+-]?\d+\.?\d*)',
            r'tns\s*[:=]?\s*([+-]?\d+\.?\d*)',
        ], default=0.0)

        wns_hold = cls._extract_metric(content, [
            r'Hold\s+WNS\s*:\s*([+-]?\d+\.?\d*)',
            r'wns_min\s*[:=]?\s*([+-]?\d+\.?\d*)',
            r'Worst\s+Hold\s+Slack\s*:\s*([+-]?\d+\.?\d*)',
        ], default=0.0)

        tns_hold = cls._extract_metric(content, [
            r'Hold\s+TNS\s*:\s*([+-]?\d+\.?\d*)',
            r'tns_min\s*[:=]?\s*([+-]?\d+\.?\d*)',
            r'Total\s+Hold\s+Slack\s*:\s*([+-]?\d+\.?\d*)',
        ], default=0.0)

        paths = cls._parse_timing_paths(content)

        setup_paths = [p for p in paths if p.path_type == "setup"]
        hold_paths = [p for p in paths if p.path_type == "hold"]

        # Recalculate WNS/TNS from parsed paths if not explicitly in summary
        if setup_paths and wns_setup == 0.0:
            min_setup_slack = min(p.slack for p in setup_paths)
            if min_setup_slack < 0:
                wns_setup = min_setup_slack
                tns_setup = sum(p.slack for p in setup_paths if p.slack < 0)

        if hold_paths and wns_hold == 0.0:
            min_hold_slack = min(p.slack for p in hold_paths)
            if min_hold_slack < 0:
                wns_hold = min_hold_slack
                tns_hold = sum(p.slack for p in hold_paths if p.slack < 0)

        report = TimingReport(
            wns_setup=round(wns_setup, 3),
            tns_setup=round(tns_setup, 3),
            wns_hold=round(wns_hold, 3),
            tns_hold=round(tns_hold, 3),
            setup_paths=setup_paths,
            hold_paths=hold_paths,
        )

        # Generate intelligent RTL structural recommendations and diffs
        report.recommendations = cls.generate_recommendations(report)
        report.actionable_diffs = cls.generate_actionable_diffs(report)

        return report

    @classmethod
    def _extract_metric(cls, content: str, patterns: List[str], default: float = 0.0) -> float:
        """Extract a floating point metric matching regex patterns."""
        for pattern in patterns:
            m = re.search(pattern, content, re.IGNORECASE)
            if m:
                try:
                    return float(m.group(1))
                except ValueError:
                    continue
        return default

    @classmethod
    def _parse_timing_paths(cls, content: str) -> List[TimingPath]:
        """Parse individual timing path sections from OpenSTA/OpenROAD reports."""
        paths: List[TimingPath] = []

        # Split report by path headers: "Startpoint: ..."
        sections = re.split(r'(?=(?:Startpoint:\s*))', content)

        for sec in sections:
            if not sec.startswith("Startpoint:"):
                continue

            sp_m = re.search(r'Startpoint:\s*([^\n]+)', sec)
            ep_m = re.search(r'Endpoint:\s*([^\n]+)', sec)
            pt_m = re.search(r'Path\s+Type:\s*(max|min|setup|hold)', sec, re.IGNORECASE)
            clk_m = re.search(r'Path\s+Group:\s*([^\n]+)', sec)

            if not (sp_m and ep_m):
                continue

            startpoint = sp_m.group(1).strip()
            endpoint = ep_m.group(1).strip()
            startpoint_clean = startpoint.split('(')[0].strip()
            endpoint_clean = endpoint.split('(')[0].strip()

            pt_val = pt_m.group(1).lower() if pt_m else "max"
            path_type = "setup" if pt_val in ("max", "setup") else "hold"

            # Slack extraction: take the final slack calculation line in the section
            slack_matches = list(re.finditer(r'([+-]?\d+\.?\d*)\s+slack\s+\((VIOLATED|MET)\)', sec, re.IGNORECASE))
            if slack_matches:
                slack_m = slack_matches[-1]
                slack_val = float(slack_m.group(1))
                is_violated = (slack_val < 0.0) or (slack_m.group(2).upper() == "VIOLATED")
            else:
                # Alternative slack format
                alt_matches = list(re.finditer(r'slack\s*[:=]?\s*([+-]?\d+\.?\d*)', sec, re.IGNORECASE))
                if not alt_matches:
                    continue
                slack_m = alt_matches[-1]
                slack_val = float(slack_m.group(1))
                is_violated = (slack_val < 0.0) or ("VIOLATED" in sec.upper())

            # Data arrival and required times
            arr_m = re.search(r'([+-]?\d+\.?\d*)\s+data\s+arrival\s+time', sec, re.IGNORECASE)
            req_m = re.search(r'([+-]?\d+\.?\d*)\s+data\s+required\s+time', sec, re.IGNORECASE)

            arr_time = float(arr_m.group(1)) if arr_m else 0.0
            req_time = float(req_m.group(1)) if req_m else 0.0

            # Extract intermediate signals
            crit_signals = re.findall(r'([a-zA-Z_0-9$]+/[a-zA-Z_0-9$]+)', sec)

            paths.append(TimingPath(
                startpoint=startpoint_clean,
                endpoint=endpoint_clean,
                path_type=path_type,
                clock=clk_m.group(1).strip() if clk_m else None,
                slack=round(slack_val, 3),
                arrival_time=arr_time,
                required_time=req_time,
                is_violated=is_violated,
                critical_signals=crit_signals[:6]
            ))

        return paths

    @classmethod
    def generate_recommendations(cls, report: TimingReport) -> List[str]:
        """Generate targeted RTL architectural fix recommendations based on violations."""
        recs: List[str] = []

        if report.is_clean:
            recs.append("All timing constraints met (WNS >= 0 ns). No structural RTL changes required.")
            return recs

        if report.has_setup_violation:
            recs.append(
                f"[SETUP VIOLATION] Worst Negative Slack: {report.wns_setup} ns | Total: {report.tns_setup} ns. "
                "Data path delay exceeds available clock period."
            )
            for i, p in enumerate(report.setup_paths[:3]):
                if p.is_violated:
                    recs.append(
                        f"  -> Path {i+1}: `{p.startpoint}` to `{p.endpoint}` (Slack: {p.slack} ns). "
                        "Recommendation: Pipeline long combinational datapath with intermediate flip-flop stage, "
                        "or split complex multi-operand arithmetic into two cycles."
                    )

        if report.has_hold_violation:
            recs.append(
                f"[HOLD VIOLATION] Worst Hold Slack: {report.wns_hold} ns | Total: {report.tns_hold} ns. "
                "Fast data path races capture clock edge."
            )
            for i, p in enumerate(report.hold_paths[:3]):
                if p.is_violated:
                    recs.append(
                        f"  -> Path {i+1}: `{p.startpoint}` to `{p.endpoint}` (Slack: {p.slack} ns). "
                        "Recommendation: Insert delay buffers on fast launch path or balance clock tree distribution."
                    )

        return recs

    @classmethod
    def generate_actionable_diffs(cls, report: TimingReport) -> List[str]:
        """Generate actionable Verilog code diff suggestions to fix timing paths."""
        diffs: List[str] = []

        if report.has_setup_violation:
            for p in report.setup_paths:
                if p.is_violated:
                    sp_short = p.startpoint.split('/')[-1]
                    ep_short = p.endpoint.split('/')[-1]
                    diff = f"""// --- Suggested Pipeline Stage for Critical Path: {sp_short} -> {ep_short} ---
// Before (Single Cycle Combinational):
- always @(posedge clk) begin
-     {ep_short} <= complex_combinational_logic({sp_short});
- end

// After (Two-Stage Pipelined):
+ reg [DATA_WIDTH-1:0] {sp_short}_stage1;
+ always @(posedge clk) begin
+     {sp_short}_stage1 <= partial_combinational_logic({sp_short});
+     {ep_short}        <= final_stage_logic({sp_short}_stage1);
+ end"""
                    diffs.append(diff)
                    break

        return diffs
