# MidMan Architecture

MidMan is a CLI-first infrastructure diagnostics tool with a strict control boundary between request interpretation and remote execution. The system is designed so that natural-language input can help select diagnostics, but cannot bypass safety policy.

## Simple Diagram

```text
Operator Request
      |
      v
CLI Layer
      |
      v
Parser / AI Layer
      |
      v
Safety Engine <----> Command Catalog
      |
      v
Execution Engine
      |
      v
SSH / Management Connectors
      |
      v
Target System
```

The important design rule is that the parser proposes actions, the safety engine approves them, and the execution engine runs only approved commands.

## CLI Layer

The CLI layer is the operator-facing entrypoint. It is responsible for:

- parsing commands such as `ask`, `run`, `connect`, `catalog`, and `interactive`
- loading profiles
- loading and validating playbooks
- selecting mock or real execution mode
- formatting output for terminal use

This layer should orchestrate the request flow without becoming the home for policy or platform-specific logic.

## Parser / AI Layer

The parser layer maps natural-language requests to supported internal actions.

Current behavior is primarily rule-based and deterministic. Over time, this layer may use optional AI backends to improve intent resolution, but its output should always remain reviewable and non-authoritative.

Responsibilities:

- normalize operator phrasing
- infer likely infrastructure intent
- map requests to catalog actions
- surface reasoning or confidence metadata when useful

## Safety Engine

The safety engine is the enforcement boundary for MidMan.

Responsibilities:

- reject shell metacharacters and command chaining
- block destructive or write-oriented patterns
- reject configuration-mode commands
- verify target compatibility for a selected action
- verify that a device command is present in the allowlist

If MidMan is unsure whether a request is safe, it should fail closed.

## Command Catalog

The command catalog defines what MidMan is allowed to do.

Each action in the catalog should include:

- a stable action name
- a human-readable description
- supported target types
- approved remote commands or checks
- parser keywords and mock-output metadata where relevant

This catalog is a core safety boundary. It keeps the tool from turning into unrestricted shell automation.

## Execution Engine

The execution engine converts an approved action into a concrete execution plan.

Responsibilities:

- resolve commands for the chosen action
- select the correct connector path
- execute in mock or real mode
- collect structured results
- return output that can be rendered in the CLI or TUI

The execution engine should not invent commands. It should consume already-approved actions.

## SSH Connectors

The connector layer adapts execution to a target class.

Current scope includes:

- SSH execution for Linux targets
- SSH execution for network devices
- TCP reachability checks for management endpoints

Planned expansion includes more connector-specific behavior for iLO, iDRAC, and other management interfaces.

## Profiles System

Profiles describe target connection details and target type metadata.

They currently provide:

- target name
- target type
- host and port
- username
- authentication references
- optional adapter metadata

Profiles allow MidMan to keep environment-specific details outside command definitions and playbooks.

## Playbooks

Playbooks are declarative YAML workflows for repeatable diagnostics.

They are intended to:

- package a sequence of approved actions
- document the intent of a diagnostic flow
- support consistent investigations across teams
- remain easy to review in code review

Playbooks should reference approved actions rather than embedding arbitrary remote commands.

## Current Source Layout

The repository currently uses a flat `src/midman/` package with focused modules such as:

- `cli.py`
- `ai_parser.py`
- `command_catalog.py`
- `safety.py`
- `executor.py`
- `profiles.py`
- `playbook_schema.py`
- `connectors.py`

As the project grows, it may make sense to group these into subpackages for `cli`, `ai`, `core`, `connectors`, `safety`, and `playbooks`, but the current layout keeps the implementation simple and stable while the feature set is still forming.
