"""Unit tests for agent loop, state machine, and model router."""

from pathlib import Path
from unittest.mock import patch
import io
import json
import pytest

from eda_agent.core.state_machine import AgentContext, AgentState, AgentStateMachine
from eda_agent.core.router import AnthropicProvider, ModelRouter
from eda_agent.core.agent_loop import AgentLoop, AgentLoopResult
from eda_agent.config import EDAConfig


def test_agent_state_machine_transitions():
    """Verify state transitions and history logging."""
    sm = AgentStateMachine()
    assert sm.current_state == AgentState.IDLE

    t1 = sm.transition_to(AgentState.PARSING, "Parsing module")
    assert sm.current_state == AgentState.PARSING
    assert t1.from_state == AgentState.IDLE
    assert t1.to_state == AgentState.PARSING

    sm.transition_to(AgentState.LINTING)
    sm.transition_to(AgentState.COMPLETED_SUCCESS)
    assert sm.is_finished() is True
    assert len(sm.context.transitions) == 3


def test_model_router_anthropic():
    """Verify Anthropic provider routing and API formatting."""
    cfg = EDAConfig(provider="anthropic", api_key="test-anthropic-key")
    router = ModelRouter(config=cfg)
    provider = router.get_provider()
    assert isinstance(provider, AnthropicProvider)

    mock_resp_data = {
        "content": [{"type": "text", "text": "```python\n# Anthropic synthesized test\n```"}]
    }
    mock_resp = io.BytesIO(json.dumps(mock_resp_data).encode("utf-8"))

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        res = provider.generate("Synthesize testbench", system_prompt="System instructions")
        assert "Anthropic synthesized test" in res
        req = mock_urlopen.call_args[0][0]
        assert req.headers["X-api-key"] == "test-anthropic-key"


def test_agent_loop_execution():
    """Verify end-to-end AgentLoop execution on ALU."""
    loop = AgentLoop()
    result = loop.run(
        rtl_file="examples/rtl/alu_8bit.v",
        sim_dir="examples/sim",
        run_linter=True,
        run_synth_check=True,
        clean=True,
    )
    assert isinstance(result, AgentLoopResult)
    assert result.success is True
    assert result.module_name == "alu_8bit"
    assert len(result.state_transitions) > 0
    assert result.final_sim_result.success is True
