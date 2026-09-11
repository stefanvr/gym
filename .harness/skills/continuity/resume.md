# Session Resume

Reconstructs only the context needed to continue safely after a new/cleared session.

## Define

Resume recovers current work from durable/reconstructable facts rather than conversation memory.

For Lifecycle, the primary recovery tuple is:

```text
current branch + doc/goals/<branch>.md + Git/repository state
```

The Goal file is local Git-ignored operational state. Runtime transaction state is consulted only when landing or abandonment has already begun.

## Inputs

- Deterministic Runtime `resume`
- current repository/Git state
- local branch-derived `doc/goals/<branch>.md` when on a Goal branch
- relevant Project specifications
- optional `doc/session.md` pointer/cache when it contains transient context that cannot be reconstructed
- retained `doc/dreams/` proposal names/state when relevant

## Outputs

A minimal current-work reconstruction and the next owning skill/action.

## Owns

Session reconstruction only. Resume does not create/modify Goal intent, specifications, approvals, Git history, or Project truth.

## Modes

### `resume`

1. Read shared Workflow and Routing.
2. Invoke Deterministic Runtime `resume` to establish Git/mainline/current branch, exact landing approval facts and landing transactions.
3. If Git is uninitialized, record that fact; Branch Start `bootstrap` owns initialization/baseline before Goal work.
4. If current branch is a non-mainline branch:
   - derive the Goal path returned by runtime (`doc/goals/<branch>.md`);
   - read it when present;
   - if it is missing, do not invent the Goal from code/history alone: ask the owner to restate/confirm the outcome before new implementation or landing approval.
5. If a runtime transaction exists:
   - unmerged landing transaction with live approval → load Branch Land and continue only from the mechanically valid phase;
   - approval missing/moved or mainline/base invalidated → Branch Land `recover`; do not infer authorization from transaction phase;
   - merged/published landing transaction → use runtime recovery/finalization path;
6. Load only specifications/capabilities relevant to the recovered Goal.
7. Inspect `doc/dreams/` names/state only when relevant to current work/immediate follow-up.
8. Read `doc/session.md` only if present and still useful; treat it as pointer/cache, never authority.
9. Determine what remains from Goal intent + Git + repository truth, then continue through the owning skill.

## Completion

Resume completes when the current Goal/transaction state and next safe owner/action are established without relying on conversation memory as authority.

## Approval

Resume never creates or infers approval. Only runtime-validated exact landing approval counts as recorded landing authority; otherwise Branch Land must obtain fresh explicit authorization where required.

## Invariants

- current Goal outcome comes from the local branch-derived Goal file, not inferred implementation
- Git/ref/transaction facts come from the Deterministic Runtime
- a missing Goal file on an active work branch is a recovery gap, not permission to manufacture intent
- a stale/missing approval never survives restart by virtue of transaction phase
- local Goal state is not Project history and is not pushed
- load context by need rather than replaying the entire repository/session

## DOC

`doc/session.md` is optional cache/pointer state for transient context not recoverable from Goal + Git + Project truth + runtime transaction facts. It is never authority.
