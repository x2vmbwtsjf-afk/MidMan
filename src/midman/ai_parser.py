"""Rule-based intent parsing for Phase 1."""

from __future__ import annotations

from dataclasses import dataclass
import re

from midman.command_catalog import ALIASES, CATALOG


@dataclass(frozen=True)
class ParsedIntent:
    action: str
    confidence: float
    reason: str


PATTERN_RULES: tuple[tuple[re.Pattern[str], str, float, str], ...] = (
    (re.compile(r"\b(bgp|neighbor|neighb(?:or|our)s?)\b", re.I), "bgp_summary", 0.95, "Matched BGP-related keywords."),
    (re.compile(r"\b(interface|port|switchport|link)\b", re.I), "interface_status", 0.92, "Matched interface-related keywords."),
    (re.compile(r"\b(ilo|idrac|management|bmc|reachability)\b", re.I), "management_reachability", 0.91, "Matched management endpoint keywords."),
    (re.compile(r"\b(linux|server|health|uptime|disk|memory|cpu)\b", re.I), "linux_health", 0.90, "Matched Linux diagnostic keywords."),
)


def parse_intent(text: str) -> ParsedIntent:
    normalized = text.strip().lower()
    if not normalized:
        raise ValueError("Intent text cannot be empty.")

    compact = re.sub(r"[^a-z0-9_ -]", " ", normalized).strip().replace(" ", "_")
    if compact in CATALOG:
        return ParsedIntent(action=compact, confidence=0.99, reason="Direct catalog action match.")
    if compact in ALIASES:
        return ParsedIntent(action=ALIASES[compact], confidence=0.97, reason="Matched action alias.")

    for pattern, action, confidence, reason in PATTERN_RULES:
        if pattern.search(normalized):
            return ParsedIntent(action=action, confidence=confidence, reason=reason)

    keyword_scores: dict[str, int] = {action: 0 for action in CATALOG}
    for action, command in CATALOG.items():
        keyword_scores[action] += sum(1 for keyword in command.keywords if keyword in normalized)

    best_action = max(keyword_scores, key=keyword_scores.get)
    if keyword_scores[best_action] > 0:
        return ParsedIntent(action=best_action, confidence=0.70, reason="Matched fallback keyword scoring.")

    raise ValueError(f"Could not map request to a supported action: {text!r}")

