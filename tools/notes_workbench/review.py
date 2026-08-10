from __future__ import annotations

import re
from typing import Any

STUB_PATTERNS = (
    r"^handle\s+(errors?|exceptions?)\.?$",
    r"^validate\s+(input|data)\.?$",
    r"^process\s+(result|response|data)\.?$",
    r"^call\s+.+\s+appropriately\.?$",
    r"^implement\s+.+$",
    r"^todo\b",
    r"^tbd\b",
)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9_=.:]+", " ", text.casefold())).strip()


def review(notes: list[dict[str, Any]], obligations: list[dict[str, Any]]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    seen: dict[str, str] = {}
    for note in notes:
        norm = _norm(note["text"])
        if norm in seen:
            findings.append({"severity":"review","code":"suspected_duplicate","note_id":note["id"],"message":f"Text duplicates {seen[norm]}."})
        else:
            seen[norm] = note["id"]
        if any(re.search(pattern, note["text"], re.IGNORECASE) for pattern in STUB_PATTERNS):
            findings.append({"severity":"review","code":"suspected_stub","note_id":note["id"],"message":"Note looks like an implementation placeholder rather than an observable requirement."})
    return {
        "schema_version": "spec_workbench_notes_review.v1",
        "summary": {
            "notes": len(notes),
            "obligations": len(obligations),
            "block": sum(item["severity"] == "block" for item in findings),
            "review": sum(item["severity"] == "review" for item in findings),
        },
        "findings": findings,
    }
