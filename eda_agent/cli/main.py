"""Command Line Interface for eda-agent."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.syntax import Syntax
from rich.table import Table

from eda_agent.analyzers.coverage_analyzer import ResultsAnalyzer
from eda_agent.analyzers.sta_analyzer import STAAnalyzer
from eda_agent.parsers.verilog_parser import VerilogParser
from eda_agent.runners.simulation_runner import SimulationRunner

app = typer.Typer(
    name="eda-agent",
    help="AI-assisted Open-Source EDA Verification & Testbench Framework",
    add_completion=False
)
console = Console()


@app.command()
def info() -> None:
    """Display environment status, detected simulators, and Python toolchain."""
    table = Table(title="EDA-Agent Environment Information", show_header=True, header_style="bold cyan")
    table.add_column("Component", style="dim", width=24)
    table.add_column("Status / Path", style="green")

    # Python
    table.add_row("Python Version", sys.version.split()[0])
    table.add_row("Python Executable", sys.executable)

    # Icarus Verilog
    iverilog_bin = shutil.which("iverilog") or shutil.which("iverilog", path=f"{Path.home()}/.local/bin:{shutil.which('iverilog') or ''}")
    table.add_row("Icarus Verilog (iverilog)", iverilog_bin or "[red]Not found[/red]")

    vvp_bin = shutil.which("vvp") or shutil.which("vvp", path=f"{Path.home()}/.local/bin:{shutil.which('vvp') or ''}")
    table.add_row("VVP Runtime", vvp_bin or "[red]Not found[/red]")

    # Verilator
    verilator_bin = shutil.which("verilator")
    table.add_row("Verilator", verilator_bin or "[yellow]Not installed[/yellow]")

    console.print(table)


@app.command()
def parse(
    file_path: str = typer.Argument(..., help="Path to Verilog file (.v/.sv)"),
) -> None:
    """Parse Verilog file and display extracted module interfaces, ports, and parameters."""
    path = Path(file_path)
    if not path.exists():
        console.print(f"[bold red]Error:[/bold red] File '{file_path}' does not exist.")
        raise typer.Exit(code=1)

    try:
        modules = VerilogParser.parse_file(path)
    except Exception as e:
        console.print(f"[bold red]Failed to parse file:[/bold red] {e}")
        raise typer.Exit(code=1)

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


@app.command()
def sim(
    work_dir: str = typer.Option("examples/sim", "--dir", "-d", help="Simulation working directory"),
    toplevel: Optional[str] = typer.Option(None, "--toplevel", "-t", help="Override TOPLEVEL module name"),
    module: Optional[str] = typer.Option(None, "--module", "-m", help="Override test MODULE name"),
    simulator: str = typer.Option("icarus", "--sim", "-s", help="Simulator (e.g. icarus)"),
    waves: bool = typer.Option(True, "--waves/--no-waves", help="Enable VCD waveform generation"),
    clean: bool = typer.Option(False, "--clean", "-c", help="Run make clean before executing simulation"),
) -> None:
    """Run a cocotb simulation testbench and report results."""
    console.print(f"[bold cyan]Launching simulation in:[/bold cyan] {work_dir}")
    result = SimulationRunner.run(
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
        raise typer.Exit(code=result.exit_code or 1)


@app.command()
def generate(
    file_path: str = typer.Argument(..., help="Path to RTL Verilog file"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output path for generated testbench"),
) -> None:
    """Synthesize a new cocotb testbench for an RTL module."""
    from eda_agent.generators.testbench_generator import TestbenchGenerator

    path = Path(file_path)
    if not path.is_file():
        console.print(f"[bold red]Error:[/bold red] File '{file_path}' does not exist.")
        raise typer.Exit(code=1)

    modules = VerilogParser.parse_file(path)
    if not modules:
        console.print(f"[bold red]Error:[/bold red] No modules found in '{file_path}'.")
        raise typer.Exit(code=1)

    spec = modules[0]
    generator = TestbenchGenerator()
    console.print(f"[bold cyan]Generating cocotb testbench for module:[/bold cyan] {spec.name}")

    source_code = path.read_text(encoding="utf-8")
    tb_code = generator.generate(spec, source_code=source_code)

    if output:
        out_path = Path(output)
        out_path.write_text(tb_code, encoding="utf-8")
        console.print(f"[bold green]Saved testbench to:[/bold green] {out_path}")
    else:
        console.print(Panel(tb_code, title=f"Generated Testbench: test_{spec.name}.py", expand=False))


@app.command()
def verify(
    rtl_file: str = typer.Argument(..., help="Path to RTL Verilog file (.v/.sv)"),
    sim_dir: str = typer.Option("examples/sim", "--dir", "-d", help="Simulation working directory"),
    max_retries: int = typer.Option(3, "--max-retries", "-r", help="Maximum autonomous repair attempts"),
) -> None:
    """Run closed-loop autonomous verification (generate -> simulate -> repair loop)."""
    from eda_agent.generators.repair_loop import VerificationLoop

    console.print(f"[bold cyan]Starting autonomous verification loop for:[/bold cyan] {rtl_file}")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(f"[cyan]Synthesizing and verifying RTL module...", total=None)

        loop = VerificationLoop()
        result = loop.run(
            rtl_file=rtl_file,
            sim_dir=sim_dir,
            max_retries=max_retries,
            clean=True,
        )
        progress.update(task, completed=True)

    itable = Table(title=f"Verification Loop History ({result.module_name})", show_header=True, header_style="bold")
    itable.add_column("Iteration", justify="center")
    itable.add_column("Action", style="cyan")
    itable.add_column("Simulation Status", style="bold")
    itable.add_column("Details", style="dim")

    for record in result.iterations:
        status_str = "[green]PASSED[/green]" if record.sim_result.success else "[red]FAILED[/red]"
        details = (
            f"Pass Rate: {record.sim_result.report.pass_rate_percent}%" if record.sim_result.report
            else (record.sim_result.diagnostics.error_summary if record.sim_result.diagnostics else "Unknown error")
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
        raise typer.Exit(code=1)


@app.command("analyze-timing")
def analyze_timing(
    log_file: str = typer.Argument(..., help="Path to OpenROAD / OpenSTA / Yosys timing log file"),
) -> None:
    """Parse Static Timing Analysis (STA) logs and output structural RTL diff recommendations."""
    path = Path(log_file)
    if not path.is_file():
        console.print(f"[bold red]Error:[/bold red] Timing log file '{log_file}' does not exist.")
        raise typer.Exit(code=1)

    try:
        report = STAAnalyzer.parse_file(path)
    except Exception as e:
        console.print(f"[bold red]Failed to parse timing log:[/bold red] {e}")
        raise typer.Exit(code=1)

    # 1. Summary Metrics Table
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

    # 2. Critical Paths Breakdown Table
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

    # 3. Structural Recommendations
    if report.recommendations:
        rec_text = "\n".join(report.recommendations)
        rec_title = "Timing Clean" if report.is_clean else "Architectural Timing Recommendations"
        rec_color = "green" if report.is_clean else "yellow"
        console.print(Panel(rec_text, title=f"[{rec_color}]{rec_title}[/{rec_color}]", expand=False))

    # 4. Actionable Diff Suggestions
    if report.actionable_diffs:
        console.print("\n[bold cyan]Actionable RTL Structural Diff Suggestions:[/bold cyan]")
        for diff in report.actionable_diffs:
            syntax = Syntax(diff, "diff", theme="monokai", line_numbers=False)
            console.print(Panel(syntax, title="Suggested Verilog Modification", expand=False))


if __name__ == "__main__":
    app()
