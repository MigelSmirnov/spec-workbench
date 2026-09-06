from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CLOSURE_SCHEMA = "spec_workbench_holded_transport_backend_closure.v1"
METHODS = ("__init__", "create_purchase", "list_purchases", "get_purchase")


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def closed_backend(project: Path) -> dict[str, Any] | None:
    """Return exact assembled Holded IR only when its lineage is closed."""
    closure_path = project / "70_holded_transport_closure.json"
    spec_path = project / "global_spec.json"
    if not closure_path.is_file() or not spec_path.is_file():
        return None
    try:
        closure = _load(closure_path)
        spec = _load(spec_path)
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return None
    backend = closure.get("backend_ir") if isinstance(closure, dict) else None
    assembled = spec.get("rules", {}).get("holded_transport_backend") if isinstance(spec, dict) else None
    if (
        closure.get("schema_version") != CLOSURE_SCHEMA
        or closure.get("status") != "closed"
        or not isinstance(backend, dict)
        or backend != assembled
    ):
        return None
    return backend


def structured_addresses(project: Path) -> set[str]:
    return {"rules.holded_transport_backend"} if closed_backend(project) is not None else set()


def deterministic_method_scopes(project: Path) -> set[str]:
    backend = closed_backend(project)
    if backend is None:
        return set()
    wiring = backend.get("wiring", {})
    concrete_class = wiring.get("concrete_class") if isinstance(wiring, dict) else None
    if not isinstance(concrete_class, str) or not concrete_class:
        return set()
    return {f"{concrete_class}.{method}" for method in METHODS}


def module_slice(project: Path, module: str) -> dict[str, Any] | None:
    backend = closed_backend(project)
    if backend is None or backend.get("wiring", {}).get("module") != module:
        return None
    return {
        "enabled": True,
        "backend_ir": backend,
        "deterministic_method_scopes": sorted(deterministic_method_scopes(project)),
    }
