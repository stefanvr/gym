# Domain Rules

Defines the explicit rules of the world being modelled.

## Define

Record domain behavior that must remain true independent of screen, interaction, or implementation.

## Inputs

May consume:

- current goal
- affected Domain scope IDs and documents from Spec Topology
- Domain language
- Domain events
- Domain data
- method/brainstorm material
- existing Domain rules

## Outputs

Authoritative business rules in the owning Domain scope.

Rules use stable local identifiers:

`R-n`

When referenced outside their owning scope, use the canonical scoped form:

`<domain-scope-id>:R-n`

Example: `domain.billing:R-017`.

## Owns

May modify only the rule section(s) of the affected Domain Spec scope(s) selected by Spec Topology.

Domain Rules does not move a rule into another stable scope merely because a different file location seems convenient. Re-scoping authority is a deliberate topology/authority migration.

## Method

For each rule establish:

1. the condition or trigger
2. the required inputs
3. the domain behavior
4. the resulting state or constraint
5. the owning Domain scope

Each rule should express one coherent domain truth.

Assign each new rule an unused `R-n` **inside that scope**. A local identifier is never reused for unrelated meaning in the same scope. Different Domain scopes may have the same local number because the canonical citation includes the scope ID.

## Data scrutiny

For every rule, name the data it needs.

Every required input must be a defined domain term, a defined piece of domain data, or an explicit primitive. A rule requiring an unnamed thing is incomplete.

## Modes

No separate modes. Invoking the skill creates or revises the explicit rules required by the current goal in the selected scope(s).

## Approval

No separate lifecycle approval is expected. Any genuinely unresolved domain rule or authority-scope placement is validated with the owner before recording; otherwise completion flows toward Goal completion and landing approval.

## Completion

Complete when:

- the behavior required by the current goal is explicitly stated
- every rule lives in the correct stable Domain scope
- every rule's inputs exist
- terminology matches the Domain language
- relevant data is defined
- rules can be meaningfully exercised by later tests
- external references use canonical scoped citations where ambiguity matters

## Invariants

- rules describe the world, not the interface
- required inputs cannot remain implicit
- rule identifiers remain stable once depended upon
- no reused `R-n` identifier inside one scope
- canonical cross-scope identity is `<scope-id>:R-n`
- file movement does not change rule identity when the scope ID is unchanged
- do not invent rules merely to make the specification exhaustive
