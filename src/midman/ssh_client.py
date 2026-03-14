"""Paramiko wrapper for safe command execution."""

from __future__ import annotations

from dataclasses import dataclass
import socket

import paramiko

from midman.profiles import Profile


@dataclass(frozen=True)
class CommandResult:
    command: str
    stdout: str
    stderr: str
    exit_status: int


class SSHClient:
    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    def run_commands(self, profile: Profile, commands: list[str]) -> list[CommandResult]:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        connect_kwargs = {
            "hostname": profile.host,
            "port": profile.port,
            "username": profile.username,
            "timeout": self.timeout,
            "look_for_keys": False,
            "allow_agent": False,
        }
        password = profile.resolve_password()
        private_key = profile.resolve_private_key()
        if private_key:
            connect_kwargs["key_filename"] = private_key
            connect_kwargs["look_for_keys"] = True
        if password:
            connect_kwargs["password"] = password

        client.connect(**connect_kwargs)
        try:
            results: list[CommandResult] = []
            for command in commands:
                stdin, stdout, stderr = client.exec_command(command, timeout=self.timeout)
                del stdin
                results.append(
                    CommandResult(
                        command=command,
                        stdout=stdout.read().decode().strip(),
                        stderr=stderr.read().decode().strip(),
                        exit_status=stdout.channel.recv_exit_status(),
                    )
                )
            return results
        finally:
            client.close()


def check_tcp_reachability(host: str, port: int, timeout: float = 3.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False

