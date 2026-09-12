# App Check

Scrutinizes authoritative App scope(s) for internal completeness and coherence.

## Authority target

Follow the [Project Authority Target Contract](../../contracts/project-authority-target-contract.md). Under `spec`, edit/check the affected stable Spec scope(s). Under `repository-native`, edit/check the corresponding section of the current transient Goal Spec and relevant named native constraints. Any scope-ID, Spec Topology, reverse-dependency, or scoped identifier requirement below is `spec`-only unless the repository already uses an equivalent native identifier deliberately.


## Define

Check whether Story Map, Interaction, and Surfaces form one coherent user-facing application model in the selected App scope(s).

Run after meaningful App changes, before implementation depends on changed App behavior, as part of broader sanity checks, or when existing App authority may have drifted.

## Inputs

Required:

- one or more affected `app.*` scope IDs and documents from Spec Topology

As available:

- current Goal
- topology dependencies required to interpret referenced Domain/Style/Tech authority

## Checks

### 1. Details are minimal

For every Story Map detail ask whether the step would still be complete without it. If yes, the detail is a finding.

### 2. Every step surfaces somewhere

A step with no interaction location is a finding.

### 3. Every surface serves behavior

Every surface must support an activity, step, interaction, or required persistent application structure.

### 4. Interaction and surfaces connect

For every relevant interaction establish:

`user action → App response → surface/state → next possible user action`

### 5. Dependencies are explicit

When an App scope relies on Domain/Style/Tech authority outside itself, that dependency must be represented by the Spec topology rather than only by physical proximity or an implicit reference.

### 6. Spec authority is conclusion-shaped

Under `spec`, apply `SPEC-WRITE-01`: stable App scopes should state the durable activity, interaction, and surface decisions, not retain the design conversation, alternatives considered, or method narrative once those no longer affect the application model. Prefer compact representation where it is equally clear.

## Outputs

Either `no change` or evidence-backed internal App findings routed to Story Map, Interaction, Surfaces, or topology ownership. Cross-authority findings belong to Sanity Specification Check.

## Owns

No durable Project state. App Check may read selected scopes and implementation evidence, but it does not repair them. Fixes remain owned by the skill/authority that owns the finding.

## Modes

### `check`

Run the complete App consistency check for selected scope(s). Narrower questions route to Story Map, Interaction, or Surfaces rather than becoming partial check modes.

## Completion

Complete when current-goal user behavior in the selected scope(s) is represented, unnecessary future behavior is absent, every step has an interaction and surface, every surface has a reason to exist, required dependencies are explicit, and unresolved findings block implementation rather than becoming guesses.

## Approval

Routine App scrutiny does not require approval. Meaningful unresolved product, interaction, or scope-placement decisions route back to the owning App authority.

## Invariants

- App Check can run independently on selected App scopes
- implementation guesses are findings
- scope/path are not conflated
- scrutiny happens before implementation relies on the specification
