"""RTL Verilog / SystemVerilog Parser and Metadata Extractor."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from eda_agent.schemas import (
    FSMStateSpec,  # alias or direct
    ModuleSpec,
    ParameterSpec,
    PortDirection,
    PortSpec,
    StateSpec,
)


class VerilogParser:
    """Advanced RTL parser for extracting module interfaces, parameters, and FSM states."""

    # Patterns for clock and reset signal names
    CLOCK_PATTERN = re.compile(
        r'^(?:.*_)?(?:clk|clock|aclk|m_axis_aclk|s_axis_aclk|wclk|rclk|tx_clk|rx_clk)(?:_.*)?$',
        re.IGNORECASE
    )
    RESET_PATTERN = re.compile(
        r'^(?:.*_)?(?:rst|reset|rst_n|reset_n|aresetn|wrst_n|rrst_n|sync_rst|async_rst)(?:_.*)?$',
        re.IGNORECASE
    )

    # Patterns for FSM states / Opcodes
    FSM_PATTERN = re.compile(r'^(?:S_|STATE_|ST_|FSM_|IDLE|WAIT|READ|WRITE|EXEC|DONE|INIT)', re.IGNORECASE)
    OPCODE_PATTERN = re.compile(r'^(?:OP_|ALU_|CMD_|INST_|INSTR_)', re.IGNORECASE)

    @classmethod
    def strip_comments(cls, code: str) -> str:
        """Remove block and line comments while preserving newlines for accurate tracking."""
        # Remove multi-line /* ... */
        code = re.sub(r'/\*.*?\*/', lambda m: '\n' * m.group(0).count('\n'), code, flags=re.DOTALL)
        # Remove single-line // ...
        code = re.sub(r'//.*', '', code)
        return code

    @classmethod
    def parse_file(cls, file_path: str | Path) -> List[ModuleSpec]:
        """Parse all modules found in an RTL source file."""
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"RTL source file not found: {file_path}")

        content = path.read_text(encoding="utf-8")
        modules = cls.parse_string(content)
        for mod in modules:
            mod.source_file = str(path.resolve())
        return modules

    @classmethod
    def parse_string(cls, content: str) -> List[ModuleSpec]:
        """Parse module metadata from RTL code string."""
        clean = cls.strip_comments(content)
        modules: List[ModuleSpec] = []

        # Find each module ... endmodule block
        module_block_re = re.compile(
            r'\bmodule\s+([a-zA-Z_][a-zA-Z0-9_$]*)\s*(?:#\s*\((.*?)\))?\s*\((.*?)\)\s*;(.*?)'
            r'\bendmodule\b',
            re.DOTALL
        )

        for match in module_block_re.finditer(clean):
            mod_name = match.group(1).strip()
            header_params_raw = match.group(2)
            header_ports_raw = match.group(3)
            body_raw = match.group(4)

            # 1. Parse parameters (from both header and body)
            parameters = cls._parse_header_parameters(header_params_raw) if header_params_raw else []
            body_params, constants, fsm_states = cls._parse_body_declarations(body_raw)
            parameters.extend(body_params)

            # 2. Parse ports (ANSI header ports + non-ANSI body port declarations)
            ports = cls._parse_ports(header_ports_raw, body_raw)

            # 3. Associate clock domains
            cls._infer_clock_domains(ports)

            modules.append(ModuleSpec(
                name=mod_name,
                parameters=parameters,
                ports=ports,
                constants=constants,
                fsm_states=fsm_states
            ))

        return modules

    @classmethod
    def _parse_header_parameters(cls, params_str: str) -> List[ParameterSpec]:
        """Parse parameter declarations inside module #(...) parameter list."""
        params: List[ParameterSpec] = []
        # Split by comma considering nested parenthesis
        chunks = cls._split_top_level(params_str, ',')

        for item in chunks:
            item = item.strip()
            if not item:
                continue

            # Remove optional 'parameter' keyword and type
            item = re.sub(r'^\s*parameter\b', '', item).strip()

            # Optional type / width before param name e.g. [31:0] or integer
            m = re.match(r'^(?:(?:signed|integer|real|time|\[.*?\])\s+)?([a-zA-Z_][a-zA-Z0-9_$]*)\s*(?:=\s*(.*?))?$', item)
            if m:
                pname = m.group(1).strip()
                pval = m.group(2).strip() if m.group(2) else None
                params.append(ParameterSpec(name=pname, default_value=pval))
            else:
                if '=' in item:
                    pname, pval = item.split('=', 1)
                    params.append(ParameterSpec(name=pname.strip(), default_value=pval.strip()))
                else:
                    params.append(ParameterSpec(name=item.strip(), default_value=None))

        return params

    @classmethod
    def _parse_body_declarations(
        cls, body_str: str
    ) -> Tuple[List[ParameterSpec], List[StateSpec], List[StateSpec]]:
        """Parse parameter, localparam, and enum declarations from the module body."""
        body_params: List[ParameterSpec] = []
        constants: List[StateSpec] = []
        fsm_states: List[StateSpec] = []

        # Match parameter declarations inside body
        param_re = re.compile(
            r'\bparameter\b\s*(?:(?:signed|integer|real|\[.*?\])\s+)?(.*?);',
            re.DOTALL
        )
        for match in param_re.finditer(body_str):
            decl = match.group(1)
            for item in cls._split_top_level(decl, ','):
                item = item.strip()
                if '=' in item:
                    pname, pval = item.split('=', 1)
                    body_params.append(ParameterSpec(name=pname.strip(), default_value=pval.strip()))

        # Match localparam declarations
        localparam_re = re.compile(
            r'\blocalparam\b\s*(?:(?:signed|integer|\[.*?\])\s+)?(.*?);',
            re.DOTALL
        )
        for match in localparam_re.finditer(body_str):
            decl = match.group(1)
            for item in cls._split_top_level(decl, ','):
                item = item.strip()
                if not item:
                    continue
                if '=' in item:
                    cname, cval = item.split('=', 1)
                    cname = cname.strip()
                    cval = cval.strip()

                    # Determine group
                    if cls.FSM_PATTERN.search(cname):
                        group = "FSM_STATE"
                    elif cls.OPCODE_PATTERN.search(cname):
                        group = "OPCODE"
                    else:
                        group = "CONSTANT"

                    state_spec = StateSpec(
                        name=cname,
                        value=cval,
                        encoding_type="localparam",
                        group=group
                    )
                    constants.append(state_spec)
                    if group in ("FSM_STATE", "OPCODE"):
                        fsm_states.append(state_spec)

        # Match SystemVerilog (typedef) enum [type] [range] { ... } [name];
        enum_re = re.compile(
            r'\b(?:typedef\s+)?enum\b(?:\s+[a-zA-Z_0-9$]+)?(?:\s*\[.*?\])?\s*\{(.*?)\}\s*([a-zA-Z_][a-zA-Z0-9_$]*)?\s*;',
            re.DOTALL
        )
        for match in enum_re.finditer(body_str):
            enum_body = match.group(1)
            enum_type_name = match.group(2).strip() if match.group(2) else "enum_t"

            for item in cls._split_top_level(enum_body, ','):
                item = item.strip()
                if not item:
                    continue
                if '=' in item:
                    sname, sval = item.split('=', 1)
                    sname = sname.strip()
                    sval = sval.strip()
                else:
                    sname = item.strip()
                    sval = None

                state_spec = StateSpec(
                    name=sname,
                    value=sval,
                    encoding_type="enum",
                    group="FSM_STATE"
                )
                constants.append(state_spec)
                fsm_states.append(state_spec)

        return body_params, constants, fsm_states

    @classmethod
    def _parse_ports(cls, header_ports_raw: str, body_raw: str) -> List[PortSpec]:
        """Parse ports handling both ANSI-style and non-ANSI style declarations."""
        ports: List[PortSpec] = []
        port_names_in_order: List[str] = []

        # Split ANSI header ports
        chunks = cls._split_top_level(header_ports_raw, ',')

        # Check if header contains ANSI style (has direction keywords like input/output/inout)
        has_ansi = any(re.search(r'\b(input|output|inout)\b', chunk) for chunk in chunks)

        if has_ansi:
            for chunk in chunks:
                chunk = chunk.strip()
                if not chunk:
                    continue

                m = re.match(
                    r'^(input|output|inout)\s+(?:(wire|reg|logic)\s+)?(?:(signed)\s+)?(?:\[(.*?)\]\s+)?([a-zA-Z_][a-zA-Z0-9_$]*)$',
                    chunk
                )
                if m:
                    direction_str, ptype, signed_kw, width_range, name = m.groups()
                    width = width_range.strip() if width_range else "1"
                    is_clk = bool(cls.CLOCK_PATTERN.match(name))
                    is_rst = bool(cls.RESET_PATTERN.match(name))
                    direction = PortDirection(direction_str.lower())

                    ports.append(PortSpec(
                        name=name,
                        direction=direction,
                        port_type=ptype or "wire",
                        width=width,
                        is_clock=is_clk,
                        is_reset=is_rst
                    ))
                else:
                    # Fallback for multi-word or simplified declarations
                    name = chunk.split()[-1]
                    dir_m = re.search(r'\b(input|output|inout)\b', chunk)
                    dir_val = PortDirection(dir_m.group(1).lower()) if dir_m else PortDirection.INPUT
                    width_m = re.search(r'\[(.*?)\]', chunk)
                    width_val = width_m.group(1).strip() if width_m else "1"

                    ports.append(PortSpec(
                        name=name,
                        direction=dir_val,
                        width=width_val,
                        is_clock=bool(cls.CLOCK_PATTERN.match(name)),
                        is_reset=bool(cls.RESET_PATTERN.match(name))
                    ))
        else:
            # Non-ANSI style: header contains just port names `(clk, rst, a, b)`
            # Body contains `input clk;`, `input [7:0] a;`, `output reg [7:0] b;`
            for chunk in chunks:
                pname = chunk.strip()
                if pname:
                    port_names_in_order.append(pname)

            # Find port declarations in body
            port_decl_re = re.compile(
                r'\b(input|output|inout)\s+(?:(wire|reg|logic)\s+)?(?:(signed)\s+)?(?:\[(.*?)\]\s+)?(.*?);',
                re.DOTALL
            )
            body_ports_dict: Dict[str, PortSpec] = {}

            for match in port_decl_re.finditer(body_raw):
                direction_str, ptype, signed_kw, width_range, names_str = match.groups()
                direction = PortDirection(direction_str.lower())
                width = width_range.strip() if width_range else "1"

                for name_chunk in cls._split_top_level(names_str, ','):
                    name = name_chunk.strip()
                    if not name:
                        continue
                    body_ports_dict[name] = PortSpec(
                        name=name,
                        direction=direction,
                        port_type=ptype or "wire",
                        width=width,
                        is_clock=bool(cls.CLOCK_PATTERN.match(name)),
                        is_reset=bool(cls.RESET_PATTERN.match(name))
                    )

            # Build in original declaration order
            for name in port_names_in_order:
                if name in body_ports_dict:
                    ports.append(body_ports_dict[name])
                else:
                    ports.append(PortSpec(
                        name=name,
                        direction=PortDirection.INPUT,
                        width="1",
                        is_clock=bool(cls.CLOCK_PATTERN.match(name)),
                        is_reset=bool(cls.RESET_PATTERN.match(name))
                    ))

        return ports

    @classmethod
    def _infer_clock_domains(cls, ports: List[PortSpec]) -> None:
        """Infer clock domain associations for ports (e.g. wclk domain vs rclk domain)."""
        clock_ports = [p for p in ports if p.is_clock]

        if not clock_ports:
            return

        if len(clock_ports) == 1:
            clk_name = clock_ports[0].name
            for p in ports:
                if not p.is_clock:
                    p.clock_domain = clk_name
            return

        # Multi-clock domain inference based on prefixes (e.g. wclk/wrst/wdata -> wclk, rclk/rrst/rdata -> rclk)
        for clk in clock_ports:
            clk_prefix = clk.name.replace("clk", "").replace("clock", "").strip("_")
            for p in ports:
                if p.is_clock:
                    continue
                if clk_prefix and (p.name.startswith(clk_prefix) or f"_{clk_prefix}" in p.name):
                    p.clock_domain = clk.name

    @staticmethod
    def _split_top_level(s: str, delimiter: str = ',') -> List[str]:
        """Split a string by delimiter without splitting inside brackets or parentheses."""
        parts: List[str] = []
        current: List[str] = []
        depth = 0

        for char in s:
            if char in '([{':
                depth += 1
                current.append(char)
            elif char in ')]}':
                depth = max(0, depth - 1)
                current.append(char)
            elif char == delimiter and depth == 0:
                parts.append(''.join(current).strip())
                current = []
            else:
                current.append(char)

        if current:
            parts.append(''.join(current).strip())

        return parts


# Backwards compatibility alias
RTLParser = VerilogParser
ModuleInfo = ModuleSpec
PortInfo = PortSpec
ParameterInfo = ParameterSpec
