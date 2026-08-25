"""Core agent execution loop, state machine, model routing, and abstract foundations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional


class FileProcessor(ABC):
    """Template base for components that consume files or text."""

    @classmethod
    def read_input_file(cls, file_path: str | Path, description: str) -> str:
        """Validate and read a UTF-8 input file for a concrete processor."""
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"{description} not found: {file_path}")
        return path.read_text(encoding="utf-8", errors="replace")

    @classmethod
    @abstractmethod
    def parse_string(cls, content: str) -> Any:
        """Parse in-memory content using the concrete processor."""


class XMLProcessor(ABC):
    """Template base for components that consume XML reports."""

    @classmethod
    @abstractmethod
    def parse_results_xml(cls, xml_path: str | Path) -> Any:
        """Parse a report from an XML file."""


class DiagnosticProcessor(ABC):
    """Polymorphic contract for translating raw tool diagnostics."""

    @classmethod
    @abstractmethod
    def translate(cls, raw_log: str, *args: Any, **kwargs: Any) -> Any:
        """Translate a raw diagnostic log into a domain diagnosis."""


class LLMBackedComponent(ABC):
    """Base for components that delegate synthesis to an injected LLM provider."""

    def __init__(self, llm_client: Optional[Any] = None) -> None:
        self._llm_client = llm_client

    @property
    def llm_client(self) -> Any:
        """Expose the configured provider without allowing accidental replacement."""
        return self._llm_client


# Import new core components
from .state_machine import AgentContext, AgentState, AgentStateMachine, StateTransition
from .router import ModelRouter, AnthropicProvider
from .agent_loop import AgentLoop, AgentLoopResult

__all__ = [
    "FileProcessor",
    "XMLProcessor",
    "DiagnosticProcessor",
    "LLMBackedComponent",
    "AgentState",
    "AgentContext",
    "AgentStateMachine",
    "StateTransition",
    "ModelRouter",
    "AnthropicProvider",
    "AgentLoop",
    "AgentLoopResult",
]
