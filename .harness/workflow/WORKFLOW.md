# Workflow

This is the agent-independent operating contract for the Harness.

Project truth, lifecycle rules, routing, and approval semantics live outside agent-specific adapters. Agent-specific files explain only how a particular agent/runtime enters this shared workflow.

## Session start

1. On a new or cleared session, follow Session Resume; it owns context reconstruction and uses the Deterministic Runtime as the Git/ref/transaction fact source.
2. Read the active Harness Composition — resolve the selected models and method packs only from `.harness/composition/active.json` — then Routing; identify current repository/runtime state, and when on a non-mainline branch derive/read `doc/goals/<branch>.md` if present.
3. Use `context-manifest.yaml` to load only context required by the current work and active composition.

Adapters must not maintain their own restart or Git-transaction checklist.

## Always

1. Establish one bounded Goal before implementation. An explicit Project-bootstrap request routes to Branch Start `bootstrap`; missing Git metadata causes the same bootstrap path before Goal work begins.
2. One Goal owns one exclusive work branch and one landing unit.
3. Persist the active Goal outcome locally at Git-ignored `doc/goals/<branch>.md`; do not serialize task/progress/status state that can be reconstructed from Goal intent + Git + repository truth.
4. Load only guides, active Project-model authority, skills, setup, and knowledge relevant to the current Goal. Do not activate planned/inactive models merely because their design notes exist.
5. Route Project concerns to their owning authority. When a concern is broad but clearly inside one authority, enter its authority orchestrator before prematurely selecting a narrow skill. Active methods may assist discovery/design but never become authority; accepted conclusions are promoted through the owning authority skill.
6. Keep implementation, specifications, tests, and repository state synchronized. When authoritative meaning changes, apply Change Impact: identify materially affected dependent conclusions, route them to their existing owners, and re-establish relevant checks before completion or approval.
7. Leave repeatable evidence for completion claims.
8. Use task-sized commits and Git History for correction folding, requirement-change visibility, and work-branch ownership. Tasks are execution decomposition, not persisted lifecycle state by default.
9. If a Goal branch has no durable outcome, route to Branch Land `abandon` rather than manufacturing integration history.
10. Every Goal branch entering configured mainline requires explicit exact user landing authorization owned by Branch Land.
11. Repository mainline, bootstrap-mainline, fixed landing mechanics, approval-ref mechanics, exact transaction anchors, guarded integration, guarded branch deletion, and restart reconstruction are computed/executed by the Deterministic Runtime. `.harness/runtime/harness.py` is the CLI entrypoint; mechanics remain owned by their runtime modules rather than workflow prose.
12. When reusable cross-work experience is recognized, route it to Dream while evidence is fresh. Persisted Dream proposals are non-authoritative Learning state and are not generic landing cleanup.

## Composition

`.harness/composition/definition.md` owns the composition contract and `.harness/composition/active.json` declares the active selections. Composition determines which Project and Collaboration models and optional method packs are available; it never overrides the authority inside those models or kernel lifecycle rules. Only active method packs are first-class named Harness methods for current work.

## Authority

Authority is **jurisdiction-first**, not one global ladder.

**[AUTH-01]** First classify the concern and determine its owner through Routing. Only then resolve same-subject precedence inside that concern. A Project owner cannot override Harness operation outside Project jurisdiction, and Harness operation does not manufacture Project truth.

Within a Project concern, use this normal same-subject precedence:

1. current Project authority / explicit Project-specific decision owned by that concern under the selected Project model
2. relevant specialized universal Guide
3. General Guide
4. skill procedure
5. temporary working state

A project-specific departure from a Guide must therefore be explicit in the Project authority that owns that concern. Where the Project is silent, the relevant universal Guide remains the governing judgment.

**[AUTH-02]** One rule has one authoritative source. Pointers, adapters, diagrams, manifests, wrappers, and summaries may route to or mirror authority, but must not become a second place that independently decides the same rule.

**[AUTH-03]** Evidence, implementation, tests, repository state, conversation memory, and temporary working state do not manufacture authority merely by existing. They can reveal drift or support a decision; changes in intended truth route back to the owner.

Workflow, Composition, contracts, the two owned vocabulary authorities, mechanisms, Guides, Lifecycle, Harness definitions, and the Deterministic Runtime are Harness authority for their own subjects. Project authority selected by the active Project model and project-specific decisions are Project authority for theirs.

## Lifecycle

```text
owner request
→ explicit Project bootstrap? Branch Start bootstrap → prepare root README / establish committed mainline
→ Goal create: scrutinize one bounded outcome and choose one Goal branch
→ Branch Start create → runtime branch start
→ Goal writes local Git-ignored branch-derived doc/goals/<branch>.md
→ execute coherent task-sized specification / implementation / verification commits
→ owning checks and any intentionally meaningful intermediate user validation
→ no durable outcome? Branch Land abandon → one guarded runtime discard
→ otherwise Goal complete
→ disposition already-identified Dream proposals whose transient evidence would otherwise be lost
→ Branch Land obtains explicit landing authorization
→ runtime records exact branch-bound landing approval
→ Branch Land prepares history while preserving the approved full tree
→ runtime land prepare confirms live remote alignment and pins the current approved-tree-equivalent branch commit plus exact mainline base
→ runtime land merge revalidates approval + branch + mainline + remote alignment, builds candidate off-mainline, and atomically integrates
→ runtime publishes the exact mainline receipt to configured remote before destructive finalization
→ successful finalization removes branch, approval, landing transaction, Goal recovery file, and Session cache
```

Only branches land. A Goal describes the outcome carried by that branch; tasks are execution decomposition.

Goal is the Harness delivery unit. Release, milestone, epic, or initiative grouping may exist in Project tooling while each Goal remains independently bounded and landed.

When explicit abandonment destroys unique work, any safely attributable dirty target work is safety-committed first. Session Resume reconstructs active Goal and landing state from Goal + Git + runtime facts, never conversation memory.

If configured mainline moves after `land prepare`, or landing approval is withdrawn/moved, the runtime refuses an unauthorized new mainline crossing. A `ready` transaction may be aborted and prepared again after affected checks. Approval withdrawal may also cancel an `integrating` transaction while mainline still equals the prepared base. Once mainline equals the recorded candidate, receipt state is irreversible recovery authority: withdrawal preserves the transaction and `land merge --branch <branch>` finishes deterministic recovery.

## Routing

`.harness/workflow/routing.md` is the routing index. Keep concern-to-owner mappings there rather than maintaining a second index here. Under an authority-owning Project model, broad intake may route to an authority orchestrator, which then selects active methods and narrow skills while retaining one authority owner.

## Manual boundaries

A step requiring privilege, secrets, GUI interaction, device access, or authority intentionally unavailable to the agent remains a human step. The agent may document and verify the result but must not claim to have performed it.

## Change propagation

Use the shared [Change Impact](../mechanisms/change-impact.md) mechanism whenever authoritative meaning changes. Changed dependents are not assumed wrong; their previous conclusions are simply not inherited without reconsideration where the changed authority could matter. Do not introduce global dirty-state bookkeeping when owner-routed impact analysis is sufficient.

## Context rule

Persist authority. Persist only irreducible operational intent. Cache pointers. Load context by need. Compute mechanical repository facts instead of caching them in prose/session state.
