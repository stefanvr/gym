# Dream

Synthesizes experience into a bounded, owner-reviewable proposal for improving future work.

## Define

Turn repeated or unusually high-value experience into one proposed change targeted at an existing owner.

Dream does not edit the target authority and does not accept its own proposal.

Use Dream when experience suggests that future executions should go differently. Invoke `propose` at the moment reusable experience is recognized when practical; do not wait for a lifecycle boundary merely because one will occur later.

Lifecycle boundaries may surface an already-identified unresolved proposal before temporary context is discarded. They must not search for or manufacture new Dream work merely because the boundary was reached.

## Inputs

Required:

- concrete experience or durable evidence
- the behavior, friction, surprise, or recurring pattern worth examining

As relevant:

- owner feedback
- landed history
- Sanity findings
- Knowledge/Setup/Build evidence
- existing guides, skills, specifications, or support-family rules
- prior Dream proposals about the same pattern
- existing `doc/dreams/<proposal>.md` retained state

## Outputs

One of:

- `no proposal` — evidence is too weak, too local, or already owned correctly
- a bounded Dream proposal naming:
  - observed experience/evidence
  - target owner
  - proposed change
  - expected execution difference
  - boundary/counterexample
  - unresolved risk or question
- an explicitly user-accepted, rejected, or deferred proposal for routing/retention
- removal of persisted proposal state whose retention boundary has ended

A proposal is non-authoritative.

## Owns

No authoritative state.

Owns non-authoritative persisted proposal state under `doc/dreams/`: Dream may create, refine, update retention state, and delete `doc/dreams/<proposal>.md` when its declared retention boundary ends.

Persist only when proposal review must survive an actual session/context loss, lifecycle cleanup would otherwise destroy evidence needed by the already-identified proposal, or the user asks to retain it. Deferral and landing alone do not require a file.

It does not modify the artifact named as target owner.

## Persisted shape

When a proposal is persisted, keep one file per proposal and make its retained state directly inspectable:

```markdown
# Dream: <proposal>

State: pending | deferred | accepted
Target owner: <one existing owner>

## Evidence
<observed evidence or durable pointers>

## Proposed execution difference
<what future execution would change>

## Boundary / counterexample
<where the proposal does not apply>

## Unresolved
<remaining risk/question, or none>
```

Use one actual state value, not the pipe-separated example. Keep the file sufficient for later review without copying unrelated project authority into it.

## Modes

### `propose`

Synthesize one candidate improvement from experience, pressure-test it with Grill, and surface one bounded approval-ready proposal while the evidence is fresh. This is the primary Dream trigger.

Prefer the smallest change that explains the evidence. Keep scrutiny proportional: enough to expose the proposal's assumption, boundary, counterexample, and cost without turning every learning into a ceremony.

### `review`

Re-open an existing proposal when it was deferred, challenged, or materially revised. Re-run Grill where the changed proposal needs renewed scrutiny and verify that its target owner is still correct.

Present the resulting proposal to the user. Do not treat silence or continuation as acceptance.

### `record`

After the user explicitly accepts, rejects, or defers the proposal, record that disposition when persistence is useful.

Acceptance only authorizes routing to the target owner; it does not itself modify authority. Deferral remains conversational by default and is persisted only when actual context loss or loss of required transient evidence would otherwise discard it.

When a proposal is persisted, set its retention state to exactly one of `pending`, `deferred`, or `accepted` as defined by Learning. Do not serialize rejected/resolved as retained state: route those files to `close`.

### `close`

Remove one persisted Dream proposal whose retention boundary has ended.

A proposal may be closed only when one of these is evidenced:

- the user rejected or withdrew it
- review established that it is superseded or otherwise no longer actionable
- the user accepted it and the receiving owning skill has durably taken custody through its normal owned state/artifact/lifecycle

A `pending` or `deferred` proposal remains unresolved and must not be deleted merely because a branch, Goal, session, or maintenance run is closing.

Delete only the corresponding `doc/dreams/<proposal>.md`; remove `doc/dreams/` itself when it becomes empty. Dream does not delete or rewrite the receiving owner's state while closing its own retained proposal.

## Method

1. When reusable experience is recognized, invoke `propose` and name the concrete experience before generalizing it. Prefer surfacing the proposal in the same conversation while its evidence is fresh.
2. Ask whether the lesson is already owned:
   - project-specific behavior → owning product/Tech/Setup skill
   - technology-conditioned operational learning → Knowledge
   - general collaboration/workflow/design behavior → candidate Guide/Harness change
3. Require an execution difference: what future action would change if the proposal were accepted?
4. Compare with prior evidence and avoid promoting a one-off preference into a universal rule without support.
5. Use Grill to challenge the proposal's assumption, boundary, evidence, and cost.
6. Name exactly one primary target owner.
7. Present the proposal distinctly from existing authority and ask for an explicit accept / reject / defer disposition when a decision is useful.
8. Wait for explicit user acceptance before routing it for promotion. Silence, continuation, landing, or persistence is not acceptance.
9. If the proposal must survive context/evidence loss, persist enough self-contained proposal state under `doc/dreams/` to support later review and set `State: pending`. If the user defers a persisted proposal, set `State: deferred`. Landing alone does not justify persistence.
10. After acceptance, invoke the existing owning skill through its normal lifecycle. Harness authority changes route to Harness Change `design`; technology knowledge routes to Knowledge Capture; project authority routes to its existing capability. Acceptance does not authorize changing an already-approved branch during landing. If an accepted proposal must remain across a handoff before owner takeover, set `State: accepted`.
11. Once the receiving owner has durably taken custody, or when the proposal is rejected/withdrawn/superseded, run `close`. Do not retain resolved files as a historical Dream backlog.
12. At a lifecycle cleanup boundary, surface only already-identified unresolved proposals whose transient evidence/context would otherwise be lost. If the user defers one and cleanup must proceed, persist enough evidence through Dream before the source state is removed. An already-persisted proposal does not block landing merely because it remains unresolved.

## Completion

`propose` completes with `no proposal` or one bounded proposal.

`review` completes when the deferred/revised proposal has been pressure-tested as needed, its target owner is known, and the user has enough information to accept, reject, defer again, or revise it.

`record` completes when an explicit user disposition has been recorded, a proposal that must survive loss has the correct retained state, or an accepted proposal has been passed toward the receiving owning skill.

`close` completes when the resolved/taken-over proposal file is absent and no unresolved retained proposal was discarded.

## Approval

Dream proposals require explicit user acceptance before any authoritative promotion.

This is proposal acceptance, not release approval. The target owning skill retains its normal approval and lifecycle rules.

## Invariants

- Dream proposes; it never self-promotes
- proposal and authority remain visibly separate
- user acceptance is explicit
- immediate event-driven proposal is the primary trigger
- lifecycle boundaries only preserve already-recognized unresolved proposals; they do not invent new Dream work
- `doc/dreams/` is Learning-owned persisted non-authoritative state and may survive branch landing
- only `pending`, `deferred`, or `accepted` are retained while a Dream file exists
- unresolved retained proposals are never deleted as generic lifecycle cleanup
- rejected/withdrawn/superseded proposals are removed, and accepted proposals are removed after the target owner durably takes custody
- the target artifact keeps exactly one owner
- evidence is not generalized beyond its boundary
- Grill scrutiny does not become a second decision owner
- rejected proposals do not quietly reappear as rules
