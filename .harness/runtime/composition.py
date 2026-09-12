#!/usr/bin/env python3
"""Harness composition runtime mechanics.

Owns the explicit bootstrap-time transition from the standalone distribution's
unconfigured composition state to one supported operating composition, and the
runtime guard that prevents normal lifecycle work before that decision exists.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from kernel import PROJECT_ROOT, atomic_json, fail, harness_version

COMPOSITION_SCHEMA_VERSION = 1
SUPPORTED_PROJECT_MODELS = frozenset({"spec", "repository-native"})
SUPPORTED_COLLABORATION_MODELS = frozenset({"single-user", "cooperative-multi-user"})
UNSUPPORTED_PROJECT_MODELS: dict[str, str] = {}



def composition_path(root: Path) -> Path:
    return root / ".harness" / "composition" / "active.json"


def _load_object(root: Path) -> dict[str, Any]:
    path = composition_path(root)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        fail(f"invalid Harness composition: cannot read {path.relative_to(root)}: {exc}")
    except json.JSONDecodeError as exc:
        fail(f"invalid Harness composition JSON: {exc}")
    if not isinstance(data, dict):
        fail("invalid Harness composition: active.json must be a JSON object")
    if data.get("schema_version") != COMPOSITION_SCHEMA_VERSION:
        fail(
            "invalid Harness composition: active.json must use "
            f"schema_version {COMPOSITION_SCHEMA_VERSION}"
        )
    release = data.get("release")
    if release != harness_version():
        fail(
            "invalid Harness composition: active.json release does not match runtime VERSION "
            f"({release!r} != {harness_version()!r})"
        )
    selection = data.get("selection")
    if not isinstance(selection, dict):
        fail("invalid Harness composition: selection must be an object")
    return data


def composition_selection(root: Path) -> dict[str, Any]:
    return dict(_load_object(root)["selection"])


def composition_is_unconfigured(root: Path) -> bool:
    selection = composition_selection(root)
    return selection.get("project_model") is None and selection.get("collaboration_model") is None


def require_operating_composition(root: Path | None = None) -> dict[str, str]:
    """Require a fully supported Project + Collaboration selection.

    The standalone distribution intentionally starts with both selections null.
    Normal lifecycle/model operation is blocked until bootstrap records the user's
    explicit decisions.
    """
    root = (root or PROJECT_ROOT).resolve()
    selection = composition_selection(root)
    project_model = selection.get("project_model")
    collaboration_model = selection.get("collaboration_model")

    if project_model is None and collaboration_model is None:
        fail(
            "Harness composition is unconfigured; bootstrap must explicitly select Project model `spec` or `repository-native` "
            "and one Collaboration model (`single-user` or `cooperative-multi-user`) before normal lifecycle work"
        )
    if project_model is None or collaboration_model is None:
        fail(
            "invalid Harness composition: Project model and Collaboration model must either both be unconfigured "
            "or both be explicitly selected"
        )
    if not isinstance(project_model, str) or not project_model.strip():
        fail("invalid Harness composition: project_model must be a non-empty string")
    if not isinstance(collaboration_model, str) or not collaboration_model.strip():
        fail("invalid Harness composition: collaboration_model must be a non-empty string")
    project_model = project_model.strip()
    collaboration_model = collaboration_model.strip()
    if project_model not in SUPPORTED_PROJECT_MODELS:
        if project_model in UNSUPPORTED_PROJECT_MODELS:
            fail(UNSUPPORTED_PROJECT_MODELS[project_model])
        fail(f"invalid Harness composition Project model: unsupported selection {project_model!r}")
    if collaboration_model not in SUPPORTED_COLLABORATION_MODELS:
        fail(f"invalid Harness composition Collaboration model: unsupported selection {collaboration_model!r}")
    return {
        "project_model": project_model,
        "collaboration_model": collaboration_model,
    }


def configure_bootstrap_composition(
    root: Path,
    *,
    project_model: str | None,
    collaboration_model: str | None,
) -> dict[str, Any]:
    """Persist the user's bootstrap operating choices without silently defaulting them."""
    data = _load_object(root)
    selection = data["selection"]
    current_project = selection.get("project_model")
    current_collaboration = selection.get("collaboration_model")

    if current_project is not None or current_collaboration is not None:
        current = require_operating_composition(root)
        if project_model is not None and project_model != current["project_model"]:
            fail(
                "Harness composition is already configured; bootstrap will not change the Project model "
                f"from {current['project_model']!r} to {project_model!r}"
            )
        if collaboration_model is not None and collaboration_model != current["collaboration_model"]:
            fail(
                "Harness composition is already configured; bootstrap will not change the Collaboration model "
                f"from {current['collaboration_model']!r} to {collaboration_model!r}"
            )
        return {"result": "already configured", **current}

    if project_model is None:
        fail(
            "bootstrap requires an explicit Project-model decision: choose `spec` or `repository-native`"
        )
    if project_model in UNSUPPORTED_PROJECT_MODELS:
        fail(UNSUPPORTED_PROJECT_MODELS[project_model])
    if project_model not in SUPPORTED_PROJECT_MODELS:
        fail(
            f"bootstrap Project model {project_model!r} is not supported by this Harness distribution; choose `spec` or `repository-native`"
        )
    if collaboration_model is None:
        fail(
            "bootstrap requires an explicit Collaboration-model decision: choose `single-user` or "
            "`cooperative-multi-user`; no default is applied"
        )
    if collaboration_model not in SUPPORTED_COLLABORATION_MODELS:
        fail(
            f"bootstrap Collaboration model {collaboration_model!r} is unsupported; choose `single-user` or "
            "`cooperative-multi-user`"
        )

    selection["project_model"] = project_model
    selection["collaboration_model"] = collaboration_model
    atomic_json(composition_path(root), data)
    return {
        "result": "configured",
        "project_model": project_model,
        "collaboration_model": collaboration_model,
    }
