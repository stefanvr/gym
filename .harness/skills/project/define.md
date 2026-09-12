# Project Define

Turns a clear Goal into implementation-ready Project authority under the selected Project model.

## Define

Resolve the decisions required by the current Goal, using targeted repository understanding plus only the Domain/App/Style/Tech reasoning, active methods, Grill, and evidence work that materially improve the definition.

## Inputs

Required:

- current Goal
- active Project model
- relevant current Project authority/evidence

As needed:

- Project Understand findings
- Domain/App/Style/Tech reasoning
- Interview Me
- Event Storming
- Story Mapping
- Design
- Grill
- proofs or external verification

## Outputs

Under `spec`: accepted conclusions incorporated by their owning capabilities into affected stable Spec scopes.

Under `repository-native`: one current-branch Goal Spec at `doc/goals/<branch>.spec.md`, containing only relevant sections and explicit acceptance/proof expectations.

## Owns

Coordination of definition completeness. It does not replace the ownership of Domain/App/Style/Tech conclusions and does not own Build implementation.

## Modes

### `define`

1. restate the bounded outcome and edge of the Goal
2. inspect relevant authority/evidence; invoke Project Understand when needed
3. identify unresolved consequential Domain/App/Style/Tech questions
4. select only useful reasoning skills and active methods
5. pressure-test consequential candidates where useful
6. incorporate accepted conclusions through their owners into the active Project authority target
7. state acceptance/proof conditions
8. verify that implementation no longer needs to invent consequential intended behavior

## Completion

Complete when implementation can begin without silently making a consequential product, domain, style, or technology decision.

For repository-native mode, the Goal Spec must exist and be non-empty before dependent implementation is treated as definition-complete.

## Approval

Definition coordination itself needs no separate approval. Individual decisions retain the approval/owner-validation rules of their owning capabilities.

## Invariants

- methods are optional techniques, not a fixed pipeline
- small Goals produce small definitions
- unresolved consequential decisions block dependent implementation
- one active Project authority target receives accepted conclusions
- Build is not used as a substitute for definition
