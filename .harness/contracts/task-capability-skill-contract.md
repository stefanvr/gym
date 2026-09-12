# Task / Capability Skill Contract

Defines the minimum structure for skills used to perform goal work.

A capability may contain one or more skills.

A skill should represent one independently invokable kind of work.

## Required core

Every skill explicitly answers these eight questions, even when the answer is `none` or `no durable state`:

- Define
- Inputs
- Outputs
- Owns
- Modes
- Completion
- Approval
- Invariants

`Owns`, `Modes`, and `Invariants` must never be omitted merely because the answer seems obvious. Explicit absence is part of the contract: for example, a check skill can state that it owns no durable state, and a single-operation skill can state that it has no separate modes.

`Started`, `Method`, `Scrutiny`, `Commit behavior`, and `Dependencies` are added when they materially improve routing or execution. Do not manufacture them for symmetry.

## 1. Define

State the outcome the skill produces.

Answer:

- what does this skill do?
- what does it not do?
- when is it the right skill to invoke?

Prefer outcome language over process language.

## 2. Inputs

List the inputs the skill may consume.

Examples:

- current goal
- existing specification
- source material
- repository state
- user instruction
- prior decisions
- outputs from other skills

Separate:

- required inputs
- optional inputs
- discovered inputs

Do not require information the skill can safely discover itself.

## 3. Outputs

State what durable result the skill produces.

Possible outputs include:

- decision
- specification
- model
- preview
- code
- tests
- documentation
- structured findings

Distinguish:

- durable output
- temporary reasoning
- user-facing preview

When a skill changes authoritative meaning rather than merely repairing representation, it must apply the shared Change Impact mechanism before dependent completion: identify materially affected dependent conclusions, route them to their existing owners, and re-establish the relevant checks. Do not duplicate that mechanism locally.

## 4. Owns

Define which state or files the skill may modify.

A skill should have narrow ownership.

If the skill produces no durable state, say so explicitly.

Do not let several skills silently own the same artifact.

## 5. Started

Describe the forms of input that commonly trigger the skill.

Examples:

- raw material
- an existing artifact needing refinement
- a correction
- a goal requiring this capability
- discovered uncertainty
- a missing decision

This section describes entry conditions, not execution steps.

## 6. Modes

Expose only independently useful operations.

Common modes may include:

### `brain`

Understand, reconcile, challenge, or reshape the input before producing durable work.

Use only when the skill genuinely benefits from an explicit reasoning mode.

### `create`

Produce the first durable version.

### `refine`

Improve an existing artifact without changing its intended outcome.

### `check`

Compare the result against its goal, invariants, or observed system state.

### `preview`

Produce something the user can meaningfully inspect before dependent work continues.

### `decide`

Resolve a bounded choice.

### `apply`

Apply an already-understood decision or specification.

A skill does not need all modes.

Do not add modes merely for structural symmetry.

## 7. Method

Describe the smallest stable procedure required to perform the skill well.

This is where SPR-level procedural knowledge may live.

Prefer:

- decision rules
- ordered checks
- heuristics
- failure signals

Avoid:

- long tutorials
- generic background knowledge
- process steps that belong to another skill
- a second prose implementation of deterministic repository/ref/transaction mechanics when the harness runtime already exposes the required command

If the procedure becomes reusable across several skills, extract it into a shared mechanism or guide.

## 8. Scrutiny

State the questions that determine whether the output is good enough to proceed.

Scrutiny should derive from guides where possible rather than inventing local philosophy.

## 9. Completion

Define what makes the skill's work complete.

Completion must be observable.

Avoid definitions such as:

- "looks good"
- "fully considered"
- "best practice followed"

Prefer conditions that can actually be checked.

## 10. Approval

State whether the output needs user validation before dependent work proceeds.

Possible policies:

- no approval expected
- approval only when a meaningful ambiguity remains
- preview required
- explicit user approval required

Intermediate approval should remain exceptional.

The preferred path is for work to accumulate toward the Goal landing boundary.

## 11. Commit behavior

State how the skill's work maps to Git history.

Specify:

- whether it normally creates a task-sized commit
- whether several outputs belong in one commit
- what counts as a correction
- what counts as a requirement change

Follow the Git History guide for the authoritative distinction between execution corrections and requirement changes; do not restate that rule in the skill contract.

## 12. Dependencies / Routing

List other skills or artifacts this skill may require or produce input for.

Prefer explicit directional relationships.

Do not create dependencies solely because one technique traditionally follows another.

## 13. Invariants

List the few rules that must always remain true while using the skill.

Keep invariants short and enforceable.

Typical examples:

- changed authoritative meaning triggers Change Impact before dependent completion
- never work beyond the current goal
- never hide an unresolved decision
- never modify artifacts outside ownership
- never require approval without a meaningful validation boundary
- never duplicate another skill's source of truth

---

# Classification test

Before creating a skill, ask what the candidate actually is.

| Candidate | Classification |
|---|---|
| Cross-cutting principle for making judgments | **Guide** |
| Independently invokable unit of work | **Skill** |
| Broad family of related skills; may also be its Project authority orchestrator when the selected Project model says so | **Capability** |
| Optional reusable discovery/design technique that owns no Project truth | **Method pack** |
| Reusable behavior inside multiple skills | **Mechanism** |
| Compact procedural knowledge for doing one skill well | **SPR** |
| Temporary exploration or notes | **Working state** |
| Durable description of the product/system | **Artifact** |

---

# Skill size test

A skill is probably too large when:

- it produces several unrelated kinds of durable output
- parts of it are useful independently
- it owns several unrelated artifacts
- its modes have little shared state
- users would reasonably invoke only one subsection
- different parts have different completion criteria

A skill is probably too small when:

- it cannot produce a meaningful outcome independently
- it exists only as one mechanical step of another skill
- it has no distinct completion condition
- separating it adds routing overhead without improving clarity

---

# Capability contract

A capability is lighter than a skill and contains no detailed execution procedure.

Every capability explicitly defines these six boundaries:

- Purpose
- Owns
- Skills
- Shared guides and mechanisms
- Dependencies
- Invariants

`Shared guides and mechanisms` and `Dependencies` may explicitly say `none beyond shared workflow` when that is genuinely true. Do not omit the boundary merely because the answer seems obvious.

`Owns` defines artifact/state boundaries for the family. Individual skills narrow that ownership; they do not silently broaden it.

Capabilities may include additional explanatory sections when they materially clarify routing or shared behavior. Under a Project model that designates a capability as an authority-owning orchestrator, its orchestration follows `.harness/contracts/authority-orchestrator-contract.md`; this adds coordination responsibility without adding a second artifact or broadening the capability's authority.

## Support families

Discovery, Personal Notes, Learning, Knowledge, Continuity, Lifecycle, and Harness are **support families**, not capabilities. They are deliberately shaped lighter than this contract requires, because none of them owns a product artifact — the boundary the capability contract exists to police.

Their definitions live at:

- `.harness/discovery/definition.md`
- `.harness/notes/definition.md`
- `.harness/learning/definition.md`
- `.harness/knowledge/definition.md`
- `.harness/continuity/definition.md`
- `.harness/lifecycle/definition.md`
- `.harness/harness/definition.md`

Each states only the boundaries that constrain something real for it, and none is held to the six capability boundaries.

These seven are the recorded departures from the capability contract. A family that owns a product artifact is a capability and follows the contract in full.

A support family still declares its skills and its ownership boundary. Skills within one follow the skill contract unchanged: the lighter shape is the family's, never the skill's.

---

# Minimal skill template

```md
# <Skill>

## Define
<outcome and boundary>

## Inputs
<required inputs>

## Outputs
<durable result>

## Owns
<state/files>

## Modes
<named operations>

## Completion
<observable done condition>

## Approval
<when user validation is required>

## Invariants
<rules that must remain true>
```

Add Method, Scrutiny, Commit behavior, and Dependencies only when they materially help.
