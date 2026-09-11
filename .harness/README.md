# Software Development Harness

Human orientation only. This file is **not execution authority** and is intentionally outside the context manifest.

The Harness is agent-independent under `.harness/`. Repository-root adapters (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`) only enter the shared workflow. Operational truth lives in [Workflow](workflow/WORKFLOW.md), [Routing](workflow/routing.md), owning capabilities/skills, and Project specifications.

## Shipped composition

The active selection lives only in [`composition/active.json`](composition/active.json). This distribution ships with `spec` + `cooperative-multi-user` selected and Interview Me, Event Storming, Story Mapping, and Design enabled; `single-user` is also supported, and each Collaboration model has its own [Assurance operating profile](harness-assurance.md#supported-operating-profiles). Domain, App, Style, and Tech are authority orchestrators. The Spec model uses [explicit stable-scope topology](project-models/spec-topology.md); the cooperative Collaboration model uses trusted immutable Goal handoffs and one serialized integration authority. The runtime is split into kernel, Project-model, Collaboration-model, checker, and CLI modules. See [Harness Composition](composition/definition.md) and the non-authoritative [architecture map](roadmap/v17.md).

## Mental model: three layers + Dream

Use this as a map, not as another authority.

The constitutional split is: **Harness owns how work is governed and universal judgment; Project owns contextual Project truth.**

### 1. Spec — decide what should be true

- **Goal** bounds the one current delivery outcome.
- **Brainstorm** is a non-authoritative exploration surface for supplied material and draft owner-intent work.
- **Domain**, **App**, **Style**, and **Tech** are the Spec Project model's authority-owning orchestrators.
- **Methods** such as Interview Me, Event Storming, Story Mapping, and Design provide reusable discovery/coordination techniques without becoming Project authority.
- **Grill** pressure-tests consequential candidates before they become authority.

The active Goal outcome is recoverable from the current branch plus local Git-ignored `doc/goals/<branch>.md`. That file is operational context, not Project history.

### 2. Verify — prove what is true

- capability checks verify their own specifications or outputs
- **Build Check** verifies implementation and executable evidence
- **Sanity** finds cross-cutting drift and routes findings to owners
- approval authorizes lifecycle boundaries; evidence does not substitute for approval

### 3. Environment — make good work repeatable

- **Guides** provide universal Harness judgment
- **Setup** keeps development/runtime preparation reproducible
- **Knowledge** preserves reusable technology-conditioned learnings
- **Continuity** reconstructs context from Goal + Git + Project truth
- **Lifecycle** sequences one Goal branch through landing or abandonment
- **Deterministic Runtime** computes repository facts and performs guarded mechanics selected by lifecycle owners

### Dream — compound experience without creating authority

Dream turns reusable experience into proposals. It never promotes itself: accepted proposals still go through the existing owner and normal lifecycle.

## Goal lifecycle

```text
Goal
  ↓
one exclusive branch
  ↓
work / task-sized commits
  ↓
verify
  ↓
explicit landing authorization
  ↓
deterministic prepare / land
```

The Harness lifecycle uses Goal as its single delivery unit. Release, milestone, epic, or initiative grouping may exist in Project tooling, while each Harness Goal remains independently bounded and landed.

## Start a Project

```text
drop Harness into Project root
        ↓
configure a reachable Git remote for eventual landing
        ↓
ask the agent to bootstrap the Project
        ↓
python .harness/runtime/harness.py check
```

**Landing is deliberately remote-required.** The remote named by `.harness/runtime/config.json` (default `origin`) must be configured and reachable when landing is prepared/completed. A Goal is not considered landed until the exact resulting mainline receipt is published there; local-only work may proceed before that boundary, but the normal landing lifecycle cannot complete without the configured remote.

Bootstrap prepares root README orientation and establishes configured Git mainline when needed. `check` deterministically answers **“is the Harness internally coherent?”**

**Semantic model evidence is deliberately not shipped as a generic baseline.** Evidence is valid only for the exact provider/model/profile, exact constitutional evaluator input digest, and current scenario-suite digest. Generate evidence with the model/profile you intend to claim after installing or changing the Harness. Until current matching evidence exists, `assure --profile ...` returning `UNKNOWN` is the intended design, not a packaging defect.

For profile-qualified Assurance, run the behavior suite with the intended model/profile, retain resulting evidence, then run:

```text
python .harness/runtime/harness.py assure --profile "provider/model/profile"
```

Harness CI remains separate from Project CI.

## Default flow

```text
Goal
 ↓
Specification flow and/or Build flow
 ↓
Verify
 ↓
land or abandon
```

Use only specification capabilities needed by the current Goal. See [Workflows](README-workflows.md) for diagrams and [Routing](workflow/routing.md) when ownership is unclear.

## Five rules to remember

1. **One Goal, one branch, one landing unit.**
2. **Jurisdiction first; one concern, one owner.** Route before applying precedence; do not duplicate authority.
3. **Changed authority propagates.** Re-establish affected dependent conclusions through their existing owners.
4. **Persist only irreducible intent.** Goal outcome is local recovery state; Git and Project artifacts carry durable history/truth.
5. **Dream proposes; owners promote.** Learning cannot silently rewrite the Harness.

## Repository map

- `.harness/composition/` — active architectural dimensions and classification inventory
- `.harness/README-vocabulary.md` — working vocabulary for Project owners/contributors/developers
- `.harness/harness-extended-vocabulary.md` — additional vocabulary for Harness development/assurance
- `.harness/project-models/` / `.harness/collaboration-models/` — selected model definitions
- `.harness/methods/` — optional non-authoritative method packs
- `.harness/workflow/` — workflow, routing, and context manifest
- `.harness/guides/` — universal Harness judgment
- `.harness/skills/` — executable skills
- `.harness/capabilities/` — capability families and artifact boundaries
- `.harness/lifecycle/` — Goal/branch sequencing
- `.harness/runtime/` — deterministic repository mechanics plus `check` / `assure`
- `.harness/learning/`, `.harness/knowledge/`, `.harness/continuity/` — learning and session support
- `.harness/harness/` — Harness maintenance/change support
- `.harness/harness-limitations.md` / `.harness/harness-assurance.md` — supported operating profile and Harness Assurance policy

Agents should enter through their root adapter and follow `workflow/context-manifest.yaml`; they should not load this README as policy.
