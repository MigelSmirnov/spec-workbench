from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_GATE_PATH = Path(__file__).resolve().parents[2] / "skills" / "spec-authoring" / "note_gate.json"


def load_gate_table() -> dict[str, Any]:
    payload = json.loads(_GATE_PATH.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "spec_workbench_note_gate.v1":
        raise ValueError("unsupported note gate schema")
    classes = payload.get("classes")
    pairs = payload.get("suspicious_pairs")
    if not isinstance(classes, dict) or not isinstance(pairs, list):
        raise ValueError("invalid note gate table")
    return payload


_GATE = load_gate_table()
NOTE_CLASSES = frozenset(_GATE["classes"])
REFERENCE_CLASS_PREFIX = {
    name: entry["requires_reference"]
    for name, entry in _GATE["classes"].items()
    if isinstance(entry, dict) and isinstance(entry.get("requires_reference"), str)
}
SINGLETON_CLASSES = frozenset(
    name
    for name, entry in _GATE["classes"].items()
    if isinstance(entry, dict) and entry.get("cardinality") == "single_per_scope"
)
SUSPICIOUS_CLASS_PAIRS = {
    frozenset(entry["classes"]): entry["reason"]
    for entry in _GATE["suspicious_pairs"]
    if isinstance(entry, dict)
    and isinstance(entry.get("classes"), list)
    and len(entry["classes"]) == 2
    and isinstance(entry.get("reason"), str)
}
