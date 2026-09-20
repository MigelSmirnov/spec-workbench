"""Everything the lenses read, loaded from design-state artifacts alone.

No assembled ``global_spec.json`` is needed: contracts, their owning modules,
typed models, authored notes, State 3 collaborators, State 5 impacts and the
declared time policy all exist before the first assembly, which is exactly when
an unclosed value is cheap to close.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import design_closure_gaps
from model_surface_workbench.index import ModelIndex
from notes_workbench import gate as notes_gate
from notes_workbench.language import _iter_authored_notes, signature_parameters
from value_flow_workbench.model import ValueFlowError

_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_MODULE_SECTION = re.compile(r"^## `([A-Za-z_][A-Za-z0-9_]*)`\s*$", re.MULTILINE)
_KNOWS = re.compile(r"^### Knows\s*$(.*?)(?=^### |\Z)", re.MULTILINE | re.DOTALL)
_BACKTICKED = re.compile(r"`(?:module:)?([A-Za-z_][A-Za-z0-9_]*)`")
_DELEGATES = re.compile(r"^[-*\s]*\**delegates to\**\s*:\s*(.*?)\s*$", re.MULTILINE | re.IGNORECASE)


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueFlowError(f"cannot read {path.name}: {exc}") from exc


def declared_type(annotation: str) -> str:
    """``X | None = None`` declares the type ``X | None``."""
    return annotation.split(" = ", 1)[0].strip()


@dataclass
class Function:
    name: str
    module: str | None
    signature: str
    notes: list[str] = field(default_factory=list)

    @property
    def parameters(self) -> list[tuple[str, str]]:
        return [(name, declared_type(kind)) for name, kind in signature_parameters(self.signature) if name != "self"]

    @property
    def returns(self) -> str:
        return self.signature.rpartition("->")[2].strip()

    @property
    def note_text(self) -> str:
        return " ".join(self.notes)


@dataclass
class Case:
    project: Path
    index: ModelIndex
    functions: dict[str, Function]
    modules: set[str]
    module_functions: dict[str, set[str]]
    knows: dict[str, list[str]]
    read_only: set[str]
    mutating: set[str]                          # public operations State 5 does not make read-only
    instant_type: str | None
    wall_clock: tuple[str, str] | None          # (module, function) that hands out the instant
    deterministic_modules: set[str]

    def record_models(self, annotation: str) -> list[str]:
        """Models with declared fields that the annotation names, in order."""
        found: list[str] = []
        for name in _IDENTIFIER.findall(annotation):
            surface = self.index.classes.get(name)
            if surface is not None and surface.fields and name not in found:
                found.append(name)
        return found

    def module_notes(self, module: str) -> str:
        return " ".join(item.note_text for item in self.functions.values() if item.module == module)


def _time_policy(project: Path) -> tuple[str | None, tuple[str, str] | None]:
    """The canonical instant type and the accessor that hands it out, as the case declares them."""
    instant: str | None = None
    data = project / "60_data_closure.json"
    if data.is_file():
        sections = _load_json(data).get("sections")
        rules = sections.get("rules") if isinstance(sections, dict) else None
        policy = rules.get("time_source_policy") if isinstance(rules, dict) else None
        representation = policy.get("representation") if isinstance(policy, dict) else None
        if isinstance(representation, dict) and isinstance(representation.get("type"), str):
            instant = representation["type"]
    accessor: tuple[str, str] | None = None
    clock = project / "70_system_clock_closure.json"
    if clock.is_file():
        backend = _load_json(clock).get("backend_ir")
        wiring = backend.get("wiring") if isinstance(backend, dict) else None
        if isinstance(wiring, dict) and isinstance(wiring.get("module"), str):
            function = wiring.get("wall_clock_function") or wiring.get("function")
            if isinstance(function, str):
                accessor = (wiring["module"], function)
    return instant, accessor


def _knows(project: Path, modules: set[str]) -> dict[str, list[str]]:
    path = project / "30_modules.md"
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    parts = _MODULE_SECTION.split(text)
    result: dict[str, list[str]] = {}
    for position in range(1, len(parts), 2):
        module, body = parts[position], parts[position + 1]
        # A collaborator is a module named in Knows, or one a facade declares it delegates to.
        section = _KNOWS.search(body)
        text = (section.group(1) if section else "") + " " + " ".join(_DELEGATES.findall(body))
        named = [name for name in _BACKTICKED.findall(text) if name in modules and name != module]
        if named:
            result[module] = sorted(set(named))
    return result


def load(project: Path) -> Case:
    contracts_path, plan_path = project / "60_contracts.json", project / "60_contract_plan.json"
    if not contracts_path.is_file() or not plan_path.is_file():
        raise ValueFlowError("value flow is judged over State 6: 60_contracts.json and 60_contract_plan.json are required")
    index = ModelIndex.load(project)
    rows = _load_json(plan_path).get("functions")
    owners: dict[str, str] = {}
    for row in rows if isinstance(rows, list) else []:
        if isinstance(row, dict) and isinstance(row.get("function"), str) and isinstance(row.get("module"), str):
            owners[row["function"]] = row["module"].split(":", 1)[-1]
    notes: dict[str, list[str]] = {}
    for note in _iter_authored_notes(project):
        notes.setdefault(note["scope"], []).append(note["text"])
    functions = {
        name: Function(name=name, module=owners.get(name) or owners.get(name.split(".", 1)[0]),
                       signature=signature, notes=notes.get(name, []))
        for name, signature in index.contracts.items()
    }
    module_functions: dict[str, set[str]] = {}
    for item in functions.values():
        if item.module:
            module_functions.setdefault(item.module, set()).add(item.name.split(".", 1)[0])
    deterministic = notes_gate._load_deterministic_callable_scopes(project)
    deterministic_modules = {
        module for module, symbols in module_functions.items()
        if all(name.split(".", 1)[0] not in symbols or name in deterministic
               for name, item in functions.items() if item.module == module)
    }
    impacts = design_closure_gaps.parse_state_impacts(project)
    instant, accessor = _time_policy(project)
    modules = set(index.modules) | set(module_functions)
    return Case(
        project=project, index=index, functions=functions, modules=modules, module_functions=module_functions,
        knows=_knows(project, modules), read_only={name for name, row in impacts.items() if row["read_only"]},
        mutating={name for name, row in impacts.items() if not row["read_only"]},
        instant_type=instant, wall_clock=accessor, deterministic_modules=deterministic_modules,
    )
