"""State machine for tracking autonomous EDA agent verification cycles."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from eda_agent.schemas import ModuleSpec


class AgentState(str, Enum):
    """Lifecycle states of the autonomous EDA agent."""
    IDLE = "IDLE"
    PARSING = "PARSING"
    LINTING = "LINTING"
    SYNTHESIS_CHECK = "SYNTHESIS_CHECK"
    TESTBENCH_GENERATION = "TESTBENCH_GENERATION"
    SIMULATING = "SIMULATING"
    TRIAGING = "TRIAGING"
    REPAIRING = "REPAIRING"
    COMPLETED_SUCCESS = "COMPLETED_SUCCESS"
    COMPLETED_FAILURE = "COMPLETED_FAILURE"


class StateTransition(BaseModel):
    """Record of a state transition."""
    from_state: AgentState
    to_state: AgentState
    timestamp: float
    message: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentContext(BaseModel):
    """Execution context and artifact state tracked across agent iterations."""
    current_state: AgentState = AgentState.IDLE
    rtl_file: Optional[str] = None
    target_module: Optional[str] = None
    module_spec: Optional[ModuleSpec] = None
    source_code: str = ""
    testbench_code: str = ""
    iteration: int = 0
    max_retries: int = 3
    transitions: List[StateTransition] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class AgentStateMachine:
    """State machine controller governing verification workflow transitions."""

    def __init__(self, context: Optional[AgentContext] = None):
        self.context = context or AgentContext()

    @property
    def current_state(self) -> AgentState:
        return self.context.current_state

    def transition_to(self, new_state: AgentState, message: str = "", **metadata: Any) -> StateTransition:
        """Execute a state transition and log transition record."""
        import time
        transition = StateTransition(
            from_state=self.context.current_state,
            to_state=new_state,
            timestamp=time.time(),
            message=message,
            metadata=metadata,
        )
        self.context.transitions.append(transition)
        self.context.current_state = new_state
        return transition

    def is_finished(self) -> bool:
        """Return True if agent has reached a terminal completion state."""
        return self.context.current_state in (AgentState.COMPLETED_SUCCESS, AgentState.COMPLETED_FAILURE)
