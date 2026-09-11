# Change Impact

Reusable mechanism for propagating changes to authoritative meaning without creating a dependency-state database.

It owns no artifact and makes no project decision. The authority owner changes meaning; Change Impact identifies what must be reconsidered because of that change.

## Rule

**[PROP-01]** When authoritative meaning changes, conclusions that materially depended on the previous meaning are no longer assumed valid.

**[PROP-02]** Before affected dependent work is considered complete or approved, identify the affected owners and re-establish the relevant checks, decisions, or evidence at the new boundary. Affected does not mean automatically wrong; it means no longer inherited without reconsideration.

## Method

When an authority owner changes meaning:

1. Name what changed and its owning concern.
2. Identify known specifications, decisions, implementation, tests, setup, lifecycle conclusions, or Harness mirrors that materially relied on the previous meaning. When the active Project model exposes reverse scope dependencies, include those dependents as impact candidates rather than assuming they all require edits.
3. Route each affected item to its existing owner; do not make the mechanism a second owner.
4. Re-run only the checks or decisions whose conclusions may have changed.
5. Record `not affected` only when there is a concrete reason, not because no edit is immediately obvious.

For the Spec Project model, `spec affected --scope ...` may mechanically enumerate dependency and reverse-dependent closures; semantic impact still decides which candidates truly require reconsideration.

Prefer local impact analysis over persistent global `dirty` flags. The Harness should not become a project-management database merely to remember that reconsideration is needed.

## Boundaries

- A correction that restores the already-authoritative meaning does not create semantic change merely because files changed.
- A requirement or decision change does create semantic impact even when the textual diff is small.
- Evidence that was valid for the old meaning may still be reusable, but its conclusion must be re-established where the changed authority could matter.
- Change Impact routes reconsideration; owning checks decide whether actual repair is needed.
