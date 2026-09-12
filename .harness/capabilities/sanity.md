# Sanity

Runs independent consistency checks across Harness authority, active Project authority, implementation, tests, and repository state.

## Skills

- `run` — orchestrate relevant sanity checks
- `harness-check` — Harness internal consistency
- `spec-check` — Spec-scope coherence when `spec` is active
- `trace-check` — Spec/code/test traceability when stable Spec identifiers are in use
- `repository-check` — repository/project consistency

## Project-model behavior

Under `spec`, Spec Check and Trace Check are available as Project-model checks.

Under `repository-native`, Sanity does not invent Spec scopes. Check the Goal Spec through the relevant Domain/App/Style/Tech/Build checks, confirm named native constraints remain truthful, and verify implementation/proof against the Goal Spec.

## Invariants

- Harness Assurance does not grade product quality
- Project-model-specific checks run only where their model semantics apply
- a repository-native project is not considered incomplete merely because no permanent Harness Spec topology exists
