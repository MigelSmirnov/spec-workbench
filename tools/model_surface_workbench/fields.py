"""State 1 model fields must equal the model closure fields."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from model_surface_workbench.index import ModelIndex

REPORT_SCHEMA = "spec_workbench_model_field_closure.v1"
_MODEL_HEADING = re.compile(r"^## Model (?P<key>M\d+) — (?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*$")
_FIELD_LINE = re.compile(r"^- `(?P<name>[A-Za-z_][A-Za-z0-9_]*): (?P<type>.+?)`;?\s*$")


def design_models(project: Path) -> dict[str, dict[str, Any]]:
    """Model name -> {key, file, line, fields} for every State 1 section that
    declares an explicit ``Candidate fields:`` list. Prose-only sections are
    reported as unparsed, never judged."""
    result: dict[str, dict[str, Any]] = {}
    for path in sorted(project.glob("01_models_*.md")):
        current: dict[str, Any] | None = None
        in_fields = False
        for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            heading = _MODEL_HEADING.match(raw)
            if heading:
                current = {"key": heading.group("key"), "file": path.name, "line": number, "fields": None}
                result[heading.group("name")] = current
                in_fields = False
                continue
            if current is None:
                continue
            if raw.startswith("Candidate fields"):
                in_fields = True
                current["bullets"] = []
                continue
            if raw.startswith("#"):
                in_fields = False
                continue
            if in_fields and raw.startswith("- "):
                current["bullets"].append(raw)
    for info in result.values():
        bullets = info.pop("bullets", [])
        typed = [_FIELD_LINE.match(line) for line in bullets]
        # judge only a fully typed list; a prose field list is design text,
        # not a closed declaration, and stays unparsed
        if bullets and all(typed):
            info["fields"] = {m.group("name"): m.group("type").strip() for m in typed}
    return result


def _normalize_type(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def lint(project: Path) -> dict[str, Any]:
    index = ModelIndex.load(project)
    designed = design_models(project)
    findings: list[dict[str, Any]] = []
    compared = 0
    unparsed: list[str] = []

    def finding(code: str, message: str, model: str, info: dict[str, Any], **extra: Any) -> None:
        item = {"severity": "error", "code": code, "message": message, "model": model,
                "file": info["file"], "line": info["line"]}
        item.update(extra)
        findings.append(item)

    for name, info in sorted(designed.items()):
        fields = info["fields"]
        if fields is None:
            unparsed.append(name)
            continue
        surface = index.surface(name)
        if surface is None:
            finding("model_missing_in_closure",
                    f"{info['key']} {name} is designed in State 1 but no 60_model_closure*.json declares it.",
                    name, info)
            continue
        if surface.kind != "model":
            # enums and interfaces carry no field list to compare
            continue
        compared += 1
        for field_name, declared_type in fields.items():
            closure_type = surface.fields.get(field_name)
            if closure_type is None:
                finding("model_field_missing_in_closure",
                        f"{info['key']} {name}.{field_name}: {declared_type} is designed in State 1 but absent from {surface.source}; the projected specification and the generator will never see it.",
                        name, info, field=field_name)
            elif _normalize_type(closure_type) != _normalize_type(declared_type):
                finding("model_field_type_drift",
                        f"{info['key']} {name}.{field_name}: State 1 declares {declared_type!r}, {surface.source} declares {closure_type!r}.",
                        name, info, field=field_name)
        for field_name in surface.fields:
            if field_name not in fields:
                finding("model_field_undeclared_in_design",
                        f"{info['key']} {name}.{field_name} exists in {surface.source} but State 1 does not design it.",
                        name, info, field=field_name)

    errors = len(findings)
    return {
        "schema_version": REPORT_SCHEMA,
        "project_root": project.resolve().name,
        "summary": {
            "models_designed": len(designed),
            "models_compared": compared,
            "models_unparsed": len(unparsed),
            "closure_files": index.closure_files,
            "errors": errors,
            "handoff_ready": errors == 0,
        },
        "unparsed_models": unparsed,
        "findings": findings,
    }
