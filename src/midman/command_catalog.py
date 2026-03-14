"""Catalog of supported diagnostic intents and safe device commands."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CatalogCommand:
    action: str
    title: str
    description: str
    target_types: tuple[str, ...]
    commands: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()
    mock_key: str = ""
    supports_ssh: bool = True


CATALOG: dict[str, CatalogCommand] = {
    "linux_health": CatalogCommand(
        action="linux_health",
        title="Linux health snapshot",
        description="Collect uptime, CPU, memory, disk, and network listener context.",
        target_types=("linux",),
        commands=("uptime", "df -h", "free -m", "ss -tulpn"),
        keywords=("linux", "server", "health", "diagnostic", "uptime", "disk", "memory", "cpu"),
        mock_key="linux_health",
    ),
    "interface_status": CatalogCommand(
        action="interface_status",
        title="Interface status",
        description="Show a concise interface summary on a network device.",
        target_types=("network",),
        commands=("show interfaces status", "show ip interface brief"),
        keywords=("interface", "ports", "status", "switch", "interfaces"),
        mock_key="interface_status",
    ),
    "bgp_summary": CatalogCommand(
        action="bgp_summary",
        title="BGP summary",
        description="Show BGP neighbor and session summary information.",
        target_types=("network",),
        commands=("show bgp summary", "show ip bgp summary"),
        keywords=("bgp", "routing", "peers", "neighbors", "summary"),
        mock_key="bgp_summary",
    ),
    "management_reachability": CatalogCommand(
        action="management_reachability",
        title="Management reachability",
        description="Check if a management endpoint is reachable and record adapter placeholder details.",
        target_types=("management",),
        commands=(),
        keywords=("ilo", "idrac", "management", "reachability", "bmc"),
        mock_key="management_reachability",
        supports_ssh=False,
    ),
}


ALIASES: dict[str, str] = {
    "linux_check": "linux_health",
    "server_health": "linux_health",
    "ports": "interface_status",
    "interfaces": "interface_status",
    "bgp": "bgp_summary",
    "mgmt": "management_reachability",
}


def get_command(action: str) -> CatalogCommand:
    resolved = ALIASES.get(action, action)
    try:
        return CATALOG[resolved]
    except KeyError as exc:
        raise KeyError(f"Unknown action: {action}") from exc


def list_commands() -> list[CatalogCommand]:
    return list(CATALOG.values())

