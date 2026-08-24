"""Natural language timing specification to SystemVerilog Assertions (SVA) and Cocotb engine."""

from __future__ import annotations

import re
from typing import List, Optional
from pydantic import BaseModel, Field

from eda_agent.generators.llm_client import LLMProvider, get_llm_client
from eda_agent.schemas import ModuleSpec


class GeneratedAssertion(BaseModel):
    """Container for synthesized SVA and Cocotb assertion checkers."""
    spec_text: str = Field(description="Original natural language specification")
    property_name: str = Field(description="Generated property identifier")
    sva_code: str = Field(description="Synthesizable SystemVerilog Assertion (SVA) code")
    cocotb_code: str = Field(description="Executable Python cocotb coroutine assertion checker")
    signals_involved: List[str] = Field(default_factory=list, description="RTL signals referenced")
    clock_signal: str = Field(default="clk", description="Clock signal associated with assertion")
    reset_signal: str = Field(default="rst_n", description="Reset signal associated with assertion")


class AssertionGenerator:
    """Translates plain-English hardware specifications into SVA properties and cocotb checkers."""

    __test__ = False  # Prevent pytest collection

    def __init__(self, llm_client: Optional[LLMProvider] = None):
        self.llm_client = llm_client or get_llm_client()

    def generate(
        self,
        spec_text: str,
        module_spec: Optional[ModuleSpec] = None,
        clock_name: str = "clk",
        reset_name: str = "rst_n",
    ) -> GeneratedAssertion:
        """Generate SVA and cocotb assertions from a plain-English specification."""
        # Clean clock & reset names from module_spec if available
        if module_spec:
            clocks = [p.name for p in module_spec.ports if p.is_clock]
            resets = [p.name for p in module_spec.ports if p.is_reset]
            if clocks:
                clock_name = clocks[0]
            if resets:
                reset_name = resets[0]

        # Generate unique property name
        prop_name = self._make_property_name(spec_text)

        # Attempt rule-based synthesis first for deterministic high precision
        rule_result = self._rule_based_synthesis(
            spec_text=spec_text,
            prop_name=prop_name,
            clk=clock_name,
            rst=reset_name,
            module_spec=module_spec
        )
        if rule_result is not None:
            return rule_result

        # Fall back to LLM completion
        return self._llm_synthesis(
            spec_text=spec_text,
            prop_name=prop_name,
            clk=clock_name,
            rst=reset_name,
            module_spec=module_spec
        )

    def _make_property_name(self, spec_text: str) -> str:
        """Create a clean identifier for the property."""
        words = re.findall(r'[a-zA-Z0-9]+', spec_text.lower())
        short = "_".join(words[:4]) if words else "assertion_check"
        return f"p_{short}"

    def _rule_based_synthesis(
        self,
        spec_text: str,
        prop_name: str,
        clk: str,
        rst: str,
        module_spec: Optional[ModuleSpec] = None,
    ) -> Optional[GeneratedAssertion]:
        """Pattern-match common timing and protocol rules."""
        text = spec_text.lower().strip()
        signals: List[str] = []

        # Find known ports from module_spec if provided
        known_ports = [p.name for p in module_spec.ports] if module_spec else []
        for port in known_ports:
            if re.search(r'\b' + re.escape(port) + r'\b', text, re.IGNORECASE):
                signals.append(port)

        # 1. Pattern: "ready drops low when valid is asserted and fifo is full"
        # / "ready must be low when valid and full"
        if ("ready" in text or "wfull" in text or "rempty" in text) and ("when" in text or "if" in text):
            m_target = re.search(r'([a-zA-Z_0-9$]+)\s+(?:drops?\s+low|must\s+be\s+low|is\s+low|is\s+0)', text)
            target_sig = m_target.group(1) if m_target else ("ready" if "ready" in text else "winc")

            # Condition signals
            cond_sigs = []
            if "valid" in text:
                cond_sigs.append("valid")
            if "full" in text or "wfull" in text:
                cond_sigs.append("wfull" if "wfull" in known_ports else "fifo_full")
            if "empty" in text or "rempty" in text:
                cond_sigs.append("rempty" if "rempty" in known_ports else "fifo_empty")

            if not cond_sigs:
                cond_sigs = ["trigger_cond"]

            signals = list(set([target_sig] + cond_sigs + signals))
            cond_sva = " && ".join(cond_sigs)
            cond_py = " and ".join([f"int(dut.{s}.value)" for s in cond_sigs])

            sva = f"""// SVA: {spec_text}
property {prop_name};
  @(posedge {clk}) disable iff (!{rst})
    ({cond_sva}) |-> (!{target_sig});
endproperty
assert property ({prop_name}) else $error("Assertion {prop_name} violated: {target_sig} was not low when {cond_sva}");"""

            cocotb_coro = f'''async def check_{prop_name}(dut):
    """Cocotb checker: {spec_text}"""
    while True:
        await RisingEdge(dut.{clk})
        if int(dut.{rst}.value) == 1:
            if {cond_py}:
                assert int(dut.{target_sig}.value) == 0, (
                    f"Assertion {prop_name} failed: dut.{target_sig} is {{dut.{target_sig}.value}}, "
                    f"expected 0 when {cond_sva} is active"
                )'''

            return GeneratedAssertion(
                spec_text=spec_text,
                property_name=prop_name,
                sva_code=sva,
                cocotb_code=cocotb_coro,
                signals_involved=signals,
                clock_signal=clk,
                reset_signal=rst
            )

        # 2. Pattern: "ack must assert N cycles after req rises"
        m_delay = re.search(r'([a-zA-Z_0-9$]+)\s+must\s+assert\s+(\d+)\s+cycles?\s+after\s+([a-zA-Z_0-9$]+)\s+rises?', text)
        if m_delay:
            tgt = m_delay.group(1)
            cycles = int(m_delay.group(2))
            src = m_delay.group(3)
            signals = list(set([tgt, src, clk, rst]))

            sva = f"""// SVA: {spec_text}
property {prop_name};
  @(posedge {clk}) disable iff (!{rst})
    $rose({src}) |-> ##{cycles} {tgt};
endproperty
assert property ({prop_name}) else $error("Assertion {prop_name} violated: {tgt} did not assert {cycles} cycles after {src}");"""

            cocotb_coro = f'''async def check_{prop_name}(dut):
    """Cocotb checker: {spec_text}"""
    prev_{src} = 0
    while True:
        await RisingEdge(dut.{clk})
        if int(dut.{rst}.value) == 1:
            curr_{src} = int(dut.{src}.value)
            if prev_{src} == 0 and curr_{src} == 1:
                # $rose detected, await {cycles} cycles
                for _ in range({cycles}):
                    await RisingEdge(dut.{clk})
                assert int(dut.{tgt}.value) == 1, (
                    f"Assertion {prop_name} failed: dut.{tgt} is not asserted {cycles} cycles after {src} rose"
                )
            prev_{src} = curr_{src}'''

            return GeneratedAssertion(
                spec_text=spec_text,
                property_name=prop_name,
                sva_code=sva,
                cocotb_code=cocotb_coro,
                signals_involved=signals,
                clock_signal=clk,
                reset_signal=rst
            )

        # 3. Pattern: "one-hot" / "mutually exclusive"
        if "one-hot" in text or "onehot" in text or "mutually exclusive" in text:
            m_sig = re.search(r'([a-zA-Z_0-9$]+)\s+(?:is|must\s+be)\s+one-?hot', text)
            tgt = m_sig.group(1) if m_sig else (known_ports[0] if known_ports else "grant")
            signals = list(set([tgt, clk, rst]))

            sva = f"""// SVA: {spec_text}
property {prop_name};
  @(posedge {clk}) disable iff (!{rst})
    $onehot0({tgt});
endproperty
assert property ({prop_name}) else $error("Assertion {prop_name} violated: {tgt} is not one-hot encoded");"""

            cocotb_coro = f'''async def check_{prop_name}(dut):
    """Cocotb checker: {spec_text}"""
    while True:
        await RisingEdge(dut.{clk})
        if int(dut.{rst}.value) == 1:
            val = int(dut.{tgt}.value)
            # Check one-hot or zero
            is_onehot = (val & (val - 1) == 0)
            assert is_onehot, f"Assertion {prop_name} failed: {{hex(val)}} is not one-hot encoded"'''

            return GeneratedAssertion(
                spec_text=spec_text,
                property_name=prop_name,
                sva_code=sva,
                cocotb_code=cocotb_coro,
                signals_involved=signals,
                clock_signal=clk,
                reset_signal=rst
            )

        return None

    def _llm_synthesis(
        self,
        spec_text: str,
        prop_name: str,
        clk: str,
        rst: str,
        module_spec: Optional[ModuleSpec] = None,
    ) -> GeneratedAssertion:
        """Synthesize SVA and cocotb assertions using LLM."""
        prompt = f"""Synthesize both a SystemVerilog Assertion (SVA) property and a cocotb (Python) asynchronous assertion checker coroutine for the following hardware requirement:

Hardware Specification: "{spec_text}"
Module Name: {module_spec.name if module_spec else "DUT"}
Clock Signal: {clk}
Reset Signal: {rst} (Active Low)

Format your output strictly as:
```systemverilog
// SVA Property
...
```

```python
# Cocotb Checker Coroutine
...
```
"""
        response = self.llm_client.generate(prompt)

        # Extract SVA
        sva_m = re.search(r'```(?:systemverilog|verilog|sva)?\s*\n([\s\S]*?)\n```', response, re.IGNORECASE)
        sva_code = sva_m.group(1).strip() if sva_m else f"// SVA for {spec_text}\nassert property (@(posedge {clk}) disable iff (!{rst}) {spec_text});"

        # Extract Cocotb
        py_m = re.search(r'```(?:python|py)?\s*\n([\s\S]*?)\n```', response, re.IGNORECASE)
        cocotb_code = py_m.group(1).strip() if py_m else f"""async def check_{prop_name}(dut):
    while True:
        await RisingEdge(dut.{clk})
        # Check: {spec_text}"""

        return GeneratedAssertion(
            spec_text=spec_text,
            property_name=prop_name,
            sva_code=sva_code,
            cocotb_code=cocotb_code,
            signals_involved=[clk, rst],
            clock_signal=clk,
            reset_signal=rst
        )
