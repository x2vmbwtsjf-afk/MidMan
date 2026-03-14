from pathlib import Path

import pytest

from midman.executor import MidmanExecutor
from midman.playbook_schema import PlaybookValidationError
from midman.profiles import load_profile


def test_execute_action_in_mock_mode() -> None:
    executor = MidmanExecutor()
    profile = load_profile("sample-linux", base_path=Path.cwd())
    report = executor.execute_action("linux_health", profile, mock=True)
    assert report.mock_mode is True
    assert report.results[0].command == "uptime"


def test_ask_uses_parser_and_mock_output() -> None:
    executor = MidmanExecutor()
    profile = load_profile("sample-switch", base_path=Path.cwd())
    report = executor.ask("check interface status", profile, mock=True)
    assert report.action == "interface_status"
    assert report.parser_confidence is not None


def test_run_playbook_in_mock_mode() -> None:
    executor = MidmanExecutor()
    playbook = Path("examples/playbooks/daily_checks.yaml")
    reports = executor.run_playbook(playbook, mock=True, base_path=Path.cwd())
    assert len(reports) == 4
    assert reports[-1].action == "management_reachability"


def test_ask_rejects_unsafe_input() -> None:
    executor = MidmanExecutor()
    profile = load_profile("sample-linux", base_path=Path.cwd())
    with pytest.raises(ValueError):
        executor.ask("show uptime && reboot", profile, mock=True)


def test_run_playbook_rejects_invalid_schema(tmp_path: Path) -> None:
    executor = MidmanExecutor()
    playbook = tmp_path / "invalid.yaml"
    playbook.write_text(
        """
name: invalid
steps:
  - action: not_real
    profile: sample-linux
"""
    )

    with pytest.raises(PlaybookValidationError):
        executor.run_playbook(playbook, mock=True, base_path=Path.cwd())
