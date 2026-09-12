#!/usr/bin/env python3
"""Constitutional coverage and semantic-evidence checks for Harness."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from kernel import run

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
