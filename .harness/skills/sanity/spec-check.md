# Sanity Specification Check

**Applicability:** `spec` Project model only. Under `repository-native`, use Sanity Run plus the relevant Domain/App/Style/Tech/Build checks against the Goal Spec and named native constraints; do not manufacture stable Spec scopes.

Checks whether authoritative Spec scopes describe one coherent product.

## Define

Check that relevant Tech, Domain, App, and Style scopes are individually sound and mutually coherent without loading every specification document by default.

## Internal checks

For selected/affected scopes invoke as present:

- Tech Check
- Domain Check
- App Check
- Style Check
- Style Preview Check where relevant

Do not duplicate their internal scrutiny.

## Cross-spec checks

1. Scope IDs resolve through the active Spec topology and physical paths are not treated as authority identities.
2. Domain concepts/rules used by App exist in the local/dependency closure.
3. Style triggers/surfaces referenced from App/Domain exist.
4. Style does not invent causes; App/Domain do not invent Style character.
5. Product scopes do not rely on technical behavior or constraints Tech has ruled out.
6. Equivalent decisions do not have two owners/scopes.
7. Current specification additions stay inside the current Goal unless the user explicitly expands it.
8. A decision open in one scope is not silently settled in another.
9. Declared `depends_on` edges cover dependencies required to interpret affected scopes; physical co-location is not a substitute.
10. Reverse dependents identified by Spec Topology are considered by Change Impact; unchanged dependents may be discharged with evidence rather than edited mechanically.
11. Spec topology is explicit; missing `doc/spec/topology.json` is unconfigured rather than inferred from file names.
12. Stable Domain, App, Style, and Tech scopes follow `SPEC-WRITE-01`: they preserve durable conclusions rather than decision/workshop/conversation transcripts, with rationale retained only when it is itself needed or explicitly requested.

## Inputs

Required:

- the Sanity Finding test
- explicit active Spec topology (`doc/spec/topology.json`)
- one or more selected/changed scope IDs, or an explicit full-project check intent
- current Goal where relevant
- capability-level check skills

Use the Spec Topology load set for interpretation and the graph-check set for affected boundary scrutiny.

## Outputs

Either `no change` or evidence-backed local/cross-scope findings routed to the owning specification authority or topology entry owner.

## Owns

No durable specification state. It invokes/combines checks but does not repair specifications or topology.

## Modes

### `check`

Run local capability checks and affected graph-boundary checks required for the selected project state. A deliberate full-project check may select all scopes; ordinary Goal work should stay scoped.

## Approval

No approval to run. Any newly exposed product/technology/topology decision follows the approval policy of its owning capability.

## Invariants

- internal capability checks remain authoritative for their own scopes
- cross-scope contradictions are findings
- stable scope identity survives file relocation
- no decision silently has two owners
- open decisions are not treated as settled elsewhere
- reverse dependents are impact candidates, not automatic edit requirements
- Sanity does not fix the specs or topology it checks

## Completion

Complete when selected scopes and their materially affected graph boundaries form one coherent desired product state.
