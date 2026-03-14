# Playbooks

Playbooks are declarative YAML definitions for repeatable diagnostic workflows in `MidMan`.

They allow contributors and operators to encode a known investigation pattern as structured metadata rather than an ad hoc sequence of commands.

## Purpose

Playbooks are useful when:

- the same checks are run repeatedly
- a diagnostic flow benefits from standardization
- a team wants a documented troubleshooting sequence
- mock-mode validation is useful during development

Playbooks should remain auditable and safe. They should describe approved diagnostic intent, not arbitrary remote execution.

## Recommended Schema

Phase 1 execution supports a simple ordered list of steps. For project documentation and future expansion, contributors should structure playbooks around the following fields:

- `id`
  Stable playbook identifier.
- `title`
  Human-readable name.
- `category`
  Broad domain such as `linux`, `network`, `management`, or `diagnostics`.
- `intents`
  List of supported operator requests or aliases that this playbook addresses.
- `command_group`
  Logical action group or catalog action used by the playbook.
- `expected_signals`
  What a healthy or interesting result should look like.
- `follow_up_steps`
  Suggested next checks for the operator after reviewing results.
- `caution`
  Notes about noise, scale, impact, or operational sensitivity.

In the current implementation, execution is driven primarily by `steps`. The richer fields above help the project evolve toward a more expressive and reviewable playbook model.

## Minimal Execution-Oriented Example

```yaml
name: daily-checks
steps:
  - action: linux_health
    profile: sample-linux
  - action: interface_status
    profile: sample-switch
  - action: management_reachability
    profile: sample-idrac
```

## Recommended Richer Example

```yaml
id: linux-basic-health
title: Linux basic health check
category: linux
intents:
  - check cpu on server
  - show server health
command_group: linux_health
expected_signals:
  - load averages remain within expected range
  - root filesystem has available capacity
  - memory pressure is not excessive
follow_up_steps:
  - review process-level CPU usage if load is elevated
  - check recent kernel messages if memory pressure is high
caution: Read-only diagnostics only. Intended for routine health validation.
steps:
  - action: linux_health
    profile: sample-linux
```

## Network Example

```yaml
id: network-bgp-summary
title: BGP neighbor summary
category: network
intents:
  - show bgp summary
  - check bgp neighbors
command_group: bgp_summary
expected_signals:
  - peers are established
  - expected prefixes are received
follow_up_steps:
  - inspect specific neighbors if sessions are down
  - review interface health if peer loss coincides with link changes
caution: Output volume may be higher on large edge devices.
steps:
  - action: bgp_summary
    profile: edge-router
```

## Management Example

```yaml
id: mgmt-reachability
title: Management endpoint reachability
category: management
intents:
  - is the idrac reachable
  - check bmc access
command_group: management_reachability
expected_signals:
  - endpoint answers on the expected TCP port
follow_up_steps:
  - confirm credentials and adapter type if reachability is good but login fails
  - validate upstream network path if the endpoint is unreachable
caution: Phase 1 supports reachability checks only, not full management workflows.
steps:
  - action: management_reachability
    profile: sample-idrac
```

## Adding a New Playbook

When contributing a playbook:

1. Start with a narrow, concrete operational goal.
2. Reuse existing approved actions where possible.
3. Add descriptive metadata so the intent is easy to understand during review.
4. Document expected signals in operator language.
5. Add caution text when output may be noisy, slow, or easy to misinterpret.

Good playbooks are:

- focused
- safe
- easy to review
- easy to test in mock mode

## Contribution Guidelines

Playbook contributions should:

- avoid write-oriented workflows
- map to approved command groups
- remain readable without extra tooling
- include test or example coverage when practical
- align with the project’s safety model

If a proposed playbook requires new remote commands, contributors should update the command catalog, document the rationale, and include safety review notes.
