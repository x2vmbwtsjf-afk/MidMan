"""Safety rules for commands and user input."""

from __future__ import annotations

from dataclasses import dataclass
import re

from midman.command_catalog import get_command


SHELL_META_PATTERN = re.compile(r"[;&|`$><]")
DESTRUCTIVE_PATTERN = re.compile(
    r"\b(rm|mv|cp|dd|mkfs|fdisk|reboot|shutdown|reload|restart|poweroff|delete|erase|format|write|copy run start|commit)\b",
    re.I,
)
CONFIG_MODE_PATTERN = re.compile(
    r"\b(config|configure terminal|conf t|interface [A-Za-z]|router bgp|hostname|no shutdown|wr mem|write memory)\b",
    re.I,
)


@dataclass(frozen=True)
class SafetyDecision:
    allowed: bool
    reason: str


def validate_user_text(text: str) -> SafetyDecision:
    if not text.strip():
        return SafetyDecision(False, "Request cannot be empty.")
    if SHELL_META_PATTERN.search(text):
        return SafetyDecision(False, "Shell metacharacters are not allowed.")
    if DESTRUCTIVE_PATTERN.search(text):
        return SafetyDecision(False, "Destructive or write-oriented language is blocked.")
    if CONFIG_MODE_PATTERN.search(text):
        return SafetyDecision(False, "Configuration-mode or write commands are blocked.")
    return SafetyDecision(True, "Input passed safety checks.")


def validate_action(action: str, target_type: str) -> SafetyDecision:
    command = get_command(action)
    if target_type not in command.target_types:
        return SafetyDecision(False, f"Action '{command.action}' is not valid for target type '{target_type}'.")
    return SafetyDecision(True, "Action is allowed for target.")


def validate_device_command(action: str, command_text: str) -> SafetyDecision:
    catalog_item = get_command(action)
    if command_text not in catalog_item.commands:
        return SafetyDecision(False, f"Command '{command_text}' is not in the allowlist for action '{action}'.")
    if SHELL_META_PATTERN.search(command_text):
        return SafetyDecision(False, "Allowlisted command contains forbidden shell metacharacters.")
    if DESTRUCTIVE_PATTERN.search(command_text) or CONFIG_MODE_PATTERN.search(command_text):
        return SafetyDecision(False, "Allowlisted command violates read-only policy.")
    return SafetyDecision(True, "Command is approved.")

