# Sanity Harness Check

Checks whether the Harness itself is internally coherent and whether its constitutional guarantees remain represented by executable/semantic evidence.

## Define

Check the Harness for inconsistent terminology, duplicated authority, broken references/routing, jurisdiction or precedence conflicts, Harness/Project-boundary drift, Guide universality drift, missed change propagation, manifest/diagram drift, adapter/wrapper drift, contract violations, semantic-regression gaps, Assurance evidence freshness/validity, and semantic/runtime-boundary drift.

Use the Deterministic Runtime structural checker for mechanically decidable invariants instead of manually reimplementing them. The executable check is evidence for this skill; it does not replace semantic review.

## Checks

1. Run `python3 .harness/runtime/harness.py check`; any finding is a Harness Check finding and must be resolved before claiming structural consistency.
2. **Harness vs Project remains constitutional** — Harness operation and universal judgment remain distinct from Project-specific truth. Project authority cannot redefine Harness operation; the Harness does not manufacture Project truth.
3. **Guides remain universal** — every Guide is Harness-owned cross-project judgment under `guides/definition.md`; project-specific departures are explicit, same-concern Project authority and do not rewrite the Guide.
4. **Jurisdiction before precedence** — classify the concern and owner before applying same-subject precedence. Look for a Project document overriding Workflow/Lifecycle or a Harness rule deciding Project truth outside its jurisdiction.
5. **One term, one meaning** — working and extended Harness vocabularies are disjoint, consistent, and owned at the correct audience boundary.
6. **One rule, one authority** — policy is not duplicated authoritatively; pointers, diagrams, adapters, wrappers, manifests, and the invariant registry remain references/mirrors rather than second authorities.
7. **Ownership does not overlap silently** and **Routing closes** — every concern maps to one real owner at the declared granularity; duplicate routing rows or unresolved ownership are findings.
8. **Authority orchestration preserves ownership** — under the active Project model, broad concerns may enter an authority orchestrator, but orchestration must not create a second authority or duplicate child-skill procedures. Narrow, already-understood concerns may still route directly.
9. **Method packs remain techniques, not truth owners** — active method packs match Composition/source bindings, method definitions satisfy the Method Pack Contract, inactive methods are not silently treated as active procedures, and method working output is promoted only through the Project authority that owns the concern.
10. **Project-model topology remains structural, not authority** — when Spec is active, stable scope IDs are independent of file paths, scope prefixes match their authority, dependency closure supports scoped loading, reverse dependents are Change Impact candidates, and missing topology is reported as unconfigured rather than inferred from file layout.
11. **Change propagation closes** — when authoritative meaning changed, identify dependent conclusions that relied on the old meaning and verify affected owners re-established relevant checks/decisions/evidence. Affected conclusions are not assumed wrong, but old conclusions are not inherited without reconsideration.
12. **Semantic regression covers the constitution** — every `behavior_required` ID in `.harness/harness/invariants.json` exists at its authoritative source and is covered by at least one valid behavior scenario; coverage is by invariant, not scenario count.
13. **Semantic evidence is fresh when supplied/claimed** — behavior evidence must name the current constitutional evaluation-input digest and scenario-suite digest. The broader semantic-surface inventory remains a change-impact signal, not evidence provenance. Stale evidence is a finding when presented as current; absent live-model evidence is missing Assurance evidence when a claim requires it, not something deterministic `check` may fabricate.
14. **Workflow diagrams, Workflow, manifest, invariant index, semantic-surface config, and skill tree match reality**.
15. **Agent adapters and skill wrappers converge on shared Harness authority without forking policy**. ChatGPT/OpenAI (`AGENTS.md`), Claude Code (`CLAUDE.md` / wrappers), and Gemini (`GEMINI.md`) are entry paths to the same Workflow and this check.
16. **Contracts are intentionally followed or intentionally departed from**, including the requirement that authority-mutating skills use Change Impact rather than inventing local propagation rules.
17. **Continuity/session state remains pointers rather than authority**.
18. **Learning/Dream remains non-authoritative and promotion owner-routed**; persisted Dream state has one retention/removal owner and is not misclassified as Lifecycle temporary state.
19. **Semantic skills do not embed a second repository/ref/transaction algorithm where the Deterministic Runtime owns the mechanics.**
20. **Harness Assurance is about Harness guarantees, not Project grade** — `harness-limitations.md` defines the supported operating boundary and `harness-assurance.md` defines status/evidence/disposition semantics. Neither may be used to explain away a defect that violates a claimed Harness guarantee, and neither grades a Project's production readiness.
21. **Known restrictions remain visible** — an accepted restriction or improvement/evidence-debt item may coexist with GREEN only under the Assurance anti-gaming rule; unsupported profiles are OUT OF SCOPE rather than false failures of the supported profile.

## Inputs

Required: Deterministic Runtime `check` output plus the [Sanity Finding test](../../capabilities/sanity.md#finding-test), Workflow, Guides and [Guide definition](../../guides/definition.md), capability/support-family definitions, active Project/Collaboration models, active method-pack definitions, skills, mechanisms including [Change Impact](../../mechanisms/change-impact.md), [README Vocabulary](../../README-vocabulary.md), [Harness Extended Vocabulary](../../harness-extended-vocabulary.md), the authority-orchestrator and method-pack contracts, the active Project-model topology contract, routing/context manifest, invariant registry, semantic-surface config, behavior corpus, skill tree, workflow diagrams, agent adapters, [Harness Limitations](../../harness-limitations.md), and [Harness Assurance](../../harness-assurance.md).

## Outputs

Either `no change` or evidence-backed Harness findings routed to the document/skill that owns the inconsistency.

When Harness Assurance is requested, add a separate profile-qualified assurance assessment using `harness-assurance.md`. Do not convert Sanity findings into non-findings merely because they are accepted for a profile. Structural/semantic consistency and Assurance are related but distinct claims.

For Harness-maintenance verification, record the deterministic `harness.py check` result once and verify the supported agent entry paths still converge on the same shared authority. Differences in findings between agent entry paths are adapter/context evidence to investigate, not separate truths.

## Owns

No durable Harness state. Harness Check discovers and routes; it does not silently edit the operating model.

## Modes

### `check`

Run the complete Harness-consistency check.

## Approval

No approval to run.

Findings whose correction leaves the Harness's operating decisions unchanged route to Harness Change `repair`. A finding whose correction would change what the Harness decides is a design change for the owner: the owner approves the intended Harness design change, a bounded Goal carries it, and Harness Change `design` applies it only after that approval.

## Invariants

- executable structural evidence is required but does not replace semantic consistency review
- Harness vs Project jurisdiction remains explicit
- universal Guides remain universal without becoming Project specifications
- concern ownership is established before same-subject precedence
- authority orchestration coordinates without creating another Project truth owner
- method output remains non-authoritative until promoted by the owning Project authority
- stable Spec scope identity is independent of physical path and topology metadata does not become a fifth Project authority
- changed authority triggers Change Impact before affected dependent completion
- one term has one meaning, is defined in exactly one of the two owned vocabulary files, and one rule has one authority
- constitutional invariant coverage is complete and machine-checkable
- stale semantic evidence is never presented as current
- deterministic Git/lifecycle mechanics have one implementation in `.harness/runtime/kernel.py`; `harness.py` is CLI wiring and skills retain semantic authority
- supported agent entry paths converge on one shared Harness authority
- findings are evidenced and routed rather than silently repaired
- Assurance conclusions always name the assessed Harness operating profile and do not grade the Project

## Completion

Complete when the Harness can be read as one non-contradictory operating model across agents and session restarts, changed authority has no unaccounted dependent conclusions, constitutional semantic coverage is complete, and supplied Assurance evidence is correctly classified as current, stale, absent, or not required.
