# Tech

Owns and orchestrates authoritative technology and project-specific architecture decisions.

## Purpose

Record and maintain the technical decisions that constrain implementation, and provide the broad intake boundary for technical concerns that are not yet safely reducible to one Tech skill.

Tech answers which technology was chosen, what it beat and why, which project-specific architecture rules constrain implementation, and whether those recorded claims are still true.

Tech does not own general software design principles, implementation, environment setup, or lessons learned from technology failures.

## Owns

All active Spec scopes whose topology authority is `tech`, such as `tech.architecture` or `tech.persistence`.

Physical paths are resolved by Spec Topology. Tech owns its own topology entries and dependency edges. Tech scopes contain authoritative choices and the project-specific constraints that follow from them.

Tech authority may be cited from code and tests, so stable scope identity and truthful content matter even when files move.

## Skills

### `decide`
Resolve an open technology choice.

### `architecture-rule`
Add or refine a project-specific architecture rule.

### `repair`
Repair evidenced non-decision truth/document integrity without changing a technology choice or architecture-rule meaning.

### `check`
Verify that authoritative Tech scopes still match the repository and relevant external reality.

## Shared guides and mechanisms

- Authority Orchestrator Contract for broad Tech intake and delegation
- Spec Topology for stable scope identity, scoped loading, and graph impact
- Method Pack Contract for activated elicitation/coordination methods
- Grill for deliberate pressure-testing of consequential candidates before authority
- Goals and Decisions for decision-goal sequencing
- General for evidence/verification discipline

## Dependencies

Tech may request Build Proof and Knowledge Lookup. Setup receives verified operational consequences; Domain, App, Style, and Build consume Tech decisions where relevant.

Under the default method selection, Tech may use Interview Me where owner constraints/preferences are genuinely needed. Design may delegate Tech concerns here. Method output remains non-authoritative until Tech Decide or Architecture Rule incorporates an accepted conclusion.

## Orchestration

When a concern is clearly Tech-owned but broad or contains several interacting choices/rules, route to Tech before prematurely choosing Decide or Architecture Rule.

Tech then:

1. establishes the technical question required by the current Goal
2. identifies the affected stable Tech scope(s)
3. loads those scopes plus relevant topology dependencies
4. separates external facts, owner constraints, technology choices, and project-specific architecture rules
5. selects useful evidence gathering, active methods, or narrow Tech skills
6. promotes accepted decisions through Tech Decide and architecture constraints through Tech Architecture Rule
7. uses Tech Repair only for evidenced non-decision truth/document repair
8. routes implementation proof to Build and reusable technology learnings to Knowledge
9. uses reverse dependents as Change Impact candidates when authoritative Tech meaning changed
10. invokes Tech Check locally and affected graph checks before dependent completion where materially required

Narrow, already-understood concerns may route directly to their owning Tech skill.

## Invariants

- Tech records decisions, not possibilities.
- Stable scope identity, not file placement, determines Tech authority.
- No required technology decision remains hidden inside an implementation goal.
- External claims are verified rather than remembered.
- Architecture rules must constrain something real.
- Method working state is not Tech authority.
- Within each Tech scope, Tech Architecture Rule assigns stable local `A-n` identifiers; the canonical cross-scope citation is `<scope-id>:A-n`.
- Stable identifiers remain unique and meaningful inside their scope.
- Implementation does not silently change the meaning of Tech decisions.
- Broad orchestration never creates a second Tech source of truth.
