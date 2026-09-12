# Software Development Harness v18
## Feature & mechanism overview

Harness is a repository-local operating system for AI-assisted software work. It does not try to replace the developer, the repository, or the coding agent. It gives them a small shared structure for deciding **what should be true**, proving **what became true**, and moving one bounded change safely through Git.

The design is intentionally split: semantic work stays with the agent and human; mechanically decidable repository work is enforced by deterministic runtime code.

---

## 1. The Harness in one view

```text
                    HARNESS KERNEL
             Goal / Git / landing / checks
                         │
                         ▼
                PROJECT REASONING
       Domain / App / Style / Tech / methods
                         │
                         ▼
                 PROJECT MODEL
              ┌──────────┴──────────┐
              │                     │
            spec             repository-native
              │                     │
       persistent scopes       transient Goal Spec
              │                     │
              └──────────┬──────────┘
                         ▼
                        Build
                         │
                         ▼
                      evidence
```

The **kernel** stays the same regardless of how a project stores its truth. Domain, App, Style, and Tech reasoning are shared. The selected **Project model** decides where accepted project decisions live.

This makes the Harness usable for both projects that want a durable structured specification and projects that want to keep their existing repository conventions intact.

---

## 2. Composition: two independent choices + optional methods

A configured Harness selects one Project model and one Collaboration model. Methods are additive techniques, not authority.

| Dimension | Choices | What it decides |
|---|---|---|
| **Project model** | `spec` / `repository-native` | Where project-specific intended truth lives |
| **Collaboration model** | `single-user` / `cooperative-multi-user` | How trusted contributors coordinate lifecycle work |
| **Method packs** | Interview Me, Event Storming, Story Mapping, Design, etc. | How uncertainty can be explored and resolved |

These dimensions do not redefine each other. For example, repository-native can be used in either single-user or cooperative mode.

### Spec mode

```text
Goal
 ↓
Domain / App / Style / Tech reasoning
 ↓
stable Harness Spec scopes
 ↓
Build + verification
```

Project authority is durable and explicitly structured. Stable scope identities and dependency topology support focused loading, impact analysis, and cross-scope checking. Stable scopes record concise durable conclusions; working analysis, alternatives, and conversation history stay outside Spec authority unless the owner explicitly asks to retain them or they are required to apply the conclusion correctly.

### Repository-native mode

```text
Goal
 ↓
targeted repository understanding
 ↓
Domain / App / Style / Tech reasoning as needed
 ↓
transient Goal Spec
 ↓
Build + verification
 ↓
Goal Spec disappears after landing
```

The repository keeps its existing documentation, ADRs, schemas, conventions, tests, and code organization. The Goal Spec temporarily owns the **intended delta** for one Goal.

Repository-native is deliberately **not code-as-spec**. Existing code and tests are evidence of current behavior; they do not automatically decide desired behavior.

---

## 3. Three layers + Dream

The Harness can also be read as three operating layers, with Dream sitting beside them as a learning loop.

```text
┌─────────────────────────────────────────────────────────┐
│  1. PROJECT DEFINITION                                  │
│  Goal · Domain · App · Style · Tech · Methods · Grill   │
│  Decide what should be true.                            │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  2. VERIFY                                              │
│  owning checks · Build Check · Sanity · approval        │
│  Prove what is true and expose drift.                   │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  3. ENVIRONMENT                                         │
│  Guides · Setup · Knowledge · Continuity · Lifecycle    │
│  Deterministic Runtime                                  │
│  Make good work repeatable and recoverable.             │
└─────────────────────────────────────────────────────────┘

                  DREAM ───────────────► proposal
                    ▲                       │
                    └──── real experience ─┘
                         never self-promotes
```

### Project definition

The Goal bounds one delivery outcome. Domain, App, Style, and Tech supply different reasoning jurisdictions. Methods such as Event Storming or Story Mapping help discover answers but do not become authority themselves.

The key rule is **jurisdiction first**: determine which concern owns a decision before deciding precedence or editing artifacts.

### Verify

Evidence supports a claim; it does not manufacture authority. Checks verify their own concerns, Build checks executable behavior, and Sanity looks for cross-cutting drift. Explicit approval remains a lifecycle boundary of its own.

### Environment

Guides provide universal engineering judgment. Setup and Knowledge preserve repeatability. Continuity reconstructs state from Git + Goal + project truth rather than conversation memory. Lifecycle and the deterministic runtime keep branch and landing mechanics coherent.

### Dream

Dream converts reusable experience into a proposal while the evidence is still fresh. It is deliberately non-authoritative:

```text
experience → Dream proposal → pressure test → user accepts? → owning authority
```

A Dream can survive a Goal, but it cannot silently rewrite the Harness or the Project.

---

## 4. Discovery, personal notes, and Extensions

The Goal rails stay strict. Freedom lives **before** the point where something becomes work.

```text
                 NON-AUTHORITATIVE SPACE

 personal notes        Discovery question
(local, never auto-read)      │
                              ▼
                 Brainstorm / methods / Grill
                       + explicit Extensions
                              │
                 ┌────────────┼─────────────┐
                 │            │             │
               close       publish       promote
                 │            │             │
              nothing    Project state      ▼
                         through owner      Goal
```

**Discovery** is question-driven and transient by default. It may inspect the repository or Spec, compare options, use active methods, or exercise an Extension. It is allowed to finish with no Goal and no retained artifact. If something is worth keeping, the owner explicitly publishes it through an existing Project authority/documentation owner; if it becomes actionable work, one bounded outcome is promoted to Goal. There is no Discovery backlog.

**Personal Notes** are deliberately weaker: a Git-ignored `doc/notes.md` for local todos/ideas. They are not Project state, are never loaded automatically, and acquire no priority merely by existing.

**Extensions** allow useful skills that do not belong in universal Harness core. Project Extensions are committed under `.harness/extensions/project/<id>/`; local Extensions are ignored under `.harness/extensions/local/<id>/`. An Extension may be mature and project-specific or newly evaluated and local—the scope is about ownership/distribution, not maturity. Extensions add capability, never authority, and cannot silently override core skills.

The deterministic runtime can list/resolve Extension entrypoints, but it never executes them or accepts their conclusions automatically.

---

## 5. Goal is the delivery unit

Harness work is organized around one bounded Goal rather than a long-lived agent task list.

```text
Goal
  ↓
one exclusive branch
  ↓
Project definition becomes implementation-ready
  ↓
work / task-sized commits
  ↓
verify + leave evidence
  ↓
explicit landing authorization
  ↓
deterministic prepare / integrate / publish
  ↓
cleanup
```

A Goal can be a documentation correction, a refactor, a UI change, or a technical proof of concept. The size changes; the lifecycle does not.

The Goal itself is local recovery state, not project history. Git carries implementation history. Project authority carries durable intended truth where the selected model requires it.

### Implementation should not silently specify

Before consequential implementation, the relevant Project authority must be sufficiently decided.

In repository-native mode the practical completion rule is:

> The Goal Spec is ready when implementation can begin without accidentally making a consequential product, domain, style, or technology decision inside the code.

If implementation discovers a missing decision, work routes back through Project reasoning before continuing.

---

## 6. Semantic judgment vs deterministic mechanics

One of the central Harness mechanisms is the deliberate split between probabilistic model work and mechanically enforceable repository work.

```text
              SEMANTIC SIDE
       human + coding agent + skills

 goal understanding        project reasoning
 routing                    design decisions
 semantic checks            impact judgment
 evidence interpretation    approval request
              │
              │ guarded boundary
              ▼
           DETERMINISTIC SIDE
        .harness/runtime/*

 Git/ref facts              branch ownership
 clean-tree checks          approval bindings
 locks                      transaction anchors
 remote alignment           guarded landing
 recovery                   final cleanup
```

### Semantic side

The model is expected to reason about meaning: what the user wants, which authority owns a concern, whether a rule is satisfied, what evidence means, and whether a repository-native Goal Spec is implementation-ready.

This work is inherently semantic and remains probabilistic.

### Deterministic side

The runtime handles facts that should not depend on interpretation: exact commits and trees, refs, branch boundaries, locks, approval bindings, remote alignment, transaction state, landing recovery, and cleanup.

The runtime does **not** decide whether the feature is good, whether the user should approve it, or whether two product changes are semantically compatible.

The design principle is simple:

> Use model judgment where meaning is unavoidable; use deterministic code wherever the fact can be computed.

---

## 7. Authority, methods, implementation, and evidence stay separate

The Harness avoids a common failure mode in agentic development: everything gradually becoming “the source of truth.”

```text
working material / method output
            │
            ▼
      accepted conclusion
            │
            ▼
     owning Project authority
            │
            ▼
       implementation
            │
            ▼
          evidence
```

Only the owning authority decides intended Project truth. Conversation memory, code, tests, generated evidence, method boards, and temporary analysis do not become authority merely by existing.

This gives the Harness a strong **one concern, one owner** property while still allowing cross-authority methods such as Design to coordinate work.

---

## 8. Continuity without conversation memory

The Harness assumes an agent session may disappear.

Context is therefore reconstructed from durable or intentionally local state:

```text
Git + active branch
      +
Goal recovery text
      +
selected Project authority
      +
runtime transaction/ref facts
      ↓
reconstructed working context
```

Under repository-native mode, the transient Goal Spec joins that reconstruction while the Goal is active. Successful landing or abandonment removes Goal-local recovery artifacts.

This keeps conversation history useful but non-authoritative.

---

## 9. Collaboration without changing Project truth

Collaboration is a separate architectural dimension.

### Single-user

One human authority works through one main/orchestrating agent. Subagents can perform bounded work, but lifecycle mutation remains serialized through the main operator and runtime.

### Cooperative multi-user

Independent contributors use independent Goal branches. Approved work crosses an immutable handoff boundary to one integration-authority workspace.

```text
contributor Goal branch
        ↓
exact approved handoff
        ↓
integration authority
        ↓
revalidate against current mainline
        ↓
land or block for human resolution
```

This is intentionally cooperative coordination, not a distributed security or consensus system. If mainline moves, old approval is not silently stretched across the new boundary.

---

## 10. Deterministic check vs semantic Assurance

Harness distinguishes structural correctness from model-behavior evidence.

| Gate | Nature | Answers |
|---|---|---|
| `check` | deterministic | Is this Harness installation internally coherent? |
| `assure --profile …` | deterministic + semantic evidence | Does the exact named model/profile currently have evidence for the Harness guarantees? |

A green deterministic check cannot prove that an LLM will follow semantic rules. Conversely, semantic evaluation should not be used to test facts the runtime can enforce directly.

Semantic Assurance is profile-specific. Evidence is bound to the exact model/profile, evaluator input, and behavior-suite version rather than shipped as a generic permanent GREEN badge.

---

## 11. What v18 deliberately does not provide yet

The architecture is intentionally narrower than a full development platform.

- **External-only Harness installation:** not yet supported in v18. The Harness remains vendored inside the repository under `.harness/`; separating `HARNESS_HOME` from `PROJECT_ROOT` is future work.
- **Uniform agent validation:** adapters exist for Claude Code, ChatGPT/OpenAI, and Gemini, but validation depth is not yet equivalent. Current confidence is strongest around the Claude-oriented test-driven path; broader real-work validation for ChatGPT/OpenAI is identified work, and Gemini should not be treated as equivalently proven merely because an adapter exists.
- **Adversarial security:** approvals, actor names, and cooperative roles are workflow guardrails, not cryptographic identity, ACLs, or protection from a process with unrestricted repository access.
- **Distributed concurrent landing:** cooperative mode intentionally uses one integration authority rather than a distributed lock or automatic semantic merge system.
- **Nested Git/submodule topologies:** v18 targets one standalone repository root rather than parent/nested repositories or tracked gitlinks.
- **Disposable experiment workspaces:** Discovery can reason, spec, and use Extensions today, but automatically managed disposable worktrees for code-producing experiments remain future work.

These are operating boundaries, not hidden capabilities.

---

## The compact mental model

If only a few ideas are retained, they are these:

```text
ONE GOAL
one branch · one bounded outcome · one landing unit

ONE OWNER
route the concern before deciding or editing

TWO KINDS OF EXECUTION
semantic judgment by human/agent
mechanical facts by deterministic runtime

TWO PROJECT AUTHORITY SHAPES
spec              → durable structured truth
repository-native → transient Goal Spec + native repository truth

THREE LAYERS
Project Definition → Verify → Environment

DISCOVERY
uncertain question → transient investigation → close / publish / promote

EXTENSIONS
additional skills → capability only; authority stays where it already lives

DREAM
experience may become a proposal; proposals never promote themselves

EVIDENCE ≠ AUTHORITY ≠ APPROVAL
all three matter, and none substitutes for the others
```

That is the core of Harness v18: **a small governance kernel around AI-assisted repository work, with explicit authority, recoverable Goals, semantic reasoning where needed, and deterministic mechanics where possible.**
