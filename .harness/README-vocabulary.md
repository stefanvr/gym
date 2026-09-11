# Working Vocabulary

Shared terms for normal Project work with the Harness. This glossary is intentionally small: procedure-local names belong in the Guide, skill, model, or runtime document that owns them.

For terms needed only while developing, validating, recovering, or assuring the Harness itself, see [Harness Extended Vocabulary](harness-extended-vocabulary.md). A term is defined in one glossary only.

Harness Change owns both vocabulary files as Harness authority. Project documents may use these terms but do not redefine Harness operation.

| Term | Meaning |
|---|---|
| **Harness** | The operating system for governing work: Workflow, Routing, Lifecycle, contracts, Guides, skills, deterministic repository mechanics, adapters, and Harness Assurance. It does not own contextual Project truth. |
| **Project** | The product/system/repository work managed by the Harness. Project intent and owned specifications/decisions may be authority; implementation, tests, and repository state are evidence/state unless an owning rule says otherwise. |
| **Guide** | Harness-owned universal judgment intended to remain useful across substantially different Projects. Project-specific same-concern authority may explicitly specialize or depart from it. |
| **Skill** | A bounded, independently invokable unit of work with defined ownership, actions, and invariants. |
| **Capability** | A family of related skills with a shared purpose and artifact boundary. |
| **Authority orchestrator** | A Project-authority capability that receives a broad concern in its own jurisdiction, selects useful methods/skills, and preserves one authoritative source. |
| **Method pack** | An optional composition-selected technique for eliciting, modelling, structuring, analysing, or coordinating work. Method output is working material, not authority by implication. |
| **Project model** | The composition dimension that defines where contextual Project authority lives and how it is routed. Exactly one supported model is active. |
| **Collaboration model** | The independent composition dimension that defines how trusted contributors coordinate Goal/lifecycle work. It does not redefine Project truth ownership. |
| **Spec scope** | Under the Spec Project model, a stable authority unit identified independently of its physical file path. |
| **Goal** | One bounded outcome with a clear edge; the Harness delivery unit. One Goal owns one work branch and one landing unit. |
| **Goal edge** | The condition that makes a Goal finishable. |
| **User capability** | What a person can do after a Goal is complete that they could not do before; it may explicitly be `none`. |
| **Decision** | A choice that constrains later implementation or design. |
| **Open decision** | A choice not yet made, recorded by the authority that owns it when knowing it is open matters to later work. |
| **Proof** | The smallest implementation or experiment that genuinely exercises a decision. |
| **Task** | A coherent piece of work contributing to a Goal. Tasks are execution decomposition, not a separate lifecycle layer. |
| **Checkpoint** | A deliberate validation boundary before dependent work proceeds. It is transient unless an owner requires durable state. |
| **Approval** | Explicit user acceptance at a meaningful boundary. Final landing authorization is the mandatory Goal-level approval before a Goal branch enters mainline. |
| **Land** | Enter configured mainline as durable Project history. |
| **Landing** | The guarded process that turns an authorized Goal branch into configured-mainline history and publishes the exact landing receipt before final cleanup. |
| **Mainline** | The repository branch configured or unambiguously discovered as the durable integration line. |
| **Work branch** | The exclusive Git branch for exactly one Goal and one landing unit. |
| **Task-sized commit** | A commit containing one coherent step toward a Goal. |
| **Correction** | Work fixing execution while the intended requirement remains unchanged. |
| **Requirement change** | New information that changes what the intended work means. |
| **Fold** | Git-history operation governed by the [Git History guide](guides/git-history.md). |
| **Branch operator** | The one human owner of a work branch together with that person's orchestrating agent/subagents and their own manual edits. Another human uses another branch. |
| **Abandon** | Explicit lifecycle transition that discards a Goal branch without pretending it completed. |
| **Landing approval** | Explicit authorization for one exact Goal-branch outcome to enter configured mainline, mechanically anchored at `refs/harness/landing-approval/<branch>`. |
| **Brainstorm** | Non-authoritative exploration used to surface observations, possibilities, constraints, tensions, or questions before owned truth is settled. |
| **Scrutiny** | Applying governing judgment to decide whether something is sufficiently understood and bounded to proceed. |
| **Check** | Evidence-based comparison between intended and observed state. |
| **Goal document** | Local Git-ignored `doc/goals/<branch>.md` containing only recoverable Goal outcome/meaningful constraints. It is not Project history. |
| **Authorship stance** | Collaboration posture for an activity: owner-led, harness-proposed, or already-settled. |
| **Owner-led** | The owner carries the relevant intent; the Harness extracts, structures, and scrutinizes it. |
| **Harness-proposed** | The Harness proposes where material is thin; the owner corrects or accepts where the decision is theirs. |
| **Already-settled** | Authoritative input already establishes the answer; apply it with scrutiny instead of re-interviewing. |
| **Unknown** | Something not yet understood or evidenced. |
| **Sanity** | Orchestration capability that discovers consistency/drift findings without owning the fixes. |
| **Dream** | Learning skill that turns reusable experience into a pressure-tested proposal for an existing owner. |
| **Handoff** | The immutable remote coordination record for one approved Goal branch in Cooperative Multi-user mode. |
| **Integration authority** | The one serialized integration workspace/role in Cooperative Multi-user mode. It accepts/releases handoffs and is the only role permitted to prepare or execute landing transactions. |
| **LANDING_BLOCKED** | Fail-closed result meaning an accepted Goal cannot land under its current approved boundary without human resolution. |
