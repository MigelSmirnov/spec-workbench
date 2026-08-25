from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import design_index
import design_stage3

from module_review_workbench.model import ModuleReviewError

TYPE_NAME = re.compile(r"\b[A-Z][A-Za-z0-9_]*\b")
RULE_ADDRESS = re.compile(r"=\s*(rules(?:\.[A-Za-z_][A-Za-z0-9_]*)+)")

def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ModuleReviewError(f"Cannot read {path}: {error}") from error
    if not isinstance(payload, dict):
        raise ModuleReviewError(f"{path} must contain a JSON object.")
    return payload

def item_text(project: Path, item: dict[str, Any]) -> str:
    source = item["source"]
    lines = (project / source["path"]).read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[source["start_line"] - 1:source["end_line"]]).strip()

def decisions(project: Path, module_key: str) -> list[dict[str, Any]]:
    path = project / "30_trace.json"
    if not path.is_file():
        return []
    trace = load_json(path).get("decisions", {})
    result = []
    for key, relation in trace.items():
        if not isinstance(relation, dict):
            continue
        role = "owner" if relation.get("primary_owner") == module_key else (
            "consumer" if module_key in relation.get("consumers", []) else None
        )
        if role is None:
            continue
        item = design_index.get_item(project, key)
        result.append({
            "key": key, "role": role,
            "title": item["title"] if item else None,
            "text": item_text(project, item) if item else None,
            "source": item["source"] if item else None,
        })
    return result

def assembled_notes(spec: dict[str, Any], module: str, symbols: set[str]) -> list[dict[str, Any]]:
    result = []
    for index, raw in enumerate(spec.get("notes", [])):
        if not isinstance(raw, str) or ":" not in raw:
            continue
        scope, text = raw.split(":", 1)
        if scope != module and scope not in symbols:
            continue
        marker = re.match(r"\s*\[([A-Z_]+)\]\s*(.*)", text)
        result.append({
            "index": index, "scope": scope,
            "class": marker.group(1) if marker else None,
            "text": marker.group(2) if marker else text.strip(),
        })
    return result

def module_owned_persistence(project: Path, module: str, persistence_names: set[str]) -> set[str]:
    item = design_stage3.get_module(project, module)
    if item is None:
        return set()
    source = item["source"]
    lines = (project / source["path"]).read_text(encoding="utf-8").splitlines()
    module_lines = lines[source["start_line"] - 1:source["end_line"]]
    in_section = False
    in_fence = False
    result: set[str] = set()
    for raw in module_lines:
        stripped = raw.strip()
        if stripped.startswith("### "):
            in_section = stripped[4:].strip().casefold() == "owned persistent records"
            in_fence = False
            continue
        if not in_section:
            continue
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence and stripped in persistence_names:
            result.add(stripped)
    return result

def referenced_models(
    spec: dict[str, Any], contracts: dict[str, str], owned: set[str], extra: set[str] | None = None
) -> dict[str, Any]:
    models = spec.get("models", {})
    names = (set(models) & owned) | (set(models) & (extra or set())) | (
        set(models) & {token for signature in contracts.values() for token in TYPE_NAME.findall(signature)}
    )
    queue = list(names)
    while queue:
        name = queue.pop()
        declaration = models.get(name, {})
        for field_type in declaration.get("fields", {}).values() if isinstance(declaration, dict) else ():
            for token in TYPE_NAME.findall(str(field_type)):
                if token in models and token not in names:
                    names.add(token); queue.append(token)
    return {name: models[name] for name in sorted(names)}

def state1_models(project: Path, names: set[str]) -> list[dict[str, Any]]:
    result = []
    for item in design_index.list_items(project, state=1, kind="model"):
        title = item["title"]
        model_name = title.split("—", 1)[1].strip() if "—" in title else None
        if model_name not in names:
            continue
        result.append({
            "key": item["key"], "name": model_name, "title": title,
            "text": item_text(project, item), "source": item["source"],
        })
    return result

def rule_values(spec: dict[str, Any], notes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for address in sorted({a for note in notes for a in RULE_ADDRESS.findall(note["text"])}):
        value: Any = spec
        resolved = True
        for part in address.split("."):
            if not isinstance(value, dict) or part not in value:
                resolved = False; value = None; break
            value = value[part]
        result.append({"address": address, "resolved": resolved, "value": value})
    return result
