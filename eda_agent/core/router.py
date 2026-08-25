"""LLM model routing, provider abstraction, and airgap enforcement."""

from __future__ import annotations

import json
import logging
import os
import re
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from eda_agent.config import EDAConfig, is_local_endpoint, load_config
from eda_agent.generators.llm_client import (
    CloudProvider,
    GeminiProvider,
    LLMProvider,
    OllamaProvider,
    OpenAICompatibleProvider,
    RuleBasedLLMClient,
)

logger = logging.getLogger(__name__)


class AnthropicProvider(LLMProvider):
    """Cloud provider for Anthropic Claude models (e.g. claude-3-5-sonnet)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.2,
        timeout: int = 60,
        fallback_to_rule_based: bool = True,
    ):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.fallback_to_rule_based = fallback_to_rule_based

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Execute completion via Anthropic Messages API."""
        if not self.api_key:
            if self.fallback_to_rule_based:
                return RuleBasedLLMClient().generate(prompt, system_prompt)
            raise ValueError("ANTHROPIC_API_KEY environment variable is required to use AnthropicProvider.")

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

        payload: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": 4096,
            "temperature": self.temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            payload["system"] = system_prompt

        req = urllib.request.Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for block in data.get("content", []):
                    if block.get("type") == "text":
                        return block.get("text", "")
                return ""
        except Exception as e:
            if self.fallback_to_rule_based:
                logger.warning(f"Anthropic API call failed ({e}). Falling back to rule-based engine.")
                return RuleBasedLLMClient().generate(prompt, system_prompt)
            raise RuntimeError(f"Anthropic API call failed: {e}") from e


class ModelRouter:
    """Routes prompts to the configured local or cloud LLM provider."""

    def __init__(self, config: Optional[EDAConfig] = None):
        self.config = config or load_config()

    def get_provider(self, provider_override: Optional[str] = None) -> LLMProvider:
        """Instantiate the active LLM provider with airgap security checks."""
        prov = (provider_override or self.config.provider).lower().strip()
        self.config.enforce_privacy()

        if prov in ("ollama", "local"):
            return OllamaProvider(
                base_url=self.config.base_url,
                model=self.config.model,
                temperature=self.config.temperature,
                timeout=self.config.timeout,
            )
        elif prov in ("openai_compatible", "vllm", "lmstudio"):
            return OpenAICompatibleProvider(
                base_url=self.config.base_url,
                model=self.config.model,
                api_key=self.config.api_key,
                temperature=self.config.temperature,
                timeout=self.config.timeout,
            )
        elif prov in ("gemini", "google"):
            return GeminiProvider(
                api_key=self.config.api_key,
                model=self.config.model if "gemini" in self.config.model else "gemini-2.5-flash",
                temperature=self.config.temperature,
                timeout=self.config.timeout,
            )
        elif prov in ("anthropic", "claude"):
            return AnthropicProvider(
                api_key=self.config.api_key,
                model=self.config.model if "claude" in self.config.model else "claude-3-5-sonnet-20241022",
                temperature=self.config.temperature,
                timeout=self.config.timeout,
            )
        elif prov in ("openai", "cloud", "gpt-4", "gpt-4o"):
            return CloudProvider(
                api_key=self.config.api_key,
                model=self.config.model,
                temperature=self.config.temperature,
                timeout=self.config.timeout,
            )
        elif prov in ("rule_based", "offline", "builtin"):
            return RuleBasedLLMClient()
        else:
            return OllamaProvider(
                base_url=self.config.base_url,
                model=self.config.model,
                temperature=self.config.temperature,
                timeout=self.config.timeout,
            )
