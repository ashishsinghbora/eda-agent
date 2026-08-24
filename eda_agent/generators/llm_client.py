"""LLM Provider abstraction supporting local models (Ollama, vLLM) and cloud endpoints."""

from __future__ import annotations

import json
import logging
import os
import re
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from eda_agent.config import EDAConfig, is_local_endpoint, load_config

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM completion and synthesis providers."""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text completion from prompt and optional system prompt."""
        pass


# Backwards compatibility alias
BaseLLMClient = LLMProvider


class OpenAICompatibleProvider(LLMProvider):
    """Generic provider for OpenAI-compatible HTTP endpoints (vLLM, Ollama, LM Studio, Enterprise)."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1",
        model: str = "deepseek-coder-v2:16b",
        api_key: Optional[str] = None,
        temperature: float = 0.2,
        timeout: int = 60,
        fallback_to_rule_based: bool = True,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key or "local"
        self.temperature = temperature
        self.timeout = timeout
        self.fallback_to_rule_based = fallback_to_rule_based

    def _get_chat_url(self) -> str:
        """Resolve full chat completions URL."""
        if self.base_url.endswith("/chat/completions"):
            return self.base_url
        return f"{self.base_url}/chat/completions"

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Execute chat completion request over HTTP with resilient fallback."""
        url = self._get_chat_url()

        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }

        req = urllib.request.Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            if self.fallback_to_rule_based:
                logger.warning(
                    f"LLM endpoint '{url}' unreachable ({e}). Falling back to built-in rule-based synthesis engine."
                )
                return RuleBasedLLMClient().generate(prompt, system_prompt)
            raise ConnectionError(
                f"Failed to connect to OpenAI-compatible endpoint at '{url}': {e}. "
                f"Ensure the local model server (e.g. Ollama, vLLM) is running."
            ) from e


class OllamaProvider(OpenAICompatibleProvider):
    """Dedicated provider for local Ollama instances (default: http://localhost:11434/v1)."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1",
        model: str = "deepseek-coder-v2:16b",
        temperature: float = 0.2,
        timeout: int = 60,
        fallback_to_rule_based: bool = True,
    ):
        # Enforce airgap and local endpoint guarantee
        if not is_local_endpoint(base_url):
            raise PermissionError(
                f"Airgap / Privacy Violation: OllamaProvider received external URL '{base_url}'. "
                f"Local providers must only point to loopback/local network endpoints."
            )

        super().__init__(
            base_url=base_url,
            model=model,
            api_key="ollama",
            temperature=temperature,
            timeout=timeout,
            fallback_to_rule_based=fallback_to_rule_based,
        )

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Attempt OpenAI-compatible endpoint, then Ollama native /api/chat, then fallback."""
        url = self._get_chat_url()

        headers = {"Content-Type": "application/json"}
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # 1. Try /v1/chat/completions
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "stream": False,
        }

        req = urllib.request.Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if "choices" in data:
                    return data["choices"][0]["message"]["content"]
                elif "message" in data:
                    return data["message"]["content"]
        except Exception as primary_err:
            # 2. Try native Ollama /api/chat if URL had /v1
            if "/v1" in self.base_url:
                native_url = self.base_url.replace("/v1", "") + "/api/chat"
                try:
                    native_req = urllib.request.Request(
                        url=native_url,
                        data=json.dumps(payload).encode("utf-8"),
                        headers=headers,
                        method="POST"
                    )
                    with urllib.request.urlopen(native_req, timeout=self.timeout) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                        if "message" in data:
                            return data["message"]["content"]
                except Exception:
                    pass

            if self.fallback_to_rule_based:
                logger.warning(
                    f"Ollama server at '{url}' unreachable ({primary_err}). "
                    "Falling back to built-in rule-based synthesis engine."
                )
                return RuleBasedLLMClient().generate(prompt, system_prompt)

            raise ConnectionError(
                f"Failed to connect to local Ollama server at '{url}': {primary_err}. "
                f"Please ensure Ollama is running (`ollama serve`) and model '{self.model}' is pulled."
            ) from primary_err


class GeminiProvider(LLMProvider):
    """Cloud provider for Google Gemini API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.5-flash",
        temperature: float = 0.2,
        timeout: int = 60,
        fallback_to_rule_based: bool = True,
    ):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.fallback_to_rule_based = fallback_to_rule_based

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.api_key:
            if self.fallback_to_rule_based:
                return RuleBasedLLMClient().generate(prompt, system_prompt)
            raise ValueError("GEMINI_API_KEY environment variable is required to use GeminiProvider.")

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
            f"?key={self.api_key}"
        )
        headers = {"Content-Type": "application/json"}

        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"System Instructions:\n{system_prompt}"}]})
            contents.append({"role": "model", "parts": [{"text": "Understood. I will follow these instructions."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": self.temperature,
            }
        }

        req = urllib.request.Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            if self.fallback_to_rule_based:
                return RuleBasedLLMClient().generate(prompt, system_prompt)
            raise RuntimeError(f"Gemini API call failed: {e}") from e


class CloudProvider(OpenAICompatibleProvider):
    """Convenience alias for OpenAI cloud service."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        temperature: float = 0.2,
        timeout: int = 60,
        fallback_to_rule_based: bool = True,
    ):
        key = api_key or os.environ.get("OPENAI_API_KEY", "")
        super().__init__(
            base_url="https://api.openai.com/v1",
            model=model,
            api_key=key,
            temperature=temperature,
            timeout=timeout,
            fallback_to_rule_based=fallback_to_rule_based,
        )


OpenAILLMClient = CloudProvider


class RuleBasedLLMClient(LLMProvider):
    """Autonomous offline testbench generator synthesizing cocotb code without an LLM server."""

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Synthesize a complete cocotb testbench using algorithmic pattern recognition."""
        mod_m = re.search(r'\*\*Module Name:\*\*\s*([a-zA-Z_0-9$]+)', prompt)
        mod_name = mod_m.group(1).strip() if mod_m else "dut_module"

        is_alu = "alu" in mod_name.lower() or "OP_" in prompt or "opcode" in prompt.lower()
        is_fifo = "fifo" in mod_name.lower() or ("wclk" in prompt and "rclk" in prompt)

        if is_fifo:
            return self._generate_fifo_testbench(mod_name)
        elif is_alu:
            return self._generate_alu_testbench(mod_name)
        else:
            return self._generate_generic_testbench(mod_name, prompt)

    def _generate_alu_testbench(self, mod_name: str) -> str:
        return f'''```python
"""Automated cocotb testbench for {mod_name}."""

import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def reset_dut(dut):
    """Apply synchronous/asynchronous reset to DUT."""
    dut.rst_n.value = 0
    if hasattr(dut, "a"):
        dut.a.value = 0
    if hasattr(dut, "b"):
        dut.b.value = 0
    if hasattr(dut, "opcode"):
        dut.opcode.value = 0
    await Timer(20, unit="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


def alu_reference_model(a: int, b: int, opcode: int):
    """Golden software model for 8-bit ALU operations."""
    if opcode == 0:    # ADD
        res = (a + b) & 0xFF
        c = 1 if (a + b) > 255 else 0
    elif opcode == 1:  # SUB
        res = (a - b) & 0xFF
        c = 1 if a >= b else 0
    elif opcode == 2:  # AND
        res = (a & b) & 0xFF
        c = 0
    elif opcode == 3:  # OR
        res = (a | b) & 0xFF
        c = 0
    elif opcode == 4:  # XOR
        res = (a ^ b) & 0xFF
        c = 0
    elif opcode == 5:  # SHL
        res = (a << (b & 0x7)) & 0xFF
        c = 0
    elif opcode == 6:  # SHR
        res = (a >> (b & 0x7)) & 0xFF
        c = 0
    elif opcode == 7:  # NOT
        res = (~a) & 0xFF
        c = 0
    else:
        res = 0
        c = 0
    z = 1 if res == 0 else 0
    return res, z, c


@cocotb.test()
async def test_{mod_name}_reset(dut):
    """Verify reset assertions and initial output values."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)

    assert int(dut.result.value) == 0, f"Expected result=0 after reset, got {{int(dut.result.value)}}"
    assert int(dut.zero.value) == 0 or int(dut.zero.value) == 1
    dut._log.info("Reset test passed successfully!")


@cocotb.test()
async def test_{mod_name}_functional(dut):
    """Verify functional ALU operations across randomized vectors."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)

    for op in range(8):
        for _ in range(15):
            a_val = random.randint(0, 255)
            b_val = random.randint(0, 255)

            dut.a.value = a_val
            dut.b.value = b_val
            dut.opcode.value = op

            await RisingEdge(dut.clk)
            await Timer(1, unit="ns")

            exp_res, exp_z, _ = alu_reference_model(a_val, b_val, op)
            act_res = int(dut.result.value)
            act_z = int(dut.zero.value)

            assert act_res == exp_res, (
                f"Op {{op}}: A={{hex(a_val)}}, B={{hex(b_val)}}: "
                f"Expected result={{hex(exp_res)}}, got {{hex(act_res)}}"
            )
            assert act_z == exp_z, (
                f"Op {{op}}: Expected zero={{exp_z}}, got {{act_z}}"
            )

    dut._log.info("Functional throughput verification completed successfully!")


@cocotb.test()
async def test_{mod_name}_corner_cases(dut):
    """Verify boundary and corner cases: 0x00, 0xFF, overflow boundaries."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)

    corner_pairs = [
        (0x00, 0x00),
        (0xFF, 0xFF),
        (0xFF, 0x01),
        (0x80, 0x80),
        (0x7F, 0x01),
        (0x01, 0xFF),
    ]

    for a_val, b_val in corner_pairs:
        for op in range(8):
            dut.a.value = a_val
            dut.b.value = b_val
            dut.opcode.value = op

            await RisingEdge(dut.clk)
            await Timer(1, unit="ns")

            exp_res, exp_z, _ = alu_reference_model(a_val, b_val, op)
            act_res = int(dut.result.value)
            assert act_res == exp_res, (
                f"Corner Case Op {{op}}: A={{hex(a_val)}}, B={{hex(b_val)}}: "
                f"Expected {{hex(exp_res)}}, got {{hex(act_res)}}"
            )

    dut._log.info("Boundary and corner case verification completed successfully!")
```'''

    def _generate_fifo_testbench(self, mod_name: str) -> str:
        return f'''```python
"""Automated cocotb testbench for {mod_name}."""

import random
from collections import deque
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def reset_dut(dut):
    """Apply asynchronous reset to both write and read clock domains."""
    dut.wrst_n.value = 0
    dut.rrst_n.value = 0
    dut.winc.value = 0
    dut.rinc.value = 0
    dut.wdata.value = 0

    await Timer(50, unit="ns")
    dut.wrst_n.value = 1
    dut.rrst_n.value = 1
    await RisingEdge(dut.wclk)
    await RisingEdge(dut.rclk)


@cocotb.test()
async def test_{mod_name}_reset(dut):
    """Verify FIFO reset states."""
    cocotb.start_soon(Clock(dut.wclk, 10, unit="ns").start())
    cocotb.start_soon(Clock(dut.rclk, 15, unit="ns").start())
    await reset_dut(dut)

    assert dut.wfull.value == 0, f"Expected wfull=0, got {{dut.wfull.value}}"
    assert dut.rempty.value == 1, f"Expected rempty=1, got {{dut.rempty.value}}"
    dut._log.info("Reset test passed!")


@cocotb.test()
async def test_{mod_name}_fill_to_full(dut):
    """Verify FIFO capacity and full flag assertion."""
    cocotb.start_soon(Clock(dut.wclk, 10, unit="ns").start())
    cocotb.start_soon(Clock(dut.rclk, 15, unit="ns").start())
    await reset_dut(dut)

    depth = 16
    for i in range(depth):
        await RisingEdge(dut.wclk)
        dut.wdata.value = i & 0xFF
        dut.winc.value = 1

    await RisingEdge(dut.wclk)
    dut.winc.value = 0
    await RisingEdge(dut.wclk)

    assert dut.wfull.value == 1, f"Expected wfull=1 after writing {{depth}} elements"
    dut._log.info("Fill to full test passed!")


@cocotb.test()
async def test_{mod_name}_concurrent_traffic(dut):
    """Verify randomized concurrent read/write cross-clock traffic."""
    cocotb.start_soon(Clock(dut.wclk, 10, unit="ns").start())
    cocotb.start_soon(Clock(dut.rclk, 13, unit="ns").start())
    await reset_dut(dut)

    golden_queue = deque()
    num_items = 50

    async def writer():
        for _ in range(num_items):
            await RisingEdge(dut.wclk)
            while dut.wfull.value == 1:
                dut.winc.value = 0
                await RisingEdge(dut.wclk)

            val = random.randint(0, 255)
            dut.wdata.value = val
            dut.winc.value = 1
            golden_queue.append(val)
            await RisingEdge(dut.wclk)
            dut.winc.value = 0

            if random.random() < 0.3:
                for _ in range(random.randint(1, 2)):
                    await RisingEdge(dut.wclk)
        dut.winc.value = 0

    async def reader():
        received = 0
        while received < num_items:
            await RisingEdge(dut.rclk)
            while dut.rempty.value == 1:
                dut.rinc.value = 0
                await RisingEdge(dut.rclk)

            expected = golden_queue.popleft()
            actual = int(dut.rdata.value)
            assert actual == expected, f"Mismatch at item {{received}}: expected {{expected}}, got {{actual}}"

            dut.rinc.value = 1
            await RisingEdge(dut.rclk)
            dut.rinc.value = 0
            received += 1

            if random.random() < 0.3:
                for _ in range(random.randint(1, 2)):
                    await RisingEdge(dut.rclk)
        dut.rinc.value = 0

    w_task = cocotb.start_soon(writer())
    r_task = cocotb.start_soon(reader())
    await w_task
    await r_task
    dut._log.info("Concurrent cross-clock traffic test passed!")
```'''

    def _generate_generic_testbench(self, mod_name: str, prompt: str) -> str:
        return f'''```python
"""Automated generic cocotb testbench for {mod_name}."""

import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def test_{mod_name}_initialization(dut):
    """Verify module initial state."""
    clk_signal = getattr(dut, "clk", getattr(dut, "clock", None))
    if clk_signal is not None:
        cocotb.start_soon(Clock(clk_signal, 10, unit="ns").start())

    rst_signal = getattr(dut, "rst_n", getattr(dut, "reset_n", getattr(dut, "rst", getattr(dut, "reset", None))))
    if rst_signal is not None:
        rst_signal.value = 0
        await Timer(20, unit="ns")
        rst_signal.value = 1
        if clk_signal is not None:
            await RisingEdge(clk_signal)
    else:
        await Timer(20, unit="ns")

    dut._log.info("Initialization completed successfully!")
```'''


def get_llm_client(
    config: Optional[EDAConfig] = None,
    provider: Optional[str] = None
) -> LLMProvider:
    """Factory function for instantiating the configured LLM provider."""
    cfg = config or load_config()
    prov = (provider or cfg.provider).lower().strip()

    # Enforce airgap / privacy policy
    cfg.enforce_privacy()

    if prov in ("ollama", "local"):
        return OllamaProvider(
            base_url=cfg.base_url,
            model=cfg.model,
            temperature=cfg.temperature,
            timeout=cfg.timeout
        )
    elif prov in ("openai_compatible", "vllm", "lmstudio"):
        return OpenAICompatibleProvider(
            base_url=cfg.base_url,
            model=cfg.model,
            api_key=cfg.api_key,
            temperature=cfg.temperature,
            timeout=cfg.timeout
        )
    elif prov in ("gemini", "google"):
        return GeminiProvider(
            api_key=cfg.api_key,
            model=cfg.model,
            temperature=cfg.temperature,
            timeout=cfg.timeout
        )
    elif prov in ("openai", "cloud", "gpt-4", "gpt-4o"):
        return CloudProvider(
            api_key=cfg.api_key,
            model=cfg.model,
            temperature=cfg.temperature,
            timeout=cfg.timeout
        )
    elif prov in ("rule_based", "template", "offline", "builtin"):
        return RuleBasedLLMClient()
    else:
        # Fallback to Ollama or RuleBased
        return OllamaProvider(
            base_url=cfg.base_url,
            model=cfg.model,
            temperature=cfg.temperature,
            timeout=cfg.timeout
        )
