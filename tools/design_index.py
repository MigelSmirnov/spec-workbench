#!/usr/bin/env python3
"""Deterministic structural index for spec-workbench design-state Markdown.

The indexer intentionally does not infer ownership, semantic similarity, or
responsibility clusters. It records only structure that is explicit in source:
state numbers, decision/open-question headings, child sections, source ranges,
and explicit A*/OQ-* references.

A separate lexical mention lookup provides grep-like visibility with structural
context. A mention is navigation evidence only; it never creates a design
relation.
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


@dataclass(frozen=True)
class Mention:
    term: str
    path: str
    line: int
    column: int
    text: str
    item_key: str | None
    item_title: str | None
    heading_path: tuple[str, ...]


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


def _headings(lines: list[str]) -> list[tuple[int, int, str]]:
    result: list[tuple[int, int, str]] = []
    for index, line in enumerate(lines, start=1):
        match = HEADING_RE.match(line)
        if match:
            result.append((index, len(match.group(1)), match.group(2).strip()))
    return result


def parse_markdown(path: Path, root: Path) -> list[DesignItem]:
    lines = path.read_text(encoding="utf-8").splitlines()
    state = _state_from_lines(lines[:40])
    headings = _headings(lines)

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


def _heading_path_at(headings: list[tuple[int, int, str]], line: int) -> tuple[str, ...]:
    stack: list[tuple[int, str]] = []
    for heading_line, level, title in headings:
        if heading_line > line:
            break
        while stack and stack[-1][0] >= level:
            stack.pop()
        stack.append((level, title))
    return tuple(title for _, title in stack)


def _item_at(items: list[DesignItem], rel: str, line: int) -> DesignItem | None:
    candidates = [
        item
        for item in items
        if item.source.path == rel and item.source.start_line <= line <= item.source.end_line
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda item: item.source.start_line)


def find_mentions(project: Path, term: str, *, case_sensitive: bool = False) -> list[Mention]:
    """Return lexical occurrences with structural context, without inferring relations."""
    if not term:
        raise ValueError("term must not be empty")

    project = project.resolve()
    result: list[Mention] = []
    needle = term if case_sensitive else term.casefold()

    for path in iter_markdown(project):
        lines = path.read_text(encoding="utf-8").splitlines()
        headings = _headings(lines)
        items = parse_markdown(path, project)
        rel = path.relative_to(project).as_posix()

        for line_number, text in enumerate(lines, start=1):
            haystack = text if case_sensitive else text.casefold()
            start = 0
            while True:
                column = haystack.find(needle, start)
                if column < 0:
                    break
                item = _item_at(items, rel, line_number)
                result.append(
                    Mention(
                        term=term,
                        path=rel,
                        line=line_number,
                        column=column + 1,
                        text=text.strip(),
                        item_key=item.key if item else None,
                        item_title=item.title if item else None,
                        heading_path=_heading_path_at(headings, line_number),
                    )
                )
                start = column + max(1, len(needle))

    return result


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
    parser.add_argument("--output", type=Path, help="Write JSON to this file instead of stdout")
    parser.add_argument("--mentions", metavar="TERM", help="Find lexical mentions with structural context")
    parser.add_argument("--case-sensitive", action="store_true", help="Use case-sensitive mention lookup")
    args = parser.parse_args()

    if args.mentions is not None:
        payload_data: object = [
            asdict(mention)
            for mention in find_mentions(
                args.project,
                args.mentions,
                case_sensitive=args.case_sensitive,
            )
        ]
        exit_code = 0
    else:
        index = build_index(args.project)
        payload_data = index
        exit_code = 2 if index["diagnostics"]["duplicate_keys"] else 0

    payload = json.dumps(payload_data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
