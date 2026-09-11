# Learning

Compounds experience into reviewable improvement proposals without creating a second source of authority.

Learning is a support family. It owns no product artifact and no harness decision.

## Principle

`experience → Dream proposal → scrutiny → explicit user acceptance → owning skill → authority`

A proposal never promotes itself.

## Skills

- **Dream** — synthesize recurring or high-value experience into one bounded proposal, pressure-test it, retain it when needed, and route an accepted proposal to the artifact's existing owner.

## Sources

Dream may learn from:

- repeated corrections or friction across goal work
- explicit owner feedback about collaboration or workflow
- recurring Sanity findings
- Build/Setup/Knowledge surprises that appear broader than their current owner
- rejected or revised proposals when the reason is reusable
- landed work and repository history when they provide durable evidence

## Trigger and proposal state

Dream is primarily event-driven. When reusable cross-work experience is recognized, invoke Dream `propose` and surface the proposal while its evidence is fresh. Do not wait for Goal completion, landing, or maintenance merely to trigger Dream.

Lifecycle boundaries are only a safety net: before temporary context that contains an **already-identified** unresolved Dream proposal is discarded, surface that proposal for explicit accept / reject / defer disposition or persist enough proposal state for later review. The boundary does not search for new lessons merely because it was reached.

Dream output is non-authoritative.

By default, keep a proposal conversational, including when the user defers it. Persist it under `doc/dreams/` only when proposal/review state must survive an actual session/context loss, when lifecycle cleanup would otherwise destroy evidence needed to review the already-identified proposal, or when the user asks to retain it. Landing by itself is not a reason to persist.

### Persisted proposal state

`doc/dreams/<proposal>.md` is **Learning-owned persisted proposal state**. It is non-authoritative repository state, not Lifecycle temporary state, and may survive work-branch landings. Its existence alone never blocks landing and Branch Land never removes it as cleanup.

A persisted proposal must carry enough context to remain intelligible after the transient source disappears: the observed evidence or durable pointers to it, target owner, proposed execution difference, boundary/counterexample, and current retention state.

Use exactly these lowercase retention states while a file exists:

- `pending` — the proposal is identified but still awaiting explicit user disposition/review
- `deferred` — the user explicitly deferred the proposal
- `accepted` — the user accepted the proposal, but the receiving owner has not yet durably taken custody

Rejected, withdrawn, superseded, or otherwise resolved proposals are not retained under `doc/dreams/`. Dream `close` removes their files. An accepted proposal is also closed once the receiving owner has durably taken custody through its normal state/artifact/lifecycle; the Dream file is not an alternate backlog or permanent history.

## Does not own

- Guides
- Workflow, mechanisms, either owned vocabulary file, contracts, or skills
- product specifications
- technology Knowledge entries
- Setup state
- lifecycle approval
- implementation

Those remain with their existing owners.

## Invariants

- learning compounds through proposals, never silent mutation
- explicit user acceptance is required before promotion
- immediate proposal is the primary trigger; lifecycle review is only a loss-prevention safety net
- lifecycle boundaries never manufacture Dream proposals by ritual
- persisted Dream proposals are non-authoritative Learning state, not branch-local temporary state
- unresolved persisted proposals may survive landing; landing never deletes them merely to clean the branch
- resolved proposal files are removed by Dream rather than accumulating as a second backlog/history
- the receiving owning skill performs the authoritative change
- one experience is not generalized beyond its evidence
- repeated evidence is preferred for broad process/style changes
