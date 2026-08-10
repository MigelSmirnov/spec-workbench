from __future__ import annotations

import hashlib
from typing import Any

OBLIGATION_SECTIONS = (
    "Enforces",
    "Errors",
    "Observable effect",
    "State impact",
    "Boundary",
    "Outcomes",
)


def _id(module: str, source: str, section: str, text: str) -> str:
    digest = hashlib.sha1(f"{module}|{source}|{section}|{text}".encode("utf-8")).hexdigest()[:12]
    return f"obligation:{module.removeprefix('module:')}:{digest}"


def build(slice_payload: dict[str, Any]) -> list[dict[str, Any]]:
    module = slice_payload["module"]
    result: list[dict[str, Any]] = []
    for group_name in ("public_operations", "flows"):
        for item in slice_payload.get(group_name, []):
            for section, text in item.get("sections", {}).items():
                if section not in OBLIGATION_SECTIONS or not text.strip():
                    continue
                result.append({
                    "key": _id(module, item["key"], section, text),
                    "module": module,
                    "source": item["key"],
                    "section": section,
                    "text": text.strip(),
                    "kind": "semantic",
                })
    for placement in slice_payload.get("structured_refs", []):
        address = placement["address"]
        text = f"Use structured value by address = {address}; do not duplicate its literal value in prose."
        result.append({
            "key": _id(module, address, "structured_reference", text),
            "module": module,
            "source": address,
            "section": "Structured reference",
            "text": text,
            "kind": "structured_reference",
        })
    return result
