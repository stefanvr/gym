# Branch Start

Establishes the deterministic Git boundary for Project bootstrap and one Goal.

## Define

A **work branch** is the exclusive Git boundary for exactly one Goal.

**One Goal = one branch = one landing unit.**

Branch Start creates the branch; Goal owns the outcome recorded in the local Git-ignored `doc/goals/<branch>.md` recovery file.

## Inputs

For `bootstrap`: explicit Project-bootstrap intent or a Goal that cannot start because Git has no committed mainline.

For `create`: an already-scrutinized bounded Goal and a chosen valid branch name.

For `bootstrap`, the working tree must still represent pre-work repository seed state; requested Goal/product work must not already have been introduced as baseline content. Bootstrap also inspects root `README.md` so the shipped Harness placeholder becomes Project orientation without overwriting an existing Project README.

## Outputs

For `bootstrap`: an established committed configured/bootstrap mainline and prepared root README orientation.

For `create`: one exclusive work branch for the Goal.

## Owns

Project bootstrap intent and the semantic decision to create one exclusive Goal branch. Deterministic repository initialization/baselining and branch creation mechanics are delegated to the Deterministic Runtime.

Branch Start owns no Goal content, specification, implementation, approval, or landing state.

## Modes

### `bootstrap`

Use when the user explicitly asks to bootstrap the Project, and automatically before Goal `create` when the repository has no committed mainline.

1. Inspect root README and apply the shipped Harness template/onboarding rule without destroying existing Project content.
2. Confirm the current non-ignored content is pre-work seed state rather than requested Goal work.
3. Invoke Deterministic Runtime `repo status`.
4. If Git/mainline is not established, invoke `repo bootstrap` with explicit seed staging only when the intended baseline requires it.
5. Verify runtime output identifies a committed baseline/mainline.
6. Verify bootstrap introduced no Goal/work-branch state.

### `create`

Use once for each Goal.

1. Choose a concise branch name that identifies the Goal.
2. Invoke Deterministic Runtime `branch start --name <branch>` from configured mainline unless repository policy requires another explicit base.
3. Verify the new branch is current and exclusive to this Goal.
4. Return control to Goal `create` to write the local Git-ignored `doc/goals/<branch>.md` before implementation proceeds.

Do not reuse one branch for unrelated Goals. Do not create a second Goal on an already active Goal branch.

## Completion

`bootstrap` completes when README orientation is prepared as applicable and a committed mainline/baseline exists without requested Goal work smuggled into it.

`create` completes when the runtime reports the exclusive Goal branch at the intended base.

## Approval

No user approval is required merely to create a non-destructive work branch after the Goal has been established. Approval for entering configured mainline is owned later by Branch Land.

## Invariants

- implementation never begins directly on configured mainline
- each active Goal has one exclusive work branch
- a Goal branch contains no unrelated Goal
- branch creation mechanics are runtime-owned rather than reproduced in prose commands
- bootstrap never launders requested Goal work into the pre-Goal baseline
