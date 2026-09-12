# Build Implement

Implements product functionality already owned by the current Goal and active Project authority.

## Define

Write or change product code so the system exhibits behavior that has already been decided.

## Preconditions

Identify:

- the current goal
- the active Project authority that owns the behavior (`spec` scopes or the repository-native Goal Spec plus named native constraints)
- relevant Tech constraints
- relevant Software Design rules

If behavior has no owner, route the gap rather than defining it in code.

## Method

1. Identify the behavior and authority.
2. Establish the smallest coherent implementation step.
3. Shape code according to Software Design and Tech.
4. Put behavioral tests at the lowest layer that truthfully proves the behavior.
5. Add surface/integration evidence only for what those layers uniquely prove.
6. Run Build Check.
7. Commit at task size.

## Inputs

Required:

- current goal/task
- active Project authority owning the behavior
- current repository state

As relevant:

- Tech architecture decisions
- Software Design guide
- existing tests and neighboring implementation

## Outputs

Task-sized implementation code and the tests/evidence needed to prove the owned behavior.

## Owns

Implementation and test files required by the current task. It does not own Domain/App/Style/Tech authority, repository-native Goal Specs, setup documents, or Goal state. It may record transient findings/notes in Build's shared `doc/scratchpad/`; closure of that directory is owned by Build Check `close`.

## Modes

No separate modes. Build Implement performs one operation: implement already-owned product behavior for the current task.

## Approval

No separate approval for routine implementation. Meaningful product validation follows Goal checkpoints and the final Branch Land approval boundary; missing decisions route out before implementation continues.

## Completion

Complete when:

- intended behavior exists
- relevant tests prove it
- implementation conforms to active Project authority
- design and Tech constraints hold
- no product decision was made accidentally in code
- Build Check passes

## Invariants

- no specification-by-implementation / no hidden Goal-Spec authoring in code
- no ahead-of-goal behavior
- implementation follows authority rather than filling its silence
