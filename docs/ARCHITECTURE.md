# Architecture

## System Overview

`MidMan` is a CLI-first infrastructure assistant that connects operator intent to safe infrastructure diagnostics.

The system is organized as a modular pipeline:

- parse a user request
- map it to a supported action
- validate that the action is safe for the selected target
- execute approved diagnostics over SSH or management checks
- summarize the results in the terminal

Phase 1 is deliberately narrow. It focuses on execution correctness, clear safety boundaries, and a practical operator experience from the command line.

## Core Architecture Diagram

```text
+-------------------+      +---------------------+      +------------------------+
| User CLI Request  | ---> | AI Intent Parser    | ---> | CLI Orchestrator       |
| ask / run / etc.  |      | rule-based mapping  |      | profiles + dispatch    |
+-------------------+      +---------------------+      +-----------+------------+
                                                                      |
                                                                      v
                                                         +------------+------------+
                                                         | Command Catalog         |
                                                         | approved actions        |
                                                         +------------+------------+
                                                                      |
                                                                      v
                                                         +------------+------------+
                                                         | Safety Layer            |
                                                         | allowlist + validation  |
                                                         +------------+------------+
                                                                      |
                                                                      v
                                     +------------------------+-------+------------------------+
                                     |                        |                                |
                                     v                        v                                v
                             +-------+--------+      +--------+--------+              +--------+--------+
                             | SSH Execution  |      | Network Targets |              | Management      |
                             | Linux Targets  |      | switches/router |              | reachability    |
                             +----------------+      +-----------------+              +-----------------+
                                                                      |
                                                                      v
                                                         +------------+------------+
                                                         | Rich terminal output    |
                                                         | summaries + results     |
                                                         +-------------------------+
```

## Layers

## 1. AI Intent Parser

The parser is currently rule-based. It interprets natural language requests and maps them to supported internal actions.

Examples:

- `check cpu on server01`
- `show interfaces on leaf01`
- `is the idrac reachable`

In Phase 1, the parser does not call an external model. It uses deterministic matching logic so behavior remains inspectable, testable, and stable.

Responsibilities:

- normalize user phrasing
- detect likely infrastructure intent
- choose a supported action
- return parser confidence and reasoning metadata

## 2. CLI Orchestrator

The CLI orchestrator is the main control layer.

It handles:

- command-line parsing through Typer
- profile resolution
- playbook loading
- mock mode selection
- parser invocation
- execution dispatch
- terminal formatting

This layer should remain thin enough to understand end-to-end, while still coordinating the full request lifecycle.

## 3. Command Catalog

The command catalog defines what `MidMan` knows how to do.

Each action should map to:

- a stable action name
- supported target types
- an approved set of device commands or checks
- metadata used by the parser and formatter

The catalog is a core safety boundary. It prevents the system from drifting into unrestricted command execution.

## 4. Safety Layer

The safety layer validates both user input and resolved actions before execution.

It is responsible for:

- blocking shell metacharacters
- blocking destructive verbs and write-oriented commands
- blocking config-mode patterns
- verifying that actions match the selected target type
- verifying that remote commands are in the approved allowlist

The expected behavior is to fail closed. If an action or command is uncertain or unsupported, it should be rejected.

## 5. Execution Engine

The execution engine translates a validated action into a concrete execution plan.

Responsibilities:

- retrieve the approved commands for an action
- route the request to the correct execution backend
- support mock output generation
- collect command results
- summarize execution status

The engine sits between the abstract action model and the concrete remote transport layer.

## 6. SSH Management Layer

The transport layer currently includes:

- SSH execution for Linux targets
- SSH execution for network devices
- TCP reachability checks for management endpoints

This is intentionally limited in Phase 1. Management interfaces such as iLO and iDRAC are modeled as future adapter targets, but their deeper vendor-specific workflows are not implemented yet.

## 7. Playbooks

Playbooks provide a repeatable workflow layer on top of individual actions.

A playbook can:

- define a sequence of approved diagnostic steps
- point each step at a named profile
- allow operators to run recurring checks consistently
- support mock-mode validation during development

Playbooks should stay declarative and easy to audit.

## Request Flow

The normal request flow is:

1. A user runs a CLI command such as `midman ask "show bgp summary" --profile edge01`.
2. The parser detects the likely intent and maps it to a supported action.
3. The command catalog resolves that action into an approved command group.
4. The safety layer validates the input text, action, target type, and command set.
5. The execution engine dispatches the request to SSH or management checks.
6. The result is summarized and rendered in the terminal with Rich formatting.

The same model applies to `run`, `ask`, and playbook execution, with only minor differences in how the initial action is selected.

## Modularity and Future Extension

The codebase is intentionally modular so future features can be added without collapsing boundaries between intent, safety, and execution.

Likely extension points include:

- richer parser backends, including optional LLM integration
- vendor-specific adapters for network operating systems
- iLO, iDRAC, and BMC command adapters
- structured result models for downstream APIs
- telemetry collection and agent workflows
- multi-step reasoning and recommendation layers

The architecture should preserve one principle as the system grows: intent interpretation must remain separate from execution authority.
