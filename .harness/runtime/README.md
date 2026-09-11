# Deterministic Runtime

The runtime package owns mechanically decidable repository facts, guarded Git transitions, model-specific runtime mechanics, and deterministic Harness validation. Semantic authority remains in Workflow and the owning models/skills.

The runtime applies only to the standalone Git repository whose root contains `.harness/`. Parent/nested repositories, running the Harness as a submodule, and tracked Git submodules/gitlinks are unsupported and mechanically detectable layouts are refused.

Run:

```text
python3 .harness/runtime/harness.py <command>
```

Output is deterministic JSON. Validation commands (`check`, and `spec topology` when Project topology has findings) exit with status `1`; expected Harness refusals exit with status `2`; unexpected runtime failures are normalized to JSON on stderr and exit with status `3`.

The supported trust, lifecycle-concurrency, sandboxing, and security boundaries are documented in [Harness Limitations](../harness-limitations.md). Assurance policy is documented in [Harness Assurance](../harness-assurance.md).

## Module ownership

- `harness.py` — CLI parsing/dispatch and normalized output/errors only
- `kernel.py` — process/Git facts plus repository, approval, landing, abandonment, and recovery mechanics
- `project_model.py` — active Project-model lookup and Spec topology mechanics
- `collaboration_model.py` — active Collaboration-model lookup, actor state, and cooperative handoff mechanics
- `checker.py` — structural validation, semantic-evidence validation, `check`, and `assure`

The kernel may consult Collaboration-model state only through its explicit landing integration seam. It does not implement handoff commands. Project-model and Collaboration-model modules use kernel repository primitives but do not own generic landing semantics. `check` validates this ownership split.

## Runtime requirements

The runtime requires **Python 3.10 or newer** and **Git 2.28 or newer**.

### Bounded noninteractive execution

Every external command launched by the runtime is noninteractive and bounded. Standard input is disconnected, Git terminal prompting and Git Credential Manager interaction are disabled, and commands time out after 120 seconds by default. `HARNESS_COMMAND_TIMEOUT_SECONDS` may raise the limit to at most 3600 seconds.

On POSIX systems commands run in their own process group so timeout handling can terminate descendants such as hooks. A timeout refuses the mechanical transition; it does not claim to reverse external side effects already produced by another program.

### Lifecycle mutation serialization

Runtime-owned lifecycle mutations use non-blocking OS advisory locks. Initialized repositories use a lock under the Git common directory so linked worktrees share one mutation boundary. Read-only commands such as `repo status`, `approval validate`, `resume`, `check`, and `assure` remain available during a mutation lock.

Direct Git/ref/state edits outside the runtime can bypass these guards and remain outside the supported cooperative operating model.

## Repository configuration

`.harness/runtime/config.json` defines only repository mechanics that genuinely vary:

- `mainline`: explicit branch name or `auto`
- `bootstrap_mainline`: branch name used for a new repository
- `remote`: configured Git remote name used to publish mainline and, when explicitly requested, delete a work branch remotely

`auto` resolves the remote default branch when available, then common local mainline names. Ambiguity requires explicit configuration. When `mainline` is explicit, `bootstrap_mainline` must be identical.

Landing shape is intentionally fixed:

- an exact one-commit Goal branch directly extending the prepared base fast-forwards;
- every other Goal branch lands with one merge commit.

This is Harness policy rather than repository configuration.

## Commands

### Repository and branch

- `repo status`
- `repo bootstrap [--seed-path <path> ... | --all-seed-files]`
- `branch start --name <branch> [--base <branch>]`

Bootstrap defaults to an empty baseline. Pre-staged content is refused unless whole-tree seed staging is explicitly selected.

### Landing approval

There is one approval namespace:

```text
refs/harness/landing-approval/<branch>
```

Commands:

- `approval record [--branch <branch>]`
- `approval validate [--branch <branch>]`
- `approval drop [--branch <branch>]`

These commands implement mechanics only. Branch Land owns the semantics of asking for, accepting, and withdrawing landing authorization.

`approval record` requires a clean tree, an existing named work branch, and a non-empty local `doc/goals/<branch>.md` Goal recovery file. The Goal file is Git-ignored and does not alter the approved branch tree.

An existing approval ref cannot be moved in place. If authority changes, drop it after the appropriate semantic decision and record fresh approval. If history is rewritten while the full tree remains identical, the original approval remains valid because `approval validate` and landing preparation compare the approved tree to the current branch tree.

Dropping approval first preflights every dependent landing transaction. A `ready` transaction is removed. An `integrating` transaction is also removed when configured mainline still equals its prepared base, because the candidate has not crossed the irreversible mainline boundary. If mainline already equals that candidate, or the transaction is `merged`/`published`, receipt/recovery state is preserved so deterministic recovery can finish. If an integrating transaction finds mainline at neither the prepared base nor candidate, withdrawal fails before the approval ref is changed.


### Cooperative multi-user handoff

When the selected Collaboration model is `cooperative-multi-user`, repository transport is used as a narrow coordination channel between trusted workspaces; it is not a distributed lock or security system. Each workspace records local actor/role metadata under the Git common directory:

```text
collaboration configure --actor <name> --role contributor|integration-authority
collaboration status
```

Contributors develop independent exclusive Goal branches and may publish one immutable approved handoff:

```text
handoff publish [--branch <branch>] [--approved-by <actor>]
handoff withdraw --branch <branch>
```

The configured integration-authority workspace serializes landing:

```text
handoff accept --branch <branch>
land assess --branch <branch>
land prepare --branch <branch>
land merge --branch <branch>
handoff release --branch <branch>
```

A published handoff binds the exact ready commit, approved tree/source commit, contributor mainline base, Goal recovery text digest, and provenance metadata. It is represented by `refs/harness/handoff/<branch>` plus the exclusive remote Goal branch. Publication is create-only: an atomic push with empty-lease guards requires both refs to be absent, so two racing publications cannot both claim the branch.

Acceptance is recorded **on the same ref**: the integration authority replaces the exact handoff commit at `refs/harness/handoff/<branch>` with an acceptance commit (`acceptance.json`: branch, handoff commit, integration actor, release) whose only parent is the handoff commit. The push is a compare-and-swap leased on the handoff commit, and contributor withdrawal is an atomic deletion leased on that same handoff commit, so exactly one of a racing accept/withdraw pair succeeds and the loser changes nothing. The published handoff content is unchanged and remains exactly recoverable as the acceptance commit's parent. Acceptance then reconstructs the branch/approval/Goal recovery boundary locally; before the compare-and-swap, local branch, approval, ignore, and Goal-file conflicts are preflighted so an ordinary workspace conflict cannot transfer ownership prematurely. An acceptance already recorded by the same integration actor is treated as an interrupted acceptance and resumed idempotently; one recorded by a different integration actor is refused.

After acceptance, the contributor cannot withdraw the handoff. The integration authority either consumes it through landing or explicitly releases it; release compare-and-swaps the handoff ref back from the acceptance commit to the exact handoff commit and is retry-safe after interruption. Accepted branch/approval/Goal state is one transferred unit: approval cannot be dropped and the branch cannot be abandoned independently before release.

`land assess` is fail-closed. If configured mainline no longer equals the contributor's handoff base, or the exact accepted handoff ref / remote-branch boundary moved, it reports `LANDING_BLOCKED` with evidence. The runtime does not auto-rebase, infer semantic compatibility, or extend exact-tree approval across that change. Human coordination releases the handoff; the contributor withdraws, reconciles against current mainline, re-checks/re-approves as needed, and republishes.

Successful cooperative landing atomically exact-deletes the accepted handoff ref and handed-off remote Goal branch during finalization. Crash recovery after the recorded candidate crosses mainline remains transaction-driven so remote coordination state is not required to manufacture or reinterpret authorization.

### Resume

`resume` reports repository/mainline/current-branch facts, the derived Goal path/existence flag, current/all landing approvals, and active landing transactions.

Session Resume uses these facts rather than manually reconstructing refs or transaction phases.

### Landing

The landing transaction is the same exact-tree mechanism in both Collaboration models. Under `single-user`, the authorized Goal branch can proceed directly. Under `cooperative-multi-user`, only the configured integration-authority may prepare/merge, and the Goal must first cross the accepted immutable handoff boundary.

The normal transaction is:

1. Branch Land obtains explicit authorization for the exact Goal outcome.
2. `approval record` anchors the approved commit/tree.
3. Branch Land may clean/rewrite the exclusive work-branch history while preserving that approved full tree.
4. `land prepare` requires the current branch tree to equal the approved tree, requires the local Goal file, and confirms live remote alignment: remote mainline must equal local mainline when it exists, and an existing remote Goal branch must equal the local ready commit.
5. `land prepare` records the exact ready branch commit plus exact current mainline base.
6. After preparation the work branch must not move.
7. `land merge` revalidates live approval, ready branch, unchanged mainline, and live remote alignment immediately before integration.
8. The landing candidate is built in a disposable detached worktree. A one-commit branch directly extending the base fast-forwards; otherwise one merge commit is created.
9. The candidate tree must equal the prepared Goal branch tree.
10. Mainline is moved by exact compare-and-swap only after the candidate is complete and revalidated.
11. The exact resulting mainline receipt is pushed to configured remote mainline before destructive finalization.
12. Successful finalization deletes the work branch, approval, runtime transaction state, local Goal file, and local Session cache.

Commands:

- `land prepare [--branch <branch>]`
- `land merge [--branch <branch>] [--message <message>] [--delete-remote]`
- `land abort [--branch <branch>]`

`land abort` is allowed only while the transaction remains `ready`. An explicit approval withdrawal may safely cancel an `integrating` transaction only while mainline is still exactly the prepared base. Once the candidate has crossed mainline, use `land merge --branch <branch>` to resume the recorded transaction. This preserves restart safety across a process interruption immediately before or after the atomic mainline ref update.

Push failure after local integration leaves the transaction in a recoverable `merged` state and preserves the Goal file and work branch. A later `land merge --branch <branch>` retries publication/finalization from the recorded exact receipt.

### Branch abandonment

Abandonment is one guarded operation:

```text
abandon discard --target <branch> --mode no-op|explicit [--delete-remote]
```

Before invoking it, Branch Land establishes either mechanically provable no-op status or explicit user discard authority for unique work. Attributable dirty work being destroyed is safety-committed first.

For `no-op`, the runtime requires the target tree to equal its merge-base tree with configured mainline. For `explicit`, the runtime uses the current exact target commit as the deletion boundary. Remote deletion is never implicit; when requested, it first verifies the remote branch still equals that exact commit and uses force-with-lease deletion.

Successful discard removes the local Goal file, local Session cache, any landing approval, and any still-local landing preparation for that branch.

Durable information that must survive cancellation must be made durable through its normal Project owner before discard.

## Local operational state

`doc/goals/<branch>.md` and `doc/session.md` are Git-ignored local recovery state. They are never Project history and are never committed or pushed as files. Under the cooperative model, a published handoff carries a copy of the Goal recovery text inside its runtime handoff commit on `refs/harness/handoff/<branch>`, outside Project history; landing finalization and withdrawal remove that ref.

Landing transaction metadata lives under the local Git common directory and `refs/harness/runtime/land/...`. Accepted cooperative handoff recovery metadata likewise lives under the Git common directory, while published/accepted handoff refs are remote coordination state. None of these are semantic authority or Project truth.

Active landing transactions use an exact runtime transaction schema. Unsupported transaction-state schemas are rejected rather than interpreted or migrated implicitly.

## Spec topology inspection

When the active Project model is `spec`, read-only Project-model commands expose the modular authority topology without folding Project grade into Harness Assurance:

```text
python3 .harness/runtime/harness.py spec topology
python3 .harness/runtime/harness.py spec affected --scope <stable-scope-id> [--scope <id> ...]
```

`spec topology` validates `doc/spec/topology.json`. When the manifest is absent, topology is reported as `unconfigured`; the runtime does not infer authority from conventional file names.

`spec affected` returns selected scopes plus transitive dependencies for minimal loading, reverse dependents as Change Impact candidates, and their union for affected graph checking. It never claims that every reverse dependent requires an edit.

These commands inspect managed Project structure. `harness.py check` intentionally validates only the shipped Harness topology contract, not whether a particular Project's specifications are good.

## Harness structural check

`check` deterministically validates mechanically decidable Harness invariants, including runtime module ownership, composition/classification integrity, the Spec-topology contract, authoritative skill contract shape, wrapper mapping, agent entrypoints, context-manifest integrity, Guide registration, Routing uniqueness, constitutional invariant coverage, semantic-evidence freshness wiring, Markdown links, runtime configuration, and release verification machinery.

Semantic sanity remains the responsibility of Sanity Harness Check; executable `check` is evidence for that skill rather than a replacement for judgment.

## Harness Assurance gate

`assure --profile <provider/model/profile>` requires zero structural findings, executable runtime/evaluator test passes, a valid behavior corpus, and current passing semantic evidence for the exact named profile.

It reports GREEN only when those conditions hold. Missing/stale profile evidence reports UNKNOWN; deterministic failures report RED.

## Runtime invariants

- the runtime never invents semantic approval or Goal meaning
- one Goal branch has one landing approval namespace
- cooperative contributors use independent exclusive Goal branches; only one configured integration-authority workspace runs landing mechanics
- a cooperative handoff is immutable until withdrawal and, once accepted, is consumed or released as one transferred branch/approval/Goal unit
- acceptance and withdrawal of one handoff are compare-and-swaps on the same remote ref; at most one of them can succeed
- stale or uncertain cooperative handoffs fail closed as `LANDING_BLOCKED`; exact-tree approval is never extended across moved mainline by inference
- approval refs cannot be moved in place
- approval remains applicable across history cleanup only while the full approved tree is unchanged
- `land prepare` creates the only pre-integration landing boundary: exact approved tree + exact ready commit + exact mainline base
- the work branch must not move after `land prepare`
- configured mainline must not move between preparation and integration
- one-commit branches directly extending the base land directly; other Goal branches receive one merge commit
- landing candidates are built and validated off-mainline
- configured mainline is never rewritten by the runtime
- local landing is not finalized before exact remote publication succeeds
- Goal and Session files are local ignored recovery state and survive failed landing recovery
- branch abandonment is one guarded current-boundary operation
- remote deletion is explicit and exact-boundary
- lifecycle mutations are serialized by advisory locks
- external commands are noninteractive and bounded
- repository topology is single-root
