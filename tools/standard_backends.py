"""Shared deterministic-backend lineage adapters.

These adapters are platform tooling: they recognize backend IR kinds that are
part of SPEC_STANDARD and expose their closed lowering evidence to Notes and
Stage 8.1 review. Product branches provide only closure/spec data; they do not
ship executable Workbench modules for standard backends.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class StandardBackend:
    id: str
    closure_file: str
    closure_schema: str
    rule_key: str
    scope_mapping_path: tuple[str, ...] | None = None
    concrete_methods: tuple[str, ...] = ()

    def _load(self, path: Path) -> Any:
        return json.loads(path.read_text(encoding="utf-8"))

    def closed_backend(self, project: Path) -> dict[str, Any] | None:
        closure_path = project / self.closure_file
        spec_path = project / "global_spec.json"
        if not closure_path.is_file() or not spec_path.is_file():
            return None
        try:
            closure = self._load(closure_path)
            spec = self._load(spec_path)
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            return None
        if not isinstance(closure, dict) or not isinstance(spec, dict):
            return None
        backend = closure.get("backend_ir")
        assembled = (spec.get("rules") or {}).get(self.rule_key)
        if (
            closure.get("schema_version") != self.closure_schema
            or closure.get("status") != "closed"
            or not isinstance(backend, dict)
            or backend != assembled
        ):
            return None
        return backend

    def _mapping(self, backend: dict[str, Any]) -> dict[str, Any] | None:
        if self.scope_mapping_path is None:
            return None
        current: Any = backend
        for part in self.scope_mapping_path:
            if not isinstance(current, dict):
                return None
            current = current.get(part)
        return current if isinstance(current, dict) else None

    def structured_addresses(self, project: Path) -> set[str]:
        backend = self.closed_backend(project)
        if backend is None:
            return set()
        root = f"rules.{self.rule_key}"
        result = {root}
        mapping = self._mapping(backend)
        if mapping is not None and self.scope_mapping_path is not None:
            path = ".".join(self.scope_mapping_path)
            result.add(f"{root}.{path}")
            result |= {f"{root}.{path}.{name}" for name in mapping}
        return result

    def deterministic_method_scopes(self, project: Path) -> set[str]:
        backend = self.closed_backend(project)
        if backend is None:
            return set()
        mapping = self._mapping(backend)
        if mapping is not None:
            return set(mapping)
        if self.concrete_methods:
            wiring = backend.get("wiring")
            concrete = wiring.get("concrete_class") if isinstance(wiring, dict) else None
            if not isinstance(concrete, str) or not concrete:
                return set()
            return {f"{concrete}.{method}" for method in self.concrete_methods}
        return set()

    def module_slice(self, project: Path, module: str) -> dict[str, Any] | None:
        backend = self.closed_backend(project)
        if backend is None:
            return None
        wiring = backend.get("wiring")
        if not isinstance(wiring, dict) or wiring.get("module") != module:
            return None
        return {
            "enabled": True,
            "backend_ir": backend,
            "deterministic_method_scopes": sorted(self.deterministic_method_scopes(project)),
        }


STANDARD_BACKENDS = (
    StandardBackend(
        id="holded_transport",
        closure_file="70_holded_transport_closure.json",
        closure_schema="spec_workbench_holded_transport_backend_closure.v1",
        rule_key="holded_transport_backend",
        concrete_methods=("__init__", "create_purchase", "list_purchases", "get_purchase"),
    ),
    StandardBackend(
        id="canonical_digest",
        closure_file="70_canonical_digest_closure.json",
        closure_schema="spec_workbench_canonical_digest_backend_closure.v1",
        rule_key="canonical_digest_backend",
        scope_mapping_path=("recipes",),
    ),
)


def standard_backends(*, exclude_ids: set[str] | None = None) -> list[StandardBackend]:
    excluded = exclude_ids or set()
    return [backend for backend in STANDARD_BACKENDS if backend.id not in excluded]
