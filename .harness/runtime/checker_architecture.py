#!/usr/bin/env python3
"""Runtime ownership, distribution integrity, and composition checks for Harness."""
from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

def distribution_evidence_findings(root: Path) -> list[str]:
    """Check that a standalone distribution ships its executable assurance machinery."""
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
        Path(".harness/update-manifest.json"),
        Path(".harness/discovery/definition.md"),
        Path(".harness/extensions/definition.md"),
        Path(".harness/collaboration-models/cooperative-multi-user.md"),
        Path(".harness/harness-assurance.md"),
        Path(".harness/harness/invariants.json"),
        Path(".harness/runtime/runtime_support.py"),
        Path(".harness/runtime/checker_manifest.py"),
        Path(".harness/runtime/checker_semantic.py"),
        Path(".harness/runtime/checker_architecture.py"),
        Path(".harness/runtime/tests/test_harness.py"),
        Path(".harness/runtime/tests/test_update.py"),
        Path(".harness/evals/behavior/README.md"),
        Path(".harness/evals/behavior/run.py"),
        Path(".harness/evals/behavior/scenarios.json"),
        Path(".harness/evals/behavior/semantic-surface.json"),
        Path(".harness/evals/behavior/tests/test_behavior.py"),
        Path("harness-update.py"),
    ]
    for rel in required:
        if not (root / rel).exists():
            findings.append(f"missing standalone distribution artifact: {rel}")

    update_manifest = root / ".harness" / "update-manifest.json"
    if update_manifest.exists():
        try:
            update_data = json.loads(update_manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            findings.append(f"invalid Harness update manifest: {exc}")
        else:
            if not isinstance(update_data, dict) or update_data.get("schema_version") != 1:
                findings.append("Harness update manifest must use schema_version 1")
            else:
                replace = update_data.get("replace", [])
                merge_line_files = update_data.get("merge_line_files", [])
                preserve_json = update_data.get("preserve_json", {})
                required_replace = {
                    ".harness", ".claude", ".github/workflows/harness-ci.yml",
                    "AGENTS.md", "CLAUDE.md", "GEMINI.md", "HARNESS-FEATURES.md", "harness-update.py",
                }
                if not isinstance(replace, list):
                    findings.append("Harness update manifest replace must be a list")
                else:
                    missing = sorted(required_replace - set(item for item in replace if isinstance(item, str)))
                    for rel in missing:
                        findings.append(f"Harness update manifest does not replace managed surface: {rel}")
                    for rel in ("README.md", ".gitignore"):
                        if rel in replace:
                            findings.append(f"Harness update manifest must not replace Project-owned/merged file: {rel}")
                if not isinstance(merge_line_files, list) or ".gitignore" not in merge_line_files:
                    findings.append("Harness update manifest must merge .gitignore rather than replace it")
                if not isinstance(preserve_json, dict):
                    findings.append("Harness update manifest preserve_json must be an object")
                else:
                    config_keys = preserve_json.get(".harness/runtime/config.json", [])
                    selection_keys = preserve_json.get(".harness/composition/active.json", [])
                    if not all(key in config_keys for key in ("mainline", "bootstrap_mainline", "remote")):
                        findings.append("Harness update manifest must preserve repository runtime config values")
                    if "selection" not in selection_keys:
                        findings.append("Harness update manifest must preserve active composition selection")

    # Standalone artifacts deliberately carry no per-version release notes or roadmap.
    for obsolete in (root / ".harness" / "releases", root / ".harness" / "roadmap"):
        if obsolete.exists():
            findings.append(f"standalone distribution must not ship release-history directory: {obsolete.relative_to(root)}")

    workflow = root / ".github" / "workflows" / "harness-ci.yml"
    if workflow.exists():
        try:
            workflow_text = workflow.read_text(encoding="utf-8")
        except OSError as exc:
            findings.append(f"cannot read Harness CI workflow: {exc}")
        else:
            required_ci_markers = {
                "python .harness/runtime/harness.py check",
                "python -m unittest discover -s .harness/runtime/tests -v",
                "python -m unittest discover -s .harness/evals/behavior/tests -v",
                "python .harness/evals/behavior/run.py --validate-only",
                "name: Harness gate",
            }
            for marker in sorted(required_ci_markers):
                if marker not in workflow_text:
                    findings.append(f"Harness CI workflow is missing required gate step: {marker}")

            required_ci_scope_markers = {
                'pull_request:\n    paths:',
                'push:\n    paths:',
                '- ".harness/**"',
                '- ".claude/**"',
                '- "AGENTS.md"',
                '- "CLAUDE.md"',
                '- "GEMINI.md"',
                '- "harness-update.py"',
                '- ".github/workflows/harness-ci.yml"',
                'workflow_dispatch:',
            }
            for marker in sorted(required_ci_scope_markers):
                if marker not in workflow_text:
                    findings.append(
                        "Harness CI workflow must stay scoped to Harness-owned changes "
                        f"and retain manual dispatch; missing marker: {marker}"
                    )
    return findings


def runtime_module_findings(root: Path) -> list[str]:
    """Validate cohesive runtime ownership while preserving thin public façades."""
    findings: list[str] = []
    runtime = root / ".harness" / "runtime"
    required = {
        "runtime_support.py": {"run", "git", "load_config", "resolve_mainline", "read_land_state"},
        "kernel.py": {"cmd_repo_status", "cmd_repo_bootstrap", "cmd_land_prepare", "cmd_land_merge"},
        "composition.py": {"composition_selection", "require_operating_composition", "configure_bootstrap_composition"},
        "project_model.py": {"active_project_model", "spec_topology_state", "cmd_spec_topology", "cmd_spec_affected"},
        "collaboration_model.py": {"active_collaboration_model", "cmd_collaboration_configure", "cmd_handoff_publish", "cmd_handoff_accept"},
        "checker_manifest.py": {"manifest_composition_findings", "routing_findings", "vocabulary_findings"},
        "checker_semantic.py": {"load_constitutional_invariants", "semantic_surface", "semantic_evidence_findings"},
        "checker_architecture.py": {"distribution_evidence_findings", "runtime_module_findings", "composition_findings"},
        "checker.py": {"cmd_check", "cmd_assure", "run_assurance_verification"},
        "extensions.py": {"extension_registry", "resolve_extension", "cmd_extension_list", "cmd_extension_resolve"},
        "harness.py": {"build_parser", "main", "print_result", "set_runtime_context"},
    }
    runtime_modules = {Path(name).stem for name in required}
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
                    if top in runtime_modules:
                        deps.add(top)
            elif isinstance(node, ast.ImportFrom) and node.module:
                top = node.module.split(".", 1)[0]
                if top in runtime_modules:
                    deps.add(top)
                    if any(alias.name == "*" for alias in node.names):
                        wildcards.append(top)
        local_imports[filename] = deps
        wildcard_imports[filename] = wildcards
        for name in sorted(expected - names):
            findings.append(f"runtime module {filename} is missing owned symbol: {name}")

    allowed_dependencies = {
        "runtime_support.py": set(),
        "kernel.py": {"runtime_support"},
        "composition.py": {"kernel"},
        "project_model.py": {"kernel"},
        "collaboration_model.py": {"kernel"},
        "checker_manifest.py": {"kernel", "project_model", "collaboration_model"},
        "checker_semantic.py": {"kernel"},
        "checker_architecture.py": set(),
        "checker.py": {"kernel", "collaboration_model", "checker_manifest", "checker_semantic", "checker_architecture"},
        "extensions.py": {"kernel"},
        "harness.py": {"runtime_support", "kernel", "composition", "project_model", "collaboration_model", "checker", "extensions"},
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
    low_level_support = {"run", "git", "git_input", "load_config", "resolve_mainline", "read_land_state", "write_land_state"}
    for name in sorted(kernel_defs & low_level_support):
        findings.append(f"kernel owns low-level runtime-support symbol that belongs in runtime_support.py: {name}")
    forbidden_kernel = {
        "active_project_model", "spec_topology_state", "scope_closure",
        "active_collaboration_model", "read_collaboration_state",
        "cmd_collaboration_configure", "cmd_collaboration_status",
        "cmd_handoff_publish", "cmd_handoff_withdraw", "cmd_handoff_accept", "cmd_handoff_release",
        "cmd_check", "cmd_assure",
        "composition_selection", "require_operating_composition", "configure_bootstrap_composition",
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
                findings.append(f"Harness composition version {release!r} does not match runtime VERSION {version!r}")

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
            explicitly_unconfigured = project_model is None and collaboration_model is None
            partially_configured = (project_model is None) != (collaboration_model is None)
            if partially_configured:
                findings.append(
                    "active composition must either leave both Project/Collaboration models explicitly unconfigured "
                    "or select both"
                )
            elif not explicitly_unconfigured:
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
            supported_by_dimension: dict[str, list[str]] = {}
            for key, selected in dimensions:
                values = supported.get(key)
                if not isinstance(values, list) or any(not isinstance(item, str) or not item for item in values):
                    findings.append(f"supported {key} must be a list of non-empty ids")
                    continue
                supported_by_dimension[key] = values
                if len(set(values)) != len(values):
                    findings.append(f"supported {key} must not contain duplicates")
                if isinstance(selected, str) and selected and selected not in values:
                    findings.append(f"active {key[:-1]} is not supported by this distribution: {selected}")

            supported_methods = supported.get("method_packs")
            if not isinstance(supported_methods, list) or any(not isinstance(item, str) or not item for item in supported_methods):
                findings.append("supported method_packs must be a list of non-empty ids")
                supported_methods = []
            if isinstance(method_packs, list):
                for method in method_packs:
                    if method not in supported_methods:
                        findings.append(f"active method pack is not supported by this distribution: {method}")

            if isinstance(sources, dict):
                for source_key, selected in dimensions:
                    mapping = sources.get(source_key)
                    if not isinstance(mapping, dict):
                        findings.append(f"composition sources.{source_key} must be an object")
                        continue
                    components_to_validate = set(supported_by_dimension.get(source_key, []))
                    if isinstance(selected, str) and selected:
                        components_to_validate.add(selected)
                    for component in sorted(components_to_validate):
                        rel = mapping.get(component)
                        if not isinstance(rel, str) or not rel.startswith(".harness/"):
                            findings.append(f"{source_key[:-1]} has no .harness source binding: {component}")
                        elif not (root / rel).exists():
                            findings.append(f"{source_key[:-1]} source is missing: {rel}")

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
            "project-reasoning",
            "project-model/spec",
            "project-model/repository-native",
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
