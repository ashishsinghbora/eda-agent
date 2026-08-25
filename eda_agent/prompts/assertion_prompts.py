"""Assertion synthesis and formal verification prompt templates."""

from __future__ import annotations

ASSERTION_SYNTHESIS_PROMPT = """Synthesize both a SystemVerilog Assertion (SVA) property and a cocotb (Python) asynchronous assertion checker coroutine for the following hardware requirement:

Hardware Specification: "{spec_text}"
Module Name: {module_name}
Clock Signal: {clock_name}
Reset Signal: {reset_name} (Active Low)

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
