# Workflow

This is the agent-independent operating contract for the Harness.

Project truth, lifecycle rules, routing, and approval semantics live outside agent-specific adapters. Agent-specific files explain only how a particular agent/runtime enters this shared workflow.

## Session start

1. On a new or cleared session, follow Session Resume; it owns context reconstruction and uses the Deterministic Runtime as the Git/ref/transaction fact source.
2. Read Harness Composition from `.harness/composition/active.json`, then Routing. If both operating selections are explicitly unconfigured, do not invent active models: only the bootstrap path may obtain and persist those user decisions. Otherwise resolve selected models and method packs only from `active.json`. Identify current repository/runtime state, and when on a non-mainline branch derive/read `doc/goals/<branch>.md` if present. If `repository-native` is active, also derive/read `doc/goals/<branch>.spec.md` when present.
3. Use `context-manifest.yaml` to load only context required by the current work and active composition.

Adapters must not maintain their own restart or Git-transaction checklist.

## Always

1. Establish one bounded Goal before implementation. An explicit Project-bootstrap request routes to Branch Start `bootstrap`; missing Git metadata or an explicitly unconfigured Harness composition causes the same bootstrap path before Goal work begins. Bootstrap first decides whether an existing committed repository should use the `main-shadow` confidence-building boundary; if selected, `main-shadow` becomes configured mainline while the repository's original mainline remains untouched. Bootstrap configuration and the pre-Goal local configured-mainline baseline are not Goal implementation.
2. One Goal owns one exclusive work branch and one landing unit.
3. Persist the active Goal outcome locally at Git-ignored `doc/goals/<branch>.md`; do not serialize task/progress/status state that can be reconstructed from Goal intent + Git + repository truth.
4. Load only guides, active Project-model authority, skills, setup, and knowledge relevant to the current Goal. Do not activate inactive models merely because their definitions are shipped.
5. After the Goal is clear, make Project authority implementation-ready before consequential implementation. Under `spec`, resolve required meaning into stable Spec scopes. Under `repository-native`, perform targeted repository understanding as needed and integrate accepted conclusions into one transient `doc/goals/<branch>.spec.md`.
6. When the owner is still deciding whether there is work at all, use Discovery: inspect only relevant evidence, use fitting Brainstorm/methods/Extensions, and remain transient unless the owner explicitly publishes a finding or promotes a bounded outcome to Goal. Personal Notes are consulted only on explicit request and never steer work by mere existence.
7. Route Project concerns to their owning authority/reasoning capability. When a concern is broad but clearly inside one authority, enter its orchestrator before prematurely selecting a narrow skill. Active methods and installed Extensions may assist discovery/design but never become authority; accepted conclusions are promoted through the owning authority skill into the active Project authority target. Extensions add capability, not authority, and never silently override core skills.
8. Keep implementation, active Project authority, tests, and repository state synchronized. When authoritative meaning changes, apply Change Impact: identify materially affected dependent conclusions, route them to their existing owners, and re-establish relevant checks before completion or approval.
9. Leave repeatable evidence for completion claims.
10. Use task-sized commits and Git History for correction folding, requirement-change visibility, and work-branch ownership. Tasks are execution decomposition, not persisted lifecycle state by default.
11. If a Goal branch has no durable outcome, route to Branch Land `abandon` rather than manufacturing integration history.
12. Every Goal branch entering configured mainline requires explicit exact user landing authorization owned by Branch Land.
13. Repository mainline, bootstrap-mainline, fixed landing mechanics, approval-ref mechanics, exact transaction anchors, guarded integration, guarded branch deletion, and restart reconstruction are computed/executed by the Deterministic Runtime. `.harness/runtime/harness.py` is the CLI entrypoint; mechanics remain owned by their runtime modules rather than workflow prose.
14. When reusable cross-work experience is recognized, route it to Dream while evidence is fresh. Persisted Dream proposals are non-authoritative Learning state and are not generic landing cleanup.

## Composition

`.harness/composition/definition.md` owns the composition contract and `.harness/composition/active.json` owns selection state. The standalone distribution may begin explicitly unconfigured; Branch Start bootstrap obtains the user's operating choices before normal lifecycle work. Once configured, Composition determines which Project and Collaboration models and optional method packs are active; it never overrides the authority inside those models or kernel lifecycle rules. Only active method packs are first-class named Harness methods for current work.

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
→ explicit Project bootstrap? Branch Start bootstrap → decide main-shadow onboarding first → prepare root README / establish committed configured mainline
→ Goal create: scrutinize one bounded outcome and choose one Goal branch
→ Branch Start create → runtime branch start
→ Goal writes local Git-ignored branch-derived doc/goals/<branch>.md
→ Project Define: inspect repository as needed and make active Project authority implementation-ready
   ↳ spec: update relevant stable Spec scopes
   ↳ repository-native: write local Git-ignored doc/goals/<branch>.spec.md
→ implement / verify in coherent task-sized commits
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
→ successful finalization removes branch, approval, landing transaction, Goal recovery file, repository-native Goal Spec when present, and Session cache
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

Persist durable authority according to the selected Project model. Repository-native Goal Specs are intentionally transient authority. Persist only irreducible operational intent. Cache pointers. Load context by need. Compute mechanical repository facts instead of caching them in prose/session state.
