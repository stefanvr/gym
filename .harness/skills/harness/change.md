# Harness Change

Maintains the harness's own operating model, either correcting it without changing what it decides or applying an owner-approved change to what it decides.

## Define

Edit harness authority in one of two ways.

A **repair** corrects an inconsistency — inconsistent terminology, duplicated authority, a broken route or path, a contract violation, adapter drift, or a stale diagram — and leaves the harness's decisions unchanged.

A **design** change moves what the harness decides: adding or removing a capability or skill, restructuring the lifecycle, changing the jurisdiction/precedence model, changing what a term means, or moving ownership between capabilities. It is applied only after the owner has approved it.

Harness Change executes what Sanity Harness Check discovers. Harness Check finds and routes; it does not edit. This skill edits.

It does not decide *whether* a design change should be made. That is the owner's. Once approved, the change proceeds as one bounded Goal and this skill applies exactly what the owner approved, coherently and with its mirrors in step.

## Started

- an evidenced Sanity Harness Check finding
- an owner-approved change to what the harness decides, including an accepted Dream proposal
- a user instruction to correct a specific harness document
- a broken route, manifest path, or reference discovered during ordinary work
- a skill added to or removed from `.harness/skills/` whose agent-side wrapper does not yet match
- a stale `README-workflows.md` diagram discovered after harness development changed a lifecycle, routing flow, capability skill set, or orchestration order

## Inputs

Required:

- the evidenced finding or the approved change, naming the document that owns the concern
- the harness documents the edit touches
- for `repair`, the evidence establishing the correct state
- for `design`, the owner's approval of the intended change

As relevant:

- `.harness/contracts/task-capability-skill-contract.md` when the edit touches skill or capability shape
- `.harness/README-vocabulary.md` when the edit touches a term used while operating the Harness, and `.harness/harness-extended-vocabulary.md` when it touches a Harness-development/internal term
- `.harness/workflow/routing.md` and `.harness/workflow/context-manifest.yaml` when the edit touches routing or loading
- the shared Change Impact mechanism for every `design` change and any repair that reveals another authority was semantically affected
- `.harness/harness/invariants.json`, behavior scenarios, and semantic-surface configuration when constitutional/model-facing semantics are affected

## Outputs

A harness whose documents agree, plus a re-run of the affected Harness Check concern establishing whether the finding is closed or the change is coherent.

For `repair`, the harness's operating decisions are unchanged. For `design`, they are exactly what the owner approved.

## Owns

`.harness/**`, except the technology entries under `.harness/knowledge/`, which Knowledge Capture owns.

That includes workflow, routing, the context manifest, both owned vocabulary files, contracts, mechanisms, guides, capability and support-family definitions, skill documents, `README-workflows.md`, the Deterministic Runtime/config/tests under `.harness/runtime/`, and the agent adapters under `.harness/workflow/agent/`.

Harness Change owns the maintenance requirement for `README-workflows.md`: every harness change must check the diagrams against the edit and update any diagram whose lifecycle, routing flow, capability skill set, or orchestration order changed. `README-workflows.md` mirrors this requirement; it does not own it.

It does not own project specifications, implementation, or Goal/Session lifecycle state.

It owns the repository-root agent entrypoints and the agent-side skill wrappers, currently `.claude/skills/`, only to the extent of keeping each one thin and pointing at its `.harness` authority: adding a wrapper when a skill is added, removing one when a skill is removed, and correcting a wrapper whose target moved. A wrapper is an invocation shortcut and never carries policy of its own.

Harness Change also maintains the **shipped** root `README.md` bootstrap marker/instruction and Harness link section as a distribution mirror of Branch Start bootstrap behavior. After bootstrap, Project name/description and any pre-existing Project README content are Project material; Harness Change does not own or rewrite them merely because the Harness section is present.

## Modes

### `repair`

Apply the smallest evidenced correction that leaves the harness's decisions unchanged.

### `design`

Apply a change to what the harness decides.

Preconditions:

- the owner has approved the intended change
- the approved change is bounded as the current Goal

Applying more than the owner approved is not a design change; it is a second one.

## Method

1. Restate the finding or approved change and name the authoritative document that owns the concern.
2. Establish which mode applies by asking whether this changes what the Harness decides. If it does not, `repair`. If it does, `design` — and do not proceed without the owner's approval.
3. Apply the smallest edit at the one authority that owns the rule. Leave pointers pointing; do not close a finding by restating the rule beside its authority.
4. For a `design` change, apply Change Impact explicitly. Build the affected set from the changed authority: dependent authority, routing/context loading, mirrors/diagrams, adapters/wrappers, deterministic implementation/config, and semantic-regression coverage/evidence. For each category establish `affected → reconciled` or `not affected → reason`. A repair uses the same test if it reveals semantic impact outside the repaired representation.
5. Read every diagram in `README-workflows.md` against the edit and update the ones it altered. Do not conclude from memory that none is affected.
6. Update `.harness/workflow/routing.md` and `.harness/workflow/context-manifest.yaml` in the same change when the edit added, moved, or removed a document or concern.
7. Add, remove, or retarget the matching agent-side skill wrapper in the same change when a skill document was added, removed, or moved.
8. When constitutional invariants changed, update `.harness/harness/invariants.json` only as an index to their authoritative source, then add/update behavior scenarios so every required invariant remains covered. Do not copy the invariant prose into the registry.
9. Treat `.harness/evals/behavior/semantic-surface.json` as a model-facing change-impact inventory, not as proof of what a constitutional evaluation saw. When the exact constitutional evaluator request sequence or behavior scenario suite changes, prior real-model evidence with a different evaluation-input or suite digest is stale. `harness.py check` verifies supplied evidence freshness; a current real-model run remains Assurance evidence when required.
10. When `.harness/runtime/` modules, runtime configuration semantics, or runtime transaction behavior changed, run the executable runtime regression suite directly with `python3 .harness/runtime/tests/test_harness.py`. Do not treat structural `harness.py check` as behavioral evidence for runtime semantics.
11. Run `python3 .harness/runtime/harness.py check`, the behavior evaluator tests/`--validate-only` when semantic-regression artifacts changed, and the semantic Sanity Harness Check. Report remaining findings or missing Assurance evidence rather than inheriting an old conclusion.

## Scrutiny

Before recording the edit, ask:

- Does this change what the harness decides, or only whether it says so consistently?
- If it changes what the harness decides, did the owner approve this, and is what I am applying what they approved?
- Does the document I edited own this rule?
- Am I closing the finding, or duplicating the rule into a second place?
- What conclusions depended on the previous authoritative meaning, and which owners/checks must be re-established?
- Did I mark something `not affected` because I have a reason, or merely because I did not notice an edit?
- Did this change a route, path, skill set, or orchestration order that another document mirrors?
- Did this add, remove, or move a skill whose agent-side wrapper must move with it?
- Did this change a constitutional invariant or model-facing authority, and if so are semantic coverage and evidence freshness accounted for?
- Did this change executable runtime behavior, and if so did the runtime integration suite exercise the changed destructive/restart/error path?

## Completion

Complete when the finding is closed or the approved change is expressed, the Change Impact set is reconciled, mirrors agree, semantic coverage remains complete, and Sanity Harness Check plus deterministic `harness.py check` pass. When model-facing semantics changed, current real-model evidence is separately required only where Harness Assurance requires it for the claimed profile. When executable runtime behavior/configuration semantics changed, the direct runtime integration suite must also pass (or an environmental inability to execute Python itself must be reported as missing evidence rather than silently omitted).

For `repair`, additionally: the harness's decisions are unchanged.

## Approval

`repair` requires no approval, because it leaves the harness's operating decisions unchanged.

`design` requires the owner's explicit approval of the intended change **before** it is applied. The approved change is then carried as one bounded Goal.

## Dependencies / Routing

Sanity Harness Check supplies harness findings. Dream may supply an owner-accepted harness-improvement proposal. Knowledge entry findings route to Knowledge Capture, which owns its own entries. Project-repository, specification, implementation, or lifecycle findings are not harness changes and route to their existing owner.

## Invariants

- a `repair` never changes what the harness decides
- a change to what the harness decides is applied only under `design`, and only after the owner approved it
- Harness Check discovers, Harness Change edits, and neither does the other's work
- every edit is grounded in an evidenced finding or an approved change
- a rule stays at its one authority; a finding is never closed by duplicating it
- changed authoritative meaning propagates through Change Impact before dependent completion
- documents mirroring a route, path, skill set, or orchestration order are updated in the same change
- constitutional invariants remain indexed once and behavior-covered when required
- agent-side skill wrappers match the `.harness` skill set exactly and carry no policy of their own
- Knowledge entries remain owned by Knowledge Capture
- the affected Harness Check concern is re-run after the edit
