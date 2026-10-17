"""SPEC_STANDARD as the writing agent reads it: an index and one section at a
time (tools/DATA_CLOSURE_WORKBENCH.md §3).

The rules of writing are the standard's own text. The agent's task names
where to start; the agent asks for the sections it needs instead of getting a
copy of them, so there is no second text of the rules that could drift from
the first.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

SKILL = Path("skills") / "spec-authoring"
STANDARD = "SPEC_STANDARD.md"
INDEX = "SPEC_STANDARD_INDEX.md"
REPO = Path(__file__).resolve().parents[2]

_HEADING_RE = re.compile(r"^(?P<level>#{1,6})\s+(?P<title>.+?)\s*$")
_NUMBER_RE = re.compile(r"^(?P<number>\d+(?:\.\d+)*)\.?(?:\s|$)")
# `§15.2`, `15.2.`, or a number with its title: `§15.3.1 Как значение доходит до кода`
_REF_RE = re.compile(r"^§?\s*(?P<number>\d+(?:\.\d+)*)\.?(?:\s+(?P<title>\S.*))?$")
_FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")


def _skill(repo: Path | None) -> Path:
    root = repo if repo is not None and (repo / SKILL / STANDARD).is_file() else REPO
    return root / SKILL


def _headings(lines: list[str]) -> list[dict[str, Any]]:
    out, fence = [], None
    for number, line in enumerate(lines):
        # a fenced block (``` or ~~~, indented up to three spaces) closes on its own marker
        marker = _FENCE_RE.match(line)
        if marker and (fence is None or marker.group(1)[0] == fence[0] and len(marker.group(1)) >= len(fence)):
            fence = marker.group(1) if fence is None else None
            continue
        match = None if fence else _HEADING_RE.match(line)
        if match:
            numbered = _NUMBER_RE.match(match.group("title"))
            out.append({"line": number, "level": len(match.group("level")), "title": match.group("title"),
                        "number": numbered.group("number") if numbered else None})
    return out


def _end(headings: list[dict[str, Any]], at: int, total: int) -> int:
    level = headings[at]["level"]
    return next((h["line"] for h in headings[at + 1:] if h["level"] <= level), total)


def contents(repo: Path | None = None) -> dict[str, Any]:
    """The quick index (where to start for a task) and the table of contents."""
    skill = _skill(repo)
    lines = (skill / STANDARD).read_text(encoding="utf-8").splitlines()
    headings = _headings(lines)
    return {
        "index": (skill / INDEX).read_text(encoding="utf-8"),
        "sections": [
            {"section": h["number"], "title": h["title"], "level": h["level"],
             "lines": _end(headings, i, len(lines)) - h["line"]}
            for i, h in enumerate(headings) if h["level"] > 1
        ],
    }


def section(ref: str, repo: Path | None = None) -> dict[str, Any]:
    """One section with its subsections: by number (`§15.2`, `15.3.1`, `2`)
    or, for an unnumbered heading, by a part of its title unique in the standard."""
    lines = (_skill(repo) / STANDARD).read_text(encoding="utf-8").splitlines()
    headings = _headings(lines)
    ref = ref.strip()
    number = _REF_RE.match(ref)
    if number:
        found = [i for i, h in enumerate(headings) if h["number"] == number.group("number")
                 # a title given with the number must be that section's
                 and (not number.group("title") or number.group("title").casefold() in h["title"].casefold())]
    else:
        exact = [i for i, h in enumerate(headings) if h["title"].casefold() == ref.casefold()]
        found = exact or [i for i, h in enumerate(headings) if ref.casefold() in h["title"].casefold()]
    if len(found) != 1:
        candidates = [h["title"] for h in (headings[i] for i in found)]
        raise ValueError(f"{ref!r} names {'no' if not found else len(found)} sections of SPEC_STANDARD"
                         + (f": {candidates}" if candidates else "; ask without a section for the contents"))
    at = found[0]
    start, end = headings[at]["line"], _end(headings, at, len(lines))
    return {"section": headings[at]["number"], "title": headings[at]["title"],
            "text": "\n".join(lines[start:end]).rstrip()}
