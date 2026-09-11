# Tech Decide

Resolves one bounded technology choice.

## Define

Choose a technology needed by the current or next goal.

A technology choice is not an implementation detail when dependent work cannot proceed without it. In that case, the choice becomes a decision goal in front of the dependent goal.

## Inputs

Required:

- the decision to make
- constraints that rule candidates in or out
- the affected Tech scope ID/document from Spec Topology, or a deliberate decision to establish a new Tech scope

Optional:

- current goal
- candidate technologies
- supplied references
- proof results

## Outputs

One authoritative decision containing:

- chosen technology
- meaningful alternatives considered
- what the chosen option beat
- the argument where the closest alternative was close
- constraints that materially drove the choice

## Owns

Only technology-choice decision portions of the affected Tech Spec scope: the chosen technology, decision constraints, meaningful alternatives, and rationale for that choice.

Tech Decide does **not** own:

- local `A-n` architecture-rule meaning or identifiers → Tech Architecture Rule
- non-decision factual/document-integrity repair → Tech Repair
- another authority's topology entries

## Modes
### `decide`

1. Establish the actual decision and owning Tech scope.
2. Establish decision constraints.
3. Identify plausible candidates.
4. Eliminate candidates ruled out by known constraints.
5. Compare the remaining meaningful options.
6. Where uncertainty is material, require the smallest genuine proof.
7. Present options and recommendation.
8. Let the owner make or approve the final technology choice.
9. Record the resulting decision in the owning Tech scope.
10. Run Tech Check.

## Proof rule

A decision that depends on uncertain real behavior must be proven by the smallest thing that genuinely exercises that uncertainty.

Do not substitute documentation familiarity, memory, popularity, dependency order, or abstract preference for evidence needed by the actual decision.

## Completion

Complete when the bounded technology decision is made, deciding constraints are known, meaningful alternatives were considered, material uncertainty was proven where needed, the decision is recorded in the correct stable Tech scope, and Tech Check passes.

## Approval

Technology choice is a meaningful decision boundary. The harness may recommend. The owner chooses or explicitly approves the choice.

## Invariants

- no technology is chosen incidentally during dependent implementation
- the decision is bounded
- authority placement follows stable Tech scope identity, not file convenience
- proof targets real uncertainty
- alternatives are meaningful, not decorative
- recorded rationale reflects the actual decision
- deciding does not implement the dependent feature
