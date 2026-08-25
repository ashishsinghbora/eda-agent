# EDA-Agent 🚀

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python: 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Docker: Ready](https://img.shields.io/badge/docker-ready-2496ED.svg?logo=docker&logoColor=white)](docker-compose.yml)
[![EDA: Open--Source](https://img.shields.io/badge/EDA-Open--Source-orange.svg)](https://github.com/ashishsinghbora/eda-agent)
[![Linter: Verilator](https://img.shields.io/badge/linter-Verilator-purple.svg)](https://www.veripool.org/verilator/)
[![Synthesis: Yosys](https://img.shields.io/badge/synthesis-Yosys-red.svg)](https://yosyshq.net/yosys/)
[![Simulator: Icarus Verilog](https://img.shields.io/badge/simulator-Icarus%20Verilog-green.svg)](https://steveicarus.github.io/iverilog/)
[![Framework: cocotb](https://img.shields.io/badge/framework-cocotb%20v2.0%2B-orange.svg)](https://www.cocotb.org/)

**EDA-Agent** is an industry-grade autonomous Electronic Design Automation (EDA) and VLSI verification assistant. It bridges hardware description languages (SystemVerilog/Verilog) with modern Python verification workflows (`cocotb`), providing automated RTL interface extraction, Verilator linting, Yosys gate-level synthesizability checking, testbench synthesis, closed-loop simulation self-repair, Static Timing Analysis (STA) diagnostics, and interactive waveform visualization.

---

## 🏛️ System Architecture & Autonomous Flow

```mermaid
flowchart TD
    A[RTL Source .v / .sv] --> B[RTL Interface Parser]
    B --> C[Verilator Linter]
    C -->|Syntax / Linter Diagnostics| D{Lint Clean?}
    D -->|No| E[RTL Auto-Repair Engine]
    E --> C
    D -->|Yes| F[Yosys Synthesizability Checker]
    F -->|Gate-level Check & Cell Counts| G{Synthesizable?}
    G -->|No| E
    G -->|Yes| H[Autonomous Cocotb Testbench Generator]
    H --> I[Headless Simulation Harness (Icarus / Cocotb)]
    I --> J{Simulation Passes?}
    J -->|Yes| K[Verification Succeeded: VCD Waveforms & Reports]
    J -->|No| L[Hardware Diagnostic & Triage Engine]
    L -->|Traceback & Signal Mismatch Context| M[Closed-Loop Testbench / RTL Repair]
    M --> I
```

### Key Modules:
- **`eda_agent.core`**: Master agent loop (`AgentLoop`), lifecycle state machine (`AgentStateMachine`), and airgapped LLM provider routing (`ModelRouter`).
- **`eda_agent.tools`**: Subprocess tool wrappers for Verilator (`verilator_linter`), Icarus/Cocotb (`sim_runner`), and Yosys (`synthesis_checker`).
- **`eda_agent.prompts`**: Hardware-specific prompt engineering enforcing IEEE 1800-2017 SystemVerilog, parameterized modules, active-low resets (`rst_n`), non-blocking (`<=`) sequential updates, and clean sensitivity lists.
- **`eda_agent.analyzers`**: Cocotb JUnit XML result aggregator (`coverage_analyzer`), digital engineering log translator (`human_diagnostics`), and OpenROAD/OpenSTA timing parser (`sta_analyzer`).
- **`eda_agent.parsers`**: AST & regex Verilog parser (`verilog_parser`) and VCD-to-WaveDrom waveform converter (`vcd_parser`).
- **`eda_agent.server`**: FastAPI backend with WebSocket verification streaming and interactive Web Studio dashboard.

---

## ⚡ Quickstart

### Option A: Zero-Dependency Docker Compose (Recommended)

Run the entire open-source EDA suite (Verilator, Icarus Verilog, Yosys, Python 3, Web UI) in isolated containers without installing EDA binaries on the host:

```bash
# 1. Clone the repository
git clone https://github.com/ashishsinghbora/eda-agent.git
cd eda-agent

# 2. Launch containerized Web Studio & API server
docker compose up -d

# 3. Access Web Studio
open http://localhost:8000
```

To run CLI commands inside Docker:
```bash
docker compose run --rm eda-agent verify examples/rtl/alu_8bit.v
docker compose run --rm eda-agent lint examples/rtl/alu_8bit.v
```

---

### Option B: Bare-Metal Installation

#### Prerequisites
- **Python 3.10+** (Python 3.11+ recommended)
- **Icarus Verilog (`iverilog`)**, **`vvp`**, **`verilator`** (optional), and **`yosys`** (optional)

```bash
# Ubuntu / Debian
sudo apt-get update && sudo apt-get install -y iverilog verilator yosys build-essential make

# Arch Linux
sudo pacman -S iverilog verilator yosys make
```

#### Install Python Package
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install EDA-Agent in editable mode
pip install -e .
```

---

## 💻 CLI Commands & Usage

```bash
# Display help and available commands
eda-agent --help
```

| Command | Description | Example |
|---|---|---|
| `generate` | Synthesizes standalone Cocotb testbench in Python | `eda-agent generate examples/rtl/alu_8bit.v -o test_alu.py` |
| `lint` | Runs Verilator `--lint-only -Wall` with structured JSON | `eda-agent lint examples/rtl/alu_8bit.v --json-output` |
| `synth` | Runs Yosys gate-level synthesizability check & cell stats | `eda-agent synth examples/rtl/alu_8bit.v` |
| `verify` | End-to-end closed-loop verification & self-repair loop | `eda-agent verify examples/rtl/alu_8bit.v --max-retries 3` |
| `triage-log` | Translates raw simulator error logs into hardware root cause | `eda-agent triage-log sim.log --rtl examples/rtl/alu_8bit.v` |
| `assert` | Synthesizes SVA properties & Cocotb check coroutines | `eda-agent assert examples/rtl/fifo_async.v -s "ready drops low when full"` |
| `analyze-timing` | Parses OpenROAD/OpenSTA timing logs & provides RTL diffs | `eda-agent analyze-timing examples/logs/openroad_sta_violated.log` |
| `sim` | Executes Cocotb simulation directly in headless sandbox | `eda-agent sim --dir examples/sim --toplevel alu_8bit` |
| `config` | Manages local (Ollama/vLLM) and cloud LLM providers | `eda-agent config --provider ollama --model deepseek-coder-v2:16b` |
| `ui` | Launches FastAPI backend & interactive Web UI studio | `eda-agent ui --port 8000` |
| `info` | Displays environment status and detected EDA tool binaries | `eda-agent info` |

---

## 🔧 Concrete Examples

### 1. 8-Bit Parameterized ALU (`examples/rtl/alu_8bit.v`)

```verilog
`timescale 1ns / 1ps

module alu_8bit #(
    parameter DATA_WIDTH = 8
)(
    input  wire                  clk,
    input  wire                  rst_n,
    input  wire [DATA_WIDTH-1:0] a,
    input  wire [DATA_WIDTH-1:0] b,
    input  wire [2:0]            opcode,
    output reg  [DATA_WIDTH-1:0] result,
    output reg                   zero,
    output reg                   carry,
    output reg                   overflow
);
    // Combinational logic & synchronous registered outputs
    ...
endmodule
```

### 2. Auto-Generated Cocotb Testbench (`examples/sim/test_alu_8bit.py`)

```python
import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

async def reset_dut(dut):
    dut.rst_n.value = 0
    dut.a.value = 0
    dut.b.value = 0
    dut.opcode.value = 0
    await Timer(20, unit="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

@cocotb.test()
async def test_alu_8bit_functional(dut):
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

            assert int(dut.result.value) == expected_alu_model(a_val, b_val, op)
```

---

## 🧪 Testing & Quality Assurance

Run the comprehensive pytest suite:

```bash
pytest -v
```

---

## 📄 License

This project is licensed under the [Apache-2.0 License](LICENSE).
