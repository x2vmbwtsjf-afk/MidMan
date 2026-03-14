"""Pydantic schema validation for YAML playbooks."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator
import yaml

from midman.command_catalog import CATALOG


class PlaybookValidationError(ValueError):
    """Raised when a playbook fails schema validation."""

    def __init__(self, path: Path, issues: list[str]) -> None:
        self.path = path
        self.issues = issues
        super().__init__(f"Playbook validation failed for {path}")


class PlaybookStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["action"] = "action"
    action: str
    profile: str
    description: str | None = None

    @field_validator("action")
    @classmethod
    def validate_action(cls, value: str) -> str:
        if value not in CATALOG:
            allowed = ", ".join(sorted(CATALOG))
            raise ValueError(f"Unsupported action '{value}'. Allowed actions: {allowed}.")
        return value

    @field_validator("profile")
    @classmethod
    def validate_profile(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Profile name cannot be empty.")
        return value


class PlaybookDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    title: str | None = None
    name: str | None = None
    category: str | None = None
    intents: list[str] = Field(default_factory=list)
    command_group: str | None = None
    expected_signals: list[str] = Field(default_factory=list)
    follow_up_steps: list[str] = Field(default_factory=list)
    caution: str | None = None
    steps: list[PlaybookStep] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_metadata(self) -> "PlaybookDocument":
        if not any((self.id, self.title, self.name)):
            raise ValueError("Playbook must include at least one of: id, title, or name.")
        if self.command_group and self.command_group not in CATALOG:
            allowed = ", ".join(sorted(CATALOG))
            raise ValueError(f"Unsupported command_group '{self.command_group}'. Allowed actions: {allowed}.")
        return self

    @property
    def display_name(self) -> str:
        return self.title or self.name or self.id or "unnamed-playbook"


def load_playbook(path: Path) -> PlaybookDocument:
    try:
        payload = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError as exc:
        raise PlaybookValidationError(path, [f"Invalid YAML: {exc}"]) from exc

    try:
        return PlaybookDocument.model_validate(payload)
    except ValidationError as exc:
        issues = [_format_validation_issue(item) for item in exc.errors()]
        raise PlaybookValidationError(path, issues) from exc


def _format_validation_issue(error: dict[str, Any]) -> str:
    location = ".".join(str(part) for part in error.get("loc", ())) or "playbook"
    message = error.get("msg", "Invalid value.")
    return f"{location}: {message}"

