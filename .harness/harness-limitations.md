# Harness Limitations

Human operating-boundary documentation. This file describes the supported trust and execution model; it does not replace Workflow, Routing, owning skills, or Deterministic Runtime authority. Harness-evidence disposition within this boundary is defined by [Harness Assurance](harness-assurance.md); a limitation is not itself a defect, and a defect must not be relabeled as a limitation merely to obtain a GREEN result. Harness Assurance concerns Harness guarantees only; it does not grade the Project managed by the Harness.

## Supported trust and execution model

The Collaboration model selected in `.harness/composition/active.json` — [Single-user](collaboration-models/single-user.md) or [Cooperative Multi-user](collaboration-models/cooperative-multi-user.md) — owns its lifecycle-collaboration semantics (for the cooperative model: trusted contributor handoff, local actor-role guardrails, and serialized integration-authority semantics). This Limitations document owns the surrounding trust, bypass, sandbox, and security boundary for both.

The Harness assumes that the human developer and cooperating agents are trusted to follow the Harness. It is a safety mechanism for accidental, stale, or mechanically inconsistent lifecycle operations; it is not an adversarial security or identity system.

In particular:

- Harness approval refs represent workflow authority inside the Harness operating model. They are not cryptographic signatures or proof of approver identity.
- A human, agent, hook, or other process with unrestricted repository access can bypass Harness guarantees by directly modifying Git refs, branches, transaction files, the index, or other repository state. Lifecycle operations must therefore be performed through the Harness workflow and Deterministic Runtime where specified.
- Runtime-owned lifecycle mutation is mechanically serialized, including across linked Git worktrees. Which actor may initiate those mutations is selected by the active Collaboration model. Direct Git/ref/state mutation by another actor bypasses that lock and remains unsupported.
- The Deterministic Runtime does not sandbox Git hooks, project scripts, build tools, tests, or other programs executed during development. Disposable worktrees isolate repository-local landing preparation but cannot prevent programs from producing external filesystem, network, credential, service, or other side effects.
- Agent instructions and skills are semantic guidance interpreted by an LLM and therefore remain probabilistic. Deterministic guarantees apply only to repository facts and mechanical transitions explicitly enforced by the runtime.
- Extension packages are additional semantic/execution capability, not a sandbox or trust grant. The runtime can resolve their entrypoints but does not inspect arbitrary extension code for safety or execute it automatically.
- Discovery does not yet provide an automatically isolated disposable experiment workspace. Code-producing experiments use normal repository/Goal discipline unless the developer deliberately manages separate isolation outside the Harness.
- The Harness does not replace repository-hosting access controls, protected branches, CI policy, secret management or scanning, code review controls, deployment authorization, or production infrastructure security.

The cooperative multi-user model, when selected, remains trusted/cooperative. Local actor/role metadata and remote handoff acceptance records are coordination guardrails, not adversarial authorization. There is no distributed lock across independent clones; serialization depends on the explicit integration-authority operating contract. Cryptographic approval, ACL enforcement, and security isolation between mutually untrusted actors are outside the supported operating model.

Harness v18 cooperative handoffs use a schema that records the active Project model and can carry a repository-native Goal Spec. Complete, release, or withdraw pre-v18 in-flight cooperative handoffs before upgrading; v18 does not promise backward compatibility for remote handoff objects created by older major versions.

## Repository and integration boundaries

The Deterministic Runtime supports one standalone Git repository root. Parent/nested repositories, running the Harness as a submodule, and tracked submodules/gitlinks are unsupported and mechanically detectable forms are refused. See [Deterministic Runtime](runtime/README.md) for the exact repository boundary.


## Responsibility boundary

The runtime does not decide whether work is valuable, complete, semantically correct, approved by the human, safe to discard, or permitted as temporary cleanup. Those decisions remain with the owning Harness workflow/skills and the human authority. The runtime only enforces the exact mechanical facts it owns.
