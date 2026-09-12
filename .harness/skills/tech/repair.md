# Tech Repair

Repairs non-decision truth or document integrity in authoritative Tech scope(s) without changing a technology choice, architecture-rule meaning, or stable scope identity.

## Authority target

Follow the [Project Authority Target Contract](../../contracts/project-authority-target-contract.md). Under `spec`, edit/check the affected stable Spec scope(s). Under `repository-native`, edit/check the corresponding section of the current transient Goal Spec and relevant named native constraints. Any scope-ID, Spec Topology, reverse-dependency, or scoped identifier requirement below is `spec`-only unless the repository already uses an equivalent native identifier deliberately.


## Define

Correct stale factual claims, ownership/header text, Markdown structure, or broken non-semantic references in affected Tech Spec scope(s) when Tech Check establishes that the intended decision itself has not changed.

Use Tech Decide when the technology choice must change. Use Tech Architecture Rule when an architecture rule's meaning must change. Route scope-identity/dependency changes through the Tech orchestrator as topology work.

## Inputs

Required:

- an evidenced Tech Check finding
- affected Tech scope ID/document from Spec Topology
- the evidence establishing the correct factual/document state

As relevant:

- current repository tree
- current external artifact/documentation
- existing code/test citations

## Outputs

Truthfully repaired Tech scope content whose technical decisions, architecture-rule meanings, local identifiers, and stable scope identity are unchanged.

## Owns

Only non-decision factual/document-integrity portions of the selected Tech scope(s):

- stale descriptions of the current repository/project state
- document ownership/header text
- Markdown/rendering defects
- broken references whose correction does not change a decision or canonical identity
- equivalent truth-maintenance edits

It does not own technology choices, architecture-rule meaning/identity, or topology re-scoping.

## Modes

### `repair`

Apply the smallest evidenced non-decision correction, then run Tech Check.

If the required correction would alter a technology choice, architecture-rule meaning, or stable scope identity, stop and route to the owning Tech decision/topology path.

## Completion

Complete when the evidenced non-decision finding is corrected and Tech Check passes for the repaired scope/document structure.

## Approval

No approval for a factual/document-integrity repair that leaves technical decisions and stable authority identity unchanged.

If the repair exposes a decision/topology change, that change follows the approval policy of the owning Tech path.

## Invariants

- repair never changes a technology choice
- repair never silently changes an `A-n` rule's meaning
- repair never silently re-scopes authority
- every repair is grounded in evidence
- document cleanup is not used to smuggle in a new decision
- Tech Check runs after repair
