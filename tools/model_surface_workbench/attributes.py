"""A note that reads ``value.attribute`` names an attribute the value has."""
from __future__ import annotations

import re
from typing import Any

from model_surface_workbench.index import ModelIndex, scalar_type

CODE = "note_attribute_unknown"
_DOTTED = re.compile(r"(?<![\w./=:])(?P<head>[A-Za-z_][A-Za-z0-9_]*)(?P<tail>(?:\.[A-Za-z_][A-Za-z0-9_]*)+)(?![\w/])")
# structured addresses resolve elsewhere; library and prose heads are not values
_SKIP_HEADS = frozenset({
    "config", "models", "rules", "module", "imports", "self_",
    "json", "hmac", "hashlib", "os", "re", "datetime", "timezone", "decimal",
    "uuid", "base64", "secrets", "time", "pathlib", "typing", "e", "i", "etc", "vs",
})
_SKIP_ATTRIBUTES = frozenset({
    "json", "py", "md", "txt", "csv", "pdf", "jpg", "jpeg", "png", "yaml", "yml",
    "html", "lock", "log", "sql", "com", "org", "net", "io", "e", "g",
})


def _bind_head(head: str, bindings: dict[str, str], index: ModelIndex) -> tuple[list[str], str]:
    """Return (candidate type names, how they were bound).

    A parameter or ``self`` binds one exact type. A bare prose noun binds to
    every declared field of that name across the case and to every class whose
    head noun it is: the author may mean any such value, so the attribute must
    be valid on at least one of them.
    """
    if head in bindings:
        bound = bindings[head] if head == "self" else scalar_type(bindings[head])
        return ([bound] if bound else []), "parameter"
    if head in index.classes:
        return [head], "class"
    candidates = sorted(index.field_types(head) | index.classes_named(head))
    return candidates, "noun"


def _walk(index: ModelIndex, type_name: str, attributes: list[str]) -> tuple[str | None, str | None, list[str]]:
    """Follow ``attributes`` from ``type_name``; return (rejecting type, rejected
    attribute, path walked) or (None, None, path) when every step resolves or
    the type becomes unknown."""
    path: list[str] = []
    current: str | None = type_name
    for attribute in attributes:
        surface = index.surface(current)
        if surface is None:
            return None, None, path
        if attribute in _SKIP_ATTRIBUTES and attribute not in surface.attributes:
            return None, None, path
        if not surface.accepts(attribute):
            return surface.name, attribute, path
        path.append(attribute)
        current = surface.attribute_type(attribute)
    return None, None, path


def findings(notes: list[dict[str, Any]], index: ModelIndex) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    if not index.classes:
        return result
    cache: dict[str, dict[str, str]] = {}
    for note in notes:
        scope = note.get("scope") or ""
        text = note.get("text") or ""
        if scope not in cache:
            cache[scope] = index.scope_bindings(scope)
        bindings = cache[scope]
        for match in _DOTTED.finditer(text):
            head = match.group("head")
            if head in _SKIP_HEADS or head.isupper() or (head in index.modules and head not in bindings):
                continue
            attributes = match.group("tail").lstrip(".").split(".")
            candidates, how = _bind_head(head, bindings, index)
            if not candidates:
                continue
            rejections = []
            for candidate in candidates:
                rejecting, attribute, path = _walk(index, candidate, attributes)
                if rejecting is None:
                    rejections = []
                    break
                rejections.append((rejecting, attribute, path))
            if not rejections:
                continue
            rejecting, attribute, path = rejections[0]
            surface = index.surface(rejecting)
            declared = sorted(surface.attributes) if surface else []
            walked = ".".join([head, *path])
            result.append({
                "severity": "block",
                "code": CODE,
                "message": (
                    f"{walked}.{attribute}: {rejecting} declares no attribute {attribute!r} "
                    f"({head} bound via {how} to {', '.join(candidates)}; declared: {', '.join(declared) or 'none'})."
                ),
                "line": note.get("line"),
                "scope": scope,
                "expression": f"{head}{match.group('tail')}",
                "type": rejecting,
                "attribute": attribute,
                "candidates": candidates,
                "hint": (
                    f"name the field {rejecting} actually declares, or add the field to "
                    f"State 1 and the model closure before the note relies on it"
                ),
            })
    return result
