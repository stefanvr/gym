# App

Defines and orchestrates the user-facing structural experience: activities, interaction flow, surfaces, and behavior visible to users.

## Purpose

Produce coherent desired application behavior for the current Goal without deciding domain truth, visual style, or technical implementation incidentally.

## Owns

Accepted App conclusions in the active Project authority target:

- under `spec`, affected stable `app.*` Spec scopes
- under `repository-native`, the App portion of the current transient Goal Spec

## Skills

- `story-map`
- `interaction`
- `surfaces`
- `check`

## Shared guides and mechanisms

- Authority Orchestrator Contract
- Project Authority Target Contract
- Spec Project Model authority recording discipline (`SPEC-WRITE-01`) when `spec` is active
- Method Pack Contract
- Story Mapping when active/useful
- Design when cross-authority coordination is useful
- Goals and Decisions

## Dependencies

Consumes Domain behavior and current Goal context. May use Story Mapping and Interview Me. Routes perceptual decisions to Style and implementation constraints to Tech.

## Orchestration

When a concern is clearly App-owned but broad or not yet decomposed, route to App before prematurely choosing Story Map, Interaction, or Surfaces.

App then:

1. establishes the user-outcome slice required by the Goal
2. resolves the active authority target
3. loads relevant existing authority/evidence and dependencies
4. selects only useful active methods or narrow App skills
5. promotes accepted conclusions through Story Map, Interaction, and/or Surfaces into the active target
6. reconciles the user experience structurally
7. routes Domain/Style/Tech concerns to their owners
8. applies Change Impact when App meaning changes
9. invokes App Check before dependent implementation where materially required

Under `spec`, stable scope topology applies. Under `repository-native`, the Goal Spec contains only the interaction/surface detail needed for this Goal.

## Invariants

- App describes user experience structurally, not visually
- user activities are not developer activities
- Domain rules are referenced, not redefined
- Style and technology decisions are routed, not made here
- method working state is not App authority
- accepted App meaning lives in one active Project authority target
- broad orchestration never creates a second App source of truth
