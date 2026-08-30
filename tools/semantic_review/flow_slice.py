from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import design_stage4
from notes_workbench import gate, slice_builder


def _flow_key(value: str) -> str:
    return value if value.startswith("flow:") else f"flow:{value}"


def _load_contracts(project: Path) -> dict[str, str]:
    path = project / "60_contracts.json"
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    contracts = payload.get("contracts", {})
    return contracts if isinstance(contracts, dict) else {}


def _load_exceptions(project: Path) -> dict[str, Any]:
    path = project / "60_exception_taxonomy.json"
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _function_name(ref: str) -> str | None:
    if ref.startswith("capability:") or ref.startswith("public_op:"):
        tail = ref.split(":", 1)[1]
        if "." in tail:
            return tail.rsplit(".", 1)[1]
    return None


def _participating_scopes(flow: dict[str, Any], module_slices: list[dict[str, Any]]) -> set[str]:
    scopes: set[str] = set()
    for ref in flow.get("capability_refs", []):
        name = _function_name(ref)
        if name:
            scopes.add(name)
    for module_slice in module_slices:
        for op in module_slice.get("public_operations", []):
            name = _function_name(op.get("key", ""))
            if name:
                scopes.add(name)
    return scopes


def build(project: Path, flow: str) -> dict[str, Any]:
    key = _flow_key(flow)
    flow_item = design_stage4.get_flow(project, key)
    if flow_item is None:
        raise ValueError(f"unknown flow: {key}")

    module_slices = [
        slice_builder.build(project, module_ref)
        for module_ref in flow_item.get("module_refs", [])
    ]
    scopes = _participating_scopes(flow_item, module_slices)
    all_contracts = _load_contracts(project)
    contracts = {name: all_contracts[name] for name in sorted(scopes) if name in all_contracts}

    notes_report = gate.coverage(project)
    notes = [
        note for note in notes_report.get("notes", [])
        if note.get("scope") in scopes
    ]

    return {
        "schema_version": "spec_workbench_stage7_1_flow_slice.v1",
        "project_root": project.resolve().name,
        "flow": flow_item,
        "modules": module_slices,
        "participating_scopes": sorted(scopes),
        "contracts": contracts,
        "exception_taxonomy": _load_exceptions(project),
        "notes": notes,
        "review_protocol": {
            "goal": "Reconstruct observable E2E behavior and detect semantic information loss from States 1-2 through the completed specification.",
            "questions": [
                "Can two materially different observable behaviors both satisfy this complete flow slice?",
                "Can a trivial implementation satisfy the accepted obligations of any participating generated callable?",
                "Can every material branch be written as an implementation-independent Given/When/Then scenario without guessing?",
            ],
            "allowed_results": ["PASS", "AMBIGUITY"],
        },
    }
