# Harness Composition

Owns how one Harness installation selects its Project model, Collaboration model, and optional method packs.

Composition is routing/configuration. It does not override Workflow, Lifecycle, an owning Project authority, or a skill's ownership.

## Dimensions

1. **Project model** — exactly one model describing where contextual Project authority lives.
2. **Collaboration model** — exactly one model describing how trusted contributors coordinate Harness lifecycle work.
3. **Method packs** — zero or more techniques that may assist owning authorities without becoming Project authority.

**[COMPOSE-01]** A valid operating composition selects exactly one supported Project model and exactly one supported Collaboration model. Method packs are optional and additive. Kernel authority remains active for every valid composition.

The standalone distribution may exist in one explicit **unconfigured bootstrap state** where both `selection.project_model` and `selection.collaboration_model` are `null`. That state is internally coherent distribution state, not a valid operating composition: normal lifecycle work is blocked until bootstrap records the user's explicit selections. A missing, malformed, partially configured, or unsupported composition is not equivalent to the explicit unconfigured state.

## Kernel boundary

The kernel is the universal governance/lifecycle layer that remains meaningful regardless of model selection. It includes the Harness/Project jurisdiction boundary, Goal/lifecycle mechanics, approval and landing semantics, Routing contracts, Change Impact, universal Guides, Continuity/recovery contracts, deterministic repository mechanics, authority/method contracts, and Harness Assurance infrastructure.

Project-model mechanics belong to the selected Project model. Shared Project reasoning may be used by more than one Project model but writes authority only through the active model's target contract. Collaboration mechanics belong to the selected Collaboration model.

## Selection authority

**`.harness/composition/active.json` is the only selection authority.** Its `selection` block decides the active Project model, Collaboration model, and method packs. Its `supported` and `sources` blocks declare what this distribution supports and where each definition lives.

The standalone distribution ships deliberately unconfigured for the two operating dimensions. Bootstrap may transition that explicit state exactly once into a supported operating composition after user input. It must not silently inherit the distribution author's preferences.

This distribution supports two Project models:

- `spec` — durable Harness Spec scopes are Project authority
- `repository-native` — one transient Goal Spec owns each Goal's intended delta while durable project knowledge stays in native repository structures unless deliberately projected

Both `single-user` and `cooperative-multi-user` are supported Collaboration models, and bootstrap must obtain an explicit choice.

No README, context manifest, model definition, roadmap, or release note may independently decide the active selection. `workflow/context-manifest.yaml` inventories loadable definitions; agents resolve the active subset from `active.json`.

When selected, the Spec model binds `.harness/project-models/spec-topology.md`. Its `doc/spec/topology.json` manifest is Project state, not composition state or Harness authority.

When selected, repository-native binds `.harness/project-models/repository-native.md` and the Project Authority Target Contract. Its transient `doc/goals/<branch>.spec.md` is Goal-local Project authority and is removed after landing/abandonment.

Whichever Collaboration model is selected binds through `active.json` `sources`. Cooperative actor/role and handoff records are coordination/runtime state, not Project authority.

## Selection rules

- The explicit bootstrap state is exactly both Project and Collaboration selections `null`; partial configuration is invalid.
- Bootstrap requires explicit choice of `spec` or `repository-native` and explicit choice of `single-user` or `cooperative-multi-user`; there is no silent default.
- Unsupported or unknown selections are structural Harness findings.
- Every supported component has one `.harness` source binding.
- Changing the selected Project or Collaboration model is a Harness design/configuration change and must not silently reinterpret existing Project truth.
- A Project model cannot redefine kernel lifecycle or approval semantics.
- A Collaboration model cannot redefine Project truth ownership.
- A method pack may propose, elicit, analyse, model, structure, or coordinate work; authority still follows the selected Project model and owning capability/skill contracts.
- Inactive method packs are not invoked as named Harness procedures merely because their definitions are shipped.

## Architectural inventory

Every shipped `.harness` artifact is classified by primary architectural home. Cross-layer dependencies are recorded as `couplings`; they describe current dependency edges, not shared ownership.

Primary layer values are:

- `kernel`
- `project-reasoning`
- `project-model/spec`
- `project-model/repository-native`
- `collaboration/single-user`
- `collaboration/cooperative-multi-user`
- `method`
- `exploration`

## Non-goals

Composition is not a plugin marketplace, dependency solver, distributed configuration service, permission system, or dynamic runtime module loader. Its purpose is to make architectural ownership explicit, selectable, and mechanically checkable.
