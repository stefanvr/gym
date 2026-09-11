# Harness Workflows

Human visualization only. These diagrams are not execution authority: where a diagram and the document that owns the flow disagree, the owning document wins.

Harness Change owns the requirement to keep these diagrams synchronized. This file mirrors that requirement: update the relevant diagram in the same change whenever harness development alters a lifecycle, routing flow, capability skill set, or orchestration order.

As required by Harness Change, read the diagrams before concluding that none of them is affected. A diagram encodes relationships that are easy to forget are drawn here at all, so an argument from memory that nothing covers the change is not evidence. Check each diagram against the change, and name the ones checked when reporting that they needed none.

# Workflow

The lifecycle runs under whatever `project_model` + `collaboration_model` `.harness/composition/active.json` selects (the distribution's default selection is `spec` + `cooperative-multi-user`); active method packs assist authority work but do not change Project authority. The collaboration layer adds an immutable handoff/integration boundary rather than forking Goal or landing semantics.

## Cooperative multi-user handoff

```text
contributor Goal branch
    │
    ▼
verify + exact approval
    │
    ▼
immutable handoff publish ── remote Goal branch + handoff ref
    │
    ▼
integration authority accept ── acceptance commit replaces handoff at its ref (CAS)
    │
    ▼
land assess
    │
    ├─ current mainline == handoff base ─→ prepare / merge / publish
    │
    └─ mainline moved ─→ LANDING_BLOCKED
                          │
                          ▼
              release → contributor withdraw/reconcile/re-check/re-approve/republish
```

## Core lifecycle

```text
owner request
    │
    ▼
Goal scrutiny ──→ one bounded outcome + edge
    │
    ▼
Git established? ── no ──→ Branch Start bootstrap → runtime repo bootstrap
    │ yes
    ▼
Branch Start create
    │
    ▼
one exclusive Goal branch
    │
    ▼
Goal writes local ignored recovery file
  doc/goals/<branch>.md
    │
    ▼
resolve affected stable Spec scope(s)
    │
    ▼
load selected scopes + transitive dependencies
  consider reverse dependents for Change Impact
    │
    ▼
load only relevant guides/skills
    │
    ▼
work in coherent task-sized commits
    │
    ▼
owning checks + meaningful intermediate validation only when needed
    │
    ├─ no durable outcome ──→ Branch Land abandon
    │                         │
    │                         ├─ no-op proven ─────────────┐
    │                         └─ explicit discard authority│
    │                                                      ▼
    │                         runtime abandon discard --mode ...
    │                                                      │
    │                                                      ▼
    │                                      local Goal/Session state removed
    │
    ▼
Goal complete
    │
    ▼
Branch Land check
    │
    ▼
explicit landing authorization
    │
    ▼
runtime approval record
  refs/harness/landing-approval/<branch>
    │
    ▼
prepare history while preserving approved full tree
    │
    ▼
runtime land prepare
  pins exact ready commit + exact mainline base
    │
    ▼
runtime land merge
  revalidate → build candidate off-mainline → exact mainline update → push exact receipt
                                                             │
                                                             ├─ push fails → recoverable merged transaction; Goal/Session remain
                                                             └─ push succeeds → finalize
                                                                                 │
                                                                                 ▼
                                                              branch/approval/runtime state removed
                                                              local Goal/Session state removed
```

### Goal is the only delivery layer

```text
Goal = one bounded outcome
  │
  ├─ one exclusive work branch
  ├─ one local recovery file: doc/goals/<branch>.md
  ├─ zero or more transient execution tasks
  ├─ task-sized commits
  └─ one final landing authorization
```

Release, milestone, epic, initiative, or similar grouping can exist in Project tooling, but it is not a Harness lifecycle object.

### Goal recovery state

`doc/goals/<branch>.md` is local and Git-ignored.

```text
current branch
      ↓
derive doc/goals/<branch>.md
      ↓
read intended outcome
      ↓
runtime resume for exact Git/approval/transaction facts
      ↓
inspect relevant specs + branch history/diff
      ↓
determine what remains
```

The file contains outcome/meaningful constraints, not status, task logs, or approval. It is never committed, pushed, or archived. Successful runtime landing/abandonment removes it. Failed landing recovery leaves it intact.

Before a landing boundary is prepared, the runtime requires live remote mainline to match local mainline when that remote ref exists and requires any existing remote Goal branch to match the local ready commit. The same alignment is rechecked before mainline integration.

### Landing recovery

```text
landing transaction exists
    │
    ├─ ready + approval/mainline/branch boundary changed
    │       └─ land abort → semantic re-check → fresh approval if needed → land prepare
    │
    └─ integration started / local integration completed
            └─ runtime resume → land merge --branch <branch> → continue exact recovery/publication/finalization
```

Old authority never silently extends to a changed mainline or changed Goal outcome.

## Specification flow

```text
bounded Project concern
        ↓
clear single authority? ── no / cross-authority ──→ Design method (when useful/active)
        │ yes                                      │
        │                                          └─ delegates; owns no Project truth
        ↓
┌────────────┬────────────┬────────────┬────────────┐
↓            ↓            ↓            ↓
Domain       App          Style        Tech
orchestrator orchestrator orchestrator orchestrator
│            │            │            │
├─ active    ├─ active    ├─ active    ├─ active methods where useful
│  methods   │  methods   │  methods   │
└─ owning    └─ owning    └─ owning    └─ owning skills
   skills       skills       skills       skills
        │            │            │            │
        └──────── accepted conclusions become authority ────────┘
                              ↓
                         owning checks
```

Interview Me may support any authority when owner intent is missing. Event Storming feeds Domain; Story Mapping feeds App. Method working state never becomes authority by completion alone. Style Preview demonstrates Style decisions; its check is a sibling of Style Check, not a step inside it.

## Specification check orchestration

```text
spec-check
    ├─ tech-check
    ├─ domain-check
    ├─ app-check
    ├─ style-check
    └─ style-preview check
```

Spec Check invokes each specification's own check rather than duplicating its scrutiny.

# Actual work

## Brainstorm exploration loop

Brainstorm remains a non-authoritative exploration surface. When Interview Me is active, use it for reusable general owner-intent elicitation; Brainstorm Analyze handles supplied-material analysis.

```text
                 ┌──────────── analyze material ────────────┐
                 │                                          ↓
start → understand current question → enough direction?
                 ↑                              │
                 │                              ├─ yes → record / route
                 │                              │
                 │                              └─ no
                 │                                  ↓
                 └──── interview ←──────── need evidence or intent?
                                                    │
                                                    └─ no
                                                        ↓
                                                     stuck?
                                                        │
                                                        ↓ yes
                                                     ideate
                                                        │
                                                        └→ discuss / analyze / route
```

## Domain refinement loop

```text
broad / unclear Domain concern
   ↓
Domain orchestrator
   ├─ Event Storming when useful/active → working model only
   └─ narrow concern → direct owning skill
   ↓
language / events / rules / data
   ↓
accepted authority edits exercise the terms
   ↓
term or model proves wrong?
   │
   ├─ no → continue
   └─ yes
        ↓
     revise language/data/rules/events
        ↓
     re-check consumers
```

A term is settled when it survives the activities that use it, not merely when first named.

## App refinement loop

```text
broad / unclear App concern
    ↓
App orchestrator
    ├─ Story Mapping when useful/active → working map only
    └─ narrow concern → direct owning skill
    ↓
App Story Map (authoritative structure)
    ↓
interaction
    ↓
needs somewhere to happen
    ↓
surfaces
    ↓
surface changes interaction constraints
    ↓
interaction revision
    ↓
app-check
```

## Style preview loop

```text
Style decision
      ↓
Style Preview update
      ↓
inspect
      ↓
Style wrong?
  │          │
 yes         no
  ↓           ↓
refine      complete
  ↓
Preview update
```

## Tech / Proof operational routing

```text
bounded technology decision
        ↓
material uncertainty?
   │             │
   no           yes
   │             ↓
   │       Knowledge Lookup where relevant
   │             ↓
   │         Build Proof
   │             ↓
   │       exercise smallest real path
   │             ↓
   │       route proof findings
   │        ├─ decision evidence / project architecture → Tech
   │        ├─ development setup fact → Setup Dev
   │        ├─ runtime / deployment fact → Setup App
   │        ├─ reusable technology finding → Knowledge
   │        └─ machine-specific anomaly → Setup / optional environment note
   │             ↓
   └────────→ Tech Decide
                 ↓
          decision + required approval
```

Build Proof owns the executable/operational evidence and finding routes; Tech owns the decision.

## Build routing loop

```text
code change requested
      ↓
classify
  │       │       │
  │       │       └─ existing code wrong → Build Repair
  │       └─ technical uncertainty → Build Proof → decision owner
  └─ product behavior → owning spec exists?
                         │
                         ├─ yes → Build Implement
                         └─ no  → route to owning capability
```

## Correction loop

```text
new information
     ↓
what changed?
     │
     ├─ execution was wrong
     │      ↓
     │   correct work
     │      ↓
     │   commit freely
     │      ↓
     │   apply Git History correction rule before landing
     │
     └─ intended requirement changed
            ↓
          brain
            ↓
       re-evaluate goal / task
            ↓
       preserve change in history
```

## Setup loop

```text
fresh environment
      ↓
Setup Dev / Setup App
      ↓
automatable step?
   │          │
  yes        no
   ↓          ↓
execute    mark manual boundary
              ↓
         owner performs step
              ↓
verify actual resulting state
      ↓
setup complete
```

Manual boundaries follow Workflow; Setup skills record and verify the resulting state.

## Learning / Dream loop

```text
reusable experience recognized during work
    ↓
Dream `propose` immediately while evidence is fresh
    ↓
Grill / evidence scrutiny
    ↓
user disposition?
  │          │          │
reject      defer      accept
  ↓          ↓           ↓
Dream       conversational /   route to existing owner
`close`     persist only if        ↓
            context/evidence      owning skill + normal lifecycle
            would be lost           ↓
              ↓                  durable owner takeover
         `doc/dreams/` may          ↓
          survive landing        Dream `close`
                                  ↓
                               authority
                                  ↓
                           future execution

cleanup boundary reached
    ↓
already-identified unresolved proposal would be lost?
  │                              │
 no                             yes
  ↓                              ↓
continue silently          surface for accept / reject / defer
                           or persist enough evidence for later review
                           (do not search for new candidates)
```

Dream output remains non-authoritative until the user explicitly accepts the proposal and the existing owning skill applies it. `doc/dreams/` is persisted Learning state, not branch-local temporary state, so an unresolved retained proposal may survive landing. Dream `close` removes rejected/resolved proposals and accepted proposals after durable owner takeover. Landing is only a loss-prevention safety net for already-identified proposals, never an automatic Dream trigger.

# Harness

## Sanity loop

```text
Sanity Run
   ├─ spec-check
   ├─ trace-check
   ├─ repository-check
   └─ trigger-driven Setup / Knowledge checks
      as defined by `skills/sanity/run.md`
          ↓
      evidence-backed findings
          ↓
      route by owner
          ↓
      owning skill fixes
          ↓
      re-run relevant check
```

Sanity owns orchestration and findings, not fixes.

## Authority change propagation

```text
authority owner changes meaning
          ↓
Change Impact
          ↓
identify materially dependent conclusions
          ↓
route each to its existing owner
          ↓
re-establish only affected checks / decisions / evidence
          ↓
dependent completion / approval may continue
```

Affected does not mean automatically wrong. It means the old conclusion is not inherited without reconsideration where the changed authority could matter. No global dirty-state database is required.

## Harness maintenance loop

```text
harness finding
      ↓
does the fix change what the harness decides?
  │       │
  │       └─ yes → owner approves → Harness Change `design`
  └─ no ────────────────────────→ Harness Change `repair`
                                         ↓
                                 re-run Harness Check
```

Sanity Harness Check discovers; Harness Change edits. Neither does the other's work.

## Harness Assurance reporting

```text
Harness Assurance request
          ↓
Sanity Harness Check + current evidence
          ↓
load Limitations + Assurance
          ↓
name Harness operating profile
          ↓
verify structural + semantic coverage
          ↓
classify model evidence as current / stale / absent
          ↓
classify observations
  ├─ blocking defect ───────────→ AMBER / RED
  ├─ accepted restriction ─────→ visible, may remain GREEN
  ├─ improvement/evidence debt → visible, may remain GREEN
  └─ unsupported requirement ──→ OUT OF SCOPE for that profile
          ↓
profile-qualified Harness Assurance result
          ↓
explicitly not a grade of the managed Project
```

An Assurance disposition never erases a Sanity finding. The Assurance anti-gaming rule controls whether an open item may coexist with GREEN.

# Session

## Session restart loop

```text
new / cleared session
        ↓
load context manifest + every current `always` entry
        ↓
runtime `resume`
   │                 │
   │ Git uninitialized
   │                 ↓
   │          record uninitialized fact
   │                 ↓
   │          classify candidate work
   │                 ↓
   │          Branch Start bootstrap when needed
   │
   └─ Git exists → consume runtime Git/ref/transaction facts
                         ↓
                   transaction present?
                    │           │
                    no         yes
                    │           ├─ active landing → Branch Land
                    │           ├─ abandonment → Branch Land
                    │           └─ stale / changed boundary → Branch Land recover
                    ↓
if on a Goal branch, derive/read local doc/goals/<branch>.md
        ↓
read relevant specs / Dream / session pointer only as needed
        ↓
verify pointer claims against runtime + repository + owning state
        ↓
load only additional context needed for current work
        ↓
report compact orientation
        ↓
continue requested work
```

Session Resume owns the restart procedure. Session state is cache/pointer state, never authority.

## Continuity checkpoint loop

```text
transient context would be lost
    ↓
Session Checkpoint update
    ↓
doc/session.md (cache only)
    ↓
/clear or handoff
    ↓
Session Resume verifies against authority
    ↓
Session Checkpoint clear when no longer needed
```
