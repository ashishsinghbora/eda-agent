"""Lightweight VCD (Value Change Dump) parser and WaveDrom JSON formatter."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class VCDVariable(BaseModel):
    """VCD variable declaration descriptor."""
    id: str
    name: str
    size: int = 1
    var_type: str = "wire"
    scope: str = ""


class VCDData(BaseModel):
    """Extracted VCD signal transitions and timescale metadata."""
    timescale: str = "1ns"
    variables: Dict[str, VCDVariable] = Field(default_factory=dict, description="id -> VCDVariable")
    name_to_id: Dict[str, str] = Field(default_factory=dict, description="name -> id")
    timestamps: List[int] = Field(default_factory=list, description="Sorted list of time steps")
    # signal_name -> list of (timestamp, value_string)
    changes: Dict[str, List[Tuple[int, str]]] = Field(default_factory=dict)


class VCDParser:
    """Pure-Python Value Change Dump (VCD) parser."""

    @classmethod
    def parse_file(cls, file_path: str | Path) -> VCDData:
        """Parse VCD from file."""
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"VCD file not found: {file_path}")
        return cls.parse_string(path.read_text(encoding="utf-8", errors="replace"))

    @classmethod
    def parse_string(cls, content: str) -> VCDData:
        """Parse raw VCD text into VCDData model."""
        timescale = "1ns"
        variables: Dict[str, VCDVariable] = {}
        name_to_id: Dict[str, str] = {}
        changes: Dict[str, List[Tuple[int, str]]] = {}
        current_scope: List[str] = []
        timestamps: List[int] = []

        lines = content.splitlines()
        in_header = True
        current_time = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if in_header:
                if line.startswith("$timescale"):
                    # e.g. $timescale 1ns $end
                    m_ts = re.search(r'\$timescale\s+([^$]+)\$end', line)
                    if m_ts:
                        timescale = m_ts.group(1).strip()
                elif line.startswith("$scope"):
                    # e.g. $scope module dut $end
                    parts = line.split()
                    if len(parts) >= 3:
                        current_scope.append(parts[2])
                elif line.startswith("$upscope"):
                    if current_scope:
                        current_scope.pop()
                elif line.startswith("$var"):
                    # e.g. $var wire 1 ! clk $end or $var wire 8 " data [7:0] $end
                    parts = line.split()
                    if len(parts) >= 5:
                        var_type = parts[1]
                        size = int(parts[2])
                        var_id = parts[3]
                        var_name = parts[4]
                        scope_str = ".".join(current_scope)
                        full_name = f"{scope_str}.{var_name}" if scope_str else var_name

                        var = VCDVariable(
                            id=var_id,
                            name=var_name,
                            size=size,
                            var_type=var_type,
                            scope=scope_str
                        )
                        variables[var_id] = var
                        name_to_id[var_name] = var_id
                        changes[var_name] = []
                elif line.startswith("$enddefinitions"):
                    in_header = False
                continue

            # Simulation time updates
            if line.startswith("#"):
                try:
                    current_time = int(line[1:].strip())
                    if not timestamps or timestamps[-1] != current_time:
                        timestamps.append(current_time)
                except ValueError:
                    pass
                continue

            # Value changes
            # Vector: b10100101 ! or bX "
            if line.startswith("b") or line.startswith("B") or line.startswith("r") or line.startswith("R"):
                parts = line.split()
                if len(parts) >= 2:
                    raw_val = parts[0][1:]
                    var_id = parts[1]
                    if var_id in variables:
                        var_name = variables[var_id].name
                        changes[var_name].append((current_time, raw_val))
            # Scalar: 0!, 1!, x!, z!
            elif len(line) >= 2 and line[0] in ("0", "1", "x", "X", "z", "Z"):
                val = line[0].lower()
                var_id = line[1:]
                if var_id in variables:
                    var_name = variables[var_id].name
                    changes[var_name].append((current_time, val))

        return VCDData(
            timescale=timescale,
            variables=variables,
            name_to_id=name_to_id,
            timestamps=sorted(timestamps),
            changes=changes
        )

    @classmethod
    def to_wavedrom(
        cls,
        vcd_source: str | Path | VCDData,
        signals: Optional[List[str]] = None,
        max_cycles: int = 30,
        clock_signal: str = "clk",
    ) -> Dict[str, Any]:
        """Convert VCD signal transitions into a WaveDrom-compatible JSON structure."""
        if isinstance(vcd_source, VCDData):
            vcd = vcd_source
        elif isinstance(vcd_source, Path) or (isinstance(vcd_source, str) and (Path(vcd_source).is_file() or "\n" not in vcd_source)):
            vcd = cls.parse_file(vcd_source)
        else:
            vcd = cls.parse_string(str(vcd_source))

        # Identify signals to display
        available_signals = list(vcd.changes.keys())
        target_signals = signals or available_signals[:10]

        # Detect clock cycles from timestamps or clock changes
        clock_id = vcd.name_to_id.get(clock_signal) or next(
            (v.name for v in vcd.variables.values() if "clk" in v.name.lower() or "clock" in v.name.lower()),
            None
        )

        sample_times: List[int] = []
        if clock_id and clock_id in vcd.changes and vcd.changes[clock_id]:
            # Sample on rising edges or transitions
            clk_changes = vcd.changes[clock_id]
            for t, val in clk_changes:
                if val == "1" or val == "p":
                    sample_times.append(t)
        else:
            # Uniform sampling from timestamps
            step = max(1, len(vcd.timestamps) // max_cycles) if len(vcd.timestamps) > max_cycles else 1
            sample_times = vcd.timestamps[::step]

        if not sample_times:
            sample_times = list(range(0, 100 * max_cycles, 10))

        sample_times = sample_times[:max_cycles]

        wavedrom_signals: List[Dict[str, Any]] = []

        for sig_name in target_signals:
            if sig_name not in vcd.changes:
                continue

            var_id = vcd.name_to_id.get(sig_name)
            is_vector = False
            if var_id and var_id in vcd.variables:
                is_vector = vcd.variables[var_id].size > 1

            sig_changes = vcd.changes[sig_name]
            wave_chars: List[str] = []
            data_values: List[str] = []

            last_val: Optional[str] = None

            for t in sample_times:
                # Find most recent value at or before time t
                current_val = "x"
                for change_t, change_val in sig_changes:
                    if change_t <= t:
                        current_val = change_val
                    else:
                        break

                if "clk" in sig_name.lower():
                    # Clock representation in WaveDrom
                    wave_chars.append("p" if len(wave_chars) == 0 else ".")
                elif not is_vector:
                    # Single bit signal: 0, 1, x, z
                    char = current_val if current_val in ("0", "1", "x", "z") else "x"
                    if last_val is not None and char == last_val:
                        wave_chars.append(".")
                    else:
                        wave_chars.append(char)
                        last_val = char
                else:
                    # Vector bus: '='
                    fmt_val = cls._format_vector_value(current_val)
                    if last_val is not None and current_val == last_val:
                        wave_chars.append(".")
                    else:
                        wave_chars.append("=")
                        data_values.append(fmt_val)
                        last_val = current_val

            sig_entry: Dict[str, Any] = {
                "name": sig_name,
                "wave": "".join(wave_chars)
            }
            if data_values:
                sig_entry["data"] = data_values

            wavedrom_signals.append(sig_entry)

        return {
            "signal": wavedrom_signals,
            "head": {"text": "EDA-Agent Simulation Waveform"},
            "foot": {"tick": 0}
        }

    @staticmethod
    def _format_vector_value(val: str) -> str:
        """Format binary vector string into compact hexadecimal."""
        if not val or val.lower() in ("x", "z"):
            return val.upper()
        try:
            int_val = int(val, 2)
            return f"0x{int_val:X}"
        except ValueError:
            return val
