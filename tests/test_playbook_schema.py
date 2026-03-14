from pathlib import Path

import pytest

from midman.playbook_schema import PlaybookValidationError, load_playbook


def test_load_playbook_accepts_example_fixture() -> None:
    playbook = load_playbook(Path("examples/playbooks/daily_checks.yaml"))
    assert playbook.display_name == "daily-checks"
    assert len(playbook.steps) == 4


def test_load_playbook_rejects_unknown_action(tmp_path: Path) -> None:
    playbook_path = tmp_path / "invalid_action.yaml"
    playbook_path.write_text(
        """
name: invalid-action
steps:
  - action: erase_everything
    profile: sample-linux
"""
    )

    with pytest.raises(PlaybookValidationError) as exc_info:
        load_playbook(playbook_path)

    assert "Unsupported action 'erase_everything'" in str(exc_info.value.issues)


def test_load_playbook_requires_steps(tmp_path: Path) -> None:
    playbook_path = tmp_path / "missing_steps.yaml"
    playbook_path.write_text(
        """
name: empty-playbook
steps: []
"""
    )

    with pytest.raises(PlaybookValidationError) as exc_info:
        load_playbook(playbook_path)

    assert "steps" in str(exc_info.value.issues)

