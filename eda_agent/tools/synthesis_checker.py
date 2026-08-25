"""Yosys gate-level synthesizability checker and cell statistic analyzer."""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from eda_agent.tools.base import BaseTool, ToolResult


class SynthesisDiagnostic(BaseModel):
    """Diagnostic detail parsed from Yosys output."""
    severity: str = "ERROR"
    message: str
    line: Optional[int] = None
    code: Optional[str] = None


class SynthesisReport(BaseModel):
    """Aggregated report of Yosys synthesizability check."""
    success: bool
    top_module: str
    yosys_available: bool = True
    cell_count: int = 0
    gate_count: int = 0
    dff_count: int = 0
    latch_count: int = 0
    wire_count: int = 0
    cells_by_type: Dict[str, int] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    non_synthesizable_constructs: List[str] = Field(default_factory=list)
    raw_log: str = ""
    command: List[str] = Field(default_factory=list)

    @property
    def has_latches(self) -> bool:
        """Return True if combinational latches were inferred."""
        return self.latch_count > 0

    def to_dict(self) -> Dict[str, Any]:
        """Export report as dictionary."""
        return self.model_dump()

    def to_json(self, indent: int = 2) -> str:
        """Export report as JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class SynthesisChecker(BaseTool):
    """Runs Yosys gate-level synthesizability and design rule checks."""

    @classmethod
    def is_available(cls) -> bool:
        """Return True if `yosys` binary is installed on PATH."""
        return cls.find_binary("yosys") is not None

    @classmethod
    def check_file(
        cls,
        file_path: str | Path,
        top_module: Optional[str] = None,
        timeout: int = 60,
    ) -> SynthesisReport:
        """Run Yosys synthesis check on an RTL source file."""
        path = Path(file_path).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"RTL file not found: {file_path}")

        binary = cls.find_binary("yosys")
        if not binary:
            content = path.read_text(encoding="utf-8", errors="replace")
            return cls._static_synthesis_fallback(content, top_module or path.stem)

        resolved_top = top_module or path.stem

        # Yosys synthesis script: read, check hierarchy, elaborate, optimize, and report stats
        yosys_script = (
            f"read_verilog -sv {path.name}; "
            f"hierarchy -check -top {resolved_top}; "
            f"proc; opt; fsm; opt; memory; opt; techmap; opt; check; stat"
        )

        cmd = [binary, "-q", "-p", yosys_script]

        result: ToolResult = cls.execute_command(
            cmd=cmd,
            cwd=path.parent,
            timeout=timeout,
        )

        combined = f"{result.stdout}\n{result.stderr}".strip()
        report = cls.parse_yosys_output(combined, resolved_top)
        report.command = cmd
        report.yosys_available = True
        return report

    @classmethod
    def check_string(
        cls,
        code: str,
        module_name: str = "top",
        timeout: int = 60,
    ) -> SynthesisReport:
        """Run Yosys synthesis check on in-memory RTL string."""
        if not cls.is_available():
            return cls._static_synthesis_fallback(code, module_name)

        with tempfile.TemporaryDirectory() as tmpdir:
            rtl_path = Path(tmpdir) / f"{module_name}.sv"
            rtl_path.write_text(code, encoding="utf-8")
            return cls.check_file(
                file_path=rtl_path,
                top_module=module_name,
                timeout=timeout,
            )

    @classmethod
    def parse_yosys_output(cls, log: str, top_module: str) -> SynthesisReport:
        """Extract synthesis statistics, latch counts, and errors from Yosys log."""
        errors: List[str] = []
        warnings: List[str] = []
        non_synth: List[str] = []
        cells_by_type: Dict[str, int] = {}

        total_cells = 0
        total_dffs = 0
        total_latches = 0
        total_wires = 0

        lines = log.splitlines()
        in_stat = False

        for line in lines:
            # Errors
            if "ERROR:" in line or "syntax error" in line.lower() or "error:" in line.lower():
                errors.append(line.strip())

            # Warnings
            elif "Warning:" in line or "WARNING:" in line:
                warnings.append(line.strip())
                if "latch" in line.lower():
                    non_synth.append(f"Inferred Latch Warning: {line.strip()}")

            # Non-synthesizable constructs detected
            if "delay" in line.lower() and "ignored" in line.lower():
                non_synth.append("Timing delay controls (#delay) ignored during synthesis.")
            if "initial" in line.lower() and "ignored" in line.lower():
                non_synth.append("Initial block initialization ignored in synthesis.")

            # Stat section parsing
            if "=== " in line:
                in_stat = True

            if in_stat or "Number of cells:" in line or "Number of wires:" in line:
                m_wire = re.search(r'Number of wires:\s*(\d+)', line)
                if m_wire:
                    total_wires = int(m_wire.group(1))

                m_cells = re.search(r'Number of cells:\s*(\d+)', line)
                if m_cells:
                    total_cells = int(m_cells.group(1))

                # Individual cell matches e.g. `$_DFF_P_ 11` or `$_DLATCH_P_ 2`
                m_cell_entry = re.search(r'^\s*(\$_[A-Z0-9_]+|[A-Za-z0-9_]+)\s+(\d+)$', line)
                if m_cell_entry:
                    cell_name = m_cell_entry.group(1)
                    count = int(m_cell_entry.group(2))
                    cells_by_type[cell_name] = count

                    if "DFF" in cell_name.upper():
                        total_dffs += count
                    elif "LATCH" in cell_name.upper():
                        total_latches += count

        # Check for inferred latches in cell types
        for cname, cnt in cells_by_type.items():
            if "LATCH" in cname.upper():
                total_latches += cnt
                non_synth.append(f"Inferred {cnt} latches of cell type `{cname}`.")

        success = (len(errors) == 0) and total_cells > 0

        return SynthesisReport(
            success=success,
            top_module=top_module,
            yosys_available=True,
            cell_count=total_cells,
            gate_count=max(0, total_cells - total_dffs - total_latches),
            dff_count=total_dffs,
            latch_count=total_latches,
            wire_count=total_wires,
            cells_by_type=cells_by_type,
            errors=errors,
            warnings=warnings,
            non_synthesizable_constructs=non_synth,
            raw_log=log,
        )

    @classmethod
    def _static_synthesis_fallback(cls, code: str, top_module: str) -> SynthesisReport:
        """Static synthesizability checker when Yosys binary is not installed."""
        errors: List[str] = []
        warnings: List[str] = []
        non_synth: List[str] = []

        # 1. Check for `#delay`
        if re.search(r'#\s*\d+', code):
            non_synth.append("Delay controls (`#<n>`) are non-synthesizable in RTL.")

        # 2. Check for `initial` block
        if re.search(r'\binitial\b', code):
            warnings.append("`initial` block detected. ASIC synthesis requires explicit reset signals.")

        # 3. Check for `real` data types
        if re.search(r'\breal\b', code):
            errors.append("Floating-point `real` type is non-synthesizable.")

        # 4. Check for `fork ... join`
        if re.search(r'\bfork\b', code) and re.search(r'\bjoin\b', code):
            errors.append("Dynamic thread `fork/join` is non-synthesizable in RTL.")

        # Estimate flip-flops and comb logic
        dff_count = len(re.findall(r'@\s*\(\s*posedge', code)) * 8
        wire_count = len(re.findall(r'\bwire\b|\blogic\b|\breg\b', code))

        return SynthesisReport(
            success=(len(errors) == 0),
            top_module=top_module,
            yosys_available=False,
            cell_count=max(10, dff_count + wire_count),
            gate_count=max(5, wire_count),
            dff_count=dff_count,
            latch_count=0,
            wire_count=wire_count,
            errors=errors,
            warnings=warnings,
            non_synthesizable_constructs=non_synth,
            raw_log="[Static Synthesis Check - Yosys binary not installed locally]",
        )
