"""Hardware prompts, testbench generation templates, and assertion specifications."""

from __future__ import annotations

from .system_prompts import HARDWARE_SYSTEM_PROMPT, RTL_REPAIR_SYSTEM_PROMPT
from .testbench_prompts import (
    COCOTB_SYSTEM_PROMPT,
    TESTBENCH_GENERATION_PROMPT,
    TESTBENCH_REPAIR_PROMPT,
)
from .assertion_prompts import ASSERTION_SYNTHESIS_PROMPT

__all__ = [
    "HARDWARE_SYSTEM_PROMPT",
    "RTL_REPAIR_SYSTEM_PROMPT",
    "COCOTB_SYSTEM_PROMPT",
    "TESTBENCH_GENERATION_PROMPT",
    "TESTBENCH_REPAIR_PROMPT",
    "ASSERTION_SYNTHESIS_PROMPT",
]
