import { PipelineStage } from '../types';

export const pipelineStages: PipelineStage[] = [
  {
    id: 'parser',
    title: '1. RTL AST & Interface Parser',
    subtitle: 'Extracts ports, parameters, bus widths, clocks & reset polarities',
    iconName: 'FileCode2',
    modulePath: 'eda_agent.parsers.verilog_parser.VerilogParser',
    description: 'Scans SystemVerilog and Verilog-2005 source files using robust regex and AST tokenizers. Extracts module headers, parameter definitions, clock/reset semantics, active-low reset detection, and port directionality into strongly typed ModuleSpec dataclasses.',
    inputs: ['Top-level RTL (.v / .sv)', 'Include directories (+incdir+)', 'Parameter overrides (-P)'],
    outputs: ['ModuleSpec (typed port lists, widths, clock flags, FSM states)', 'Parsed parameter map'],
    toolCommand: 'python -m eda_agent.parsers.verilog_parser examples/rtl/alu_8bit.v',
    sampleDiagnostic: 'Extracted module `alu_8bit`: 8 ports detected (clk[1], rst_n[1], a[DATA_WIDTH-1:0], b[DATA_WIDTH-1:0], opcode[2:0], result[DATA_WIDTH-1:0], zero[1], carry[1], overflow[1]).',
    recoveryAction: 'Infers default widths (1-bit wire) if implicit port definitions are detected; logs syntax parse warnings for malformed module headers.',
    color: 'cyan'
  },
  {
    id: 'verilator',
    title: '2. Verilator Lint Engine',
    subtitle: 'High-speed static linting with structured JSON diagnostic parsing',
    iconName: 'ShieldAlert',
    modulePath: 'eda_agent.tools.verilator_linter.VerilatorLinter',
    description: 'Executes Verilator with -Wall -Wno-fatal --lint-only in headless subprocesses. Parses GCC-style compiler warnings, implicit net declarations, width mismatches (WIDTHCONCAT, WIDTHTRUNC), unhandled sensitivity lists (COMBDLY), and combinational loops.',
    inputs: ['Verilog Source Code', 'Lint configuration flags', 'Include search paths'],
    outputs: ['LintReport (boolean clean, warning count, line-by-line diagnostic tokens, severity levels)'],
    toolCommand: 'verilator --lint-only -Wall -Wno-fatal --bbox-sys --sv examples/rtl/alu_8bit.v',
    sampleDiagnostic: '%Warning-WIDTHCONCAT: alu_8bit.v:32:15: Operator ADD expects 8 bits on RHS, but LHS has 9 bits. Output may truncate carry flag.',
    recoveryAction: 'Trigger Autonomous RTL Repair Loop: feeds line number, token context, and fix recommendation to Prompt Engine to patch SystemVerilog source.',
    color: 'purple'
  },
  {
    id: 'yosys',
    title: '3. Yosys Gate-Level Synthesis Check',
    subtitle: 'Verifies hardware synthesizability, infers cell counts & detects latches',
    iconName: 'Cpu',
    modulePath: 'eda_agent.tools.synthesis_checker.SynthesisChecker',
    description: 'Runs lightweight Yosys synthesis script (read_verilog, hierarchy -check, proc, opt, stat) to ensure the RTL is physically synthesizable to standard cell gates. Detects unintentional inferred transparent latches and multi-driven nets.',
    inputs: ['Lint-clean RTL source', 'Target technology cell library (generic CMOS / Sky130 / ASAP7)'],
    outputs: ['SynthesisReport (is_synthesizable, cell_count_map: DFF, MUX, NAND, inferred_latches: list)'],
    toolCommand: 'yosys -p "read_verilog -sv rtl.v; hierarchy -check -top alu_8bit; proc; opt; stat"',
    sampleDiagnostic: 'Warning: Inferred latch for signal `next_state` in process at rtl.v:45. Not all conditions covered in combinational case statement.',
    recoveryAction: 'Auto-injects default assignment values into combinational always blocks (always_comb) before case statements to eliminate transparent latches.',
    color: 'amber'
  },
  {
    id: 'cocotb_gen',
    title: '4. Autonomous Cocotb Testbench Generator',
    subtitle: 'Synthesizes clean Python coroutines with randomized stimulus & assertions',
    iconName: 'FlaskConical',
    modulePath: 'eda_agent.generators.testbench_generator.TestbenchGenerator',
    description: 'Generates robust, asynchronous Python testbenches powered by cocotb 2.0+. Automatically produces clock generators (cocotb.clock.Clock), active-low asynchronous reset sequences (reset_dut()), randomized boundary test vectors, and golden reference software models.',
    inputs: ['ModuleSpec dataclass', 'Natural language test specification / timing requirements', 'Target simulator flags'],
    outputs: ['Complete `test_<module>.py` file', 'Automated Makefile / pyproject.toml runner harness'],
    toolCommand: 'eda-agent generate examples/rtl/alu_8bit.v -o sim/test_alu_8bit.py',
    sampleDiagnostic: 'Synthesized 4 coroutine test vectors: test_reset_behavior, test_alu_exhaustive_opcodes, test_randomized_boundary_vectors, test_corner_cases.',
    recoveryAction: 'Refines stimulus generators if port ranges are constrained by parameters (e.g., parameterized 16-bit or 32-bit registers).',
    color: 'emerald'
  },
  {
    id: 'sim_runner',
    title: '5. Headless Simulation Sandbox',
    subtitle: 'Runs Icarus Verilog, Verilator, or Synopsys VCS in an isolated environment',
    iconName: 'PlaySquare',
    modulePath: 'eda_agent.runners.simulation_runner.SimulationRunner',
    description: 'Orchestrates headless simulation jobs using Icarus Verilog (iverilog + vvp) or Verilator C++ simulation harnesses. Captures stdout/stderr streams, generates Value Change Dump (.vcd) waveforms, and parses JUnit XML test result summaries.',
    inputs: ['Synthesized Cocotb Testbench', 'Target RTL', 'Simulator backend (iverilog, verilator, vcs)'],
    outputs: ['SimulationResult (exit_code, pass_count, fail_count, duration_seconds, vcd_path, raw_log)'],
    toolCommand: 'pytest -v sim/ --cocotb-simulator=icarus',
    sampleDiagnostic: 'AssertionError: assert 0x100 == 0x00 at 1240.00ns [Cycle 124]. Opcode ADD failed with inputs a=0xFF, b=0x01.',
    recoveryAction: 'Feeds traceback and simulation failure timestamp directly into Hardware Failure Triage Engine.',
    color: 'rose'
  },
  {
    id: 'triage_repair',
    title: '6. Closed-Loop Hardware Diagnostics & Self-Repair',
    subtitle: 'Translates raw tracebacks into hardware terms and iterates until 100% green',
    iconName: 'Wrench',
    modulePath: 'eda_agent.analyzers.human_diagnostics.HumanDiagnosticsTranslator',
    description: 'Translates complex simulator mismatches and stack traces into plain digital engineering root causes (e.g., "1-cycle setup lag on registered output", "missing synchronous reset clear", "carry overflow wraparound bug"). Applies precise surgical code diffs and re-triggers simulation in a bounded loop.',
    inputs: ['Failure logs', 'RTL source code', 'Testbench code', 'Max retry iteration limit (default: 3)'],
    outputs: ['Patched RTL file', 'Human-readable failure explanation & diff', 'Final green verification report'],
    toolCommand: 'eda-agent verify examples/rtl/alu_8bit.v --max-retries 3',
    sampleDiagnostic: 'Iteration 1 Failed: Opcode 0 (ADD) produced 9-bit result 0x100 instead of truncated 8-bit 0x00. Applied patch: `result <= (a + b) & 8\'hFF;`. Iteration 2: PASSED (100%).',
    recoveryAction: 'Performs multi-turn self-correction; halts gracefully if iteration limit exceeded and generates comprehensive hardware post-mortem.',
    color: 'cyan'
  },
  {
    id: 'sta_engine',
    title: '7. Static Timing Analysis (STA) Diagnostics',
    subtitle: 'Parses OpenROAD / OpenSTA logs, computes WNS/TNS & suggests pipelining',
    iconName: 'Clock',
    modulePath: 'eda_agent.analyzers.sta_analyzer.STAAnalyzer',
    description: 'Parses Static Timing Analysis reports from OpenROAD and OpenSTA. Identifies critical timing paths, setup/hold slack violations, Worst Negative Slack (WNS), and Total Negative Slack (TNS). Recommends register retiming and pipeline stage insertion to achieve timing closure.',
    inputs: ['OpenSTA / OpenROAD timing log', 'Target clock period constraint (SDC)'],
    outputs: ['TimingReport (WNS: float, TNS: float, critical_path: list, violated_endpoints: list, pipeline_diff)'],
    toolCommand: 'eda-agent analyze-timing examples/logs/openroad_sta_violated.log',
    sampleDiagnostic: 'CRITICAL TIMING VIOLATION: WNS = -0.450 ns (Setup Slack Violated) on path `reg_stage0` -> `alu_out_reg` at 1.0 GHz target frequency.',
    recoveryAction: 'Proposes RTL register slice insertion: splits combinational ALU logic across two clock cycles with intermediate `reg_stage1` pipeline register.',
    color: 'purple'
  }
];

export const pipelineModes = [
  {
    id: 'verify',
    title: 'End-to-End Autonomous Verification Loop',
    description: 'Full automated cycle: RTL parsing → Verilator lint → Yosys synthesis check → Cocotb testbench synthesis → Headless simulation → Closed-loop self-repair → Waveform export.',
    activeStages: ['parser', 'verilator', 'yosys', 'cocotb_gen', 'sim_runner', 'triage_repair']
  },
  {
    id: 'synth',
    title: 'Gate-Level Synthesizability & Latch Checking',
    description: 'Fast static flow to ensure RTL is free of combinational loops, unhandled case branches, transparent latches, and meets technology mapping requirements.',
    activeStages: ['parser', 'verilator', 'yosys']
  },
  {
    id: 'timing',
    title: 'Static Timing (STA) Slack Analysis & Pipelining',
    description: 'Parses OpenROAD/OpenSTA logs to diagnose setup/hold slack violations, locate worst critical timing paths, and suggest register retiming diffs.',
    activeStages: ['sta_engine']
  },
  {
    id: 'assertions',
    title: 'Natural Language Spec → SVA Property Synthesis',
    description: 'Translates English timing specifications (e.g., "ready drops low when full") into formal SystemVerilog Assertions (`assert property`) and Cocotb check coroutines.',
    activeStages: ['parser', 'cocotb_gen', 'sim_runner']
  }
];
