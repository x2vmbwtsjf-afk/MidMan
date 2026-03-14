"""Execution orchestrator between parsed intent and target adapters."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from midman.ai_parser import parse_intent
from midman.command_catalog import get_command
from midman.playbook_schema import load_playbook
from midman.profiles import Profile, load_profile
from midman.safety import validate_action, validate_device_command, validate_user_text
from midman.ssh_client import CommandResult, SSHClient, check_tcp_reachability


MOCK_OUTPUTS: dict[str, dict[str, Any]] = {
    "linux_health": {
        "summary": "Linux host healthy with moderate load and ample disk headroom.",
        "results": [
            {"command": "uptime", "stdout": " 10:22:11 up 42 days,  3:10,  2 users,  load average: 0.22, 0.18, 0.12", "stderr": "", "exit_status": 0},
            {"command": "df -h", "stdout": "/dev/sda1  80G  29G  48G  38% /", "stderr": "", "exit_status": 0},
            {"command": "free -m", "stdout": "Mem:  4096  1320  2110  130  665  2490", "stderr": "", "exit_status": 0},
            {"command": "ss -tulpn", "stdout": "tcp LISTEN 0 128 0.0.0.0:22 users:(\"sshd\",pid=728,fd=3)", "stderr": "", "exit_status": 0},
        ],
    },
    "interface_status": {
        "summary": "All access uplinks are up; one unused access port is administratively down.",
        "results": [
            {"command": "show interfaces status", "stdout": "Gi1/0/1 connected trunk\nGi1/0/2 connected 10G uplink\nGi1/0/24 disabled unused", "stderr": "", "exit_status": 0},
            {"command": "show ip interface brief", "stdout": "Vlan10 up up 10.0.10.1\nVlan20 up up 10.0.20.1", "stderr": "", "exit_status": 0},
        ],
    },
    "bgp_summary": {
        "summary": "BGP peers are established and prefixes are being received.",
        "results": [
            {"command": "show bgp summary", "stdout": "Neighbor 192.0.2.1 Estab 4d12h PfxRcd 120\nNeighbor 198.51.100.1 Estab 3d02h PfxRcd 118", "stderr": "", "exit_status": 0},
            {"command": "show ip bgp summary", "stdout": "IPv4 Unicast peers: 2 established", "stderr": "", "exit_status": 0},
        ],
    },
    "management_reachability": {
        "summary": "Management endpoint reachable. Adapter functions are placeholders in Phase 1.",
        "results": [
            {"command": "tcp_connect", "stdout": "Reachable on TCP/443", "stderr": "", "exit_status": 0},
        ],
    },
}


@dataclass(frozen=True)
class ExecutionReport:
    action: str
    profile: str
    target_type: str
    mock_mode: bool
    summary: str
    results: list[CommandResult]
    parser_reason: str | None = None
    parser_confidence: float | None = None


class MidmanExecutor:
    def __init__(self, ssh_client: SSHClient | None = None) -> None:
        self.ssh_client = ssh_client or SSHClient()

    def execute_action(self, action: str, profile: Profile, mock: bool = False) -> ExecutionReport:
        decision = validate_action(action, profile.type)
        if not decision.allowed:
            raise ValueError(decision.reason)

        catalog_item = get_command(action)
        if mock:
            return self._mock_report(action, profile)

        if profile.type == "management":
            port = profile.port or 443
            reachable = check_tcp_reachability(profile.host, port)
            result = CommandResult(
                command="tcp_connect",
                stdout=f"{'Reachable' if reachable else 'Unreachable'} on TCP/{port}",
                stderr="",
                exit_status=0 if reachable else 1,
            )
            summary = "Management endpoint reachable. Adapter functions are placeholders in Phase 1." if reachable else "Management endpoint is not reachable."
            return ExecutionReport(action, profile.name, profile.type, False, summary, [result])

        approved_commands: list[str] = []
        for command in catalog_item.commands:
            cmd_decision = validate_device_command(action, command)
            if not cmd_decision.allowed:
                raise ValueError(cmd_decision.reason)
            approved_commands.append(command)

        results = self.ssh_client.run_commands(profile, approved_commands)
        summary = self._summarize(action, results)
        return ExecutionReport(action, profile.name, profile.type, False, summary, results)

    def ask(self, text: str, profile: Profile, mock: bool = False) -> ExecutionReport:
        user_decision = validate_user_text(text)
        if not user_decision.allowed:
            raise ValueError(user_decision.reason)
        parsed = parse_intent(text)
        report = self.execute_action(parsed.action, profile=profile, mock=mock)
        return ExecutionReport(
            action=report.action,
            profile=report.profile,
            target_type=report.target_type,
            mock_mode=report.mock_mode,
            summary=report.summary,
            results=report.results,
            parser_reason=parsed.reason,
            parser_confidence=parsed.confidence,
        )

    def run_playbook(self, playbook_path: Path, mock: bool = False, base_path: Path | None = None) -> list[ExecutionReport]:
        playbook = load_playbook(playbook_path)
        reports: list[ExecutionReport] = []
        for step in playbook.steps:
            profile = load_profile(step.profile, base_path=base_path)
            reports.append(self.execute_action(step.action, profile, mock=mock))
        return reports

    def _mock_report(self, action: str, profile: Profile) -> ExecutionReport:
        fixture = MOCK_OUTPUTS[action]
        results = [CommandResult(**item) for item in fixture["results"]]
        return ExecutionReport(action, profile.name, profile.type, True, fixture["summary"], results)

    def _summarize(self, action: str, results: list[CommandResult]) -> str:
        failures = [result for result in results if result.exit_status != 0]
        if failures:
            return f"{action} completed with {len(failures)} command failure(s)."
        return f"{action} completed successfully with {len(results)} approved command(s)."
