#!/usr/bin/env python3
"""Data Closure lint L2–L5 of one case's State 7 notes, as a report.

    python tools/design_notes_lint.py examples/<case> [--json]

Reads every `80_notes*.md` and the in-memory projection of the authored
sources (tools/DATA_CLOSURE_WORKBENCH.md §6, decisions Q1 and Q12). Not a
gate: the exit code is 0 whatever the lint finds; it becomes a gate with the
notes-writing environment.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from notes_authoring.lint import lint_project  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("project", type=Path)
    parser.add_argument("--json", action="store_true", help="the full report")
    args = parser.parse_args(argv)
    report = lint_project(args.project)
    if args.json:
        json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0
    summary = report["summary"]
    print(f"notes lint: {summary['notes']} notes, {summary['modules']} modules, "
          f"{summary['blocks']} blocking, {summary['reports']} reported")
    for rule, count in summary["by_rule"].items():
        print(f"  {rule}: {count}")
    for module, row in report["modules"].items():
        if row["blocks"] or row["reports"]:
            print(f"  {module}: {row['blocks']} blocking, {row['reports']} reported ({row['notes']} notes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
