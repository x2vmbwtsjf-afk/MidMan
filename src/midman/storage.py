"""Local persistence for dashboard configuration and saved targets."""

from __future__ import annotations

from pathlib import Path
import json
import os
from typing import Any

import yaml

from midman.ai_backends import AIBackendConfig, backend_to_mapping, load_backend_from_mapping


def ensure_data_dir(base_path: Path | None = None) -> Path:
    workspace = base_path or Path.cwd()
    root = workspace / ".midman"
    root.mkdir(exist_ok=True)
    legacy = workspace / ".netdoc"
    if legacy.exists():
        _migrate_legacy_dir(legacy, root)
    return root


def save_backend_config(config: AIBackendConfig, base_path: Path | None = None) -> None:
    data_dir = ensure_data_dir(base_path)
    state_path = data_dir / "state.json"
    secrets_path = data_dir / "secrets.json"
    state_path.write_text(json.dumps({"ai_backend": backend_to_mapping(config) | {"api_key": None}}, indent=2))
    secrets_path.write_text(json.dumps({"ai_backend": {"api_key": config.api_key}}, indent=2))
    _restrict_permissions(state_path)
    _restrict_permissions(secrets_path)


def load_backend_config(base_path: Path | None = None) -> AIBackendConfig | None:
    data_dir = ensure_data_dir(base_path)
    state_path = data_dir / "state.json"
    secrets_path = data_dir / "secrets.json"
    if not state_path.exists():
        return None
    payload = dict(json.loads(state_path.read_text()).get("ai_backend", {}))
    if secrets_path.exists():
        payload["api_key"] = json.loads(secrets_path.read_text()).get("ai_backend", {}).get("api_key")
    return load_backend_from_mapping(payload)


def save_profile_mapping(name: str, payload: dict[str, Any], base_path: Path | None = None) -> Path:
    root = (base_path or Path.cwd()) / "profiles"
    root.mkdir(exist_ok=True)
    path = root / f"{name}.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    _restrict_permissions(path)
    return path


def _restrict_permissions(path: Path) -> None:
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def _migrate_legacy_dir(legacy: Path, target: Path) -> None:
    for name in ("state.json", "secrets.json"):
        src = legacy / name
        dst = target / name
        if src.exists() and not dst.exists():
            dst.write_text(src.read_text())
            _restrict_permissions(dst)
