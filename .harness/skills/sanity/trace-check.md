# Sanity Trace Check

Checks that authoritative scoped specification identifiers, implementation, and tests remain traceable in both directions.

## Define

Verify that specs, code, and tests agree about behavior and architecture deliberately made authoritative.

This is not line-level traceability or coverage percentage.

## Checks

### Spec → implementation

Every canonical identifier expected to have implementation still has code that gives it meaning.

### Spec → tests

Every behavior identifier expected to be testable has a meaningful asserting test.

### Tests → spec

Tests asserting product rules have an owning specification scope. A product-behavior test with no owner may reveal specification-by-test.

### Code → spec

Explicit spec citations in code still resolve to the same stable scope ID and local identifier, even if that scope's physical path moved.

### Identifier conventions

Each specification capability owns whether it carries stable local identifiers and what they look like. Read the convention from the owning capability rather than assuming one.

For scoped identifiers, canonical external references use:

`<scope-id>:<local-id>`

Examples: `domain.billing:R-017`, `tech.architecture:A-004`.

A capability that explicitly declares no identifiers is not a finding; expect no identifier trace where none is declared.


### Orphan behavior

Important product behavior in code/tests but absent from authoritative specification scope is a finding.

### Orphan specification

Authoritative behavior with no implementation/test where one should exist is a finding.

## Inputs

Required:

- the Sanity Finding test
- active Spec topology and authoritative scope documents containing stable identifiers/citations
- implementation tree
- test tree

As relevant: conventions defining which identifiers are expected to be implemented/tested.

## Outputs

Either `no change` or bidirectional traceability findings across stable specification scope identity, implementation, and tests.

## Owns

No durable state. Trace Check reads/correlates specs, topology, code, and tests; fixes belong to the relevant spec authority or Build skill.

## Modes

### `check`

Run the bidirectional trace check. It is not a general line-coverage mode.

## Approval

No approval to run.

## Invariants

- spec → code/test and code/test → spec are both checked where expected
- file relocation with unchanged scope ID does not invalidate canonical citations
- implementation/test behavior without authority is a finding, not permission
- absence is reported only where the harness expects a trace

## Completion

Complete when deliberate traceability forms a coherent graph:

`stable specification scope ↔ implementation ↔ tests`
