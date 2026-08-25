"""Automated cocotb testbench generator and LLM orchestrator."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional
from eda_agent.core import LLMBackedComponent
from eda_agent.schemas import ModuleSpec
from eda_agent.runners.simulation_runner import SimulationDiagnostics
from .llm_client import BaseLLMClient, get_llm_client
from .prompt_templates import (
    COCOTB_SYSTEM_PROMPT,
    TESTBENCH_GENERATION_PROMPT,
    TESTBENCH_REPAIR_PROMPT,
)


class TestbenchGenerator(LLMBackedComponent):
    """Orchestrates testbench synthesis and diagnostic-driven repair."""

    __test__ = False  # Prevent pytest from collecting this class as a test suite

    def __init__(self, llm_client: Optional[BaseLLMClient] = None):
        super().__init__(llm_client or get_llm_client())

    @staticmethod
    def extract_python_code(text: str) -> str:
        """Extract pure Python code from markdown code blocks or raw text."""
        # Find ```python ... ``` or ``` ... ``` handling arbitrary indentation
        match = re.search(r'```(?:python)?\s*\n([\s\S]*?)\n\s*```', text)
        if match:
            return match.group(1).strip()
        return text.strip()

    def format_ports_summary(self, spec: ModuleSpec) -> str:
        """Format port list into readable markdown string for prompt."""
        lines = []
        for p in spec.ports:
            dir_str = p.direction.value if hasattr(p.direction, "value") else str(p.direction)
            w_str = f"[{p.width}]" if p.width != "1" else "1-bit"
            domain_str = f" (clock domain: {p.clock_domain})" if p.clock_domain else ""
            lines.append(f"  - `{p.name}`: {dir_str} {p.port_type} {w_str}{domain_str}")
        return "\n".join(lines) if lines else "  - None"

    def build_generation_prompt(self, spec: ModuleSpec, source_code: Optional[str] = None) -> str:
        """Construct the prompt for generating a new testbench."""
        params_str = ", ".join(f"{p.name}={p.default_value or 'None'}" for p in spec.parameters) if spec.parameters else "None"
        clock_ports = ", ".join(p.name for p in spec.get_clock_ports()) or "None"
        reset_ports = ", ".join(p.name for p in spec.get_reset_ports()) or "None"
        fsm_states = ", ".join(f"{s.name}={s.value or 'auto'}" for s in spec.fsm_states) if spec.fsm_states else "None"

        return TESTBENCH_GENERATION_PROMPT.format(
            module_name=spec.name,
            parameters=params_str,
            ports_summary=self.format_ports_summary(spec),
            clock_ports=clock_ports,
            reset_ports=reset_ports,
            fsm_states=fsm_states,
            source_code=source_code or "// No raw source provided."
        )

    def build_repair_prompt(
        self,
        spec: ModuleSpec,
        broken_code: str,
        diagnostics: SimulationDiagnostics
    ) -> str:
        """Construct the prompt for fixing a failing testbench."""
        clock_ports = ", ".join(p.name for p in spec.get_clock_ports()) or "None"
        reset_ports = ", ".join(p.name for p in spec.get_reset_ports()) or "None"

        return TESTBENCH_REPAIR_PROMPT.format(
            module_name=spec.name,
            ports_summary=self.format_ports_summary(spec),
            clock_ports=clock_ports,
            reset_ports=reset_ports,
            broken_code=broken_code,
            failure_type=diagnostics.failure_type.value,
            error_summary=diagnostics.error_summary,
            failing_testcase=diagnostics.failing_testcase or "Unknown / All",
            stack_trace=diagnostics.stack_trace or diagnostics.raw_stderr or diagnostics.raw_stdout
        )

    def generate(self, spec: ModuleSpec, source_code: Optional[str] = None) -> str:
        """Generate a complete cocotb testbench for an RTL module."""
        prompt = self.build_generation_prompt(spec, source_code)
        raw_response = self.llm_client.generate(prompt, system_prompt=COCOTB_SYSTEM_PROMPT)
        return self.extract_python_code(raw_response)

    def repair(
        self,
        spec: ModuleSpec,
        broken_code: str,
        diagnostics: SimulationDiagnostics
    ) -> str:
        """Repair a failing cocotb testbench using diagnostics."""
        prompt = self.build_repair_prompt(spec, broken_code, diagnostics)
        raw_response = self.llm_client.generate(prompt, system_prompt=COCOTB_SYSTEM_PROMPT)
        return self.extract_python_code(raw_response)
