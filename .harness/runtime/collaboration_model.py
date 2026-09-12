#!/usr/bin/env python3
"""Collaboration-model runtime mechanics.

Owns active Collaboration-model selection, local actor state, cooperative
handoff publication/acceptance/release, and model-specific coordination facts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from kernel import (
    PROJECT_ROOT,
    approval_ref,
    atomic_json,
    branch_ref,
    current_branch,
    delete_goal_document,
    fail,
    file_at,
    git,
    git_common_dir,
    git_input,
    goal_document_file,
    goal_document_path,
    harness_version,
    is_ancestor,
    key_for_branch,
    land_state_path,
    load_config,
    ref_exists,
    remote_head,
    remote_ref_oids,
    require_clean,
    require_goal_document,
    require_repo,
    require_valid_branch_name,
    resolve_mainline,
    rev,
    tree,
    update_ref,
)

HANDOFF_SCHEMA_VERSION = 2
ACCEPTANCE_SCHEMA_VERSION = 1
HANDOFF_STATE_SCHEMA_VERSION = 2
COLLABORATION_STATE_SCHEMA_VERSION = 1
COMPOSITION_SCHEMA_VERSION = 1
SUPPORTED_COLLABORATION_MODELS = frozenset({"single-user", "cooperative-multi-user"})

def _project_model():
    """Load Project-model mechanics only at the collaboration integration seam."""
    import project_model
    return project_model

def handoff_ref(branch: str) -> str:
    return f"refs/harness/handoff/{branch}"


def handoff_runtime_ref(branch: str, name: str) -> str:
    return f"refs/harness/runtime/handoff/{key_for_branch(branch)}/{name}"


def handoff_state_dir(repo: Path) -> Path:
    return git_common_dir(repo) / "harness" / "handoff"


def handoff_state_path(repo: Path, branch: str) -> Path:
    return handoff_state_dir(repo) / f"{key_for_branch(branch)}.json"


def delete_handoff_runtime_refs(repo: Path, branch: str) -> None:
    prefix = f"refs/harness/runtime/handoff/{key_for_branch(branch)}/"
    cp = git(["for-each-ref", "--format=%(refname)", prefix], repo)
    for ref in [line.strip() for line in cp.stdout.splitlines() if line.strip()]:
        update_ref(repo, ref, None)


def validate_handoff_metadata(branch: str, data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        fail(f"invalid handoff metadata for {branch}: expected JSON object")
    if data.get("schema_version") != HANDOFF_SCHEMA_VERSION:
        fail(f"invalid handoff metadata for {branch}: unsupported schema_version")
    if data.get("branch") != branch:
        fail(f"invalid handoff metadata for {branch}: branch binding mismatch")
    required = {
        "ready_commit": str,
        "approved_tree": str,
        "approval_source_commit": str,
        "handoff_base": str,
        "contributor_actor": str,
        "goal_sha256": str,
        "project_model": str,
        "harness_release": str,
    }
    for key, expected in required.items():
        if not isinstance(data.get(key), expected) or not str(data.get(key)).strip():
            fail(f"invalid handoff metadata for {branch}: `{key}` has invalid type or is missing")
    for key in ("ready_commit", "approved_tree", "approval_source_commit", "handoff_base"):
        if not re.fullmatch(r"[0-9a-fA-F]{40,64}", data[key]):
            fail(f"invalid handoff metadata for {branch}: `{key}` is not a Git object id")
    if not re.fullmatch(r"[0-9a-f]{64}", data["goal_sha256"]):
        fail(f"invalid handoff metadata for {branch}: goal_sha256 is not SHA-256")
    if data["project_model"] not in {"spec", "repository-native"}:
        fail(f"invalid handoff metadata for {branch}: unsupported project_model {data['project_model']!r}")
    goal_spec_sha = data.get("goal_spec_sha256")
    if data["project_model"] == "repository-native":
        if not isinstance(goal_spec_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", goal_spec_sha):
            fail(f"invalid handoff metadata for {branch}: repository-native handoff requires goal_spec_sha256")
    elif goal_spec_sha is not None:
        fail(f"invalid handoff metadata for {branch}: spec-mode handoff must not carry goal_spec_sha256")
    approval_actor = data.get("approval_actor")
    if approval_actor is not None and (not isinstance(approval_actor, str) or not approval_actor.strip()):
        fail(f"invalid handoff metadata for {branch}: approval_actor must be non-empty text when present")
    return data


def create_handoff_commit(
    repo: Path, metadata: dict[str, Any], goal_text: str, goal_spec_text: str | None = None
) -> str:
    branch = metadata["branch"]
    metadata_text = json.dumps(metadata, indent=2, sort_keys=True) + "\n"
    metadata_blob = git_input(["hash-object", "-w", "--stdin"], repo, metadata_text).stdout.strip()
    goal_blob = git_input(["hash-object", "-w", "--stdin"], repo, goal_text).stdout.strip()
    tree_rows = [
        f"100644 blob {goal_blob}\tgoal.md\n",
        f"100644 blob {metadata_blob}\thandoff.json\n",
    ]
    if goal_spec_text is not None:
        goal_spec_blob = git_input(["hash-object", "-w", "--stdin"], repo, goal_spec_text).stdout.strip()
        tree_rows.append(f"100644 blob {goal_spec_blob}\tgoal-spec.md\n")
    handoff_tree = git_input(["mktree"], repo, "".join(tree_rows)).stdout.strip()
    parents = [metadata["ready_commit"]]
    if metadata["approval_source_commit"] != metadata["ready_commit"]:
        parents.append(metadata["approval_source_commit"])
    args = ["commit-tree", handoff_tree]
    for parent in parents:
        args.extend(["-p", parent])
    args.extend(["-m", f"Harness handoff: {branch}"])
    return git(args, repo).stdout.strip()


def read_handoff_commit(repo: Path, branch: str, commit: str) -> tuple[dict[str, Any], str, str | None]:
    kind = git(["cat-file", "-t", commit], repo, check=False)
    if kind.returncode != 0 or kind.stdout.strip() != "commit":
        fail(f"invalid handoff object for {branch}: {commit} is not a commit")
    raw = file_at(repo, commit, "handoff.json")
    goal_text = file_at(repo, commit, "goal.md")
    if raw is None or goal_text is None:
        fail(f"invalid handoff object for {branch}: missing handoff.json or goal.md")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f"invalid handoff metadata for {branch}: {exc}")
    data = validate_handoff_metadata(branch, data)
    digest = hashlib.sha256(goal_text.encode("utf-8")).hexdigest()
    if digest != data["goal_sha256"]:
        fail(f"invalid handoff object for {branch}: Goal recovery text digest mismatch")
    goal_spec_text = file_at(repo, commit, "goal-spec.md")
    if data["project_model"] == "repository-native":
        if goal_spec_text is None:
            fail(f"invalid handoff object for {branch}: repository-native handoff is missing goal-spec.md")
        digest = hashlib.sha256(goal_spec_text.encode("utf-8")).hexdigest()
        if digest != data["goal_spec_sha256"]:
            fail(f"invalid handoff object for {branch}: Goal Spec digest mismatch")
    elif goal_spec_text is not None:
        fail(f"invalid handoff object for {branch}: spec-mode handoff unexpectedly contains goal-spec.md")
    if tree(repo, data["approval_source_commit"]) != data["approved_tree"]:
        fail(f"invalid handoff object for {branch}: approval source tree does not match approved_tree")
    return data, goal_text, goal_spec_text


def create_acceptance_commit(repo: Path, branch: str, handoff_commit: str, integration_actor: str) -> str:
    """Create the acceptance commit that replaces the handoff commit at the handoff ref.

    Its only parent is the immutable handoff commit, so the published handoff content is
    unchanged and remains exactly recoverable, while acceptance becomes a compare-and-swap
    on the same remote ref that contributor withdrawal leases.
    """
    data = {
        "schema_version": ACCEPTANCE_SCHEMA_VERSION,
        "kind": "harness-handoff-acceptance",
        "branch": branch,
        "handoff_commit": handoff_commit,
        "integration_actor": integration_actor,
        "harness_release": harness_version(),
    }
    text = json.dumps(data, indent=2, sort_keys=True) + "\n"
    data_blob = git_input(["hash-object", "-w", "--stdin"], repo, text).stdout.strip()
    acceptance_tree = git_input(["mktree"], repo, f"100644 blob {data_blob}\tacceptance.json\n").stdout.strip()
    return git(
        ["commit-tree", acceptance_tree, "-p", handoff_commit, "-m", f"Harness handoff acceptance: {branch}"],
        repo,
    ).stdout.strip()


def read_acceptance_commit(repo: Path, branch: str, commit: str) -> dict[str, Any] | None:
    """Return acceptance metadata when `commit` is an acceptance commit, else None."""
    raw = file_at(repo, commit, "acceptance.json")
    if raw is None:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f"invalid handoff acceptance for {branch}: {exc}")
    if not isinstance(data, dict) or data.get("kind") != "harness-handoff-acceptance":
        fail(f"invalid handoff acceptance for {branch}: unexpected acceptance object")
    if data.get("schema_version") != ACCEPTANCE_SCHEMA_VERSION:
        fail(f"invalid handoff acceptance for {branch}: unsupported schema_version")
    if data.get("branch") != branch:
        fail(f"invalid handoff acceptance for {branch}: branch binding mismatch")
    handoff_commit = data.get("handoff_commit")
    if not isinstance(handoff_commit, str) or not re.fullmatch(r"[0-9a-fA-F]{40,64}", handoff_commit):
        fail(f"invalid handoff acceptance for {branch}: handoff_commit")
    actor = data.get("integration_actor")
    if not isinstance(actor, str) or not actor.strip():
        fail(f"invalid handoff acceptance for {branch}: integration_actor")
    parents = git(["rev-list", "--parents", "-n", "1", commit], repo).stdout.split()[1:]
    if parents != [handoff_commit]:
        fail(f"invalid handoff acceptance for {branch}: acceptance must have exactly the handoff commit as parent")
    return data


def fetch_remote_handoff(repo: Path, branch: str) -> dict[str, Any]:
    """Fetch and classify the live cooperative handoff for `branch`.

    The handoff ref holds either the immutable handoff commit (published) or an
    acceptance commit whose only parent is that handoff commit (accepted). Keeping both
    states on one ref makes acceptance and withdrawal a single compare-and-swap each, so
    exactly one of two racing operations can succeed.
    """
    remote = str(load_config().get("remote", "origin"))
    h_ref = handoff_ref(branch)
    branch_remote_ref = f"refs/heads/{branch}"
    live = remote_ref_oids(repo, remote, [h_ref, branch_remote_ref])
    tip = live[h_ref]
    branch_oid = live[branch_remote_ref]
    if tip is None:
        fail(f"no published handoff for branch: {branch}")
    if branch_oid is None:
        fail(f"published handoff branch is missing from {remote}: {branch}")
    local_tip = handoff_runtime_ref(branch, "remote-handoff")
    local_branch = handoff_runtime_ref(branch, "remote-branch")
    cp = git(
        ["fetch", "--no-tags", remote, f"+{h_ref}:{local_tip}", f"+{branch_remote_ref}:{local_branch}"],
        repo,
        check=False,
    )
    if cp.returncode != 0:
        fail(f"cannot fetch published handoff for {branch}: {cp.stderr.strip() or cp.stdout.strip()}")
    fetched_tip = rev(repo, local_tip)
    fetched_branch = rev(repo, local_branch)
    if fetched_tip != tip or fetched_branch != branch_oid:
        fail(f"published handoff moved during fetch for {branch}; retry from current remote state")
    acceptance = read_acceptance_commit(repo, branch, fetched_tip)
    handoff_commit = acceptance["handoff_commit"] if acceptance is not None else fetched_tip
    data, goal_text, goal_spec_text = read_handoff_commit(repo, branch, handoff_commit)
    if data["ready_commit"] != fetched_branch:
        fail(f"published handoff ready commit does not match remote branch for {branch}")
    if tree(repo, fetched_branch) != data["approved_tree"]:
        fail(f"published handoff branch tree does not equal approved tree for {branch}")
    return {
        "remote": remote,
        "tip": fetched_tip,
        "handoff_commit": handoff_commit,
        "acceptance_commit": fetched_tip if acceptance is not None else None,
        "acceptance": acceptance,
        "metadata": data,
        "goal_text": goal_text,
        "goal_spec_text": goal_spec_text,
        "branch_commit": fetched_branch,
    }


def read_handoff_state(repo: Path, branch: str, *, required: bool = False) -> dict[str, Any] | None:
    path = handoff_state_path(repo, branch)
    if not path.exists():
        if required:
            fail(f"no locally accepted handoff for branch: {branch}")
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"invalid accepted handoff state {path}: {exc}")
    if not isinstance(data, dict) or data.get("branch") != branch:
        fail(f"invalid accepted handoff state for {branch}")
    if data.get("schema_version") != HANDOFF_STATE_SCHEMA_VERSION:
        fail(f"accepted handoff state for {branch} uses an unsupported schema_version")
    validate_handoff_metadata(branch, data.get("metadata"))
    for key in ("handoff_commit", "acceptance_commit"):
        if not isinstance(data.get(key), str) or not re.fullmatch(r"[0-9a-fA-F]{40,64}", data[key]):
            fail(f"invalid accepted handoff state for {branch}: {key}")
    return data


def require_live_accepted_handoff(repo: Path, branch: str) -> dict[str, Any] | None:
    if active_collaboration_model(PROJECT_ROOT) != "cooperative-multi-user":
        return None
    state = read_handoff_state(repo, branch, required=True)
    assert state is not None
    metadata = validate_handoff_metadata(branch, state["metadata"])
    remote = str(load_config().get("remote", "origin"))
    h_ref = handoff_ref(branch)
    branch_remote_ref = f"refs/heads/{branch}"
    live = remote_ref_oids(repo, remote, [h_ref, branch_remote_ref])
    if live[h_ref] != state["acceptance_commit"] or live[branch_remote_ref] != metadata["ready_commit"]:
        fail(
            "LANDING_BLOCKED: accepted handoff is no longer live at its exact remote coordination boundary; "
            "run `land assess --branch <branch>` and resolve with the contributor/integration authority"
        )
    return state


def cmd_handoff_publish(args: argparse.Namespace) -> dict[str, Any]:
    repo = require_repo()
    actor = require_multi_user_actor(repo)
    require_clean(repo)
    branch = args.branch or current_branch(repo)
    if not branch:
        fail("handoff publish requires a named Goal branch")
    branch = require_valid_branch_name(branch, "handoff --branch" if args.branch is not None else "current branch")
    if current_branch(repo) != branch:
        fail(f"switch to Goal branch before publishing handoff: {branch}")
    config = load_config()
    mainline = resolve_mainline(repo, config)
    if branch == mainline:
        fail("cannot publish configured mainline as a Goal handoff")
    goal_text = require_goal_document(repo, branch)
    project_authority = _project_model().require_goal_authority(repo, branch)
    goal_spec_text = None
    if project_authority["project_model"] == "repository-native":
        goal_spec_text = _project_model().goal_spec_document_file(repo, branch).read_text(encoding="utf-8")
    approval = approval_ref(branch)
    if not ref_exists(repo, approval):
        fail(f"handoff publish requires recorded approval: {approval}")
    ready = rev(repo, branch_ref(branch))
    approval_source = rev(repo, approval)
    approved_tree = tree(repo, approval_source)
    if tree(repo, ready) != approved_tree:
        fail("handoff publish requires the current branch full tree to equal the approved tree")
    mainline_head = rev(repo, branch_ref(mainline))
    if not is_ancestor(repo, mainline_head, ready):
        fail(
            "handoff publish requires the Goal branch to contain the current configured mainline; "
            "reconcile/re-check/re-approve before handoff"
        )
    remote = str(config.get("remote", "origin"))
    remote_mainline = remote_head(repo, remote, mainline)
    if remote_mainline is not None and remote_mainline != mainline_head:
        fail(
            f"local {mainline} is not aligned with {remote}/{mainline}: local {mainline_head}, remote {remote_mainline}; "
            "synchronize before publishing handoff"
        )
    h_ref = handoff_ref(branch)
    branch_remote_ref = f"refs/heads/{branch}"
    live = remote_ref_oids(repo, remote, [h_ref, branch_remote_ref])
    existing_handoff = live[h_ref]
    remote_branch = live[branch_remote_ref]
    if existing_handoff is not None:
        # Published handoffs are immutable. Reconciliation creates a new handoff only
        # after an explicit withdrawal of the previous one.
        local_ref = handoff_runtime_ref(branch, "existing-handoff")
        cp = git(["fetch", "--no-tags", remote, f"+{h_ref}:{local_ref}"], repo, check=False)
        if cp.returncode == 0:
            fetched = rev(repo, local_ref)
            if read_acceptance_commit(repo, branch, fetched) is not None:
                delete_handoff_runtime_refs(repo, branch)
                fail(f"published handoff for {branch} has already been accepted by the integration authority")
            old, _, _ = read_handoff_commit(repo, branch, fetched)
            if old["ready_commit"] == ready and old["contributor_actor"] == actor["actor"]:
                delete_handoff_runtime_refs(repo, branch)
                return {
                    "result": "already published",
                    "branch": branch,
                    "handoff_commit": existing_handoff,
                    "ready_commit": ready,
                    "contributor_actor": actor["actor"],
                }
        fail(f"a different immutable handoff already exists for {branch}; withdraw it before republishing")
    if remote_branch is not None and remote_branch != ready:
        fail(
            f"remote Goal branch already exists at a different boundary: {remote}/{branch}={remote_branch}; "
            "published Goal branches are not shared mutable branches"
        )

    metadata = {
        "schema_version": HANDOFF_SCHEMA_VERSION,
        "branch": branch,
        "ready_commit": ready,
        "approved_tree": approved_tree,
        "approval_source_commit": approval_source,
        "handoff_base": mainline_head,
        "contributor_actor": actor["actor"],
        "approval_actor": args.approved_by.strip() if isinstance(args.approved_by, str) and args.approved_by.strip() else None,
        "goal_sha256": hashlib.sha256(goal_text.encode("utf-8")).hexdigest(),
        "project_model": project_authority["project_model"],
        "harness_release": harness_version(),
    }
    if goal_spec_text is not None:
        metadata["goal_spec_sha256"] = hashlib.sha256(goal_spec_text.encode("utf-8")).hexdigest()
    handoff_commit = create_handoff_commit(repo, metadata, goal_text, goal_spec_text)
    candidate_ref = handoff_runtime_ref(branch, "publish-candidate")
    update_ref(repo, candidate_ref, handoff_commit)
    # Publication is create-only: the empty-lease form requires each created ref to be
    # absent at the remote, so two racing publications cannot both claim the branch.
    leases = [f"--force-with-lease={h_ref}:"]
    push_specs = []
    if remote_branch is None:
        leases.append(f"--force-with-lease={branch_remote_ref}:")
        push_specs.append(f"{ready}:{branch_remote_ref}")
    push_specs.append(f"{candidate_ref}:{h_ref}")
    cp = git(["push", "--atomic", *leases, remote, *push_specs], repo, check=False)
    if cp.returncode != 0:
        delete_handoff_runtime_refs(repo, branch)
        fail(f"cannot publish immutable Goal handoff: {cp.stderr.strip() or cp.stdout.strip()}")
    delete_handoff_runtime_refs(repo, branch)
    return {
        "result": "published",
        "branch": branch,
        "handoff_ref": h_ref,
        "handoff_commit": handoff_commit,
        "ready_commit": ready,
        "handoff_base": mainline_head,
        "contributor_actor": actor["actor"],
        "approval_actor": metadata["approval_actor"],
        "rule": "handoff is immutable until explicitly withdrawn; remote Goal branch is exclusive to this handoff",
    }


def cmd_handoff_withdraw(args: argparse.Namespace) -> dict[str, Any]:
    repo = require_repo()
    actor = require_multi_user_actor(repo)
    branch = require_valid_branch_name(args.branch, "handoff --branch")
    remote = str(load_config().get("remote", "origin"))
    h_ref = handoff_ref(branch)
    live = remote_ref_oids(repo, remote, [h_ref])
    if live[h_ref] is None:
        return {"result": "already absent", "branch": branch}
    handoff = fetch_remote_handoff(repo, branch)
    if handoff["acceptance_commit"] is not None:
        fail(
            f"handoff for {branch} is accepted by the integration authority; it must be released or landed before contributor withdrawal"
        )
    handoff_oid = handoff["handoff_commit"]
    branch_oid = handoff["branch_commit"]
    metadata = handoff["metadata"]
    if metadata["contributor_actor"] != actor["actor"]:
        fail(
            f"handoff contributor is {metadata['contributor_actor']!r}, not current actor {actor['actor']!r}; "
            "trusted coordination still requires the publishing contributor to withdraw its handoff"
        )

    # Withdrawal deletes the handoff ref and its exclusive Goal branch in one atomic
    # push. The lease on the handoff ref is the acceptance guard: acceptance replaces
    # the handoff commit with an acceptance commit on that same ref, so a concurrent
    # acceptance makes this lease fail and nothing is withdrawn.
    branch_remote_ref = f"refs/heads/{branch}"
    cp = git(
        [
            "push",
            "--atomic",
            f"--force-with-lease={branch_remote_ref}:{branch_oid}",
            f"--force-with-lease={h_ref}:{handoff_oid}",
            remote,
            f":{branch_remote_ref}",
            f":{h_ref}",
        ],
        repo,
        check=False,
    )
    if cp.returncode != 0:
        after = remote_ref_oids(repo, remote, [branch_remote_ref, h_ref])
        after_branch = after[branch_remote_ref]
        after_handoff = after[h_ref]
        if after_branch is None and after_handoff is None:
            pass
        elif after_handoff is not None and after_handoff != handoff_oid:
            delete_handoff_runtime_refs(repo, branch)
            fail(
                f"handoff for {branch} changed during withdrawal (for example, it was accepted concurrently by the "
                f"integration authority); nothing was withdrawn. Live handoff ref: {after_handoff}"
            )
        elif after_branch != branch_oid or after_handoff != handoff_oid:
            fail(
                f"published handoff boundary moved during withdrawal for {branch}; "
                f"remote branch={after_branch}, handoff={after_handoff}; refusing ambiguous cleanup"
            )
        else:
            fail(f"cannot atomically withdraw handoff for {branch}: {cp.stderr.strip() or cp.stdout.strip()}")
    delete_handoff_runtime_refs(repo, branch)
    return {"result": "withdrawn", "branch": branch, "handoff_commit": handoff_oid, "ready_commit": branch_oid}


def cmd_handoff_accept(args: argparse.Namespace) -> dict[str, Any]:
    repo = require_repo()
    actor = require_integration_authority(repo)
    assert actor is not None
    require_clean(repo)
    branch = require_valid_branch_name(args.branch, "handoff --branch")
    existing = read_handoff_state(repo, branch, required=False)
    handoff = fetch_remote_handoff(repo, branch)
    fetched = handoff["handoff_commit"]
    metadata = handoff["metadata"]
    active_project = _project_model().active_project_model(PROJECT_ROOT)
    if active_project != metadata["project_model"]:
        fail(
            f"handoff Project model {metadata['project_model']!r} does not match integration workspace "
            f"Project model {active_project!r}; align composition before acceptance"
        )
    goal_text = handoff["goal_text"]
    goal_spec_text = handoff.get("goal_spec_text")
    branch_oid = handoff["branch_commit"]
    live_acceptance = handoff["acceptance_commit"]
    acceptance_data = handoff["acceptance"]
    if acceptance_data is not None and acceptance_data["integration_actor"] != actor["actor"]:
        fail(
            f"handoff for {branch} is already accepted by integration authority "
            f"{acceptance_data['integration_actor']!r}; only one integration-authority workspace may hold it"
        )
    if existing is not None:
        if existing.get("handoff_commit") == fetched and existing.get("acceptance_commit") == live_acceptance:
            return {
                "result": "already accepted",
                "branch": branch,
                "handoff_commit": fetched,
                "acceptance_commit": live_acceptance,
                "metadata": metadata,
            }
        fail(f"a different handoff is already accepted locally for {branch}; release it before accepting another")
    remote = handoff["remote"]
    h_ref = handoff_ref(branch)

    # Preflight every local import boundary before publishing the remote
    # acceptance. This prevents an ordinary local naming/state conflict
    # from transferring handoff ownership to an integration workspace that
    # cannot reconstruct the exact accepted Goal.
    if ref_exists(repo, branch_ref(branch)) and rev(repo, branch_ref(branch)) != branch_oid:
        fail(f"local branch {branch} already exists at a different boundary; release/rename it before handoff acceptance")
    approval = approval_ref(branch)
    if ref_exists(repo, approval) and rev(repo, approval) != metadata["approval_source_commit"]:
        fail(f"local approval ref already exists at a different boundary for {branch}")
    goal_path = goal_document_path(branch)
    ignore = git(["check-ignore", "--quiet", "--", goal_path], repo, check=False)
    if ignore.returncode != 0:
        fail(f"cannot materialize transferred Goal recovery state because it is not Git-ignored: {goal_path}")
    goal_file = goal_document_file(repo, branch)
    if goal_file.exists() and goal_file.read_text(encoding="utf-8") != goal_text:
        fail(f"local Goal recovery state differs from published handoff: {goal_path}")
    goal_spec_file = _project_model().goal_spec_document_file(repo, branch)
    if metadata["project_model"] == "repository-native":
        goal_spec_path = _project_model().goal_spec_document_path(branch)
        ignore = git(["check-ignore", "--quiet", "--", goal_spec_path], repo, check=False)
        if ignore.returncode != 0:
            fail(f"cannot materialize transferred Goal Spec because it is not Git-ignored: {goal_spec_path}")
        if goal_spec_text is None:
            fail(f"published repository-native handoff has no Goal Spec: {goal_spec_path}")
        if goal_spec_file.exists() and goal_spec_file.read_text(encoding="utf-8") != goal_spec_text:
            fail(f"local Goal Spec differs from published handoff: {goal_spec_path}")

    if live_acceptance is None:
        # Acceptance is one compare-and-swap on the handoff ref: it replaces the exact
        # published handoff commit with an acceptance commit whose parent is that handoff.
        # A concurrent contributor withdrawal leases the same ref, so exactly one wins.
        acceptance_commit = create_acceptance_commit(repo, branch, fetched, actor["actor"])
        update_ref(repo, handoff_runtime_ref(branch, "acceptance"), acceptance_commit)
        cp = git(
            ["push", f"--force-with-lease={h_ref}:{fetched}", remote, f"{acceptance_commit}:{h_ref}"],
            repo,
            check=False,
        )
        if cp.returncode != 0:
            after = remote_ref_oids(repo, remote, [h_ref])[h_ref]
            delete_handoff_runtime_refs(repo, branch)
            if after is None:
                fail(f"handoff for {branch} was withdrawn by its contributor before acceptance completed; nothing was accepted")
            if after != fetched:
                fail(f"handoff for {branch} changed during acceptance (live handoff ref {after}); nothing was accepted")
            fail(f"cannot record handoff acceptance for {branch}: {cp.stderr.strip() or cp.stdout.strip()}")
    else:
        # Idempotent retry after an interruption between remote acceptance and local import.
        acceptance_commit = live_acceptance
        update_ref(repo, handoff_runtime_ref(branch, "acceptance"), acceptance_commit)
    if not ref_exists(repo, branch_ref(branch)):
        update_ref(repo, branch_ref(branch), branch_oid)
    if not ref_exists(repo, approval):
        update_ref(repo, approval, metadata["approval_source_commit"])
    if not goal_file.exists():
        goal_file.parent.mkdir(parents=True, exist_ok=True)
        goal_file.write_text(goal_text, encoding="utf-8")
    if metadata["project_model"] == "repository-native" and not goal_spec_file.exists():
        goal_spec_file.parent.mkdir(parents=True, exist_ok=True)
        goal_spec_file.write_text(goal_spec_text or "", encoding="utf-8")
    state = {
        "schema_version": HANDOFF_STATE_SCHEMA_VERSION,
        "branch": branch,
        "handoff_commit": fetched,
        "acceptance_commit": acceptance_commit,
        "metadata": metadata,
        "integration_actor": actor["actor"],
    }
    atomic_json(handoff_state_path(repo, branch), state)
    if current_branch(repo) != branch:
        git(["switch", branch], repo)
    return {
        "result": "accepted",
        "branch": branch,
        "handoff_commit": fetched,
        "acceptance_commit": acceptance_commit,
        "ready_commit": branch_oid,
        "contributor_actor": metadata["contributor_actor"],
        "approval_actor": metadata.get("approval_actor"),
        "integration_actor": actor["actor"],
        "next": "run `land assess --branch <branch>` before landing preparation",
    }


def cmd_handoff_release(args: argparse.Namespace) -> dict[str, Any]:
    repo = require_repo()
    require_integration_authority(repo)
    require_clean(repo)
    branch = require_valid_branch_name(args.branch, "handoff --branch")
    state = read_handoff_state(repo, branch, required=True)
    assert state is not None
    metadata = validate_handoff_metadata(branch, state["metadata"])
    if land_state_path(repo, branch).exists():
        fail(f"cannot release accepted handoff while a landing transaction exists for {branch}; abort ready landing first")

    config = load_config()
    mainline = resolve_mainline(repo, config)
    remote = str(config.get("remote", "origin"))
    h_ref = handoff_ref(branch)
    handoff_oid = state["handoff_commit"]
    acceptance_oid = state["acceptance_commit"]
    live_tip = remote_ref_oids(repo, remote, [h_ref])[h_ref]
    if live_tip not in (acceptance_oid, handoff_oid, None):
        fail(f"cannot release accepted handoff because the remote handoff ref moved for {branch}: {live_tip}")

    # While the remote still holds this workspace's acceptance, require the complete
    # exact imported state. Once the handoff ref is back at the published handoff (or
    # already withdrawn afterwards), a release operation may have been interrupted during
    # local cleanup, so missing local pieces are treated as already-cleaned while any
    # surviving piece must still match the transferred boundary exactly.
    release_started = live_tip != acceptance_oid
    local_branch = rev(repo, branch_ref(branch)) if ref_exists(repo, branch_ref(branch)) else None
    approval = approval_ref(branch)
    local_approval = rev(repo, approval) if ref_exists(repo, approval) else None
    goal_file = goal_document_file(repo, branch)
    local_goal = goal_file.read_text(encoding="utf-8") if goal_file.exists() else None
    goal_spec_file = _project_model().goal_spec_document_file(repo, branch)
    local_goal_spec = goal_spec_file.read_text(encoding="utf-8") if goal_spec_file.exists() else None
    if local_branch is not None and local_branch != metadata["ready_commit"]:
        fail(f"cannot release accepted handoff because local branch {branch} moved from imported ready boundary")
    if local_approval is not None and local_approval != metadata["approval_source_commit"]:
        fail(f"cannot release accepted handoff because local approval boundary changed for {branch}")
    if local_goal is not None and hashlib.sha256(local_goal.encode("utf-8")).hexdigest() != metadata["goal_sha256"]:
        fail(f"cannot release accepted handoff because local Goal recovery state changed for {branch}")
    if metadata["project_model"] == "repository-native":
        if local_goal_spec is not None and hashlib.sha256(local_goal_spec.encode("utf-8")).hexdigest() != metadata["goal_spec_sha256"]:
            fail(f"cannot release accepted handoff because local Goal Spec changed for {branch}")
        if not release_started and local_goal_spec is None:
            fail(f"cannot release accepted repository-native handoff because local Goal Spec is missing for {branch}")
    if not release_started and (local_branch is None or local_approval is None or local_goal is None):
        fail(f"cannot release accepted handoff because its local imported state is incomplete for {branch}")

    if current_branch(repo) == branch:
        git(["switch", mainline], repo)
    if live_tip == acceptance_oid:
        # Compare-and-swap the handoff ref back to the exact published handoff commit.
        cp = git(
            ["push", f"--force-with-lease={h_ref}:{acceptance_oid}", remote, f"{handoff_oid}:{h_ref}"],
            repo,
            check=False,
        )
        if cp.returncode != 0:
            after = remote_ref_oids(repo, remote, [h_ref])[h_ref]
            if after != handoff_oid:
                fail(
                    f"cannot release accepted handoff for {branch}: remote handoff ref is {after}; "
                    f"{cp.stderr.strip() or cp.stdout.strip()}"
                )
    if ref_exists(repo, approval):
        update_ref(repo, approval, None, metadata["approval_source_commit"])
    if ref_exists(repo, branch_ref(branch)):
        update_ref(repo, branch_ref(branch), None, metadata["ready_commit"])
    if goal_file.exists():
        delete_goal_document(repo, branch)
    _project_model().delete_goal_spec_document(repo, branch)
    handoff_state_path(repo, branch).unlink(missing_ok=True)
    delete_handoff_runtime_refs(repo, branch)
    return {
        "result": "released",
        "branch": branch,
        "handoff_commit": handoff_oid,
        "remote_handoff_retained": live_tip is not None,
        "next": "publishing contributor may now withdraw/reconcile the immutable handoff",
    }



def active_collaboration_model(root: Path) -> str:
    """Return the selected Collaboration model, failing closed on invalid composition.

    Lifecycle semantics differ materially between single-user and cooperative operation.
    An unreadable, malformed, missing, or unknown selection therefore cannot safely inherit
    single-user behavior. Only models whose runtime semantics are implemented by this release
    are accepted here.
    """
    path = root / ".harness" / "composition" / "active.json"
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"invalid Harness composition collaboration model: cannot read {path}: {exc}")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f"invalid Harness composition collaboration model: malformed JSON in {path}: {exc}")
    if not isinstance(data, dict):
        fail("invalid Harness composition collaboration model: active.json must contain a JSON object")
    if data.get("schema_version") != COMPOSITION_SCHEMA_VERSION:
        fail(
            "invalid Harness composition collaboration model: "
            f"unsupported schema_version {data.get('schema_version')!r}; expected {COMPOSITION_SCHEMA_VERSION}"
        )
    selection = data.get("selection")
    if not isinstance(selection, dict):
        fail("invalid Harness composition collaboration model: selection must be a JSON object")
    model = selection.get("collaboration_model")
    if not isinstance(model, str) or not model.strip():
        fail("invalid Harness composition collaboration model: selection.collaboration_model must be a non-empty string")
    if model != model.strip():
        fail("invalid Harness composition collaboration model: selection.collaboration_model must not contain surrounding whitespace")
    if model not in SUPPORTED_COLLABORATION_MODELS:
        supported = ", ".join(sorted(SUPPORTED_COLLABORATION_MODELS))
        fail(
            "invalid Harness composition collaboration model: "
            f"unsupported active model {model!r}; runtime-supported models are: {supported}"
        )
    return model


def collaboration_state_path(repo: Path) -> Path:
    return git_common_dir(repo) / "harness" / "collaboration.json"


def read_collaboration_state(repo: Path, *, required: bool = False) -> dict[str, Any] | None:
    path = collaboration_state_path(repo)
    if not path.exists():
        if required:
            fail(
                "cooperative multi-user collaboration requires local actor configuration; "
                "run `collaboration configure --actor <name> --role contributor|integration-authority`"
            )
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"invalid local collaboration state {path}: {exc}")
    if not isinstance(data, dict) or data.get("schema_version") != COLLABORATION_STATE_SCHEMA_VERSION:
        fail(f"invalid local collaboration state {path}: unsupported schema")
    actor = data.get("actor")
    role = data.get("role")
    if not isinstance(actor, str) or not actor.strip():
        fail(f"invalid local collaboration state {path}: actor must be non-empty")
    if role not in {"contributor", "integration-authority"}:
        fail(f"invalid local collaboration state {path}: unsupported role {role!r}")
    return {"schema_version": COLLABORATION_STATE_SCHEMA_VERSION, "actor": actor.strip(), "role": role}


def require_multi_user_actor(repo: Path) -> dict[str, Any]:
    if active_collaboration_model(PROJECT_ROOT) != "cooperative-multi-user":
        fail("handoff/collaboration actor mechanics require the active Collaboration model `cooperative-multi-user`")
    state = read_collaboration_state(repo, required=True)
    assert state is not None
    return state


def require_integration_authority(repo: Path) -> dict[str, Any] | None:
    if active_collaboration_model(PROJECT_ROOT) != "cooperative-multi-user":
        return None
    state = read_collaboration_state(repo, required=True)
    assert state is not None
    if state["role"] != "integration-authority":
        fail(
            "LANDING_BLOCKED: cooperative multi-user landing is restricted to the configured "
            "integration-authority workspace"
        )
    return state


def cmd_collaboration_configure(args: argparse.Namespace) -> dict[str, Any]:
    repo = require_repo()
    if active_collaboration_model(PROJECT_ROOT) != "cooperative-multi-user":
        fail("local actor roles are only used by the `cooperative-multi-user` Collaboration model")
    actor = str(args.actor).strip()
    if not actor or any(ch in actor for ch in "\r\n\0"):
        fail("collaboration actor must be non-empty plain text")
    data = {
        "schema_version": COLLABORATION_STATE_SCHEMA_VERSION,
        "actor": actor,
        "role": args.role,
    }
    atomic_json(collaboration_state_path(repo), data)
    return {"result": "configured", **data, "scope": "local Git common directory; coordination metadata, not authorization"}


def cmd_collaboration_status(args: argparse.Namespace) -> dict[str, Any]:
    repo = require_repo()
    model = active_collaboration_model(PROJECT_ROOT)
    state = read_collaboration_state(repo, required=False)
    return {
        "result": "configured" if state else "unconfigured",
        "collaboration_model": model,
        "local_actor": state,
        "security_boundary": "actor/role metadata is a trusted-coordination guardrail, not cryptographic authorization",
    }


