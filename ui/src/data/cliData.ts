import { CliCommand } from '../types';

export const cliCommands: CliCommand[] = [
  {
    name: 'verify',
    syntax: 'eda-agent verify <RTL_FILE> [OPTIONS]',
    description: 'Runs complete closed-loop autonomous verification: linting, gate-level synthesis, cocotb testbench synthesis, headless simulation, and iterative self-repair.',
    category: 'Core Flow',
    flags: [
      { flag: '--max-retries', description: 'Maximum closed-loop self-repair attempts if tests fail', default: '3' },
      { flag: '--spec', description: 'Natural language specification or timing requirement prompt' },
      { flag: '--simulator', description: 'Simulation backend engine (icarus, verilator, vcs)', default: 'icarus' },
      { flag: '--clean', description: 'Clean intermediate simulation build artifacts', default: 'true' },
      { flag: '--dump-vcd', description: 'Generate Value Change Dump waveform for WaveDrom visualization', default: 'true' }
    ],
    sampleExecution: 'eda-agent verify examples/rtl/alu_8bit.v --max-retries 3 --dump-vcd',
    sampleOutput: `[EDA-AGENT] Starting autonomous verification loop for module 'alu_8bit'...
[STAGE 1] RTL Interface Extraction: Extracted 8 ports (clk, rst_n, a, b, opcode, result, zero, carry).
[STAGE 2] Verilator Static Lint: Lint clean (0 warnings, 0 errors).
[STAGE 3] Yosys Synthesizability: Gate-level check passed. 42 logic cells mapped. 0 latches inferred.
[STAGE 4] Cocotb Synthesis: Synthesizing testbench in sim/test_alu_8bit.py...
[STAGE 5] Simulation Iteration 1:
          - Running Icarus Verilog + Cocotb v2.0 harness...
          - Assertion Error: Expected result 0x00 for opcode ADD, observed 0x100 at cycle 124.
[STAGE 6] Hardware Diagnostics:
          - Root cause: 9-bit carry overflow unmasked in 8-bit output register.
          - Applying surgical RTL patch: 'result <= (a + b) & 8\'hFF;'
[STAGE 7] Simulation Iteration 2:
          - Re-running simulation with patched RTL...
          - All 8 opcodes validated across 120 randomized vectors!
🏆 Verification PASSED in 2 attempt(s). VCD Waveform saved to sim/alu_8bit.vcd.`
  },
  {
    name: 'lint',
    syntax: 'eda-agent lint <RTL_FILE> [OPTIONS]',
    description: 'Executes Verilator static linting with -Wall and formats diagnostic output as human-readable summaries or structured JSON.',
    category: 'Core Flow',
    flags: [
      { flag: '--json-output', description: 'Output structured JSON array containing file, line, and warning tokens' },
      { flag: '--strict', description: 'Treat warnings as fatal errors (return code 1)' },
      { flag: '--incdir', description: 'Add directory to SystemVerilog include search path' }
    ],
    sampleExecution: 'eda-agent lint examples/rtl/alu_8bit.v --json-output',
    sampleOutput: `{
  "file": "examples/rtl/alu_8bit.v",
  "clean": true,
  "warning_count": 0,
  "error_count": 0,
  "diagnostics": [],
  "tool": "Verilator 5.020",
  "duration_ms": 142
}`
  },
  {
    name: 'synth',
    syntax: 'eda-agent synth <RTL_FILE> [OPTIONS]',
    description: 'Runs Yosys gate-level synthesis script to check technology synthesizability, count standard cells, and flag unintended transparent latches.',
    category: 'Core Flow',
    flags: [
      { flag: '--top', description: 'Top-level module name if file contains multiple modules' },
      { flag: '--tech', description: 'Target technology library (generic, sky130, asap7)', default: 'generic' },
      { flag: '--show-cells', description: 'Print full standard cell breakdown (DFF, MUX, NAND, NOR)', default: 'true' }
    ],
    sampleExecution: 'eda-agent synth examples/rtl/alu_8bit.v --show-cells',
    sampleOutput: `[YOSYS SYNTHESIS REPORT]
Top Module: alu_8bit
Synthesizable: YES
Inferred Transparent Latches: 0 (PASSED)

Standard Cell Breakdown:
  $_DFF_P_    : 11 flip-flops
  $_MUX_      : 32 multiplexers
  $_NAND_     : 18 gates
  $_XOR_      : 8 gates
  Total Area  : 69 equivalent gate units.`
  },
  {
    name: 'generate',
    syntax: 'eda-agent generate <RTL_FILE> [OPTIONS]',
    description: 'Synthesizes a standalone, production-ready Python cocotb testbench with randomized stimulus, clock generation, and golden software models.',
    category: 'Core Flow',
    flags: [
      { flag: '-o, --output', description: 'Target path for generated Python testbench', default: 'test_<module>.py' },
      { flag: '--spec', description: 'Optional natural language specification or corner case requirements' },
      { flag: '--coverage', description: 'Include functional coverage bins (cocotb-coverage format)' }
    ],
    sampleExecution: 'eda-agent generate examples/rtl/alu_8bit.v -o sim/test_alu_8bit.py',
    sampleOutput: `[EDA-AGENT] Parsing 'examples/rtl/alu_8bit.v'...
[EDA-AGENT] Synthesized 145 lines of Python cocotb code:
  - 1 Clock coroutine (10ns period, 100MHz)
  - 1 Reset coroutine (active-low 20ns pulse)
  - 1 Golden reference model: golden_alu_model(a, b, op)
  - 4 Cocotb test functions covering all opcodes and boundary conditions
Saved testbench to sim/test_alu_8bit.py.`
  },
  {
    name: 'assert',
    syntax: 'eda-agent assert <RTL_FILE> [OPTIONS]',
    description: 'Translates natural language hardware timing specifications into formal SystemVerilog Assertions (SVA) and Cocotb check coroutines.',
    category: 'Assertions',
    flags: [
      { flag: '-s, --spec', description: 'Natural language assertion string', required: true },
      { flag: '--format', description: 'Output format: sva, cocotb, or both', default: 'both' }
    ],
    sampleExecution: 'eda-agent assert examples/rtl/fifo_async.v -s "ready drops low when valid is asserted and fifo is full"',
    sampleOutput: `[SYNTHESIZED SVA PROPERTY]
property p_ready_drop_on_full;
    @(posedge clk) disable iff (!rst_n)
    (valid && full) |-> ##1 (!ready);
endproperty
assert property (p_ready_drop_on_full) else $error("Ready failed to drop when FIFO full!");

[COCOTB CHECK COROUTINE]
async def check_ready_drop(dut):
    while True:
        await RisingEdge(dut.clk)
        if dut.valid.value and dut.full.value:
            await RisingEdge(dut.clk)
            assert dut.ready.value == 0, "Ready signal failed to drop low!"`
  },
  {
    name: 'triage-log',
    syntax: 'eda-agent triage-log <LOG_FILE> [OPTIONS]',
    description: 'Translates raw simulator stack traces, assertion failures, or compiler logs into plain digital engineering root cause explanations.',
    category: 'Diagnostics & STA',
    flags: [
      { flag: '--rtl', description: 'Path to corresponding RTL file for line number referencing' },
      { flag: '--json', description: 'Output diagnostic report as structured JSON' }
    ],
    sampleExecution: 'eda-agent triage-log sim.log --rtl examples/rtl/alu_8bit.v',
    sampleOutput: `[HARDWARE DIAGNOSTIC POST-MORTEM]
Failure Type: Combinational Settling & Bitwidth Overflow
Timestamp   : T = 1240.00 ns (Clock Cycle #124)
Failing Net : result[7:0]

Root Cause Explanation:
  During execution of Opcode 3'b000 (ADD) with inputs a=0xFF and b=0x01, the arithmetic operation produced 9'h100.
  The RTL assigned full 9 bits into an 8-bit bus without explicit carry truncation, causing bit 8 to corrupt the adjacent zero flag.

Recommended Hardware Fix:
  Modify line 32 of examples/rtl/alu_8bit.v:
  - result <= temp_result;
  + result <= temp_result[DATA_WIDTH-1:0];`
  },
  {
    name: 'analyze-timing',
    syntax: 'eda-agent analyze-timing <STA_LOG_FILE> [OPTIONS]',
    description: 'Parses OpenROAD and OpenSTA Static Timing Analysis reports to extract Worst Negative Slack (WNS), Total Negative Slack (TNS), and critical paths.',
    category: 'Diagnostics & STA',
    flags: [
      { flag: '--suggest-pipeline', description: 'Generate RTL register slice code diff to close timing', default: 'true' },
      { flag: '--clock-period', description: 'Target clock period in nanoseconds (e.g. 1.25 for 800MHz)' }
    ],
    sampleExecution: 'eda-agent analyze-timing examples/logs/openroad_sta_violated.log --suggest-pipeline',
    sampleOutput: `[OPENROAD / OPENSTA TIMING ANALYSIS]
Timing Status         : VIOLATED (Setup Slack)
Worst Negative Slack  : -0.450 ns
Total Negative Slack  : -2.850 ns
Violated Endpoints    : 4 endpoints

Critical Path:
  Startpoint : reg_stage0/clk -> Q (0.22 ns delay)
  Data Path  : 32-bit Multiplier Tree + 64-bit Adder (1.48 ns combinational)
  Endpoint   : mac_out_reg[63]/D (Data arrival time = 1.70 ns vs required = 1.25 ns)

Recommended RTL Pipeline Diff:
+ reg [63:0] mult_stage1;
+ always @(posedge clk) begin
+     mult_stage1 <= data_a * data_b;
+     mac_out     <= mac_out + mult_stage1;
+ end`
  },
  {
    name: 'sim',
    syntax: 'eda-agent sim [OPTIONS]',
    description: 'Runs standalone Cocotb test execution directly in an isolated sandbox with automated pytest harness.',
    category: 'Core Flow',
    flags: [
      { flag: '--dir', description: 'Simulation directory containing Makefile and testbench', default: 'sim/' },
      { flag: '--toplevel', description: 'Top-level Verilog module name', default: 'alu_8bit' },
      { flag: '--gui', description: 'Launch GTKWave / Surfer waveform viewer upon completion' }
    ],
    sampleExecution: 'eda-agent sim --dir examples/sim --toplevel alu_8bit',
    sampleOutput: `[SIM RUNNER] Running pytest with cocotb-test plugin...
======================= test session starts =======================
platform linux -- Python 3.11.8, pytest-8.2.0, cocotb-2.0.0
sim/test_alu_8bit.py::test_alu_8bit_functional PASSED        [100%]
======================= 1 passed in 0.08s =======================`
  },
  {
    name: 'config',
    syntax: 'eda-agent config [OPTIONS]',
    description: 'Configures airgapped local LLMs (Ollama, vLLM) or cloud API providers (Google Gemini, OpenAI).',
    category: 'Configuration & UI',
    flags: [
      { flag: '--provider', description: 'LLM provider: ollama, openai_compatible, gemini, openai, rule_based' },
      { flag: '--model', description: 'Model identifier (e.g. deepseek-coder-v2:16b, gemini-1.5-pro)' },
      { flag: '--base-url', description: 'Custom API base URL endpoint (e.g. http://localhost:11434/v1)' },
      { flag: '--show', description: 'Display current active configuration' }
    ],
    sampleExecution: 'eda-agent config --provider ollama --model deepseek-coder-v2:16b',
    sampleOutput: `[EDA-AGENT CONFIG]
Configuration successfully saved to ~/.config/eda-agent/config.json:
  Provider : ollama
  Model    : deepseek-coder-v2:16b
  Endpoint : http://localhost:11434/v1
  Airgapped: TRUE (Zero telemetry, 100% local processing)`
  },
  {
    name: 'ui',
    syntax: 'eda-agent ui [OPTIONS]',
    description: 'Launches the FastAPI backend and interactive Web Studio dashboard in your browser.',
    category: 'Configuration & UI',
    flags: [
      { flag: '--port', description: 'Web server port', default: '8000' },
      { flag: '--host', description: 'Bind host interface', default: '127.0.0.1' },
      { flag: '--open-browser', description: 'Automatically open browser on startup', default: 'true' }
    ],
    sampleExecution: 'eda-agent ui --port 8000',
    sampleOutput: `[EDA-AGENT WEB STUDIO]
FastAPI backend listening on http://127.0.0.1:8000
WebSocket verification streaming active on ws://127.0.0.1:8000/ws/verify
Opening browser... Press Ctrl+C to terminate.`
  },
  {
    name: 'info',
    syntax: 'eda-agent info',
    description: 'Inspects host environment, Python version, and checks availability of EDA binaries (iverilog, vvp, verilator, yosys, opensta).',
    category: 'Configuration & UI',
    flags: [],
    sampleExecution: 'eda-agent info',
    sampleOutput: `[EDA-AGENT TOOLCHAIN STATUS]
Python Version    : 3.11.8 (Linux x86_64)
EDA-Agent Version : 0.1.0

Detected Toolchain Binaries:
  [FOUND] Icarus Verilog : /usr/bin/iverilog (v12.0)
  [FOUND] VVP Engine     : /usr/bin/vvp
  [FOUND] Verilator      : /usr/bin/verilator (v5.020)
  [FOUND] Yosys          : /usr/bin/yosys (v0.38)
  [OPTIONAL] OpenSTA     : /usr/bin/sta (OpenROAD v2.0)`
  }
];
