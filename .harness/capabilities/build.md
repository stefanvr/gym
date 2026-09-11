# Build

Turns already-understood goals and authoritative decisions into executable evidence and implementation.

Build does not silently decide product behavior.

## Purpose

Turn current goals and authoritative decisions into executable implementation/evidence while exposing missing decisions instead of inventing them.

## Owns

Build has no single durable product artifact. Its skills own bounded implementation/test/proof state; specifications, Goal state, Setup, and Git lifecycle remain with their owners.

Build additionally owns `doc/scratchpad/` as shared **temporary working state** across Build work. Build Implement, Proof, and Repair may add transient findings/notes when useful. Build Check uniquely owns closure/deletion after every finding is resolved or routed.

## Skills

- `implement`
- `proof`
- `repair`
- `check`

## Shared guides and mechanisms

- Workflow owns the jurisdiction-first authority model and lifecycle rules.
- Software Design governs implementation structure where project Tech is silent.
- General supplies cross-cutting development/verification principles.
- Git History owns correction-versus-requirement-change history semantics.

The current Goal constrains **what work is in bounds**. It is not a second authority over product or Tech specifications.

## Dependencies

Consumes the current Goal as a bounded outcome and the relevant product/Tech specifications as authority for behavior and technical decisions.

Build Proof may route operational findings to Setup and reusable technology findings to Knowledge. Missing product decisions route to their owning capability before implementation continues. Goal owns persistent task/checkpoint state.

## Invariants

- Build implements or proves; it does not quietly specify.
- The current Goal constrains work scope but does not override authoritative project specifications.
- A Goal/specification conflict is routed through Goal `brain` and the owning specification capability before coding continues.
- Product behavior has an authority before implementation.
- Proof contains no accidental product decisions.
- Repair does not disguise requirement changes.
- Software Design governs code shape unless project Tech explicitly overrides it.
- Goal owns persistent task state.
- Git History owns correction/requirement-change history semantics.
- executable evidence is repeatable where reasonable.
- `doc/scratchpad/` is Build-owned temporary state, never authority or backlog.
- scratchpad cleanup never discards an unresolved finding.
