"""Index of declared model fields, enum kinds and class surfaces for one case."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from notes_workbench.language import signature_parameters

# Methods every pydantic model exposes; notes may name them without declaring them.
PYDANTIC_API = frozenset({
    "model_validate", "model_validate_json", "model_dump", "model_dump_json",
    "model_copy", "model_json_schema", "model_fields", "model_construct",
})
_WRAPPERS = ("tuple[", "list[", "set[", "frozenset[", "dict[", "Optional[", "Sequence[", "Mapping[")


def _snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def scalar_type(annotation: str) -> str | None:
    """The single named type an annotation resolves to, or None for unions of
    several types, containers and builtins."""
    text = annotation.strip()
    parts = [part.strip() for part in text.split("|")]
    parts = [part for part in parts if part and part != "None"]
    if len(parts) != 1:
        return None
    text = parts[0]
    if text.startswith("Optional[") and text.endswith("]"):
        text = text[len("Optional["):-1].strip()
    if any(text.startswith(w) for w in _WRAPPERS) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", text):
        return None
    return text.rsplit(".", 1)[-1]


@dataclass
class ClassSurface:
    name: str
    kind: str                         # model | enum | interface | class
    fields: dict[str, str] = field(default_factory=dict)
    methods: set[str] = field(default_factory=set)
    init_params: dict[str, str] = field(default_factory=dict)
    source: str = ""

    @property
    def attributes(self) -> set[str]:
        return set(self.fields) | self.methods | set(self.init_params)

    def attribute_type(self, attribute: str) -> str | None:
        annotation = self.fields.get(attribute) or self.init_params.get(attribute)
        return scalar_type(annotation) if annotation else None

    def accepts(self, attribute: str) -> bool:
        if self.kind == "enum":
            return True
        if attribute in self.attributes:
            return True
        return bool(self.fields) and attribute in PYDANTIC_API


@dataclass
class ModelIndex:
    classes: dict[str, ClassSurface] = field(default_factory=dict)
    contracts: dict[str, str] = field(default_factory=dict)
    modules: set[str] = field(default_factory=set)
    closure_files: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, project: Path) -> "ModelIndex":
        index = cls()
        for path in sorted(project.glob("60_model_closure*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            models = payload.get("models")
            if not isinstance(models, dict):
                continue
            index.closure_files.append(path.name)
            for name, declared in models.items():
                if not isinstance(name, str) or not isinstance(declared, dict):
                    continue
                fields = declared.get("fields")
                kind = str(declared.get("kind") or "")
                if kind == "enum" or isinstance(declared.get("values"), list) and not fields:
                    surface_kind = "enum"
                elif kind == "interface":
                    surface_kind = "interface"
                elif isinstance(fields, dict):
                    surface_kind = "model"
                else:
                    surface_kind = "class"
                index.classes[name] = ClassSurface(
                    name=name, kind=surface_kind,
                    fields={k: str(v) for k, v in fields.items()} if isinstance(fields, dict) else {},
                    source=path.name,
                )
        contracts_path = project / "60_contracts.json"
        if contracts_path.is_file():
            payload = json.loads(contracts_path.read_text(encoding="utf-8"))
            contracts = payload.get("contracts")
            if isinstance(contracts, dict):
                for name, signature in contracts.items():
                    if not isinstance(name, str) or not isinstance(signature, str):
                        continue
                    index.contracts[name] = signature
                    if "." not in name:
                        continue
                    owner, method = name.split(".", 1)
                    surface = index.classes.setdefault(owner, ClassSurface(name=owner, kind="class", source="60_contracts.json"))
                    if method == "__init__":
                        surface.init_params = {
                            p: t for p, t in signature_parameters(signature) if p != "self"
                        }
                    else:
                        surface.methods.add(method)
        modules_path = project / "30_modules.md"
        if modules_path.is_file():
            text = modules_path.read_text(encoding="utf-8")
            index.modules = set(re.findall(r"`module:([A-Za-z_][A-Za-z0-9_]*)`", text))
            index.modules |= set(re.findall(r"^##\s+`([A-Za-z_][A-Za-z0-9_]*)`\s*$", text, re.MULTILINE))
        return index

    def surface(self, type_name: str | None) -> ClassSurface | None:
        if not type_name:
            return None
        return self.classes.get(type_name)

    def scope_bindings(self, scope: str) -> dict[str, str]:
        """Names a note may use inside ``scope`` and their declared types:
        contract parameters, and ``self`` for a method scope."""
        bindings: dict[str, str] = {}
        signature = self.contracts.get(scope)
        if signature:
            for name, annotation in signature_parameters(signature):
                if name == "self":
                    continue
                bindings[name] = annotation
        if "." in scope:
            owner = scope.split(".", 1)[0]
            if owner in self.classes:
                bindings["self"] = owner
        return bindings

    def field_types(self, field_name: str) -> set[str]:
        """Declared types of every field or __init__ parameter named ``field_name``
        across the case, restricted to types the index can describe."""
        result: set[str] = set()
        for surface in self.classes.values():
            annotation = surface.fields.get(field_name) or surface.init_params.get(field_name)
            target = scalar_type(annotation) if annotation else None
            if target and target in self.classes:
                result.add(target)
        return result

    def classes_named(self, noun: str) -> set[str]:
        """Classes whose snake-cased name carries ``noun`` as a whole segment:
        prose names a value by a noun of its model (``item`` may be an
        ``EstimateItemSnapshot``)."""
        result: set[str] = set()
        for name in self.classes:
            if noun in _snake(name).split("_") or _snake(name) == noun:
                result.add(name)
        return result

    def reachable_fields(self, root_types: list[str], depth: int = 3) -> dict[str, set[str]]:
        """Field name -> set of declared types reachable from the root types
        through model fields; a bare field name in prose is resolved only when
        exactly one type carries it."""
        result: dict[str, set[str]] = {}
        seen: set[str] = set()
        frontier = [(t, 0) for t in root_types]
        while frontier:
            type_name, level = frontier.pop()
            surface = self.surface(type_name)
            if surface is None or type_name in seen or level > depth:
                continue
            seen.add(type_name)
            for attribute, annotation in {**surface.fields, **surface.init_params}.items():
                target = scalar_type(annotation)
                if target and target in self.classes:
                    result.setdefault(attribute, set()).add(target)
                    frontier.append((target, level + 1))
        return result
