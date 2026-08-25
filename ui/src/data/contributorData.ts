export const backendAdapterGuide = {
  overview: `EDA-Agent uses a modular plugin architecture. All hardware tool wrappers subclass the abstract base class \`BaseTool\` or \`BaseSimulator\`. Adding support for a new EDA tool (e.g. Synopsys VCS, AMD Vivado xsim, OpenLane, PyUVM) requires implementing three standard methods.`,
  snippet: `from pathlib import Path
from typing import List, Optional
from eda_agent.tools.base import BaseSimulator, SimulationResult

class VivadoXsimRunner(BaseSimulator):
    """Adapter for AMD Vivado xsim hardware simulation."""
    
    @property
    def name(self) -> str:
        return "vivado_xsim"
    
    def is_available(self) -> bool:
        """Check if 'xelab' and 'xsim' binaries are present in PATH."""
        return self._check_binary("xelab") and self._check_binary("xsim")
    
    def run_simulation(
        self,
        top_module: str,
        rtl_files: List[Path],
        testbench_path: Path,
        sim_dir: Path,
        dump_vcd: bool = True
    ) -> SimulationResult:
        """Execute xelab elaboration and xsim batch simulation."""
        # 1. Elaboration: xelab -svlog <rtl> -s top_sim
        elab_cmd = ["xelab", "-svlog", str(rtl_files[0]), "-s", f"{top_module}_sim"]
        self._run_subprocess(elab_cmd, cwd=sim_dir)
        
        # 2. Execution: xsim top_sim -R
        xsim_cmd = ["xsim", f"{top_module}_sim", "-R"]
        res = self._run_subprocess(xsim_cmd, cwd=sim_dir)
        
        return self._parse_output(res.stdout, res.stderr, res.returncode)`
};

export const goodFirstIssues = [
  {
    id: 'ISSUE-101',
    title: 'Add Cadence Xcelium & Synopsys VCS simulator runners',
    area: '`eda_agent.runners`',
    difficulty: 'Intermediate',
    description: 'Implement `VCSSimulator` and `XceliumSimulator` subclasses with DPI-C cocotb argument bindings (`-cc`, `-debug_access+all`).',
    tags: ['Simulators', 'Commercial EDA', 'Python']
  },
  {
    id: 'ISSUE-102',
    title: 'Support VHDL-2008 & Mixed-Language Parsing',
    area: '`eda_agent.parsers`',
    difficulty: 'Advanced',
    description: 'Add GHDL AST parser frontend to support mixed Verilog/VHDL interface extraction and port direction mapping.',
    tags: ['VHDL', 'GHDL', 'Parser']
  },
  {
    id: 'ISSUE-103',
    title: 'SymbiYosys (sby) Formal Verification Backend',
    area: '`eda_agent.generators`',
    difficulty: 'Intermediate',
    description: 'Synthesize `.sby` formal verification configurations and bounded model checking (BMC) harnesses from SVA properties.',
    tags: ['Formal Verification', 'SymbiYosys', 'SVA']
  },
  {
    id: 'ISSUE-104',
    title: 'OpenLane 2.0 Physical ASIC Flow Plugin',
    area: '`eda_agent.tools`',
    difficulty: 'Advanced',
    description: 'Automate floorplanning, placement, and routing metric diagnostics with Sky130 PDK integration.',
    tags: ['OpenLane', 'Physical Design', 'Sky130']
  },
  {
    id: 'ISSUE-105',
    title: 'Add CLI autocomplete for Zsh & Fish',
    area: '`eda_agent.cli`',
    difficulty: 'Easy',
    description: 'Generate shell autocompletion scripts using Typer/Click shell completion hooks for all 11 subcommands.',
    tags: ['CLI', 'Good First Issue', 'Python']
  }
];

export const roadmapMilestones = [
  {
    quarter: '2025 Q1',
    status: 'Completed',
    title: 'AST Interface Parsing & Local Airgapped LLM Router',
    details: [
      'Regex & AST Verilog token parser with parameter detection',
      'Verilator 5.0 static linting integration with structured JSON reports',
      'Local Ollama & vLLM airgapped model routing (zero telemetry)',
      'Autonomous Cocotb 2.0 Python testbench generation'
    ]
  },
  {
    quarter: '2025 Q2',
    status: 'Completed',
    title: 'Yosys Synthesis & Closed-Loop Self-Repair Engine',
    details: [
      'Yosys gate-level synthesizability checks & latch inference detection',
      'Interactive Web Studio & WebSocket live streaming harness',
      'OpenROAD / OpenSTA timing parser with negative slack diagnostics',
      'Value Change Dump (.vcd) to WaveDrom timing diagram converter'
    ]
  },
  {
    quarter: '2025 Q3',
    status: 'In Progress',
    title: 'Formal Verification & SymbiYosys (sby) BMC Engine',
    details: [
      'Automated SVA property synthesis and induction proving',
      'Integration with SymbiYosys and Z3 / boolector SMT solvers',
      'Equivalence checking between unpipelined and pipelined RTL variants',
      'Multi-engine formal assertion coverage analysis'
    ]
  },
  {
    quarter: '2025 Q4',
    status: 'Planned',
    title: 'Physical Design & OpenLane ASIC Closure Integration',
    details: [
      'Automated floorplanning and standard cell macro placement checks',
      'Closed-loop DRC (Design Rule Check) and LVS (Layout vs Schematic) repair',
      'SkyWater 130nm and ASAP 7nm technology PDK automated sweeps',
      'Interactive GDSII layout stream viewer in Web Studio'
    ]
  },
  {
    quarter: '2026 Q1',
    status: 'Planned',
    title: 'Cloud-Distributed Regression Matrix & Multi-Agent Swarms',
    details: [
      'Distributed Slurm / Kubernetes simulation runner cluster',
      'Multi-agent role-playing verification: Designer Agent vs Adversarial Hacker Agent',
      'Full UVM / PyUVM VIP (Verification IP) automated generator for AXI4, PCIe & RISC-V',
      'Native IDE plugins for VS Code, Cursor, and Neovim'
    ]
  }
];
