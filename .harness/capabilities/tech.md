# Tech

Owns and orchestrates technology and project-specific architecture decisions required by the current Goal.

## Purpose

Resolve technical choices and architecture constraints before dependent implementation needs them, and keep recorded technical authority truthful against repository/external evidence.

## Owns

Accepted Tech conclusions in the active Project authority target:

- under `spec`, affected stable `tech.*` Spec scopes
- under `repository-native`, the Tech portion of the current transient Goal Spec

Existing native ADRs/architecture documents remain native authority when the repository already treats them as normative. A Goal that changes them must update them as part of implementation.

## Skills

- `decide`
- `architecture-rule`
- `repair`
- `check`

## Shared guides and mechanisms

- Authority Orchestrator Contract
- Project Authority Target Contract
- Spec Project Model authority recording discipline (`SPEC-WRITE-01`) when `spec` is active
- Method Pack Contract
- Grill
- Goals and Decisions
- General evidence discipline

## Dependencies

Tech may request Build Proof and Knowledge Lookup. Setup receives verified operational consequences; Domain, App, Style, and Build consume Tech decisions where relevant.

## Orchestration

When a concern is clearly Tech-owned but broad or contains interacting choices/rules, route to Tech before prematurely choosing Decide or Architecture Rule.

Tech then:

1. establishes the technical question required by the Goal
2. resolves the active authority target
3. inspects relevant current architecture, native authority, configuration, and external evidence
4. separates facts, owner constraints, technology choices, and architecture rules
5. selects useful evidence gathering, active methods, or narrow Tech skills
6. promotes accepted decisions through Tech Decide and constraints through Tech Architecture Rule into the active target
7. uses Tech Repair only for evidenced non-decision truth/document repair
8. routes implementation proof to Build and reusable technology learnings to Knowledge
9. applies Change Impact when technical meaning changes
10. invokes Tech Check before dependent completion where materially required

Under `spec`, stable scope IDs and `A-n` rules apply. Under `repository-native`, use clear Goal-Spec decisions/native references rather than inventing Spec identifiers.

## Invariants

- Tech records decisions, not possibilities
- no required technology decision remains hidden inside implementation
- external claims are verified rather than remembered when material
- architecture rules constrain something real
- method working state is not Tech authority
- implementation does not silently change accepted Tech decisions
- broad orchestration never creates a second Tech source of truth
