"""EDA-Agent: Open-Source EDA Verification & Testbench Framework."""

from .config import (
    EDAConfig,
    is_local_endpoint,
    load_config,
    save_config,
    update_config,
)
from .generators.llm_client import (
    BaseLLMClient,
    CloudProvider,
    GeminiProvider,
    LLMProvider,
    OllamaProvider,
    OpenAICompatibleProvider,
    RuleBasedLLMClient,
    get_llm_client,
)
from .parsers.verilog_parser import RTLParser, VerilogParser
from .schemas import (
    FSMStateSpec,
    ModuleSpec,
    ParameterSpec,
    PortDirection,
    PortSpec,
    StateSpec,
)

__version__ = "0.1.0"

__all__ = [
    "EDAConfig",
    "load_config",
    "save_config",
    "update_config",
    "is_local_endpoint",
    "LLMProvider",
    "BaseLLMClient",
    "OllamaProvider",
    "OpenAICompatibleProvider",
    "GeminiProvider",
    "CloudProvider",
    "RuleBasedLLMClient",
    "get_llm_client",
    "ModuleSpec",
    "ParameterSpec",
    "PortDirection",
    "PortSpec",
    "StateSpec",
    "FSMStateSpec",
    "VerilogParser",
    "RTLParser",
    "__version__",
]
