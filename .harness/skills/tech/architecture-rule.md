# Tech Architecture Rule

Records a project-specific architecture rule that constrains implementation.

## Define

Create an architecture rule only when the project needs an explicit technical constraint or deliberate departure from the general design guide.

An architecture rule should rule something out. If it constrains nothing meaningful, it is not a rule.

## Inputs

Typical inputs:

- current Goal
- affected Tech scope ID/document from Spec Topology
- a recurring implementation problem
- a discovered architectural tension
- a deliberate project-specific constraint
- a departure from the general design guide

## Outputs

An authoritative architecture rule in one owning Tech scope.

Rules use stable local identifiers:

`A-n`

Canonical external citations use:

`<tech-scope-id>:A-n`

Example: `tech.architecture:A-004`.

## Modes
### `create`

1. Establish the owning Tech scope.
2. State the candidate rule.
3. Identify what it rules out.
4. Identify why the project needs the rule.
5. Check whether the general design guide already covers it.
6. Reject the rule if it adds no project-specific constraint.
7. Assign a new unused `A-n` inside the owning scope.
8. Record the rule.
9. Run Tech Check for that scope.

Refusing an `A-n` is a valid result. When refused, explain why outside Tech authority.

## Owns

May modify only the project-specific architecture-rule portion of the affected Tech Spec scope selected by Spec Topology, including assignment of local `A-n` identifiers.

It does not re-scope an architecture rule merely to move files. Changing the stable scope identity is an explicit topology/authority migration.

## Approval

A new architecture rule that materially constrains future implementation must be put to the owner before it becomes authoritative. Refusing a candidate rule requires no approval.

## Completion

Complete when:

- the rule expresses a real project-specific constraint
- it rules out at least one meaningful alternative
- it does not merely repeat the general design guide
- its local identifier is unique inside the owning Tech scope
- external citations use the canonical scoped form where needed
- relevant implementation can cite or exercise it
- Tech Check passes

## Invariants

- no decorative architecture rules
- no reused local identifiers inside one Tech scope
- canonical cross-scope identity is `<scope-id>:A-n`
- file movement does not change architecture-rule identity when the scope ID is unchanged
- no rule exists only because it sounds principled
- project-specific rules do not replace the general design guide
- a rule that no longer constrains anything should be questioned
