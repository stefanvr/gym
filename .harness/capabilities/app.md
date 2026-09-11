# App

Defines and orchestrates what a user does in the product and where those actions surface.

App owns the desired user-facing application structure.

It does not own rules of the domain, visual/audio styling, technical implementation, implementation architecture, or developer-only tooling.

## Purpose

Produce and maintain authoritative application structure describing what users do, the steps required, how those steps are interacted with, which user-facing surfaces exist, and where each interaction happens.

App is also the broad intake/orchestration boundary for an App concern that cannot yet be safely reduced to one narrow App skill.

## Owns

All active Spec scopes whose topology authority is `app`, such as `app.customer` or `app.admin`.

Physical paths are resolved by Spec Topology. App owns its own topology entries and dependency edges; file placement alone never transfers App authority.

## Skills

- `story-map`
- `interaction`
- `surfaces`
- `check`

## Shared guides and mechanisms

- Authority Orchestrator Contract for broad App intake and delegation
- Spec Topology for stable scope identity, scoped loading, and graph impact
- Method Pack Contract for activated discovery/structuring methods
- Grill for deliberate pressure-testing of consequential candidates before authority
- Goals and Decisions for current-goal boundaries
- Authorship Stance when user-experience intent is being elicited

## Dependencies

Consumes Domain rules/events where user behavior depends on them. Requests perceptual decisions from Style and technical decisions from Tech; Build consumes the resulting App authority.

Under the default method selection, App may use Interview Me and Story Mapping. Design may delegate App concerns here. Method output remains non-authoritative until an App skill incorporates an accepted conclusion.

## Orchestration

When a concern is clearly App-owned but broad or not yet decomposed, route to App before prematurely choosing Story Map, Interaction, or Surfaces.

App then:

1. establishes the user-outcome slice required by the current Goal
2. identifies the affected stable App scope(s)
3. loads those scopes plus relevant topology dependencies, including Domain scopes they explicitly depend on
4. selects only useful active methods or narrow App skills
5. promotes accepted method conclusions through Story Map, Interaction, and/or Surfaces into the owning App scopes
6. reconciles those edits inside the App boundary
7. routes Domain/Style/Tech concerns to their owners
8. uses reverse dependents as Change Impact candidates when App meaning changed
9. invokes App Check locally and affected graph checks before dependent completion where materially required

Narrow, already-understood concerns may route directly to their owning App skill.

## Shared rule

Story Map, Interaction, and Surfaces may revise one another during specification. That revision is expected. The deadline for understanding is implementation, not the first draft.

## Invariants

- App describes the user experience structurally, not visually.
- Stable scope identity, not file placement, determines App authority.
- User activities are not developer activities.
- Domain rules are referenced, not redefined.
- Style decisions are requested, not made here.
- Technology choices are requested, not made here.
- Method working state is not App authority.
- Work remains bounded by the current Goal.
- App declares no stable local specification identifiers; user behavior traces through scoped Domain/Tech identifiers it references.
- Broad orchestration never creates a second App source of truth.
