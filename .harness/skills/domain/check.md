# Domain Check

Scrutinizes authoritative Domain scope(s) before implementation relies on them.

## Authority target

Follow the [Project Authority Target Contract](../../contracts/project-authority-target-contract.md). Under `spec`, edit/check the affected stable Spec scope(s). Under `repository-native`, edit/check the corresponding section of the current transient Goal Spec and relevant named native constraints. Any scope-ID, Spec Topology, reverse-dependency, or scoped identifier requirement below is `spec`-only unless the repository already uses an equivalent native identifier deliberately.


## Define

Check that Domain language, events, rules, and data form one coherent desired state inside the selected scope(s), then surface dependency-boundary concerns for graph checking.

Run after meaningful Domain changes and independently as part of broader sanity checks.

## Inputs

Required:

- one or more affected `domain.*` scope IDs and their documents from Spec Topology

As needed:

- transitive dependency scopes required to interpret them
- current goal
- method/brainstorm source material
- existing code/tests when checking an existing specification

## Checks

### 1. Rule inputs exist

Every input required by a rule must resolve to a Domain term, defined Domain data, or an explicit primitive in the local scope or an explicitly depended-on scope.

### 2. Flow connects end to end

Walk relevant flows as:

`cause → event → changed state → next consumer`

A step with no cause is a finding. A result nothing consumes is a finding unless intentionally terminal.

### 3. Vocabulary has no orphans

Every term used by rules or data must exist in Domain language. Cross-scope terms must resolve through an explicit topology dependency rather than an accidental file import.

Every Domain term should be used by a rule, event, or the data model.

### 4. Proposed names are resolved

Any unresolved harness-proposed name must be put to the owner. After resolution, discard provenance metadata from authoritative scope documents.

### 5. Event names describe occurrences

Ask whether every event name describes what happened rather than merely one consequence.

### 6. No parked scrutiny

Find unresolved work masquerading as specification, including confidence columns, “whose word”, proposed-name markers, decided-but-unbuilt markers, or unresolved questions embedded in authoritative tables.

### 7. Rule identifiers

For every local `R-n`:

- the identifier is unique inside its stable Domain scope
- the rule still expresses a domain truth the scope needs
- obsolete rules are questioned rather than silently retained for numbering continuity
- external citations use `<scope-id>:R-n` where cross-scope ambiguity is possible

Spec/code/test citation resolution belongs to Sanity Trace Check.

### 8. Scope boundary

Question duplicated meaning across selected Domain scopes and undeclared dependencies discovered during scrutiny. Moving or splitting authority is not a local cleanup; route it as a topology/authority change.

### 9. Spec authority is conclusion-shaped

Under `spec`, apply `SPEC-WRITE-01`: stable Domain scopes should state the durable terms, rules, flows, and data needed by the product, not preserve workshop narrative, conversational reasoning, candidate analysis, or provenance that no longer affects meaning. Prefer compact representation where it is equally clear.

## Outputs

Either `no change` or evidence-backed Domain findings routed to Language, Events, Rules, Data, or affected topology ownership.

## Owns

No durable Domain state. Domain Check reads selected Domain scopes and relevant evidence but does not repair specification or topology itself.

## Modes

### `check`

Run the local/cross-section Domain coherence check for selected scope(s). Narrow creation/refinement work belongs to the owning Domain skill. Cross-authority graph coherence belongs to Sanity Specification Check.

## Completion

Complete when:

- all findings are resolved or explicitly block implementation
- each selected scope states one coherent desired Domain slice
- required dependencies are explicit
- no scrutiny metadata remains parked in authoritative documents

## Approval

Routine scrutiny does not require approval. When scrutiny exposes a real unresolved domain decision or scope-placement decision, route it to the appropriate Domain owner.

## Invariants

- Domain Check can run independently on selected scopes
- local identifier uniqueness is scoped, not globally inferred from filenames
- scrutiny happens before implementation depends on the specification
- raw method/brainstorm material is never copied into authority without scrutiny
- unresolved reasoning does not masquerade as specification
