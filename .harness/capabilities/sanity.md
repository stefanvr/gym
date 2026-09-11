# Sanity

Runs independent consistency checks across the harness, specifications, implementation, tests, and repository state.

Sanity discovers and routes findings. It does not own fixes.

## Purpose

Detect cross-cutting drift that individual goal work may not expose, while keeping expensive or context-specific checks conditional rather than ritualistic.

## Owns

No fixes or authoritative product state. Through Sanity Run, the capability owns orchestration of checks and grouping/routing of findings.

## Skills

- `run` — orchestrate the selected Sanity checks and trigger-driven checks
- `harness-check` — harness internal consistency
- `spec-check` — specification coherence
- `trace-check` — specification/code/test traceability
- `repository-check` — repository structural/lifecycle drift

Setup Dev/App `check` and Knowledge Check remain owned by their own capabilities and may be invoked by Sanity Run when triggered.

## Shared guides and mechanisms

- Workflow's jurisdiction-first / one-authority model
- Guide definition and Change Impact for universal-judgment and propagation checks
- shared Check mechanism where applicable
- capability-specific checks retain their own scrutiny and ownership

## Finding test

A check result becomes a finding only when it names an execution that would go differently.

Evidence that something is inconsistent is not sufficient. The [General](../guides/general.md) principle test applies to findings as well as to principles: name the execution it would change.

This bar is owned here and applies to every Sanity check. Individual checks point to it rather than restating it.

For Harness Assurance reporting, finding existence and assurance impact are deliberately separate. [Harness Assurance](../harness-assurance.md) classifies evidenced observations as blocking defects, accepted operating restrictions, improvement/evidence debt, or outside the supported model for a named profile. That classification never makes an evidenced Sanity finding disappear and never grades the Project managed by the Harness.

## Dependencies

Sanity Run invokes existing checks; it never reimplements them. Findings route to the capability/skill that owns the violated invariant.

## Invariants

- Sanity checks; it does not become a universal repair capability.
- Findings cite evidence rather than suspicion.
- A finding names an execution that would go differently; an evidenced observation that changes no behavior is not a finding.
- Absence of evidence is not silently treated as success.
- Every finding routes to one owning capability.
- Capability-owned checks stay authoritative for their own scrutiny.
- Trigger-driven checks are omitted deliberately, not forgotten.
