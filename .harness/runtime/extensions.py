#!/usr/bin/env python3
"""Deterministic Harness Extension discovery/resolution.

Extensions add agent capabilities but never authority. This module only reports
installed package entrypoints and resolves explicit ids; it never executes an
Extension or evaluates its semantic advice.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from kernel import PROJECT_ROOT, fail

EXTENSION_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def _scope_root(root: Path, scope: str) -> Path:
    if scope == "project":
        return root / ".harness" / "extensions" / "project"
    if scope == "local":
        return root / ".harness" / "extensions" / "local"
    fail(f"unknown Extension scope: {scope}")


def extension_registry(root: Path | None = None) -> list[dict[str, Any]]:
    base = (root or PROJECT_ROOT).resolve()
    rows: list[dict[str, Any]] = []
    for scope in ("project", "local"):
        scope_root = _scope_root(base, scope)
        if not scope_root.is_dir():
            continue
        for package in sorted(scope_root.iterdir(), key=lambda p: p.name):
            if not package.is_dir() or package.name.startswith("."):
                continue
            entry = package / "SKILL.md"
            rows.append(
                {
                    "id": package.name,
                    "scope": scope,
                    "valid_id": bool(EXTENSION_ID.fullmatch(package.name)),
                    "entrypoint": entry.relative_to(base).as_posix(),
                    "entrypoint_exists": entry.is_file(),
                }
            )
    return rows


def resolve_extension(extension_id: str, scope: str | None = None, root: Path | None = None) -> dict[str, Any]:
    if not EXTENSION_ID.fullmatch(extension_id):
        fail(f"invalid Extension id {extension_id!r}; use lowercase letters/numbers plus . _ -")
    rows = [row for row in extension_registry(root) if row["id"] == extension_id]
    if scope is not None:
        rows = [row for row in rows if row["scope"] == scope]
    rows = [row for row in rows if row["entrypoint_exists"] and row["valid_id"]]
    if not rows:
        label = f" in scope {scope!r}" if scope else ""
        fail(f"Extension {extension_id!r}{label} is not installed with a valid SKILL.md entrypoint")
    if len(rows) > 1:
        fail(
            f"Extension {extension_id!r} exists in both project and local scopes; "
            "select --scope project or --scope local explicitly"
        )
    return rows[0]


def cmd_extension_list(args: argparse.Namespace) -> dict[str, Any]:
    rows = extension_registry(PROJECT_ROOT)
    by_id: dict[str, list[str]] = {}
    for row in rows:
        by_id.setdefault(str(row["id"]), []).append(str(row["scope"]))
    collisions = sorted(extension_id for extension_id, scopes in by_id.items() if len(scopes) > 1)
    return {"extensions": rows, "collisions": collisions, "count": len(rows)}


def cmd_extension_resolve(args: argparse.Namespace) -> dict[str, Any]:
    return {"extension": resolve_extension(args.id, getattr(args, "scope", None), PROJECT_ROOT)}
