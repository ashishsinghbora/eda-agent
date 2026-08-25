import { ApiDocSection } from '../types';

export const apiDocs: ApiDocSection[] = [
  {
    package: 'eda_agent.core',
    title: 'Core Agent Engine & State Machine',
    description: 'Manages the master autonomous verification loop, state transitions, model router routing, and session contexts.',
    classes: [
      {
        name: 'AgentStateMachine',
        summary: 'Finite state machine managing lifecycle states: PARSING -> LINTING -> SYNTHESIZING -> SIMULATING -> TRIAGING -> REPAIRING -> COMPLETED.',
        methods: [
          { signature: 'transition_to(next_state: AgentState, context: dict = None) -> None', description: 'Validates state transition legality and updates active session context.', returnType: 'None' },
          { signature: 'get_history() -> List[StateRecord]', description: 'Returns complete chronological audit log of all state transitions and timestamps.', returnType: 'List[StateRecord]' }
        ],
        exampleCode: `from eda_agent.core.state_machine import AgentStateMachine, AgentState

sm = AgentStateMachine()
sm.transition_to(AgentState.PARSING, context={"file": "alu_8bit.v"})
sm.transition_to(AgentState.LINTING)
print(sm.current_state) # AgentState.LINTING`
      },
      {
        name: 'ModelRouter',
        summary: 'Routes prompt requests to local airgapped models (Ollama, vLLM) or cloud providers with automatic fallback and schema enforcement.',
        methods: [
          { signature: 'generate_completion(prompt: str, system_prompt: str = None) -> str', description: 'Executes inference request against configured LLM backend with retry logic.', returnType: 'str' },
          { signature: 'get_active_provider() -> ProviderConfig', description: 'Returns active provider type, base URL, and model name.', returnType: 'ProviderConfig' }
        ],
        exampleCode: `from eda_agent.core.router import ModelRouter

router = ModelRouter()
response = router.generate_completion(
    prompt="Generate cocotb test coroutine for 8-bit adder",
    system_prompt="You are a senior digital verification engineer."
)`
      }
    ]
  },
  {
    package: 'eda_agent.tools',
    title: 'Subprocess Tool Wrappers',
    description: 'Hardware tool integrations wrapping Verilator, Yosys, and Icarus Verilog in isolated subprocess sandboxes.',
    classes: [
      {
        name: 'VerilatorLinter',
        summary: 'Executes Verilator with `--lint-only -Wall` and converts compiler warnings into structured Python dataclasses.',
        methods: [
          { signature: 'lint_file(rtl_path: Path, incdirs: List[Path] = None) -> LintReport', description: 'Lints a Verilog file on disk and returns warning/error tokens.', returnType: 'LintReport' },
          { signature: 'lint_string(code: str) -> LintReport', description: 'Writes Verilog string to a temporary sandbox and executes static linting.', returnType: 'LintReport' }
        ],
        exampleCode: `from eda_agent.tools.verilator_linter import VerilatorLinter
from pathlib import Path

report = VerilatorLinter.lint_file(Path("examples/rtl/alu_8bit.v"))
print(f"Clean: {report.is_clean}, Warnings: {len(report.warnings)}")`
      },
      {
        name: 'SynthesisChecker',
        summary: 'Lightweight Yosys script executor that checks synthesizability, generates cell statistics, and flags transparent latches.',
        methods: [
          { signature: 'check_synthesizability(rtl_path: Path, top_module: str = None) -> SynthesisReport', description: 'Runs Yosys pass and returns cell counts and latch detections.', returnType: 'SynthesisReport' }
        ],
        exampleCode: `from eda_agent.tools.synthesis_checker import SynthesisChecker
from pathlib import Path

synth_report = SynthesisChecker.check_synthesizability(Path("examples/rtl/alu_8bit.v"))
print(f"Synthesizable: {synth_report.is_synthesizable}, Cell Map: {synth_report.cell_counts}")`
      }
    ]
  },
  {
    package: 'eda_agent.generators',
    title: 'Generators & Autonomous Repair',
    description: 'Autonomous generation of Python cocotb testbenches, SystemVerilog Assertions (SVA), and closed-loop self-repair loops.',
    classes: [
      {
        name: 'TestbenchGenerator',
        summary: 'Synthesizes clean, asynchronous Python cocotb testbenches from extracted ModuleSpec schemas and natural language specifications.',
        methods: [
          { signature: 'generate(module_spec: ModuleSpec, source_code: str = None, spec_text: str = None) -> str', description: 'Returns complete standalone Python testbench string ready for execution.', returnType: 'str' }
        ],
        exampleCode: `from eda_agent.parsers.verilog_parser import VerilogParser
from eda_agent.generators.testbench_generator import TestbenchGenerator

spec = VerilogParser.parse_file("examples/rtl/alu_8bit.v")[0]
generator = TestbenchGenerator()
tb_code = generator.generate(spec, spec_text="Verify zero flag on all operations")`
      },
      {
        name: 'VerificationLoop',
        summary: 'Master closed-loop self-repair harness. Orchestrates repeated simulation runs and applies diagnostic patches until 100% test pass.',
        methods: [
          { signature: 'run(rtl_file: Path, sim_dir: Path, max_retries: int = 3, clean: bool = True) -> LoopResult', description: 'Executes the iterative repair loop and returns detailed trial records.', returnType: 'LoopResult' }
        ],
        exampleCode: `from eda_agent.generators.repair_loop import VerificationLoop
from pathlib import Path

loop = VerificationLoop()
result = loop.run(
    rtl_file=Path("examples/rtl/alu_8bit.v"),
    sim_dir=Path("examples/sim"),
    max_retries=3
)
print(f"Success: {result.success} in {result.attempts} attempt(s)")`
      }
    ]
  },
  {
    package: 'eda_agent.analyzers',
    title: 'Hardware Diagnostics & STA Analyzers',
    description: 'Translates raw simulator failures into human-readable digital engineering root causes and analyzes static timing slack.',
    classes: [
      {
        name: 'HumanDiagnosticsTranslator',
        summary: 'Decodes simulator tracebacks, signal mismatches, and cocotb assertion failures into actionable hardware explanations and code patches.',
        methods: [
          { signature: 'translate(raw_log: str, dut_spec: ModuleSpec = None) -> HardwareFailureDiagnosis', description: 'Returns diagnosis with root cause, affected signals, and recommended patch.', returnType: 'HardwareFailureDiagnosis' }
        ],
        exampleCode: `from eda_agent.analyzers.human_diagnostics import HumanDiagnosticsTranslator

log = "AssertionError: assert 0x100 == 0x00 at 1240.00ns [Cycle 124]"
diag = HumanDiagnosticsTranslator.translate(raw_log=log)
print(diag.error_summary)
print(diag.recommended_fix)`
      },
      {
        name: 'STAAnalyzer',
        summary: 'Parses OpenROAD and OpenSTA static timing logs to identify Worst Negative Slack (WNS), Total Negative Slack (TNS), and critical paths.',
        methods: [
          { signature: 'parse_file(sta_log_path: Path) -> TimingReport', description: 'Parses STA report on disk into structured TimingReport dataclass.', returnType: 'TimingReport' },
          { signature: 'parse_string(log_content: str) -> TimingReport', description: 'Parses raw STA log string and extracts critical endpoints.', returnType: 'TimingReport' }
        ],
        exampleCode: `from eda_agent.analyzers.sta_analyzer import STAAnalyzer
from pathlib import Path

report = STAAnalyzer.parse_file(Path("examples/logs/openroad_sta_violated.log"))
print(f"WNS: {report.wns} ns | TNS: {report.tns} ns | Violated: {report.is_violated}")`
      }
    ]
  },
  {
    package: 'eda_agent.parsers',
    title: 'AST & Waveform Parsers',
    description: 'Tokenizes Verilog/SystemVerilog sources and converts simulation VCD files to interactive WaveDrom JSON timing diagrams.',
    classes: [
      {
        name: 'VerilogParser',
        summary: 'AST & regex Verilog parser extracting port lists, bus widths, clock domains, active-low resets, and parameters.',
        methods: [
          { signature: 'parse_file(file_path: Path) -> List[ModuleSpec]', description: 'Parses all modules inside a file into ModuleSpec objects.', returnType: 'List[ModuleSpec]' },
          { signature: 'parse_string(code: str) -> List[ModuleSpec]', description: 'Parses Verilog code string into ModuleSpec objects.', returnType: 'List[ModuleSpec]' }
        ],
        exampleCode: `from eda_agent.parsers.verilog_parser import VerilogParser

modules = VerilogParser.parse_file("examples/rtl/alu_8bit.v")
for mod in modules:
    print(f"Module: {mod.name}, Ports: {[p.name for p in mod.ports]}")`
      },
      {
        name: 'VCDParser',
        summary: 'Reads Value Change Dump (.vcd) files generated by Icarus/Verilator and formats them as WaveDrom timing diagrams.',
        methods: [
          { signature: 'to_wavedrom(vcd_path: Path, max_cycles: int = 20) -> dict', description: 'Extracts clock cycles and digital transitions into WaveDrom JSON schema.', returnType: 'dict' }
        ],
        exampleCode: `from eda_agent.parsers.vcd_parser import VCDParser
from pathlib import Path

wavedrom_json = VCDParser.to_wavedrom(Path("sim/alu_8bit.vcd"), max_cycles=15)
print(wavedrom_json["signal"])`
      }
    ]
  }
];

export const hardwareDesignRules = [
  {
    rule: 'IEEE 1800-2017 SystemVerilog Compliance',
    detail: 'Use modern standard constructs: `always_ff @(posedge clk or negedge rst_n)`, `always_comb`, and explicit `logic` / `wire` port typings.'
  },
  {
    rule: 'Active-Low Asynchronous Reset Convention',
    detail: 'Standardized reset naming (`rst_n`, `wrst_n`, `rrst_n`) with immediate asynchronous assert and synchronous deassert logic.'
  },
  {
    rule: 'Non-Blocking (<=) vs Blocking (=) Separation',
    detail: 'Strict enforcement: Sequential flip-flop updates MUST use `<=` non-blocking assignments; combinational logic MUST use `=` blocking assignments.'
  },
  {
    rule: 'Zero Inferred Latches & Complete Sensitivity Lists',
    detail: 'Combinational `always_comb` or `always @(*)` blocks must provide full coverage for all conditional branches or define top-level defaults.'
  },
  {
    rule: 'Parameterized Bitwidths',
    detail: 'All data buses, FIFO depths, and register files must expose parameterized widths (`#(parameter DATA_WIDTH = 8)`) for hardware reusability.'
  }
];
