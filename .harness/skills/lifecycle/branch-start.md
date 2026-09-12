# Branch Start

Establishes the deterministic Git boundary for Project bootstrap and one Goal.

## Define

A **work branch** is the exclusive Git boundary for exactly one Goal.

**One Goal = one branch = one landing unit.**

Branch Start creates the branch; Goal owns the outcome recorded in the local Git-ignored `doc/goals/<branch>.md` recovery file.

Bootstrap is a pre-Goal repository-establishment operation. It may create the first committed configured/bootstrap mainline directly because no Goal lifecycle exists yet; requested Goal/product implementation must never be included in that baseline.

## Inputs

For `bootstrap`: explicit Project-bootstrap intent or a Goal that cannot start because Git has no committed mainline.

The standalone distribution begins with Project and Collaboration selections explicitly unconfigured in `.harness/composition/active.json`. Bootstrap's first user decision is whether an **existing committed repository** should use `main-shadow` for confidence-building onboarding. Only after that decision does bootstrap obtain an explicit Project-model choice and Collaboration-model choice.

This distribution supports:

- Project model `spec`: shared Domain/App/Style/Tech reasoning persists accepted conclusions in stable Harness Spec scopes and uses Spec topology.
- Project model `repository-native`: shared reasoning uses repository evidence/native authority and persists accepted Goal-specific conclusions in one transient branch-local Goal Spec. It does not treat existing code as desired specification automatically.
- Collaboration model: exactly one of `single-user` or `cooperative-multi-user`. No Project or Collaboration model may be silently selected.

For `create`: an already-scrutinized bounded Goal and a chosen valid branch name.

For `bootstrap`, the working tree must still represent pre-work repository seed state; requested Goal/product work must not already have been introduced as baseline content. Bootstrap also inspects root `README.md` so the shipped Harness placeholder becomes Project orientation without overwriting an existing Project README.

`main-shadow` is an onboarding safety boundary, not a second landing mode. When selected for an existing repository, the runtime creates `main-shadow` at the existing repository mainline tip, switches to it, rewrites Harness runtime configuration on that branch so `main-shadow` is the configured mainline, and leaves the original repository mainline unchanged. All ordinary Goal branching, approval, landing, and publication semantics then target `main-shadow` exactly as they would target any configured mainline.

## Outputs

For `bootstrap`: an explicitly configured operating composition, an established committed configured/bootstrap mainline when needed, prepared root README orientation, and a clear statement that bootstrap did not publish the baseline to the configured remote.

For `create`: one exclusive work branch for the Goal.

## Owns

Project bootstrap intent, bootstrap-time composition choice/consent, and the semantic decision to create one exclusive Goal branch. Deterministic composition persistence, repository initialization/baselining, and branch creation mechanics are delegated to the Deterministic Runtime.

Branch Start owns no Goal content, specification, implementation, approval, or landing state.

## Modes

### `bootstrap`

Use when the user explicitly asks to bootstrap the Project, and automatically before Goal `create` when the repository has no committed mainline or the Harness composition is still unconfigured.

1. Inspect repository state and root README before mutation. Apply the shipped Harness template/onboarding rule without destroying existing Project content.
2. **Ask first whether confidence-building onboarding should use `main-shadow`.** Explain that this is available only when the repository already has committed history. If selected, the repository's existing mainline remains untouched and Harness uses `main-shadow` as configured mainline. If the repository is new/unborn, explain that `main-shadow` is not applicable and continue with normal bootstrap.
3. Confirm the current non-ignored content is pre-work repository/Harness seed state rather than requested Goal work. In `main-shadow` mode, this seed baseline is committed on `main-shadow`, never on the original mainline.
4. Read `.harness/composition/active.json`. If Project/Collaboration selection is already valid, report it and do not ask again. If it is explicitly unconfigured, obtain the two operating-model decisions before mutation:
   - explain the operational distinction between `spec` and `repository-native`;
   - ask the user to choose one Project model explicitly;
   - ask the user to choose `single-user` or `cooperative-multi-user`, explaining the operational distinction; do not infer or default either choice.
5. Invoke Deterministic Runtime `repo status`.
6. Before a new baseline commit is created, tell the user that bootstrap will establish the pre-Goal baseline directly on **local configured/bootstrap mainline**, and that **bootstrap will not push mainline or otherwise publish that commit to the configured remote**. In `main-shadow` mode, explicitly identify the original source mainline and say it will not be changed.
7. Invoke `repo bootstrap --project-model <chosen-project-model> --collaboration-model <chosen-collaboration-model>` with explicit seed staging only when the intended baseline requires it. Add `--main-shadow` when the user selected shadow onboarding. For a standalone Harness dropped into an existing repository, normally use `--all-seed-files` only after confirming the whole non-ignored tree is the intended onboarding seed. When composition was already valid, the runtime may be invoked without repeating the model flags.
8. In `main-shadow` mode, verify runtime output reports `mainline: main-shadow`, `main_shadow: true`, the shadow source when newly established, and `remote_publication: not attempted by bootstrap` / `remote_changed_by_bootstrap: false`. Otherwise verify the normal configured baseline/mainline output and the same no-publication boundary.
9. Tell the user after completion that the bootstrap baseline is local only, identify the local configured mainline/commit when one was created, and state that the remote was not changed. If `main-shadow` was selected, also state that the original repository mainline was left untouched and that future Harness Goal landings target `main-shadow` unless repository configuration is deliberately changed later.
10. Verify bootstrap introduced no Goal/work-branch state.

When `repository-native` is chosen, do not silently reinterpret existing repository documentation or code as desired authority. Bootstrap selects the model only; Goal-specific repository understanding and Goal-Spec definition happen after the Goal branch exists.

### `create`

Use once for each Goal.

1. Choose a concise branch name that identifies the Goal.
2. Invoke Deterministic Runtime `branch start --name <branch>` from configured mainline unless repository policy requires another explicit base.
3. Verify the new branch is current and exclusive to this Goal.
4. Return control to Goal `create` to write the local Git-ignored `doc/goals/<branch>.md` before implementation proceeds.

Do not reuse one branch for unrelated Goals. Do not create a second Goal on an already active Goal branch.

## Completion

`bootstrap` completes when composition is explicitly configured, README orientation is prepared as applicable, a committed mainline/baseline exists when needed without requested Goal work smuggled into it, and the user has been told that bootstrap did not push the baseline to the remote. When `main-shadow` was selected, completion additionally requires that the original mainline is unchanged and `main-shadow` is the runtime's configured mainline.

`create` completes when the runtime reports the exclusive Goal branch at the intended base.

## Approval

The `main-shadow` onboarding choice, Project-model choice, and Collaboration-model choice are bootstrap configuration decisions. The first must be explicitly asked during onboarding; the latter two require explicit user input when the standalone distribution is unconfigured. None is landing approval.

No user approval is required merely to create a non-destructive work branch after the Goal has been established. Approval for entering configured mainline is owned later by Branch Land.

## Invariants

- implementation never begins directly on configured mainline; the bootstrap baseline is the pre-Goal repository-establishment exception and contains no requested Goal implementation
- bootstrap never silently selects a Project or Collaboration operating model
- bootstrap asks about `main-shadow` before operating-model selection; shadow onboarding is never inferred merely because a repository already exists
- `main-shadow` onboarding is only valid for an existing repository with committed history
- when selected, `main-shadow` begins at the existing repository mainline tip and becomes Harness configured mainline without moving or rewriting the original mainline
- an existing divergent `main-shadow` branch is never repurposed automatically
- bootstrap presents both supported Project models accurately and never silently selects either
- bootstrap baseline publication is local-only; bootstrap never pushes configured mainline or claims the remote changed
- each active Goal has one exclusive work branch
- a Goal branch contains no unrelated Goal
- branch creation mechanics are runtime-owned rather than reproduced in prose commands
- bootstrap never launders requested Goal work into the pre-Goal baseline
