# Domain

Defines and orchestrates the rules, concepts, events, and data of the world being modelled.

Domain owns the desired domain state.

It does not own user interface structure, interaction design, visual presentation, technology choices, or implementation structure.

## Purpose

Produce and maintain authoritative Domain state. Domain is also the broad intake/orchestration boundary for a Domain concern that cannot yet be safely reduced to one narrow Domain skill.

## Owns

All active Spec scopes whose topology authority is `domain`, such as `domain.identity` or `domain.billing`.

Physical paths are resolved by Spec Topology; the file path is not the authority identity. Domain also owns its own topology entries and the `depends_on` edges declared by those Domain scopes.

The specification states the desired domain state. It does not retain who proposed a term, confidence markers, workshop notation, brainstorm provenance, or decided-but-unbuilt markers. Those belong to working history or non-authoritative method/brainstorm material.

Once a decision is accepted into a Domain scope, it is simply the specification.

## Skills

- `language`
- `events`
- `rules`
- `data`
- `check`

## Shared guides and mechanisms

- Authority Orchestrator Contract for broad Domain intake and delegation
- Spec Topology for stable scope identity, scoped loading, and graph impact
- Method Pack Contract for activated discovery/modelling methods
- Grill for deliberate pressure-testing of consequential candidates before authority
- Goals and Decisions for current-goal boundaries
- Authorship Stance when intent/terminology authorship matters

## Dependencies

Consumes Goal, method, and Brainstorm material as context. App and Build consume Domain authority; technical concerns route to Tech.

Under the default method selection, Domain may use Interview Me and Event Storming. Design may delegate Domain concerns here. Method output remains non-authoritative until a Domain skill incorporates an accepted conclusion.

## Orchestration

When a concern is clearly Domain-owned but broad or not yet decomposed, route to Domain before prematurely choosing Language, Events, Rules, or Data.

Domain then:

1. establishes the Domain slice required by the current Goal
2. identifies the affected stable Domain scope(s)
3. loads those scopes plus relevant transitive dependencies rather than the full Domain corpus by default
4. selects only useful active methods or narrow Domain skills
5. routes accepted method conclusions through Language, Events, Rules, and/or Data into the owning scopes
6. reconciles those edits inside the Domain boundary
7. uses reverse dependents as Change Impact candidates when Domain meaning changed
8. invokes Domain Check locally and affected graph checks before dependent completion where materially required

Domain does not reproduce child-skill procedures. Narrow, already-understood concerns may route directly to their owning Domain skill.

## Activity selection

Not every Domain goal needs every skill, method, or Domain scope.

Select only the work and topology closure required by the current Goal. Event Storming is useful discovery for consequential/unclear flows; it is not a mandatory precondition for Domain Events.

## Shared rule

Revision during Domain work is expected. Revision after implementation has already depended on the wrong specification is the failure to avoid. The deadline for understanding is the start of implementation, not the start of specification.

## Invariants

- Domain owns world rules, not UI behavior.
- Stable scope identity, not file placement, determines Domain authority.
- The specification states desired state rather than provenance or workshop state.
- Method and Brainstorm material are input, not authority.
- Every required domain concept is named.
- Every rule has the data it needs.
- Event flows connect causally.
- Domain work stops at the boundary required by the current Goal.
- Within each Domain scope, Domain Rules assigns stable local `R-n` identifiers; the canonical cross-scope citation is `<scope-id>:R-n`.
- Broad orchestration never creates a second Domain source of truth.
