#!/usr/bin/env python3
"""Static manifest, documentation, routing, and contract checks for Harness."""
from __future__ import annotations

import json
import re
from pathlib import Path

from kernel import HarnessError
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
    """Validate shared Project-reasoning authority orchestrators."""
    active_path = root / ".harness" / "composition" / "active.json"
    if not active_path.exists():
        return []
    try:
        active = json.loads(active_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []  # composition_findings owns malformed composition diagnostics
    selection = active.get("selection") if isinstance(active, dict) else None
    supported = active.get("supported") if isinstance(active, dict) else None
    selected_model = selection.get("project_model") if isinstance(selection, dict) else None
    supported_models = supported.get("project_models") if isinstance(supported, dict) else []
    if selected_model is None and not isinstance(supported_models, list):
        return []
    findings: list[str] = []
    contract_ref = "Authority Orchestrator Contract"
    for name in ("domain", "app", "style", "tech"):
        path = root / ".harness" / "capabilities" / f"{name}.md"
        if not path.exists():
            findings.append(f"Project reasoning authority orchestrator is missing: {path.relative_to(root)}")
            continue
        text = path.read_text(encoding="utf-8")
        if not re.search(r"(?m)^##\s+Orchestration\s*$", text):
            findings.append(f"{path.relative_to(root)} missing authority-orchestrator Orchestration section")
        if contract_ref not in text:
            findings.append(f"{path.relative_to(root)} does not reference the Authority Orchestrator Contract")
        if "Project Authority Target Contract" not in text:
            findings.append(f"{path.relative_to(root)} does not reference the Project Authority Target Contract")
    return findings


def repository_native_contract_findings(root: Path) -> list[str]:
    """Validate the repository-native model and transient Goal-Spec binding."""
    findings: list[str] = []
    model = root / ".harness" / "project-models" / "repository-native.md"
    target = root / ".harness" / "contracts" / "project-authority-target-contract.md"
    required_model = ("[REPO-NATIVE-01]", "Goal Spec", "doc/goals/<branch>.spec.md", "repository-native is not code-as-spec", "Project Authority Target Contract")
    required_target = ("[TARGET-01]", "repository-native", "transient Goal Spec", "implementation", "spec")
    if not model.exists():
        findings.append("missing Repository-native Project model: .harness/project-models/repository-native.md")
    else:
        text = model.read_text(encoding="utf-8")
        findings.extend(f"Repository-native Project model missing required concept: {item}" for item in required_model if item not in text)
    if not target.exists():
        findings.append("missing Project Authority Target Contract")
    else:
        text = target.read_text(encoding="utf-8")
        findings.extend(f"Project Authority Target Contract missing required concept: {item}" for item in required_target if item not in text)
    active = root / ".harness" / "composition" / "active.json"
    if active.exists():
        try:
            data = json.loads(active.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        supported_models = data.get("supported", {}).get("project_models") if isinstance(data, dict) else None
        sources = data.get("sources", {}).get("project_models") if isinstance(data, dict) else None
        if isinstance(supported_models, list) and "repository-native" in supported_models:
            if not isinstance(sources, dict) or sources.get("repository-native") != ".harness/project-models/repository-native.md":
                findings.append("supported repository-native Project model has no canonical source binding")
    return findings


def extension_package_findings(root: Path) -> list[str]:
    """Validate committed project Extension packages without constraining third-party skill semantics."""
    findings: list[str] = []
    definition = root / ".harness" / "extensions" / "definition.md"
    if not definition.exists():
        findings.append("missing Extension definition: .harness/extensions/definition.md")
    project_root = root / ".harness" / "extensions" / "project"
    if project_root.exists():
        valid_id = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
        for path in sorted(project_root.iterdir(), key=lambda p: p.name):
            if path.name.startswith("."):
                continue
            if not path.is_dir():
                findings.append(f"project Extension entry must be a directory: {path.relative_to(root)}")
                continue
            if not valid_id.fullmatch(path.name):
                findings.append(f"project Extension id is invalid: {path.name!r}")
            if not (path / "SKILL.md").is_file():
                findings.append(f"project Extension is missing SKILL.md: {path.relative_to(root)}")
    gitignore = root / ".gitignore"
    if gitignore.exists() and ".harness/extensions/local/" not in gitignore.read_text(encoding="utf-8"):
        findings.append(".gitignore must ignore developer-local Extension packages at .harness/extensions/local/")
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
    active_path = root / ".harness" / "composition" / "active.json"
    spec_supported = False
    if active_path.exists():
        try:
            active = json.loads(active_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            active = {}
        supported = active.get("supported") if isinstance(active, dict) else None
        spec_supported = (
            isinstance(supported, dict)
            and isinstance(supported.get("project_models"), list)
            and "spec" in supported.get("project_models", [])
        )
    if (active_project_model(root) == "spec" or spec_supported) and model.exists():
        model_text = model.read_text(encoding="utf-8")
        if "spec-topology.md" not in model_text:
            findings.append("supported Spec Project model does not bind the Spec topology contract")
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
    try:
        model = active_collaboration_model(root)
    except HarnessError:
        # composition_findings owns malformed/unsupported active-composition diagnostics.
        model = None
    if model == "cooperative-multi-user":
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
