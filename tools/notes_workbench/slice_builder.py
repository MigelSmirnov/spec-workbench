from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import design_stage3
import design_stage4

from notes_workbench.markdown_sections import child_map, sections


def _public_op_details(project: Path, module: str) -> list[dict[str, Any]]:
    path = project / "50_public_apis.md"
    if not path.is_file():
        return []
    prefix = f"`public_op:{module}."
    result: list[dict[str, Any]] = []
    for item in sections(path):
        if item.level != 2 or not item.title.startswith(prefix):
            continue
        result.append({
            "key": item.title.strip("`"),
            "sections": child_map(path, item.title),
            "source": {"path": path.name, "start_line": item.start_line, "end_line": item.end_line},
        })
    return result


def _flow_details(project: Path, module_key: str) -> list[dict[str, Any]]:
    handoff = design_stage4.handoff(project)
    wanted = {flow["key"] for flow in handoff["flows"] if module_key in set(flow["module_refs"])}
    path = project / "40_flows.md"
    if not path.is_file():
        return []
    result: list[dict[str, Any]] = []
    for item in sections(path):
        key = item.title.strip("`")
        if item.level == 2 and key in wanted:
            result.append({
                "key": key,
                "sections": child_map(path, item.title),
                "source": {"path": path.name, "start_line": item.start_line, "end_line": item.end_line},
            })
    return result


def _structured_refs(project: Path, module: str) -> list[dict[str, Any]]:
    path = project / "60_data_closure.json"
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    refs: list[dict[str, Any]] = []
    for placement in payload.get("placements", []):
        address = placement.get("address", "")
        parts = address.split(".")
        if len(parts) >= 2 and parts[1] == module:
            refs.append(placement)
    return refs


def build(project: Path, module: str) -> dict[str, Any]:
    module_key = module if module.startswith("module:") else f"module:{module}"
    module_name = module_key.removeprefix("module:")
    stage3 = design_stage3.handoff(project)
    module_entry = next((item for item in stage3["modules"] if item["key"] == module_key), None)
    if module_entry is None:
        raise ValueError(f"unknown module: {module_key}")
    capabilities = [item for item in stage3["capabilities"] if item["module"] == module_key]
    return {
        "schema_version": "spec_workbench_notes_slice.v1",
        "project_root": project.resolve().name,
        "module": module_key,
        "responsibility": module_entry,
        "capabilities": capabilities,
        "flows": _flow_details(project, module_key),
        "public_operations": _public_op_details(project, module_name),
        "structured_refs": _structured_refs(project, module_name),
    }
