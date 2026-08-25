"""Master Autonomous Verification & Self-Repair Agent Loop."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from eda_agent.core.state_machine import AgentContext, AgentState, AgentStateMachine, StateTransition
from eda_agent.generators.testbench_generator import TestbenchGenerator
from eda_agent.parsers.verilog_parser import VerilogParser
from eda_agent.runners.simulation_runner import FailureType, SimulationDiagnostics, SimulationResult
from eda_agent.schemas import ModuleSpec
from eda_agent.tools.sim_runner import SimRunner
from eda_agent.tools.synthesis_checker import SynthesisChecker, SynthesisReport
from eda_agent.tools.verilator_linter import LintReport, VerilatorLinter

logger = logging.getLogger(__name__)


class IterationRecord(BaseModel):
    """Record of a single cycle in the verification and repair loop."""
    iteration: int
    action: str = Field(description="'INITIAL_GENERATION' or 'REPAIR_ATTEMPT_N'")
    code: str
    sim_result: SimulationResult


class AgentLoopResult(BaseModel):
    """Aggregated output of the master autonomous EDA agent loop."""
    success: bool
    module_name: str
    attempts: int
    lint_report: Optional[LintReport] = None
    synthesis_report: Optional[SynthesisReport] = None
    final_testbench_code: str
    testbench_path: str
    iterations: List[IterationRecord] = Field(default_factory=list)
    final_sim_result: SimulationResult
    state_transitions: List[StateTransition] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class AgentLoop:
    """Master agent loop coordinating linting, synthesis, test generation, and simulation repair."""

    def __init__(
        self,
        generator: Optional[TestbenchGenerator] = None,
        runner: Optional[SimRunner] = None,
    ):
        self.generator = generator or TestbenchGenerator()
        self.runner = runner or SimRunner()

    def run(
        self,
        rtl_file: str | Path,
        sim_dir: str | Path = "examples/sim",
        module_name: Optional[str] = None,
        run_linter: bool = True,
        run_synth_check: bool = True,
        max_retries: int = 3,
        clean: bool = True,
        simulator: str = "icarus",
        waves: bool = True,
        timeout: int = 120,
    ) -> AgentLoopResult:
        """Execute the end-to-end verification, lint, synthesis, and self-repair loop."""
        rtl_path = Path(rtl_file).resolve()
        sim_path = Path(sim_dir).resolve()

        if not rtl_path.is_file():
            raise FileNotFoundError(f"RTL source file not found: {rtl_path}")
        if not sim_path.is_dir():
            raise FileNotFoundError(f"Simulation directory not found: {sim_path}")

        context = AgentContext(
            rtl_file=str(rtl_path),
            target_module=module_name,
            max_retries=max_retries,
        )
        sm = AgentStateMachine(context)

        # 1. State: PARSING
        sm.transition_to(AgentState.PARSING, f"Parsing RTL module from {rtl_path.name}")
        modules = VerilogParser.parse_file(rtl_path)
        if not modules:
            sm.transition_to(AgentState.COMPLETED_FAILURE, "No valid RTL modules found in file")
            raise ValueError(f"No RTL modules parsed from {rtl_file}")

        spec = next((m for m in modules if m.name == module_name), modules[0])
        target_mod_name = spec.name
        context.target_module = target_mod_name
        context.module_spec = spec
        source_code = rtl_path.read_text(encoding="utf-8")
        context.source_code = source_code

        # 2. State: LINTING (Optional)
        lint_report: Optional[LintReport] = None
        if run_linter:
            sm.transition_to(AgentState.LINTING, f"Running Verilator lint check on {target_mod_name}")
            try:
                lint_report = VerilatorLinter.lint_file(rtl_path, top_module=target_mod_name)
            except Exception as e:
                logger.warning(f"Linter execution encountered warning: {e}")

        # 3. State: SYNTHESIS_CHECK (Optional)
        synthesis_report: Optional[SynthesisReport] = None
        if run_synth_check:
            sm.transition_to(AgentState.SYNTHESIS_CHECK, f"Running Yosys gate-level synthesis check on {target_mod_name}")
            try:
                synthesis_report = SynthesisChecker.check_file(rtl_path, top_module=target_mod_name)
            except Exception as e:
                logger.warning(f"Synthesis checker execution encountered warning: {e}")

        # 4. State: TESTBENCH_GENERATION
        sm.transition_to(AgentState.TESTBENCH_GENERATION, f"Synthesizing cocotb testbench for {target_mod_name}")
        testbench_filename = f"test_{target_mod_name}.py"
        testbench_file_path = sim_path / testbench_filename

        current_code = self.generator.generate(spec, source_code=source_code)
        context.testbench_code = current_code
        testbench_file_path.write_text(current_code, encoding="utf-8")

        # 5. State: SIMULATING
        sm.transition_to(AgentState.SIMULATING, f"Executing cocotb simulation in {sim_path.name}")
        iterations: List[IterationRecord] = []

        sim_res = self.runner.run(
            work_dir=sim_path,
            toplevel=target_mod_name,
            module=f"test_{target_mod_name}",
            simulator=simulator,
            waves=waves,
            clean=clean,
            timeout=timeout,
        )

        iterations.append(IterationRecord(
            iteration=1,
            action="INITIAL_GENERATION",
            code=current_code,
            sim_result=sim_res,
        ))

        attempts = 1

        # 6. Self-Repair Loop
        while not sim_res.success and attempts <= max_retries:
            sm.transition_to(AgentState.TRIAGING, f"Analyzing simulation failure (Attempt {attempts})")
            diagnostics = sim_res.diagnostics

            if diagnostics is None:
                diagnostics = SimulationDiagnostics(
                    failure_type=FailureType.UNKNOWN_FAILURE,
                    error_summary="Simulation exited with non-zero status.",
                    raw_stderr=sim_res.stderr,
                    raw_stdout=sim_res.stdout,
                )

            # Do not retry if simulator binary itself is missing on host
            if "was not found on PATH" in diagnostics.error_summary or "not found on system PATH" in diagnostics.error_summary:
                break

            attempts += 1
            sm.transition_to(AgentState.REPAIRING, f"Synthesizing repaired testbench (Attempt {attempts})")

            repaired_code = self.generator.repair(
                spec=spec,
                broken_code=current_code,
                diagnostics=diagnostics,
            )
            current_code = repaired_code
            context.testbench_code = current_code
            testbench_file_path.write_text(current_code, encoding="utf-8")

            sm.transition_to(AgentState.SIMULATING, f"Re-running simulation with repaired testbench (Attempt {attempts})")
            sim_res = self.runner.run(
                work_dir=sim_path,
                toplevel=target_mod_name,
                module=f"test_{target_mod_name}",
                simulator=simulator,
                waves=waves,
                clean=clean,
                timeout=timeout,
            )

            iterations.append(IterationRecord(
                iteration=attempts,
                action=f"REPAIR_ATTEMPT_{attempts - 1}",
                code=current_code,
                sim_result=sim_res,
            ))

        if sim_res.success:
            sm.transition_to(AgentState.COMPLETED_SUCCESS, f"Verification PASSED for module '{target_mod_name}'")
        else:
            sm.transition_to(AgentState.COMPLETED_FAILURE, f"Verification FAILED after {attempts} attempts")

        return AgentLoopResult(
            success=sim_res.success,
            module_name=target_mod_name,
            attempts=attempts,
            lint_report=lint_report,
            synthesis_report=synthesis_report,
            final_testbench_code=current_code,
            testbench_path=str(testbench_file_path),
            iterations=iterations,
            final_sim_result=sim_res,
            state_transitions=context.transitions,
        )


# Backward compatibility alias
VerificationLoop = AgentLoop
