# Harness Composition

Owns how one Harness installation selects its Project model, Collaboration model, and optional method packs.

Composition is routing/configuration. It does not override Workflow, Lifecycle, an owning Project authority, or a skill's ownership.

## Dimensions

1. **Project model** — exactly one model describing where contextual Project authority lives.
2. **Collaboration model** — exactly one model describing how trusted contributors coordinate Harness lifecycle work.
3. **Method packs** — zero or more techniques that may assist owning authorities without becoming Project authority.

**[COMPOSE-01]** A valid composition selects exactly one supported Project model and exactly one supported Collaboration model. Method packs are optional and additive. Kernel authority remains active for every valid composition.

## Kernel boundary

The kernel is the universal governance/lifecycle layer that remains meaningful regardless of model selection. It includes the Harness/Project jurisdiction boundary, Goal/lifecycle mechanics, approval and landing semantics, Routing contracts, Change Impact, universal Guides, Continuity/recovery contracts, deterministic repository mechanics, authority/method contracts, and Harness Assurance infrastructure.

Project-model mechanics belong to the selected Project model. Collaboration mechanics belong to the selected Collaboration model. The runtime mirrors that boundary with separate `kernel.py`, `project_model.py`, and `collaboration_model.py` modules; `checker.py` may inspect all layers without owning their rules.

## Selection authority

**`.harness/composition/active.json` is the only selection authority.** Its `selection` block decides the active Project model, Collaboration model, and method packs. Its `supported` and `sources` blocks declare what this distribution supports and where each definition lives.

No README, context manifest, model definition, roadmap, or release note may independently decide the active selection. `workflow/context-manifest.yaml` inventories loadable definitions; agents resolve the active subset from `active.json`.

The machine-readable architectural inventory is `.harness/composition/classification.json`.

When selected, the Spec model binds `.harness/project-models/spec-topology.md`. Its `doc/spec/topology.json` manifest is Project state, not composition state or Harness authority.

Whichever Collaboration model is selected binds through `active.json` `sources`. Cooperative actor/role and handoff records are coordination/runtime state, not Project authority.

## Selection rules

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
- `project-model/spec`
- `collaboration/single-user`
- `collaboration/cooperative-multi-user`
- `method`
- `exploration`

## Non-goals

Composition is not a plugin marketplace, dependency solver, distributed configuration service, permission system, or dynamic runtime module loader. Its purpose is to make architectural ownership explicit, selectable, and mechanically checkable.
