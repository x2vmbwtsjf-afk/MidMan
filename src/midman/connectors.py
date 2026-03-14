"""Connector inventory and AI backend visibility."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from midman.ai_backends import resolve_ai_backend
from midman.profiles import list_profiles
from midman.ssh_client import check_tcp_reachability


@dataclass(frozen=True)
class ConnectorStatus:
    name: str
    target_type: str
    endpoint: str
    transport: str
    status: str
    adapter: str
    ai_backend: str


def collect_connectors(base_path: Path | None = None, probe: bool = False, timeout: float = 1.0) -> list[ConnectorStatus]:
    ai_backend = resolve_ai_backend()
    connectors: list[ConnectorStatus] = []
    for profile in list_profiles(base_path=base_path):
        transport = "ssh" if profile.type in {"linux", "network"} else "https"
        port = profile.port if profile.type != "management" else (profile.port or 443)
        endpoint = f"{profile.host}:{port}"
        adapter = profile.adapter or ("ssh" if profile.type in {"linux", "network"} else "placeholder")
        status = "configured"
        if probe:
            status = "reachable" if check_tcp_reachability(profile.host, port, timeout=timeout) else "unreachable"
        connectors.append(
            ConnectorStatus(
                name=profile.name,
                target_type=profile.type,
                endpoint=endpoint,
                transport=transport,
                status=status,
                adapter=adapter,
                ai_backend=ai_backend if profile.use_llm else resolve_ai_backend(),
            )
        )
    return connectors
