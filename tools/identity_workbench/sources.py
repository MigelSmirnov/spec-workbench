from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from identity_workbench.model import Finding, IdentityWorkbenchError, SourceIdentity

MODEL_HEADING = re.compile(r"^## Model M\d+ — (?P<name>[^\n]+)", re.MULTILINE)
IDENTITY_SECTION = re.compile(r"^### Identity\s*\n\s*(?P<identity>value|entity)\s*$", re.MULTILINE)

def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise IdentityWorkbenchError(f"Cannot read {path}: {error}") from error
    if not isinstance(payload, dict):
        raise IdentityWorkbenchError(f"{path} must contain a JSON object.")
    return payload

def load_state1(project: Path) -> tuple[dict[str, SourceIdentity], list[Finding]]:
    records: dict[str, SourceIdentity] = {}
    findings: list[Finding] = []
    for path in sorted(project.glob("01_models*.md")):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as error:
            raise IdentityWorkbenchError(f"Cannot read {path}: {error}") from error
        headings = list(MODEL_HEADING.finditer(text))
        for index, heading in enumerate(headings):
            name = heading.group("name").strip()
            end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
            match = IDENTITY_SECTION.search(text, heading.end(), end)
            if not match:
                continue
            line = text.count("\n", 0, heading.start()) + 1
            record = SourceIdentity(match.group("identity"), f"{path.name}:{line}")
            if name in records:
                findings.append(Finding("duplicate_state1_model", f"{name} has more than one canonical State 1 model record.", name, record.location))
            records[name] = record
    return records, findings

def load_closure(project: Path) -> tuple[dict[str, SourceIdentity], list[Finding]]:
    records: dict[str, SourceIdentity] = {}
    findings: list[Finding] = []
    for path in sorted(project.glob("60_model_closure_*.json")):
        models = _read_json(path).get("models", {})
        if not isinstance(models, dict):
            raise IdentityWorkbenchError(f"{path}: models must be an object.")
        for name, model in models.items():
            if not isinstance(model, dict) or model.get("kind"):
                continue
            identity = model.get("identity")
            if identity not in {"value", "entity"}:
                findings.append(Finding("invalid_closure_identity", f"{name} has invalid model-closure identity {identity!r}.", name, path.name))
                continue
            record = SourceIdentity(identity, path.name)
            if name in records:
                findings.append(Finding("duplicate_closure_model", f"{name} appears in more than one model-closure file.", name, path.name))
            records[name] = record
    return records, findings

def load_assembled(project: Path) -> tuple[dict[str, SourceIdentity], list[Finding]]:
    path = project / "global_spec.json"
    models = _read_json(path).get("models", {})
    if not isinstance(models, dict):
        raise IdentityWorkbenchError(f"{path}: models must be an object.")
    records: dict[str, SourceIdentity] = {}
    findings: list[Finding] = []
    for name, model in models.items():
        if not isinstance(model, dict) or model.get("kind"):
            continue
        identity = model.get("identity")
        if identity not in {"value", "entity"}:
            findings.append(Finding("invalid_assembled_identity", f"{name} has invalid assembled identity {identity!r}.", name, path.name))
            continue
        records[name] = SourceIdentity(identity, path.name)
    return records, findings
