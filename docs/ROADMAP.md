# Roadmap

This roadmap describes a realistic development path for `MidMan`. It is intended to guide contributors, not to promise exact dates or scope guarantees.

## Phase 1 — CLI MVP

Goal: establish a safe, usable local CLI for infrastructure diagnostics.

Scope:

- Typer-based CLI commands
- Rich terminal output
- SSH execution for supported targets
- rule-based intent parser
- command catalog
- safety validation layer
- YAML playbooks
- mock mode
- saved profiles

Milestone checklist:

- [x] CLI skeleton and command routing
- [x] catalog-backed action model
- [x] read-only safety checks
- [x] mock execution paths
- [x] example profiles and playbooks
- [x] test coverage for parser, safety, executor, and CLI
- [ ] richer real-device examples
- [ ] broader command catalog coverage

## Phase 2 — Advanced Diagnostics

Goal: improve operational depth and expand supported infrastructure targets.

Scope:

- better parsing for real operator language
- expanded network device support
- vendor adapters for common platforms
- richer device profile options
- improved playbook structure and reuse

Milestone checklist:

- [ ] add more diagnostic action groups
- [ ] support vendor-specific command selection
- [ ] improve network interface and routing diagnostics
- [ ] improve profile metadata and authentication options
- [ ] validate playbooks against a documented schema

## Phase 3 — AI Reasoning

Goal: move beyond intent matching into assisted troubleshooting and explanation.

Scope:

- optional LLM integration
- smarter intent resolution
- root-cause suggestion engine
- conversational CLI mode

Milestone checklist:

- [ ] add pluggable parser backends
- [ ] support LLM-assisted intent classification
- [ ] generate structured troubleshooting hints
- [ ] add iterative question-and-answer workflows in the terminal

## Phase 4 — Agent Layer

Goal: support richer remote diagnostics and structured collection.

Scope:

- remote collectors
- structured telemetry
- device adapters
- reusable data gathering workflows

Milestone checklist:

- [ ] define collector protocol or execution model
- [ ] add structured result export formats
- [ ] support vendor management adapters
- [ ] enable richer state collection beyond SSH command output

## Phase 5 — Frontend Platform

Goal: extend `midman` into a broader operational platform.

Scope:

- API layer
- web dashboard
- execution history
- collaboration and team features

Milestone checklist:

- [ ] define API surface
- [ ] persist history and run metadata
- [ ] add dashboard and UI workflows
- [ ] support multi-user and team-oriented operations

## Future Ideas

Potential future directions include:

- policy packs for environment-specific safety rules
- topology-aware diagnostics
- change-review mode before any write-capable workflows
- integration with CMDB or inventory systems
- structured export to incident or observability tools
- approval workflows for privileged operations

The project should continue to grow in stages. Safety, auditability, and modularity should remain more important than feature velocity.
