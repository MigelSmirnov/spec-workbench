#!/usr/bin/env python3
"""Model surface closure: State 1 fields versus the model closure, and note
attribute references versus the declared surfaces.

    python tools/design_field_closure.py examples/<case> --json

Exit 1 when either lens reports a finding. The assembly ``fields`` check and
the State 7 notes gate run the same lenses; this CLI is the human entry point.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from model_surface_workbench import attributes, fields
from model_surface_workbench.index import ModelIndex
from notes_workbench.gate import NOTE_RE


def note_findings(project: Path) -> list[dict]:
    path = project / "80_notes.md"
    if not path.is_file():
        return []
    notes = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        match = NOTE_RE.fullmatch(raw.strip())
        if match:
            notes.append({"line": number, "scope": match.group("scope"), "text": match.group("text")})
    return attributes.findings(notes, ModelIndex.load(project))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    field_report = fields.lint(args.project)
    note_items = note_findings(args.project)
    report = {
        "schema_version": "spec_workbench_model_surface_closure.v1",
        "project_root": args.project.resolve().name,
        "fields": field_report,
        "notes": {"findings": note_items, "blocks": len(note_items)},
        "ready": field_report["summary"]["errors"] == 0 and not note_items,
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for item in field_report["findings"]:
            print(f"{item['file']}:{item['line']}: {item['code']}: {item['message']}")
        for item in note_items:
            print(f"80_notes.md:{item['line']}: {item['code']}: {item['message']}")
        summary = field_report["summary"]
        print(f"fields: compared={summary['models_compared']} unparsed={summary['models_unparsed']} errors={summary['errors']}; note attribute blocks={len(note_items)}")
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
