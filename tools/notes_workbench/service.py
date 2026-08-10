from __future__ import annotations

from pathlib import Path
from typing import Any

from notes_workbench import note_parser, obligations, review, slice_builder


def module_slice(project: Path, module: str) -> dict[str, Any]:
    payload = slice_builder.build(project, module)
    payload["obligations"] = obligations.build(payload)
    return payload


def module_review(project: Path, module: str) -> dict[str, Any]:
    payload = module_slice(project, module)
    module_name = payload["module"].removeprefix("module:")
    symbols = {cap["name"] for cap in payload.get("capabilities", [])}
    notes = note_parser.parse(project, symbols, module_name)
    result = review.review(notes, payload["obligations"])
    result["module"] = payload["module"]
    result["notes"] = notes
    return result
