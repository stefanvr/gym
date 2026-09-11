# Setup Dev

Documents and verifies what is required to bring a fresh machine to a development-ready state for this project.

## Define

Document and verify how a fresh machine becomes capable of developing this project.


## Source of truth

The content is project-specific and may depend on Tech choices.

Do not infer setup merely from the Tech specification.

Prefer knowledge discovered through Build Proof and verified development use.

## Content

Typical sections:

- prerequisites and versions
- development bootstrap
- canonical install/build/test/run commands
- developer affordances
- manual/privileged steps
- verification

## Manual and privileged steps

For every action automation cannot or should not perform, record:

- who performs it
- why it is manual
- exact action/command
- when it is required
- expected result
- how to verify success

Examples:

- `sudo`
- administrator/system package installation
- browser authentication
- SSH key setup
- private registry login
- device permissions

## Verification

A setup step should have an observable success check where failure can be silent.

Do not report an unrun step as verified.

## Inputs

Required:

- project Tech choices relevant to local development
- verified setup findings from Build Proof or actual development use

As relevant: existing dev setup doc, reusable Knowledge, and current machine constraints.

## Outputs

A verified/updateable `doc/setup-dev-env.md` covering prerequisites, development bootstrap commands, developer affordances, manual boundaries, and readiness checks.

## Owns

`doc/setup-dev-env.md`. It does not own Tech choices, personal machine configuration itself, or reusable technology Knowledge.

## Modes

### `document`

Create or update development setup instructions from verified operational knowledge.

### `check`

Verify a development environment against the documented requirements and report blockers/manual steps.

## Approval

No approval for documentation/checking. Manual/privileged actions are performed by the owner when required; technology decisions discovered during setup route to Tech.

## Invariants

- setup facts are project-specific consequences, not technology rationale
- do not infer success from a command description or exit code alone where failure can be silent
- Workflow manual boundaries are explicit in the setup artifact
- unrun steps are not marked verified
- secrets/personal details are not committed

## Completion

Complete when a fresh machine can be brought to a verified development-ready state, with all unavoidable human steps explicit.
