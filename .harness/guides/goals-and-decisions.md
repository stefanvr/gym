# Goals and Decisions

Universal Harness guidance for goal formation and decision sequencing under [Guides](definition.md).

Always uncover or understand the goal, including its **edge**: what done is, in one sentence.

A goal without an edge can only be abandoned, not finished.

**Say what a person can do that they could not before, and notice when the answer is nothing.**

A goal that only moves the platform is sometimes right, but being next in a dependency chain is not the same as being worth doing. Technical ordering can pass for a plan for a surprisingly long time. Name which one it is.

A goal never carries an unmade technology or architecture decision.

When such a choice must be made, that decision becomes the goal in front of the dependent goal and is proven by the smallest thing that genuinely exercises the choice.

Otherwise the decision gets made mid-feature, under delivery pressure, by whoever needed it first.

Do not build, and do not specify, further than the goal in front of you needs.

A rule written three goals early is written from a worse understanding, and a specification is an expensive place to be wrong: its identifiers become cited by code and tests.

## Goal scrutiny

When a skill needs to establish or evaluate a goal, scrutinize:

| Check | Question |
|---|---|
| Outcome | What changes when this goal is complete? |
| Edge | What does done mean, in one sentence? |
| User capability | What can a person do afterward that they could not do before? If nothing, say `none`. |
| Kind | Is this a user outcome, platform outcome, or decision goal? |
| Decisions | Is any required technology or architecture decision still unmade? |
| Boundary | Are we building or specifying anything the current goal does not require? |

If these cannot be established, clarify, split, reject, or place another goal before the candidate.

Goal scrutiny is a guide operation, not a skill.
