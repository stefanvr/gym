#!/usr/bin/env python3
"""Universal deterministic runtime kernel.

Owns lifecycle command orchestration, approval/landing policy, and guarded mutations.
Low-level process, Git, repository, locking, and persisted-state mechanics live in
`runtime_support.py`; Project- and Collaboration-model mechanics remain separate.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

from runtime_support import (
    RUNTIME_ROOT,
    VERSION_PATH,
    CONFIG_SCHEMA_VERSION,
    TRANSACTION_SCHEMA_VERSION,
    PROJECT_ROOT,
    CONFIG_PATH,
    CONFIG_KEYS,
    MAIN_SHADOW_BRANCH,
    DEFAULT_COMMAND_TIMEOUT_SECONDS,
    MAX_COMMAND_TIMEOUT_SECONDS,
    MUTATING_COMMANDS,
    HarnessError,
    fail,
    harness_version,
    load_config,
    command_timeout_seconds,
    run,
    git,
    git_input,
    discover_git_root,
    validate_repository_topology,
    require_repo,
    git_dir,
    git_common_dir,
    project_lifecycle_lock_path,
    repository_lifecycle_lock_path,
    advisory_lock,
    mutation_command_key,
    command_mutates_lifecycle,
    lifecycle_mutation_lock,
    current_branch,
    has_commits,
    ref_exists,
    rev,
    tree,
    commit_count,
    blob,
    file_at,
    worktree_status,
    require_clean,
    branch_ref,
    require_valid_branch_name,
    goal_document_path,
    goal_document_file,
    require_goal_document,
    delete_session_document,
    delete_goal_document,
    resolve_mainline,
    resolve_bootstrap_mainline,
    configure_main_shadow,
    preflight_main_shadow_bootstrap,
    atomic_json,
    key_for_branch,
    validate_land_state,
    land_state_dir,
    land_state_path,
    read_land_state,
    write_land_state,
    delete_land_state,
    update_ref,
    land_runtime_ref,
    delete_land_runtime_refs,
    list_refs,
    is_ancestor,
    configured_remote_names,
    require_configured_remote,
    remote_head,
    remote_ref_oid,
    remote_ref_oids,
    delete_remote_refs_exact,
    require_remote_landing_alignment,
    delete_remote_exact,
)

def _project_model():
    """Load Project-model mechanics only at the lifecycle integration seam."""
    import project_model
    return project_model


def _collaboration():
    """Load Collaboration-model mechanics only at the lifecycle integration seam."""
    import collaboration_model
    return collaboration_model

def cmd_land_assess(args: argparse.Namespace) -> dict[str, Any]:
    repo = require_repo()
    config = load_config()
    branch = args.branch or current_branch(repo)
    if not branch:
        fail("land assess requires a branch")
    branch = require_valid_branch_name(branch, "land --branch" if args.branch is not None else "current branch")
    mainline = resolve_mainline(repo, config)
    current_mainline = rev(repo, branch_ref(mainline))
    if _collaboration().active_collaboration_model(PROJECT_ROOT) != "cooperative-multi-user":
        valid = cmd_approval_validate(argparse.Namespace(branch=branch))
        return {
            "result": "READY_FOR_LANDING" if valid.get("valid") else "LANDING_BLOCKED",
            "collaboration_model": "single-user",
            "branch": branch,
            "mainline": mainline,
            "current_mainline": current_mainline,
            "approval": valid,
        }
    actor = _collaboration().require_integration_authority(repo)
    assert actor is not None
    state = _collaboration().read_handoff_state(repo, branch, required=False)
    if state is None:
        return {
            "result": "LANDING_BLOCKED",
            "cause": "Goal branch has not been accepted through the cooperative handoff boundary",
            "evidence": {"branch": branch, "current_mainline": current_mainline},
            "next": ["accept a published contributor handoff", "or abandon/supersede intentionally"],
        }
    metadata = _collaboration().validate_handoff_metadata(branch, state["metadata"])
    remote = str(config.get("remote", "origin"))
    refs = remote_ref_oids(repo, remote, [_collaboration().handoff_ref(branch), f"refs/heads/{branch}"])
    live = {
        "handoff_ref": refs[_collaboration().handoff_ref(branch)],
        "branch": refs[f"refs/heads/{branch}"],
    }
    expected = {
        "handoff_ref": state["acceptance_commit"],
        "branch": metadata["ready_commit"],
    }
    if live != expected:
        return {
            "result": "LANDING_BLOCKED",
            "cause": "accepted handoff no longer matches the exact remote coordination boundary",
            "evidence": {"branch": branch, "expected_remote": expected, "live_remote": live},
            "next": ["integration authority releases the local handoff if safe", "coordinate with the publishing contributor"],
        }
    if current_mainline != metadata["handoff_base"]:
        return {
            "result": "LANDING_BLOCKED",
            "cause": "configured mainline moved after the contributor's approved handoff base",
            "evidence": {
                "branch": branch,
                "handoff_base": metadata["handoff_base"],
                "current_mainline": current_mainline,
                "ready_commit": metadata["ready_commit"],
                "contributor_actor": metadata["contributor_actor"],
                "approval_actor": metadata.get("approval_actor"),
                "integration_actor": actor["actor"],
            },
            "next": [
                "integration authority releases the handoff",
                "publishing contributor withdraws it, reconciles with current mainline, re-checks/re-approves as required, and republishes",
                "or a human intentionally supersedes/abandons the Goal",
            ],
        }
    return {
        "result": "READY_FOR_LANDING",
        "branch": branch,
        "mainline": mainline,
        "handoff_commit": state["handoff_commit"],
        "acceptance_commit": state["acceptance_commit"],
        "handoff_base": metadata["handoff_base"],
        "ready_commit": metadata["ready_commit"],
        "contributor_actor": metadata["contributor_actor"],
        "approval_actor": metadata.get("approval_actor"),
        "integration_actor": actor["actor"],
    }


def publish_landed_mainline(repo: Path, data: dict[str, Any]) -> dict[str, Any]:
    """Publish an already-integrated local landing before destructive finalization.

    The landing receipt itself is the push source, so retrying a transaction never
    pushes unrelated mainline commits that may have appeared after integration.
    A remote that already contains the receipt is accepted as already published.
    """
    branch = data["branch"]
    mainline = data["mainline"]
    receipt = data.get("merge_commit")
    if not receipt:
        fail("merged landing transaction has no recorded merge receipt to publish")
    if not ref_exists(repo, branch_ref(mainline)):
        fail(f"configured mainline branch no longer exists: {mainline}")
    if not is_ancestor(repo, receipt, rev(repo, branch_ref(mainline))):
        fail("recorded landing merge receipt is no longer reachable from configured mainline")

    remote = str(load_config().get("remote", "origin"))
    require_configured_remote(repo, remote)
    remote_commit = remote_head(repo, remote, mainline)
    if remote_commit == receipt:
        pass
    else:
        remote_ref = land_runtime_ref(branch, "remote-mainline")
        try:
            if remote_commit is not None:
                cp = git(
                    ["fetch", "--no-tags", remote, f"refs/heads/{mainline}:{remote_ref}"],
                    repo,
                    check=False,
                )
                if cp.returncode != 0:
                    fail(
                        f"cannot inspect remote {remote}/{mainline} before landing publication: "
                        f"{cp.stderr.strip() or cp.stdout.strip()}"
                    )
                fetched = rev(repo, remote_ref)
                if is_ancestor(repo, receipt, fetched):
                    data["phase"] = "published"
                    write_land_state(repo, branch, data)
                    update_ref(repo, land_runtime_ref(branch, "published"), receipt)
                    return data

            cp = git(
                ["push", remote, f"{receipt}:refs/heads/{mainline}"],
                repo,
                check=False,
            )
            if cp.returncode != 0:
                fail(
                    f"landing integrated locally but pushing {mainline} to {remote} failed; "
                    f"landing remains recoverable and is not finalized: "
                    f"{cp.stderr.strip() or cp.stdout.strip()}"
                )
        finally:
            if ref_exists(repo, remote_ref):
                update_ref(repo, remote_ref, None)

    data["phase"] = "published"
    write_land_state(repo, branch, data)
    update_ref(repo, land_runtime_ref(branch, "published"), receipt)
    return data


def cmd_repo_status(args: argparse.Namespace) -> dict[str, Any]:
    config = load_config()
    repo = discover_git_root()
    if repo is None:
        return {
            "harness_version": harness_version(),
            "git": "uninitialized",
            "project_root": str(PROJECT_ROOT),
            "configured_mainline": config.get("mainline"),
            "bootstrap_mainline": config.get("bootstrap_mainline"),
            "main_shadow": config.get("mainline") == MAIN_SHADOW_BRANCH,
        }
    repo = validate_repository_topology(repo)
    mainline = resolve_mainline(repo, config)
    return {
        "harness_version": harness_version(),
        "git": "initialized",
        "project_root": str(PROJECT_ROOT),
        "git_root": str(repo),
        "head": rev(repo, "HEAD") if has_commits(repo) else None,
        "branch": current_branch(repo),
        "clean": not worktree_status(repo),
        "mainline": mainline,
        "mainline_head": rev(repo, branch_ref(mainline)) if ref_exists(repo, branch_ref(mainline)) else None,
        "main_shadow": mainline == MAIN_SHADOW_BRANCH,
    }


def cmd_repo_bootstrap(args: argparse.Namespace) -> dict[str, Any]:
    config = load_config()
    bootstrap_mainline = resolve_bootstrap_mainline(config)
    repo = discover_git_root()
    requested_main_shadow = bool(getattr(args, "main_shadow", False))
    if repo is None:
        if requested_main_shadow:
            fail("main-shadow onboarding is only available for an existing repository with committed history")
        mainline = bootstrap_mainline
        cp = run(["git", "init", "-b", mainline, str(PROJECT_ROOT)], check=False)
        if cp.returncode != 0:
            fail(cp.stderr.strip() or cp.stdout.strip() or "git init failed")
        repo = require_repo()
    else:
        repo = validate_repository_topology(repo)
        if requested_main_shadow:
            preflight_main_shadow_bootstrap(args)
            shadow = configure_main_shadow(repo, config)
            mainline = shadow["mainline"]
            config = load_config()
        else:
            shadow = None
            mainline = resolve_mainline(repo, config)

    if has_commits(repo):
        if requested_main_shadow:
            seed_paths = list(args.seed_path or [])
            # The shadow selection itself must be durable on main-shadow. Seed staging remains
            # explicit; runtime/composition configuration are mandatory Harness-owned onboarding changes.
            mandatory_paths = [str(CONFIG_PATH.relative_to(repo))]
            active_composition = repo / ".harness" / "composition" / "active.json"
            if active_composition.exists():
                mandatory_paths.append(str(active_composition.relative_to(repo)))
            git(["add", "--", *mandatory_paths], repo)
            if args.all_seed_files:
                git(["add", "-A"], repo)
            elif seed_paths:
                git(["add", "--", *seed_paths], repo)

            staged = git(["diff", "--cached", "--quiet"], repo, check=False)
            baseline_created = staged.returncode != 0
            if baseline_created:
                git(["commit", "-m", args.message], repo)
            result = {
                "result": "main-shadow established" if baseline_created else "main-shadow already established",
                "git_root": str(repo),
                "mainline": MAIN_SHADOW_BRANCH,
                "head": rev(repo, "HEAD"),
                "baseline_commit_created": baseline_created,
                "baseline_scope": "local main-shadow",
                "main_shadow": True,
                "remote_publication": "not attempted by bootstrap",
                "remote_changed_by_bootstrap": False,
            }
            if shadow is not None:
                result.update({
                    "shadow_source_mainline": shadow["shadow_source_mainline"],
                    "shadow_source_head": shadow["shadow_source_head"],
                    "main_shadow_created": shadow["main_shadow_created"],
                    "main_shadow_reused": shadow["main_shadow_reused"],
                })
            return result
        return {
            "result": "already established",
            "git_root": str(repo),
            "mainline": resolve_mainline(repo, config),
            "head": rev(repo, "HEAD"),
            "baseline_commit_created": False,
            "main_shadow": resolve_mainline(repo, config) == MAIN_SHADOW_BRANCH,
            "remote_publication": "not attempted by bootstrap",
            "remote_changed_by_bootstrap": False,
        }

    mainline = bootstrap_mainline
    branch = current_branch(repo)
    if branch != mainline:
        git(["symbolic-ref", "HEAD", branch_ref(mainline)], repo)

    # Git itself is authoritative for whether identity is configured/usable.
    ident_name = git(["var", "GIT_AUTHOR_IDENT"], repo, check=False)
    ident_committer = git(["var", "GIT_COMMITTER_IDENT"], repo, check=False)
    if ident_name.returncode != 0 or ident_committer.returncode != 0:
        fail("Git author/committer identity is unavailable; repository may remain initialized/unborn")

    require_clean(repo) if args.require_clean else None
    seed_paths = list(args.seed_path or [])
    pre_staged = []
    for line in git(["ls-files", "--stage"], repo).stdout.splitlines():
        if not line.strip():
            continue
        pre_staged.append(line.split("\t", 1)[1] if "\t" in line else line.strip())
    if pre_staged and not args.all_seed_files:
        fail(
            "bootstrap index is not empty; refusing to inherit pre-staged content into the baseline "
            "unless --all-seed-files is explicitly selected:\n" + "\n".join(pre_staged[:50])
        )
    if args.all_seed_files:
        git(["add", "-A"], repo)
    elif seed_paths:
        # `--` prevents seed paths beginning with '-' from being parsed as Git options.
        git(["add", "--", *seed_paths], repo)
    # Safe default: create an empty baseline unless seed content was explicitly selected for staging.
    git(["commit", "--allow-empty", "-m", args.message], repo)
    return {
        "result": "baseline created",
        "mainline": mainline,
        "head": rev(repo, "HEAD"),
        "tree": tree(repo, "HEAD"),
        "baseline_commit_created": True,
        "baseline_scope": "local mainline",
        "main_shadow": False,
        "remote_publication": "not attempted by bootstrap",
        "remote_changed_by_bootstrap": False,
    }


def cmd_branch_start(args: argparse.Namespace) -> dict[str, Any]:
    repo = require_repo()
    config = load_config()
    if not has_commits(repo):
        fail("repository is unborn; run `repo bootstrap` first")
    mainline = resolve_mainline(repo, config)
    name = require_valid_branch_name(args.name, "branch --name")
    base = require_valid_branch_name(
        args.base or mainline,
        "branch --base" if args.base is not None else "configured mainline",
    )
    if not ref_exists(repo, branch_ref(base)):
        fail(f"base branch does not exist: {base}")
    if ref_exists(repo, branch_ref(name)):
        if current_branch(repo) == name and args.reuse:
            return {"result": "reused", "branch": name, "base": base, "head": rev(repo, "HEAD")}
        fail(f"branch already exists: {name}")
    require_clean(repo)
    # Use the full starting ref as defense in depth so a branch-like token can
    # never be reinterpreted as a `git switch` option.
    git(["switch", "-c", name, branch_ref(base)], repo)
    return {"result": "created", "branch": name, "base": base, "head": rev(repo, "HEAD")}


def approval_ref(branch: str) -> str:
    return f"refs/harness/landing-approval/{branch}"


def landing_approval_ref_reason(approval: str | None, branch: str) -> tuple[bool, str]:
    """Validate the single landing-approval namespace and branch binding."""
    if not approval:
        return False, "transaction has no approval ref"
    expected = approval_ref(branch)
    if approval != expected:
        return False, f"landing approval ref must be the branch's own Harness approval ref; expected {expected}, got {approval}"
    return True, "valid branch-bound approval ref"


def cmd_approval_record(args: argparse.Namespace) -> dict[str, Any]:
    repo = require_repo()
    require_clean(repo)
    branch = args.branch or current_branch(repo)
    if not branch:
        fail("approval requires a named branch")
    branch = require_valid_branch_name(branch, "approval --branch" if args.branch is not None else "current branch")
    if not ref_exists(repo, branch_ref(branch)):
        fail(f"branch does not exist: {branch}")
    require_goal_document(repo, branch)
    _project_model().require_goal_authority(repo, branch)
    commit = rev(repo, branch_ref(branch))
    ref = approval_ref(branch)
    if ref_exists(repo, ref):
        if rev(repo, ref) == commit:
            return {"result": "already recorded", "branch": branch, "ref": ref, "commit": commit, "tree": tree(repo, commit)}
        fail(f"approval already exists at a different boundary: {ref}; drop it after renewed user authorization")
    update_ref(repo, ref, commit)
    return {"result": "recorded", "branch": branch, "ref": ref, "commit": commit, "tree": tree(repo, commit)}


def cmd_approval_validate(args: argparse.Namespace) -> dict[str, Any]:
    repo = require_repo()
    branch = args.branch or current_branch(repo)
    if not branch:
        fail("approval validation requires a named branch")
    branch = require_valid_branch_name(branch, "approval --branch" if args.branch is not None else "current branch")
    ref = approval_ref(branch)
    if not ref_exists(repo, ref):
        return {"valid": False, "reason": "missing", "ref": ref}
    commit = rev(repo, ref)
    approved_tree = tree(repo, ref)
    branch_commit = rev(repo, branch_ref(branch)) if ref_exists(repo, branch_ref(branch)) else None
    same_tree = branch_commit is not None and tree(repo, branch_commit) == approved_tree
    project_authority = _project_model().goal_authority_state(repo, branch)
    return {
        "valid": bool(same_tree and project_authority.get("ready")),
        "ref": ref,
        "commit": commit,
        "tree": approved_tree,
        "branch": branch,
        "branch_commit": branch_commit,
        "same_tree": same_tree,
        "project_authority": project_authority,
    }


def land_approval_valid(repo: Path, data: dict[str, Any]) -> tuple[bool, str]:
    """Return whether an unmerged landing transaction still has live exact authority."""
    approval = data.get("approval_ref")
    branch = data.get("branch")
    if not branch:
        return False, "transaction has no branch"
    ref_ok, ref_reason = landing_approval_ref_reason(approval, branch)
    if not ref_ok:
        return False, ref_reason
    if not ref_exists(repo, approval):
        return False, f"approval ref is missing: {approval}"
    actual = rev(repo, approval)
    expected = data.get("approval_source_commit")
    if expected and actual != expected:
        return False, f"approval ref moved from {expected} to {actual}"
    return True, "valid"

def abort_land_transaction(repo: Path, branch: str) -> None:
    delete_land_runtime_refs(repo, branch)
    delete_land_state(repo, branch)


def approval_withdrawal_plan(repo: Path, approval: str) -> tuple[list[str], list[str]]:
    """Classify dependent landing transactions before mutating approval state.

    A transaction may be discarded only while its candidate has not crossed the
    configured mainline ref. Once mainline equals the recorded candidate, receipt
    state is recovery authority and must survive approval withdrawal.
    """
    cancel: list[str] = []
    preserve: list[str] = []
    directory = land_state_dir(repo)
    if not directory.exists():
        return cancel, preserve
    for path in sorted(directory.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            fail(f"cannot inspect landing transaction during approval withdrawal: {path}: {exc}")
        branch = data.get("branch")
        if not isinstance(branch, str) or not branch:
            fail(f"invalid landing transaction metadata during approval withdrawal: {path} has no branch binding")
        data = validate_land_state(branch, data)
        if data.get("approval_ref") != approval:
            continue
        phase = data.get("phase")
        if phase == "ready":
            cancel.append(branch)
            continue
        if phase in {"merged", "published"}:
            preserve.append(branch)
            continue
        if phase != "integrating":
            fail(f"unsupported landing phase during approval withdrawal: {phase!r}")

        mainline = data["mainline"]
        if not ref_exists(repo, branch_ref(mainline)):
            fail(f"cannot withdraw approval while integrating: configured mainline is missing: {mainline}")
        candidate = data.get("merge_commit")
        if not candidate:
            fail("cannot withdraw approval while integrating: transaction has no candidate receipt")
        current_mainline = rev(repo, branch_ref(mainline))
        if current_mainline == data.get("base_commit"):
            # Candidate exists, but the irreversible mainline boundary has not
            # been crossed. Withdrawal may safely cancel the prepared attempt.
            cancel.append(branch)
        elif current_mainline == candidate:
            # A crash may have happened after the atomic CAS but before `merged`
            # was persisted. Keep the transaction so deterministic recovery can
            # finish without needing the withdrawn approval.
            preserve.append(branch)
        else:
            fail(
                "cannot withdraw approval while an integrating landing has ambiguous mainline state; "
                f"{mainline} is neither prepared base {data.get('base_commit')} nor candidate {candidate}"
            )
    return cancel, preserve


def cmd_approval_drop(args: argparse.Namespace) -> dict[str, Any]:
    repo = require_repo()
    branch = args.branch or current_branch(repo)
    if not branch:
        fail("approval invalidation requires a branch name")
    branch = require_valid_branch_name(branch, "approval --branch" if args.branch is not None else "current branch")
    if _collaboration().active_collaboration_model(PROJECT_ROOT) == "cooperative-multi-user" and _collaboration().read_handoff_state(repo, branch, required=False) is not None:
        fail(
            "accepted cooperative handoff approval cannot be dropped independently; "
            "abort any ready landing transaction and release the handoff instead"
        )
    ref = approval_ref(branch)
    # Preflight every dependent transaction before deleting the approval ref so
    # a corrupt/diverged recovery state cannot cause a partial withdrawal.
    cancel, preserved = approval_withdrawal_plan(repo, ref)
    existed = ref_exists(repo, ref)
    if existed:
        update_ref(repo, ref, None)
    for dependent_branch in cancel:
        abort_land_transaction(repo, dependent_branch)
    return {
        "result": "removed" if existed else "already absent",
        "ref": ref,
        "invalidated_land_transactions": cancel,
        "preserved_land_transactions": preserved,
    }


def land_state_summary(repo: Path, data: dict[str, Any]) -> dict[str, Any]:
    branch = data["branch"]
    branch_exists_now = ref_exists(repo, branch_ref(branch))
    head = rev(repo, branch_ref(branch)) if branch_exists_now else None
    mainline = data["mainline"]
    mainline_head = rev(repo, branch_ref(mainline)) if ref_exists(repo, branch_ref(mainline)) else None
    approval_live, approval_reason = land_approval_valid(repo, data)
    return {
        **data,
        "branch_exists": branch_exists_now,
        "current_branch_head": head,
        "current_mainline_head": mainline_head,
        "base_unchanged": mainline_head == data.get("base_commit"),
        "head_at_ready": bool(head and data.get("ready_commit") == head),
        "approval_live": approval_live,
        "approval_status": approval_reason,
    }


def cmd_land_prepare(args: argparse.Namespace) -> dict[str, Any]:
    repo = require_repo()
    integration_actor = _collaboration().require_integration_authority(repo)
    config = load_config()
    require_clean(repo)
    branch = args.branch or current_branch(repo)
    if not branch:
        fail("landing preparation requires a named work branch")
    branch = require_valid_branch_name(branch, "land --branch" if args.branch is not None else "current branch")
    if current_branch(repo) != branch:
        fail(f"switch to landing branch before prepare: {branch}")
    mainline = resolve_mainline(repo, config)
    if branch == mainline:
        fail("cannot prepare configured mainline as a work branch")
    if not ref_exists(repo, branch_ref(branch)):
        fail(f"branch does not exist: {branch}")
    require_goal_document(repo, branch)
    _project_model().require_goal_authority(repo, branch)

    path = land_state_path(repo, branch)
    if path.exists():
        old = read_land_state(repo, branch)
        if old.get("phase") in {"merged", "published"}:
            fail("landing already crossed mainline; finish deterministic recovery instead")
        head = rev(repo, branch_ref(branch))
        base = rev(repo, branch_ref(mainline))
        if old.get("ready_commit") == head and old.get("base_commit") == base:
            approval_ok, _ = land_approval_valid(repo, old)
            if approval_ok:
                return {"result": "already prepared", **land_state_summary(repo, old)}
        fail("landing transaction already exists at a different boundary; abort it before preparing again")

    approval = approval_ref(branch)
    if not ref_exists(repo, approval):
        fail(f"landing preparation requires recorded approval: {approval}")
    approval_source_commit = rev(repo, approval)
    approved_tree = tree(repo, approval)
    head = rev(repo, branch_ref(branch))
    if tree(repo, head) != approved_tree:
        fail("branch full tree no longer equals the recorded approval tree")
    base = rev(repo, branch_ref(mainline))
    accepted_handoff = _collaboration().require_live_accepted_handoff(repo, branch)
    if accepted_handoff is not None:
        handoff_metadata = _collaboration().validate_handoff_metadata(branch, accepted_handoff["metadata"])
        if handoff_metadata["handoff_base"] != base:
            fail(
                "LANDING_BLOCKED: configured mainline moved after the contributor's approved handoff base; "
                "run `land assess --branch <branch>` for human-resolvable evidence"
            )
    else:
        handoff_metadata = None
    remote = str(config.get("remote", "origin"))
    require_remote_landing_alignment(repo, remote, mainline, branch, head)

    data = {
        "branch": branch,
        "mainline": mainline,
        "approval_ref": approval,
        "approval_source_commit": approval_source_commit,
        "approved_tree": approved_tree,
        "base_commit": base,
        "ready_commit": head,
        "phase": "ready",
    }
    if accepted_handoff is not None and handoff_metadata is not None:
        data.update({
            "handoff_commit": accepted_handoff["handoff_commit"],
            "acceptance_commit": accepted_handoff["acceptance_commit"],
            "handoff_base": handoff_metadata["handoff_base"],
            "contributor_actor": handoff_metadata["contributor_actor"],
            "approval_actor": handoff_metadata.get("approval_actor"),
            "integration_actor": integration_actor["actor"] if integration_actor else None,
        })
    write_land_state(repo, branch, data)
    update_ref(repo, land_runtime_ref(branch, "base"), base)
    update_ref(repo, land_runtime_ref(branch, "ready"), head)
    return {"result": "prepared", **land_state_summary(repo, data)}


def finalize_land(repo: Path, data: dict[str, Any], delete_remote: bool) -> dict[str, Any]:
    branch = data["branch"]
    mainline = data["mainline"]
    remote = str(load_config().get("remote", "origin"))
    branch_commit = data.get("ready_commit")
    merge_commit = data.get("merge_commit")
    if not merge_commit:
        fail("merged landing transaction has no recorded merge receipt")
    if not ref_exists(repo, branch_ref(mainline)):
        fail(f"configured mainline branch no longer exists: {mainline}")
    mainline_head = rev(repo, branch_ref(mainline))
    if not is_ancestor(repo, merge_commit, mainline_head):
        fail("recorded landing merge receipt is no longer reachable from configured mainline")
    local_branch_exists = ref_exists(repo, branch_ref(branch))
    if local_branch_exists:
        if current_branch(repo) == branch:
            fail("cannot finalize landing while still on the work branch")
        if not branch_commit:
            fail("cannot delete local work branch without a prepared ready boundary")
        actual_branch_commit = rev(repo, branch_ref(branch))
        if actual_branch_commit != branch_commit:
            fail(
                "local work branch moved from prepared ready boundary after merge; refusing deletion "
                f"({branch_commit} -> {actual_branch_commit})"
            )
    # Preflight local exactness before any destructive remote/local cleanup so a
    # locally advanced branch cannot cause partial finalization.
    handoff_commit = data.get("handoff_commit")
    if handoff_commit and branch_commit:
        # A consumed cooperative handoff is runtime coordination state, not Project
        # history. Finalization atomically removes the accepted handoff ref and the
        # published Goal branch. Exact leases keep cleanup fail-closed and retry-safe.
        acceptance_commit = data.get("acceptance_commit")
        if not acceptance_commit:
            fail(
                "landing transaction carries a cooperative handoff without an acceptance commit; "
                "the transaction is incomplete and cannot be finalized safely"
            )
        delete_remote_refs_exact(
            repo,
            remote,
            {_collaboration().handoff_ref(branch): acceptance_commit, f"refs/heads/{branch}": branch_commit},
        )
    elif delete_remote and branch_commit:
        delete_remote_exact(repo, remote, branch, branch_commit)
    if local_branch_exists:
        update_ref(repo, branch_ref(branch), None, branch_commit)
    delete_goal_document(repo, branch)
    _project_model().delete_goal_spec_document(repo, branch)
    delete_session_document(repo)
    approval = data.get("approval_ref")
    if approval and approval.startswith("refs/harness/landing-approval/") and ref_exists(repo, approval):
        update_ref(repo, approval, None)
    delete_land_runtime_refs(repo, branch)
    delete_land_state(repo, branch)
    handoff_path = _collaboration().handoff_state_path(repo, branch)
    if handoff_path.exists():
        handoff_path.unlink()
    _collaboration().delete_handoff_runtime_refs(repo, branch)
    result = {"result": "landed", "branch": branch, "mainline": data["mainline"], "merge_commit": data.get("merge_commit")}
    return result


def prepare_local_integration(repo: Path, data: dict[str, Any], message: str) -> str:
    """Build the configured landing shape without moving mainline."""
    branch = data["branch"]
    base = data["base_commit"]
    ready = data["ready_commit"]
    with tempfile.TemporaryDirectory(prefix="harness-land-") as td:
        worktree = Path(td) / "integration"
        cp = git(["worktree", "add", "--detach", str(worktree), base], repo, check=False)
        if cp.returncode != 0:
            detail = cp.stderr.strip() or cp.stdout.strip() or f"exit {cp.returncode}"
            fail(f"cannot create disposable landing worktree: {detail}")
        try:
            if is_ancestor(repo, base, ready) and commit_count(repo, base, ready) == 1:
                git(["merge", "--ff-only", ready], worktree)
            else:
                git(["merge", "--no-ff", ready, "-m", message], worktree)
            candidate = rev(worktree, "HEAD")
            if tree(worktree, candidate) != tree(repo, ready):
                fail("landing candidate tree does not equal prepared branch tree")
            update_ref(repo, land_runtime_ref(branch, "candidate"), candidate)
            return candidate
        except HarnessError as exc:
            fail(f"landing preparation failed before mainline update: {exc}")
        finally:
            git(["worktree", "remove", "--force", str(worktree)], repo, check=False)


def worktrees_with_branch(repo: Path, branch: str) -> list[Path]:
    """Return linked worktrees whose HEAD is attached to the exact branch ref."""
    cp = git(["worktree", "list", "--porcelain"], repo)
    target = branch_ref(branch)
    matches: list[Path] = []
    current_path: Path | None = None
    for line in cp.stdout.splitlines():
        if line.startswith("worktree "):
            current_path = Path(line[len("worktree "):]).resolve()
        elif line == f"branch {target}" and current_path is not None:
            matches.append(current_path)
    return matches


def refuse_mainline_checked_out_elsewhere(repo: Path, mainline: str) -> None:
    current = repo.resolve()
    elsewhere = [path for path in worktrees_with_branch(repo, mainline) if path != current]
    if elsewhere:
        rendered = ", ".join(str(path) for path in elsewhere)
        fail(
            f"mainline branch {mainline!r} is checked out in another linked Git worktree: {rendered}; "
            "refusing to move its ref behind that worktree"
        )


def complete_local_integration(repo: Path, data: dict[str, Any]) -> dict[str, Any]:
    """Atomically cross a prepared local candidate onto mainline, restart-safely."""
    branch = data["branch"]
    mainline = data["mainline"]
    base = data["base_commit"]
    ready = data.get("ready_commit")
    candidate = data.get("merge_commit")
    candidate_ref = land_runtime_ref(branch, "candidate")
    if not candidate or not ready:
        fail("integrating landing transaction is missing its candidate/ready boundary")
    if not ref_exists(repo, candidate_ref) or rev(repo, candidate_ref) != candidate:
        fail("integrating landing candidate anchor is missing or moved")
    if tree(repo, candidate) != tree(repo, ready):
        fail("integrating landing candidate no longer has the verified ready tree")
    if not ref_exists(repo, branch_ref(mainline)):
        fail(f"mainline branch no longer exists: {mainline}")

    current_mainline = rev(repo, branch_ref(mainline))
    if current_mainline == base:
        if data.get("handoff_commit"):
            _collaboration().require_live_accepted_handoff(repo, branch)
        remote = str(load_config().get("remote", "origin"))
        require_remote_landing_alignment(repo, remote, mainline, branch, ready)
        approval_ok, approval_reason = land_approval_valid(repo, data)
        if not approval_ok:
            fail(f"landing approval is no longer valid: {approval_reason}; refusing mainline update")
        if not ref_exists(repo, branch_ref(branch)) or rev(repo, branch_ref(branch)) != ready:
            fail("work branch moved from verified ready boundary before mainline update")
        refuse_mainline_checked_out_elsewhere(repo, mainline)
        # A checked-out branch must not have its ref moved behind its worktree.
        # Detach only in the uncommon recovery/invocation case where mainline is
        # currently checked out; ordinary Branch Land enters here from work branch.
        if current_branch(repo) == mainline:
            git(["switch", "--detach", base], repo)
        update_ref(repo, branch_ref(mainline), candidate, base)
    elif current_mainline != candidate:
        fail(
            "mainline moved while a local landing candidate was prepared; "
            "refusing to extend the prepared authority to a different boundary"
        )

    # If a previous process crossed the atomic ref update and stopped before
    # persisting `merged`, this is the restart-safe completion point.
    data["phase"] = "merged"
    write_land_state(repo, branch, data)
    update_ref(repo, land_runtime_ref(branch, "merged"), candidate)
    if current_branch(repo) != mainline:
        git(["switch", mainline], repo)
    return data


def cmd_land_merge(args: argparse.Namespace) -> dict[str, Any]:
    repo = require_repo()
    _collaboration().require_integration_authority(repo)
    require_clean(repo)
    branch = args.branch or current_branch(repo)
    if not branch:
        fail("landing merge requires a branch")
    branch = require_valid_branch_name(branch, "land --branch" if args.branch is not None else "current branch")
    data = read_land_state(repo, branch)
    mainline = data["mainline"]
    if not ref_exists(repo, branch_ref(mainline)):
        fail(f"mainline branch no longer exists: {mainline}")

    if data.get("phase") == "published":
        if current_branch(repo) != mainline:
            git(["switch", mainline], repo)
        return finalize_land(repo, data, args.delete_remote)

    if data.get("phase") == "merged":
        if current_branch(repo) != mainline:
            git(["switch", mainline], repo)
        data = publish_landed_mainline(repo, data)
        return finalize_land(repo, data, args.delete_remote)

    if data.get("phase") == "integrating":
        data = complete_local_integration(repo, data)
        data = publish_landed_mainline(repo, data)
        return finalize_land(repo, data, args.delete_remote)

    if data.get("handoff_commit"):
        _collaboration().require_live_accepted_handoff(repo, branch)
    approval_ok, approval_reason = land_approval_valid(repo, data)
    if not approval_ok:
        fail(f"landing approval is no longer valid: {approval_reason}; re-check and prepare again before landing")

    if not ref_exists(repo, branch_ref(branch)):
        fail("work branch is missing before landing")
    head = rev(repo, branch_ref(branch))
    if data.get("ready_commit") != head:
        fail("work branch moved after `land prepare`; abort and prepare the current boundary")
    if tree(repo, head) != data.get("approved_tree"):
        fail("prepared branch tree no longer equals the approved tree")
    if rev(repo, branch_ref(mainline)) != data.get("base_commit"):
        fail("mainline moved after `land prepare`; re-check the Goal against current mainline and prepare again")

    message = args.message or f"Land {branch}"
    candidate = prepare_local_integration(repo, data, message)
    candidate_ref = land_runtime_ref(branch, "candidate")
    try:
        approval_ok, approval_reason = land_approval_valid(repo, data)
        if not approval_ok:
            fail(f"landing approval is no longer valid after candidate preparation: {approval_reason}")
        if rev(repo, branch_ref(branch)) != head:
            fail("work branch moved while landing candidate was being prepared")
        if rev(repo, branch_ref(mainline)) != data.get("base_commit"):
            fail("mainline moved while landing candidate was being prepared; re-check and prepare again")
        remote = str(load_config().get("remote", "origin"))
        require_remote_landing_alignment(repo, remote, mainline, branch, head)

        data["phase"] = "integrating"
        data["merge_commit"] = candidate
        write_land_state(repo, branch, data)
    except HarnessError:
        if ref_exists(repo, candidate_ref):
            update_ref(repo, candidate_ref, None)
        raise
    data = complete_local_integration(repo, data)
    data = publish_landed_mainline(repo, data)
    return finalize_land(repo, data, args.delete_remote)


def cmd_land_abort(args: argparse.Namespace) -> dict[str, Any]:
    repo = require_repo()
    _collaboration().require_integration_authority(repo)
    branch = args.branch or current_branch(repo)
    if not branch:
        fail("land abort requires a branch")
    branch = require_valid_branch_name(branch, "land --branch" if args.branch is not None else "current branch")
    data = read_land_state(repo, branch)
    if data.get("phase") != "ready":
        fail("cannot abort after integration has started; resume deterministic landing recovery instead")
    abort_land_transaction(repo, branch)
    return {"result": "transaction removed", "branch": branch}


def cmd_abandon_discard(args: argparse.Namespace) -> dict[str, Any]:
    repo = require_repo()
    config = load_config()
    require_clean(repo)
    target = require_valid_branch_name(args.target, "abandon --target")
    if _collaboration().active_collaboration_model(PROJECT_ROOT) == "cooperative-multi-user" and _collaboration().read_handoff_state(repo, target, required=False) is not None:
        fail(
            "accepted cooperative handoff cannot be abandoned independently; "
            "abort any ready landing transaction and release the handoff first"
        )
    if not ref_exists(repo, branch_ref(target)):
        fail(f"target branch does not exist: {target}")
    mainline = resolve_mainline(repo, config)
    if target == mainline:
        fail("cannot abandon configured mainline")

    target_commit = rev(repo, branch_ref(target))
    if args.mode == "no-op":
        mb = git(["merge-base", branch_ref(mainline), branch_ref(target)], repo, check=False)
        if mb.returncode != 0 or not mb.stdout.strip():
            fail("cannot prove no-op abandonment because target has no merge base with configured mainline")
        merge_base_commit = mb.stdout.strip()
        if tree(repo, target_commit) != tree(repo, merge_base_commit):
            fail(
                "no-op abandonment requires the target tree to equal its merge-base tree; "
                "unique durable branch changes require --mode explicit"
            )

    if args.delete_remote:
        remote = str(config.get("remote", "origin"))
        delete_remote_exact(repo, remote, target, target_commit)

    if current_branch(repo) == target:
        if not ref_exists(repo, branch_ref(mainline)):
            fail(f"cannot switch away from target; fallback branch missing: {mainline}")
        git(["switch", mainline], repo)

    update_ref(repo, branch_ref(target), None, target_commit)
    delete_goal_document(repo, target)
    _project_model().delete_goal_spec_document(repo, target)
    delete_session_document(repo)
    approval = approval_ref(target)
    if ref_exists(repo, approval):
        update_ref(repo, approval, None)
    abort_land_transaction(repo, target)
    return {"result": "discarded", "target": target, "discarded_commit": target_commit, "mode": args.mode}


def list_land_transaction_states(repo: Path) -> list[dict[str, Any]]:
    directory = land_state_dir(repo)
    if not directory.exists():
        return []
    result: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            result.append({"state_file": str(path), "error": str(exc)})
            continue
        branch = data.get("branch")
        if not isinstance(branch, str) or not branch:
            result.append({"state_file": str(path), "error": "invalid land transaction: missing branch binding"})
            continue
        try:
            data = validate_land_state(branch, data)
            result.append(land_state_summary(repo, data))
        except HarnessError as exc:
            result.append({**data, "state_file": str(path), "error": str(exc)})
    return result


def cmd_resume(args: argparse.Namespace) -> dict[str, Any]:
    config = load_config()
    repo = discover_git_root()
    if repo is None:
        return {
            "git": "uninitialized",
            "project_root": str(PROJECT_ROOT),
            "next_git_action": "after lifecycle classification, Branch Start may invoke `repo bootstrap`",
        }
    repo = validate_repository_topology(repo)
    mainline = resolve_mainline(repo, config)
    branch = current_branch(repo)
    approvals = list_refs(repo, "refs/harness/landing-approval/")
    current_approval = None
    if branch:
        ref = approval_ref(branch)
        if ref_exists(repo, ref):
            current_approval = {
                "ref": ref,
                "commit": rev(repo, ref),
                "tree": tree(repo, ref),
                "current_branch_tree_matches": tree(repo, ref) == tree(repo, branch_ref(branch)),
            }
    collaboration_model = _collaboration().active_collaboration_model(PROJECT_ROOT)
    project_model = _project_model().active_project_model(PROJECT_ROOT)
    project_authority = (
        _project_model().goal_authority_state(repo, branch)
        if branch and branch != mainline else None
    )
    local_actor = _collaboration().read_collaboration_state(repo, required=False)
    accepted_handoff = _collaboration().read_handoff_state(repo, branch, required=False) if branch else None
    result = {
        "git": "initialized",
        "collaboration_model": collaboration_model,
        "project_model": project_model,
        "project_authority": project_authority,
        "local_actor": local_actor,
        "accepted_handoff": accepted_handoff,
        "git_root": str(repo),
        "branch": branch,
        "head": rev(repo, "HEAD") if has_commits(repo) else None,
        "clean": not worktree_status(repo),
        "working_tree_changes": worktree_status(repo),
        "mainline": mainline,
        "mainline_head": rev(repo, branch_ref(mainline)) if ref_exists(repo, branch_ref(mainline)) else None,
        "goal_path": goal_document_path(branch) if branch and branch != mainline else None,
        "goal_document_exists": bool(
            branch and branch != mainline and goal_document_file(repo, branch).is_file()
        ),
        "current_landing_approval": current_approval,
        "approvals": approvals,
        "land_transactions": list_land_transaction_states(repo),
    }
    if branch and branch != mainline and ref_exists(repo, branch_ref(mainline)):
        mb = git(["merge-base", branch_ref(mainline), branch_ref(branch)], repo, check=False)
        result["merge_base"] = mb.stdout.strip() if mb.returncode == 0 else None
    return result


