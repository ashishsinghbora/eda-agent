"""Unit tests for LLM providers, configuration manager, and local airgap guarantees."""

import io
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from eda_agent.config import (
    EDAConfig,
    is_local_endpoint,
    load_config,
    save_config,
    update_config,
)
from eda_agent.generators.llm_client import (
    BaseLLMClient,
    CloudProvider,
    GeminiProvider,
    LLMProvider,
    OllamaProvider,
    OpenAICompatibleProvider,
    RuleBasedLLMClient,
    get_llm_client,
)


def test_is_local_endpoint():
    """Verify classification of local/loopback vs external endpoints."""
    # Local endpoints
    assert is_local_endpoint("http://localhost:11434/v1") is True
    assert is_local_endpoint("http://127.0.0.1:8000/v1") is True
    assert is_local_endpoint("http://0.0.0.0:11434") is True
    assert is_local_endpoint("http://192.168.1.100:8080/v1") is True
    assert is_local_endpoint("http://10.0.0.5:11434") is True
    assert is_local_endpoint("http://my-gpu-server.local:8000") is True
    assert is_local_endpoint("http://server.lan:11434/v1") is True
    assert is_local_endpoint("http://cluster.internal:8000") is True

    # External endpoints
    assert is_local_endpoint("https://api.openai.com/v1") is False
    assert is_local_endpoint("https://generativelanguage.googleapis.com") is False
    assert is_local_endpoint("https://public-api.cloud.com/v1") is False


def test_privacy_enforcement():
    """Verify that local providers prevent sending data to external endpoints."""
    # Ollama with local URL is permitted
    ollama_local = OllamaProvider(base_url="http://localhost:11434/v1", model="deepseek-coder-v2")
    assert ollama_local.base_url == "http://localhost:11434/v1"

    # Ollama with external URL must raise PermissionError
    with pytest.raises(PermissionError, match="Airgap / Privacy Violation"):
        OllamaProvider(base_url="https://external-leak.com/v1")

    # EDAConfig privacy enforcement
    cfg_leak = EDAConfig(provider="ollama", base_url="https://api.external.com/v1")
    with pytest.raises(PermissionError, match="Privacy Protection Error"):
        cfg_leak.enforce_privacy()


def test_config_persistence(tmp_path: Path):
    """Verify saving, loading, and updating configuration from JSON."""
    test_config_file = tmp_path / "config.json"

    cfg = EDAConfig(
        provider="ollama",
        model="deepseek-coder-v2:16b",
        base_url="http://localhost:11434/v1",
        temperature=0.15
    )

    saved_path = save_config(cfg, path=test_config_file)
    assert saved_path.is_file()

    with patch("eda_agent.config.get_config_path", return_value=test_config_file):
        loaded = load_config()
        assert loaded.provider == "ollama"
        assert loaded.model == "deepseek-coder-v2:16b"
        assert loaded.temperature == 0.15


def test_ollama_provider_mock_response():
    """Verify OllamaProvider HTTP payload construction and response parsing with mocks."""
    provider = OllamaProvider(
        base_url="http://localhost:11434/v1",
        model="deepseek-coder-v2:16b",
        temperature=0.2
    )

    mock_response_data = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "```python\n# Synthesized cocotb test\nimport cocotb\n```"
                }
            }
        ]
    }

    mock_resp = io.BytesIO(json.dumps(mock_response_data).encode("utf-8"))

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        result = provider.generate(
            prompt="Generate ALU testbench",
            system_prompt="You are an expert EDA assistant."
        )

        assert "import cocotb" in result
        assert mock_urlopen.called

        # Inspect the HTTP Request object passed to urlopen
        req = mock_urlopen.call_args[0][0]
        assert req.full_url == "http://localhost:11434/v1/chat/completions"
        assert req.headers["Content-type"] == "application/json"

        body = json.loads(req.data.decode("utf-8"))
        assert body["model"] == "deepseek-coder-v2:16b"
        assert body["temperature"] == 0.2
        assert len(body["messages"]) == 2
        assert body["messages"][0]["role"] == "system"
        assert body["messages"][1]["content"] == "Generate ALU testbench"


def test_openai_compatible_provider_mock():
    """Verify OpenAICompatibleProvider with custom auth and endpoint."""
    provider = OpenAICompatibleProvider(
        base_url="http://localhost:8000/v1",
        model="qwen2.5-coder:32b",
        api_key="custom-secret-token",
        temperature=0.1
    )

    mock_response_data = {
        "choices": [{"message": {"content": "```python\nimport cocotb\n```"}}]
    }
    mock_resp = io.BytesIO(json.dumps(mock_response_data).encode("utf-8"))

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        result = provider.generate("Test prompt")
        assert "import cocotb" in result
        req = mock_urlopen.call_args[0][0]
        assert req.headers["Authorization"] == "Bearer custom-secret-token"
        assert req.full_url == "http://localhost:8000/v1/chat/completions"


def test_gemini_provider_mock():
    """Verify GeminiProvider payload and response format."""
    provider = GeminiProvider(api_key="mock-gemini-key", model="gemini-2.5-flash")

    mock_gemini_resp = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "```python\n# Gemini cocotb test\n```"}]
                }
            }
        ]
    }
    mock_resp = io.BytesIO(json.dumps(mock_gemini_resp).encode("utf-8"))

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        result = provider.generate("Test prompt", system_prompt="EDA Instructions")
        assert "Gemini cocotb test" in result
        req = mock_urlopen.call_args[0][0]
        assert "key=mock-gemini-key" in req.full_url


def test_get_llm_client_factory():
    """Verify factory instantiation across providers."""
    # Ollama
    cfg_ollama = EDAConfig(provider="ollama", base_url="http://localhost:11434/v1")
    client_ollama = get_llm_client(config=cfg_ollama)
    assert isinstance(client_ollama, OllamaProvider)

    # vLLM / OpenAI Compatible
    cfg_vllm = EDAConfig(provider="vllm", base_url="http://localhost:8000/v1")
    client_vllm = get_llm_client(config=cfg_vllm)
    assert isinstance(client_vllm, OpenAICompatibleProvider)

    # Gemini
    cfg_gemini = EDAConfig(provider="gemini", api_key="test-key")
    client_gemini = get_llm_client(config=cfg_gemini)
    assert isinstance(client_gemini, GeminiProvider)

    # Rule based offline
    cfg_rule = EDAConfig(provider="rule_based")
    client_rule = get_llm_client(config=cfg_rule)
    assert isinstance(client_rule, RuleBasedLLMClient)
