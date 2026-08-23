# Workflow

**Purpose.** The development routine: how a stage goes from plan to merged code, and where the
review gates are.

**What belongs here.** Anything about *process* — branching, commit granularity, review points,
merge and push order, how the docs get updated as work lands.

**What doesn't.** Anything about the product itself. Rules go in domain-spec, technical choices in
tech-spec, behavior in implementation-spec, the build order in implementation-tracking.

---

## Project-specific rules

These sit outside the generic process below because they're this project's own standing
preferences, not things every project using this doc set would share.

- **No GitHub pull requests, ever.** Branch, implement, push the branch — then merge straight into
  the integration branch locally (`git merge --ff-only <branch>`) and push that. Never open or
  suggest a PR, even though `git push` prints GitHub's "Create a pull request…" link.
- **Nothing merges without the reviewer's explicit go-ahead.** This is really just step 7 below
  taken literally rather than as a formality — the branch gets pushed and reported on, then
  work stops until sign-off arrives, even for small changes.
- **Git operations run inside real WSL, never Windows-side Git Bash** — see
  [environment.md](environment.md) for why (wrong commit author, and commit signing fails
  outright, both silently from the Windows side).
- Once merged and confirmed landed, delete the stage branch both locally and on `origin`.

> **Integration branch for this project:** `main`. It's a small solo project — every stage reaches
> `main` directly rather than through a longer-lived integration branch.

---

## Per stage

Work is organized into **stages** (see implementation-tracking.md). Each one runs the same loop.

### 1. Review the plan

Re-read the stage's own checklist and check whether it still holds up. Add, remove, or tweak
steps based on what's been learned since it was written — especially from how the previous stage
actually went. Do this **before** touching the spec or writing any code.

Answer the stage's **Try it:** line now, if it isn't already filled in — concretely, as the steps
you'd actually take.

### 2. Create the stage's branch

One branch per stage, off `main`. Keeps a stage's history reviewable as a unit, and reverting it a
single operation.

### 3. Fill in the spec, then stop

Write the implementation-spec sections the stage needs.

**Then stop and wait for explicit sign-off before writing implementation code** — unless the
reviewer has explicitly opted out for that stage ("if there are no significant questions, spec it
and start — I'll review after"), in which case: note any genuine open design questions *in the
spec text itself*, pick the sensible default for each rather than blocking, and proceed. Review
then happens against the finished result instead of the spec draft.

If the design shifts once implementation starts, update the spec section — it describes the end
state, so it must match what actually got built.

### 4. Implement, one commit per checklist step

A separate commit per checklist item, not one commit per stage. Each commit message says **why**,
not just what — the what is in the diff.

### 5. Verify before claiming done

Run the **full** test suite (`npm test && npm run test:e2e`), not just what you touched. Report
failures plainly, with the output.

**Look at anything visual.** A passing test says the code ran, not that the result is right —
screenshot it, at both the desktop and mobile viewports this project actually ships (see
tech-spec.md's testing strategy).

**Write throwaway verification for anything you're reasoning about rather than observing** — a
scratch script that runs the real functions and prints what happened, a direct check of a computed
value. Delete it in the same session (see code-conventions.md), and don't write its output into a
directory the dev server serves or watches.

### 6. Push the branch

Push the stage branch to `origin` as soon as it's complete — **before** review, and before any
merge.

### 7. Review

The reviewer reviews the finished stage. Nothing merges before this — see Project-specific rules
above.

### 8. Merge, then push `main`

`git merge --ff-only <branch>` into `main`, then push `main`. No PR, per Project-specific rules.
Delete the stage branch, locally and on `origin`, once merged and confirmed landed.

---

## Checking work off

When a stage's item is done, check it off **with a note on what actually happened** —
particularly where it diverged from the plan:

- Something that turned out to be already handled by earlier generic work: say so, and what
  confirmed it.
- Something found and fixed along the way that wasn't in the plan: add it as an `Ad hoc:` item
  rather than leaving the checklist looking like the plan was perfect.
- Something deliberately *not* done: move it to the backlog/polish stage with the reasoning,
  don't silently drop it.

---

## Deferring work honestly

When something real is found but shouldn't be fixed now, write it into the polish/backlog stage
with enough detail to act on later: what's wrong, why it was deferred, and what fixing it would
take. Anything deferred because it needs a **decision** rather than work should say which
decision, and what the options are.

---

## When a rule turns out to be wrong

Specs get things wrong. When implementation reveals that a documented rule doesn't hold up:

1. Fix the doc that owns the rule, in the same change as the code.
2. Say plainly in the commit message that it's a reversal, and why the original reasoning failed.

Watch specifically for **implementation limitations leaking into rules** — "it works this way
because that was awkward to build" is a bug in the doc, not a design decision. Write the rule the
domain actually wants, then note the gap if the implementation can't meet it yet.
