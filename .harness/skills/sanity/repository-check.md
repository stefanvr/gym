# Repository Check

Finds repository-level structural drift and stale temporary state relied upon by the Harness.

## Define

Repository Check discovers mechanically/semantically visible repository problems outside internal `.harness/` consistency. It does not own fixes.

## Inputs

Inspect as relevant:

- repository/Git state and configured mainline
- local `doc/goals/` Goal recovery files
- `doc/session.md`
- `doc/scratchpad/`
- runtime-reported landing approval state
- runtime landing transactions
- Project documentation and repository conventions relied upon by the Harness
- setup/developer affordance docs
- Learning persisted-proposal rules when `doc/dreams/` exists

`doc/dreams/` is deliberately not generic lifecycle temporary state. Persisted Dream proposals are Learning-owned non-authoritative retained state and may survive branch landings.

## Outputs

Repository findings routed to the owner that can repair them.

Examples:

- local `doc/goals/<branch>.md` exists but the named branch no longer exists → Goal/Lifecycle stale local recovery state; remove the orphan after confirming no recovery need remains
- active non-mainline branch lacks its branch-derived Goal file → Goal recovery-state finding
- `doc/session.md` no longer carries non-reconstructable context → Session Checkpoint `clear`
- `doc/scratchpad/` contains no unresolved Build finding → Build Check `close`
- stale/moved landing approval → Branch Land `invalidate approval` / `recover`
- stale runtime landing transaction → Branch Land recovery path
- broken Project-facing development instructions → route to their Project owner

When `doc/dreams/` exists, judge it by Learning's persisted-proposal retention boundary, not by Lifecycle cleanup.

## Owns

Discovery/routing of repository findings only. Repository Check does not edit Goal files, Project docs, Git refs, runtime state, Setup docs, or Dream proposals.

## Modes

### `check`

1. Establish repository/mainline facts through the Deterministic Runtime where applicable.
2. Compare local `doc/goals/` recovery files to existing work branches.
3. For the current non-mainline branch, verify the expected branch-derived Goal file exists before treating the branch as a normal active Goal.
4. Inspect tracked temporary state and runtime transactions for stale ownership/lifecycle boundaries.
5. Inspect repository conventions/documentation needed by the current Goal when there is a reason to suspect drift.
6. Route every finding; do not repair it here.

## Completion

Complete when relevant repository concerns have been checked and every finding is either absent or routed to an owner.

## Approval

No approval merely to discover repository drift. Destructive fixes, landing, or Harness design changes remain owned by their respective skills/boundaries.

## Invariants

- discovery and repair remain separate
- local Goal files are operational recovery state, not Project authority/history
- a Goal file path is derived from its branch; no archive/index is authoritative
- runtime approval/transaction facts are not reconstructed manually
- persisted Dream proposals are not classified as stale merely because a Goal lands
- do not treat unrelated Project documentation as Harness-owned merely because it is Markdown
