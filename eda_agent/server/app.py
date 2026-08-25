"""FastAPI Local Backend for EDA-Agent Web UI and Real-Time Verification Streaming."""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from eda_agent import __version__
from eda_agent.analyzers.human_diagnostics import HardwareFailureDiagnosis, HumanDiagnosticsTranslator
from eda_agent.analyzers.sta_analyzer import STAAnalyzer, TimingReport
from eda_agent.config import load_config
from eda_agent.generators.assertion_generator import AssertionGenerator
from eda_agent.generators.repair_loop import VerificationLoop
from eda_agent.generators.testbench_generator import TestbenchGenerator
from eda_agent.parsers.vcd_parser import VCDParser
from eda_agent.parsers.verilog_parser import VerilogParser
from eda_agent.runners.simulation_runner import SimulationRunner
from eda_agent.schemas import ModuleSpec


STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(
    title="EDA-Agent Local Backend",
    version=__version__,
    description="Local EDA verification, waveform streaming, and testbench synthesis engine",
)

# Allow local frontend cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request/Response Models ---

class StatusResponse(BaseModel):
    version: str
    python_version: str
    iverilog: Optional[str]
    vvp: Optional[str]
    verilator: Optional[str]
    llm_provider: str
    llm_model: str
    llm_base_url: str


class ParseRequest(BaseModel):
    code: Optional[str] = Field(default=None, description="Verilog RTL source code")
    file_path: Optional[str] = Field(default=None, description="Path to Verilog file on server")


class GenerateTestRequest(BaseModel):
    code: str = Field(description="Verilog source code")
    module_name: Optional[str] = Field(default=None, description="Target module name")
    spec: Optional[str] = Field(default=None, description="Natural language specification or requirement")


class GenerateTestResponse(BaseModel):
    testbench: str
    module_spec: ModuleSpec
    sva_assertion: Optional[str] = None


class DiagnoseRequest(BaseModel):
    log: str = Field(description="Raw simulator error log or stack trace")
    code: Optional[str] = Field(default=None, description="Optional RTL code for port/state reference")


class TimingRequest(BaseModel):
    log: str = Field(description="Raw OpenROAD / Yosys timing log")


class ProviderUpdateRequest(BaseModel):
    provider: str = Field(description="LLM provider name")


# --- HTTP Endpoints ---

@app.get("/api/status", response_model=StatusResponse)
async def get_status() -> StatusResponse:
    """Return environment toolchain and local LLM configuration."""
    cfg = load_config()
    local_bin = str(Path.home() / ".local" / "bin")
    project_tool_bin = str(Path(__file__).resolve().parents[2] / ".tools" / "iverilog" / "bin")
    search_path = os.pathsep.join((project_tool_bin, local_bin, os.environ.get("PATH", "")))
    iverilog_bin = shutil.which("iverilog", path=search_path)
    vvp_bin = shutil.which("vvp", path=search_path)
    verilator_bin = shutil.which("verilator")

    return StatusResponse(
        version=__version__,
        python_version=sys.version.split()[0],
        iverilog=iverilog_bin,
        vvp=vvp_bin,
        verilator=verilator_bin,
        llm_provider=cfg.provider,
        llm_model=cfg.model,
        llm_base_url=cfg.base_url
    )


@app.post("/api/config/provider", response_model=StatusResponse)
async def update_provider(req: ProviderUpdateRequest) -> StatusResponse:
    """Persist the selected LLM provider and return refreshed environment status."""
    allowed = {"ollama", "openai_compatible", "gemini", "openai", "rule_based"}
    if req.provider not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {req.provider}")
    from eda_agent.config import update_config
    update_config(provider=req.provider)
    return await get_status()


@app.get("/api/examples")
async def get_examples() -> Dict[str, Dict[str, str]]:
    """Return bundled RTL examples."""
    examples = {}
    alu_path = Path("examples/rtl/alu_8bit.v")
    fifo_path = Path("examples/rtl/fifo_async.v")

    if alu_path.is_file():
        examples["alu_8bit.v"] = {
            "name": "alu_8bit",
            "code": alu_path.read_text(encoding="utf-8"),
            "spec_preset": "opcode 0 is ADD, result equals A + B with zero flag"
        }

    if fifo_path.is_file():
        examples["fifo_async.v"] = {
            "name": "fifo_async",
            "code": fifo_path.read_text(encoding="utf-8"),
            "spec_preset": "ready drops low when valid is asserted and fifo is full"
        }

    return examples


@app.post("/api/parse", response_model=List[ModuleSpec])
async def parse_verilog(req: ParseRequest) -> List[ModuleSpec]:
    """Parse Verilog source code or file and return extracted ModuleSpec list."""
    if req.code:
        modules = VerilogParser.parse_string(req.code)
    elif req.file_path:
        p = Path(req.file_path)
        if not p.is_file():
            raise HTTPException(status_code=404, detail=f"File not found: {req.file_path}")
        modules = VerilogParser.parse_file(p)
    else:
        raise HTTPException(status_code=400, detail="Either 'code' or 'file_path' must be provided.")

    return modules


@app.post("/api/generate-test", response_model=GenerateTestResponse)
async def generate_testbench(req: GenerateTestRequest) -> GenerateTestResponse:
    """Synthesize cocotb testbench and optional assertions from RTL and specs."""
    modules = VerilogParser.parse_string(req.code)
    if not modules:
        raise HTTPException(status_code=400, detail="No valid Verilog module found in provided code.")

    # Match target module or use first
    if req.module_name:
        spec = next((m for m in modules if m.name == req.module_name), modules[0])
    else:
        spec = modules[0]

    generator = TestbenchGenerator()
    tb_code = generator.generate(spec, source_code=req.code)

    sva_code = None
    if req.spec:
        assert_gen = AssertionGenerator()
        gen_assert = assert_gen.generate(spec_text=req.spec, module_spec=spec)
        sva_code = gen_assert.sva_code
        checker_code = gen_assert.cocotb_code
        if "@cocotb.test" not in checker_code and "module dut_module" not in checker_code:
            tb_code += f"\n\n# --- Natural Language Assertion Checker ---\n{checker_code}\n"

    return GenerateTestResponse(
        testbench=tb_code,
        module_spec=spec,
        sva_assertion=sva_code
    )


@app.post("/api/diagnose", response_model=HardwareFailureDiagnosis)
async def diagnose_failure(req: DiagnoseRequest) -> HardwareFailureDiagnosis:
    """Translate raw simulator log into hardware engineering terms."""
    dut_spec = None
    if req.code:
        mods = VerilogParser.parse_string(req.code)
        if mods:
            dut_spec = mods[0]

    return HumanDiagnosticsTranslator.translate(raw_log=req.log, dut_spec=dut_spec)


@app.post("/api/timing", response_model=TimingReport)
async def analyze_timing_report(req: TimingRequest) -> TimingReport:
    """Parse STA timing report and return critical paths, WNS/TNS, and diffs."""
    return STAAnalyzer.parse_string(req.log)


# --- WebSocket Verification Streaming Endpoint ---

@app.websocket("/ws/verify")
async def websocket_verify(websocket: WebSocket) -> None:
    """Stream live compiler logs, simulation execution, pass/fail status, and WaveDrom data."""
    await websocket.accept()

    try:
        data_text = await websocket.receive_text()
        data = json.loads(data_text)

        rtl_code = data.get("rtl_code")
        rtl_file = data.get("rtl_file")
        module_name = data.get("module_name", "dut")
        max_retries = int(data.get("max_retries", 3))

        await websocket.send_json({
            "event": "start",
            "message": f"Starting autonomous verification loop for module '{module_name}'",
            "module_name": module_name
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            if rtl_code:
                verilog_path = tmp_path / f"{module_name}.v"
                verilog_path.write_text(rtl_code, encoding="utf-8")
            elif rtl_file and Path(rtl_file).is_file():
                verilog_path = Path(rtl_file)
            else:
                verilog_path = Path("examples/rtl/alu_8bit.v")

            sim_dir = Path("examples/sim")

            loop = VerificationLoop()
            result = loop.run(
                rtl_file=verilog_path,
                sim_dir=sim_dir,
                max_retries=max_retries,
                clean=True
            )

            # Stream each iteration record
            for record in result.iterations:
                diagnostic_text = ""
                if record.sim_result.diagnostics:
                    diagnostic_text = record.sim_result.diagnostics.error_summary
                iteration_output = record.sim_result.stdout[-1000:] if record.sim_result.stdout else ""
                if diagnostic_text:
                    iteration_output = f"{iteration_output}\n{diagnostic_text}".strip()
                await websocket.send_json({
                    "event": "iteration",
                    "iteration": record.iteration,
                    "action": record.action,
                    "success": record.sim_result.success,
                    "pass_rate": record.sim_result.report.pass_rate_percent if record.sim_result.report else 0.0,
                    "stdout": iteration_output,
                })

            # Check if VCD waveform was produced and format as WaveDrom
            vcd_files = list(sim_dir.glob(f"sim_build_{result.module_name}/*.vcd")) + list(sim_dir.glob("*.vcd"))
            wavedrom_data = None
            if vcd_files:
                try:
                    wavedrom_data = VCDParser.to_wavedrom(vcd_files[0], max_cycles=20)
                    await websocket.send_json({
                        "event": "waveform",
                        "wavedrom": wavedrom_data
                    })
                except Exception:
                    pass

            await websocket.send_json({
                "event": "complete",
                "success": result.success,
                "attempts": result.attempts,
                "testbench_path": str(result.testbench_path),
                "summary": f"Verification {'PASSED' if result.success else 'FAILED'} in {result.attempts} attempt(s)"
            })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({
            "event": "error",
            "message": str(e)
        })
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


# --- Serve Static UI Bundle ---

if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    async def serve_index():
        index_file = STATIC_DIR / "index.html"
        if index_file.is_file():
            return FileResponse(index_file)
        return {"message": "EDA-Agent API is running. Build UI static bundle in eda_agent/server/static/"}
