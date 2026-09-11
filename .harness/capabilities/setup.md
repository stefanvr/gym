# Setup

Documents how a human or automation prepares the environments required to develop and run the project. Setup is operational documentation, not technology choice.

## Purpose

Make development and application/runtime environments reproducibly operable, including explicit human/privileged boundaries and verification.

## Owns

Through its skills, Setup owns `doc/setup-dev-env.md` and `doc/setup-app-env.md`. It does not own the Tech choices those documents operationalize.

## Skills

- `dev` — document and verify development-environment preparation
- `app` — document and verify application/runtime/deployment preparation

## Shared guides and mechanisms

- General verification/evidence principles
- Workflow manual-boundary rule

## Dependencies

Consumes Tech choices, Build Proof findings, reusable Knowledge, and verified real-environment observations. Tech retains technology/architecture decisions. Build Proof owns routing of newly discovered operational facts.

## Invariants

- Setup records verified operational consequences, not technology choices.
- Workflow's manual-boundary rule governs actions the agent cannot perform; Setup skills own the project-specific recording/verification detail.
- setup evidence checks resulting state where practical.
