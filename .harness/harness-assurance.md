# Harness Assurance

Authoritative policy for assessing whether the Harness has current evidence for the guarantees it claims inside a named supported operating profile. Read this together with [Harness Limitations](harness-limitations.md).

Harness Assurance assesses the **Harness**, not the quality, grade, production readiness, architecture, security, or completeness of a Project managed by it. Project quality remains defined by that Project's own authority, informed by the universal Guides.

## Check vs assure

The runtime exposes two deliberately different gates:

- `python .harness/runtime/harness.py check` is a **deterministic internal-consistency gate**. It validates mechanically decidable Harness structure, routing, universal Guide registration, constitutional invariant coverage, semantic-surface configuration, and other structural guarantees. Model evidence may be absent or stale without making the Harness structurally incoherent.
- `python .harness/runtime/harness.py assure --profile "provider/model/profile"` is the **profile-qualified assurance gate**. It runs/collects the deterministic verification required by this policy and requires current passing semantic evidence for the named model/profile before it can report GREEN.

A passing `check` is necessary but not sufficient for GREEN Harness Assurance.

### Evidence distribution policy

**The Harness distribution intentionally does not bundle a generic current real-model evidence set.** Semantic evidence is a claim about one exact provider/model/profile against one exact constitutional evaluator request digest and scenario-suite digest. Shipping a precomputed generic GREEN baseline would invite evidence inheritance across profiles or Harness revisions that were never actually evaluated. Therefore a fresh installation or materially changed constitutional evaluator input is expected to report **UNKNOWN** for `assure --profile ...` until current passing evidence is generated for the exact profile being claimed. This is a deliberate assurance design choice, not missing release content.

## Assurance principle

**GREEN means the claimed Harness guarantees for the named supported profile have current evidence and no unresolved blocking defect.** It does not mean every Project produced with the Harness is production-ready, nor that the Harness is an adversarial security boundary or that every future provider/model behavior is proven.

An assurance result is always qualified twice:

- by the **model profile** named with `--profile provider/model/profile`; and
- by the **operating profile** of the Collaboration model selected in `.harness/composition/active.json`, as defined under [Supported operating profiles](#supported-operating-profiles).

A result for one operating profile is never inherited by another. Changing the selected Collaboration model changes the operating profile being assessed and, because active.json is part of the constitutional evaluator input, also makes earlier semantic evidence stale. `harness.py check` requires this document to define an operating profile for every supported Collaboration model, and `assure` reports which operating profile it assessed.

The untouched standalone distribution has no selected Collaboration operating profile yet. In that explicit bootstrap state, `assure --profile ...` reports **UNKNOWN** with no operating-profile claim; bootstrap must select a supported Collaboration model before GREEN can be possible. A malformed or unsupported composition remains an error rather than an unconfigured Assurance state.

## Status model

Use these statuses:

- **GREEN** — current evidence supports the Harness guarantees claimed for the named profile. Open items are explicit restrictions or improvement/evidence debt that do not invalidate those guarantees.
- **AMBER** — usable with material operational restrictions, supervision, or remediation before the named Harness guarantees should be claimed.
- **RED** — an unresolved defect violates a claimed Harness guarantee or makes the named profile materially unsafe/unreliable.
- **OUT OF SCOPE** — the requested operating profile requires behavior explicitly excluded by `harness-limitations.md`.
- **UNKNOWN** — required evidence could not be obtained or is stale. Missing required evidence is not silently promoted to GREEN.

## Finding disposition

After evidence collection, classify each material observation into exactly one assurance disposition:

1. **Blocking defect** — occurs inside the named supported profile and violates a claimed Harness guarantee. Blocks GREEN.
2. **Accepted operating restriction** — an explicit boundary of the supported profile that is concrete, understood, and does not contradict a guarantee claimed for that same profile.
3. **Improvement / evidence debt** — hardening, maintainability, simplification, automation, or additional evidence that improves confidence but is not itself a currently violated guarantee. Missing *required* evidence still produces UNKNOWN.
4. **Outside supported model** — belongs to an operating profile explicitly excluded by `harness-limitations.md`.

Do not erase a Sanity finding by assigning an assurance disposition. Sanity determines whether evidenced Harness execution/interpretation would go differently; Assurance determines whether that finding blocks a Harness guarantee for a named profile.

## Anti-gaming rule

A defect cannot be reclassified as a limitation, operating restriction, Project concern, or evidence debt merely to obtain GREEN. A broader profile that removes a containing assumption must be reassessed rather than inheriting the narrower profile's status.

Likewise, Project quality concerns do not become Harness defects merely because the Harness manages the Project. The Harness is defective when it fails to preserve, route, propagate, or verify the Project authority that should govern those concerns.

## Supported operating profiles

Both operating profiles share these base conditions:

- lifecycle mutations executed through the Deterministic Runtime, which serializes them per workspace with OS advisory locks including across linked worktrees;
- cooperative delegated subagents that do not independently mutate Harness lifecycle state;
- one standalone supported Git repository root per workspace;
- external programs/hooks/remotes remain trusted for side effects, but runtime subprocess execution is noninteractive and bounded;
- repository/hosting/deployment security supplied by their own controls rather than by Harness approval refs;
- trusted, cooperative actors as defined by [Harness Limitations](harness-limitations.md).

### Operating profile: `single-user`

Applies when active.json selects the [Single-user](collaboration-models/single-user.md) Collaboration model:

- one human developer;
- one main/orchestrating trusted AI/LLM lifecycle operator;
- landing performed from that operator's workspace.

### Operating profile: `cooperative-multi-user`

Applies when active.json selects the [Cooperative Multi-user](collaboration-models/cooperative-multi-user.md) Collaboration model:

- multiple trusted human contributors, each working through a main/orchestrating trusted AI/LLM lifecycle operator in its own workspace/clone, on independent exclusive Goal branches;
- contributor workspaces configured with the `contributor` role; exactly **one** workspace configured with the `integration-authority` role, which is the only workspace that accepts handoffs and runs landing mechanics;
- Goal transfer only through runtime `handoff publish` / `accept` / `release` / `withdraw`; no actor mutates the handoff ref, the published Goal branch, or approval refs directly;
- one configured shared remote supporting atomic pushes and force-with-lease (standard Git hosting does);
- conflicts between Goals resolved by humans through the `LANDING_BLOCKED` → release → withdraw/reconcile/re-approve → republish path.

For either operating profile, Harness Assurance may report **GREEN** only when the required evidence below passes and no additional blocking defect is found.

## Assurance guarantees

The current maturity contract includes:

| Area | Guarantee |
| --- | --- |
| Harness vs Project | Harness governance/universal judgment and contextual Project authority remain separate jurisdictions. |
| Universal Guides | Guides remain Harness-owned universal judgment; explicit same-concern Project authority may specialize them without rewriting them. |
| Authority | Concern ownership is resolved before precedence; one rule has one authoritative source; evidence/implementation cannot manufacture authority. |
| Change propagation | Material authority changes cause affected dependent conclusions to be reconsidered through their existing owners. |
| Semantic regression | Constitutional invariants are machine-indexed and required behavioral coverage is complete. |
| Evidence freshness | Real-model constitutional evidence is bound to the exact serialized evaluator request sequence and scenario suite it evaluated. |
| Structural gate | `harness.py check` mechanically verifies all mechanically decidable parts of the maturity contract. |
| Cooperative integration (`cooperative-multi-user` only) | Only the integration-authority workspace runs landing mechanics; published handoffs are immutable; acceptance and withdrawal of one handoff are mutually exclusive at the remote; stale, moved, or uncertain handoffs fail closed as `LANDING_BLOCKED`; exact-tree approval is never extended across moved mainline. |

## Remaining known restrictions and debt

| ID | Observation | Disposition | Containment / profile impact |
| --- | --- | --- | --- |
| `R-001` | Destructive/error coverage is substantial but not exhaustive. | Improvement / evidence debt | Deterministic CI plus targeted destructive/restart tests and semantic behavior scenarios are required. Coverage percentage alone is not a Harness invariant. |
| `R-002` | The runtime cannot prevent two workspaces from each being configured with the `integration-authority` role. | Accepted operating restriction (`cooperative-multi-user`) | Exactly one integration-authority workspace is part of the operating profile. The runtime refuses to let a second integration actor take over an existing acceptance, and each landing still revalidates exact remote mainline/branch boundaries, but role uniqueness itself is an operating contract, not an enforced lock. |

## Constitutional semantic invariants

`.harness/harness/invariants.json` is the machine-readable index of stable constitutional invariant IDs. It is an index, not a second prose authority: each entry points to the document that owns the rule.

Behavior scenarios declare the invariant IDs they exercise. `harness.py check` must reject missing, duplicate, unknown, or uncovered required invariant IDs.

**[SEM-01]** Real-model constitutional behavior evidence is valid only for the exact evaluator request sequence and behavior scenario suite it evaluated. The evaluator deterministically serializes the same request object it sends to the runner for every scenario and hashes that ordered byte sequence as `evaluation_input_digest`; evidence also records the suite digest. When either digest changes, older evidence is stale and must not be inherited as current Assurance evidence.

This is deliberately **constitutional Assurance (Option A)**: the evaluator supplies only its declared constitutional authority set, not every file in the broader model-facing semantic surface. `.harness/evals/behavior/semantic-surface.json` remains a governance/change-impact inventory and must not be represented as the set a particular behavior run evaluated. The deterministic checker can report evidence freshness but cannot manufacture a real-model run. Response captures used for replay must themselves be bound to the evaluation-input digest, scenario-suite digest, and model profile they saw before a replay may mint current Harness Assurance evidence; an unbound or stale replay cannot be restamped as current merely because its answers still pass.

## Profile matrix

| Operating profile | Assurance baseline |
| --- | --- |
| `single-user` operating profile with current required evidence | **GREEN** |
| `cooperative-multi-user` operating profile with current required evidence | **GREEN** |
| Either profile running approved lifecycle commands unattended with respect to terminal prompts | **GREEN** for Harness-owned blocking behavior; external program side effects remain governed by `harness-limitations.md` |
| Multiple independent lifecycle operators landing from separate workspaces, or more than one `integration-authority` workspace | **OUT OF SCOPE** |
| Actors directly mutating Git refs/state outside the runtime while Harness lifecycle commands run | **OUT OF SCOPE** |
| Multi-user/adversarial authorization or cryptographic approver identity | **OUT OF SCOPE** |
| Nested/submodule/multi-repository transaction orchestration | **OUT OF SCOPE** |

The matrix is a baseline, not a substitute for current evidence. A new blocking defect changes the result even if this table has not yet been edited.

## Evidence required for GREEN Harness Assurance

For either operating profile, collect at least:

- `python .harness/runtime/harness.py check` with zero structural findings;
- Python compilation/import evidence for the runtime and behavior evaluator;
- the runtime regression suite, including subprocess timeout/noninteractive tests, lifecycle-lock contention/worktree tests, and the cooperative handoff tests (including racing accept/withdraw);
- `python -m unittest discover -s .harness/evals/behavior/tests -v`;
- `python .harness/evals/behavior/run.py --validate-only`;
- current real-model constitutional behavioral evidence for **each model/profile being claimed**, with all scenarios passing and evidence bound to the current evaluation-input and scenario-suite digests;
- semantic Sanity Harness Check when Assurance is performed through the agent workflow;
- any additional targeted evidence required by a newly discovered material finding.

`harness assure --profile ...` executes the deterministic verification it can own and checks the retained semantic evidence for that exact profile. It cannot hide a blocking defect discovered outside the command; the anti-gaming rule still applies.

The bundled GitHub Actions workflow is the deterministic gate. It deliberately does not call an external LLM or require provider secrets. CI GREEN plus `--validate-only` is **not** evidence that a changed constitutional evaluator contract passed a real LLM behavioral run.

## Assurance report shape

When Harness Assurance is requested, report at minimum:

1. **Profile** — the exact model profile and the operating profile (selected Collaboration model) assessed.
2. **Overall status** — GREEN, AMBER, RED, OUT OF SCOPE, or UNKNOWN.
3. **Evidence** — checks/tests/inspection actually performed, including the constitutional evaluation-input digest, semantic-surface change-impact digest, and missing/stale model evidence when applicable.
4. **Blocking defects** — unresolved items that prevent GREEN.
5. **Operating restrictions / debt** — applicable known items and containment.
6. **Project boundary** — explicitly state that the result does not grade the Project being managed.

A conforming GREEN headline is:

> **GREEN — Harness guarantees assured for the `<collaboration-model>` operating profile under `<provider/model/profile>`.**

`harness assure` emits this headline with the selected Collaboration model filled in.

## Ownership

`harness-limitations.md` owns the supported trust/execution boundary. Each Collaboration model definition owns its collaboration semantics. This document owns the operating-profile definitions used for assurance and Harness assurance status/disposition/evidence semantics. Sanity Harness Check owns discovery and evidence-backed consistency findings. Harness Change owns edits to Harness authority. The Deterministic Runtime owns mechanically decidable repository facts/transitions, `check`, and the executable portion of `assure`; it does not decide Project quality.
