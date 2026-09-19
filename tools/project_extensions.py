"""Project-declared Workbench extensions.

Generic tools must not import product-specific modules by name. A project may
declare deterministic backends and project-local deterministic gates in
``<project>/workbench_extensions.json`` and ships each implementation inside
its own directory. Generic tooling loads only the declared protocol and never
learns the product's name.

```json
{
  "schema_version": "spec_workbench_project_extensions.v1",
  "deterministic_backends": [
    {"id": "holded_transport", "module": "tools/holded_transport_workbench.py"}
  ],
  "project_gates": [
    {"id": "domain_clock", "module": "tools/project_gate.py"}
  ]
}
```

Each backend module must expose:

- ``structured_addresses(project) -> set[str]`` — addresses the backend IR
  makes resolvable for State 7 notes;
- ``deterministic_method_scopes(project) -> set[str]`` — callables fully owned
  by the closed backend IR (no note required);
- ``module_slice(project, module) -> dict | None`` — the module-scoped lowering
  evidence for Stage 8.1 review, or ``None`` when the module owns nothing.

Each project-gate module must expose:

- ``run_gate(project) -> dict`` — a deterministic report with schema
  ``spec_workbench_project_gate_result.v1``, boolean ``ready``, a summary
  containing integer ``errors`` / ``warnings``, and a list of findings.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

EXTENSIONS_FILE = "workbench_extensions.json"
SCHEMA = "spec_workbench_project_extensions.v1"
REQUIRED_CALLABLES = ("structured_addresses", "deterministic_method_scopes", "module_slice")
GATE_CALLABLE = "run_gate"
_ID_CHARS = set("abcdefghijklmnopqrstuvwxyz0123456789_")


class ProjectExtensionError(ValueError):
    pass


@dataclass(frozen=True)
class DeterministicBackendExtension:
    id: str
    path: Path
    module: ModuleType

    def structured_addresses(self, project: Path) -> set[str]:
        return set(self.module.structured_addresses(project))

    def deterministic_method_scopes(self, project: Path) -> set[str]:
        return set(self.module.deterministic_method_scopes(project))

    def module_slice(self, project: Path, module: str) -> dict[str, Any] | None:
        return self.module.module_slice(project, module)


@dataclass(frozen=True)
class ProjectGateExtension:
    id: str
    path: Path
    module: ModuleType

    def run_gate(self, project: Path) -> dict[str, Any]:
        return self.module.run_gate(project)


def _load_module(extension_id: str, path: Path, *, kind: str) -> ModuleType:
    name = f"workbench_extension_{kind}_{extension_id}"
    cached = sys.modules.get(name)
    if cached is not None and getattr(cached, "__file__", None) == str(path):
        return cached
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ProjectExtensionError(f"extension {extension_id!r}: cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _manifest_payload(project: Path) -> tuple[Path, dict[str, Any] | None]:
    project = project.resolve()
    manifest = project / EXTENSIONS_FILE
    if not manifest.is_file():
        return manifest, None
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ProjectExtensionError(f"{manifest.name}: invalid JSON: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA:
        raise ProjectExtensionError(f"{manifest.name}: expected schema_version {SCHEMA}")
    return manifest, payload


def _declared_entries(project: Path, field: str, *, kind: str) -> list[dict[str, Any]]:
    project = project.resolve()
    manifest, payload = _manifest_payload(project)
    if payload is None:
        return []
    entries = payload.get(field, [])
    if not isinstance(entries, list):
        raise ProjectExtensionError(f"{manifest.name}: {field} must be a list")
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ProjectExtensionError(f"{manifest.name}: each {kind} must be an object")
        extension_id = entry.get("id")
        module = entry.get("module")
        if not isinstance(extension_id, str) or not extension_id or set(extension_id) - _ID_CHARS:
            raise ProjectExtensionError(f"{manifest.name}: {kind} id must be a snake_case identifier")
        if extension_id in seen:
            raise ProjectExtensionError(f"{manifest.name}: duplicate {kind} id {extension_id!r}")
        if not isinstance(module, str) or not module:
            raise ProjectExtensionError(f"{manifest.name}: {kind} {extension_id!r} needs a module path")
        path = (project / module).resolve()
        if project not in path.parents or not path.is_file():
            raise ProjectExtensionError(
                f"{manifest.name}: {kind} {extension_id!r} module must be a file inside the project"
            )
        seen.add(extension_id)
        result.append({"id": extension_id, "module": module, "path": path})
    return result


def declared_backends(project: Path) -> list[dict[str, Any]]:
    """Return the raw backend declarations, validated but not loaded."""
    return _declared_entries(project, "deterministic_backends", kind="backend")


def declared_project_gates(project: Path) -> list[dict[str, Any]]:
    """Return raw project-gate declarations, validated but not loaded."""
    return _declared_entries(project, "project_gates", kind="project gate")


def deterministic_backends(project: Path) -> list[DeterministicBackendExtension]:
    """Load every deterministic backend the project declares."""
    result: list[DeterministicBackendExtension] = []
    for entry in declared_backends(project):
        module = _load_module(entry["id"], entry["path"], kind="backend")
        missing = [name for name in REQUIRED_CALLABLES if not callable(getattr(module, name, None))]
        if missing:
            raise ProjectExtensionError(
                f"backend {entry['id']!r} ({entry['module']}) lacks required callables: {', '.join(missing)}"
            )
        result.append(DeterministicBackendExtension(id=entry["id"], path=entry["path"], module=module))
    return result



def project_gates(project: Path) -> list[ProjectGateExtension]:
    """Load every deterministic gate declared by a project."""
    result: list[ProjectGateExtension] = []
    for entry in declared_project_gates(project):
        module = _load_module(entry["id"], entry["path"], kind="gate")
        if not callable(getattr(module, GATE_CALLABLE, None)):
            raise ProjectExtensionError(
                f"project gate {entry['id']!r} ({entry['module']}) lacks required callable: {GATE_CALLABLE}"
            )
        result.append(ProjectGateExtension(id=entry["id"], path=entry["path"], module=module))
    return result
