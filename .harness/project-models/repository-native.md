# Repository-native Project Model

Defines the `repository-native` Project model.

**[REPO-NATIVE-01]** Repository-native mode preserves the Harness Goal/Git/landing lifecycle while keeping durable project knowledge in the repository's own native structures. Harness Domain/App/Style/Tech reasoning remains available, but accepted Goal-specific decisions are integrated into one transient Goal Spec rather than requiring a permanent Harness Spec corpus.

## Authority shape

For each active Goal:

1. the Goal defines the bounded outcome
2. targeted repository understanding establishes relevant current behavior, native authority, conventions, and constraints
3. Domain/App/Style/Tech reasoning and active methods resolve only the decisions needed for that Goal
4. accepted conclusions are integrated into `doc/goals/<branch>.spec.md`
5. Build implements and proves against that Goal Spec plus any named native constraints
6. required changes to existing native authority are implemented with the Goal
7. optional documentation may persist useful knowledge after implementation
8. landing removes the transient Goal and Goal Spec

The Goal Spec is the temporary authority for the intended delta. Existing code and tests are evidence of current behavior; they do not automatically decide desired behavior.

## Goal Spec contract

A Goal Spec may be tiny. It should contain only what the Goal needs. Use Domain, App, Style, Tech, Event Storming, Story Mapping, Design, Interview Me, Grill, or other active procedures only when they materially reduce uncertainty.

The completion rule is:

> The Goal Spec is ready when implementation can begin without making a consequential product, domain, style, or technology decision accidentally in implementation.

A documentation correction may need only outcome, exact change, and proof. A cross-cutting product change may need all concern sections and several methods.

The Project Authority Target Contract defines how shared authority-editing skills bind to the Goal Spec.

## Repository understanding

Repository analysis is an activity, not a mandatory lifecycle phase. Perform only enough targeted analysis to define the Goal and Goal Spec responsibly. Relevant evidence can include native docs, ADRs, schemas, tests, code, configuration, UI behavior, design-system rules, and established conventions.

Do not declare all existing repository files authoritative. Record only constraints that materially govern the Goal.

## Documentation disposition

After implementation and proof, repository-native mode supports two optional persistence modes in addition to any required native-authority updates:

### Native documentation

Add or update explanatory documentation using the repository's existing organization, terminology, and style.

### Harness Spec projection

Project useful durable knowledge from this Goal into Harness-style Spec scopes. While `repository-native` remains active, projected Spec material is candidate/shadow material and must not silently compete with repository-native authority.

A future move to the `spec` Project model is an explicit migration Goal: establish/validate topology, reconcile native authorities, resolve conflicts, and only then change composition.

## Build contract

Implementation authority is:

- the current Goal boundary
- the current Goal Spec
- relevant native authority/constraints explicitly identified by the Goal Spec

Build may discover missing decisions. It must route them back through Project reasoning and update the Goal Spec before continuing consequential implementation.

## Invariants

- repository-native is not code-as-spec
- the repository supplies evidence and native constraints; the Goal Spec states the intended delta
- one transient Goal Spec integrates accepted Goal-specific conclusions
- Domain/App/Style/Tech reasoning remains available without requiring stable Spec scopes
- Goal Specs are not committed durable project documentation
- required native-authority changes are not deferred to optional documentation
- optional Harness Spec projection remains non-authoritative until an explicit Project-model migration
- Goal/Git/approval/landing semantics remain kernel-owned and identical to other Project models
