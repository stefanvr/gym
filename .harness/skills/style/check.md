# Style Check

Scrutinizes authoritative Style scope(s) for truth and product implementation-source consistency.

## Define

Check that the selected Style scope(s) accurately describe the desired visual/audio state and that Style-owned decisions are represented consistently in implementation.

Style Check does **not** own preview demonstrability. Style Preview `check` owns whether decisions can be inspected and whether previews consume the intended sources of truth.

Run after meaningful Style changes, before implementation depends on new Style decisions, as part of broader sanity checking, or when Style implementation may have drifted.

## Inputs

Required:

- one or more affected `style.*` scope IDs and documents from Spec Topology

As applicable:

- topology dependencies
- visual implementation values
- audio implementation values
- current Goal

## Checks

### 1. Every concrete Style value has one implementation home

For every concrete Style value, identify its product implementation source of truth. No implementation home or multiple independent product copies are findings.

Preview-local duplication/divergence is owned by Style Preview `check`, not repeated here.

### 2. Every Style decision was actually made

A decision that appeared in authority without the required owner interaction is a finding.

### 3. Open decisions are still open

If a later pass settled an open item, remove the stale entry.

### 4. Sensory coverage is intentional

For the current goal, ask whether visual, audio, and feel/feedback behavior matter. A sense may legitimately require no work. Omission through never asking is a finding.

### 5. Scope dependencies are explicit

Style references to App/Domain triggers or other Style foundations must resolve through selected scope authority and explicit topology dependencies where cross-scope interpretation is required.

## Outputs

Either `no change` or evidence-backed Style findings concerning product implementation value sources, unauthorized decisions, open decisions, sensory omissions, or topology boundaries. Cross-authority ownership findings belong to Sanity Specification Check.

## Owns

No durable Style state. Style Check reads selected scopes and implementation values but routes fixes to Reference, Visual, Audio, App, Domain, Tech, or topology ownership. It does not own Preview findings or Preview artifacts.

## Modes

### `check`

Run the Style specification/implementation consistency check for selected scopes. It invokes no other skill.

## Completion

Complete when concrete Style values have single product implementation homes, no unauthorized decisions are present, open decisions are accurate, sensory omissions are intentional, and required scope dependencies are explicit.

## Approval

Routine Style checks do not require approval. A check that reveals a new Style or scope-placement decision routes back to the appropriate Style owner.

## Invariants

- Style Check can run independently on selected Style scopes and invokes no sibling skill
- product implementation duplication is a finding here
- preview coverage and preview-source divergence belong only to Style Preview `check`
- specification decisions must have actually been decided
- stable scope identity is not inferred from file path
- Preview ownership is not absorbed; cross-authority ownership is checked by Sanity Specification Check
