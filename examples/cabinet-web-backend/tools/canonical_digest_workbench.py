from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CLOSURE_SCHEMA = "spec_workbench_canonical_digest_backend_closure.v1"
RULE_KEY = "canonical_digest_backend"


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def closed_backend(project: Path) -> dict[str, Any] | None:
    """Return the exact assembled canonical digest IR only when its lineage is closed."""
    closure_path = project / "70_canonical_digest_closure.json"
    spec_path = project / "global_spec.json"
    if not closure_path.is_file() or not spec_path.is_file():
        return None
    try:
        closure = _load(closure_path)
        spec = _load(spec_path)
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return None
    backend = closure.get("backend_ir") if isinstance(closure, dict) else None
    assembled = spec.get("rules", {}).get(RULE_KEY) if isinstance(spec, dict) else None
    if (
        closure.get("schema_version") != CLOSURE_SCHEMA
        or closure.get("status") != "closed"
        or not isinstance(backend, dict)
        or backend != assembled
    ):
        return None
    return backend


def _recipes(backend: dict[str, Any]) -> list[str]:
    recipes = backend.get("recipes")
    return [str(name) for name in recipes] if isinstance(recipes, dict) else []


def structured_addresses(project: Path) -> set[str]:
    backend = closed_backend(project)
    if backend is None:
        return set()
    root = f"rules.{RULE_KEY}"
    return {root, f"{root}.recipes"} | {f"{root}.recipes.{name}" for name in _recipes(backend)}


def deterministic_method_scopes(project: Path) -> set[str]:
    backend = closed_backend(project)
    return set(_recipes(backend)) if backend is not None else set()


def module_slice(project: Path, module: str) -> dict[str, Any] | None:
    backend = closed_backend(project)
    if backend is None or backend.get("wiring", {}).get("module") != module:
        return None
    return {
        "enabled": True,
        "backend_ir": backend,
        "deterministic_method_scopes": sorted(deterministic_method_scopes(project)),
    }
