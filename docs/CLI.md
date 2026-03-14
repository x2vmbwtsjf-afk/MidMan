# CLI Reference

`MidMan` is a terminal-first tool. Phase 1 focuses entirely on CLI workflows.

## Command Overview

The main commands are:

- `midman connect`
- `midman run`
- `midman ask`
- `midman interactive`
- `midman profiles`
- `midman catalog`
- `midman doctor`

Run help at any time with:

```bash
midman --help
```

## `midman connect`

Checks basic target reachability for a saved profile.

Use this when you want to verify that a host or management endpoint is reachable before running a diagnostic.

Example:

```bash
midman connect --profile sample-linux
```

## `midman run`

Runs an approved action directly, or executes a YAML playbook.

Use `run` when you already know the action name and do not need natural language parsing.

Examples:

```bash
midman run linux_health --profile sample-linux
midman run bgp_summary --profile sample-switch
midman run --playbook examples/playbooks/daily_checks.yaml --mock
```

## `midman ask`

Accepts a natural language request, resolves it to a supported action, and executes the approved diagnostic workflow.

Examples:

```bash
midman ask "check cpu on server01" --profile sample-linux
midman ask "show interfaces on leaf01" --profile sample-switch
midman ask "is the idrac reachable" --profile sample-idrac --mock
```

This command is useful when operators want a simpler interface than remembering action names.

## `midman interactive`

Starts a simple terminal session for repeated requests against the same profile.

Example:

```bash
midman interactive --profile sample-switch --mock
```

Inside the prompt, enter requests such as:

```text
show bgp summary
show interfaces
exit
```

## `midman profiles`

Lists saved profiles.

Current implementation:

```bash
midman profiles list
```

Profiles define target connection details and metadata used by the CLI.

## `midman catalog`

Displays the supported action catalog.

Example:

```bash
midman catalog
```

Use this to inspect what `MidMan` can currently do without relying on the parser.

## `midman doctor`

Shows environment and capability checks for the local installation.

Example:

```bash
midman doctor
```

This is a lightweight verification command for contributors and operators.

## Profiles

Profiles are YAML definitions for saved targets.

They typically include:

- `name`
- `type`
- `host`
- `port`
- `username`
- `auth`
- optional metadata

Example:

```yaml
name: sample-linux
type: linux
host: 192.0.2.10
port: 22
username: ops
auth:
  password_env: MIDMAN_SAMPLE_PASSWORD
```

Supported target types currently include:

- `linux`
- `network`
- `management`

By default, `MidMan` looks for profiles in:

- `profiles/`
- `examples/profiles/`

## Mock Mode

Mock mode simulates execution and returns built-in sample output for supported actions.

Use `--mock` to:

- test the CLI without connecting to infrastructure
- develop playbooks locally
- validate parser and formatter behavior
- document examples safely

Examples:

```bash
midman run linux_health --profile sample-linux --mock
midman ask "show bgp summary" --profile sample-switch --mock
```

## Notes on Safety

The CLI does not expose free-form shell execution.

Requests pass through:

1. parser or direct action selection
2. command catalog lookup
3. safety validation
4. execution

If a request is unsupported or unsafe, it should fail rather than attempting an unapproved remote command.
