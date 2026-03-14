# Roadmap

This roadmap describes a practical path for MidMan to grow from a safe CLI utility into a broader operations tool without weakening its control boundaries.

## Phase 1 — CLI MVP

Goal: establish a dependable local CLI for safe infrastructure diagnostics.

Scope:

- Typer-based CLI commands
- profile loading and target resolution
- command catalog and safety validation
- SSH execution for supported Linux and network checks
- management reachability checks
- mock mode and test coverage

Current focus:

- broaden the command catalog for real operator use
- improve examples and documentation
- keep the read-only safety model strict

## Phase 2 — Playbooks

Goal: make repeatable troubleshooting workflows first-class.

Scope:

- validate and document the playbook schema
- ship a small set of built-in troubleshooting playbooks
- improve playbook metadata and reuse
- add stronger tests for playbook execution and validation

## Phase 3 — AI Parsing Improvements

Goal: improve how MidMan maps natural-language requests to approved actions.

Scope:

- expand rule-based parser coverage for real operator phrasing
- add optional pluggable AI backends
- surface parser confidence and fallback behavior
- keep parser output auditable before execution

## Phase 4 — Connectors

Goal: deepen support for real infrastructure targets beyond generic SSH checks.

Scope:

- iLO and iDRAC adapter support
- broader network device coverage
- connector-specific capability modeling
- clearer target-type handling for routers, switches, and management interfaces

## Phase 5 — Interactive TUI

Goal: mature the interactive dashboard into a reliable operator interface.

Scope:

- harden the existing Textual workflow
- improve repeated request handling against a chosen target
- tighten target selection, logs, and session state behavior
- keep the CLI as the primary supported interface

## Phase 6 — API / Integrations

Goal: expose MidMan capabilities to adjacent tooling without losing safety guarantees.

Scope:

- local API surface for integrations
- structured result export
- hooks for ticketing, chat, or inventory systems
- execution history and audit-friendly artifacts
