from __future__ import annotations

import re
from pathlib import Path
from typing import Any

NOTE_RE = re.compile(r"^(?P<scope>[A-Za-z_][A-Za-z0-9_.]*):\s*\[(?P<class>[A-Z_]+)\]\s*(?P<text>.+?)\s*$")


def parse(project: Path, module_symbols: set[str], module_name: str) -> list[dict[str, Any]]:
    path = project / "80_notes.md"
    if not path.is_file():
        return []
    result: list[dict[str, Any]] = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        match = NOTE_RE.match(line)
        if not match:
            continue
        scope = match.group("scope")
        if scope != module_name and scope not in module_symbols:
            continue
        result.append({
            "id": f"note:{scope}:{number}",
            "scope": scope,
            "class": match.group("class"),
            "text": match.group("text").strip(),
            "source": {"path": path.name, "line": number},
        })
    return result
