"""Profile loading and validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os
from typing import Any

import yaml


DEFAULT_PROFILE_DIRS = ("profiles", "examples/profiles")


@dataclass(frozen=True)
class Profile:
    name: str
    type: str
    host: str
    username: str | None = None
    port: int = 22
    adapter: str | None = None
    auth: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    use_llm: bool = False

    def resolve_password(self) -> str | None:
        password = self.auth.get("password")
        if password:
            return password
        env_name = self.auth.get("password_env")
        if env_name:
            return os.getenv(env_name)
        return None

    def resolve_private_key(self) -> str | None:
        key_path = self.auth.get("private_key")
        if not key_path:
            return None
        return str(Path(key_path).expanduser())


def profile_search_paths(base_path: Path | None = None) -> list[Path]:
    root = base_path or Path.cwd()
    return [root / rel for rel in DEFAULT_PROFILE_DIRS]


def load_profile(name: str, base_path: Path | None = None) -> Profile:
    for directory in profile_search_paths(base_path):
        yaml_path = directory / f"{name}.yaml"
        yml_path = directory / f"{name}.yml"
        candidate = yaml_path if yaml_path.exists() else yml_path
        if candidate.exists():
            data = yaml.safe_load(candidate.read_text()) or {}
            return _profile_from_mapping(data, default_name=name)
    raise FileNotFoundError(f"Profile '{name}' was not found in configured profile directories.")


def list_profiles(base_path: Path | None = None) -> list[Profile]:
    discovered: dict[str, Profile] = {}
    for directory in profile_search_paths(base_path):
        if not directory.exists():
            continue
        for candidate in sorted(directory.glob("*.y*ml")):
            data = yaml.safe_load(candidate.read_text()) or {}
            profile = _profile_from_mapping(data, default_name=candidate.stem)
            discovered[profile.name] = profile
    return list(discovered.values())


def _profile_from_mapping(data: dict[str, Any], default_name: str) -> Profile:
    profile = Profile(
        name=data.get("name", default_name),
        type=data["type"],
        host=data["host"],
        username=data.get("username"),
        port=int(data.get("port", 22)),
        adapter=data.get("adapter"),
        auth=data.get("auth", {}) or {},
        metadata=data.get("metadata", {}) or {},
        use_llm=bool(data.get("use_llm", False)),
    )
    if profile.type not in {"linux", "network", "management"}:
        raise ValueError(f"Unsupported profile type: {profile.type}")
    return profile

