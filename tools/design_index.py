#!/usr/bin/env python3
"""Deterministic structural index for spec-workbench design-state Markdown.

The indexer intentionally does not infer ownership, semantic similarity, or
responsibility clusters. It records only structure that is explicit in source:
state numbers, decision/open-question headings, child sections, source ranges,
and explicit A*/OQ-* references.

Lexical navigation is deliberately two-phase:
- broad mentions discover all textual occurrences with structural context;
- focused mentions narrow those occurrences to indexed design items.
Neither mode creates architectural relations.
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
MODEL_ID_RE = re.compile(r"\b(M\d+)\b")
OPEN_QUESTION_ID_RE = re.compile(r"\b(OQ-\d+)\b", re.IGNORECASE)
EXPLICIT_REF_RE = re.compile(r"\b(?:A\d+|OQ-\d+)\b", re.IGNORECASE)
LOCATION_RE = re.compile(r"^(?P<path>.+):(?P<line>\d+)$")


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


@dataclass(frozen=True)
class Context:
    path: str
    line: int
    item_key: str | None
    item_title: str | None
    heading_path: tuple[str, ...]
    start_line: int
    end_line: int
    lines: tuple[str, ...]


def _slug(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return value or "item"


def _item_kind(title: str) -> tuple[str, str | None] | None:
    model = MODEL_ID_RE.search(title)
    if model and title.casefold().startswith("model "):
        return "model", model.group(1).upper()

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
            sections.append(Section(child_title, child_level, child_start, child_end))

        key = explicit_id or f"source:{rel}#{_slug(title)}"
        items.append(DesignItem(key, kind, title, state, SourceRange(rel, start, end), explicit_id, refs, sections))

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
    candidates = [item for item in items if item.source.path == rel and item.source.start_line <= line <= item.source.end_line]
    return max(candidates, key=lambda item: item.source.start_line) if candidates else None


def find_mentions(project: Path, term: str, *, case_sensitive: bool = False) -> list[Mention]:
    """Return all lexical occurrences with structural context."""
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
                result.append(Mention(term, rel, line_number, column + 1, text.strip(), item.key if item else None, item.title if item else None, _heading_path_at(headings, line_number)))
                start = column + max(1, len(needle))
    return result


def find_mentions_in_items(project: Path, term: str, *, state: int | None = None, kind: str | None = None, case_sensitive: bool = False) -> list[Mention]:
    """Narrow broad mention results to occurrences enclosed by matching indexed items."""
    allowed = {
        item["key"]
        for item in list_items(project, state=state, kind=kind)
    }
    return [mention for mention in find_mentions(project, term, case_sensitive=case_sensitive) if mention.item_key in allowed]


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
    return {"schema_version": "spec_workbench_design_index.v1", "project_root": project.name, "items": [asdict(item) for item in items], "diagnostics": {"duplicate_keys": sorted(set(duplicates))}}


def list_items(project: Path, *, state: int | None = None, kind: str | None = None) -> list[dict[str, object]]:
    result = []
    for item in build_index(project)["items"]:
        if state is not None and item["state"] != state:
            continue
        if kind is not None and item["kind"] != kind:
            continue
        result.append(item)
    return result


def get_item(project: Path, key: str) -> dict[str, object] | None:
    normalized = key.upper() if re.fullmatch(r"(?:A\d+|M\d+|OQ-\d+)", key, re.IGNORECASE) else key
    for item in build_index(project)["items"]:
        if item["key"] == normalized:
            return item
    return None


def get_references(project: Path, key: str) -> dict[str, object] | None:
    item = get_item(project, key)
    if item is None:
        return None
    all_items = {entry["key"]: entry for entry in build_index(project)["items"]}
    outgoing = item["explicit_refs"]
    incoming = sorted(entry["key"] for entry in all_items.values() if item["key"] in entry["explicit_refs"])
    return {"key": item["key"], "outgoing": outgoing, "incoming": incoming, "resolved_outgoing": [all_items[ref] for ref in outgoing if ref in all_items], "unresolved_outgoing": [ref for ref in outgoing if ref not in all_items]}


def context_at(project: Path, location: str, *, radius: int = 3) -> Context:
    match = LOCATION_RE.fullmatch(location)
    if not match:
        raise ValueError("location must be PATH:LINE")
    if radius < 0:
        raise ValueError("radius must be >= 0")
    project = project.resolve()
    rel = match.group("path")
    line = int(match.group("line"))
    path = (project / rel).resolve()
    if not path.is_relative_to(project) or not path.is_file():
        raise ValueError(f"path is not a Markdown file inside project: {rel}")
    lines = path.read_text(encoding="utf-8").splitlines()
    if line < 1 or line > len(lines):
        raise ValueError(f"line is outside file: {line}")
    headings = _headings(lines)
    items = parse_markdown(path, project)
    item = _item_at(items, rel, line)
    start = max(1, line - radius)
    end = min(len(lines), line + radius)
    rendered = tuple(f"{number}: {lines[number - 1]}" for number in range(start, end + 1))
    return Context(rel, line, item.key if item else None, item.title if item else None, _heading_path_at(headings, line), start, end, rendered)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path, help="Directory containing design-state Markdown files")
    parser.add_argument("--output", type=Path, help="Write JSON to this file instead of stdout")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--list", action="store_true", help="List indexed design items")
    action.add_argument("--get", metavar="KEY", help="Get one design item by stable key")
    action.add_argument("--references", metavar="KEY", help="Show explicit incoming/outgoing references")
    action.add_argument("--mentions", metavar="TERM", help="Broad lexical discovery across all Markdown")
    action.add_argument("--mentions-in-items", metavar="TERM", help="Narrow lexical occurrences to indexed items")
    action.add_argument("--context", metavar="PATH:LINE", help="Show structural context around a source line")
    parser.add_argument("--state", type=int, help="Filter --list or --mentions-in-items by design state")
    parser.add_argument("--kind", choices=("decision", "model", "open_question"), help="Filter --list or --mentions-in-items by item kind")
    parser.add_argument("--case-sensitive", action="store_true", help="Use case-sensitive mention lookup")
    parser.add_argument("--radius", type=int, default=3, help="Context lines before/after --context (default: 3)")
    args = parser.parse_args()

    exit_code = 0
    if args.mentions is not None:
        payload_data: object = [asdict(m) for m in find_mentions(args.project, args.mentions, case_sensitive=args.case_sensitive)]
    elif args.mentions_in_items is not None:
        payload_data = [asdict(m) for m in find_mentions_in_items(args.project, args.mentions_in_items, state=args.state, kind=args.kind, case_sensitive=args.case_sensitive)]
    elif args.list:
        payload_data = list_items(args.project, state=args.state, kind=args.kind)
    elif args.get is not None:
        payload_data = get_item(args.project, args.get)
        if payload_data is None:
            exit_code = 1
    elif args.references is not None:
        payload_data = get_references(args.project, args.references)
        if payload_data is None:
            exit_code = 1
    elif args.context is not None:
        payload_data = asdict(context_at(args.project, args.context, radius=args.radius))
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
