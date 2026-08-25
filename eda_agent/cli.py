"""Production CLI for EDA-Agent supporting generate, lint, verify, triage-log, and UI."""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Optional
import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.syntax import Syntax
from rich.table import Table

from eda_agent import __version__
from eda_agent.analyzers.human_diagnostics import HumanDiagnosticsTranslator
from eda_agent.analyzers.sta_analyzer import STAAnalyzer
from eda_agent.core.agent_loop import AgentLoop
from eda_agent.generators.assertion_generator import AssertionGenerator
from eda_agent.generators.testbench_generator import TestbenchGenerator
from eda_agent.parsers.verilog_parser import VerilogParser
from eda_agent.tools.sim_runner import SimRunner
from eda_agent.tools.synthesis_checker import SynthesisChecker
from eda_agent.tools.verilator_linter import LintSeverity, VerilatorLinter

console = Console()


@click.group()
@click.version_option(__version__, "-v", "--version", prog_name="eda-agent")
def main() -> None:
    """EDA-Agent: AI-Assisted Open-Source EDA & VLSI Autonomous Verification Assistant."""
    pass


# -----------------------------------------------------------------------------
# COMMAND: generate
# -----------------------------------------------------------------------------
@main.command(name="generate")
@click.argument("file_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("-o", "--output", type=click.Path(dir_okay=False, path_type=Path), help="Output path for synthesized testbench")
@click.option("-t", "--top", help="Top-level module name if multiple modules exist in file")
def generate_cmd(file_path: Path, output: Optional[Path], top: Optional[str]) -> None:
    """Synthesize a complete cocotb testbench in Python for an RTL module."""
    modules = VerilogParser.parse_file(file_path)
    if not modules:
        console.print(f"[bold red]Error:[/bold red] No valid Verilog modules found in '{file_path}'.")
        sys.exit(1)

    spec = next((m for m in modules if m.name == top), modules[0])
    generator = TestbenchGenerator()
    console.print(f"[bold cyan]Synthesizing cocotb testbench for module:[/bold cyan] {spec.name}")

    source_code = file_path.read_text(encoding="utf-8")
    tb_code = generator.generate(spec, source_code=source_code)

    if output:
        output.write_text(tb_code, encoding="utf-8")
        console.print(f"[bold green]Saved testbench to:[/bold green] {output}")
    else:
        console.print(Panel(tb_code, title=f"Generated Testbench: test_{spec.name}.py", expand=False))


# -----------------------------------------------------------------------------
# COMMAND: lint
# -----------------------------------------------------------------------------
@main.command(name="lint")
@click.argument("file_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("-t", "--top", help="Top-level module name")
@click.option("-j", "--json-output", is_flag=True, help="Output structured diagnostics as JSON")
@click.option("--strict", is_flag=True, help="Treat warnings as errors")
def lint_cmd(file_path: Path, top: Optional[str], json_output: bool, strict: bool) -> None:
    """Run Verilator --lint-only -Wall and output structured diagnostics."""
    report = VerilatorLinter.lint_file(file_path, top_module=top)

    if json_output:
        click.echo(report.to_json(indent=2))
        if not report.success or (strict and report.total_warnings > 0):
            sys.exit(1)
        return

    # Header Panel
    status_style = "bold green" if report.success and (not strict or report.total_warnings == 0) else "bold red"
    status_text = "PASSED (Clean)" if report.total_errors == 0 and report.total_warnings == 0 else (
        "PASSED (with warnings)" if report.total_errors == 0 else "FAILED (Errors Detected)"
    )

    console.print(Panel(
        f"[bold]Target File:[/bold] {file_path.name}\n"
        f"[bold]Verilator Engine:[/bold] {'Active' if report.verilator_available else 'Static Linter Fallback'}\n"
        f"[bold]Status:[/bold] [{status_style}]{status_text}[/{status_style}]\n"
        f"[bold]Summary:[/bold] {report.total_errors} Error(s), {report.total_warnings} Warning(s)",
        title="Verilator Lint Report",
        expand=False
    ))

    if report.diagnostics:
        table = Table(title="Diagnostic Breakdown", show_header=True, header_style="bold cyan")
        table.add_column("Severity", width=10)
        table.add_column("Line:Col", width=10, justify="center")
        table.add_column("Code", width=16, style="yellow")
        table.add_column("Message & Suggested Fix", style="dim")

        for diag in report.diagnostics:
            sev_color = "red" if diag.severity == LintSeverity.ERROR else "yellow"
            pos_str = f"{diag.line or '-'}:{diag.column or '-'}"
            msg_text = diag.message
            if diag.suggestion:
                msg_text += f"\n[green]-> Fix:[/green] {diag.suggestion}"
            table.add_row(f"[{sev_color}]{diag.severity.value}[/{sev_color}]", pos_str, diag.code, msg_text)

        console.print(table)

    if not report.success or (strict and report.total_warnings > 0):
        sys.exit(1)


# -----------------------------------------------------------------------------
# COMMAND: synth
# -----------------------------------------------------------------------------
@main.command(name="synth")
@click.argument("file_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("-t", "--top", help="Top-level module name")
@click.option("-j", "--json-output", is_flag=True, help="Output structured synthesis report as JSON")
def synth_cmd(file_path: Path, top: Optional[str], json_output: bool) -> None:
    """Run Yosys gate-level synthesizability checks and cell statistics."""
    report = SynthesisChecker.check_file(file_path, top_module=top)

    if json_output:
        click.echo(report.to_json(indent=2))
        if not report.success:
            sys.exit(1)
        return

    status_color = "green" if report.success else "red"
    console.print(Panel(
        f"[bold]Target Module:[/bold] {report.top_module}\n"
        f"[bold]Yosys Synthesizability:[/bold] [{status_color}]{'SYNTHESIZABLE' if report.success else 'FAILED'}[/{status_color}]\n"
        f"[bold]Total Cells:[/bold] {report.cell_count} | [bold]DFF Flip-Flops:[/bold] {report.dff_count} | [bold]Inferred Latches:[/bold] {report.latch_count}\n"
        f"[bold]Logic Gates:[/bold] {report.gate_count} | [bold]Wires:[/bold] {report.wire_count}",
        title="Yosys Synthesis Report",
        expand=False
    ))

    if report.cells_by_type:
        table = Table(title=f"Cell Statistics ({report.top_module})", show_header=True, header_style="bold magenta")
        table.add_column("Cell Type", style="cyan")
        table.add_column("Count", justify="right", style="yellow")
        for cname, count in sorted(report.cells_by_type.items(), key=lambda x: -x[1]):
            table.add_row(cname, str(count))
        console.print(table)

    if report.non_synthesizable_constructs:
        console.print(Panel(
            "\n".join(f"• {c}" for c in report.non_synthesizable_constructs),
            title="[yellow]Non-Synthesizable Warnings[/yellow]",
            expand=False
        ))

    if not report.success:
        sys.exit(1)


# -----------------------------------------------------------------------------
# COMMAND: verify
# -----------------------------------------------------------------------------
@main.command(name="verify")
@click.argument("rtl_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("-d", "--dir", "sim_dir", default="examples/sim", type=click.Path(exists=True, file_okay=False, path_type=Path), help="Simulation working directory")
@click.option("-r", "--max-retries", default=3, type=int, help="Maximum autonomous repair attempts")
@click.option("--no-lint", is_flag=True, help="Skip Verilator linting stage")
@click.option("--no-synth", is_flag=True, help="Skip Yosys synthesis check stage")
def verify_cmd(rtl_file: Path, sim_dir: Path, max_retries: int, no_lint: bool, no_synth: bool) -> None:
    """Run closed-loop autonomous verification (generate -> simulate -> repair loop)."""
    console.print(f"[bold cyan]Starting autonomous verification loop for:[/bold cyan] {rtl_file}")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Executing verification and self-repair pipeline...", total=None)

        loop = AgentLoop()
        result = loop.run(
            rtl_file=rtl_file,
            sim_dir=sim_dir,
            run_linter=not no_lint,
            run_synth_check=not no_synth,
            max_retries=max_retries,
            clean=True,
        )
        progress.update(task, completed=True)

    itable = Table(title=f"Verification Loop History ({result.module_name})", show_header=True, header_style="bold")
    itable.add_column("Iteration", justify="center", width=10)
    itable.add_column("Action", style="cyan")
    itable.add_column("Simulation Status", style="bold")
    itable.add_column("Details", style="dim")

    for record in result.iterations:
        status_str = "[green]PASSED[/green]" if record.sim_result.success else "[red]FAILED[/red]"
        details = (
            f"Pass Rate: {record.sim_result.report.pass_rate_percent}%" if record.sim_result.report
            else (record.sim_result.diagnostics.error_summary if record.sim_result.diagnostics else "Error")
        )
        itable.add_row(str(record.iteration), record.action, status_str, details)

    console.print(itable)

    if result.success:
        console.print(Panel(
            f"[bold green]Verification SUCCESSFUL in {result.attempts} iteration(s)![/bold green]\n"
            f"Testbench saved to: [cyan]{result.testbench_path}[/cyan]",
            title="Verification Result",
            expand=False
        ))
    else:
        console.print(Panel(
            f"[bold red]Verification FAILED after {result.attempts} attempts.[/bold red]",
            title="Verification Result",
            expand=False
        ))
        sys.exit(1)


# -----------------------------------------------------------------------------
# COMMAND: triage-log
# -----------------------------------------------------------------------------
@main.command(name="triage-log")
@click.argument("log_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("-r", "--rtl", type=click.Path(exists=True, dir_okay=False, path_type=Path), help="Optional RTL file for signal and state cross-referencing")
@click.option("-p", "--clock-period", default=10.0, type=float, help="Clock period in ns for cycle calculations")
def triage_log_cmd(log_file: Path, rtl: Optional[Path], clock_period: float) -> None:
    """Triage and translate raw simulation error logs into digital hardware root-cause diagnostics."""
    log_content = log_file.read_text(encoding="utf-8", errors="replace")

    dut_spec = None
    if rtl:
        modules = VerilogParser.parse_file(rtl)
        if modules:
            dut_spec = modules[0]

    diagnosis = HumanDiagnosticsTranslator.translate(
        raw_log=log_content,
        dut_spec=dut_spec,
        clock_period_ns=clock_period,
    )

    console.print(Panel(
        f"[bold]Timestamp:[/bold] {diagnosis.timestamp_ns:.2f} ns "
        f"([bold]Clock Cycle:[/bold] #{diagnosis.clock_cycle if diagnosis.clock_cycle is not None else 'N/A'})\n"
        f"[bold]Context / State:[/bold] {diagnosis.fsm_state or 'N/A'}\n"
        f"[bold]Failing Check:[/bold] [red]{diagnosis.failing_assertion or diagnosis.raw_error[:120]}[/red]",
        title="Simulation Failure Triage",
        expand=False
    ))

    if diagnosis.violating_signals:
        table = Table(title="Signal Discrepancy Breakdown", show_header=True, header_style="bold cyan")
        table.add_column("Signal", style="cyan")
        table.add_column("Expected Value", style="green")
        table.add_column("Observed Value", style="red")

        for sig, data in diagnosis.violating_signals.items():
            exp = str(data.get("expected", "-"))
            act = str(data.get("actual", data.get("value", "-")))
            table.add_row(sig, exp, act)
        console.print(table)

    console.print(Panel(
        f"[bold]Summary:[/bold] {diagnosis.engineering_summary}\n\n"
        f"[bold]Hardware Root-Cause & Recommendation:[/bold]\n{diagnosis.hardware_diagnosis}",
        title="Digital Engineering Analysis",
        expand=False
    ))


# -----------------------------------------------------------------------------
# COMMAND: assert
# -----------------------------------------------------------------------------
@main.command(name="assert")
@click.argument("verilog_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("-s", "--spec", required=True, help="Plain-English timing or protocol requirement")
@click.option("-o", "--output", type=click.Path(dir_okay=False, path_type=Path), help="Output file to save assertions")
def assert_cmd(verilog_file: Path, spec: str, output: Optional[Path]) -> None:
    """Synthesize SystemVerilog Assertions (SVA) and Cocotb check coroutines from plain-English specifications."""
    modules = VerilogParser.parse_file(verilog_file)
    module_spec = modules[0] if modules else None

    generator = AssertionGenerator()
    console.print(f"[bold cyan]Synthesizing assertions for requirement:[/bold cyan] \"{spec}\"")

    generated = generator.generate(spec_text=spec, module_spec=module_spec)

    console.print(Panel(
        f"[bold]Target Module:[/bold] {module_spec.name if module_spec else 'Generic'}\n"
        f"[bold]Property Identifier:[/bold] [cyan]{generated.property_name}[/cyan]\n"
        f"[bold]Clock Domain:[/bold] {generated.clock_signal} | [bold]Reset:[/bold] {generated.reset_signal}\n"
        f"[bold]Signals Involved:[/bold] {', '.join(generated.signals_involved)}",
        title="Hardware Assertion Specification",
        expand=False
    ))

    # SVA Panel
    sva_syntax = Syntax(generated.sva_code, "verilog", theme="monokai", line_numbers=False)
    console.print(Panel(sva_syntax, title="Synthesizable SystemVerilog Assertion (SVA)", expand=False))

    # Cocotb Checker Panel
    cocotb_syntax = Syntax(generated.cocotb_code, "python", theme="monokai", line_numbers=False)
    console.print(Panel(cocotb_syntax, title="Cocotb Coroutine Assertion Checker", expand=False))

    if output:
        content = f"// SystemVerilog Assertions\n{generated.sva_code}\n\n# Cocotb Assertion Checker\n{generated.cocotb_code}\n"
        output.write_text(content, encoding="utf-8")
        console.print(f"[bold green]Saved assertions to:[/bold green] {output}")


# -----------------------------------------------------------------------------
# COMMAND: analyze-timing
# -----------------------------------------------------------------------------
@main.command(name="analyze-timing")
@click.argument("log_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def analyze_timing_cmd(log_file: Path) -> None:
    """Parse Static Timing Analysis (STA) logs and output structural RTL diff recommendations."""
    report = STAAnalyzer.parse_file(log_file)

    m_table = Table(title="Static Timing Analysis (STA) Summary", show_header=True, header_style="bold cyan")
    m_table.add_column("Timing Metric", style="dim", width=28)
    m_table.add_column("Value (ns)", justify="right")
    m_table.add_column("Status", style="bold")

    setup_status = "[bold green]MET[/bold green]" if not report.has_setup_violation else "[bold red]VIOLATED[/bold red]"
    hold_status = "[bold green]MET[/bold green]" if not report.has_hold_violation else "[bold red]VIOLATED[/bold red]"

    m_table.add_row("Worst Negative Slack (Setup WNS)", f"{report.wns_setup:.3f}", setup_status)
    m_table.add_row("Total Negative Slack (Setup TNS)", f"{report.tns_setup:.3f}", setup_status)
    m_table.add_row("Worst Hold Slack (Hold WNS)", f"{report.wns_hold:.3f}", hold_status)
    m_table.add_row("Total Hold Slack (Hold TNS)", f"{report.tns_hold:.3f}", hold_status)

    console.print(m_table)

    all_paths = report.setup_paths + report.hold_paths
    if all_paths:
        ptable = Table(title="Critical Timing Paths", show_header=True, header_style="bold magenta")
        ptable.add_column("Path Type", style="cyan", width=10)
        ptable.add_column("Startpoint", style="dim")
        ptable.add_column("Endpoint", style="dim")
        ptable.add_column("Slack (ns)", justify="right")
        ptable.add_column("Arrival (ns)", justify="right")
        ptable.add_column("Required (ns)", justify="right")
        ptable.add_column("Status", style="bold")

        for p in all_paths:
            p_status = "[bold red]VIOLATED[/bold red]" if p.is_violated else "[bold green]MET[/bold green]"
            slack_color = "red" if p.is_violated else "green"
            ptable.add_row(
                p.path_type.upper(),
                p.startpoint,
                p.endpoint,
                f"[{slack_color}]{p.slack:.3f}[/{slack_color}]",
                f"{p.arrival_time:.3f}",
                f"{p.required_time:.3f}",
                p_status
            )
        console.print(ptable)

    if report.recommendations:
        rec_text = "\n".join(report.recommendations)
        rec_title = "Timing Clean" if report.is_clean else "Architectural Timing Recommendations"
        rec_color = "green" if report.is_clean else "yellow"
        console.print(Panel(rec_text, title=f"[{rec_color}]{rec_title}[/{rec_color}]", expand=False))

    if report.actionable_diffs:
        console.print("\n[bold cyan]Actionable RTL Structural Diff Suggestions:[/bold cyan]")
        for diff in report.actionable_diffs:
            syntax = Syntax(diff, "diff", theme="monokai", line_numbers=False)
            console.print(Panel(syntax, title="Suggested Verilog Modification", expand=False))


# -----------------------------------------------------------------------------
# COMMAND: parse
# -----------------------------------------------------------------------------
@main.command(name="parse")
@click.argument("file_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def parse_cmd(file_path: Path) -> None:
    """Parse Verilog file and display extracted module interfaces, ports, and parameters."""
    modules = VerilogParser.parse_file(file_path)
    if not modules:
        console.print(f"[yellow]No modules found in {file_path}[/yellow]")
        return

    for mod in modules:
        console.print(Panel(f"[bold green]Module:[/bold green] [bold cyan]{mod.name}[/bold cyan]", expand=False))

        if mod.parameters:
            ptable = Table(title=f"Parameters ({mod.name})", show_header=True, header_style="bold magenta")
            ptable.add_column("Parameter Name", style="cyan")
            ptable.add_column("Default Value", style="yellow")
            for p in mod.parameters:
                ptable.add_row(p.name, p.default_value or "None")
            console.print(ptable)

        if mod.ports:
            table = Table(title=f"Ports ({mod.name})", show_header=True, header_style="bold blue")
            table.add_column("Port Name", style="cyan")
            table.add_column("Direction", style="magenta")
            table.add_column("Type", style="dim")
            table.add_column("Width", style="yellow")
            table.add_column("Clock Domain", style="cyan")
            table.add_column("Special", style="green")

            for port in mod.ports:
                specials = []
                if port.is_clock:
                    specials.append("CLOCK")
                if port.is_reset:
                    specials.append("RESET")
                table.add_row(
                    port.name,
                    port.direction.value if hasattr(port.direction, "value") else str(port.direction),
                    port.port_type,
                    f"[{port.width}]" if port.width != "1" else "1-bit",
                    port.clock_domain or "-",
                    ", ".join(specials) if specials else "-"
                )
            console.print(table)

        if mod.fsm_states:
            stable = Table(title=f"FSM States / Opcodes ({mod.name})", show_header=True, header_style="bold green")
            stable.add_column("Identifier", style="bold cyan")
            stable.add_column("Value / Encoding", style="yellow")
            stable.add_column("Type", style="dim")
            stable.add_column("Group", style="magenta")
            for st in mod.fsm_states:
                stable.add_row(st.name, st.value or "Auto", st.encoding_type, st.group or "-")
            console.print(stable)


# -----------------------------------------------------------------------------
# COMMAND: sim
# -----------------------------------------------------------------------------
@main.command(name="sim")
@click.option("-d", "--dir", "work_dir", default="examples/sim", type=click.Path(exists=True, file_okay=False, path_type=Path), help="Simulation directory")
@click.option("-t", "--toplevel", help="Override TOPLEVEL module name")
@click.option("-m", "--module", help="Override test MODULE name")
@click.option("-s", "--sim", "simulator", default="icarus", help="Simulator engine (icarus)")
@click.option("--waves/--no-waves", default=True, help="Enable VCD waveform generation")
@click.option("-c", "--clean", is_flag=True, help="Run make clean before simulation")
def sim_cmd(work_dir: Path, toplevel: Optional[str], module: Optional[str], simulator: str, waves: bool, clean: bool) -> None:
    """Run a cocotb simulation testbench and report results."""
    console.print(f"[bold cyan]Launching simulation in:[/bold cyan] {work_dir}")
    result = SimRunner.run(
        work_dir=work_dir,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        waves=waves,
        clean=clean,
    )

    if result.stdout:
        console.print(result.stdout, markup=False)

    if result.report:
        report = result.report
        rtable = Table(title=f"Test Results: {report.name}", show_header=True, header_style="bold")
        rtable.add_column("Test Case", style="cyan")
        rtable.add_column("Status", style="bold")
        rtable.add_column("Time (s)", justify="right")
        rtable.add_column("Sim Time (ns)", justify="right")

        for tc in report.test_cases:
            status = "[bold green]PASSED[/bold green]" if tc.passed else "[bold red]FAILED[/bold red]"
            rtable.add_row(tc.name, status, f"{tc.time:.3f}", f"{tc.sim_time_ns:.1f}")

        console.print(rtable)
        summary_color = "green" if report.failures == 0 and report.errors == 0 else "red"
        console.print(Panel(
            f"[{summary_color}]Total: {report.tests} | Passed: {report.passed} | Failed: {report.failures} | "
            f"Errors: {report.errors} | Pass Rate: {report.pass_rate_percent}%[/{summary_color}]",
            title="Summary",
            expand=False
        ))

    if not result.success:
        if result.stderr:
            console.print("[bold red]Errors:[/bold red]")
            console.print(result.stderr, markup=False)
        sys.exit(result.exit_code or 1)


# -----------------------------------------------------------------------------
# COMMAND: config
# -----------------------------------------------------------------------------
@main.command(name="config")
@click.option("-p", "--provider", help="LLM Provider ('ollama', 'openai_compatible', 'vllm', 'gemini', 'anthropic', 'openai', 'rule_based')")
@click.option("-m", "--model", help="Model name (e.g. 'deepseek-coder-v2:16b', 'qwen2.5-coder:32b', 'claude-3-5-sonnet')")
@click.option("-u", "--base-url", help="Base URL for LLM endpoint")
@click.option("-t", "--temperature", type=float, help="Sampling temperature (0.0 to 2.0)")
@click.option("-k", "--api-key", help="API key for authenticated endpoints")
@click.option("--timeout", type=int, help="Request timeout in seconds")
@click.option("--reset", is_flag=True, help="Reset configuration to defaults")
def config_cmd(
    provider: Optional[str],
    model: Optional[str],
    base_url: Optional[str],
    temperature: Optional[float],
    api_key: Optional[str],
    timeout: Optional[int],
    reset: bool,
) -> None:
    """View and update EDA-Agent LLM provider configuration and local model endpoints."""
    from eda_agent.config import EDAConfig, get_config_path, load_config, save_config, update_config

    if reset:
        default_cfg = EDAConfig()
        save_config(default_cfg)
        console.print("[bold green]Configuration reset to default settings.[/bold green]")
        cfg = default_cfg
    elif any(v is not None for v in (provider, model, base_url, temperature, api_key, timeout)):
        updates = {}
        if provider is not None:
            updates["provider"] = provider
        if model is not None:
            updates["model"] = model
        if base_url is not None:
            updates["base_url"] = base_url
        if temperature is not None:
            updates["temperature"] = temperature
        if api_key is not None:
            updates["api_key"] = api_key
        if timeout is not None:
            updates["timeout"] = timeout

        try:
            cfg = update_config(**updates)
            console.print(f"[bold green]Updated configuration successfully! Saved to {get_config_path()}[/bold green]")
        except Exception as e:
            console.print(f"[bold red]Configuration error:[/bold red] {e}")
            sys.exit(1)
    else:
        cfg = load_config()

    table = Table(title="EDA-Agent LLM & Provider Configuration", show_header=True, header_style="bold cyan")
    table.add_column("Setting", style="dim", width=22)
    table.add_column("Current Value", style="bold green")
    table.add_column("Source / Note", style="dim")

    table.add_row("Provider", cfg.provider, "Local Ollama" if cfg.provider == "ollama" else "Configured Provider")
    table.add_row("Model Name", cfg.model, "Target coding model")
    table.add_row("Base URL", cfg.base_url, "Local Endpoint" if "localhost" in cfg.base_url or "127.0.0.1" in cfg.base_url else "Remote Endpoint")
    table.add_row("Temperature", str(cfg.temperature), "Synthesis temperature")
    table.add_row("API Key", "********" if cfg.api_key else "(None / Local)", "Authentication")
    table.add_row("Timeout (s)", str(cfg.timeout), "HTTP connection timeout")
    table.add_row("Config File", str(get_config_path()), "Persistent storage")

    console.print(table)


# -----------------------------------------------------------------------------
# COMMAND: info
# -----------------------------------------------------------------------------
@main.command(name="info")
def info_cmd() -> None:
    """Display environment status, detected EDA binaries, and Python toolchain."""
    table = Table(title="EDA-Agent Environment Information", show_header=True, header_style="bold cyan")
    table.add_column("Component", style="dim", width=26)
    table.add_column("Status / Path", style="green")

    table.add_row("EDA-Agent Version", __version__)
    table.add_row("Python Version", sys.version.split()[0])
    table.add_row("Python Executable", sys.executable)

    # Icarus Verilog
    iverilog_bin = SimRunner.find_binary("iverilog")
    table.add_row("Icarus Verilog (iverilog)", iverilog_bin or "[red]Not found[/red]")

    vvp_bin = SimRunner.find_binary("vvp")
    table.add_row("VVP Runtime", vvp_bin or "[red]Not found[/red]")

    # Verilator
    verilator_bin = VerilatorLinter.find_binary("verilator")
    table.add_row("Verilator", verilator_bin or "[yellow]Not installed (using static fallback)[/yellow]")

    # Yosys
    yosys_bin = SynthesisChecker.find_binary("yosys")
    table.add_row("Yosys Synthesis Suite", yosys_bin or "[yellow]Not installed (using static fallback)[/yellow]")

    console.print(table)


# -----------------------------------------------------------------------------
# COMMAND: ui
# -----------------------------------------------------------------------------
@main.command(name="ui")
@click.option("-h", "--host", default="127.0.0.1", help="Host interface to bind")
@click.option("-p", "--port", default=8000, type=int, help="Port number for web server")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def ui_cmd(host: str, port: int, reload: bool) -> None:
    """Launch the EDA-Agent FastAPI local backend and interactive dashboard server."""
    import uvicorn

    console.print(Panel(
        f"[bold green]Starting EDA-Agent Web UI Server[/bold green]\n\n"
        f"  📡 API Endpoint:      [bold cyan]http://{host}:{port}[/bold cyan]\n"
        f"  📚 Interactive Docs:  [cyan]http://{host}:{port}/docs[/cyan]\n"
        f"  ⚡ WebSocket Stream:  [cyan]ws://{host}:{port}/ws/verify[/cyan]",
        title="EDA-Agent Local Backend",
        expand=False
    ))

    uvicorn.run("eda_agent.server.app:app", host=host, port=port, reload=reload, log_level="info")


# Export app alias for Click / Typer script entrypoints
app = main

if __name__ == "__main__":
    main()
