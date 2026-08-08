#!/usr/bin/env python3
"""Deterministic structural index for spec-workbench design-state Markdown.

The indexer intentionally does not infer ownership, semantic similarity, or
responsibility clusters. It records only structure that is explicit in source:
state numbers, decision/open-question headings, child sections, source ranges,
and explicit A*/OQ-* references.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
STATE_RE = re.compile(r"\bState\s+(\d+)\b", re.IGNORECASE)
DECISION_ID_RE = re.compile(r"\b(A\d+)\b")
OPEN_QUESTION_ID_RE = re.compile(r"\b(OQ-\d+)\b", re.IGNORECASE)
EXPLICIT_REF_RE = re.compile(r"\b(?:A\d+|OQ-\d+)\b", re.IGNORECASE)


@dataclass(frozen=True)
class SourceRange:
    path: str
    start_line: int
    end_line: int


@dataclass
class Section:
    title: str
    level: int
    start_line: int
    end_line: int


@dataclass
class DesignItem:
    key: str
    kind: str
    title: str
    state: int | None
    source: SourceRange
    explicit_id: str | None = None
    explicit_refs: list[str] = field(default_factory=list)
    sections: list[Section] = field(default_factory=list)


def _slug(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return value or "item"


def _item_kind(title: str) -> tuple[str, str | None] | None:
    oq = OPEN_QUESTION_ID_RE.search(title)
    if oq:
        return "open_question", oq.group(1).upper()

    decision = DECISION_ID_RE.search(title)
    lowered = title.lower()
    if decision and ("decision" in lowered or "accepted" in lowered):
        return "decision", decision.group(1).upper()

    if "accepted decision" in lowered:
        return "decision", None

    return None


def _state_from_lines(lines: list[str]) -> int | None:
    for line in lines:
        match = STATE_RE.search(line)
        if match:
            return int(match.group(1))
    return None


def parse_markdown(path: Path, root: Path) -> list[DesignItem]:
    lines = path.read_text(encoding="utf-8").splitlines()
    state = _state_from_lines(lines[:40])
    headings: list[tuple[int, int, str]] = []
    for index, line in enumerate(lines, start=1):
        match = HEADING_RE.match(line)
        if match:
            headings.append((index, len(match.group(1)), match.group(2).strip()))

    rel = path.relative_to(root).as_posix()
    items: list[DesignItem] = []

    for h_index, (start, level, title) in enumerate(headings):
        parsed_kind = _item_kind(title)
        if parsed_kind is None:
            continue
        kind, explicit_id = parsed_kind

        end = len(lines)
        for next_start, next_level, _ in headings[h_index + 1 :]:
            if next_level <= level:
                end = next_start - 1
                break

        body = "\n".join(lines[start - 1 : end])
        refs = sorted({ref.upper() for ref in EXPLICIT_REF_RE.findall(body)})
        if explicit_id in refs:
            refs.remove(explicit_id)

        sections: list[Section] = []
        child_headings = [h for h in headings[h_index + 1 :] if start < h[0] <= end and h[1] > level]
        for child_index, (child_start, child_level, child_title) in enumerate(child_headings):
            child_end = end
            for next_child_start, next_child_level, _ in child_headings[child_index + 1 :]:
                if next_child_level <= child_level:
                    child_end = next_child_start - 1
                    break
            sections.append(
                Section(
                    title=child_title,
                    level=child_level,
                    start_line=child_start,
                    end_line=child_end,
                )
            )

        key = explicit_id or f"source:{rel}#{_slug(title)}"
        items.append(
            DesignItem(
                key=key,
                explicit_id=explicit_id,
                kind=kind,
                title=title,
                state=state,
                source=SourceRange(rel, start, end),
                explicit_refs=refs,
                sections=sections,
            )
        )

    return items


def iter_markdown(project: Path) -> Iterable[Path]:
    yield from sorted(path for path in project.rglob("*.md") if path.is_file())


def build_index(project: Path) -> dict[str, object]:
    project = project.resolve()
    items: list[DesignItem] = []
    for path in iter_markdown(project):
        items.extend(parse_markdown(path, project))

    by_key: dict[str, DesignItem] = {}
    duplicates: list[str] = []
    for item in items:
        if item.key in by_key:
            duplicates.append(item.key)
        else:
            by_key[item.key] = item

    return {
        "schema_version": "spec_workbench_design_index.v1",
        "project_root": project.name,
        "items": [asdict(item) for item in items],
        "diagnostics": {"duplicate_keys": sorted(set(duplicates))},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path, help="Directory containing design-state Markdown files")
    parser.add_argument("--output", type=Path, help="Write JSON index to this file instead of stdout")
    args = parser.parse_args()

    index = build_index(args.project)
    payload = json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")

    if index["diagnostics"]["duplicate_keys"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
