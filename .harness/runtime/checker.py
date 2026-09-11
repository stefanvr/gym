#!/usr/bin/env python3
"""Deterministic Harness checker and Assurance evidence validation.

Owns structural findings, composition/model contract checks, semantic-evidence
validation, and the `check` / `assure` commands.
"""
from __future__ import annotations

import argparse
import ast
import contextlib
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable

from kernel import HarnessError, PROJECT_ROOT, fail, load_config, run
from project_model import active_project_model
from collaboration_model import active_collaboration_model

def yaml_manifest_paths(text: str) -> list[str]:
    # The manifest intentionally contains only scalar path values. This small parser avoids a
    # runtime dependency while still checking every .harness path appearing as a scalar value/list item.
    paths: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("- "):
            value = line[2:].strip().strip('"\'')
        elif ":" in line:
            value = line.split(":", 1)[1].strip().strip('"\'')
        else:
            continue
        if value.startswith(".harness/"):
            paths.append(value)
    return paths


def yaml_scalar_tree(text: str) -> dict[str, str]:
    """Map dotted key paths to scalar values for the manifest's simple nested YAML subset."""
    result: dict[str, str] = {}
    containers: set[str] = set()
    stack: list[tuple[int, str]] = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("- ") or ":" not in stripped:
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        key, value = stripped.split(":", 1)
        key = key.strip().strip('"\'')
        value = value.strip().strip('"\'')
        while stack and stack[-1][0] >= indent:
            stack.pop()
        path = ".".join([name for _, name in stack] + [key])
        if value:
            result[path] = value
        else:
            containers.add(path)
            stack.append((indent, key))
    for path in containers:
        result.setdefault(path, "")
    return result


def manifest_composition_findings(root: Path) -> list[str]:
    """Keep composition selection single-sourced in active.json ([AUTH-02]).

    The context manifest may inventory every supported model/method definition, but it
    must not restate which ones are active or supported; agents resolve the selection
    from `.harness/composition/active.json`.
    """
    findings: list[str] = []
    manifest = root / ".harness" / "workflow" / "context-manifest.yaml"
    active_path = root / ".harness" / "composition" / "active.json"
    if not manifest.exists() or not active_path.exists():
        return findings
    tree_map = yaml_scalar_tree(manifest.read_text(encoding="utf-8"))
    for path in sorted(tree_map):
        if any(segment.startswith(("active_", "supported_")) for segment in path.split(".")):
            findings.append(
                f"context manifest restates composition selection at `{path}`; "
                "selection is owned only by .harness/composition/active.json"
            )
    try:
        active = json.loads(active_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return findings  # composition_findings reports the invalid file
    sources = active.get("sources") if isinstance(active, dict) else None
    if not isinstance(sources, dict):
        return findings
    for dimension in ("project_models", "collaboration_models"):
        expected = sources.get(dimension)
        if not isinstance(expected, dict):
            continue
        prefix = f"composition.{dimension}."
        listed = {
            path[len(prefix):]: value
            for path, value in tree_map.items()
            if path.startswith(prefix) and "." not in path[len(prefix):] and value
        }
        if listed != expected:
            findings.append(
                f"context manifest composition.{dimension} inventory {listed} does not match "
                f"active.json sources.{dimension} {expected}"
            )
    method_sources = sources.get("method_packs")
    if isinstance(method_sources, dict):
        listed_methods = {value for path, value in tree_map.items() if path.startswith("methods.") and value}
        if listed_methods != set(method_sources.values()):
            findings.append(
                "context manifest methods inventory does not match active.json sources.method_packs: "
                f"{sorted(listed_methods)} != {sorted(method_sources.values())}"
            )
    return findings


def assurance_profile_findings(root: Path) -> list[str]:
    """Require an explicit Assurance operating profile for every supported Collaboration model."""
    findings: list[str] = []
    assurance = root / ".harness" / "harness-assurance.md"
    active_path = root / ".harness" / "composition" / "active.json"
    if not assurance.exists() or not active_path.exists():
        return findings
    try:
        active = json.loads(active_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return findings
    supported = active.get("supported", {}).get("collaboration_models") if isinstance(active, dict) else None
    if not isinstance(supported, list):
        return findings
    text = assurance.read_text(encoding="utf-8")
    for model in supported:
        if f"### Operating profile: `{model}`" not in text:
            findings.append(
                f"Harness Assurance defines no operating profile for supported Collaboration model `{model}`; "
                "a model must not inherit another model's assured profile"
            )
    return findings


def markdown_relative_links(text: str) -> list[str]:
    result = []
    for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
        target = target.split("#", 1)[0].strip()
        if not target or "://" in target or target.startswith("mailto:") or target.startswith("#"):
            continue
        result.append(target)
    return result


def skill_contract_findings(root: Path) -> list[str]:
    required = ["Define", "Inputs", "Outputs", "Owns", "Modes", "Completion", "Approval", "Invariants"]
    findings = []
    for path in sorted((root / ".harness" / "skills").rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        heads = set(re.findall(r"(?m)^##\s+(.+?)\s*$", text))
        missing = [name for name in required if name not in heads]
        if missing:
            findings.append(f"{path.relative_to(root)} missing skill contract sections: {', '.join(missing)}")
    return findings


def method_pack_contract_findings(root: Path) -> list[str]:
    """Validate shipped first-class method definitions against the method-pack contract."""
    required = ["Purpose", "Inputs", "Working outputs", "Authority interaction", "Invocation", "Method", "Completion", "Invariants"]
    findings: list[str] = []
    methods_root = root / ".harness" / "methods"
    if not methods_root.exists():
        return ["missing first-class method directory: .harness/methods"]
    for path in sorted(methods_root.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        heads = set(re.findall(r"(?m)^##\s+(.+?)\s*$", text))
        missing = [name for name in required if name not in heads]
        if missing:
            findings.append(f"{path.relative_to(root)} missing method-pack contract sections: {', '.join(missing)}")
    return findings


def authority_orchestrator_findings(root: Path) -> list[str]:
    """Validate the active Spec authority orchestrators without making the kernel assume Spec forever."""
    active_path = root / ".harness" / "composition" / "active.json"
    if not active_path.exists():
        return []
    try:
        active = json.loads(active_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []  # composition_findings owns malformed composition diagnostics
    selection = active.get("selection") if isinstance(active, dict) else None
    if not isinstance(selection, dict) or selection.get("project_model") != "spec":
        return []
    findings: list[str] = []
    contract_ref = "Authority Orchestrator Contract"
    for name in ("domain", "app", "style", "tech"):
        path = root / ".harness" / "capabilities" / f"{name}.md"
        if not path.exists():
            findings.append(f"Spec authority orchestrator is missing: {path.relative_to(root)}")
            continue
        text = path.read_text(encoding="utf-8")
        if not re.search(r"(?m)^##\s+Orchestration\s*$", text):
            findings.append(f"{path.relative_to(root)} missing authority-orchestrator Orchestration section")
        if contract_ref not in text:
            findings.append(f"{path.relative_to(root)} does not reference the Authority Orchestrator Contract")
    return findings


def wrapper_findings(root: Path) -> list[str]:
    findings = []
    skills_root = root / ".claude" / "skills"
    if skills_root.is_dir():
        for directory in sorted(path for path in skills_root.iterdir() if path.is_dir()):
            if not (directory / "SKILL.md").is_file():
                findings.append(f"{directory.relative_to(root).as_posix()} is a Claude skill directory without SKILL.md")
    wrappers = sorted(skills_root.glob("*/SKILL.md"))
    references: dict[str, list[Path]] = {}
    for path in wrappers:
        text = path.read_text(encoding="utf-8")
        candidates = re.findall(r"\.harness/skills/[A-Za-z0-9_./-]+\.md", text)
        unique = sorted(set(candidates))
        if len(unique) != 1:
            findings.append(f"{path.relative_to(root)} should point to exactly one authoritative skill; found {unique}")
            continue
        target = unique[0]
        if not (root / target).exists():
            findings.append(f"{path.relative_to(root)} points to missing {target}")
            continue
        references.setdefault(target, []).append(path)
    authoritative = sorted((root / ".harness" / "skills").rglob("*.md"))
    authoritative_refs = {path.relative_to(root).as_posix() for path in authoritative}
    for target, paths in sorted(references.items()):
        if len(paths) > 1:
            wrappers_text = ", ".join(str(path.relative_to(root)) for path in paths)
            findings.append(f"authoritative skill {target} has duplicate Claude wrappers: {wrappers_text}")
    for target in sorted(authoritative_refs - set(references)):
        findings.append(f"authoritative skill {target} has no Claude wrapper")
    if len(wrappers) != len(authoritative):
        findings.append(f"Claude wrapper count {len(wrappers)} != authoritative skill count {len(authoritative)}")
    return findings


def link_findings(root: Path) -> list[str]:
    findings = []
    paths = list((root / ".harness").rglob("*.md")) + list((root / ".claude").rglob("*.md"))
    paths += [root / name for name in ("AGENTS.md", "CLAUDE.md", "GEMINI.md") if (root / name).exists()]
    for path in sorted(set(paths)):
        text = path.read_text(encoding="utf-8")
        for target in markdown_relative_links(text):
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                continue
            if not resolved.exists():
                findings.append(f"{path.relative_to(root)} broken link: {target}")
    return findings


def agent_adapter_findings(root: Path) -> list[str]:
    """Check that every supported agent enters the same shared workflow authority."""
    entrypoints = {
        "AGENTS.md": ".harness/workflow/agent/chatgpt.md",
        "CLAUDE.md": ".harness/workflow/agent/claude-code.md",
        "GEMINI.md": ".harness/workflow/agent/gemini.md",
    }
    findings: list[str] = []
    for entry, adapter in entrypoints.items():
        path = root / entry
        if not path.exists():
            findings.append(f"missing agent entrypoint: {entry}")
            continue
        text = path.read_text(encoding="utf-8")
        if adapter not in text:
            findings.append(f"{entry} does not route to shared adapter {adapter}")

        adapter_path = root / adapter
        if not adapter_path.exists():
            findings.append(f"missing agent adapter: {adapter}")
            continue
        adapter_text = adapter_path.read_text(encoding="utf-8")
        if ".harness/workflow/WORKFLOW.md" not in adapter_text:
            findings.append(f"{adapter} does not route to .harness/workflow/WORKFLOW.md")
        if "agent-independent harness" not in adapter_text:
            findings.append(f"{adapter} does not declare the agent-independent authority boundary")
    return findings


def guide_registry_findings(root: Path, manifest_paths: list[str]) -> list[str]:
    """Check that universal Guides have one definition and are registered exactly once."""
    findings: list[str] = []
    definition = ".harness/guides/definition.md"
    guide_files = sorted(
        path.relative_to(root).as_posix()
        for path in (root / ".harness" / "guides").glob("*.md")
    )
    if definition not in guide_files:
        findings.append("missing universal Guide definition: .harness/guides/definition.md")
    for rel in guide_files:
        count = manifest_paths.count(rel)
        if count < 1:
            findings.append(f"Guide is not registered in context manifest: {rel}")
    manifest_guides = sorted(path for path in manifest_paths if path.startswith(".harness/guides/"))
    for rel in sorted(set(manifest_guides) - set(guide_files)):
        findings.append(f"context manifest registers missing/non-Guide path as Guide: {rel}")
    return findings


def routing_findings(root: Path) -> list[str]:
    """Check simple mechanically decidable routing topology invariants."""
    findings: list[str] = []
    path = root / ".harness" / "workflow" / "routing.md"
    if not path.exists():
        return ["missing .harness/workflow/routing.md"]
    seen: dict[str, int] = {}
    in_table = False
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if line == "| Concern | Owner |":
            in_table = True
            continue
        if not in_table:
            continue
        if line.startswith("|---") or line.startswith("| ---"):
            continue
        if not line.startswith("|"):
            if seen:
                break
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 2:
            findings.append(f"routing row {lineno} must contain Concern and Owner")
            continue
        concern, owner = cells[0], cells[1]
        if not concern or not owner:
            findings.append(f"routing row {lineno} has empty Concern/Owner")
            continue
        if concern in seen:
            findings.append(
                f"routing concern appears more than once: {concern!r} (lines {seen[concern]} and {lineno})"
            )
        else:
            seen[concern] = lineno
    if not seen:
        findings.append("routing index contains no concern-owner rows")
    return findings


def load_constitutional_invariants(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    findings: list[str] = []
    path = root / ".harness" / "harness" / "invariants.json"
    if not path.exists():
        return [], ["missing constitutional invariant registry: .harness/harness/invariants.json"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [], [f"invalid constitutional invariant registry: {exc}"]
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        findings.append("constitutional invariant registry must use schema_version 1")
    rows = data.get("invariants") if isinstance(data, dict) else None
    if not isinstance(rows, list) or not rows:
        findings.append("constitutional invariant registry must contain invariants")
        return [], findings
    seen: set[str] = set()
    valid: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            findings.append("every constitutional invariant must be an object")
            continue
        iid = row.get("id")
        category = row.get("category")
        source = row.get("source")
        required = row.get("behavior_required")
        if not isinstance(iid, str) or not re.fullmatch(r"[A-Z]+(?:-[A-Z]+)*-\d{2}", iid):
            findings.append(f"invalid constitutional invariant id: {iid!r}")
            continue
        if iid in seen:
            findings.append(f"duplicate constitutional invariant id: {iid}")
            continue
        seen.add(iid)
        if not isinstance(category, str) or not category:
            findings.append(f"{iid}: category must be non-empty text")
        if not isinstance(source, str) or not source.startswith(".harness/"):
            findings.append(f"{iid}: source must be a .harness path")
        else:
            source_path = root / source
            if not source_path.exists():
                findings.append(f"{iid}: authoritative source does not exist: {source}")
            elif f"[{iid}]" not in source_path.read_text(encoding="utf-8"):
                findings.append(f"{iid}: authoritative source does not contain marker [{iid}]: {source}")
            declarations = []
            marker = f"[{iid}]"
            for markdown in (root / ".harness").rglob("*.md"):
                if marker in markdown.read_text(encoding="utf-8"):
                    declarations.append(markdown.relative_to(root).as_posix())
            unexpected = sorted(set(declarations) - {source})
            if unexpected:
                findings.append(
                    f"{iid}: declaration marker appears outside authoritative source {source}: "
                    + ", ".join(unexpected)
                )
        if not isinstance(required, bool):
            findings.append(f"{iid}: behavior_required must be boolean")
        valid.append(row)
    return valid, findings


def behavior_coverage_findings(root: Path, invariants: list[dict[str, Any]]) -> tuple[list[str], dict[str, Any]]:
    findings: list[str] = []
    summary: dict[str, Any] = {"required": [], "covered": [], "uncovered": [], "scenario_count": 0}
    path = root / ".harness" / "evals" / "behavior" / "scenarios.json"
    if not path.exists():
        return ["missing .harness/evals/behavior/scenarios.json"], summary
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"invalid LLM behavior scenario corpus: {exc}"], summary
    if not isinstance(data, dict) or data.get("schema_version") != 2:
        findings.append("LLM behavior scenario corpus must use schema_version 2")
    rows = data.get("scenarios") if isinstance(data, dict) else None
    if not isinstance(rows, list) or not rows:
        findings.append("LLM behavior scenario corpus must contain scenarios")
        return findings, summary
    summary["scenario_count"] = len(rows)
    ids: set[str] = set()
    known = {row.get("id") for row in invariants if isinstance(row.get("id"), str)}
    coverage: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            findings.append("every LLM behavior scenario must be an object")
            continue
        sid = row.get("id")
        if not isinstance(sid, str) or not sid:
            findings.append("LLM behavior scenario ids must be non-empty strings")
            continue
        if sid in ids:
            findings.append(f"duplicate LLM behavior scenario id: {sid}")
        ids.add(sid)
        family = row.get("family")
        if not isinstance(family, str) or not family:
            findings.append(f"{sid}: family must be non-empty text")
        covers = row.get("covers")
        if not isinstance(covers, list) or any(not isinstance(item, str) for item in covers):
            findings.append(f"{sid}: covers must be a list of invariant ids")
            continue
        unknown = sorted(set(covers) - known)
        if unknown:
            findings.append(f"{sid}: covers unknown invariant ids: {', '.join(unknown)}")
        coverage.update(set(covers) & known)
    required = sorted(
        row["id"] for row in invariants
        if row.get("behavior_required") is True and isinstance(row.get("id"), str)
    )
    uncovered = sorted(set(required) - coverage)
    summary.update(required=required, covered=sorted(coverage), uncovered=uncovered)
    for iid in uncovered:
        findings.append(f"constitutional invariant has no behavior scenario coverage: {iid}")
    return findings, summary


def semantic_surface(root: Path) -> tuple[list[Path], str, list[str]]:
    findings: list[str] = []
    config_path = root / ".harness" / "evals" / "behavior" / "semantic-surface.json"
    if not config_path.exists():
        return [], "", ["missing semantic-surface configuration"]
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [], "", [f"invalid semantic-surface configuration: {exc}"]
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        findings.append("semantic-surface configuration must use schema_version 1")
    globs = data.get("include_globs") if isinstance(data, dict) else None
    if not isinstance(globs, list) or not globs or any(not isinstance(item, str) or not item for item in globs):
        findings.append("semantic-surface include_globs must be a non-empty list of strings")
        return [], "", findings
    matched: set[Path] = set()
    for pattern in globs:
        paths = [path for path in root.glob(pattern) if path.is_file()]
        if not paths:
            findings.append(f"semantic-surface glob matches no files: {pattern}")
        matched.update(paths)
    files = sorted(matched, key=lambda path: path.relative_to(root).as_posix())
    digest = hashlib.sha256()
    for path in files:
        rel = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(rel + b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return files, digest.hexdigest() if files else "", findings


def behavior_evaluation_provenance(root: Path) -> tuple[dict[str, Any], list[str]]:
    """Ask the evaluator for the provenance it itself derives from runner requests.

    The runtime deliberately does not reimplement runner-payload hashing. This keeps
    one owner for the exact bytes that constitute constitutional evaluation input.
    """
    evaluator = root / ".harness" / "evals" / "behavior" / "run.py"
    if not evaluator.exists():
        return {}, ["missing behavior evaluator for evaluation provenance"]
    cp = run(
        [sys.executable, str(evaluator), "--validate-only"],
        cwd=root,
        check=False,
        timeout_seconds=120.0,
    )
    if cp.returncode != 0:
        detail = cp.stderr.strip() or cp.stdout.strip() or f"exit {cp.returncode}"
        return {}, [f"cannot derive constitutional evaluation provenance: {detail}"]
    try:
        data = json.loads(cp.stdout)
    except json.JSONDecodeError as exc:
        return {}, [f"behavior evaluator returned invalid evaluation provenance JSON: {exc}"]
    if not isinstance(data, dict) or data.get("result") != "valid":
        return {}, ["behavior evaluator did not return valid evaluation provenance"]
    if data.get("assurance_scope") != "constitutional":
        return {}, ["behavior evaluator assurance_scope must be constitutional"]
    for field in ("evaluation_input_digest", "suite_digest"):
        value = data.get(field)
        if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
            return {}, [f"behavior evaluator returned invalid {field}"]
    return data, []


def semantic_evidence_findings(root: Path, evaluation_input_digest: str, current_suite_digest: str) -> tuple[list[str], dict[str, Any]]:
    """Validate semantic evidence shape and report freshness without conflating it with structure."""
    findings: list[str] = []
    evidence_dir = root / ".harness" / "evals" / "behavior" / "evidence"
    summary: dict[str, Any] = {
        "status": "absent",
        "files": [],
        "current": [],
        "stale": [],
        "invalid": [],
        "current_profiles": {},
        "stale_profiles": {},
    }
    if not evidence_dir.exists():
        return findings, summary
    for path in sorted(evidence_dir.glob("*.json")):
        rel = path.relative_to(root).as_posix()
        summary["files"].append(rel)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            findings.append(f"invalid semantic evidence {rel}: {exc}")
            summary["invalid"].append(rel)
            continue
        if not isinstance(data, dict):
            findings.append(f"semantic evidence must be a JSON object: {rel}")
            summary["invalid"].append(rel)
            continue
        schema_version = data.get("schema_version")
        if schema_version == 1:
            # Schema-v1 evidence is bound to the declared semantic-surface inventory,
            # not the exact constitutional evaluator requests. It can be retained as
            # stale evidence but can never satisfy a current Assurance claim.
            profile = data.get("profile")
            if isinstance(profile, str) and profile.strip():
                profile = profile.strip()
                summary["stale"].append(rel)
                summary["stale_profiles"].setdefault(profile, []).append(rel)
                continue
            findings.append(f"schema-v1 semantic evidence missing profile: {rel}")
            summary["invalid"].append(rel)
            continue
        if schema_version != 2:
            findings.append(f"semantic evidence must use schema_version 2: {rel}")
            summary["invalid"].append(rel)
            continue
        profile = data.get("profile")
        if not isinstance(profile, str) or not profile.strip():
            findings.append(f"semantic evidence missing profile: {rel}")
            summary["invalid"].append(rel)
            continue
        profile = profile.strip()
        if data.get("evaluation_source") not in {"live_runner", "response_replay"}:
            findings.append(f"semantic evidence has invalid evaluation_source: {rel}")
            summary["invalid"].append(rel)
            continue
        if data.get("result") != "pass":
            findings.append(f"semantic evidence does not record a passing run: {rel}")
            summary["invalid"].append(rel)
            continue
        passed, total = data.get("passed"), data.get("total")
        if not isinstance(passed, int) or not isinstance(total, int) or total <= 0 or passed != total:
            findings.append(f"semantic evidence has invalid pass counts: {rel}")
            summary["invalid"].append(rel)
            continue
        evidence_digest = data.get("evaluation_input_digest")
        evidence_suite_digest = data.get("suite_digest")
        if not isinstance(evidence_digest, str) or not evidence_digest:
            findings.append(f"semantic evidence missing evaluation_input_digest: {rel}")
            summary["invalid"].append(rel)
            continue
        if not isinstance(evidence_suite_digest, str) or not evidence_suite_digest:
            findings.append(f"semantic evidence missing suite_digest: {rel}")
            summary["invalid"].append(rel)
            continue
        if evidence_digest == evaluation_input_digest and evidence_suite_digest == current_suite_digest:
            summary["current"].append(rel)
            summary["current_profiles"].setdefault(profile, []).append(rel)
        else:
            # Stale evidence remains inspectable but is not a structural Harness defect.
            # `assure` requires current evidence for the claimed profile.
            summary["stale"].append(rel)
            summary["stale_profiles"].setdefault(profile, []).append(rel)
    if summary["current"]:
        summary["status"] = "current"
    elif summary["stale"]:
        summary["status"] = "stale"
    elif summary["invalid"]:
        summary["status"] = "invalid"
    return findings, summary


def constitutional_wiring_findings(root: Path) -> list[str]:
    """Check that constitutional concepts are connected to the execution/check path."""
    findings: list[str] = []
    required_markers = {
        Path(".harness/composition/definition.md"): ["[COMPOSE-01]", "exactly one supported Project model", "active.json"],
        Path(".harness/contracts/authority-orchestrator-contract.md"): ["[ORCH-01]", "methods", "Project truth"],
        Path(".harness/contracts/method-pack-contract.md"): ["[METHOD-01]", "Project authority", "active"],
        Path(".harness/collaboration-models/cooperative-multi-user.md"): ["[COLLAB-01]", "integration-authority", "LANDING_BLOCKED", "immutable handoff"],
        Path(".harness/workflow/WORKFLOW.md"): ["[AUTH-01]", "[AUTH-02]", "[AUTH-03]", "Change Impact"],
        Path(".harness/contracts/task-capability-skill-contract.md"): ["Change Impact"],
        Path(".harness/skills/harness/change.md"): ["Change Impact", "invariants.json", "semantic-surface"],
        Path(".harness/skills/sanity/harness-check.md"): ["Harness vs Project", "Guides remain universal", "Authority orchestration", "Method packs remain techniques", "Change propagation", "invariants.json"],
        Path(".harness/harness/definition.md"): ["[BOUNDARY-01]", "[BOUNDARY-02]", "Harness Assurance"],
        Path(".harness/guides/definition.md"): ["[GUIDE-01]", "[GUIDE-02]"],
        Path(".harness/mechanisms/change-impact.md"): ["[PROP-01]", "[PROP-02]"],
        Path(".harness/harness-assurance.md"): ["[SEM-01]", "does not grade", "semantic-surface"],
    }
    for rel, markers in required_markers.items():
        path = root / rel
        if not path.exists():
            findings.append(f"missing constitutional wiring document: {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        for expected in markers:
            if expected not in text:
                findings.append(f"{rel} is missing constitutional wiring marker: {expected}")

    old_readiness = root / ".harness" / "readiness.md"
    if old_readiness.exists():
        findings.append("obsolete .harness/readiness.md remains beside Harness Assurance authority")
    for path in sorted((root / ".harness").rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        if "Harness Readiness" in text or ".harness/readiness.md" in text:
            findings.append(f"{path.relative_to(root)} still references obsolete Harness Readiness authority")
    return findings


def release_evidence_findings(root: Path) -> list[str]:
    """Check that deterministic release automation and semantic-eval machinery ship together."""
    findings: list[str] = []
    version_path = root / ".harness" / "runtime" / "VERSION"
    try:
        version = version_path.read_text(encoding="utf-8").strip()
    except OSError:
        version = ""
    if not version:
        findings.append("missing or empty runtime VERSION: .harness/runtime/VERSION")
    required = [
        Path(".github/workflows/harness-ci.yml"),
        Path(".harness/composition/definition.md"),
        Path(".harness/composition/active.json"),
        Path(".harness/composition/classification.json"),
        *([Path(f".harness/roadmap/v{version}.md")] if version else []),
        Path(".harness/collaboration-models/cooperative-multi-user.md"),
        *([Path(f".harness/releases/{version}.md")] if version else []),
        Path(".harness/harness-assurance.md"),
        Path(".harness/harness/invariants.json"),
        Path(".harness/runtime/tests/test_harness.py"),
        Path(".harness/evals/behavior/README.md"),
        Path(".harness/evals/behavior/run.py"),
        Path(".harness/evals/behavior/scenarios.json"),
        Path(".harness/evals/behavior/semantic-surface.json"),
        Path(".harness/evals/behavior/tests/test_behavior.py"),
    ]
    for rel in required:
        if not (root / rel).exists():
            findings.append(f"missing release evidence artifact: {rel}")

    workflow = root / ".github" / "workflows" / "harness-ci.yml"
    if workflow.exists():
        try:
            workflow_text = workflow.read_text(encoding="utf-8")
        except OSError as exc:
            findings.append(f"cannot read release CI workflow: {exc}")
        else:
            required_ci_markers = {
                "python .harness/runtime/harness.py check",
                "python -m unittest discover -s .harness/runtime/tests -v",
                "python -m unittest discover -s .harness/evals/behavior/tests -v",
                "python .harness/evals/behavior/run.py --validate-only",
                "name: Release gate",
            }
            for marker in sorted(required_ci_markers):
                if marker not in workflow_text:
                    findings.append(f"release CI workflow is missing required gate step: {marker}")

            required_ci_scope_markers = {
                'pull_request:\n    paths:',
                'push:\n    paths:',
                '- ".harness/**"',
                '- ".claude/**"',
                '- "AGENTS.md"',
                '- "CLAUDE.md"',
                '- "GEMINI.md"',
                '- ".github/workflows/harness-ci.yml"',
                'workflow_dispatch:',
            }
            for marker in sorted(required_ci_scope_markers):
                if marker not in workflow_text:
                    findings.append(
                        "release CI workflow must stay scoped to Harness-owned changes "
                        f"and retain manual dispatch; missing marker: {marker}"
                    )
    return findings


def git_policy_findings(root: Path) -> list[str]:
    findings = []
    allowed_raw_git_docs = {
        Path(".harness/runtime/README.md"),
        Path(".harness/guides/git-history.md"),
    }
    patterns = [
        (re.compile(r"git init -b main"), "hard-coded `git init -b main`; use runtime-resolved bootstrap mainline"),
        (re.compile(r"`main` remains the non-rewritable boundary"), "hard-coded mainline name; use configured mainline"),
        (re.compile(r"Never rewrite `main`"), "hard-coded mainline name; use configured mainline"),
        (re.compile(r"git update-ref"), "raw approval/transaction ref mechanics; delegate to deterministic runtime"),
    ]
    for path in sorted((root / ".harness").rglob("*.md")):
        rel = path.relative_to(root)
        if rel in allowed_raw_git_docs:
            continue
        text = path.read_text(encoding="utf-8")
        for pattern, note in patterns:
            if pattern.search(text):
                findings.append(f"{rel}: {note}")
    return findings





def spec_topology_contract_findings(root: Path) -> list[str]:
    """Validate the shipped Spec-topology contract without grading Project specs."""
    path = root / ".harness" / "project-models" / "spec-topology.md"
    if not path.exists():
        return ["missing Spec topology contract: .harness/project-models/spec-topology.md"]
    text = path.read_text(encoding="utf-8")
    required = (
        "[TOPOLOGY-01]",
        "doc/spec/topology.json",
        "stable scope",
        "explicit",
        "transitive dependencies",
        "reverse dependents",
    )
    findings = [f"Spec topology contract missing required concept: {item}" for item in required if item not in text]
    model = root / ".harness" / "project-models" / "spec.md"
    if active_project_model(root) == "spec" and model.exists():
        model_text = model.read_text(encoding="utf-8")
        if "spec-topology.md" not in model_text:
            findings.append("active Spec Project model does not bind the Spec topology contract")
    return findings

def collaboration_model_contract_findings(root: Path) -> list[str]:
    """Validate the cooperative multi-user Collaboration-model contract."""
    findings: list[str] = []
    single = root / ".harness" / "collaboration-models" / "single-user.md"
    cooperative = root / ".harness" / "collaboration-models" / "cooperative-multi-user.md"
    if not single.exists():
        findings.append("missing Single-user Collaboration model")
    if not cooperative.exists():
        findings.append("missing Cooperative Multi-user Collaboration model")
        return findings
    text = cooperative.read_text(encoding="utf-8")
    required = (
        "[COLLAB-01]",
        "integration-authority",
        "immutable handoff",
        "LANDING_BLOCKED",
        "not a security system",
        "independent exclusive Goal branches",
    )
    findings.extend(
        f"cooperative multi-user Collaboration model missing required concept: {item}"
        for item in required if item not in text
    )
    if active_collaboration_model(root) == "cooperative-multi-user":
        active = root / ".harness" / "composition" / "active.json"
        if active.exists() and "cooperative-multi-user" not in active.read_text(encoding="utf-8"):
            findings.append("active composition does not bind cooperative-multi-user Collaboration model")
    return findings


def vocabulary_findings(root: Path) -> list[str]:
    """Validate the split working/extended Harness vocabulary and ownership boundary."""
    findings: list[str] = []
    working_rel = Path(".harness/README-vocabulary.md")
    extended_rel = Path(".harness/harness-extended-vocabulary.md")
    legacy_rel = Path(".harness/vocabulary.md")
    paths = (("working", working_rel), ("extended", extended_rel))

    if (root / legacy_rel).exists():
        findings.append("obsolete .harness/vocabulary.md remains beside the split vocabulary authorities")

    terms_by_file: dict[str, set[str]] = {}
    term_pattern = re.compile(r"^\| \*\*(.+?)\*\* \|")
    for label, rel in paths:
        path = root / rel
        if not path.exists():
            findings.append(f"missing {label} vocabulary authority: {rel.as_posix()}")
            continue
        text = path.read_text(encoding="utf-8")
        if "Harness Change owns" not in text and "Harness Change" not in text:
            findings.append(f"{rel.as_posix()} does not declare Harness Change ownership")
        terms: set[str] = set()
        for line in text.splitlines():
            match = term_pattern.match(line)
            if not match:
                continue
            term = match.group(1).strip()
            if term in terms:
                findings.append(f"duplicate term in {rel.as_posix()}: {term}")
            terms.add(term)
        if not terms:
            findings.append(f"{rel.as_posix()} defines no vocabulary terms")
        terms_by_file[label] = terms

    overlap = sorted(terms_by_file.get("working", set()) & terms_by_file.get("extended", set()))
    for term in overlap:
        findings.append(f"vocabulary term is defined in both working and extended authorities: {term}")

    manifest = root / ".harness" / "workflow" / "context-manifest.yaml"
    if manifest.exists():
        manifest_text = manifest.read_text(encoding="utf-8")
        for rel in (working_rel, extended_rel):
            if rel.as_posix() not in manifest_text:
                findings.append(f"context manifest does not bind vocabulary authority: {rel.as_posix()}")

    routing = root / ".harness" / "workflow" / "routing.md"
    if routing.exists():
        routing_text = routing.read_text(encoding="utf-8")
        for rel in (working_rel, extended_rel):
            if rel.as_posix() not in routing_text:
                findings.append(f"routing does not bind vocabulary authority: {rel.as_posix()}")

    return findings



def startup_context_findings(root: Path) -> list[str]:
    """Keep unconditional model-facing startup context intentionally bounded."""
    manifest = root / ".harness" / "workflow" / "context-manifest.yaml"
    if not manifest.exists():
        return ["missing .harness/workflow/context-manifest.yaml"]

    always: list[str] = []
    in_always = False
    for raw_line in manifest.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not in_always:
            if raw_line == "always:":
                in_always = True
            continue
        if raw_line and not raw_line[0].isspace() and not raw_line.startswith("-"):
            break
        if stripped.startswith("-"):
            value = stripped[1:].strip()
            if value:
                always.append(value)

    expected = [
        ".harness/workflow/WORKFLOW.md",
        ".harness/composition/active.json",
        ".harness/workflow/routing.md",
    ]
    findings: list[str] = []
    if always != expected:
        findings.append(
            "startup context must contain only the three ordered routing anchors: "
            + ", ".join(expected)
        )
    return findings


def runtime_module_findings(root: Path) -> list[str]:
    """Validate the runtime ownership split."""
    findings: list[str] = []
    runtime = root / ".harness" / "runtime"
    required = {
        "harness.py": {"build_parser", "main", "print_result", "set_runtime_context"},
        "kernel.py": {"run", "git", "cmd_repo_status", "cmd_land_prepare", "cmd_land_merge"},
        "project_model.py": {"active_project_model", "spec_topology_state", "cmd_spec_topology", "cmd_spec_affected"},
        "collaboration_model.py": {"active_collaboration_model", "cmd_collaboration_configure", "cmd_handoff_publish", "cmd_handoff_accept"},
        "checker.py": {"cmd_check", "cmd_assure", "composition_findings", "vocabulary_findings"},
    }
    definitions: dict[str, set[str]] = {}
    local_imports: dict[str, set[str]] = {}
    wildcard_imports: dict[str, list[str]] = {}
    for filename, expected in required.items():
        path = runtime / filename
        if not path.exists():
            findings.append(f"missing runtime module: .harness/runtime/{filename}")
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=filename)
        except (OSError, SyntaxError) as exc:
            findings.append(f"cannot parse runtime module {filename}: {exc}")
            continue
        names = {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
        definitions[filename] = names
        deps: set[str] = set()
        wildcards: list[str] = []
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".", 1)[0]
                    if top in {"kernel", "project_model", "collaboration_model", "checker"}:
                        deps.add(top)
            elif isinstance(node, ast.ImportFrom) and node.module:
                top = node.module.split(".", 1)[0]
                if top in {"kernel", "project_model", "collaboration_model", "checker"}:
                    deps.add(top)
                    if any(alias.name == "*" for alias in node.names):
                        wildcards.append(top)
        local_imports[filename] = deps
        wildcard_imports[filename] = wildcards
        for name in sorted(expected - names):
            findings.append(f"runtime module {filename} is missing owned symbol: {name}")

    allowed_dependencies = {
        "kernel.py": set(),
        "project_model.py": {"kernel"},
        "collaboration_model.py": {"kernel"},
        "checker.py": {"kernel", "project_model", "collaboration_model"},
        "harness.py": {"kernel", "project_model", "collaboration_model", "checker"},
    }
    for filename, deps in local_imports.items():
        unexpected = deps - allowed_dependencies.get(filename, set())
        for dep in sorted(unexpected):
            findings.append(f"runtime module {filename} has disallowed top-level dependency: {dep}")
        if filename != "harness.py":
            for dep in wildcard_imports.get(filename, []):
                findings.append(f"runtime module {filename} must import explicit symbols from {dep}, not wildcard")

    harness_defs = definitions.get("harness.py", set())
    allowed_harness = {"build_parser", "main", "print_result", "set_runtime_context"}
    for name in sorted(harness_defs - allowed_harness):
        findings.append(f"runtime entrypoint owns non-wiring implementation: {name}")

    kernel_defs = definitions.get("kernel.py", set())
    forbidden_kernel = {
        "active_project_model", "spec_topology_state", "scope_closure",
        "active_collaboration_model", "read_collaboration_state",
        "cmd_collaboration_configure", "cmd_collaboration_status",
        "cmd_handoff_publish", "cmd_handoff_withdraw", "cmd_handoff_accept", "cmd_handoff_release",
        "cmd_check", "cmd_assure",
    }
    for name in sorted(kernel_defs & forbidden_kernel):
        findings.append(f"kernel owns model/checker symbol that belongs in another runtime module: {name}")
    for name in sorted(name for name in kernel_defs if name.startswith("cmd_spec_")):
        findings.append(f"kernel owns Project-model command that belongs in project_model.py: {name}")

    return findings


def composition_findings(root: Path) -> list[str]:
    """Validate architectural composition and the current classification inventory."""
    findings: list[str] = []
    active_path = root / ".harness" / "composition" / "active.json"
    classification_path = root / ".harness" / "composition" / "classification.json"

    def load_object(path: Path, label: str) -> dict[str, Any] | None:
        if not path.exists():
            findings.append(f"missing {label}: {path.relative_to(root)}")
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            findings.append(f"invalid {label} JSON: {exc}")
            return None
        if not isinstance(data, dict):
            findings.append(f"{label} must be a JSON object")
            return None
        return data

    active = load_object(active_path, "Harness composition")
    classification = load_object(classification_path, "Harness architectural classification")

    if active is not None:
        if active.get("schema_version") != 1:
            findings.append("Harness composition must use schema_version 1")
        release = active.get("release")
        version_path = root / ".harness" / "runtime" / "VERSION"
        if version_path.exists():
            version = version_path.read_text(encoding="utf-8").strip()
            if release != version:
                findings.append(f"Harness composition release {release!r} does not match runtime VERSION {version!r}")

        selection = active.get("selection")
        supported = active.get("supported")
        sources = active.get("sources")
        if not isinstance(selection, dict):
            findings.append("Harness composition selection must be an object")
        if not isinstance(supported, dict):
            findings.append("Harness composition supported registry must be an object")
        if not isinstance(sources, dict):
            findings.append("Harness composition sources registry must be an object")

        if isinstance(selection, dict) and isinstance(supported, dict):
            project_model = selection.get("project_model")
            collaboration_model = selection.get("collaboration_model")
            method_packs = selection.get("method_packs")
            if not isinstance(project_model, str) or not project_model:
                findings.append("active composition must select exactly one non-empty project_model")
            if not isinstance(collaboration_model, str) or not collaboration_model:
                findings.append("active composition must select exactly one non-empty collaboration_model")
            if not isinstance(method_packs, list) or any(not isinstance(item, str) or not item for item in method_packs):
                findings.append("active composition method_packs must be a list of non-empty ids")
                method_packs = []
            elif len(set(method_packs)) != len(method_packs):
                findings.append("active composition method_packs must not contain duplicates")

            dimensions = (
                ("project_models", project_model),
                ("collaboration_models", collaboration_model),
            )
            for key, selected in dimensions:
                values = supported.get(key)
                if not isinstance(values, list) or any(not isinstance(item, str) or not item for item in values):
                    findings.append(f"supported {key} must be a list of non-empty ids")
                    continue
                if len(set(values)) != len(values):
                    findings.append(f"supported {key} must not contain duplicates")
                if isinstance(selected, str) and selected and selected not in values:
                    findings.append(f"active {key[:-1]} is not supported by this release: {selected}")

            supported_methods = supported.get("method_packs")
            if not isinstance(supported_methods, list) or any(not isinstance(item, str) or not item for item in supported_methods):
                findings.append("supported method_packs must be a list of non-empty ids")
                supported_methods = []
            if isinstance(method_packs, list):
                for method in method_packs:
                    if method not in supported_methods:
                        findings.append(f"active method pack is not supported by this release: {method}")

            if isinstance(sources, dict):
                for source_key, selected in dimensions:
                    mapping = sources.get(source_key)
                    if not isinstance(mapping, dict):
                        findings.append(f"composition sources.{source_key} must be an object")
                        continue
                    if isinstance(selected, str) and selected:
                        rel = mapping.get(selected)
                        if not isinstance(rel, str) or not rel.startswith(".harness/"):
                            findings.append(f"active {source_key[:-1]} has no .harness source binding: {selected}")
                        elif not (root / rel).exists():
                            findings.append(f"active {source_key[:-1]} source is missing: {rel}")

                method_sources = sources.get("method_packs")
                if not isinstance(method_sources, dict):
                    findings.append("composition sources.method_packs must be an object")
                else:
                    methods_to_validate: set[str] = set()
                    if isinstance(supported_methods, list):
                        methods_to_validate.update(supported_methods)
                    if isinstance(method_packs, list):
                        methods_to_validate.update(method_packs)
                    source_paths: dict[str, str] = {}
                    for method in sorted(methods_to_validate):
                        rel = method_sources.get(method)
                        if not isinstance(rel, str) or not rel.startswith(".harness/"):
                            findings.append(f"method pack has no .harness source binding: {method}")
                            continue
                        if rel in source_paths:
                            findings.append(
                                f"method packs must not share one source definition: {source_paths[rel]} and {method} -> {rel}"
                            )
                        else:
                            source_paths[rel] = method
                        if not (root / rel).exists():
                            findings.append(f"method-pack source is missing: {rel}")

    if classification is not None:
        if classification.get("schema_version") != 1:
            findings.append("Harness architectural classification must use schema_version 1")
        allowed_layers = {
            "kernel",
            "project-model/spec",
            "collaboration/single-user",
            "collaboration/cooperative-multi-user",
            "method",
            "exploration",
        }
        entries = classification.get("entries")
        dynamic_rules = classification.get("dynamic_rules", [])
        if not isinstance(entries, list):
            findings.append("Harness architectural classification entries must be a list")
            entries = []
        if not isinstance(dynamic_rules, list):
            findings.append("Harness architectural classification dynamic_rules must be a list")
            dynamic_rules = []

        classified: dict[str, dict[str, Any]] = {}
        for row in entries:
            if not isinstance(row, dict):
                findings.append("every architectural classification entry must be an object")
                continue
            rel = row.get("path")
            layer = row.get("layer")
            kind = row.get("kind")
            authority = row.get("authority")
            if not isinstance(rel, str) or not rel.startswith(".harness/"):
                findings.append(f"architectural classification entry has invalid path: {rel!r}")
                continue
            if rel in classified:
                findings.append(f"duplicate architectural classification path: {rel}")
                continue
            classified[rel] = row
            if layer not in allowed_layers:
                findings.append(f"architectural classification has unknown layer for {rel}: {layer!r}")
            if not isinstance(kind, str) or not kind:
                findings.append(f"architectural classification missing kind for {rel}")
            if not isinstance(authority, str) or not authority:
                findings.append(f"architectural classification missing authority for {rel}")
            couplings = row.get("couplings", [])
            if not isinstance(couplings, list) or any(not isinstance(item, str) or not item for item in couplings):
                findings.append(f"architectural classification couplings must be string ids for {rel}")
            if not (root / rel).exists():
                findings.append(f"architectural classification points to missing path: {rel}")

        globs: list[str] = []
        for rule in dynamic_rules:
            if not isinstance(rule, dict):
                findings.append("every architectural dynamic rule must be an object")
                continue
            pattern = rule.get("glob")
            layer = rule.get("layer")
            if not isinstance(pattern, str) or not pattern.startswith(".harness/"):
                findings.append(f"architectural dynamic rule has invalid glob: {pattern!r}")
                continue
            if layer not in allowed_layers:
                findings.append(f"architectural dynamic rule has unknown layer for {pattern}: {layer!r}")
            globs.append(pattern)

        shipped: list[str] = []
        harness_root = root / ".harness"
        if harness_root.exists():
            for path in harness_root.rglob("*"):
                if not path.is_file():
                    continue
                rel = path.relative_to(root).as_posix()
                if "/__pycache__/" in rel or rel.endswith(".pyc"):
                    continue
                shipped.append(rel)
        for rel in sorted(shipped):
            if rel in classified:
                continue
            rel_path = Path(rel)
            if any(rel_path.match(pattern) for pattern in globs):
                continue
            findings.append(f"unclassified shipped Harness artifact: {rel}")

    return findings


def cmd_check(args: argparse.Namespace) -> dict[str, Any]:
    root = PROJECT_ROOT
    checks: dict[str, list[str]] = {}

    checks["skill_contract"] = skill_contract_findings(root)
    checks["method_pack_contract"] = method_pack_contract_findings(root)
    checks["authority_orchestrators"] = authority_orchestrator_findings(root)
    checks["spec_topology_contract"] = spec_topology_contract_findings(root)
    checks["collaboration_model_contract"] = collaboration_model_contract_findings(root)
    checks["vocabulary"] = vocabulary_findings(root)
    checks["startup_context"] = startup_context_findings(root)
    checks["runtime_modules"] = runtime_module_findings(root)
    checks["wrappers"] = wrapper_findings(root)
    checks["agent_adapters"] = agent_adapter_findings(root)

    checks["composition"] = composition_findings(root)
    checks["composition_selection"] = manifest_composition_findings(root)
    checks["assurance_profiles"] = assurance_profile_findings(root)

    manifest = root / ".harness" / "workflow" / "context-manifest.yaml"
    manifest_findings: list[str] = []
    manifest_paths_list: list[str] = []
    if not manifest.exists():
        manifest_findings.append("missing .harness/workflow/context-manifest.yaml")
    else:
        manifest_paths_list = yaml_manifest_paths(manifest.read_text(encoding="utf-8"))
        manifest_paths = set(manifest_paths_list)
        for path in sorted(manifest_paths):
            if not (root / path).exists():
                manifest_findings.append(f"context manifest points to missing path: {path}")
        required_operating_context = {
            ".harness/composition/definition.md",
            ".harness/composition/active.json",
            ".harness/composition/classification.json",
            ".harness/project-models/spec.md",
            ".harness/project-models/spec-topology.md",
            ".harness/collaboration-models/single-user.md",
            ".harness/collaboration-models/cooperative-multi-user.md",
            ".harness/contracts/authority-orchestrator-contract.md",
            ".harness/contracts/method-pack-contract.md",
            ".harness/methods/interview-me.md",
            ".harness/methods/event-storming.md",
            ".harness/methods/story-mapping.md",
            ".harness/methods/design.md",
            ".harness/harness-limitations.md",
            ".harness/harness-assurance.md",
            ".harness/harness/definition.md",
            ".harness/guides/definition.md",
            ".harness/mechanisms/change-impact.md",
            ".harness/harness/invariants.json",
        }
        for path in sorted(required_operating_context - manifest_paths):
            manifest_findings.append(f"context manifest must include Harness operating authority: {path}")

        required_semantic_regression_context = {
            ".harness/evals/behavior/README.md",
            ".harness/evals/behavior/semantic-surface.json",
            ".harness/evals/behavior/scenarios.json",
            ".harness/evals/behavior/run.py",
            ".harness/evals/behavior/tests/test_behavior.py",
        }
        for path in sorted(required_semantic_regression_context - manifest_paths):
            manifest_findings.append(f"context manifest must include semantic-regression input/tooling: {path}")

        runtime_regression_suite = ".harness/runtime/tests/test_harness.py"
        if runtime_regression_suite not in manifest_paths:
            manifest_findings.append(
                f"context manifest must include runtime regression suite: {runtime_regression_suite}"
            )
    checks["context_manifest"] = manifest_findings
    checks["guides"] = guide_registry_findings(root, manifest_paths_list)
    checks["routing"] = routing_findings(root)

    invariants, invariant_findings = load_constitutional_invariants(root)
    checks["constitutional_invariants"] = invariant_findings
    coverage_findings, coverage_summary = behavior_coverage_findings(root, invariants)
    checks["semantic_coverage"] = coverage_findings

    surface_files, surface_digest, surface_findings = semantic_surface(root)
    surface_rels = {path.relative_to(root).as_posix() for path in surface_files}
    required_surface_sources = {
        row["source"] for row in invariants
        if isinstance(row.get("source"), str)
    } | {
        ".harness/composition/definition.md",
        ".harness/composition/active.json",
        ".harness/project-models/spec.md",
        ".harness/project-models/spec-topology.md",
        ".harness/collaboration-models/single-user.md",
        ".harness/collaboration-models/cooperative-multi-user.md",
        ".harness/contracts/authority-orchestrator-contract.md",
        ".harness/contracts/method-pack-contract.md",
        ".harness/methods/interview-me.md",
        ".harness/methods/event-storming.md",
        ".harness/methods/story-mapping.md",
        ".harness/methods/design.md",
        ".harness/workflow/WORKFLOW.md",
        ".harness/workflow/routing.md",
        ".harness/harness/definition.md",
        ".harness/guides/definition.md",
        ".harness/mechanisms/change-impact.md",
        ".harness/harness-assurance.md",
        ".harness/README-vocabulary.md",
        ".harness/harness-extended-vocabulary.md",
        ".harness/README-workflows.md",
        ".harness/workflow/context-manifest.yaml",
        ".harness/runtime/README.md",
        ".harness/workflow/agent/chatgpt.md",
        ".harness/workflow/agent/claude-code.md",
        ".harness/workflow/agent/gemini.md",
    }
    for rel in sorted(required_surface_sources - surface_rels):
        surface_findings.append(f"semantic surface omits required model-facing authority: {rel}")
    checks["semantic_surface"] = surface_findings
    evaluation_provenance, provenance_findings = behavior_evaluation_provenance(root)
    checks["evaluation_provenance"] = provenance_findings
    evaluation_input_digest = str(evaluation_provenance.get("evaluation_input_digest", ""))
    current_suite_digest = str(evaluation_provenance.get("suite_digest", ""))
    evidence_findings, evidence_summary = semantic_evidence_findings(
        root, evaluation_input_digest, current_suite_digest
    )
    checks["semantic_evidence"] = evidence_findings

    checks["constitutional_wiring"] = constitutional_wiring_findings(root)
    checks["links"] = link_findings(root)
    checks["git_policy"] = git_policy_findings(root)
    checks["release_evidence"] = release_evidence_findings(root)
    config_findings: list[str] = []
    try:
        load_config()
    except HarnessError as exc:
        config_findings.append(str(exc))
    checks["runtime_config"] = config_findings

    findings = [finding for category in checks.values() for finding in category]

    def dimension_status(categories: tuple[str, ...]) -> str:
        return "pass" if all(not checks.get(name) for name in categories) else "findings"

    maturity_dimensions = {
        "composition": {
            "deterministic_status": dimension_status(("composition", "composition_selection", "assurance_profiles", "method_pack_contract", "authority_orchestrators", "spec_topology_contract", "collaboration_model_contract", "context_manifest", "constitutional_invariants", "semantic_coverage")),
            "invariants": ["COMPOSE-01", "METHOD-01", "ORCH-01", "TOPOLOGY-01", "COLLAB-01"],
        },
        "harness_project_boundary": {
            "deterministic_status": dimension_status(("constitutional_invariants", "constitutional_wiring", "semantic_coverage")),
            "invariants": ["BOUNDARY-01", "BOUNDARY-02"],
        },
        "universal_guides": {
            "deterministic_status": dimension_status(("guides", "constitutional_invariants", "constitutional_wiring", "semantic_coverage")),
            "invariants": ["GUIDE-01", "GUIDE-02"],
        },
        "simplification": {
            "deterministic_status": dimension_status(("routing", "guides", "wrappers", "agent_adapters", "startup_context", "runtime_modules", "constitutional_invariants")),
            "mechanical_proxies": [
                "unique routing concerns",
                "registered Guides",
                "one wrapper per authoritative skill",
                "shared agent authority",
                "three-file startup context",
                "runtime module ownership",
                "one constitutional declaration source",
            ],
        },
        "semantic_regression": {
            "deterministic_status": dimension_status(("semantic_coverage", "semantic_surface", "evaluation_provenance", "semantic_evidence", "release_evidence")),
            "evidence_status": evidence_summary["status"],
        },
        "change_propagation": {
            "deterministic_status": dimension_status(("constitutional_wiring", "constitutional_invariants", "semantic_coverage")),
            "invariants": ["PROP-01", "PROP-02"],
        },
        "unambiguous_authority": {
            "deterministic_status": dimension_status(("routing", "constitutional_invariants", "constitutional_wiring", "semantic_coverage")),
            "invariants": ["AUTH-01", "AUTH-02", "AUTH-03"],
        },
    }

    return {
        "result": "no change" if not findings else "findings",
        "finding_count": len(findings),
        "findings": findings,
        "checks": {
            name: {"finding_count": len(items), "findings": items}
            for name, items in checks.items()
        },
        "maturity_dimensions": maturity_dimensions,
        "semantic_regression": {
            "coverage": coverage_summary,
            "assurance_scope": evaluation_provenance.get("assurance_scope", "constitutional"),
            "constitutional_authority_paths": evaluation_provenance.get("constitutional_authority_paths", []),
            "evaluation_input_digest": evaluation_input_digest,
            "suite_digest": current_suite_digest,
            "semantic_surface_digest": surface_digest,
            "semantic_surface_file_count": len(surface_files),
            "evidence": evidence_summary,
        },
        "counts": {
            "authoritative_skills": len(list((root / ".harness" / "skills").rglob("*.md"))),
            "claude_wrappers": len(list((root / ".claude" / "skills").glob("*/SKILL.md"))),
            "agent_entrypoints": sum(1 for name in ("AGENTS.md", "CLAUDE.md", "GEMINI.md") if (root / name).exists()),
            "agent_adapters": len(list((root / ".harness" / "workflow" / "agent").glob("*.md"))),
            "guides": len(list((root / ".harness" / "guides").glob("*.md"))),
            "method_packs": len(list((root / ".harness" / "methods").glob("*.md"))),
            "constitutional_invariants": len(invariants),
            "markdown_files": len(list(root.rglob("*.md"))),
        },
    }


def run_assurance_verification(root: Path) -> list[dict[str, Any]]:
    """Run the deterministic executable evidence owned by the runtime Assurance gate."""
    steps = [
        (
            "compile",
            [sys.executable, "-m", "compileall", "-q", ".harness/runtime", ".harness/evals/behavior/run.py"],
        ),
        (
            "runtime_tests",
            [sys.executable, "-m", "unittest", "discover", "-s", ".harness/runtime/tests", "-v"],
        ),
        (
            "behavior_tests",
            [sys.executable, "-m", "unittest", "discover", "-s", ".harness/evals/behavior/tests", "-v"],
        ),
        (
            "behavior_validate",
            [sys.executable, ".harness/evals/behavior/run.py", "--validate-only"],
        ),
    ]
    results: list[dict[str, Any]] = []
    for name, command in steps:
        cp = run(command, cwd=root, check=False, timeout_seconds=600.0)
        results.append({
            "name": name,
            "status": "pass" if cp.returncode == 0 else "fail",
            "returncode": cp.returncode,
            "stdout_tail": cp.stdout[-4000:] if cp.stdout else "",
            "stderr_tail": cp.stderr[-4000:] if cp.stderr else "",
        })
    return results


def cmd_assure(args: argparse.Namespace) -> dict[str, Any]:
    """Report profile-qualified Harness Assurance from current deterministic and semantic evidence."""
    profile = args.profile.strip()
    if not profile:
        fail("assure --profile must be non-empty")

    check = cmd_check(args)
    if check.get("finding_count", 0):
        return {
            "result": "RED",
            "profile": profile,
            "reason": "deterministic Harness check has findings",
            "check": check,
            "verification": [],
            "semantic_evidence": "not evaluated because deterministic check failed",
            "project_boundary": "Harness Assurance does not grade the managed Project.",
        }

    verification = run_assurance_verification(PROJECT_ROOT)
    failed_steps = [step["name"] for step in verification if step["status"] != "pass"]
    if failed_steps:
        return {
            "result": "RED",
            "profile": profile,
            "reason": "deterministic Assurance verification failed",
            "failed_steps": failed_steps,
            "check": check,
            "verification": verification,
            "semantic_evidence": check["semantic_regression"]["evidence"],
            "project_boundary": "Harness Assurance does not grade the managed Project.",
        }

    evidence = check["semantic_regression"]["evidence"]
    current_profiles = evidence.get("current_profiles", {})
    stale_profiles = evidence.get("stale_profiles", {})
    if profile in current_profiles:
        status = "GREEN"
        reason = "deterministic verification passes and current passing semantic evidence exists for the named profile"
    elif profile in stale_profiles:
        status = "UNKNOWN"
        reason = "semantic evidence for the named profile is stale for the current constitutional evaluation input or scenario suite"
    else:
        status = "UNKNOWN"
        reason = "current passing semantic evidence is absent for the named profile"

    collaboration_model = active_collaboration_model(PROJECT_ROOT)
    return {
        "result": status,
        "profile": profile,
        "operating_profile": {
            "collaboration_model": collaboration_model,
            "definition": f".harness/harness-assurance.md (Operating profile: `{collaboration_model}`)",
        },
        "headline": (
            f"GREEN — Harness guarantees assured for the `{collaboration_model}` operating profile under {profile}."
            if status == "GREEN"
            else f"{status} — `{collaboration_model}` operating profile under {profile}: {reason}."
        ),
        "reason": reason,
        "check": {
            "result": check["result"],
            "finding_count": check["finding_count"],
            "maturity_dimensions": check["maturity_dimensions"],
        },
        "verification": verification,
        "semantic_regression": {
            "assurance_scope": check["semantic_regression"].get("assurance_scope", "constitutional"),
            "evaluation_input_digest": check["semantic_regression"]["evaluation_input_digest"],
            "suite_digest": check["semantic_regression"]["suite_digest"],
            "semantic_surface_digest": check["semantic_regression"]["semantic_surface_digest"],
            "evidence": evidence,
            "profile_evidence": current_profiles.get(profile, []) if status == "GREEN" else stale_profiles.get(profile, []),
        },
        "project_boundary": "Harness Assurance does not grade the managed Project.",
        "note": "A separately discovered blocking defect still overrides GREEN under the Assurance anti-gaming rule.",
    }


