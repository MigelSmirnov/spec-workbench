"""What one module is, for the agent that writes its notes
(tools/DATA_CLOSURE_WORKBENCH.md §3): its callables with their signatures
(and its other symbols, such as exceptions),
the models those signatures name (fields and members are names a note may
write as words), what the design says the module does, and its open
structure requests. Data is not here: the agent reaches a value only through
its home (find_value_homes, resolve_data_address, find_absence)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from notes_authoring import request
from notes_authoring.index import SpecIndex

SCHEMA = "spec_workbench_notes_module_brief.v1"
DESIGN_KEYS = ("responsibility", "capabilities", "flows", "public_operations", "obligations")
_TYPE_NAME_RE = re.compile(r"\b[A-Z][A-Za-z0-9_]*\b")


def _models_named(signatures: dict[str, str], index: SpecIndex) -> dict[str, Any]:
    named = sorted({n for s in signatures.values() for n in _TYPE_NAME_RE.findall(s)}
                   & (set(index.fields) | set(index.enums)))
    return {
        name: ({"enum_members": list(index.enums[name])} if name in index.enums
               else {"fields": sorted(index.fields[name])})
        for name in named
    }


def build(project: Path, module: str, spec: dict[str, Any], slice_payload: dict[str, Any]) -> dict[str, Any]:
    index = SpecIndex.build(spec)
    callables = list((spec.get("module_functions") or {}).get(module) or [])
    contracts = spec.get("contracts") or {}
    signatures = {name: contracts[name] for name in callables if isinstance(contracts.get(name), str)}
    open_requests = [r for r in request.load(project, module) if not request.stale(r, index)]
    return {
        "schema_version": SCHEMA,
        "module": module,
        "standard_version": spec.get("standard_version"),
        "callables": signatures,
        "other_symbols": [name for name in callables if name not in signatures],
        "models_named": _models_named(signatures, index),
        "design": {key: slice_payload.get(key) for key in DESIGN_KEYS},
        "open_structure_requests": [{"need": r.get("need"), "route": r.get("route")} for r in open_requests],
    }
