#!/usr/bin/env python3
"""Project-model runtime mechanics.

Owns active Project-model selection, repository-native transient Goal-Spec state,
and the Spec model's stable authority-scope topology. It may use low-level
repository facts but does not own universal lifecycle mechanics.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable

from kernel import PROJECT_ROOT, fail, require_repo, current_branch, require_valid_branch_name

SPEC_TOPOLOGY_SCHEMA_VERSION = 1
SPEC_TOPOLOGY_MANIFEST = Path("doc/spec/topology.json")
SPEC_AUTHORITIES = ("domain", "app", "style", "tech")
SPEC_SCOPE_ID_RE = re.compile(r"^(domain|app|style|tech)\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)*$")
def active_project_model(root: Path) -> str | None:
    """Return the selected Project model when composition is readable."""
    path = root / ".harness" / "composition" / "active.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    selection = data.get("selection") if isinstance(data, dict) else None
    model = selection.get("project_model") if isinstance(selection, dict) else None
    return model if isinstance(model, str) and model else None




REPOSITORY_NATIVE_MODEL = "repository-native"
GOAL_SPEC_SUFFIX = ".spec.md"

def goal_spec_document_path(branch: str) -> str:
    """Return the branch-derived transient repository-native Goal Spec path."""
    return f"doc/goals/{branch}{GOAL_SPEC_SUFFIX}"


def goal_spec_document_file(repo: Path, branch: str) -> Path:
    return repo / goal_spec_document_path(branch)


def goal_authority_state(repo: Path, branch: str) -> dict[str, Any]:
    """Report whether the active Project model has the Goal-local authority it requires."""
    model = active_project_model(PROJECT_ROOT)
    if model == "spec":
        return {
            "project_model": model,
            "authority_kind": "stable-spec-scopes",
            "required_goal_local_artifact": None,
            "ready": True,
        }
    if model == REPOSITORY_NATIVE_MODEL:
        path = goal_spec_document_file(repo, branch)
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            text = ""
        except OSError as exc:
            fail(f"cannot read repository-native Goal Spec {goal_spec_document_path(branch)}: {exc}")
        return {
            "project_model": model,
            "authority_kind": "transient-goal-spec",
            "goal_spec_path": goal_spec_document_path(branch),
            "goal_spec_exists": path.is_file(),
            "goal_spec_nonempty": bool(text.strip()),
            "ready": bool(text.strip()),
        }
    fail(f"unsupported active Project model: {model!r}")


def require_goal_authority(repo: Path, branch: str) -> dict[str, Any]:
    state = goal_authority_state(repo, branch)
    if not state.get("ready"):
        fail(
            "repository-native work requires a non-empty transient Goal Spec before approval/landing: "
            f"{state.get('goal_spec_path')}"
        )
    return state


def delete_goal_spec_document(repo: Path, branch: str) -> None:
    """Remove transient repository-native Goal Spec state after durable Goal completion."""
    path = goal_spec_document_file(repo, branch)
    try:
        path.unlink()
    except FileNotFoundError:
        return
    except OSError as exc:
        fail(f"cannot remove completed Goal Spec {path}: {exc}")
    stop = repo / "doc" / "goals"
    parent = path.parent
    while parent != stop and parent != repo:
        try:
            parent.rmdir()
        except OSError:
            break
        parent = parent.parent


def cmd_project_status(args: argparse.Namespace) -> dict[str, Any]:
    """Report active Project-model authority placement for the current/selected Goal branch."""
    repo = require_repo()
    branch = args.branch or current_branch(repo)
    if not branch:
        fail("project status requires a named branch")
    branch = require_valid_branch_name(branch, "project --branch" if args.branch is not None else "current branch")
    state = goal_authority_state(repo, branch)
    result = {"result": "resolved", "branch": branch, **state}
    if state["project_model"] == "spec":
        result["topology_manifest"] = SPEC_TOPOLOGY_MANIFEST.as_posix()
    return result

def validate_spec_scope_path(value: Any) -> str | None:
    """Return a normalized safe project-relative Markdown path or None."""
    if not isinstance(value, str) or not value or "\\" in value:
        return None
    path = Path(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        return None
    if value.startswith(".harness/") or path.suffix.lower() != ".md":
        return None
    return path.as_posix()


def spec_topology_state(root: Path) -> dict[str, Any]:
    """Read and mechanically validate the active Spec topology.

    This grades Project-model topology only when explicitly invoked by the Spec
    commands. Harness `check` intentionally does not call it, preserving the
    Harness-vs-Project Assurance boundary.
    """
    manifest_path = root / SPEC_TOPOLOGY_MANIFEST
    findings: list[str] = []

    if manifest_path.exists():
        mode = "explicit"
        try:
            raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raw = {}
            findings.append(f"invalid Spec topology manifest JSON: {exc}")
    else:
        mode = "unconfigured"
        raw = {
            "schema_version": SPEC_TOPOLOGY_SCHEMA_VERSION,
            "project_model": "spec",
            "scopes": [],
        }

    if not isinstance(raw, dict):
        findings.append("Spec topology manifest must be a JSON object")
        raw = {}
    if raw.get("schema_version") != SPEC_TOPOLOGY_SCHEMA_VERSION:
        findings.append(f"Spec topology manifest must use schema_version {SPEC_TOPOLOGY_SCHEMA_VERSION}")
    if raw.get("project_model") != "spec":
        findings.append("Spec topology manifest project_model must be `spec`")

    rows = raw.get("scopes", [])
    if not isinstance(rows, list):
        findings.append("Spec topology manifest scopes must be a list")
        rows = []

    scopes: dict[str, dict[str, Any]] = {}
    paths: dict[str, str] = {}
    for index, row in enumerate(rows):
        label = f"Spec topology scope[{index}]"
        if not isinstance(row, dict):
            findings.append(f"{label} must be an object")
            continue
        scope_id = row.get("id")
        authority = row.get("authority")
        rel = validate_spec_scope_path(row.get("path"))
        depends_on = row.get("depends_on", [])
        if not isinstance(scope_id, str) or not SPEC_SCOPE_ID_RE.fullmatch(scope_id):
            findings.append(f"{label} has invalid stable scope id: {scope_id!r}")
            continue
        if scope_id in scopes:
            findings.append(f"duplicate Spec scope id: {scope_id}")
            continue
        if authority not in SPEC_AUTHORITIES:
            findings.append(f"{scope_id} has invalid authority: {authority!r}")
        elif not scope_id.startswith(authority + "."):
            findings.append(f"{scope_id} authority must match its scope-id prefix: {authority}")
        if rel is None:
            findings.append(f"{scope_id} has invalid project-relative Markdown path: {row.get('path')!r}")
        elif rel in paths:
            findings.append(f"Spec scope paths must be unique: {paths[rel]} and {scope_id} -> {rel}")
        else:
            paths[rel] = scope_id
            if mode == "explicit" and not (root / rel).is_file():
                findings.append(f"Spec scope document is missing for {scope_id}: {rel}")
        if not isinstance(depends_on, list) or any(not isinstance(item, str) or not item for item in depends_on):
            findings.append(f"{scope_id} depends_on must be a list of non-empty scope ids")
            depends_on = []
        elif len(set(depends_on)) != len(depends_on):
            findings.append(f"{scope_id} depends_on must not contain duplicates")
        if scope_id in depends_on:
            findings.append(f"{scope_id} must not depend on itself")
        scopes[scope_id] = {
            "id": scope_id,
            "authority": authority,
            "path": rel or row.get("path"),
            "depends_on": list(depends_on),
        }

    for scope_id, row in scopes.items():
        for dependency in row["depends_on"]:
            if dependency not in scopes:
                findings.append(f"{scope_id} depends on unknown Spec scope: {dependency}")


    reverse: dict[str, list[str]] = {scope_id: [] for scope_id in scopes}
    for scope_id, row in scopes.items():
        for dependency in row["depends_on"]:
            if dependency in reverse:
                reverse[dependency].append(scope_id)
    for values in reverse.values():
        values.sort()

    return {
        "result": "findings" if findings else ("unconfigured" if mode == "unconfigured" else "valid"),
        "mode": mode,
        "manifest": SPEC_TOPOLOGY_MANIFEST.as_posix(),
        "finding_count": len(findings),
        "findings": findings,
        "scopes": [scopes[key] for key in sorted(scopes)],
        "reverse_dependencies": reverse,
    }


def scope_closure(scopes: dict[str, dict[str, Any]], seeds: Iterable[str], *, reverse: bool = False) -> list[str]:
    edges: dict[str, list[str]]
    if reverse:
        edges = {scope_id: [] for scope_id in scopes}
        for scope_id, row in scopes.items():
            for dependency in row.get("depends_on", []):
                if dependency in edges:
                    edges[dependency].append(scope_id)
    else:
        edges = {scope_id: list(row.get("depends_on", [])) for scope_id, row in scopes.items()}

    seen: set[str] = set()
    pending = list(seeds)
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        pending.extend(edges.get(current, []))
    return sorted(seen)


def cmd_spec_topology(args: argparse.Namespace) -> dict[str, Any]:
    if active_project_model(PROJECT_ROOT) != "spec":
        fail("`spec` commands require the active Project model to be `spec`")
    return spec_topology_state(PROJECT_ROOT)


def cmd_spec_affected(args: argparse.Namespace) -> dict[str, Any]:
    if active_project_model(PROJECT_ROOT) != "spec":
        fail("`spec` commands require the active Project model to be `spec`")
    state = spec_topology_state(PROJECT_ROOT)
    if state["finding_count"]:
        fail("Spec topology has findings; run `spec topology` and repair them first")
    if state["mode"] == "unconfigured":
        fail("Spec topology is unconfigured; establish doc/spec/topology.json")

    scopes = {row["id"]: row for row in state["scopes"]}
    requested = list(dict.fromkeys(args.scope))
    unknown = sorted(set(requested) - set(scopes))
    if unknown:
        fail("unknown Spec scope id(s): " + ", ".join(unknown))
    dependencies = scope_closure(scopes, requested)
    dependents = scope_closure(scopes, requested, reverse=True)
    graph = sorted(set(dependencies) | set(dependents))
    by_id = scopes
    return {
        "result": "resolved",
        "mode": state["mode"],
        "requested": requested,
        "load_scopes": dependencies,
        "impact_scopes": dependents,
        "graph_check_scopes": graph,
        "load_paths": [by_id[scope_id]["path"] for scope_id in dependencies],
        "graph_check_paths": [by_id[scope_id]["path"] for scope_id in graph],
        "rule": "load=requested+transitive dependencies; impact=requested+transitive reverse dependents; graph-check=union",
    }


