# Session Checkpoint

Persists a minimal restart pointer only when Goal + Git + Project truth are insufficient to reconstruct an immediate continuation.

## Define

Most sessions need no checkpoint. The active Goal is recoverable from the current branch plus local `doc/goals/<branch>.md` and repository state.

Use Session Checkpoint only for transient context that is meaningful, cannot be cheaply reconstructed, and should survive a context reset.

## Inputs

As relevant:

- current Goal and branch-derived Goal file
- current repository/runtime facts
- current Project authority/decisions
- transient manual-step/provider/context details not otherwise durable
- existing `doc/session.md`

Do not duplicate:

- the Goal outcome already present in `doc/goals/<branch>.md`
- Git status/history/mainline facts
- landing approval or runtime transaction state
- full Project-authority documents
- completed task lists
- Dream proposal state owned by Dream

## Outputs

An optional compact `doc/session.md` restart pointer, or its removal when no longer needed.

## Owns

Only `doc/session.md` and only as non-authoritative transient cache.

## Modes

### `update`

Create/update `doc/session.md` only when an actual context loss would otherwise lose useful non-reconstructable continuation information.

Keep it compact. Prefer pointers and the one fact needed to resume over summaries of durable artifacts.

### `clear`

Delete `doc/session.md` when its transient information is no longer needed or has become durable elsewhere.

## Completion

`update` completes when the minimum non-reconstructable restart context is persisted without duplicating authority.

`clear` completes when `doc/session.md` is absent.

## Approval

No approval is required to maintain this temporary pointer. It must never encode user authorization as a substitute for the runtime landing approval ref.

## Invariants

- checkpoint only what cannot be reconstructed from Goal + Git + Project truth
- `doc/session.md` is cache, never authority
- do not copy full Project-authority documents, history, or task-progress logs
- do not duplicate the Goal file
- Dream owns persisted Dream proposals
- `doc/session.md` is Git-ignored local state and runtime finalization removes it after landing or abandonment
