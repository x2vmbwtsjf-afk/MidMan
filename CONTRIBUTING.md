# Contributing to MidMan

Thank you for considering a contribution to `MidMan`.

This project aims to be a dependable open-source foundation for safe infrastructure diagnostics. We welcome contributions from operators, network engineers, Python developers, documentation writers, and reviewers with strong safety instincts.

## Ways to Contribute

There are several useful ways to contribute:

- add or improve CLI features
- expand the command catalog for supported diagnostics
- improve parser coverage for real operator phrasing
- strengthen safety validation and negative test coverage
- add or refine playbooks
- improve example profiles and mock fixtures
- improve documentation, onboarding, and architecture notes
- review pull requests with a focus on safety and maintainability

## Development Setup

`MidMan` targets Python 3.12.

```bash
git clone <your-fork-or-repo-url>
cd midman
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run the test suite:

```bash
pytest
```

Inspect the CLI:

```bash
midman --help
midman catalog
midman doctor
```

## Pull Request Guidelines

Before opening a pull request:

- make sure the change is scoped and clearly explained
- include tests for behavior changes
- update documentation when user-facing behavior changes
- keep the safety model intact or explicitly justify any change to it
- prefer additive, modular changes over broad rewrites

Pull requests should include:

- a short problem statement
- a summary of the proposed change
- any safety implications
- test coverage notes
- follow-up items, if relevant

Small, focused pull requests are easier to review and merge.

## Coding Standards

The codebase is intended to stay simple, readable, and modular.

- target Python 3.12
- prefer explicit data flow over hidden magic
- keep modules focused on one responsibility
- use clear names for actions, profiles, and safety checks
- favor predictable behavior over clever abstractions
- preserve a clean CLI experience and useful terminal output

When in doubt, optimize for maintainability and operational clarity.

## Tests

Changes that affect parser logic, command validation, execution paths, playbooks, or CLI behavior should include tests.

Important areas to cover:

- intent parsing for valid and invalid inputs
- safety validation for blocked patterns
- catalog-to-command mapping
- mock-mode execution paths
- playbook loading and execution
- CLI command behavior

If you add a new action or playbook structure, add both positive and negative test cases where practical.

## Playbook Contributions

Playbooks should represent safe, repeatable workflows.

When contributing a playbook:

- keep the purpose narrow and easy to understand
- prefer diagnostics and observation over mutation
- document expected signals clearly
- note follow-up steps for human operators
- include any caution text if a check may be expensive or noisy

See [docs/PLAYBOOKS.md](docs/PLAYBOOKS.md) for the recommended structure.

## Safety Guidelines

Safety is a project-level requirement, not an optional enhancement.

Contributors should not:

- add free-form shell execution paths
- bypass the allowlist model
- introduce configuration-mode or write operations as diagnostics
- weaken shell injection protections without a strong review process

Contributors should:

- treat remote execution as a high-risk boundary
- default to read-only commands
- preserve strict validation for user input and mapped commands
- document any new command groups and their risk profile

If a contribution changes what can be executed on a remote system, it should receive especially careful review.

## Reviewing and Discussion

Questions, proposals, and design discussions are welcome in issues and pull requests. Constructive disagreement is healthy. Clear examples, real operator workflows, and concrete failure modes are especially helpful.

For community expectations, see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
