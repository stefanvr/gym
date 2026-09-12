# Spec Project Model

Defines the `spec` Project model. Whether it is active is decided only by `.harness/composition/active.json`. Harness v18 also supports the sibling `repository-native` model; selecting one never silently reinterprets authority owned by the other.

The model locates Project authority in explicit specifications owned by Domain, App, Style, and Tech. Those capabilities are authority orchestrators; their narrow skills edit the concern-specific truth they own.

## Authority topology

Spec authority is addressed through stable scopes defined by [Spec Topology](spec-topology.md). Scope IDs are independent of file paths, for example:

```text
domain.identity
domain.billing
app.customer
style.foundation
tech.architecture
```

The mapping and dependency graph live in `doc/spec/topology.json`. Without that manifest, Spec topology is unconfigured; the runtime does not infer authority from conventional file names.

## Project-model contract

The model lets the Harness:

- route a Project concern to one owning authority
- accept broad concerns through the authority orchestrator for that jurisdiction
- locate authority scopes relevant to the current Goal
- distinguish Project truth from method/working material and implementation/evidence
- identify authority changes that require Change Impact
- provide relevant authority to implementation/checking without redefining lifecycle mechanics

The Project model does not own Goal/branch lifecycle, approval, landing, universal Guides, Harness Assurance, or deterministic Git mechanics.

## Authority recording discipline

**[SPEC-WRITE-01]** Stable Spec scopes record **durable conclusions, not the reasoning transcript that produced them**. Domain, App, Style, and Tech use the same recording discipline.

When accepted working conclusions are promoted into a Spec scope:

- state the fact, rule, value, or chosen option first
- prefer compact bullets, tables, or short clauses when they express the authority clearly
- retain constraints that still govern implementation or are needed to interpret the conclusion
- do not preserve brainstorm history, conversational reasoning, candidate comparisons, proof narrative, false starts, or provenance by default
- retain rationale or a rejected alternative only when the owner explicitly asks to keep it, or when that reason is itself needed to interpret or apply the authoritative constraint; normally one concise clause is enough
- do not manufacture standard rationale sections such as `Alternatives considered`, `Why`, `What this rules out`, `Departure`, or `Revisit if` when the durable authority does not need them

Reasoning before promotion may be as detailed as the decision requires. Evidence and working material may retain that analysis where their own owner requires it. Promotion into stable Spec authority compresses the result to the minimum durable truth.

Conciseness must not erase meaning. A compact statement may still include an exception, boundary, dependency, or reason when that information is itself required to apply the authority correctly. History the owner explicitly asked to retain remains. When a touched scope contains transcript-like material with no durable function and no explicit retention requirement, the owning authority should compress it without changing meaning.

## Authority orchestrators

The Spec model binds shared Domain, App, Style, and Tech reasoning to stable Spec scopes. Each follows the [Authority Orchestrator Contract](../contracts/authority-orchestrator-contract.md) and [Project Authority Target Contract](../contracts/project-authority-target-contract.md).

A broad concern enters its owning capability. The orchestrator identifies affected stable scopes, loads required dependencies, and selects useful active methods/narrow skills. Accepted conclusions become authority only through the existing authority-editing skills.

Build consumes selected Project authority but is not a fifth Spec authority.

## Scope ownership

A scope belongs to the authority declared by its stable ID/topology entry. File placement does not transfer authority.

Each Domain/App/Style/Tech orchestrator owns topology entries for its own scopes. A dependency edge is owned by the dependent scope's authority. `doc/spec/topology.json` is structural Project-model metadata, not product truth by itself.

Moving a scope file while preserving its ID is physical reorganization. Renaming, splitting, merging, or reassigning scopes changes authority structure and is a deliberate Project change.

## Scoped context and checks

For selected scopes, Spec Topology provides:

- **load set** — selected scopes plus transitive dependencies
- **impact set** — selected scopes plus transitive reverse dependents
- **graph-check set** — union of load and impact sets

These sets reduce context; they do not replace semantic Change Impact. Reverse dependents are candidates for reconsideration, not proof that each dependent must change.

Authority checks operate locally on relevant scopes. Sanity Specification Check examines affected cross-scope relationships. A full-project check may deliberately select every scope.

## Stable citations

Where an authority uses local stable identifiers, cross-scope citations include the scope ID, for example `domain.billing:R-017` or `tech.architecture:A-004`. Moving a file does not change the citation.

## Method integration

When selected, Interview Me, Event Storming, Story Mapping, and Design may assist Spec authorities. Methods are techniques, not Project authorities; their output becomes authority only through the owning capability/skill.

Natural routes are:

- Interview Me → any authority where owner intent is incomplete
- Event Storming → Domain discovery
- Story Mapping → App discovery/structuring
- Design → cross-authority coordination with each authority retaining its own truth
