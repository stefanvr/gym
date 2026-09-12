# Style

Defines and orchestrates how the product should look, sound, and feel.

## Purpose

Produce coherent perceptual direction and concrete style decisions required by the current Goal without taking ownership of user-flow, domain, or technical behavior.

## Owns

Accepted Style conclusions in the active Project authority target:

- under `spec`, affected stable `style.*` Spec scopes
- under `repository-native`, the Style portion of the current transient Goal Spec

Style Preview may additionally own developer-facing preview artifacts when created during the work.

## Skills

- `reference`
- `visual`
- `audio`
- `preview`
- `check`

## Shared guides and mechanisms

- Authority Orchestrator Contract
- Project Authority Target Contract
- Spec Project Model authority recording discipline (`SPEC-WRITE-01`) when `spec` is active
- Method Pack Contract
- Grill
- Authorship Stance
- Goals and Decisions

## Dependencies

Consumes App/Domain triggers and surfaces without redefining them. Technical production routes to Tech; Build implements Style. May use Interview Me for owner perceptual intent.

## Orchestration

When a concern is clearly Style-owned but broad or not yet decomposed, route to Style before prematurely choosing Reference, Visual, Audio, or Preview.

Style then:

1. establishes the perceptual slice required by the Goal
2. resolves the active authority target
3. inspects relevant native style/design-system constraints and current authority
4. uses owner elicitation or narrow Style skills only where useful
5. promotes accepted conclusions through Reference, Visual, Audio, and/or Preview ownership into the active target
6. reconciles perceptual decisions inside the Style boundary
7. routes behavior or production concerns to their owners
8. applies Change Impact when Style meaning changes
9. invokes Style Check and useful Preview checks before dependent completion

Under `repository-native`, follow existing repository visual conventions where they are normative or deliberate, but do not treat incidental current styling as desired authority automatically.

## Invariants

- Style owns what is perceived, not what causes it
- Style decisions become authoritative only after required owner involvement
- visual and audio may use different references
- method working state is not Style authority
- accepted Style meaning lives in one active Project authority target
- broad orchestration never creates a second Style source of truth
