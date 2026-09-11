# Cooperative Multi-user Collaboration Model

Defines the Cooperative Multi-user collaboration model for trusted contributors working on independent Goal branches with one explicitly serialized integration authority. Whether it is active is decided only by `.harness/composition/active.json`. Its assured operating profile is defined in [Harness Assurance](../harness-assurance.md).

This model is deliberately a **coordination model, not a security system**. Actor names and roles are provenance/guardrail metadata. They are not cryptographic identity, ACLs, signatures, or proof that an actor is authorized outside the trusted operating agreement.

## Constitutional boundary

**[COLLAB-01]** Cooperative multi-user work uses independent exclusive Goal branches and immutable approved handoffs. Only the configured `integration-authority` workspace may run landing mechanics. A stale, moved, withdrawn, incompatible, or otherwise uncertain handoff fails closed as `LANDING_BLOCKED` with evidence for human resolution; Harness does not automatically extend approval across changed mainline state or semantically resolve competing Goals.

## Roles

Each clone/workspace using this model configures local coordination metadata in the Git common directory:

- `contributor` — may develop, check, approve, publish, and withdraw its own independent Goal handoffs.
- `integration-authority` — is the single serialized landing workspace. It may accept/release handoffs and is the only role allowed to `land prepare`, `land merge`, or resume landing recovery.

An integration authority may also create ordinary Goal work, but landing still crosses the same integration boundary.

Role configuration is local runtime state and is intentionally not committed as Project truth.

## Independent Goal branches

The collaboration unit remains the kernel invariant:

> one Goal = one exclusive work branch = one landing unit

A normal cooperative workflow does not share one mutable Goal branch among contributors. A contributor owns its Goal branch until publishing a handoff. Different contributors may independently work on different Goal branches from the same mainline base.

## Immutable handoff

The immutable handoff boundary transfers an exact approved Goal outcome to the integration authority without transferring conversation state.

`handoff publish` requires:

- a clean worktree
- the contributor's current Goal branch
- non-empty local branch-derived Goal recovery text
- a live exact landing approval
- current branch tree equal to the approved tree
- the Goal branch containing the contributor's current configured mainline
- local configured mainline aligned with the configured remote mainline

The handoff binds:

- branch name
- exact ready commit
- exact approved tree and approval-source commit
- contributor's exact mainline base at handoff
- Goal recovery text by SHA-256 and content
- contributor actor
- optional approval actor as coordination provenance
- Harness release

The handoff is published through Git runtime refs plus the exclusive remote Goal branch. It is immutable. Changing the Goal outcome or reconciliation boundary requires explicit withdrawal followed by a fresh handoff.

The handoff ref and the exclusive remote Goal branch are runtime coordination state, not Project history or Project authority.

## Acceptance transfer

`handoff accept` is performed only by the integration authority.

Acceptance:

1. fetches the exact published Goal branch and handoff object;
2. verifies branch/tree/approval/Goal recovery bindings;
3. records the acceptance by replacing the exact handoff commit at the handoff ref with an acceptance commit whose only parent is that handoff (one compare-and-swap on the same ref that contributor withdrawal leases, so a racing accept and withdraw cannot both succeed);
4. reconstructs the local Goal document and approval ref in the integration workspace;
5. records local accepted-handoff recovery state;
6. switches the integration workspace to the imported Goal branch.

Once accepted, the contributor may not withdraw that handoff. The integration authority must either land it or explicitly `handoff release` it. Release compare-and-swaps the handoff ref back to the exact handoff commit and removes local imported state, leaving the contributor's immutable remote handoff intact so the contributor can then withdraw/reconcile it.

Acceptance and withdrawal are mutually exclusive at the remote: exactly one of two racing operations succeeds, and the loser changes nothing.

## Serialized integration

The configured integration-authority workspace is the only landing actor. Its existing repository/common-directory lifecycle lock serializes local lifecycle mutations there.

This model does **not** claim a distributed lock across clones. Serialization is an operating contract plus the integration-role runtime guardrail. Trusted contributors do not independently land mainline from their clones.

Before preparation, `land assess` compares the accepted handoff with current mainline and remote coordination refs.

A handoff is `READY_FOR_LANDING` only when the current configured mainline still equals the handoff base and the exact remote branch/handoff/acceptance boundaries remain live.

## Human-resolvable blocked state

Mainline movement after handoff does not silently inherit old authority. A representative result is:

```text
LANDING_BLOCKED
cause: configured mainline moved after the contributor's approved handoff base
evidence: handoff base, current mainline, ready commit, contributor/approval/integration actors
next: release -> contributor withdraw/reconcile/re-check/re-approve/republish, or intentionally supersede/abandon
```

The Harness may mechanically identify that boundaries differ. It does not infer that two Goal outcomes are semantically compatible merely because Git could merge them.

This means two contributors can independently reach the integration boundary. If Goal A lands first, Goal B may need a fresh handoff against the new mainline even when the conflict is only concurrency rather than a product disagreement. This is an intentional simplicity/safety trade-off that preserves exact-tree approval.

## Recovery and finalization

Accepted-handoff identity is copied into the deterministic landing transaction. Existing crash/restart rules remain authoritative.

Before mainline is crossed, the exact accepted handoff/acceptance/remote Goal branch is revalidated. After the recorded candidate has crossed mainline, deterministic transaction recovery takes precedence so a crash cannot strand an ambiguous integration.

Successful landing consumes and atomically exact-deletes the accepted handoff ref and handed-off remote Goal branch, then clears local accepted-handoff state along with ordinary landing cleanup.

## Explicit non-goals

- distributed lock service
- arbitrary contributors landing concurrently from independent clones
- shared mutable Goal branches as normal collaboration
- adversarial permissions or ACL framework
- cryptographic approval or identity
- consensus protocol
- automatic semantic conflict resolution
- central Harness server/database
- mapping Spec scopes to human ownership

## Project-model independence

This Collaboration model knows only Goal/lifecycle/repository boundaries. It must not depend on Domain/App/Style/Tech, Spec scope topology, or any other Project-model-specific representation.

When repository-native is implemented, the same handoff and serialized-integration contract should apply without redesigning lifecycle semantics.
