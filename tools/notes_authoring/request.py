"""The structure request (tools/DATA_CLOSURE_WORKBENCH.md §5).

A writer that finds no home for a value stops the module and returns one; it
never writes the value into prose and never invents a home. The request
lives in `<case>/notes_authoring/<module>/requests.json` on the case branch:
the input of the next run and the operator's evidence. The gate does not
close it; a change of a source does (§5.3), and a request whose `absence`
digests no longer match the current namespaces is stale — to recheck, not to
keep open.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from notes_authoring.index import SpecIndex

SCHEMA = "spec_workbench_structure_request.v1"
FILE_SCHEMA = "spec_workbench_structure_requests.v1"
VALUE_KINDS = frozenset({"threshold", "path", "rate", "coefficient", "allow_list", "mapping", "enumeration", "other"})
ROUTES = frozenset({"state6", "author", "owner"})
REQUIRED_NAMESPACES = frozenset({"models", "rules", "config"})
DIRECTORY = "notes_authoring"


def path_for(project: Path, module: str) -> Path:
    return project / DIRECTORY / module / "requests.json"


def _string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value)


def validate(request: Any, module: str) -> list[str]:
    """Every reason the request is not one; empty when it is."""
    if not isinstance(request, dict):
        return ["a structure request is a JSON object"]
    errors = []
    if request.get("schema_version") != SCHEMA:
        errors.append(f"schema_version must be {SCHEMA}")
    if request.get("module") != module:
        errors.append(f"module must be {module!r}")
    if not isinstance(request.get("need"), str) or not request["need"].strip():
        errors.append("need: one sentence of what the note must say")
    if request.get("value_kind") not in VALUE_KINDS:
        errors.append(f"value_kind must be one of {sorted(VALUE_KINDS)}")
    if request.get("route") not in ROUTES:
        errors.append(f"route must be one of {sorted(ROUTES)}")
    if not _string_list(request.get("candidate_values")) or not request["candidate_values"]:
        errors.append("candidate_values: the values as the writer sees them, each with its source")
    sources = request.get("sources")
    if not isinstance(sources, list) or not sources or not all(
        isinstance(s, dict) and isinstance(s.get("path"), str) and type(s.get("line")) is int
        and isinstance(s.get("quote"), str) and s["quote"].strip() for s in sources
    ):
        errors.append("sources: a non-empty list of {path, line, quote} from the design texts")
    absence = request.get("absence")
    # §15.10: "no home" is the result of a search, never an assumption.
    if not isinstance(absence, dict) or not _string_list(absence.get("terms")) or not absence["terms"]:
        errors.append("absence.terms: the terms find_absence searched")
    elif not isinstance(absence.get("namespaces"), dict) or not REQUIRED_NAMESPACES <= set(absence["namespaces"]):
        errors.append(f"absence.namespaces: the digests find_absence gave for {sorted(REQUIRED_NAMESPACES)}")
    considered = request.get("homes_considered", [])
    if not isinstance(considered, list) or not all(
        isinstance(h, dict) and isinstance(h.get("home"), str) and isinstance(h.get("why_not"), str) for h in considered
    ):
        errors.append("homes_considered: a list of {home, why_not}")
    if not _string_list(request.get("blocked_notes")) or not request["blocked_notes"]:
        errors.append("blocked_notes: the notes the missing home holds back, as '<scope>: <class>'")
    return errors


def stale(request: dict[str, Any], index: SpecIndex) -> bool:
    """True when a namespace the absence was proven over has changed since."""
    current = index.absence([])["namespaces"]
    proven = (request.get("absence") or {}).get("namespaces") or {}
    return any(current.get(name) != digest for name, digest in proven.items())


def load(project: Path, module: str) -> list[dict[str, Any]]:
    path = path_for(project, module)
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return list(payload.get("requests") or [])


def write(project: Path, module: str, requests: list[dict[str, Any]]) -> Path:
    path = path_for(project, module)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": FILE_SCHEMA, "module": module, "requests": requests}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def clear(project: Path, module: str) -> None:
    path = path_for(project, module)
    if path.is_file():
        path.unlink()
        if not any(path.parent.iterdir()):
            path.parent.rmdir()


def status(project: Path, index: SpecIndex) -> dict[str, Any]:
    """Per module: open and stale requests, with their routes (decision Q17)."""
    root = project / DIRECTORY
    modules: dict[str, Any] = {}
    for path in sorted(root.glob("*/requests.json")) if root.is_dir() else []:
        module = path.parent.name
        rows = []
        for request in load(project, module):
            rows.append({"need": request.get("need"), "route": request.get("route"),
                         "value_kind": request.get("value_kind"), "stale": stale(request, index)})
        modules[module] = {
            "open": sum(not row["stale"] for row in rows),
            "stale": sum(row["stale"] for row in rows),
            "requests": rows,
        }
    return {"schema_version": "spec_workbench_structure_request_status.v1", "modules": modules}
