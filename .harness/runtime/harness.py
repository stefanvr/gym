#!/usr/bin/env python3
"""Harness deterministic runtime command-line entry point.

Runtime ownership is split across kernel, composition, Project-model, Collaboration-model,
and checker modules. This file only wires commands and preserves a convenient
import surface for runtime tests/tooling.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parent
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

import runtime_support as runtime_support
import kernel as kernel
import composition as composition
import project_model as project_model
import collaboration_model as collaboration_model
import checker as checker
import extensions as extensions

# Re-export runtime symbols for tests and embedding tools that use the CLI module as a facade.
from kernel import *
from composition import *
from project_model import *
from collaboration_model import *
from checker import *
from extensions import *


def set_runtime_context(project_root: Path, config_path: Path | None = None) -> None:
    """Point every runtime module at one repository (primarily for tests/embedding)."""
    root = Path(project_root).resolve()
    config = Path(config_path).resolve() if config_path is not None else root / ".harness" / "runtime" / "config.json"
    for module in (runtime_support, kernel, composition, project_model, collaboration_model, checker, extensions):
        module.PROJECT_ROOT = root
        module.CONFIG_PATH = config
    globals()["PROJECT_ROOT"] = root
    globals()["CONFIG_PATH"] = config

def print_result(data: dict[str, Any]) -> None:
    print(json.dumps(data, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="harness", description="Harness deterministic Git/runtime mechanics")
    sub = parser.add_subparsers(dest="command", required=True)

    repo = sub.add_parser("repo", help="repository discovery/bootstrap")
    repo_sub = repo.add_subparsers(dest="repo_command", required=True)
    p = repo_sub.add_parser("status")
    p.set_defaults(func=cmd_repo_status)
    p = repo_sub.add_parser("bootstrap")
    p.add_argument("--message", default="chore: establish repository baseline")
    p.add_argument(
        "--project-model",
        help="explicit Project model for an unconfigured install: `spec` or `repository-native`",
    )
    p.add_argument(
        "--collaboration-model",
        help="explicit Collaboration model for an unconfigured install: `single-user` or `cooperative-multi-user`",
    )
    p.add_argument(
        "--main-shadow",
        action="store_true",
        help="onboard an existing committed repository by creating/using `main-shadow` as Harness configured mainline while leaving the repository's original mainline untouched",
    )
    seed = p.add_mutually_exclusive_group()
    seed.add_argument("--all-seed-files", action="store_true", help="explicitly stage all non-ignored seed files with `git add -A`")
    seed.add_argument("--seed-path", action="append", default=[], help="stage only this seed path; repeat for multiple paths")
    p.add_argument("--require-clean", action="store_true", help="require a clean tree before baseline creation")
    p.set_defaults(func=cmd_repo_bootstrap)

    branch = sub.add_parser("branch", help="work-branch mechanics")
    branch_sub = branch.add_subparsers(dest="branch_command", required=True)
    p = branch_sub.add_parser("start")
    p.add_argument("--name", required=True)
    p.add_argument("--base")
    p.add_argument("--reuse", action="store_true")
    p.set_defaults(func=cmd_branch_start)

    approval = sub.add_parser("approval", help="mechanical approval-ref operations; ownership remains in skills")
    approval_sub = approval.add_subparsers(dest="approval_command", required=True)
    for name, func in (("record", cmd_approval_record), ("validate", cmd_approval_validate), ("drop", cmd_approval_drop)):
        p = approval_sub.add_parser(name)
        p.add_argument("--branch")
        p.set_defaults(func=func)

    collaboration = sub.add_parser("collaboration", help="local cooperative collaboration actor/role configuration")
    collaboration_sub = collaboration.add_subparsers(dest="collaboration_command", required=True)
    p = collaboration_sub.add_parser("configure")
    p.add_argument("--actor", required=True)
    p.add_argument("--role", choices=["contributor", "integration-authority"], required=True)
    p.set_defaults(func=cmd_collaboration_configure)
    p = collaboration_sub.add_parser("status")
    p.set_defaults(func=cmd_collaboration_status)

    handoff = sub.add_parser("handoff", help="immutable cooperative Goal handoff through configured remote")
    handoff_sub = handoff.add_subparsers(dest="handoff_command", required=True)
    p = handoff_sub.add_parser("publish")
    p.add_argument("--branch")
    p.add_argument("--approved-by", help="coordination provenance only; not cryptographic authorization")
    p.set_defaults(func=cmd_handoff_publish)
    p = handoff_sub.add_parser("withdraw")
    p.add_argument("--branch", required=True)
    p.set_defaults(func=cmd_handoff_withdraw)
    p = handoff_sub.add_parser("accept")
    p.add_argument("--branch", required=True)
    p.set_defaults(func=cmd_handoff_accept)
    p = handoff_sub.add_parser("release")
    p.add_argument("--branch", required=True)
    p.set_defaults(func=cmd_handoff_release)

    p = sub.add_parser("resume", help="reconstruct deterministic Git/lifecycle transaction facts")
    p.set_defaults(func=cmd_resume)

    land = sub.add_parser("land", help="guarded landing transaction")
    land_sub = land.add_subparsers(dest="land_command", required=True)
    p = land_sub.add_parser("assess", help="report READY_FOR_LANDING or human-resolvable LANDING_BLOCKED evidence")
    p.add_argument("--branch")
    p.set_defaults(func=cmd_land_assess)
    p = land_sub.add_parser("prepare")
    p.add_argument("--branch")
    p.set_defaults(func=cmd_land_prepare)
    p = land_sub.add_parser("merge")
    p.add_argument("--branch")
    p.add_argument("--message")
    p.add_argument("--delete-remote", action="store_true")
    p.set_defaults(func=cmd_land_merge)
    p = land_sub.add_parser("abort")
    p.add_argument("--branch")
    p.set_defaults(func=cmd_land_abort)

    abandon = sub.add_parser("abandon", help="guarded branch discard")
    abandon_sub = abandon.add_subparsers(dest="abandon_command", required=True)
    p = abandon_sub.add_parser("discard")
    p.add_argument("--target", required=True)
    p.add_argument("--mode", choices=["no-op", "explicit"], required=True)
    p.add_argument("--delete-remote", action="store_true")
    p.set_defaults(func=cmd_abandon_discard)

    project = sub.add_parser("project", help="active Project-model authority inspection")
    project_sub = project.add_subparsers(dest="project_command", required=True)
    p = project_sub.add_parser("status", help="report authority placement for the current Goal branch")
    p.add_argument("--branch")
    p.set_defaults(func=cmd_project_status)

    extension = sub.add_parser("extension", help="list/resolve installed Harness skill Extensions")
    extension_sub = extension.add_subparsers(dest="extension_command", required=True)
    p = extension_sub.add_parser("list", help="list project and local Extension packages")
    p.set_defaults(func=cmd_extension_list)
    p = extension_sub.add_parser("resolve", help="resolve one Extension entrypoint without executing it")
    p.add_argument("--id", required=True)
    p.add_argument("--scope", choices=["project", "local"])
    p.set_defaults(func=cmd_extension_resolve)

    spec = sub.add_parser("spec", help="Spec Project-model topology inspection")
    spec_sub = spec.add_subparsers(dest="spec_command", required=True)
    p = spec_sub.add_parser("topology", help="validate and report the active Spec scope topology")
    p.set_defaults(func=cmd_spec_topology)
    p = spec_sub.add_parser("affected", help="resolve scoped loading and graph-check closure")
    p.add_argument("--scope", action="append", required=True, help="stable Spec scope id; repeat for multiple changed scopes")
    p.set_defaults(func=cmd_spec_affected)

    p = sub.add_parser("check", help="run deterministic Harness internal-consistency checks")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("assure", help="report profile-qualified Harness Assurance from current evidence")
    p.add_argument("--profile", required=True, help="exact provider/model/profile being assured")
    p.set_defaults(func=cmd_assure)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        exempt_from_operating_composition = (
            args.command in {"check", "assure", "extension"}
            or (args.command == "repo" and getattr(args, "repo_command", None) in {"status", "bootstrap"})
        )
        if not exempt_from_operating_composition:
            composition.require_operating_composition(PROJECT_ROOT)

        if command_mutates_lifecycle(args):
            with lifecycle_mutation_lock(args):
                composition_result = None
                if args.command == "repo" and getattr(args, "repo_command", None) == "bootstrap":
                    if getattr(args, "main_shadow", False):
                        preflight_main_shadow_bootstrap(args)
                    composition_result = composition.configure_bootstrap_composition(
                        PROJECT_ROOT,
                        project_model=getattr(args, "project_model", None),
                        collaboration_model=getattr(args, "collaboration_model", None),
                    )
                data = args.func(args)
                if composition_result is not None:
                    data["composition"] = composition_result
        else:
            data = args.func(args)
        print_result(data)
        if args.command == "check" and data.get("finding_count", 0):
            return 1
        if args.command == "spec" and getattr(args, "spec_command", None) == "topology" and data.get("finding_count", 0):
            return 1
        if args.command == "assure" and data.get("result") != "GREEN":
            return 1
        return 0
    except HarnessError as exc:
        print(json.dumps({"error": str(exc)}, indent=2), file=sys.stderr)
        return 2
    except Exception as exc:
        print(
            json.dumps(
                {
                    "error": f"unexpected runtime failure: {type(exc).__name__}: {exc}",
                    "error_kind": "unexpected",
                },
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
