# Style

Defines and orchestrates how the product should look, sound, and feel.

Style owns the desired perceptual character of the product. It does not own what causes something to happen, domain timing, user-flow structure, technical production, or implementation.

## Purpose

Produce and maintain authoritative Style state describing perceptual references, visual character, audio character, perceptual rules/exceptions, concrete style values, and intentionally open style decisions.

Style is also the broad intake/orchestration boundary for a perceptual concern that cannot yet be safely reduced to one narrow Style skill.

## Owns

All active Spec scopes whose topology authority is `style`, such as `style.foundation` or `style.customer`.

Physical paths are resolved by Spec Topology. Style owns its own topology entries and dependency edges.

Style additionally owns developer-facing Style preview artifacts and their developer preview index entries at the project-specific paths established during the work. Style Preview uniquely owns those artifacts; the harness defines no universal preview path.

## Skills

- `reference`
- `visual`
- `audio`
- `preview`
- `check`

## Shared guides and mechanisms

- Authority Orchestrator Contract for broad Style intake and delegation
- Spec Topology for stable scope identity, scoped loading, and graph impact
- Method Pack Contract for activated discovery/coordination methods
- Grill for deliberate pressure-testing of consequential candidates before authority
- Authorship Stance for owner-led vs harness-proposed Style decisions
- Goals and Decisions for current-goal boundaries

## Dependencies

Consumes App/Domain triggers and surfaces without redefining them. Technical production routes to Tech; Build implements Style; Style Preview demonstrates Style decisions.

Under the default method selection, Style may use Interview Me when owner perceptual intent is incomplete. Design may delegate Style concerns here. Method output remains non-authoritative until a Style skill incorporates an accepted conclusion.

## Orchestration

When a concern is clearly Style-owned but broad or not yet decomposed, route to Style before prematurely choosing Reference, Visual, Audio, or Preview.

Style then:

1. establishes the perceptual slice required by the current Goal
2. identifies the affected stable Style scope(s)
3. loads those scopes plus relevant topology dependencies
4. uses owner elicitation or narrow Style skills only where useful
5. promotes accepted conclusions through Reference, Visual, Audio, and/or Preview ownership
6. reconciles perceptual decisions inside the Style boundary
7. routes behavior or production concerns to their owners
8. uses reverse dependents as Change Impact candidates when Style meaning changed
9. invokes Style Check and relevant Preview checks before dependent completion where materially affected

Narrow, already-understood concerns may route directly to their owning Style skill.

## Per-sense independence

References are established per sense. Visual and audio references may come from different sources and do not need to form one literal reference object.

## Open decisions

Style may explicitly record decisions that remain open when knowing that they are open matters to later work. When resolved, remove them.

## Invariants

- Style owns what is perceived, not what causes it.
- Stable scope identity, not file placement, determines Style authority.
- Style decisions become authoritative only after required owner involvement.
- Visual and audio may use different references.
- Method working state is not Style authority.
- Style declares no stable local specification identifiers; Style decisions trace through named values, owning scope IDs, and previews.
- Broad orchestration never creates a second Style source of truth.
