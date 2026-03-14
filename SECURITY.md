# MidMan Security Model

MidMan is designed to help engineers troubleshoot infrastructure without turning a natural-language interface into a general-purpose remote shell.

Its security posture is based on explicit command approval, conservative execution defaults, and clear separation between request interpretation and execution authority.

## Core Principles

- allowlist-only commands
- read-only diagnostics by default
- fail closed on unsupported or ambiguous input
- keep request parsing separate from command authorization
- preserve an auditable path from request to executed command

## Allowlist-Only Commands

MidMan should execute only commands that are present in the reviewed command catalog for a supported action.

This means:

- no free-form remote shell passthrough
- no direct execution of raw AI output
- no implicit expansion from user phrasing to unreviewed commands

## Read-Only Default Behavior

The expected operating mode is diagnosis and observation. Commands that change system state, enter configuration mode, modify files, restart services, or alter network behavior should be blocked unless the project introduces a separately reviewed privileged mode in the future.

## Blocked Destructive Operations

The current safety model is designed to reject patterns associated with:

- file deletion or modification
- reboots, shutdowns, and restarts
- configuration mode on network devices
- shell metacharacters and command chaining
- write-oriented management operations

## Credential Handling

Credentials should not be committed to the repository.

Recommended practice:

- use environment variables or key references in profiles
- keep plaintext secrets out of tracked files
- prefer SSH keys or external secret sources where possible
- avoid logging credentials or secret-bearing inputs

## Threat Model Assumptions

MidMan assumes:

- the operator is trusted to access the target
- targets may be production systems
- natural-language input may be ambiguous or maliciously phrased
- the parser or future AI backend is untrusted until safety validation passes
- connectors must not expand scope beyond the approved action

## Reporting Security Issues

Please avoid filing public issues for sensitive vulnerabilities until the project has a documented private disclosure channel. For now, coordinate directly with maintainers when possible.
