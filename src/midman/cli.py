"""Typer CLI entrypoint for MidMan."""

from __future__ import annotations

from pathlib import Path
import typer

from midman.connectors import collect_connectors
from midman.executor import MidmanExecutor
from midman.formatter import (
    console,
    print_catalog,
    print_connectors,
    print_doctor,
    print_playbook_validation_error,
    print_profiles,
    print_report,
)
from midman.playbook_schema import PlaybookValidationError
from midman.profiles import list_profiles, load_profile
from midman.ssh_client import check_tcp_reachability


app = typer.Typer(help="MidMan: CLI-first infrastructure assistant for safe diagnostics.")
profiles_app = typer.Typer(help="List and inspect target profiles.", invoke_without_command=True, no_args_is_help=False)
app.add_typer(profiles_app, name="profiles")

executor = MidmanExecutor()


@app.command()
def connect(
    profile: str | None = typer.Option(None, help="Profile name to connect to."),
    host: str | None = typer.Option(None, help="Host or IP address to probe directly."),
    port: int = typer.Option(22, help="TCP port to probe when using --host."),
    timeout: float = typer.Option(3.0, help="TCP reachability timeout in seconds."),
) -> None:
    """Check basic target reachability."""
    if host:
        if profile:
            raise typer.BadParameter("Use either --profile or --host, not both.")
        reachable = check_tcp_reachability(host, port, timeout=timeout)
        status = "reachable" if reachable else "unreachable"
        console.print(f"{host}:{port} is [bold]{status}[/bold].")
        raise typer.Exit(code=0 if reachable else 1)

    if not profile:
        raise typer.BadParameter("Provide either --profile or --host.")

    selected = load_profile(profile)
    selected_port = selected.port if selected.type != "management" else (selected.port or 443)
    reachable = check_tcp_reachability(selected.host, selected_port, timeout=timeout)
    status = "reachable" if reachable else "unreachable"
    console.print(f"{selected.name} ({selected.host}:{selected_port}) is [bold]{status}[/bold].")
    raise typer.Exit(code=0 if reachable else 1)


@app.command()
def connectors(
    probe: bool = typer.Option(False, "--probe", help="Probe connector reachability instead of only showing configured targets."),
    timeout: float = typer.Option(1.0, help="TCP reachability timeout in seconds when --probe is used."),
) -> None:
    """Show configured connectors and the active AI module."""
    print_connectors(collect_connectors(base_path=Path.cwd(), probe=probe, timeout=timeout))


@app.command()
def run(
    action: str = typer.Argument(None, help="Catalog action to execute."),
    profile: str = typer.Option(None, help="Profile name."),
    playbook: Path | None = typer.Option(None, exists=True, dir_okay=False, help="Playbook YAML path."),
    mock: bool = typer.Option(False, "--mock", help="Use mock outputs instead of real execution."),
) -> None:
    """Run an approved diagnostic action or playbook."""
    if playbook:
        try:
            reports = executor.run_playbook(playbook, mock=mock, base_path=Path.cwd())
        except PlaybookValidationError as exc:
            print_playbook_validation_error(exc)
            raise typer.Exit(code=2) from exc
        for report in reports:
            print_report(report)
        return
    if not action or not profile:
        raise typer.BadParameter("Provide both ACTION and --profile, or use --playbook.")
    selected = load_profile(profile)
    report = executor.execute_action(action, selected, mock=mock)
    print_report(report)


@app.command()
def ask(
    text: str = typer.Argument(..., help="Natural language request."),
    profile: str = typer.Option(..., help="Profile name."),
    mock: bool = typer.Option(False, "--mock", help="Use mock outputs instead of real execution."),
) -> None:
    """Parse a request and execute the mapped approved action."""
    selected = load_profile(profile)
    report = executor.ask(text, selected, mock=mock)
    print_report(report)


@app.command()
def interactive(
    profile: str = typer.Option(None, help="Default profile name."),
    mock: bool = typer.Option(False, "--mock", help="Use mock outputs instead of real execution."),
) -> None:
    """Start the MidMan infrastructure operations dashboard."""
    from midman.tui import MidmanDashboardApp

    app_instance = MidmanDashboardApp(profile_name=profile, mock=mock, base_path=Path.cwd())
    app_instance.run()


@profiles_app.callback()
def profiles_callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        print_profiles(list_profiles())


@profiles_app.command("list")
def profiles_list() -> None:
    """List available profiles."""
    print_profiles(list_profiles())


@app.command()
def catalog() -> None:
    """Show supported actions."""
    print_catalog()


@app.command()
def doctor() -> None:
    """Show environment and architecture checks."""
    print_doctor()


def main() -> None:
    app()


if __name__ == "__main__":
    main()
