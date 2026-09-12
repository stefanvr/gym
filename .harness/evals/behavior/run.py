#!/usr/bin/env python3
"""Small provider-neutral behavioral regression harness for LLM lifecycle decisions.

A runner command receives one JSON request on stdin and must emit one JSON object
on stdout with: {"decision": str, "actions": [str, ...], "claims": [str, ...]}.
The evaluator intentionally withholds expected outcomes from the runner.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import signal
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
MAX_RUNNER_TIMEOUT_SECONDS = 3600.0
SUITE_PATH = Path(__file__).resolve().with_name("scenarios.json")
AUTHORITY_PATHS = [
    ".harness/composition/definition.md",
    ".harness/composition/active.json",
    ".harness/project-models/spec.md",
    ".harness/project-models/spec-topology.md",
    ".harness/project-models/repository-native.md",
    ".harness/collaboration-models/single-user.md",
    ".harness/collaboration-models/cooperative-multi-user.md",
    ".harness/contracts/authority-orchestrator-contract.md",
    ".harness/contracts/project-authority-target-contract.md",
    ".harness/contracts/method-pack-contract.md",
    ".harness/discovery/definition.md",
    ".harness/extensions/definition.md",
    ".harness/harness/definition.md",
    ".harness/guides/definition.md",
    ".harness/workflow/WORKFLOW.md",
    ".harness/workflow/routing.md",
    ".harness/mechanisms/change-impact.md",
    ".harness/harness-limitations.md",
    ".harness/harness-assurance.md",
    ".harness/skills/lifecycle/branch-start.md",
    ".harness/skills/lifecycle/branch-land.md",
    ".harness/guides/git-history.md",
    ".harness/runtime/README.md",
]
INVARIANT_PATH = ROOT / ".harness" / "harness" / "invariants.json"
SEMANTIC_SURFACE_PATH = Path(__file__).resolve().with_name("semantic-surface.json")


class EvalError(RuntimeError):
    pass


def load_suite(path: Path = SUITE_PATH) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvalError(f"cannot load behavior suite: {exc}") from exc
    validate_suite(data)
    return data


def _nonempty_strings(value: Any, field: str, scenario_id: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise EvalError(f"{scenario_id}: {field} must be a list of non-empty strings")
    return value


def load_invariant_registry(path: Path = INVARIANT_PATH) -> dict[str, dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvalError(f"cannot load constitutional invariant registry: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise EvalError("constitutional invariant registry must use schema_version 1")
    rows = data.get("invariants")
    if not isinstance(rows, list) or not rows:
        raise EvalError("constitutional invariant registry must contain invariants")
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise EvalError("every constitutional invariant must be an object")
        iid = row.get("id")
        source = row.get("source")
        if not isinstance(iid, str) or not iid:
            raise EvalError("every constitutional invariant needs a non-empty id")
        if iid in result:
            raise EvalError(f"duplicate constitutional invariant id: {iid}")
        if not isinstance(source, str) or not source:
            raise EvalError(f"{iid}: source must be non-empty text")
        source_path = ROOT / source
        if not source_path.exists():
            raise EvalError(f"{iid}: authoritative source does not exist: {source}")
        if f"[{iid}]" not in source_path.read_text(encoding="utf-8"):
            raise EvalError(f"{iid}: authoritative source lacks marker [{iid}]")
        if not isinstance(row.get("behavior_required"), bool):
            raise EvalError(f"{iid}: behavior_required must be boolean")
        result[iid] = row
    return result


def validate_suite(data: dict[str, Any]) -> None:
    if not isinstance(data, dict) or data.get("schema_version") != 2:
        raise EvalError("behavior suite must be schema_version 2")
    action_catalog = set(_nonempty_strings(data.get("action_catalog"), "action_catalog", "suite"))
    decision_catalog = set(_nonempty_strings(data.get("decision_catalog"), "decision_catalog", "suite"))
    invariants = load_invariant_registry()
    scenarios = data.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise EvalError("behavior suite must contain at least one scenario")
    ids: set[str] = set()
    covered: set[str] = set()
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            raise EvalError("every behavior scenario must be an object")
        sid = scenario.get("id")
        if not isinstance(sid, str) or not sid:
            raise EvalError("every behavior scenario needs a non-empty id")
        if sid in ids:
            raise EvalError(f"duplicate behavior scenario id: {sid}")
        ids.add(sid)
        if not isinstance(scenario.get("family"), str) or not scenario["family"].strip():
            raise EvalError(f"{sid}: family must be non-empty text")
        covers = scenario.get("covers")
        if not isinstance(covers, list) or any(not isinstance(item, str) or not item for item in covers):
            raise EvalError(f"{sid}: covers must be a list of invariant ids")
        unknown_invariants = sorted(set(covers) - set(invariants))
        if unknown_invariants:
            raise EvalError(f"{sid}: covers unknown invariant ids: {', '.join(unknown_invariants)}")
        covered.update(covers)
        if not isinstance(scenario.get("situation"), str) or not scenario["situation"].strip():
            raise EvalError(f"{sid}: situation must be non-empty text")
        decision = scenario.get("expected_decision")
        if decision not in decision_catalog:
            raise EvalError(f"{sid}: expected_decision is not in decision_catalog: {decision!r}")
        for field in ("required_actions", "forbidden_actions", "ordered_actions"):
            values = _nonempty_strings(scenario.get(field, []), field, sid)
            unknown = sorted(set(values) - action_catalog)
            if unknown:
                raise EvalError(f"{sid}: {field} contains unknown actions: {', '.join(unknown)}")
        _nonempty_strings(scenario.get("forbidden_claims", []), "forbidden_claims", sid)
    required = sorted(iid for iid, row in invariants.items() if row.get("behavior_required") is True)
    missing = sorted(set(required) - covered)
    if missing:
        raise EvalError("behavior suite does not cover required constitutional invariants: " + ", ".join(missing))


def semantic_surface_digest(root: Path = ROOT) -> tuple[str, list[str]]:
    try:
        data = json.loads(SEMANTIC_SURFACE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvalError(f"cannot load semantic-surface configuration: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise EvalError("semantic-surface configuration must use schema_version 1")
    globs = data.get("include_globs")
    if not isinstance(globs, list) or not globs or any(not isinstance(item, str) or not item for item in globs):
        raise EvalError("semantic-surface include_globs must be a non-empty list of strings")
    matched: set[Path] = set()
    for pattern in globs:
        files = [path for path in root.glob(pattern) if path.is_file()]
        if not files:
            raise EvalError(f"semantic-surface glob matches no files: {pattern}")
        matched.update(files)
    paths = sorted(matched, key=lambda path: path.relative_to(root).as_posix())
    digest = hashlib.sha256()
    rels: list[str] = []
    for path in paths:
        rel = path.relative_to(root).as_posix()
        rels.append(rel)
        digest.update(rel.encode("utf-8") + b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest(), rels


def suite_digest(path: Path = SUITE_PATH) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def serialize_runner_request(payload: dict[str, Any]) -> str:
    """Return the exact deterministic JSON bytes presented to a runner."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def runner_request_sequence(suite: dict[str, Any], context: str) -> list[tuple[str, str]]:
    """Build each scenario request once as the exact string presented to the runner."""
    return [
        (scenario["id"], serialize_runner_request(runner_payload(suite, scenario, context)))
        for scenario in suite["scenarios"]
    ]


def digest_runner_request_sequence(requests: list[tuple[str, str]]) -> str:
    """Hash an ordered sequence of exact serialized runner requests without ambiguity."""
    digest = hashlib.sha256()
    for _scenario_id, request_text in requests:
        request = request_text.encode("utf-8")
        digest.update(len(request).to_bytes(8, "big"))
        digest.update(request)
    return digest.hexdigest()


def evaluation_input_digest(suite: dict[str, Any], context: str) -> str:
    """Hash exactly the serialized request sequence the constitutional evaluator presents."""
    return digest_runner_request_sequence(runner_request_sequence(suite, context))


def authority_context(root: Path = ROOT) -> str:
    sections = []
    for rel in AUTHORITY_PATHS:
        path = root / rel
        if not path.exists():
            raise EvalError(f"missing authority file required by behavior suite: {rel}")
        sections.append(f"\n===== {rel} =====\n{path.read_text(encoding='utf-8')}")
    return "".join(sections)


def runner_payload(suite: dict[str, Any], scenario: dict[str, Any], context: str) -> dict[str, Any]:
    return {
        "instruction": (
            "Follow the supplied Harness authority and active composition. Return only JSON matching response_schema. "
            "Classify concern/owner before precedence, use an authority orchestrator when broad concern decomposition is premature, "
            "keep method output non-authoritative until promoted by its Project owner, preserve the Harness/Project boundary and universal Guide semantics, "
            "propagate changed authority when relevant, and choose the decision/actions you would actually take. "
            "Do not invent completed manual work."
        ),
        "authority": context,
        "scenario": {"id": scenario["id"], "family": scenario["family"], "situation": scenario["situation"]},
        "decision_catalog": suite["decision_catalog"],
        "action_catalog": suite["action_catalog"],
        "response_schema": {"decision": "string", "actions": ["string"], "claims": ["string"]},
    }


def validate_response_shape(response: Any, scenario_id: str) -> dict[str, Any]:
    if not isinstance(response, dict):
        raise EvalError(f"{scenario_id}: runner response must be a JSON object")
    decision = response.get("decision")
    actions = response.get("actions")
    claims = response.get("claims", [])
    if not isinstance(decision, str) or not decision:
        raise EvalError(f"{scenario_id}: response decision must be a non-empty string")
    if not isinstance(actions, list) or any(not isinstance(item, str) for item in actions):
        raise EvalError(f"{scenario_id}: response actions must be a list of strings")
    if not isinstance(claims, list) or any(not isinstance(item, str) for item in claims):
        raise EvalError(f"{scenario_id}: response claims must be a list of strings")
    return {"decision": decision, "actions": actions, "claims": claims}


def evaluate_response(
    scenario: dict[str, Any],
    response: dict[str, Any],
    action_catalog: set[str] | None = None,
) -> list[str]:
    failures: list[str] = []
    if action_catalog is not None:
        unknown = sorted(set(response["actions"]) - action_catalog)
        if unknown:
            failures.append("unknown actions outside action_catalog: " + ", ".join(unknown))
    if response["decision"] != scenario["expected_decision"]:
        failures.append(
            f"decision {response['decision']!r} != expected {scenario['expected_decision']!r}"
        )
    actions = response["actions"]
    for action in scenario.get("required_actions", []):
        if action not in actions:
            failures.append(f"missing required action: {action}")
    for action in scenario.get("forbidden_actions", []):
        if action in actions:
            failures.append(f"performed forbidden action: {action}")
    ordered = scenario.get("ordered_actions", [])
    if ordered:
        positions = []
        for action in ordered:
            try:
                positions.append(actions.index(action))
            except ValueError:
                positions.append(-1)
        if -1 not in positions and positions != sorted(positions):
            failures.append("required actions occurred in the wrong order: " + " -> ".join(ordered))
    lowered_claims = "\n".join(response.get("claims", [])).lower()
    for claim in scenario.get("forbidden_claims", []):
        if claim.lower() in lowered_claims:
            failures.append(f"made forbidden completion claim: {claim}")
    return failures


def _terminate_runner_tree(proc: subprocess.Popen[str]) -> None:
    if proc.poll() is not None:
        return
    if os.name == "posix":
        try:
            os.killpg(proc.pid, signal.SIGKILL)
            return
        except (OSError, ProcessLookupError):
            pass
    elif os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            pass
        if proc.poll() is not None:
            return
    proc.kill()


def invoke_runner_request(command: str, request_text: str, timeout: float) -> dict[str, Any]:
    if not (0 < timeout <= MAX_RUNNER_TIMEOUT_SECONDS):
        raise EvalError(
            "runner timeout must be greater than 0 and no more than "
            f"{int(MAX_RUNNER_TIMEOUT_SECONDS)} seconds"
        )
    argv = shlex.split(command)
    if not argv:
        raise EvalError("--runner command is empty")
    kwargs: dict[str, Any] = {}
    if os.name == "posix":
        kwargs["start_new_session"] = True
    elif os.name == "nt" and hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    proc = subprocess.Popen(
        argv,
        text=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        **kwargs,
    )
    try:
        stdout, stderr = proc.communicate(input=request_text, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        _terminate_runner_tree(proc)
        try:
            proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            if proc.stdout is not None:
                proc.stdout.close()
            if proc.stderr is not None:
                proc.stderr.close()
            try:
                proc.kill()
                proc.wait(timeout=1)
            except (OSError, subprocess.TimeoutExpired):
                pass
        raise EvalError(f"runner timed out after {timeout:g}s") from exc
    if proc.returncode != 0:
        detail = stderr.strip() or stdout.strip() or f"exit {proc.returncode}"
        raise EvalError(f"runner failed: {detail}")
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise EvalError(f"runner did not emit valid JSON: {exc}") from exc


def invoke_runner(command: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    """Compatibility wrapper for callers that already hold a structured payload."""
    return invoke_runner_request(command, serialize_runner_request(payload), timeout)


def load_responses(path: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Any] | None]:
    result: dict[str, dict[str, Any]] = {}
    metadata: dict[str, Any] | None = None
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise EvalError(f"{path}:{lineno}: invalid JSON: {exc}") from exc
        if isinstance(row, dict) and row.get("type") == "capture":
            if metadata is not None:
                raise EvalError(f"{path}:{lineno}: duplicate capture metadata")
            schema_version = row.get("schema_version")
            if schema_version not in {1, 2}:
                raise EvalError(f"{path}:{lineno}: capture metadata must use schema_version 1 or 2")
            fields = ("profile", "suite_digest") if schema_version == 1 else ("profile", "evaluation_input_digest", "suite_digest")
            for field in fields:
                if not isinstance(row.get(field), str) or not row[field]:
                    raise EvalError(f"{path}:{lineno}: capture metadata needs non-empty {field}")
            metadata = row
            continue
        sid = row.get("id") if isinstance(row, dict) else None
        response = row.get("response") if isinstance(row, dict) else None
        if not isinstance(sid, str) or not isinstance(response, dict):
            raise EvalError(
                f"{path}:{lineno}: expected capture metadata or {{\"id\": str, \"response\": object}}"
            )
        if sid in result:
            raise EvalError(f"{path}:{lineno}: duplicate response id: {sid}")
        result[sid] = response
    return result, metadata


def capture_freshness(metadata: dict[str, Any] | None, input_digest: str, current_suite_digest: str) -> str:
    if metadata is None:
        return "unknown"
    # v1 captures were bound to a declared file inventory rather than the exact
    # evaluator requests, so they remain stale and cannot be current evidence.
    if metadata.get("schema_version") != 2:
        return "stale"
    if (
        metadata.get("evaluation_input_digest") == input_digest
        and metadata.get("suite_digest") == current_suite_digest
    ):
        return "current"
    return "stale"


def run_suite(suite: dict[str, Any], runner: str | None, responses_path: Path | None, timeout: float) -> dict[str, Any]:
    if bool(runner) == bool(responses_path):
        raise EvalError("provide exactly one of --runner or --responses")
    context = authority_context()
    requests = runner_request_sequence(suite, context)
    request_by_id = dict(requests)
    input_digest = digest_runner_request_sequence(requests)
    captured, capture_metadata = load_responses(responses_path) if responses_path else ({}, None)
    if responses_path:
        expected_ids = {scenario["id"] for scenario in suite["scenarios"]}
        extra_ids = sorted(set(captured) - expected_ids)
        if extra_ids:
            raise EvalError("responses file contains unknown scenario ids: " + ", ".join(extra_ids))
    action_catalog = set(suite["action_catalog"])
    results = []
    passed = 0
    for scenario in suite["scenarios"]:
        sid = scenario["id"]
        if runner:
            raw_response = invoke_runner_request(runner, request_by_id[sid], timeout)
        else:
            if sid not in captured:
                raise EvalError(f"responses file has no entry for scenario: {sid}")
            raw_response = captured[sid]
        response = validate_response_shape(raw_response, sid)
        failures = evaluate_response(scenario, response, action_catalog)
        ok = not failures
        passed += int(ok)
        results.append({"id": sid, "passed": ok, "failures": failures, "response": response})
    surface_digest, surface_files = semantic_surface_digest()
    current_suite_digest = suite_digest()
    return {
        "result": "pass" if passed == len(results) else "fail",
        "passed": passed,
        "total": len(results),
        "semantic_surface_digest": surface_digest,
        "semantic_surface_file_count": len(surface_files),
        "evaluation_input_digest": input_digest,
        "suite_digest": current_suite_digest,
        "capture_metadata": capture_metadata,
        "capture_freshness": capture_freshness(capture_metadata, input_digest, current_suite_digest) if responses_path else None,
        "results": results,
    }


def write_capture(path: Path, report: dict[str, Any], profile: str) -> None:
    if not profile.strip():
        raise EvalError("--profile must be non-empty when writing a response capture")
    rows = [{
        "type": "capture",
        "schema_version": 2,
        "profile": profile.strip(),
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "evaluation_input_digest": report["evaluation_input_digest"],
        "suite_digest": report["suite_digest"],
    }]
    rows.extend({"id": row["id"], "response": row["response"]} for row in report["results"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def write_evidence(path: Path, report: dict[str, Any], profile: str, evaluation_source: str) -> None:
    if report.get("result") != "pass":
        raise EvalError("refusing to write Assurance evidence for a failing behavior run")
    if not profile.strip():
        raise EvalError("--profile must be non-empty when writing evidence")
    if evaluation_source not in {"live_runner", "response_replay"}:
        raise EvalError("invalid evidence evaluation_source")
    payload = {
        "schema_version": 2,
        "profile": profile.strip(),
        "evaluation_source": evaluation_source,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "evaluation_input_digest": report["evaluation_input_digest"],
        "suite_digest": report["suite_digest"],
        "passed": report["passed"],
        "total": report["total"],
        "result": report["result"],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Harness LLM lifecycle behavioral regression suite")
    parser.add_argument("--runner", help="command that reads one JSON request from stdin and emits one JSON response")
    parser.add_argument("--responses", type=Path, help="JSONL file of captured model responses for deterministic replay")
    parser.add_argument("--timeout", type=float, default=60.0, help="per-scenario runner timeout in seconds")
    parser.add_argument("--validate-only", action="store_true", help="validate suite schema/authority files without invoking a model")
    parser.add_argument("--profile", help="LLM profile name used for response capture / Assurance evidence")
    parser.add_argument("--capture-out", type=Path, help="write model responses bound to current evaluation-input/suite digests")
    parser.add_argument("--evidence-out", type=Path, help="write passing Harness Assurance evidence metadata")
    args = parser.parse_args(argv)
    try:
        suite = load_suite()
        if args.validate_only:
            authority_context()
            digest, files = semantic_surface_digest()
            invariants = load_invariant_registry()
            covered = sorted({iid for scenario in suite["scenarios"] for iid in scenario.get("covers", [])})
            context = authority_context()
            print(json.dumps({
                "result": "valid",
                "assurance_scope": "constitutional",
                "scenario_count": len(suite["scenarios"]),
                "required_invariants": sorted(iid for iid, row in invariants.items() if row.get("behavior_required") is True),
                "covered_invariants": covered,
                "constitutional_authority_paths": AUTHORITY_PATHS,
                "evaluation_input_digest": evaluation_input_digest(suite, context),
                "semantic_surface_digest": digest,
                "semantic_surface_file_count": len(files),
                "suite_digest": suite_digest(),
            }, indent=2, sort_keys=True))
            return 0
        if not (0 < args.timeout <= MAX_RUNNER_TIMEOUT_SECONDS):
            raise EvalError(
                "--timeout must be greater than 0 and no more than "
                f"{int(MAX_RUNNER_TIMEOUT_SECONDS)} seconds"
            )
        report = run_suite(suite, args.runner, args.responses, args.timeout)
        if args.capture_out:
            if not args.runner:
                raise EvalError("--capture-out is only valid with --runner")
            if not args.profile:
                raise EvalError("--capture-out requires --profile")
            write_capture(args.capture_out, report, args.profile)
        if args.evidence_out:
            if not args.profile:
                raise EvalError("--evidence-out requires --profile")
            if args.responses:
                metadata = report.get("capture_metadata")
                if report.get("capture_freshness") != "current":
                    raise EvalError(
                        "response replay cannot create current Assurance evidence without capture metadata matching current evaluation-input and suite digests"
                    )
                if metadata.get("profile") != args.profile:
                    raise EvalError("--profile does not match response capture profile")
                source = "response_replay"
            else:
                source = "live_runner"
            write_evidence(args.evidence_out, report, args.profile, source)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["result"] == "pass" else 1
    except (EvalError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
