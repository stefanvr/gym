# General Guidelines

Defines the principles used when multiple reasonable approaches remain and something has to decide between them.

This is a universal Harness Guide under [Guides](definition.md). Project-specific truth remains with the Project owner for its concern.

## Does not own

This guide does not own:

- workflow mechanics
- Git mechanics
- implementation structure
- project-specific architecture
- environment behavior
- technology choices
- product/domain decisions
- goal formation and decision sequencing

Those are routed to their owning guides, skills, or specifications.

## Principle test

A principle belongs here only when it rules something out.

Before adding one, name a decision it would have changed.

A principle that never changes a decision is a slogan.

---

# Goal Work

Goal formation, goal edges, user-capability tests, decision goals, proof-before-dependency, and ahead-of-goal boundaries are owned by [Goals and Decisions](goals-and-decisions.md).

This guide relies on that specialized guide and does not restate its rules.

---

# Development

## Work in small coherent changes

Prefer small, integrated changes over large batches.

Nothing important should exist only in an uncommitted local state for longer than the work requires.

Git-history meaning belongs to the Git History guide and branch skills. Exact repository/ref/transaction facts and guarded lifecycle mechanics belong to the Deterministic Runtime when a runtime command exists; do not reconstruct those algorithms conversationally.

## Understand before modifying

Before changing something, establish:

- what owns it
- what the intended outcome is
- what evidence will show the change is correct

## Keep authority synchronized

When implementation changes an owned decision, update the owning artifact as part of the same coherent work.

When an authoritative document is structurally repaired, re-read the artifacts that cite or depend on it.

Documents have no compiler to reveal broken references.

## Tests are implementation

Testing is part of producing the behavior, not a separate clean-up phase.

Where tests belong and what they should prove is governed by the Software Design guide.

## Leave a verifiable state

A change is not complete merely because the intended edit was made.

Leave enough evidence that another session or machine can establish the result again.

---

# Verification and Honesty

## Distinguish verified from believed

Never present an assumption, expectation, or remembered fact as verification.

Say what was actually checked.

## Prefer artifacts to self-report

Verify by inspecting the thing produced, not only the tool or process claiming it succeeded.

## Prefer repeatable evidence

When a meaningful property can reasonably be checked automatically, prefer a repeatable check over a one-off manual observation.

Manual inspection remains useful for judgment and exploratory validation, but it does not replace durable evidence for repeatable claims.

## Use an independent reader for multi-step work

For consequential multi-step work, create an independent way of detecting error.

This may be:

- a test
- a check
- a second model/reviewer
- an independently derived expected value

The second reader should be capable of disagreeing with the first.

## Record surprises at their owning layer

When a tool, environment, technology, or workflow behaves unexpectedly, record the reusable lesson where that class of surprise is owned.

Do not turn every incident into a standing general principle.

When repeated experience suggests future work should change across owners or projects, route it to Dream for proposal and owner review rather than promoting it directly.

---

# Writing It Down

## Record durable decisions

Authoritative documents should primarily state the state or rule that now holds.

Draft reasoning and provenance belong to working material or history unless the argument itself is required to use the decision correctly.

## Portable reasons belong in durable guides

A durable justification should remain meaningful to someone on another machine and in another session.

Machine-specific facts belong to environment/setup documentation.

Project-specific facts belong to the appropriate specification.

## Elaborate where it changes understanding

Do not explain every obvious convention equally.

Spend explanation on:

- surprising rules
- important exceptions
- observed failure modes
- decisions whose boundary is easy to misuse

## Do not duplicate authority

When a pointer and its target both contain the same rule, keep the rule at the target and let the pointer route.

## Do not document easily derived tree state

Do not manually maintain facts that the repository already expresses clearly unless deriving them is materially expensive.

When a copy is necessary, name the authority.

---

# When Principles Collide

Use the jurisdiction-first authority model defined in [Workflow](../workflow/WORKFLOW.md#authority); do not maintain a second hierarchy here.

When two rules at the same level genuinely conflict, choose one and preserve enough history to show which trade-off was taken.

Repeated losses are evidence that a principle may need revision.
