# Tech Decide

Resolves one bounded technology choice.

## Authority target

Follow the [Project Authority Target Contract](../../contracts/project-authority-target-contract.md). Under `spec`, edit/check the affected stable Spec scope(s). Under `repository-native`, edit/check the corresponding section of the current transient Goal Spec and relevant named native constraints. Any scope-ID, Spec Topology, reverse-dependency, or scoped identifier requirement below is `spec`-only unless the repository already uses an equivalent native identifier deliberately.


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

One authoritative decision stating the durable result:

- chosen technology
- constraints or boundaries that remain operative
- only the minimal rationale or rejected alternative needed to interpret or apply the decision, or explicitly requested by the owner

Candidate comparison, close-call analysis, proof narrative, and rejected options remain working/evidence material by default rather than stable Tech authority. Under `spec`, record the result according to `SPEC-WRITE-01`.

## Owns

Only technology-choice decision portions of the active Tech authority target: the chosen technology, durable decision constraints, and any rationale the authority genuinely needs or the owner explicitly asked to retain.

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
9. Compress the accepted result into the active Tech authority target; do not copy the comparison transcript into stable Spec authority.
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
- detailed decision reasoning may be transient; recorded authority preserves only the durable result and necessary context
- deciding does not implement the dependent feature
