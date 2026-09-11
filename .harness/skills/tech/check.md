# Tech Check

Verifies that authoritative Tech scope(s) still describe the project and relevant external reality truthfully.

## Define

Check every authoritative claim in the selected `tech.*` scope(s) against current evidence.

Use after any Tech change, when implementation materially changes architecture, during maintenance/sanity discovery, before relying on an old technical claim, or before release when Tech claims are relevant.

## Inputs

Required:

- one or more affected `tech.*` scope IDs and documents from Spec Topology
- current repository state

As needed:

- transitive topology dependencies
- current external documentation or artifacts
- code references
- tests
- configuration

## Outputs

Either `no change`, corrections required, obsolete rule found, broken Tech-document/evidence reference found, stale external claim found, invalid/duplicate local identifier found, or a topology-boundary finding.

## Method

### 1. Repository claims

Every statement describing the current tree must still be true. A sentence accurately describing the project two goals ago but not today is a finding.

### 2. External claims

Every material claim about the outside world must be verified against current evidence. Do not rely on memory for claims whose truth matters to the decision.

### 3. Scope/document ownership

Each selected document must still be the path bound to its stable Tech scope, and its content must belong to that scope's declared authority.

### 4. Markdown integrity

The specification must render as intended. Formatting errors that change semantic structure are findings.

### 5. Architecture identifiers

For every local `A-n`:

- the identifier is unique inside its stable Tech scope
- the architecture rule still expresses a technical truth the scope needs
- obsolete rules are questioned rather than silently retained
- external citations use `<scope-id>:A-n` where cross-scope ambiguity is possible

Spec/code/test citation resolution belongs to Sanity Trace Check.

### 6. Dependencies

Cross-scope technical assumptions needed to interpret this scope should be represented explicitly in Spec Topology. Undeclared structural coupling is a finding or a Change Impact signal.

## Owns

No durable Tech state. Tech Check reads selected Tech scopes, repository state, topology, and external evidence; findings route to Tech Repair, Tech Decide, Tech Architecture Rule, or the owning Tech orchestrator for topology changes.

## Modes

### `check`

Run the complete Tech truth/document-reference/external-claim check for selected scope(s). Spec/code/test traceability remains with Sanity Trace Check.

## Completion

Complete when all authoritative claims have been verified, corrected, or explicitly identified as unresolved, and required topology dependencies are explicit.

## Approval

Routine truth corrections do not require approval unless they reveal that an actual technology, architecture, or scope-structure decision must change.

## Invariants

- scrutiny runs after every Tech modification
- stale authority is a finding
- remembered external behavior is not enough when verification is possible
- local `A-n` uniqueness is scoped; canonical identity includes the stable scope ID
- broken references inside Tech authority are findings; spec/code/test traceability is not re-checked here
- obsolete architecture rules are not preserved merely for numbering continuity
