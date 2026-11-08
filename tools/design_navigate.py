#!/usr/bin/env python3
"""Navigation over a snapshot of design texts, for people and for reviewing agents.

Issue #159: a State 2 reviewer explores the earlier layers itself — State 0 by
its structure, not only as one document or by lexical search — and every
passage it reads or quotes is bound to one snapshot.

A **snapshot** is a directory of markdown documents (``docs/`` for the case's
states, ``methodology/`` for the documents of the phase) with ``snapshot.json``
naming each file, its state and its sha256; its id is the sha256 of that
listing. Without ``snapshot.json`` the directory's markdown files are read as
they are and the id is computed the same way.

Commands (every answer is JSON, every read carries the snapshot id):

    toc [DOCUMENT]          documents, sections and nested sections, the
                            text before the first heading (``#preamble``)
    ids [PREFIX]            explicitly written identifiers and the section that
                            defines each: R0-*, decision keys, models, INV-*
    read KEY [--snapshot ID] a section (with its nested sections) or an
                            identifier's section: verbatim text, document,
                            line range, sha256; a key that does not resolve,
                            or a snapshot id that is not this one, is an error
    refs KEY                explicit references: the identifiers the section
                            names (outgoing) and the sections naming what it
                            defines (incoming)
    search TEXT             lexical occurrences — search results, never
                            proven dependencies

A section key is ``<document>#<heading path>``: the slugs of the headings from
the top down, joined by ``/`` (a document's one ``#`` title is ``#title`` and
not part of the paths); a repeated path gets ``~2``, ``~3``. Keys are
unique within a snapshot. An identifier (``R0-07``, ``A12``) is an alias of
the section that defines it; an alias defined twice is ambiguous and names
both keys. Nothing here infers a dependency from shared words: a reference is
an identifier written in the text, and finding none proves nothing.

The module is copied into a reviewer's workspace as ``nav.py`` and run there
read-only; it imports nothing outside the standard library.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SNAPSHOT_FILE = "snapshot.json"
HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
FENCE = re.compile(r"^\s*(```|~~~)")
# identifiers a section defines when its heading or one of its list items starts with them
DEFINED_ID = re.compile(r"\b(R\d+-\d+[A-Za-z]?|A\d+|M\d+|[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d{1,4})\b")
ITEM_START = re.compile(r"^\s{0,3}(?:[-*+]|\d+[.)])\s+\**`?([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d{1,4}[A-Za-z]?)\b")
NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "section"


@dataclass
class Section:
    key: str
    document: str
    title: str
    level: int            # 0 for the preamble
    start: int            # first line, 1-based
    own_end: int          # last line before the next heading of any level
    end: int              # last line before the next heading of the same or a higher level
    defines: set[str] = field(default_factory=set)


@dataclass
class Document:
    name: str
    state: int | None
    text: str
    sha256: str
    lines: list[str] = field(default_factory=list)
    sections: list[Section] = field(default_factory=list)


class NavigationError(Exception):
    pass


def _sections(name: str, text: str) -> list[Section]:
    lines = text.splitlines()
    heads: list[tuple[int, int, str]] = []  # (line, level, title)
    fenced = False
    for number, line in enumerate(lines, 1):
        if FENCE.match(line):
            fenced = not fenced
            continue
        found = None if fenced else HEADING.match(line)
        if found:
            heads.append((number, len(found.group(1)), found.group(2)))
    found: list[Section] = []
    first = heads[0][0] if heads else len(lines) + 1
    if any(line.strip() for line in lines[:first - 1]):
        found.append(Section(f"{name}#preamble", name, "before the first heading", 0, 1, first - 1, first - 1))
    seen: dict[str, int] = {}
    path: list[tuple[int, str]] = []
    # a document's one title heading is not part of the paths below it
    title_line = heads[0][0] if heads and heads[0][1] == 1 and sum(1 for h in heads if h[1] == 1) == 1 else None
    for index, (line, level, title) in enumerate(heads):
        while path and path[-1][0] >= level:
            path.pop()
        if line == title_line:
            key = f"{name}#title"
        else:
            path.append((level, _slug(title)))
            key = f"{name}#" + "/".join(slug for _, slug in path)
        seen[key] = seen.get(key, 0) + 1
        if seen[key] > 1:
            key = f"{key}~{seen[key]}"
        own_end = (heads[index + 1][0] - 1) if index + 1 < len(heads) else len(lines)
        end = next((h[0] - 1 for h in heads[index + 1:] if h[1] <= level), len(lines))
        section = Section(key, name, title, level, line, own_end, end)
        section.defines = _defines(title, lines[line:own_end])
        found.append(section)
    return found


def _defines(title: str, body: list[str]) -> set[str]:
    names = set(DEFINED_ID.findall(title.split("—", 1)[0]))
    named = title.split("—", 1)[1].strip().strip("`") if "—" in title else ""
    if NAME.fullmatch(named) and named[0].isupper():   # "Model M12 — Expense"
        names.add(named)
    names |= {m.group(1) for line in body for m in [ITEM_START.match(line)] if m}
    return names


class Snapshot:
    """The documents of one snapshot, their sections and the identifiers they define."""

    def __init__(self, root: Path):
        self.root = Path(root)
        manifest = self.root / SNAPSHOT_FILE
        if manifest.is_file():
            listing = json.loads(manifest.read_text(encoding="utf-8"))["documents"]
            entries = [(d["name"], d.get("state")) for d in listing]
        else:
            entries = [(p.relative_to(self.root).as_posix(), None) for p in sorted(self.root.rglob("*.md"))]
        self.documents: dict[str, Document] = {}
        for name, state in entries:
            text = (self.root / name).read_text(encoding="utf-8")
            document = Document(name, state, text, _sha(text), text.splitlines())
            document.sections = _sections(name, text)
            self.documents[name] = document
        self.id = _sha(json.dumps(sorted((d.name, d.sha256) for d in self.documents.values())))
        self.sections = {s.key: s for d in self.documents.values() for s in d.sections}
        self.aliases: dict[str, list[str]] = {}
        for section in self.sections.values():
            for name in section.defines:
                self.aliases.setdefault(name, []).append(section.key)

    # ------------------------------------------------------------------ helpers
    def _text(self, section: Section, own: bool = False) -> str:
        lines = self.documents[section.document].lines
        return "\n".join(lines[section.start - 1:(section.own_end if own else section.end)])

    def resolve(self, target: str) -> Section:
        if target in self.sections:
            return self.sections[target]
        keys = self.aliases.get(target)
        if keys and len(keys) == 1:
            return self.sections[keys[0]]
        if keys:
            raise NavigationError(f"{target} is defined by several sections: {', '.join(keys)}; read one by its key")
        close = difflib.get_close_matches(target, list(self.sections) + list(self.aliases), n=5, cutoff=0.6)
        raise NavigationError(f"{target} is no section key or identifier of snapshot {self.id[:12]}"
                              + (f"; close: {', '.join(close)}" if close else ""))

    def _mentions(self, text: str, names: set[str]) -> list[str]:
        return sorted(n for n in names if re.search(rf"(?<![\w-]){re.escape(n)}(?![\w-])", text))

    # ----------------------------------------------------------------- commands
    def toc(self, document: str | None = None) -> dict[str, Any]:
        docs = [self.documents[document]] if document else list(self.documents.values())
        if document and document not in self.documents:
            raise NavigationError(f"{document} is no document of snapshot {self.id[:12]}")
        return {"snapshot": self.id, "documents": [
            {"document": d.name, "state": d.state, "sha256": d.sha256, "lines": len(d.lines),
             "sections": [{"key": s.key, "title": s.title, "level": s.level, "lines": [s.start, s.end],
                           "defines": sorted(s.defines)} for s in d.sections]} for d in docs]}

    def ids(self, prefix: str = "") -> dict[str, Any]:
        return {"snapshot": self.id, "identifiers": {
            name: keys for name, keys in sorted(self.aliases.items()) if name.startswith(prefix)}}

    def read(self, target: str, snapshot: str | None = None) -> dict[str, Any]:
        if snapshot and snapshot not in (self.id, self.id[:len(snapshot)]):
            raise NavigationError(f"snapshot {snapshot} is not this snapshot ({self.id}): the key may name "
                                  "another text; read it again here")
        section = self.resolve(target)
        text = self._text(section)
        nested = [s.key for s in self.sections.values()
                  if s.document == section.document and section.start < s.start <= section.end]
        return {"snapshot": self.id, "key": section.key, "document": section.document,
                "state": self.documents[section.document].state, "title": section.title,
                "lines": [section.start, section.end], "sha256": _sha(text), "defines": sorted(section.defines),
                "nested": nested, "text": text}

    def refs(self, target: str) -> dict[str, Any]:
        section = self.resolve(target)
        text = self._text(section)
        own = section.defines | {d for k, s in self.sections.items()
                                 if s.document == section.document and section.start <= s.start <= section.end
                                 for d in s.defines}
        outgoing = {name: self.aliases[name] for name in self._mentions(text, set(self.aliases) - own)}
        incoming = []
        for other in self.sections.values():
            if other.document == section.document and section.start <= other.start <= section.end:
                continue
            named = self._mentions(self._text(other, own=True), own)
            if named:
                incoming.append({"key": other.key, "document": other.document,
                                 "state": self.documents[other.document].state, "names": named})
        return {"snapshot": self.id, "key": section.key, "defines": sorted(own),
                "outgoing": outgoing, "incoming": incoming,
                "note": "explicit identifiers only; a missing reference does not prove that nothing depends"}

    def search(self, needle: str) -> dict[str, Any]:
        found = []
        lowered = needle.lower()
        for document in self.documents.values():
            for number, line in enumerate(document.lines, 1):
                if lowered in line.lower():
                    owner = max((s for s in document.sections if s.start <= number <= s.own_end),
                                key=lambda s: s.start, default=None)
                    found.append({"document": document.name, "line": number,
                                  "key": owner.key if owner else None, "text": line.strip()[:240]})
        return {"snapshot": self.id, "query": needle, "results": found,
                "note": "lexical search results, not dependencies"}

    def verify_quote(self, target: str, quote: str, snapshot: str | None = None) -> bool:
        """Whether ``quote`` occurs, whitespace aside, in the section ``target`` of this snapshot."""
        try:
            text = self.read(target, snapshot)["text"]
        except NavigationError:
            return False
        return " ".join(quote.split()) in " ".join(text.split())


def write_snapshot(root: Path, documents: list[tuple[str, int | None, str]]) -> str:
    """Write ``documents`` (name, state, text) under ``root`` with their manifest; return the id."""
    listing = []
    for name, state, text in documents:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        listing.append({"name": name, "state": state, "sha256": _sha(text)})
    (root / SNAPSHOT_FILE).write_text(json.dumps({"documents": listing}, ensure_ascii=False, indent=1) + "\n",
                                      encoding="utf-8")
    return Snapshot(root).id


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    sub = parser.add_subparsers(dest="command", required=True)
    toc = sub.add_parser("toc")
    toc.add_argument("document", nargs="?")
    ids = sub.add_parser("ids")
    ids.add_argument("prefix", nargs="?", default="")
    read = sub.add_parser("read")
    read.add_argument("key")
    read.add_argument("--snapshot")
    refs = sub.add_parser("refs")
    refs.add_argument("key")
    search = sub.add_parser("search")
    search.add_argument("text")
    args = parser.parse_args(argv)
    try:
        snapshot = Snapshot(args.root)
        result: dict[str, Any] = {
            "toc": lambda: snapshot.toc(args.document), "ids": lambda: snapshot.ids(args.prefix),
            "read": lambda: snapshot.read(args.key, args.snapshot), "refs": lambda: snapshot.refs(args.key),
            "search": lambda: snapshot.search(args.text)}[args.command]()
    except NavigationError as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
