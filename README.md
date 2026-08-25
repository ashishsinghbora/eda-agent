# EDA-Agent 🚀

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Simulator: Icarus Verilog](https://img.shields.io/badge/simulator-Icarus%20Verilog-green.svg)](https://steveicarus.github.io/iverilog/)
[![Framework: cocotb](https://img.shields.io/badge/framework-cocotb%20v2.0%2B-orange.svg)](https://www.cocotb.org/)

**EDA-Agent** is an open-source, AI-powered Electronic Design Automation (EDA) verification and timing analysis framework. It automates RTL interface extraction, synthesizes exhaustive `cocotb` testbenches, runs hardware simulations with open-source simulators, diagnoses simulation and Static Timing Analysis (STA) failures, and performs closed-loop iterative repair.

---

## 🌟 Key Capabilities

1. **RTL Interface & Metadata Parser**
   - Extracts module definitions, ANSI / non-ANSI ports, parameters, bit widths, and registers.
   - Automatically detects clock signals (`clk`, `wclk`, `rclk`, etc.) and reset lines (`rst_n`, `wrst_n`, `aresetn`).
   - Infers multi-clock domain signal associations.
   - Parses FSM state encodings and opcodes from `localparam` and SystemVerilog `typedef enum` blocks.

2. **Autonomous `cocotb` Testbench Generator**
   - Synthesizes clean Python testbenches adhering to modern cocotb v2.0+ conventions.
   - Generates multi-tier test suites:
     - **Reset Verification**: Initial signal and register checks.
     - **Functional Throughput**: Randomized stimulus matched against software golden reference models.
     - **Corner Cases & Boundary Limits**: Full/empty flags, overflow conditions, extreme values.
   - Pluggable LLM interface supporting OpenAI / API providers and offline rule-based synthesis.

3. **Closed-Loop Simulation & Self-Repair Engine**
   - Executes simulations in isolated build sandboxes (`sim_build_<toplevel>`).
   - Automatically classifies failures into `ASSERTION_ERROR`, `TIMEOUT`, `SYNTAX_ERROR`, `COMPILATION_ERROR`, or `RUNTIME_ERROR`.
   - Feeds failure diagnostics and tracebacks back into the LLM loop to repair failing testbenches (up to configurable max retries).

4. **Static Timing Analysis (STA) Diagnostics & RTL Advisor**
   - Parses OpenROAD, OpenSTA, and Yosys timing logs.
   - Extracts Worst Negative Slack (WNS) and Total Negative Slack (TNS) for Setup and Hold paths.
   - Flags violating startpoints and endpoints.
   - Recommends architectural RTL fixes and generates actionable Verilog diff suggestions (e.g. pipelining long combinational paths).

---

## 🏗️ Directory Layout

```
.
├── pyproject.toml                     # Package specification & dependencies
├── README.md                          # Framework documentation
├── LICENSE                            # Apache-2.0 Open Source License
├── eda_agent/                         # Core framework
│   ├── __init__.py
│   ├── schemas.py                     # Pydantic metadata models (ModuleSpec, PortSpec, etc.)
│   ├── cli/
│   │   ├── __init__.py
│   │   └── main.py                    # Typer & Rich CLI
│   ├── parsers/
│   │   ├── __init__.py
│   │   └── verilog_parser.py          # Verilog AST & regex parser
│   ├── runners/
│   │   ├── __init__.py
│   │   └── simulation_runner.py       # Simulation execution & diagnostic engine
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── coverage_analyzer.py       # JUnit XML results analyzer
│   │   └── sta_analyzer.py            # OpenROAD/Yosys timing log parser & RTL advisor
│   └── generators/
│       ├── __init__.py
│       ├── prompt_templates.py        # System and repair prompt engineering
│       ├── llm_client.py              # LLM client abstractions (API & offline synthesis)
│       ├── testbench_generator.py     # Cocotb generator orchestrator
│       └── repair_loop.py             # Closed-loop autonomous verification loop
├── examples/
│   ├── rtl/
│   │   ├── fifo_async.v               # Asynchronous FIFO with Gray-code pointers
│   │   └── alu_8bit.v                 # 8-bit parameterizable ALU
│   ├── sim/
│   │   ├── Makefile                   # Cocotb simulator Makefile
│   │   ├── test_fifo_async.py         # FIFO testbench
│   │   └── test_alu_8bit.py           # ALU testbench
│   └── logs/
│       ├── openroad_sta_violated.log  # Sample OpenROAD timing log with violations
│       └── openroad_sta_clean.log     # Sample clean OpenROAD timing log
└── tests/                             # Unit and integration test suite
    ├── test_parser.py
    ├── test_generator.py
    ├── test_loop.py
    ├── test_runners.py
    ├── test_analyzers.py
    └── test_sta_analyzer.py
```

---

## 📦 Installation

### Prerequisites
- **Python 3.10+**
- **Icarus Verilog (`iverilog`)** and **`vvp`**

```bash
# Clone repository
git clone https://github.com/ashishsinghbora/eda-agent.git
cd eda-agent

# Set up Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode
pip install -e .
```

---

## 💻 CLI Usage

### 1. Local LLM & Provider Configuration
Configure local models (Ollama, vLLM) or cloud fallbacks without sending proprietary RTL over the internet:

```bash
# Configure local Ollama with DeepSeek Coder V2
eda-agent config --provider ollama --model deepseek-coder-v2:16b

# Configure local vLLM / OpenAI-compatible endpoint
eda-agent config --provider openai_compatible --base-url http://localhost:8000/v1 --model qwen2.5-coder:32b

# Display active configuration
eda-agent config
```

### 2. Autonomous Verification Loop
Synthesize an exhaustive testbench, run the simulation, diagnose failures, and iteratively self-repair:

```bash
# Run verification loop on 8-bit ALU
eda-agent verify examples/rtl/alu_8bit.v

# Run verification loop on Asynchronous FIFO with custom retry limit
eda-agent verify examples/rtl/fifo_async.v --max-retries 5
```

### 3. Natural Language Assertion Engine
Synthesize synthesizable SystemVerilog Assertions (SVA) and Cocotb assertion checkers from plain-English timing specifications:

```bash
# Generate SVA and cocotb assertions for FIFO ready signal
eda-agent assert examples/rtl/fifo_async.v --spec "ready drops low when valid is asserted and fifo is full"

# Generate multi-cycle protocol assertion
eda-agent assert examples/rtl/alu_8bit.v --spec "ack must assert 2 cycles after req rises"
```

### 4. Static Timing Analysis (STA) Diagnostics
Parse OpenROAD / Yosys timing reports, inspect critical paths, and generate actionable RTL diff suggestions:

```bash
# Analyze timing report with setup violations
eda-agent analyze-timing examples/logs/openroad_sta_violated.log

# Analyze timing clean report
eda-agent analyze-timing examples/logs/openroad_sta_clean.log
```

### 5. Parse RTL Interfaces & Display Metadata
```bash
eda-agent parse examples/rtl/fifo_async.v
eda-agent parse examples/rtl/alu_8bit.v
```

### 6. Run Cocotb Simulation Directly
```bash
eda-agent sim --dir examples/sim --toplevel fifo_async --module test_fifo_async --clean
```

### 7. Launch Interactive Web UI Studio & FastAPI Backend
Start the local web application with real-time waveform visualization, live streaming terminal, dual code editor, and interactive SVG hardware schematics:

```bash
# Launch Web UI on http://127.0.0.1:8000
eda-agent ui --port 8000
```
- **Interactive Web Studio**: `http://127.0.0.1:8000`
- **Interactive OpenAPI Docs**: `http://127.0.0.1:8000/docs`
- **Real-Time WebSocket Stream**: `ws://127.0.0.1:8000/ws/verify`

#### Web UI Architecture & Capabilities:
- **Left Panel**: Target RTL module explorer, local LLM selector (Ollama status badge), natural language specification prompt input, and 1-click action buttons (*Run Verification*, *Auto-Fix RTL Bug*, *Explain Failure in Simple Terms*, *Export Testbench*).
- **Center Panel**: Dual code editor view (Verilog RTL on the left, auto-generated Cocotb testbench and SVA assertions on the right).
- **Right Panel (Top)**: Interactive SVG hardware block diagram rendering input/output ports, bit widths, clock domains, and reset pins.
- **Bottom Panel**: Live simulation terminal streaming compiler outputs (`iverilog`), testcase execution, and an interactive digital waveform viewer powered by WaveDrom.

### 8. Check Environment & Toolchain
```bash
eda-agent info
```

---

## 🧪 Running Tests

Execute the complete test suite:

```bash
pytest -v
```

---

## 📄 License

This project is licensed under the [Apache-2.0 License](LICENSE).
