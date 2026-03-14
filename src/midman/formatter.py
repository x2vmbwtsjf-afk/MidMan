"""Rich formatting helpers for CLI output."""

from __future__ import annotations

from dataclasses import dataclass, field

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from midman.command_catalog import list_commands
from midman.ai_backends import resolve_ai_backend
from midman.connectors import ConnectorStatus
from midman.executor import ExecutionReport
from midman.playbook_schema import PlaybookValidationError
from midman.profiles import Profile


console = Console()


@dataclass(frozen=True)
class TranscriptLine:
    speaker: str
    message: str
    style: str


@dataclass(frozen=True)
class ActivityLine:
    level: str
    message: str
    style: str


@dataclass
class DashboardState:
    connectors: list[ConnectorStatus]
    transcript: list[TranscriptLine] = field(default_factory=list)
    activity: list[ActivityLine] = field(default_factory=list)
    footer_hint: str = "[/help] [/targets] [/logs] [/exit]"
    prompt_label: str = "midman >_"


def print_catalog() -> None:
    table = Table(title="midman command catalog")
    table.add_column("Action")
    table.add_column("Targets")
    table.add_column("Description")
    for item in list_commands():
        table.add_row(item.action, ", ".join(item.target_types), item.description)
    console.print(table)


def print_profiles(profiles: list[Profile]) -> None:
    table = Table(title="Profiles")
    table.add_column("Name")
    table.add_column("Type")
    table.add_column("Host")
    table.add_column("Port")
    for profile in profiles:
        table.add_row(profile.name, profile.type, profile.host, str(profile.port))
    console.print(table)


def print_connectors(connectors: list[ConnectorStatus]) -> None:
    table = Table(title="Connectors")
    table.add_column("Name")
    table.add_column("Type")
    table.add_column("Endpoint")
    table.add_column("Transport")
    table.add_column("Adapter")
    table.add_column("Status")
    table.add_column("AI")
    for connector in connectors:
        table.add_row(
            connector.name,
            connector.target_type,
            connector.endpoint,
            connector.transport,
            connector.adapter,
            connector.status,
            connector.ai_backend,
        )
    console.print(table)
    console.print(f"[bold]Active AI module:[/bold] {resolve_ai_backend()}")


def render_dashboard(state: DashboardState) -> None:
    layout = Layout(name="root")
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body", ratio=1),
        Layout(name="footer", size=4),
    )
    layout["body"].split_row(
        Layout(name="left", ratio=3),
        Layout(name="right", ratio=2),
    )
    layout["left"].split_column(
        Layout(name="connections", size=10),
        Layout(name="map", ratio=1),
    )
    layout["right"].split_column(
        Layout(name="ai", ratio=2),
        Layout(name="activity", ratio=2),
    )

    header_text = Text()
    header_text.append("MidMan Dashboard", style="bold bright_cyan")
    header_text.append("  ")
    header_text.append(f"AI: {resolve_ai_backend()}", style="bold bright_blue")
    layout["header"].update(Panel(header_text, border_style="bright_blue"))

    layout["connections"].update(_build_connections_panel(state.connectors))
    layout["map"].update(_build_map_panel(state.connectors))
    layout["ai"].update(_build_ai_panel(state.transcript))
    layout["activity"].update(_build_activity_panel(state.activity))
    layout["footer"].update(
        Panel(
            Text.from_markup(f"[bold bright_cyan]{state.prompt_label}[/bold bright_cyan] {state.footer_hint}"),
            border_style="bright_blue",
            title="Console",
        )
    )
    console.print(layout)


def print_report(report: ExecutionReport) -> None:
    title = f"{report.action} on {report.profile}"
    if report.mock_mode:
        title += " [mock]"
    console.rule(title)
    console.print(f"[bold]Summary:[/bold] {report.summary}")
    if report.parser_reason:
        confidence = f"{report.parser_confidence:.2f}" if report.parser_confidence is not None else "n/a"
        console.print(f"[bold]Parsed:[/bold] {report.action} ({confidence}) - {report.parser_reason}")
    table = Table(show_lines=True)
    table.add_column("Command")
    table.add_column("Status")
    table.add_column("Stdout")
    table.add_column("Stderr")
    for result in report.results:
        status = "ok" if result.exit_status == 0 else f"exit {result.exit_status}"
        table.add_row(result.command, status, result.stdout or "-", result.stderr or "-")
    console.print(table)


def print_doctor() -> None:
    table = Table(title="Doctor")
    table.add_column("Check")
    table.add_column("Status")
    table.add_row("Python", "3.12+ required")
    table.add_row("CLI mode", "Typer + Rich ready")
    table.add_row("Execution", "SSH and mock mode available")
    table.add_row("Safety", "Allowlist-only, read-only diagnostics")
    table.add_row("AI backend", resolve_ai_backend())
    console.print(table)


def print_playbook_validation_error(error: PlaybookValidationError) -> None:
    message = "\n".join(f"- {issue}" for issue in error.issues)
    console.print(
        Panel.fit(
            f"[bold red]Playbook validation failed[/bold red]\nPath: {error.path}\n\n{message}",
            title="Invalid playbook",
            border_style="red",
        )
    )


def _build_connections_panel(connectors: list[ConnectorStatus]) -> Panel:
    counts: dict[str, int] = {}
    for connector in connectors:
        counts[connector.target_type] = counts.get(connector.target_type, 0) + 1

    lines = Text()
    ai_status = "Connected" if connectors else "Idle"
    lines.append("▸ AI API: ", style="bold white")
    lines.append(ai_status, style="bold bright_green" if connectors else "yellow")
    lines.append("\n")
    lines.append("▸ SSH: ", style="bold yellow")
    lines.append(f"{counts.get('linux', 0)} Servers", style="bright_cyan")
    lines.append("\n")
    lines.append("▸ Switches: ", style="bold yellow")
    lines.append(f"{counts.get('network', 0)} Devices", style="bright_cyan")
    lines.append("\n")
    lines.append("▸ Management: ", style="bold yellow")
    lines.append(f"{counts.get('management', 0)} Systems", style="bright_cyan")
    lines.append("\n")
    lines.append("▸ AI Module: ", style="bold white")
    lines.append(resolve_ai_backend(), style="bright_blue")
    return Panel(lines, title="AI Connections", border_style="bright_green")


def _build_map_panel(connectors: list[ConnectorStatus]) -> Panel:
    tree = Tree("[bold white]Infrastructure Map[/bold white]")
    groups: dict[str, list[ConnectorStatus]] = {
        "SSH Servers": [item for item in connectors if item.target_type == "linux"],
        "Switches / Routers": [item for item in connectors if item.target_type == "network"],
        "Management Systems": [item for item in connectors if item.target_type == "management"],
    }
    for label, items in groups.items():
        branch = tree.add(f"[bold bright_cyan]{label}[/bold bright_cyan]")
        if not items:
            branch.add("[dim]No connectors configured[/dim]")
            continue
        for connector in items:
            branch.add(
                f"[bold white]{connector.name}[/bold white] "
                f"[dim]({connector.endpoint}, {connector.status})[/dim]"
            )
    return Panel(tree, border_style="grey66")


def _build_ai_panel(lines: list[TranscriptLine]) -> Panel:
    if not lines:
        content = Text.from_markup("[dim]No conversation yet. Ask for a check in interactive mode.[/dim]")
        return Panel(content, title="AI Command Interface", border_style="bright_blue")

    table = Table.grid(expand=True)
    for line in lines[-6:]:
        row = Text()
        row.append(f"{line.speaker}: ", style=line.style)
        row.append(line.message, style="white")
        table.add_row(Panel(row, border_style="grey50"))
    return Panel(table, title="AI Command Interface", border_style="bright_blue")


def _build_activity_panel(lines: list[ActivityLine]) -> Panel:
    if not lines:
        content = Text.from_markup("[dim]No activity yet.[/dim]")
        return Panel(content, title="Activity Log", border_style="red")

    table = Table.grid(expand=True)
    for line in lines[-8:]:
        row = Text()
        row.append("• ", style=line.style)
        row.append(line.message, style="white")
        table.add_row(row)
    return Panel(table, title="Activity Log", border_style="red")
