"""Autonomous closed-loop cocotb testbench synthesis, simulation, and repair."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field

from eda_agent.parsers.verilog_parser import VerilogParser
from eda_agent.runners.simulation_runner import SimulationResult, SimulationRunner
from eda_agent.schemas import ModuleSpec
from .testbench_generator import TestbenchGenerator


class IterationRecord(BaseModel):
    """Record of a single cycle in the verification and repair loop."""
    iteration: int
    action: str = Field(description="'INITIAL_GENERATION' or 'REPAIR_ATTEMPT_N'")
    code: str
    sim_result: SimulationResult


class VerificationLoopResult(BaseModel):
    """Aggregated output of the autonomous verification loop."""
    success: bool
    module_name: str
    attempts: int
    final_testbench_code: str
    testbench_path: str
    iterations: List[IterationRecord] = Field(default_factory=list)
    final_sim_result: SimulationResult


class VerificationLoop:
    """Orchestrates testbench generation, execution, diagnosis, and iterative repair."""

    def __init__(
        self,
        generator: Optional[TestbenchGenerator] = None,
        runner: Optional[SimulationRunner] = None
    ):
        self.generator = generator or TestbenchGenerator()
        self.runner = runner or SimulationRunner()

    def run(
        self,
        rtl_file: str | Path,
        sim_dir: str | Path,
        module_name: Optional[str] = None,
        max_retries: int = 3,
        clean: bool = True,
        simulator: str = "icarus",
        waves: bool = True,
        timeout: int = 120,
    ) -> VerificationLoopResult:
        """Run the end-to-end generate -> simulate -> diagnose -> repair loop."""
        rtl_path = Path(rtl_file).resolve()
        sim_path = Path(sim_dir).resolve()

        if not rtl_path.is_file():
            raise FileNotFoundError(f"RTL source file not found: {rtl_path}")
        if not sim_path.is_dir():
            raise FileNotFoundError(f"Simulation directory not found: {sim_path}")

        # 1. Parse RTL module
        modules = VerilogParser.parse_file(rtl_path)
        if not modules:
            raise ValueError(f"No RTL modules parsed from {rtl_file}")

        spec = next((m for m in modules if m.name == module_name), modules[0])
        target_mod_name = spec.name
        testbench_filename = f"test_{target_mod_name}.py"
        testbench_file_path = sim_path / testbench_filename
        source_code = rtl_path.read_text(encoding="utf-8")

        iterations: List[IterationRecord] = []

        # 2. Initial Generation (Iteration 0)
        current_code = self.generator.generate(spec, source_code=source_code)
        testbench_file_path.write_text(current_code, encoding="utf-8")

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
            sim_result=sim_res
        ))

        attempts = 1

        # 3. Closed-Loop Repair if simulation failed
        while not sim_res.success and attempts <= max_retries:
            attempts += 1
            diagnostics = sim_res.diagnostics

            # If no diagnostics were generated, create fallback
            if diagnostics is None:
                from eda_agent.runners.simulation_runner import FailureType, SimulationDiagnostics
                diagnostics = SimulationDiagnostics(
                    failure_type=FailureType.UNKNOWN_FAILURE,
                    error_summary="Simulation exited with non-zero code.",
                    raw_stderr=sim_res.stderr,
                    raw_stdout=sim_res.stdout
                )

            repaired_code = self.generator.repair(
                spec=spec,
                broken_code=current_code,
                diagnostics=diagnostics
            )
            current_code = repaired_code
            testbench_file_path.write_text(current_code, encoding="utf-8")

            # Re-execute simulation
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
                sim_result=sim_res
            ))

        return VerificationLoopResult(
            success=sim_res.success,
            module_name=target_mod_name,
            attempts=attempts,
            final_testbench_code=current_code,
            testbench_path=str(testbench_file_path),
            iterations=iterations,
            final_sim_result=sim_res
        )
