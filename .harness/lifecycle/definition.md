# Lifecycle

Sequences one bounded Goal through one exclusive work branch to landing or abandonment.

This is a support family, not a capability: it owns no product artifact, which is the boundary the capability contract exists to police. It is therefore shaped lighter than that contract requires.

## Principle

Lifecycle decides when work may proceed, not what the work is.

The Harness has one first-class delivery unit: the **Goal**.

**One Goal = one work branch = one landing unit.**

The durable result of a successful lifecycle is configured-mainline Git history and the Project artifacts intentionally retained there. Goal state is temporary Harness operational context. It is not a second project history.

Landing is not finished until the exact configured-mainline receipt has been published to the configured remote. Deterministic approval and landing transaction anchors are maintained by the runtime as local mechanical state and are never Project authority. Abandonment is a single guarded runtime operation and has no persistent transaction state.

Learning-owned `doc/dreams/` proposal files are outside Lifecycle temporary state: they are non-authoritative persisted proposal state and may survive landings until Dream closes them.

Workflow owns lifecycle order, including that only branches land. The selected Collaboration model determines who may operate the landing boundary: `single-user` permits the owning workspace to proceed, while `cooperative-multi-user` transfers an approved Goal through an immutable handoff to one serialized integration-authority workspace.

## Owns

Through its skills: Goal intent state, repository bootstrap intent, work-branch lifecycle intent, landing/abandonment authorization, and landing boundaries. The Deterministic Runtime implements repository/ref/transaction mechanics selected by those owners.

Each skill declares its own narrow ownership; this definition does not restate it.

## Does not own

- specifications, implementation, tests, and setup documents
- harness authority
- what any goal is worth, beyond applying Goals and Decisions to it
- release/milestone/epic grouping outside the current Goal
- Learning-owned persisted Dream proposal state under `doc/dreams/`

## Skills

- **Goal** — one bounded outcome, its edge, useful execution-task decomposition, meaningful intermediate validation boundaries, and the branch-derived Goal document
- **Branch Start** — `bootstrap` prepares root README Harness orientation, initializes Git at the project root when missing, and creates the one-time pre-Goal baseline commit when no commits exist; `create` establishes the exclusive Git boundary for one Goal
- **Branch Land** — landing readiness, history preparation, temporary-state cleanup coordination, configured-strategy landing, and semantically authorized abandonment; exact Git/ref/transaction mechanics are delegated to the Deterministic Runtime

## Goal state

Every active Goal is represented by:

1. its exclusive work branch;
2. one branch-derived local Goal document at `doc/goals/<branch>.md`.

The branch identifies the delivery unit. The Goal document records what outcome needs to be true and only the meaningful constraints/decisions needed to understand that outcome. It is local Harness operational state and is intentionally ignored by Git.

The Goal document is not a task log, progress tracker, session transcript, serialized state machine, or implementation journal.

For branch `feature/api-keys`, the Goal path is:

```text
 doc/goals/feature/api-keys.md
```

Because the Git branch name is used as the path suffix, multiple local Goal documents can coexist without naming collisions. The branch-derived path is the Goal identity used for recovery.

Current execution state is reconstructed from Goal intent + Git + repository truth. Do not serialize `open`, `complete`, `approved`, `ready`, current-task, or completed-task state into Goal documents. Goal documents are never committed or pushed.

## Cooperative collaboration

Under the `cooperative-multi-user` Collaboration model, multiple trusted contributors may independently develop different exclusive Goal branches. A contributor remains responsible for its Goal until it publishes an immutable handoff containing the exact approved outcome and recovery context. The remote Git repository is only the handoff channel; it is not a distributed transaction coordinator or security authority.

One configured `integration-authority` workspace accepts handoffs and is the only role that may prepare or merge landing transactions. Acceptance is an explicit ownership-transfer boundary: after acceptance, contributor withdrawal is blocked until the integration authority lands or releases the handoff. Accepted branch, approval, and Goal recovery state are released as a unit rather than independently mutated.

If mainline moved after the handoff base, or the exact remote coordination boundary is uncertain, landing fails closed as `LANDING_BLOCKED`. Mechanical mergeability does not prove semantic compatibility. Human coordination releases the blocked handoff; the contributor reconciles against current mainline, re-checks/re-approves if required, and republishes. Harness intentionally does not add distributed locking, arbitrary concurrent landing, ACLs, consensus, or automatic semantic conflict resolution.

## Recovery

To recover an active Goal:

1. identify the current work branch;
2. derive and read `doc/goals/<branch>.md`;
3. inspect current Git status and branch history relative to configured mainline;
4. load only relevant specifications/Project context;
5. determine what remains to satisfy the Goal;
6. inspect runtime landing transaction state only when such a transaction exists.

Persist only state that cannot be safely and cheaply reconstructed. Landing approval/seals remain runtime transaction state because inference must not manufacture authorization.

## Invariants

- one active Goal owns one exclusive work branch
- a Goal branch contains no unrelated Goal
- every active Goal branch has exactly one branch-derived Goal document before implementation proceeds
- Goal documents record intended outcome, not workflow progress
- Git and retained Project artifacts are the durable history; Goal documents are temporary recovery state
- every branch entering configured mainline has explicit landing authorization for its exact approved outcome
- withdrawing/moving approval invalidates ordinary unmerged landing transaction authority; Session Resume never continues such a transaction from phase alone
- the branch-derived Goal document is local/ignored, never enters Git history, and is removed only after the Goal branch durably lands or is abandoned
- persisted `doc/dreams/` proposals are not branch-local temporary documents and are never removed by Lifecycle merely because a branch lands
- work branches follow Git History **Work branch ownership**; shared work branches are not a supported lifecycle state
- cooperative multi-user work uses independent Goal branches plus one serialized integration authority; contributors do not independently land mainline
- a published cooperative handoff is immutable until withdrawal, and an accepted handoff must be consumed or released before its transferred approval/branch/Goal state is changed
- stale cooperative handoffs fail closed as `LANDING_BLOCKED` for human reconciliation rather than inheriting approval across moved mainline
- no-op or explicitly aborted branches may be abandoned without landing; attributable dirty work being discarded is safety-committed first and the Deterministic Runtime verifies the exact destructive boundary before deletion
- product truth is never decided here

## Modes

Lifecycle has no direct executable modes; its skills own lifecycle actions.

## Inputs

A bounded owner request plus repository/project context relevant to executing it.

## Outputs

A landed or explicitly abandoned Goal branch, with temporary Goal state removed before successful landing. In cooperative multi-user mode, the handoff/acceptance boundary is also consumed or explicitly released so no stale integration ownership remains.

## Approval

Every Goal branch requires explicit user authorization before entering configured mainline. Final landing authorization normally constitutes acceptance of the Goal outcome. Intermediate approval exists only where another owning skill identifies a meaningful user-validation or consequential-decision boundary.

## Completion

Lifecycle completes when the Goal branch has either been landed and published/finalized according to repository strategy, or has been explicitly/no-op abandoned through the deterministic discard path, with no stale lifecycle transaction left behind.
