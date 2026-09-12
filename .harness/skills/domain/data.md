# Domain Data

Defines what domain concepts exist as data and which data is authored/reference material rather than runtime state.

## Authority target

Follow the [Project Authority Target Contract](../../contracts/project-authority-target-contract.md). Under `spec`, edit/check the affected stable Spec scope(s). Under `repository-native`, edit/check the corresponding section of the current transient Goal Spec and relevant named native constraints. Any scope-ID, Spec Topology, reverse-dependency, or scoped identifier requirement below is `spec`-only unless the repository already uses an equivalent native identifier deliberately.


## Define

Describe the minimum data structure required by current Domain rules and events.

## Inputs

May consume:

- Domain language
- Domain events
- Domain rules
- current goal
- known authored/reference material

## Outputs

Authoritative domain data definitions.

May distinguish:

- identity
- attributes
- relationships
- state
- authored/reference data
- runtime/generated data

## Owns

May modify the data sections of:

the active Domain authority target

## Method

Start from required behavior.

For each rule or event ask:

- what data must exist for this to make sense?
- what has identity?
- what is merely a value?
- what relationships must be preserved?
- what is authored ahead of time?
- what is created or changed during use?

Do not model data merely because it might be useful later.

## Reference data

Treat reference data as domain data that is authored or supplied rather than produced through normal runtime behavior.

Make the distinction only where it matters to the current goal.

## Modes

No separate modes. Invoking the skill creates or revises only the data/reference-data definitions required by current Domain behavior.

## Approval

No separate lifecycle approval is expected. Validate with the owner only when data shape encodes an unresolved domain decision rather than a derived representation of already-owned rules.

## Completion

Complete when every rule/event in the current goal has the data it requires and no unexplained data structure has been introduced.

## Invariants

- data exists to support domain meaning and behavior
- no speculative future schema
- identity is explicit where behavior depends on identity
- authored/reference data is distinguished only where operationally meaningful
