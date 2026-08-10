from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


@dataclass(frozen=True)
class Section:
    title: str
    level: int
    start_line: int
    end_line: int
    body: str


def sections(path: Path) -> list[Section]:
    lines = path.read_text(encoding="utf-8").splitlines()
    heads: list[tuple[int, int, str]] = []
    for number, line in enumerate(lines, start=1):
        match = HEADING_RE.match(line)
        if match:
            heads.append((number, len(match.group(1)), match.group(2).strip()))
    result: list[Section] = []
    for index, (start, level, title) in enumerate(heads):
        end = len(lines)
        for next_start, next_level, _ in heads[index + 1 :]:
            if next_level <= level:
                end = next_start - 1
                break
        body = "\n".join(lines[start:end]).strip()
        result.append(Section(title, level, start, end, body))
    return result


def child_map(path: Path, parent_title: str) -> dict[str, str]:
    all_sections = sections(path)
    parent = next((item for item in all_sections if item.title == parent_title), None)
    if parent is None:
        return {}
    result: dict[str, str] = {}
    for item in all_sections:
        if item.start_line <= parent.start_line or item.start_line > parent.end_line:
            continue
        if item.level == parent.level + 1:
            result[item.title] = item.body
    return result
