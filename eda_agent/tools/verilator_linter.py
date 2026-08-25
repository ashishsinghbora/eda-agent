"""Deterministic Verilator linter wrapper with structured JSON diagnostics."""

from __future__ import annotations

import json
import re
import tempfile
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from eda_agent.tools.base import BaseTool, ToolResult


class LintSeverity(str, Enum):
    """Diagnostic severity level."""
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class LintDiagnostic(BaseModel):
    """Structured diagnostic message extracted from Verilator or static lint."""
    file: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    severity: LintSeverity = LintSeverity.WARNING
    code: str = Field(default="LINT", description="Verilator error/warning code (e.g. WIDTH, BLKSEQ, UNDRIVEN)")
    message: str = Field(description="Human-readable diagnostic description")
    snippet: Optional[str] = None
    suggestion: Optional[str] = None


class LintReport(BaseModel):
    """Aggregated Verilator lint report."""
    success: bool
    verilator_available: bool = True
    total_errors: int = 0
    total_warnings: int = 0
    diagnostics: List[LintDiagnostic] = Field(default_factory=list)
    raw_output: str = ""
    command: List[str] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Export report as dictionary."""
        return self.model_dump()

    def to_json(self, indent: int = 2) -> str:
        """Export report as JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class VerilatorLinter(BaseTool):
    """Executes `verilator --lint-only -Wall` and returns structured JSON diagnostics."""

    @classmethod
    def is_available(cls) -> bool:
        """Return True if `verilator` binary is located on PATH."""
        return cls.find_binary("verilator") is not None

    @classmethod
    def lint_file(
        cls,
        file_path: str | Path,
        include_dirs: Optional[List[str | Path]] = None,
        top_module: Optional[str] = None,
        extra_args: Optional[List[str]] = None,
        timeout: int = 30,
    ) -> LintReport:
        """Run Verilator lint check on an RTL source file."""
        path = Path(file_path).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"RTL source file not found: {file_path}")

        binary = cls.find_binary("verilator")
        if not binary:
            # Fallback to static rule-based linter
            content = path.read_text(encoding="utf-8", errors="replace")
            return cls._static_lint_fallback(content, str(path))

        cmd = [
            binary,
            "--lint-only",
            "-Wall",
            "-Wno-DECLFILENAME",
            "--sv",
        ]

        if top_module:
            cmd.extend(["--top-module", top_module])

        if include_dirs:
            for inc in include_dirs:
                cmd.extend(["-I" + str(Path(inc).resolve())])

        if extra_args:
            cmd.extend(extra_args)

        cmd.append(str(path))

        result: ToolResult = cls.execute_command(
            cmd=cmd,
            cwd=path.parent,
            timeout=timeout,
        )

        combined_output = f"{result.stdout}\n{result.stderr}".strip()
        report = cls.parse_verilator_output(combined_output, default_file=str(path))
        report.command = cmd
        report.verilator_available = True
        return report

    @classmethod
    def lint_string(
        cls,
        code: str,
        module_name: str = "temp_module",
        top_module: Optional[str] = None,
        timeout: int = 30,
    ) -> LintReport:
        """Lint an in-memory SystemVerilog string by writing to a temporary file."""
        if not cls.is_available():
            return cls._static_lint_fallback(code, f"{module_name}.sv")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir) / f"{module_name}.sv"
            tmp_path.write_text(code, encoding="utf-8")
            return cls.lint_file(
                file_path=tmp_path,
                top_module=top_module or module_name,
                timeout=timeout,
            )

    @classmethod
    def parse_verilator_output(cls, raw_output: str, default_file: Optional[str] = None) -> LintReport:
        """Parse raw stdout/stderr from Verilator into structured LintDiagnostic objects."""
        diagnostics: List[LintDiagnostic] = []
        errors_count = 0
        warnings_count = 0

        # Pattern: %Error: path:line:col: message OR %Warning-CODE: path:line:col: message
        # Example: %Warning-WIDTHEXPAND: /path/to/alu.v:34:15: Operator ADD expects 8 bits on LHS...
        diag_re = re.compile(
            r'%(Error|Warning(?:-[A-Z0-9_]+)?):\s*(?:([^:\n]+):(\d+):(?:(\d+):)?)?\s*([^\n]+)',
            re.MULTILINE
        )

        lines = raw_output.splitlines()
        for i, line in enumerate(lines):
            match = diag_re.search(line)
            if not match:
                continue

            kind, file_match, line_num, col_num, msg = match.groups()
            
            # Determine severity
            if kind.startswith("Error"):
                sev = LintSeverity.ERROR
                code = "SYNTAX_ERROR"
                errors_count += 1
            else:
                sev = LintSeverity.WARNING
                code = kind.split("-", 1)[1] if "-" in kind else "WARNING"
                warnings_count += 1

            # Extract line/col
            line_idx = int(line_num) if line_num else None
            col_idx = int(col_num) if col_num else None
            file_str = file_match.strip() if file_match else default_file

            # Suggestion lookup based on Verilator code
            suggestion = cls._get_code_suggestion(code, msg)

            # Look ahead for snippet context lines (often marked with ... or |)
            snippet_lines = []
            for j in range(i + 1, min(i + 4, len(lines))):
                if lines[j].startswith("%"):
                    break
                snippet_lines.append(lines[j])
            snippet = "\n".join(snippet_lines).strip() if snippet_lines else None

            diagnostics.append(LintDiagnostic(
                file=file_str,
                line=line_idx,
                column=col_idx,
                severity=sev,
                code=code,
                message=msg.strip(),
                snippet=snippet,
                suggestion=suggestion,
            ))

        success = (errors_count == 0)
        return LintReport(
            success=success,
            verilator_available=True,
            total_errors=errors_count,
            total_warnings=warnings_count,
            diagnostics=diagnostics,
            raw_output=raw_output,
        )

    @classmethod
    def _get_code_suggestion(cls, code: str, msg: str) -> Optional[str]:
        """Provide actionable RTL fix suggestions for known Verilator warning codes."""
        code_upper = code.upper()
        if "WIDTH" in code_upper:
            return "Ensure operands on both sides of assignment/operator match identical bit width, or use explicit concatenation `{1'b0, val}`."
        elif "BLKSEQ" in code_upper:
            return "Use non-blocking assignment (`<=`) inside sequential clocked `always_ff` or `always @(posedge clk)` blocks."
        elif "COMBDLY" in code_upper:
            return "Use blocking assignment (`=`) inside combinational `always_comb` or `always @(*)` blocks."
        elif "UNDRIVEN" in code_upper:
            return "Signal has no driver. Assign an initial default value or connect it to an input/register."
        elif "UNUSED" in code_upper:
            return "Signal is declared but never read. Remove unused declaration or mark with `/* verilator lint_off UNUSED */`."
        elif "CASEINCOMPLETE" in code_upper:
            return "Add a `default:` branch to case statement to avoid unintended latch synthesis."
        elif "LATCH" in code_upper:
            return "Combinational block inferred a latch. Ensure all variables are assigned in every branch of `if/else` and `case`."
        elif "MULTIDRIVEN" in code_upper:
            return "Signal is driven by multiple concurrent always/assign blocks. Consolidate driver into a single block."
        return None

    @classmethod
    def _static_lint_fallback(cls, code: str, filename: str) -> LintReport:
        """Algorithmic static linter when Verilator binary is absent."""
        diagnostics: List[LintDiagnostic] = []
        errors_count = 0
        warnings_count = 0

        lines = code.splitlines()

        in_seq_always = False
        in_comb_always = False
        seq_paren_depth = 0

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            # Skip comments
            if stripped.startswith("//") or stripped.startswith("/*"):
                continue

            # Detect sequential block
            if re.search(r'\balways\s*@\s*\(\s*posedge|\balways_ff\b', line):
                in_seq_always = True
                in_comb_always = False

            # Detect combinational block
            elif re.search(r'\balways\s*@\s*\(\s*\*\s*\)|\balways_comb\b', line):
                in_comb_always = True
                in_seq_always = False

            # Check blocking assignment in sequential block
            if in_seq_always:
                # Match `foo = bar;` but not `<=`, `==`, `!=`, or `>=`
                if re.search(r'\b[a-zA-Z_][a-zA-Z0-9_$]*\s*=[^=><]', line) and "<=" not in line:
                    warnings_count += 1
                    diagnostics.append(LintDiagnostic(
                        file=filename,
                        line=idx,
                        severity=LintSeverity.WARNING,
                        code="BLKSEQ",
                        message="Blocking assignment '=' used inside sequential clocked always block.",
                        snippet=line.strip(),
                        suggestion="Replace blocking assignment (`=`) with non-blocking assignment (`<=`).",
                    ))

            # Check non-blocking assignment in combinational block
            if in_comb_always:
                if "<=" in line:
                    warnings_count += 1
                    diagnostics.append(LintDiagnostic(
                        file=filename,
                        line=idx,
                        severity=LintSeverity.WARNING,
                        code="COMBDLY",
                        message="Non-blocking assignment '<=' used inside combinational always block.",
                        snippet=line.strip(),
                        suggestion="Replace non-blocking assignment (`<=`) with blocking assignment (`=`).",
                    ))

            # Check case statement without default
            if re.search(r'\bcase\s*\(', line):
                # Check next 15 lines for default
                has_default = False
                for fwd in lines[idx:min(idx + 25, len(lines))]:
                    if "default:" in fwd or "default :" in fwd:
                        has_default = True
                        break
                    if "endcase" in fwd:
                        break
                if not has_default:
                    warnings_count += 1
                    diagnostics.append(LintDiagnostic(
                        file=filename,
                        line=idx,
                        severity=LintSeverity.WARNING,
                        code="CASEINCOMPLETE",
                        message="Case statement missing explicit 'default:' branch (may infer latch).",
                        snippet=line.strip(),
                        suggestion="Add a `default:` branch specifying safe fallback values.",
                    ))

        return LintReport(
            success=(errors_count == 0),
            verilator_available=False,
            total_errors=errors_count,
            total_warnings=warnings_count,
            diagnostics=diagnostics,
            raw_output="[Static RTL Linter - Verilator binary not installed locally]",
        )
