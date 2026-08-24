"""Configuration management for EDA-Agent using Pydantic Settings."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


CONFIG_DIR = Path.home() / ".eda-agent"
CONFIG_FILE = CONFIG_DIR / "config.json"


def is_local_endpoint(url: str) -> bool:
    """Verify if a URL points to a local or on-premises host (no external internet traffic)."""
    if not url:
        return True
    try:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()
        # Localhost and loopback addresses
        if hostname in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
            return True
        # Local subnets (10.x.x.x, 192.168.x.x, 172.16-31.x.x, .local, .internal)
        if (
            hostname.startswith("10.")
            or hostname.startswith("192.168.")
            or hostname.endswith(".local")
            or hostname.endswith(".internal")
            or hostname.endswith(".lan")
        ):
            return True
        if hostname.startswith("172."):
            parts = hostname.split(".")
            if len(parts) >= 2 and parts[1].isdigit():
                sec = int(parts[1])
                if 16 <= sec <= 31:
                    return True
        return False
    except Exception:
        return False


class EDAConfig(BaseSettings):
    """Global configuration settings for EDA-Agent and LLM providers."""

    provider: str = Field(
        default="ollama",
        description="LLM provider name: 'ollama', 'openai_compatible', 'vllm', 'gemini', 'openai', 'rule_based', 'local'"
    )
    base_url: str = Field(
        default="http://localhost:11434/v1",
        description="Base URL for LLM completion endpoint"
    )
    model: str = Field(
        default="deepseek-coder-v2:16b",
        description="Model name/tag (e.g. deepseek-coder-v2, qwen2.5-coder, codestral, gpt-4o)"
    )
    temperature: float = Field(
        default=0.2,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for code synthesis"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key for authenticated endpoints (optional for local Ollama/vLLM)"
    )
    timeout: int = Field(
        default=60,
        ge=1,
        description="HTTP request timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        ge=1,
        description="Maximum autonomous verification repair attempts"
    )

    model_config = SettingsConfigDict(
        env_prefix="EDA_LLM_",
        env_file=".env",
        extra="ignore"
    )

    @field_validator("provider")
    @classmethod
    def normalize_provider(cls, v: str) -> str:
        """Normalize provider string."""
        return v.lower().strip()

    def enforce_privacy(self) -> None:
        """Enforce strict airgap when configured for local/offline operation."""
        if self.provider in ("ollama", "local", "vllm", "offline"):
            if not is_local_endpoint(self.base_url):
                raise PermissionError(
                    f"Privacy Protection Error: Provider '{self.provider}' is configured with a non-local "
                    f"external endpoint '{self.base_url}'. Refusing to send proprietary RTL prompts."
                )


def get_config_path() -> Path:
    """Return path to persistent configuration file."""
    return CONFIG_FILE


def load_config() -> EDAConfig:
    """Load configuration from ~/.eda-agent/config.json with environment variable overrides."""
    file_data = {}
    config_file = get_config_path()

    if config_file.is_file():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                file_data = json.load(f)
        except Exception:
            file_data = {}

    # Pydantic BaseSettings will prioritize environment variables over file_data kwargs
    return EDAConfig(**file_data)


def save_config(config: EDAConfig, path: Optional[Path] = None) -> Path:
    """Persist configuration to JSON file."""
    save_path = path or get_config_path()
    save_path.parent.mkdir(parents=True, exist_ok=True)

    data = config.model_dump(exclude_none=False)
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return save_path


def update_config(**kwargs) -> EDAConfig:
    """Update settings and persist to configuration file."""
    current = load_config()
    current_dict = current.model_dump()

    # Filter out None values in kwargs
    filtered_updates = {k: v for k, v in kwargs.items() if v is not None}
    current_dict.update(filtered_updates)

    updated = EDAConfig(**current_dict)
    save_config(updated)
    return updated
