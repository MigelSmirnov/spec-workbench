from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from types import ModuleType
from typing import Any

from .model import EvidenceGraph, EvidenceRef


FACTORY_ROOT_ENV = "SPEC_WORKBENCH_FACTORY_ROOT"


def _load_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("spec_workbench_factory_route_b_affected", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _factory_root(project: Path, explicit: Path | None) -> Path | None:
    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(explicit)
    configured = os.environ.get(FACTORY_ROOT_ENV)
    if configured:
        candidates.append(Path(configured))
    for parent in [project, *project.parents]:
        candidates.append(parent / "code_factory")
        candidates.append(parent.parent / "code_factory")
    for candidate in candidates:
        if (candidate / "tools" / "route_b_affected.py").is_file():
            return candidate.resolve()
    return None


def _factory_project(project: Path, explicit: str | None) -> str | None:
    if explicit:
        return explicit
    target = project / "90_factory_target.json"
    if not target.is_file():
        return None
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    value = payload.get("factory_project") if isinstance(payload, dict) else None
    return value if isinstance(value, str) and value else None


def _edges(mapping: dict[str, set[str]]) -> set[tuple[str, str]]:
    return {(consumer, provider) for consumer, providers in mapping.items() for provider in providers if consumer != provider}


def classify_edge_sets(
    workbench_edges: set[tuple[str, str]],
    merged_edges: set[tuple[str, str]],
) -> tuple[set[tuple[str, str]], set[tuple[str, str]], set[tuple[str, str]]]:
    """Return compiler-derived, undesigned, and Workbench-only relations."""
    extra = merged_edges - workbench_edges
    compiler_derived = {(consumer, provider) for consumer, provider in extra if provider == "models"}
    undesigned = extra - compiler_derived
    missing_in_factory = workbench_edges - merged_edges
    return compiler_derived, undesigned, missing_in_factory


def compare(
    graph: EvidenceGraph,
    *,
    factory_root: Path | None = None,
    factory_project: str | None = None,
) -> dict[str, Any]:
    root = _factory_root(graph.project, factory_root)
    project_name = _factory_project(graph.project, factory_project)
    if root is None:
        return {"available": False, "reason": f"Factory checkout not found; pass --factory-root or set {FACTORY_ROOT_ENV}"}
    if project_name is None:
        return {"available": False, "reason": "90_factory_target.json has no factory_project; pass --factory-project"}
    project_dir = root / "projects" / project_name
    spec_path = project_dir / "specs" / "base" / "global_spec.json"
    local_specs = project_dir / "specs" / "local_specs"
    if not spec_path.is_file() or not local_specs.is_dir():
        return {"available": False, "project": project_name, "reason": "Factory base spec or local_specs are unavailable"}
    try:
        factory = _load_module(root / "tools" / "route_b_affected.py")
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        import_map = factory.import_to_module_map(spec)
        modules = set(factory.module_paths(spec))
        merged, _, unresolved = factory.merged_dependency_graph(spec, local_specs, import_map, modules)
    except (OSError, ValueError, json.JSONDecodeError, ImportError) as exc:
        return {"available": False, "project": project_name, "reason": str(exc)}

    workbench_edges = {
        (edge.source.removeprefix("module:"), edge.target.removeprefix("module:"))
        for edge in graph.edges
        if edge.kind == "module_dependency"
    }
    merged_edges = _edges(merged)
    compiler_derived, undesigned, missing_in_factory = classify_edge_sets(workbench_edges, merged_edges)
    return {
        "available": True,
        "project": project_name,
        "source": str(spec_path),
        "declared_workbench_edges": sorted([list(edge) for edge in workbench_edges]),
        "factory_merged_edges": sorted([list(edge) for edge in merged_edges]),
        "compiler_derived_filtered_edges": [
            {"consumer": consumer, "provider": provider, "class": "model_context"}
            for consumer, provider in sorted(compiler_derived)
        ],
        "dependency_not_designed": sorted([list(edge) for edge in undesigned]),
        "workbench_edges_missing_from_factory": sorted([list(edge) for edge in missing_in_factory]),
        "unresolved_factory_imports": unresolved,
        "counts": {
            "declared_workbench_edges": len(workbench_edges),
            "factory_merged_edges": len(merged_edges),
            "compiler_derived_filtered_edges": len(compiler_derived),
            "dependency_not_designed": len(undesigned),
        },
        "evidence": EvidenceRef("factory", f"{project_name}:merged_dependency_graph").to_dict(),
    }
