# Domain

Defines and orchestrates domain meaning: language, meaningful events, rules, and domain data.

## Purpose

Produce coherent desired domain state for the current Goal and keep domain decisions out of incidental implementation choices.

## Owns

Accepted Domain conclusions in the active Project authority target defined by the [Project Authority Target Contract](../contracts/project-authority-target-contract.md):

- under `spec`, the affected stable `domain.*` Spec scopes
- under `repository-native`, the Domain portion of the current transient Goal Spec

The target states desired domain state. Working provenance, workshop notation, confidence markers, and method artifacts remain non-authoritative.

## Skills

- `language`
- `events`
- `rules`
- `data`
- `check`

## Shared guides and mechanisms

- Authority Orchestrator Contract
- Project Authority Target Contract
- Spec Project Model authority recording discipline (`SPEC-WRITE-01`) when `spec` is active
- active Project-model structure where applicable
- Method Pack Contract
- Grill
- Authorship Stance
- Goals and Decisions

## Dependencies

Consumes the current Goal and relevant repository/native authority. May use Event Storming and Interview Me. Design may delegate Domain concerns here. Domain conclusions can constrain App, Tech, and Build.

## Orchestration

When a concern is clearly Domain-owned but broad or not yet decomposed, route to Domain before prematurely choosing Language, Events, Rules, or Data.

Domain then:

1. establishes the domain slice required by the Goal
2. resolves the active authority target
3. loads only relevant current authority/evidence and Project-model dependencies
4. selects useful active methods or narrow Domain skills
5. promotes accepted conclusions through Language, Events, Rules, and/or Data into the active target
6. reconciles the Domain slice as one coherent desired state
7. routes App/Style/Tech concerns to their owners
8. applies Change Impact where existing meaning changes
9. invokes Domain Check before dependent implementation where materially required

Under `spec`, stable-scope topology and scoped identifiers apply. Under `repository-native`, do not manufacture Spec scopes or identifiers; integrate the needed domain conclusions into the Goal Spec.

## Invariants

- Domain describes the business/world meaning, not UI flow or technology
- method working state is not Domain authority
- accepted Domain meaning lives in exactly one active Project authority target
- consequential domain decisions are resolved before implementation depends on them
- repository evidence describes current reality but does not automatically decide desired domain state
- broad orchestration never creates a second Domain source of truth
