# Git History

Universal Harness guidance for meaningful development history under [Guides](definition.md). Project-specific repository policy may specialize it only through the Project authority that owns that concern.

Git history should describe the work that was intended and landed, not every correction made while reaching it.

Each Goal branch provides the boundary for one coherent landing.

One Goal owns one exclusive branch and one landing unit.

## Branch before work

Start development work on an exclusive Goal branch before implementing a new Goal.

Do not place another Goal on that branch. Tasks within the Goal remain on the same branch.

## Commit at task size

Commit coherent task-sized work.

A commit should represent one meaningful implementation step that builds cleanly on the commits before it.

Commit freely while working.

Intermediate correctness is less important than preserving enough structure to rewrite the branch accurately before landing.

## Corrections fold

**The branch is rewritten before it lands so its commits describe the work, not its corrections.**

A correction to an error made while implementing an already-understood task belongs to that task's commit.

Examples:

- fixing a bug introduced by the task
- correcting an implementation mistake
- adding something accidentally omitted
- fixing tests broken by the implementation
- correcting naming or structure that should have been right originally

Fold those changes into the commit they belong to.

A corrective commit can be useful while working without deserving a permanent place in history.

## Requirement changes stay visible

Work caused by a new instruction, correction to the requirement, elaboration, or additional information that arrived after the original task is **not** folded into the original task.

That work represents a change in what was understood or required.

Keep it visible in history.

> Correcting the implementation rewrites history.  
> Correcting the requirement preserves history.

The history should reveal when the intended work moved.

This distinction also applies outside Git: the harness should distinguish learning that its **execution was wrong** from learning that its **understanding of the requested outcome changed**.

## Rewriting commits

When changes are folded into an earlier commit:

- rewrite the affected commit
- reconsider its commit message
- update the message when the resulting commit means something different

A rewritten commit message describes the commit that remains, not its earlier incomplete state.

## Nothing to fold

A branch with nothing to fold is this rule succeeding.

Report explicitly whether:

- `history rewritten`
- `nothing to fold`

Do not leave these cases indistinguishable.

## Work branch ownership

A work branch has one branch operator: one human owner together with the orchestrating agent, that agent's subagents, and manual edits made by that same human.

Another human, directly or through another agent, must work on a different branch. Do not create a shared-branch fallback mode.

Because a work branch is exclusive to one operator boundary, Branch Land may rewrite its pre-landing history after landing approval while preserving the approved full tree. `land prepare` ends the rewrite window by pinning the exact ready commit and mainline base. Configured mainline remains the non-rewritable boundary.

## Single-commit landing

When the prepared Goal branch contains exactly one commit directly beyond its prepared mainline base, that commit is already the smallest coherent landing boundary. The Deterministic Runtime fast-forwards it without manufacturing a merge commit.

Every other prepared Goal branch receives one merge commit using the Goal/landing message. The rule is evaluated after history preparation, so provisional corrective commits do not force a permanent merge boundary when they have been folded into one coherent final commit.

## Mainline

Never rewrite configured mainline. Its concrete branch name is repository configuration/discovery, not a universal harness constant.

Do not retroactively rewrite mainline to manufacture landing evidence. A prepared one-commit Goal branch lands directly; every other Goal branch is represented by one merge commit.
