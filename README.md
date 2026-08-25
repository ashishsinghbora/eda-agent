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
- **GNU Make**
- **Icarus Verilog (`iverilog`)** and **`vvp`**
- **Git Bash** on Windows. Cocotb's Makefiles use Unix shell utilities such as `sh`, `tr`, and `uname`.

The application can discover a repository-local toolchain under `.tools/iverilog/bin` and `.tools/make/bin`. This is useful on Windows when machine-wide installation requires administrator access. If no local tools are present, install GNU Make and Icarus Verilog through your operating system package manager and ensure both `iverilog` and `vvp` are on `PATH`.

```bash
# Clone repository
git clone https://github.com/ashishsinghbora/eda-agent.git
cd eda-agent

# Set up Python virtual environment (Linux/macOS)
python3 -m venv .venv
source .venv/bin/activate

# Windows PowerShell equivalent
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install in editable mode
pip install -e .
```

### Windows: repository-local simulator setup

If you cannot install packages globally, unpack the 64-bit Icarus archive into `.tools/iverilog` so that these files exist:

```text
.tools/iverilog/bin/iverilog.exe
.tools/iverilog/bin/vvp.exe
```

This workspace includes the archive used for that setup under `hoco/ChocolateyScratch/iverilog/11.0.0/tools/_archives`. From the repository root, PowerShell can extract it with:

```powershell
New-Item -ItemType Directory -Force .tools/iverilog | Out-Null
Expand-Archive `
   -Path hoco/ChocolateyScratch/iverilog/11.0.0/tools/_archives/iverilog-mingw32-w64-x86_64-11.0.zip `
   -DestinationPath .tools/iverilog -Force
```

The GNU Make archive is not part of the Icarus package. Download or install a real GNU Make binary and place `make.exe` at `.tools/make/bin/make.exe`, or install it system-wide.

The repository's simulation runner automatically adds this directory to the subprocess `PATH`. It also looks for `.tools/make/bin/make.exe`, then a system `make`, and finally the virtual-environment fallback. A real GNU Make executable is required for the Cocotb Makefile; `pymake` is not compatible with Cocotb's conditional Makefile syntax.

For a normal Windows installation, install GNU Make and Icarus Verilog with an elevated package-manager shell, then open a new terminal so the updated `PATH` is visible:

```powershell
choco install iverilog make -y
```

Git Bash is normally installed with Git for Windows. The runner uses `C:\Program Files\Git\usr\bin\sh.exe` when it is available.

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

The simulation runner sets `SIM`, `TOPLEVEL`, `MODULE`, `SIM_BUILD`, and `WAVES` for the example Makefile. Build artifacts and Cocotb reports are written below `examples/sim/sim_build_<toplevel>`.

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

#### Web UI workflow

1. Select `alu_8bit.v` or `fifo_async.v`, or choose **Custom RTL Buffer** and edit the RTL editor.
2. Enter a natural-language requirement or select a preset prompt. The **Synthesize TB** button calls `POST /api/generate-test` and updates the testbench editor.
3. Use the **testbench.py** and **SVA Assertions** tabs to switch between generated Cocotb code and generated SVA/checker code. SVA is generated when a specification is supplied.
4. Click **Refresh Diagram** after changing RTL. The UI calls `POST /api/parse` and redraws the module ports and schematic.
5. Click **Run Verification** to open `/ws/verify`. The server runs the generate, simulate, diagnose, and repair loop, streams iteration records, and displays any WaveDrom data produced by the simulation.
6. **Auto-Fix RTL Bug** starts the same closed-loop verification flow and labels the terminal output as a repair run.
7. **Explain Failure in Simple Terms** sends the latest simulator output and RTL to `POST /api/diagnose`, then displays the engineering summary, hardware diagnosis, and raw error.
8. **Analyze Static Timing (STA)** sends the latest available log to `POST /api/timing` and displays WNS, TNS, timing status, and recommendations. It requires an OpenSTA/Yosys-style timing log; ordinary simulator output may parse as a clean report with zero metrics.
9. **Refresh Wave** displays the latest captured waveform. If no simulation waveform exists yet, it displays the built-in sample waveform as a visual placeholder.
10. The provider selector persists the selected provider through `POST /api/config/provider`. It changes the configured inference backend; it does not install or start Ollama, vLLM, Gemini, or OpenAI services.
11. **Export Testbench** downloads the generated Cocotb testbench as `test_<module>.py`.

#### Backend endpoints

| Endpoint | Purpose |
|---|---|
| `GET /api/status` | Python, simulator, and LLM configuration status |
| `GET /api/examples` | Bundled RTL examples and specification presets |
| `POST /api/parse` | Parse RTL and return module metadata |
| `POST /api/generate-test` | Generate a Cocotb testbench and optional SVA checker |
| `POST /api/diagnose` | Translate simulator failures into hardware diagnostics |
| `POST /api/timing` | Parse OpenSTA/Yosys timing reports |
| `POST /api/config/provider` | Persist the selected LLM provider |
| `WS /ws/verify` | Stream verification and repair-loop events |

### Verification troubleshooting

The UI checks `/api/status` on startup. If either `iverilog` or `vvp` is missing, it intentionally shows **Simulator unavailable** and disables the verification workflow. This is a prerequisite warning, not a WebSocket failure.

Check the status directly:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/status
```

Verification is ready only when the response contains non-null paths for both `iverilog` and `vvp`. After installing or unpacking the tools, restart the server and reload the browser page. On Windows, also confirm Git Bash exists at `C:\Program Files\Git\usr\bin\sh.exe`.

Common failure messages:

- **`Simulator unavailable`**: Icarus or VVP is not discoverable. Check `.tools/iverilog/bin` or system `PATH`.
- **`make: ... No rule to make target`**: GNU Make is missing or a Python `pymake` substitute is being selected. Install real GNU Make or place it at `.tools/make/bin/make.exe`.
- **`tr is not recognized` / `uname ... failed`**: Git Bash utilities are not available to the Make subprocess. Install Git for Windows and restart the server.
- **Port 8000 already in use**: use another port, for example `eda-agent ui --port 8001`, then open `http://127.0.0.1:8001`.
- **Ollama connection warnings**: the generator falls back to the built-in rule-based engine when the configured LLM endpoint is unavailable. Simulation still requires the simulator toolchain.

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
