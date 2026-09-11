# Branch Land

Owns the semantic boundary for landing or abandoning one Goal branch. Exact Git/ref/transaction mechanics are delegated to the Deterministic Runtime.

## Define

A Goal branch may either:

- **land** — enter configured mainline as the verified Goal outcome; or
- **abandon** — be discarded without entering mainline when it is a no-op or the user explicitly authorizes destruction of unique work.

Every branch entering configured mainline requires explicit user authorization for the exact Goal outcome being landed.

## Inputs

As relevant:

- current Goal and local `doc/goals/<branch>.md`
- current specifications and Project decisions
- implementation/tests/evidence
- configured mainline
- current runtime approval/landing facts
- optional local `doc/session.md` restart cache

## Outputs

A verified and published/finalized landing, or a guarded abandonment, with local lifecycle state removed at the correct boundary.

## Owns

Landing readiness, landing authorization semantics, approval invalidation, history-preparation boundary, landing message, and semantic authority to abandon a branch.

Branch Land does not own Goal or Session content. Both are local Git-ignored recovery state and are removed automatically when the Goal lands or is abandoned.

## Modes

### `check`

Establish whether the current Goal branch is ready to seek landing authorization.

1. Run Goal `check`.
2. Run applicable specification/capability checks and Project verification.
3. Confirm the Goal edge is reached and no consequential unresolved decision remains.
4. Confirm the branch contains only the current Goal.
5. Confirm any already-recorded landing approval still matches the branch tree; if not, invalidate it.
6. Confirm Dream proposals whose transient evidence would otherwise be lost have been dispositioned.

Result may be `not ready`, `ready for approval`, or `ready under existing exact approval`.

### `land`

Use when the Goal branch is ready. The selected Collaboration model determines whether landing happens directly in one workspace or through the cooperative handoff boundary.

Common authorization boundary:

1. Present the bounded Goal outcome and meaningful verification evidence to the user.
2. Obtain explicit landing authorization unless an already-recorded exact authorization still applies.
3. Record authorization through Deterministic Runtime `approval record [--branch <branch>]`.
4. Prepare branch history according to Git History. History may be rewritten after approval only while the resulting full tree remains identical to the approved tree.
5. Re-run/confirm semantic verification affected by history preparation when needed.

Under **Single-user**, continue directly with the established deterministic landing path: `land prepare`, then `land merge`.

Under **Cooperative Multi-user**:

6. The contributor publishes the exact approved Goal through `handoff publish [--approved-by <actor>]`. Publication is immutable and binds the contributor's current mainline base.
7. The designated integration authority runs `handoff accept --branch <branch>`. This reconstructs local Goal/approval recovery state and accepts the exact handoff remotely.
8. The integration authority runs `land assess --branch <branch>`.
9. Continue only on `READY_FOR_LANDING`. If the result is `LANDING_BLOCKED`, do not auto-merge or extend approval. Follow its human-resolvable evidence: normally release the accepted handoff, let the contributor withdraw/reconcile/re-check/re-approve/republish, or intentionally supersede/abandon.
10. The integration authority invokes `land prepare`. It proves the current branch tree still equals the approved tree, confirms the accepted handoff remains live, and pins the exact mainline base plus ready commit.
11. The integration authority invokes `land merge [--message <goal name>]`.

For either model, the runtime rechecks approval/branch/mainline/remote exactness, builds the landing candidate off-mainline, updates mainline atomically, publishes the exact resulting mainline receipt to the configured remote, then removes the work branch, approval, transaction state, Goal file, and Session cache. A consumed cooperative handoff also exact-deletes its acceptance commit, handoff ref, and handed-off remote Goal branch.

After `land prepare`, branch history must not change. If it does, abort the ready transaction and prepare again after re-establishing the relevant checks.

### `invalidate approval`

Use when a previously recorded landing authorization no longer represents the exact current outcome or the user withdraws it.

Invoke Deterministic Runtime `approval drop [--branch <branch>]` only after establishing that semantic condition. Withdrawal removes a dependent `ready` transaction, and may also cancel an `integrating` transaction while configured mainline still equals its prepared base. Once mainline equals the recorded candidate, or the transaction is `merged`/`published`, recovery state is preserved and deterministic recovery must finish.

### `recover`

Use when a landing cannot continue because mainline moved, approval changed/was withdrawn, branch history changed after preparation, publication failed, or execution stopped mid-transaction.

- If the transaction is still `ready`, `land abort` may remove it; re-check against the current boundary and run `land prepare` again.
- Do not manually abort an `integrating`, `merged`, or `published` transaction. Approval withdrawal may cancel only the pre-crossing `integrating` case that the runtime can prove still has mainline at the prepared base. Once the candidate crossed mainline, use `land merge --branch <branch>` to continue deterministic recovery from the recorded candidate/receipt.
- If mainline moved before integration in Single-user, re-establish affected semantic/project checks and prepare again.
- If a Cooperative Multi-user handoff's mainline base is stale, treat `LANDING_BLOCKED` as a collaboration boundary: integration authority releases; contributor withdraws, reconciles, re-checks/re-approves as required by the changed exact tree, and republishes.
- Never silently extend old authorization to a changed Goal outcome or a different cooperative handoff base.

### `abandon`

Use when the Goal branch should not land.

1. Determine whether the branch is a true no-op or whether the user explicitly authorizes discard of unique branch work.
2. If attributable dirty work will be destroyed, safety-commit it first.
3. Invoke Deterministic Runtime `abandon discard --target <branch> --mode no-op|explicit`.
4. Add `--delete-remote` only when remote branch deletion is explicitly intended.

The runtime checks the current exact target boundary and performs deletion in one serialized command. `no-op` mechanically proves the target tree equals its merge-base tree. `explicit` relies on the semantic destructive authority established by Branch Land.

Durable information that must survive abandonment belongs in normal Project artifacts before discard, or on a separate independently authorized Goal.

## Completion

`land` completes only when the exact prepared Goal outcome is integrated into configured mainline, the resulting mainline receipt is published to the configured remote, and destructive finalization succeeds.

`abandon` completes when the guarded discard command succeeds.

`invalidate approval` completes when the approval ref is absent; a ready dependent landing transaction is also removed.

## Approval

Final landing authorization is the single mandatory Goal-level user approval boundary. It normally constitutes acceptance of the Goal outcome and authority to enter mainline.

Approval is exact and branch-bound by tree. History cleanup may rewrite commits without requiring renewed approval when the approved full tree remains identical. A material tree change requires fresh authorization.

If configured mainline moves after `land prepare`, affected checks must be re-established and the landing prepared again. Under cooperative handoff, mainline movement after publication blocks that immutable handoff; reconciliation normally changes the full branch tree to incorporate current mainline, so exact-tree approval must be re-established before a fresh handoff even when the Goal-specific intent is unchanged.

Explicit abandonment authority is separate from landing approval and authorizes destruction, not integration.

## Invariants

- every branch entering configured mainline has explicit exact landing authorization
- one Goal branch has one landing approval namespace: `refs/harness/landing-approval/<branch>`
- approval refs cannot be moved in place; changed authority is represented by drop then fresh record
- history preparation before `land prepare` preserves the approved full tree
- branch history does not change after `land prepare`
- single-commit Goal branches land directly; multi-commit Goal branches receive one merge boundary
- Goal and Session recovery files are Git-ignored local state, survive failed landing recovery, and are removed only after successful landing/abandonment
- moved mainline or withdrawn/moved approval never silently inherits old authority
- under cooperative multi-user, only the integration-authority role performs landing mechanics
- a cooperative handoff is immutable until withdrawn and cannot be contributor-withdrawn while integration-accepted
- stale cooperative handoff bases fail closed as `LANDING_BLOCKED`; mechanical mergeability does not establish semantic compatibility
- local landing is not reported complete before the exact mainline receipt is published to the configured remote
- integration candidates are built off-mainline and mainline is updated only after exact checks
- branch abandonment is one guarded exact-current-boundary operation and is never inferred from lack of interest
