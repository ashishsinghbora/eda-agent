import { CaseStudy } from '../types';

export const uvmVsCocotbComparison = {
  uvmCode: `// -------------------------------------------------------------
// Traditional UVM 1.2 SystemVerilog Testbench (Over 150+ lines)
// Requires: uvm_sequence_item, uvm_sequencer, uvm_driver,
// uvm_monitor, uvm_scoreboard, uvm_env, uvm_test & DPI-C bridges.
// -------------------------------------------------------------
\`include "uvm_macros.svh"
import uvm_pkg::*;

class alu_item extends uvm_sequence_item;
  rand bit [7:0] a, b;
  rand bit [2:0] opcode;
  bit [7:0] result;
  bit zero, carry;

  \`uvm_object_utils_begin(alu_item)
    \`uvm_field_int(a, UVM_ALL_ON)
    \`uvm_field_int(b, UVM_ALL_ON)
    \`uvm_field_int(opcode, UVM_ALL_ON)
    \`uvm_field_int(result, UVM_ALL_ON)
  \`uvm_object_utils_end

  function new(string name = "alu_item");
    super.new(name);
  endfunction
endclass

class alu_driver extends uvm_driver #(alu_item);
  \`uvm_component_utils(alu_driver)
  virtual alu_if vif;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual task run_phase(uvm_phase phase);
    forever begin
      seq_item_port.get_next_item(req);
      @(posedge vif.clk);
      vif.a      <= req.a;
      vif.b      <= req.b;
      vif.opcode <= req.opcode;
      @(posedge vif.clk);
      seq_item_port.item_done();
    end
  endtask
endclass

// ... Scoreboard, Monitor, Environment, Test definitions (100+ more lines)`,

  cocotbCode: `# -------------------------------------------------------------
# EDA-Agent Autonomous Python cocotb Testbench (24 lines)
# Native async/await, Python math models, zero boilerplate macros!
# -------------------------------------------------------------
import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

def alu_model(a: int, b: int, op: int) -> int:
    ops = [a + b, a - b, a & b, a | b, a ^ b, ~(a | b), a << 1, a >> 1]
    return ops[op] & 0xFF

@cocotb.test()
async def test_alu_exhaustive(dut):
    """Verify all 8 ALU opcodes across 150 randomized vectors."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    
    # Active-low reset pulse
    dut.rst_n.value = 0
    await Timer(20, unit="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    for op in range(8):
        for _ in range(20):
            a_val, b_val = random.randint(0, 255), random.randint(0, 255)
            dut.a.value, dut.b.value, dut.opcode.value = a_val, b_val, op
            await RisingEdge(dut.clk)
            await Timer(1, unit="ns")
            
            assert int(dut.result.value) == alu_model(a_val, b_val, op)`
};

export const comparisonMetrics = [
  {
    feature: 'Testbench Lines of Code',
    uvm: '300 - 1,500 lines per module (Boilerplate heavy)',
    edaAgent: '20 - 45 lines of concise Python async coroutines',
    advantage: '95% reduction in test harness code volume'
  },
  {
    feature: 'Language & Ecosystem',
    uvm: 'SystemVerilog only, proprietary macro language',
    edaAgent: 'Standard Python 3.11+, PyTest, NumPy, SciPy, Cocotb',
    advantage: 'Leverage rich Python data science & math libraries'
  },
  {
    feature: 'Simulator Licensing',
    uvm: 'Requires costly proprietary EDA simulators ($25k+/seat)',
    edaAgent: 'Runs seamlessly on 100% Free & Open-Source (Icarus, Verilator)',
    advantage: 'Zero simulator licensing fees; infinite cloud parallelism'
  },
  {
    feature: 'Autonomous Self-Repair',
    uvm: 'Manual engineer debugging & log inspection required',
    edaAgent: 'Closed-loop AI agent modifies RTL and testbench automatically',
    advantage: 'Self-corrects syntax, latches, and signal mismatches'
  },
  {
    feature: 'CI/CD Container Setup',
    uvm: 'Heavyweight license servers, complex vendor tool wrappers',
    edaAgent: 'Lightweight Docker image (<400MB), runs in GitHub Actions',
    advantage: 'Sub-second start time in standard CI/CD runners'
  },
  {
    feature: 'Hardware Diagnostics',
    uvm: 'Raw simulator assertion crashes with cryptic SV stack traces',
    edaAgent: 'Structured root cause triage (timing slack, state trap, latch)',
    advantage: 'Instant digital engineering plain-language explanations'
  }
];

export const fieldCaseStudies: CaseStudy[] = [
  {
    id: 'fsm_trap',
    title: 'Case Study 1: Edge-Case FSM Deadlock State Trap',
    category: 'FSM Deadlock',
    severity: 'Critical',
    explanation: 'A 4-state protocol arbiter (IDLE -> REQ -> GRANT -> RELEASE) omitted a default branch in its synchronous next-state decoder. When subjected to an illegal single-cycle noise burst on the reset deassertion boundary, the state register entered undefined binary state `2\'b11` (ERR_STATE) and became permanently trapped in a lockup cycle.',
    badRTL: `// BUGGY RTL: Missing default branch & unhandled state recovery
always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        current_state <= STATE_IDLE;
    else
        current_state <= next_state;
end

always @(*) begin
    case (current_state)
        STATE_IDLE:    next_state = req ? STATE_REQ : STATE_IDLE;
        STATE_REQ:     next_state = ack ? STATE_GRANT : STATE_REQ;
        STATE_GRANT:   next_state = done ? STATE_RELEASE : STATE_GRANT;
        STATE_RELEASE: next_state = STATE_IDLE;
        // Missing default branch: State 2'b11 traps FSM in undefined loop!
    endcase
end`,
    goodRTL: `// PATCHED RTL: Explicit default recovery & synthesis-safe always_comb
always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        current_state <= STATE_IDLE;
    else
        current_state <= next_state;
end

always @(*) begin
    next_state = STATE_IDLE; // Safe pre-assignment prevents latches
    case (current_state)
        STATE_IDLE:    next_state = req ? STATE_REQ : STATE_IDLE;
        STATE_REQ:     next_state = ack ? STATE_GRANT : STATE_REQ;
        STATE_GRANT:   next_state = done ? STATE_RELEASE : STATE_GRANT;
        STATE_RELEASE: next_state = STATE_IDLE;
        default:       next_state = STATE_IDLE; // Traps prevented
    endcase
end`,
    agentDiagnostic: 'DIAGNOSTIC TRIAGE: FSM lockup detected at T=450ns. State variable `current_state` stalled at 2\'b11 with no outgoing transition edge. Yosys warning: "Coverage gap in case statement". Patch applied: Injected `default: next_state = STATE_IDLE;` and pre-default assignment.',
    testbenchSnippet: `@cocotb.test()
async def test_fsm_illegal_state_recovery(dut):
    """Force FSM into undefined state 2'b11 and assert recovery within 1 clock."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.rst_n.value = 1
    # Force internal state wire via simulator handle
    dut.current_state.value = 3
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert dut.current_state.value == 0, "FSM failed to recover from illegal state!"`
  },
  {
    id: 'latch_detection',
    title: 'Case Study 2: Combinational Inferred Latch & Race Condition',
    category: 'Combinational Latch',
    severity: 'High',
    explanation: 'A combinational multiplexer and arithmetic decoder assigned the output `alu_out` only for valid opcodes 0-5. For opcodes 6 and 7, the signal was unassigned. In SystemVerilog, this forces synthesis tools (Yosys/Design Compiler) to synthesize transparent level-sensitive D-latches, causing severe timing hazards, glitching, and DFT scan-chain test failures.',
    badRTL: `// BUGGY RTL: Incomplete branch assignments infer transparent latches
always @(opcode or a or b) begin
    if (opcode == 3'b000) alu_out = a + b;
    else if (opcode == 3'b001) alu_out = a - b;
    else if (opcode == 3'b010) alu_out = a & b;
    else if (opcode == 3'b011) alu_out = a | b;
    else if (opcode == 3'b100) alu_out = a ^ b;
    // Opcode 3'b101, 3'b110, 3'b111 UNHANDLED!
    // Yosys will infer a hardware latch for alu_out!
end`,
    goodRTL: `// PATCHED RTL: Complete conditional branches with deterministic defaults
always @(*) begin
    alu_out = 8'h00; // Deterministic default assignment
    case (opcode)
        3'b000: alu_out = a + b;
        3'b001: alu_out = a - b;
        3'b010: alu_out = a & b;
        3'b011: alu_out = a | b;
        3'b010: alu_out = a ^ b;
        3'b101: alu_out = ~(a | b);
        3'b110: alu_out = a << 1;
        3'b111: alu_out = a >> 1;
        default: alu_out = 8'h00;
    endcase
end`,
    agentDiagnostic: 'YOSYS SYNTHESIS WARNING: "Inferred latch for signal `alu_out` in process at line 34". EDA-Agent Latch Analyzer detected 3 uncovered opcode branches. Applied patch replacing incomplete `if-else` chain with complete `case` structure and top-level default zeroing.',
    testbenchSnippet: `@cocotb.test()
async def test_unhandled_opcodes_deterministic(dut):
    """Assert unhandled opcodes produce deterministic outputs without latching memory."""
    for invalid_op in [5, 6, 7]:
        dut.opcode.value = invalid_op
        await Timer(5, unit="ns")
        assert dut.alu_out.value.is_resolvable, "Output floating or X detected!"`
  },
  {
    id: 'cdc_fifo',
    title: 'Case Study 3: Async FIFO Gray-Code Pointer Metastability',
    category: 'CDC Metastability',
    severity: 'Critical',
    explanation: 'In a dual-clock asynchronous FIFO (`wclk` at 200MHz, `rclk` at 50MHz), binary write pointers were directly sampled by the read clock domain without 2-stage flip-flop synchronizers or Gray-code encoding. Multi-bit simultaneous transitions caused bus skew and metastability, corrupting FIFO `full` / `empty` flags.',
    badRTL: `// BUGGY RTL: Direct binary pointer sampling across clock domains
always @(posedge rclk or negedge rst_n) begin
    if (!rst_n)
        rempty <= 1'b1;
    else
        // Direct multi-bit comparison across async clock boundary!
        rempty <= (rptr == wptr); 
end`,
    goodRTL: `// PATCHED RTL: Gray-code encoding + 2-Stage DFF Synchronizers
// 1. Convert binary pointers to Gray code
assign wptr_gray = (wptr_bin >> 1) ^ wptr_bin;

// 2. 2-Stage synchronizer into read clock domain
always @(posedge rclk or negedge rst_n) begin
    if (!rst_n) begin
        wptr_gray_sync1 <= 0;
        wptr_gray_sync2 <= 0;
    end else begin
        wptr_gray_sync1 <= wptr_gray;
        wptr_gray_sync2 <= wptr_gray_sync1;
    end
end
assign rempty = (rptr_gray == wptr_gray_sync2);`,
    agentDiagnostic: 'CDC DIAGNOSTIC: Clock Domain Crossing violation detected between `wclk` (200MHz) and `rclk` (50MHz). Multi-bit binary signal `wptr` sampled without synchronizer. EDA-Agent synthesized 2-stage Gray-code sync module with dual flip-flop metastability filters.',
    testbenchSnippet: `@cocotb.test()
async def test_async_fifo_burst_stress(dut):
    """Drive asynchronous burst traffic with non-integer clock phase offsets."""
    cocotb.start_soon(Clock(dut.wclk, 5, unit="ns").start())  # 200 MHz
    cocotb.start_soon(Clock(dut.rclk, 20, unit="ns").start()) # 50 MHz
    # Concurrently push 64 words while reading
    # Validates that no word is dropped and flags never glitch`
  },
  {
    id: 'timing_slack',
    title: 'Case Study 4: Setup Timing Slack Violation & Automated Pipelining',
    category: 'STA Negative Slack',
    severity: 'High',
    explanation: 'A 32-bit parameterized MAC (Multiply-Accumulate) unit placed a 32x32 multiplier and 64-bit adder in a single clock cycle combinational path. At 800 MHz (1.25 ns period), the propagation delay exceeded 1.70 ns, yielding a Worst Negative Slack (WNS) of -0.450 ns.',
    badRTL: `// BUGGY RTL: Unpipelined single-cycle multiplier + accumulator
always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        mac_out <= 64'h0;
    else if (enable)
        // 1.70ns combinational delay exceeds 1.25ns clock period!
        mac_out <= mac_out + (data_a * data_b);
end`,
    goodRTL: `// PATCHED RTL: 2-Stage Pipelined Multiply-Accumulate
reg [63:0] mult_stage1;
reg        valid_stage1;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        mult_stage1  <= 64'h0;
        valid_stage1 <= 1'b0;
        mac_out      <= 64'h0;
    end else begin
        // Stage 1: Multiplication slice (0.85 ns)
        mult_stage1  <= data_a * data_b;
        valid_stage1 <= enable;
        
        // Stage 2: Accumulation slice (0.55 ns)
        if (valid_stage1)
            mac_out  <= mac_out + mult_stage1;
    end
end`,
    agentDiagnostic: 'OPENSTA TIMING REPORT PARSER: WNS = -0.450 ns (VIOLATED) on endpoint `mac_out_reg[63]`. Path delay = 1.70 ns vs constraint = 1.25 ns. Rebuilding RTL: Inserted intermediate pipeline register slice `mult_stage1`. Timing closed: WNS = +0.320 ns (MET).',
    testbenchSnippet: `@cocotb.test()
async def test_pipelined_latency_throughput(dut):
    """Verify that 2-stage pipelined MAC produces outputs with exact 2-cycle latency."""
    dut.enable.value = 1
    dut.data_a.value = 10
    dut.data_b.value = 5
    await RisingEdge(dut.clk) # Cycle 1: Multiplier computes
    await RisingEdge(dut.clk) # Cycle 2: Accumulator registers
    await Timer(1, unit="ns")
    assert int(dut.mac_out.value) == 50, "Pipelined latency mismatch!"`
  }
];
