"""Cocotb simulation runner wrapper."""

from __future__ import annotations

import os
import sys
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class SimConfig(BaseModel):
    """Configuration options for a simulation run."""
    toplevel: str = Field(description="Top-level Verilog/VHDL module name")
    module: str = Field(description="Python testbench module name (without .py)")
    verilog_sources: List[str] = Field(default_factory=list, description="Paths to RTL Verilog sources")
    simulator: str = Field(default="icarus", description="Simulator engine ('icarus', 'verilator', etc.)")
    sim_build: str = Field(default="sim_build", description="Build output directory")
    waves: bool = Field(default=True, description="Whether to dump VCD waveforms")
    work_dir: Optional[str] = Field(default=None, description="Working directory for simulation")
    extra_env: Dict[str, str] = Field(default_factory=dict, description="Extra environment variables")


class SimResult(BaseModel):
    """Result of a simulation execution."""
    success: bool
    exit_code: int
    duration_seconds: float
    stdout: str
    stderr: str
    results_xml_path: Optional[str] = None
    waveform_path: Optional[str] = None


class CocotbRunner:
    """Runner for invoking cocotb simulations via Makefile or subprocess."""

    @staticmethod
    def run_make(
        work_dir: str | Path,
        toplevel: Optional[str] = None,
        module: Optional[str] = None,
        simulator: str = "icarus",
        waves: bool = True,
        clean: bool = False,
        extra_env: Optional[Dict[str, str]] = None,
        timeout: int = 120,
    ) -> SimResult:
        """Run simulation in a directory containing a cocotb Makefile."""
        work_path = Path(work_dir).resolve()
        if not work_path.exists():
            raise FileNotFoundError(f"Simulation directory does not exist: {work_path}")

        env = os.environ.copy()
        # Add python environment bin and user's local bin to PATH
        py_bin_dir = str(Path(sys.executable).parent)
        user_local_bin = str(Path.home() / ".local" / "bin")
        current_path = env.get("PATH", "")
        env["PATH"] = os.pathsep.join((py_bin_dir, user_local_bin, current_path))

        env["SIM"] = simulator
        env["WAVES"] = "1" if waves else "0"
        if toplevel:
            env["TOPLEVEL"] = toplevel
            env["SIM_BUILD"] = f"sim_build_{toplevel}"
        if module:
            env["MODULE"] = module
        if extra_env:
            env.update(extra_env)

        start_time = time.time()
        try:
            if clean:
                subprocess.run(["make", "clean"], cwd=str(work_path), env=env, capture_output=True, text=True)

            proc = subprocess.run(
                ["make"],
                cwd=str(work_path),
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            duration = time.time() - start_time
            success = (proc.returncode == 0)

            # Look for results.xml in work_path and sim_build directories
            candidates = [
                work_path / "results.xml",
                work_path / f"sim_build_{toplevel}" / "results.xml" if toplevel else None,
                work_path / "sim_build" / "results.xml",
            ]
            results_xml = next((p for p in candidates if p and p.exists()), None)

            # Look for dump.vcd / dump.fst / waves
            vcd_candidates = [
                work_path / "dump.vcd",
                work_path / f"sim_build_{toplevel}" / "dump.vcd" if toplevel else None,
                work_path / "sim_build" / "dump.vcd",
            ]
            vcd_path = next((p for p in vcd_candidates if p and p.exists()), None)

            return SimResult(
                success=success,
                exit_code=proc.returncode,
                duration_seconds=round(duration, 3),
                stdout=proc.stdout,
                stderr=proc.stderr,
                results_xml_path=str(results_xml) if results_xml else None,
                waveform_path=str(vcd_path) if vcd_path else None
            )

        except subprocess.TimeoutExpired as exc:
            duration = time.time() - start_time
            return SimResult(
                success=False,
                exit_code=-1,
                duration_seconds=round(duration, 3),
                stdout=exc.stdout.decode() if exc.stdout else "",
                stderr=f"Simulation timed out after {timeout} seconds",
            )
