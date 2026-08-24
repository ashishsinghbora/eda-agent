"""Integration tests for FastAPI local backend, UI static bundle, and VCD WaveDrom parser."""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from eda_agent.server.app import app
from eda_agent.parsers.vcd_parser import VCDParser, VCDData


def test_vcd_parser_and_wavedrom():
    """Verify VCD parser and WaveDrom formatting."""
    sample_vcd = """$date
   Tue Aug 25 04:00:00 2026
$end
$version
   Icarus Verilog
$end
$timescale
   1ns
$end
$scope module dut $end
$var wire 1 ! clk $end
$var wire 1 " rst_n $end
$var wire 8 # data [7:0] $end
$upscope $end
$enddefinitions $end
#0
0!
0"
b00000000 #
#10
1!
#20
0!
1"
b10101010 #
#30
1!
#40
0!
b01010101 #
"""

    vcd = VCDParser.parse_string(sample_vcd)
    assert isinstance(vcd, VCDData)
    assert vcd.timescale == "1ns"
    assert "clk" in vcd.changes
    assert "rst_n" in vcd.changes
    assert "data" in vcd.changes
    assert len(vcd.timestamps) == 5

    # Convert to WaveDrom
    wd = VCDParser.to_wavedrom(vcd, max_cycles=10)
    assert "signal" in wd
    assert len(wd["signal"]) >= 3

    sig_names = [s["name"] for s in wd["signal"]]
    assert "clk" in sig_names
    assert "rst_n" in sig_names
    assert "data" in sig_names

    # Check vector data hex formatting
    data_entry = next(s for s in wd["signal"] if s["name"] == "data")
    assert "data" in data_entry
    assert "0xAA" in data_entry["data"] or "0x55" in data_entry["data"]


def test_serve_ui_index():
    """Verify GET / serves the Web UI bundle."""
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "EDA-Agent" in resp.text
    assert "WaveDrom" in resp.text
    assert "Hardware Schematic" in resp.text


def test_api_status():
    """Verify GET /api/status endpoint."""
    client = TestClient(app)
    resp = client.get("/api/status")

    assert resp.status_code == 200
    data = resp.json()
    assert "version" in data
    assert "python_version" in data
    assert "llm_provider" in data
    assert "llm_model" in data


def test_api_examples():
    """Verify GET /api/examples endpoint."""
    client = TestClient(app)
    resp = client.get("/api/examples")
    assert resp.status_code == 200
    data = resp.json()
    assert "alu_8bit.v" in data
    assert "fifo_async.v" in data


def test_api_parse_code():
    """Verify POST /api/parse with Verilog source string."""
    client = TestClient(app)
    code = """
    module simple_counter #(parameter WIDTH = 8) (
        input  wire             clk,
        input  wire             rst_n,
        output reg  [WIDTH-1:0] count
    );
    endmodule
    """
    resp = client.post("/api/parse", json={"code": code})
    assert resp.status_code == 200
    modules = resp.json()
    assert len(modules) == 1
    assert modules[0]["name"] == "simple_counter"
    assert len(modules[0]["ports"]) == 3
    assert len(modules[0]["parameters"]) == 1


def test_api_parse_file():
    """Verify POST /api/parse with file_path."""
    client = TestClient(app)
    resp = client.post("/api/parse", json={"file_path": "examples/rtl/alu_8bit.v"})
    assert resp.status_code == 200
    modules = resp.json()
    assert len(modules) == 1
    assert modules[0]["name"] == "alu_8bit"


def test_api_generate_test():
    """Verify POST /api/generate-test synthesizes testbench and assertions."""
    client = TestClient(app)
    alu_path = Path("examples/rtl/alu_8bit.v")
    code = alu_path.read_text(encoding="utf-8")

    resp = client.post("/api/generate-test", json={
        "code": code,
        "module_name": "alu_8bit",
        "spec": "ready drops low when valid is asserted and fifo is full"
    })

    assert resp.status_code == 200
    data = resp.json()
    assert "testbench" in data
    assert "@cocotb.test()" in data["testbench"]
    assert "module_spec" in data
    assert data["module_spec"]["name"] == "alu_8bit"
    assert "sva_assertion" in data
    assert data["sva_assertion"] is not None


def test_api_diagnose():
    """Verify POST /api/diagnose translates simulator log into digital engineering terms."""
    client = TestClient(app)
    raw_log = "1240.00ns ERROR AssertionError: Op 0: Expected result=0x5, got 0x0"
    resp = client.post("/api/diagnose", json={"log": raw_log})
    assert resp.status_code == 200
    data = resp.json()
    assert data["timestamp_ns"] == 1240.0
    assert data["clock_cycle"] == 124
    assert "result" in data["violating_signals"]


def test_api_timing():
    """Verify POST /api/timing parses STA timing report."""
    client = TestClient(app)
    log_text = """
    Worst Negative Slack (WNS): -0.45 ns
    Total Negative Slack (TNS): -2.85 ns
    """
    resp = client.post("/api/timing", json={"log": log_text})
    assert resp.status_code == 200
    data = resp.json()
    assert data["wns_setup"] == -0.45
    assert data["tns_setup"] == -2.85
    assert data["has_setup_violation"] is True


def test_websocket_verify():
    """Verify WebSocket /ws/verify real-time verification streaming."""
    client = TestClient(app)
    with client.websocket_connect("/ws/verify") as ws:
        # Send verification request for alu_8bit
        ws.send_json({
            "rtl_file": "examples/rtl/alu_8bit.v",
            "module_name": "alu_8bit",
            "max_retries": 2
        })

        events = []
        # Collect streamed events until complete
        for _ in range(10):
            msg = ws.receive_json()
            events.append(msg)
            if msg.get("event") in ("complete", "error"):
                break

        event_types = [e.get("event") for e in events]
        assert "start" in event_types
        assert "iteration" in event_types
        assert "complete" in event_types

        complete_event = next(e for e in events if e.get("event") == "complete")
        assert complete_event["success"] is True
