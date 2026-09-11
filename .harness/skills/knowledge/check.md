# Knowledge Check

Checks reusable technology knowledge for drift and misplaced authority.

## Define

Check reusable technology knowledge for drift, contradiction, obsolete examples, and misplaced authority.

## Checks

- entry still names a technology/context it actually applies to
- entry does not make project choices
- contradictory entries are reconciled or context-bounded
- obsolete examples are updated or retired
- project-specific facts are not masquerading as reusable knowledge
- general principles that have clearly outgrown the technology entry route to Dream as candidate experience

## Inputs

Required: the relevant knowledge entries.

As needed: current vendor/tool behavior, newer evidence, and project examples that exposed the possible drift.

## Outputs

Either `no change` or evidence-backed knowledge findings with a route: update/retire the entry, narrow its context, move project facts to Setup/Tech, or route broader experience to Dream.

## Owns

No durable state while checking. Knowledge Check does not silently rewrite entries; Knowledge Capture/refinement owns the update.

## Modes

### `check`

Run the knowledge consistency/freshness check for the selected entry set.

## Approval

No project lifecycle approval. Changes in a shared knowledge repository follow that repository’s review policy.

## Invariants

- knowledge never becomes a technology choice
- stale knowledge is a finding, not silently trusted context
- contradictory advice must be context-bounded or reconciled
- project-specific facts do not remain in shared knowledge

## Completion

Complete when knowledge remains useful, scoped, and non-authoritative with respect to project choices.
