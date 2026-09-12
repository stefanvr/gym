# Goal

Defines and drives one bounded outcome. A Goal is the Harness's single first-class delivery unit.

## Define

A **Goal** is one bounded outcome with a clear edge that can be verified, authorized, and landed as one coherent branch outcome.

**One Goal = one work branch = one landing unit.**

A Goal may be achieved directly or decomposed into tasks. Tasks describe work required to reach the Goal; they are not lifecycle objects by default.

Every Goal is evaluated using the **Goals and Decisions** guide.

## Started

A Goal commonly starts from:

- an owner request
- a raw list of tasks
- a correction
- an elaboration
- additional information discovered during work

Incoming information is interpreted against the current Goal rather than automatically accepted as structure.

### Explicit start invocation

When the owner explicitly starts a named goal, interpret the start boundary before creating Goal state:

- `start goal <goal>, <input>` — treat trailing content as additional Goal input and reconcile it with the named outcome before work begins.
- `start goal <goal> nip` — `nip` explicitly means no additional input is being supplied. Do not ask for more input; establish the Goal from available specification/repository context and continue.
- `start goal <goal>` with neither trailing input nor `nip` — ask one question such as `Any input for <goal>, or just start?`. Do not silently interpret omission as `nip`.

The start syntax selects the input boundary; Goal `create` still owns establishment of the executable Goal.

## Goal document

Every active Goal branch has one **local, Git-ignored** Goal document derived mechanically from the branch name:

```text
branch: feature/api-keys
path:   doc/goals/feature/api-keys.md
```

The document contains the intended outcome and only constraints/decisions that materially affect understanding of that outcome. It is recovery state, not Project history, and MUST NOT be committed.

Minimum form:

```md
# Goal

<what outcome needs to be true>
```

Optional sections may capture meaningful constraints, acceptance conditions, or unresolved consequential questions.

Do not persist:

- status fields
- completed/current tasks
- implementation journals
- session transcripts
- check results that can be rerun
- landing approval

Those facts are reconstructed from Goal intent + Git + repository truth, or are held by the deterministic landing transaction when inference would be unsafe.

## Tasks

Break the Goal into execution tasks whenever decomposition materially improves understanding, sequencing, verification, delegation, or commit coherence. A genuinely single-step Goal may remain undecomposed.

Tasks are normally transient reasoning structure. They do not require their own document, lifecycle status, or approval merely because they exist.

A task may become an intentional intermediate user-validation checkpoint when later work should not proceed until the user can meaningfully validate the changed behavior. That checkpoint remains conversational unless some Project-owned artifact needs to record the decision.

While executing tasks, follow Git History's **Commit at task size** rule. Task-sized commits remain expected even though tasks are not persisted in the Goal document.

## Modes

### `brain`

Reconcile incoming information with the current understanding of the Goal.

Actions:

1. Re-establish the intended outcome.
2. Apply goal scrutiny.
3. Reconcile new information with current understanding.
4. Determine whether implementation was wrong or the requirement moved.
5. Identify missing consequential decisions.
6. Challenge unnecessary work.
7. Adjust execution-task decomposition where useful.
8. Identify any meaningful intermediate user-validation boundary.
9. Update the Goal document only when the intended outcome or a material constraint/decision changed.

`brain` changes understanding and proposed execution structure. It does not itself implement the Goal.

### `create`

Establish the executable Goal before implementation:

1. Apply goal scrutiny.
2. Establish the Goal edge.
3. Determine the smallest useful execution-task decomposition.
4. Identify meaningful intermediate validation boundaries, if any.
5. Establish the exclusive Goal branch through Branch Start `create`.
6. Derive `doc/goals/<branch>.md` from that branch and write the Goal outcome there.
7. Verify the Goal file is ignored by Git and leave it local.
8. If the active Project model is `repository-native`, route through Project Define to create `doc/goals/<branch>.spec.md` before consequential implementation begins; targeted Project Understand analysis may occur before or during this step. Under `spec`, route required definition work into the relevant stable Spec scopes.
9. Implementation may proceed once the active Project authority is implementation-ready.

### `check`

Evaluate current work against the Goal.

May establish:

- `no change`
- an intermediate checkpoint ready/complete result
- `goal ready`
- `goal complete`

These are current conclusions, not serialized Goal status.

When intended meaning has changed, update the Goal document and apply Change Impact before carrying old completion conclusions forward.

### `close`

Close Goal state only after its branch has durably landed or been deterministically abandoned. The Deterministic Runtime removes the exact branch-derived local Goal file as part of successful finalization/discard so a crash cannot erase recovery context before the branch outcome is durable.

Do not archive or move completed Goal files.

## Invariants

- a Goal is an outcome, not a task list
- one Goal owns one exclusive work branch and one landing unit
- a Goal has an edge before implementation begins
- every active Goal branch has one local branch-derived Goal document before implementation proceeds
- the Goal document records intended outcome, not progress/status
- raw tasks are evidence about the Goal, not automatically the plan
- execution-task decomposition is used whenever it materially improves coherent execution
- task-sized commits follow Git History even though tasks are normally transient
- user interruption happens only for meaningful validation or consequential decisions
- no unmade technology decision remains hidden inside the Goal
- do not build or define Project authority beyond the current Goal
- repository-native work uses one transient branch-derived Goal Spec; spec-mode work uses stable Spec scopes
- Goal documents are Git-ignored local recovery state; completed Goal documents are removed, never archived, and never committed or pushed as Project files (a cooperative handoff carries a copy of the Goal text only inside runtime coordination refs outside Project history, removed when the handoff is landed or withdrawn)

## Inputs

Required: an owner request, raw task/correction/elaboration, or other candidate bounded outcome.

As relevant: repository state, active Project authority, native documentation/constraints, and discovered information.

## Outputs

A scrutinized bounded Goal, useful transient task decomposition, current completion/readiness conclusions, and exactly one branch-derived Goal document while the Goal is active. Under `repository-native`, Project Define additionally owns one transient branch-derived Goal Spec while that Goal is active.

## Owns

The current Goal intent and local `doc/goals/<branch>.md` for its active branch. Goal owns the document content; the Deterministic Runtime may mechanically remove that exact file only after successful landing/abandon finalization. Goal does not own Project authority, implementation, Git history, or landing approval mechanics. Repository-native Goal Spec ownership belongs to Project Definition/shared Project reasoning under the active Project-model contract.

## Approval

Goal itself does not serialize approval state. Intermediate user validation occurs only when meaningful. Explicit final landing authorization is owned by Branch Land and normally constitutes acceptance of the Goal outcome.

## Completion

Goal work is complete when the Goal edge has been reached, required work/checks are complete, and any intentionally required intermediate validation has occurred. Goal `close` completes after the branch outcome is durable and its local Goal recovery file has been removed.
