# Build Repair

Makes existing implementation conform to already-owned behavior.

## Define

Use when code is wrong but the intended behavior is already known.

## Method

1. Reproduce the mismatch.
2. Identify the owning requirement.
3. Add or strengthen the check exposing the mismatch where useful.
4. Correct implementation.
5. Verify the correction.
6. Run Build Check.

## Correction versus requirement change

Classify the change using the Git History guide.

If implementation is wrong, repair it and leave history handling to the Git History/Branch Land flow.

If the requirement changed or was never decided, stop Repair and route through Goal `brain` and the owning capability before implementation continues.

## Inputs

Required:

- reproducible implementation mismatch
- authoritative expected behavior
- current repository state

As relevant: existing tests, active Project authority, and original task/commit context.

## Outputs

Corrected implementation and appropriate evidence/tests showing the mismatch is repaired.

## Owns

Implementation and test files needed to repair the mismatch. It does not own the requirement; if the requirement changed or was absent, Repair stops and routes out. It may record transient findings/notes in Build's shared `doc/scratchpad/`; closure of that directory is owned by Build Check `close`.

## Modes

### `repair`

Correct implementation that disagrees with already-owned behavior. Requirement discovery/change is not a Repair mode.

## Approval

No separate approval for a true implementation correction. Requirement changes route to Goal and the owning capability, where their normal validation policy applies.

## Completion

Complete when implementation matches its authority and the failure is covered by appropriate evidence.

## Invariants

- Repair does not invent desired behavior.
- Silence in Spec scopes, a Goal Spec, or named native authority is not permission for Repair to invent behavior.
- Requirement changes are not disguised as repairs.
