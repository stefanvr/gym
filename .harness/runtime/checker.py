#!/usr/bin/env python3
"""Deterministic Harness checker and Assurance command façade.

Checker rules are grouped by concern so an agent can inspect or change one class of
validation without loading the entire deterministic checker implementation.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from kernel import HarnessError, PROJECT_ROOT, fail, load_config, run
from collaboration_model import active_collaboration_model
from checker_manifest import (
    yaml_manifest_paths,
    yaml_scalar_tree,
    manifest_composition_findings,
    assurance_profile_findings,
    markdown_relative_links,
    skill_contract_findings,
    method_pack_contract_findings,
    authority_orchestrator_findings,
    wrapper_findings,
    link_findings,
    agent_adapter_findings,
    guide_registry_findings,
    routing_findings,
    constitutional_wiring_findings,
    git_policy_findings,
    spec_topology_contract_findings,
    repository_native_contract_findings,
    extension_package_findings,
    collaboration_model_contract_findings,
    vocabulary_findings,
    startup_context_findings,
)
from checker_semantic import (
    load_constitutional_invariants,
    behavior_coverage_findings,
    semantic_surface,
    behavior_evaluation_provenance,
    semantic_evidence_findings,
)
from checker_architecture import (
    distribution_evidence_findings,
    runtime_module_findings,
    composition_findings,
)

def cmd_check(args: argparse.Namespace) -> dict[str, Any]:
    root = PROJECT_ROOT
    checks: dict[str, list[str]] = {}

    checks["skill_contract"] = skill_contract_findings(root)
    checks["method_pack_contract"] = method_pack_contract_findings(root)
    checks["authority_orchestrators"] = authority_orchestrator_findings(root)
    checks["spec_topology_contract"] = spec_topology_contract_findings(root)
    checks["repository_native_contract"] = repository_native_contract_findings(root)
    checks["extensions"] = extension_package_findings(root)
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
            ".harness/project-models/repository-native.md",
            ".harness/contracts/project-authority-target-contract.md",
            ".harness/capabilities/project-definition.md",
            ".harness/discovery/definition.md",
            ".harness/extensions/definition.md",
            ".harness/notes/definition.md",
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
        ".harness/project-models/repository-native.md",
        ".harness/contracts/project-authority-target-contract.md",
        ".harness/capabilities/project-definition.md",
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
    checks["distribution_evidence"] = distribution_evidence_findings(root)
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
            "deterministic_status": dimension_status(("semantic_coverage", "semantic_surface", "evaluation_provenance", "semantic_evidence", "distribution_evidence")),
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

    try:
        collaboration_model: str | None = active_collaboration_model(PROJECT_ROOT)
    except HarnessError:
        # The standalone distribution deliberately permits exactly one non-operating
        # state: both Project and Collaboration selections are null before bootstrap.
        # Assurance cannot claim an operating profile there, but that coherent
        # bootstrap state is UNKNOWN rather than a damaged-install runtime error.
        active_path = PROJECT_ROOT / ".harness" / "composition" / "active.json"
        try:
            active = json.loads(active_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            raise
        selection = active.get("selection") if isinstance(active, dict) else None
        if not (
            isinstance(selection, dict)
            and selection.get("project_model") is None
            and selection.get("collaboration_model") is None
        ):
            raise
        collaboration_model = None
        status = "UNKNOWN"
        reason = "Harness composition is explicitly unconfigured, so no Collaboration operating profile is selected yet"

    operating_profile = (
        {
            "collaboration_model": collaboration_model,
            "definition": f".harness/harness-assurance.md (Operating profile: `{collaboration_model}`)",
        }
        if collaboration_model is not None
        else {"collaboration_model": None, "definition": None}
    )
    return {
        "result": status,
        "profile": profile,
        "operating_profile": operating_profile,
        "headline": (
            f"GREEN — Harness guarantees assured for the `{collaboration_model}` operating profile under {profile}."
            if status == "GREEN" and collaboration_model is not None
            else (
                f"UNKNOWN — no Collaboration operating profile is selected under {profile}: {reason}."
                if collaboration_model is None
                else f"{status} — `{collaboration_model}` operating profile under {profile}: {reason}."
            )
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


