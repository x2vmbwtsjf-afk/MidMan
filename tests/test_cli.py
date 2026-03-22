from typer.testing import CliRunner

from midman import cli

import re


runner = CliRunner()


ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def normalize_output(result) -> str:
    return ANSI_RE.sub("", result.stdout + result.stderr)


def test_catalog_command() -> None:
    result = runner.invoke(cli.app, ["catalog"])
    assert result.exit_code == 0
    assert "linux_health" in result.stdout


def test_run_mock_command() -> None:
    result = runner.invoke(cli.app, ["run", "linux_health", "--profile", "sample-linux", "--mock"])
    assert result.exit_code == 0
    assert "Linux host healthy" in result.stdout


def test_ask_mock_command() -> None:
    result = runner.invoke(cli.app, ["ask", "check bgp summary", "--profile", "sample-switch", "--mock"])
    assert result.exit_code == 0
    assert "BGP peers are established" in result.stdout


def test_profiles_command_lists_by_default() -> None:
    result = runner.invoke(cli.app, ["profiles"])
    assert result.exit_code == 0
    assert "sample-linux" in result.stdout


def test_connectors_command_shows_ai_backend() -> None:
    result = runner.invoke(cli.app, ["connectors"])
    assert result.exit_code == 0
    assert "Active AI module" in result.stdout
    assert "Connectors" in result.stdout


def test_interactive_help_renders_dashboard_command_help() -> None:
    result = runner.invoke(cli.app, ["interactive", "--help"])
    assert result.exit_code == 0
    output = normalize_output(result)
    assert "MidMan infrastructure operations dashboard" in output
    assert "profile" in output


def test_run_invalid_playbook_prints_validation_error(tmp_path) -> None:
    playbook = tmp_path / "invalid_playbook.yaml"
    playbook.write_text(
        """
name: broken
steps:
  - action: nope
    profile: sample-linux
"""
    )
    result = runner.invoke(cli.app, ["run", "--playbook", str(playbook), "--mock"])
    assert result.exit_code == 2
    assert "Playbook validation failed" in result.stdout


def test_connect_supports_direct_host(monkeypatch) -> None:
    monkeypatch.setattr(cli, "check_tcp_reachability", lambda host, port, timeout=3.0: host == "192.168.1.50" and port == 22)
    result = runner.invoke(cli.app, ["connect", "--host", "192.168.1.50", "--port", "22"])
    assert result.exit_code == 0
    assert "192.168.1.50:22 is reachable" in result.stdout


def test_connect_requires_profile_or_host() -> None:
    result = runner.invoke(cli.app, ["connect"])
    assert result.exit_code != 0
    output = normalize_output(result)
    assert "provide either" in output.lower()
    assert "profile" in output.lower()
    assert "host" in output.lower()


def test_connect_rejects_profile_and_host_together() -> None:
    result = runner.invoke(cli.app, ["connect", "--profile", "sample-linux", "--host", "192.168.1.50"])
    assert result.exit_code != 0
    output = normalize_output(result)
    assert "use either" in output.lower()
    assert "profile" in output.lower()
    assert "host" in output.lower()
