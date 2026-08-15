#!/usr/bin/env python3
"""Stage 9 read-only Factory admission gate for an assembled Workbench case."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from factory_admission_workbench import check


PROJECT_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def main(argv: list[str] | None = None) -> int:
    workbench_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", type=Path)
    parser.add_argument("--project", required=True)
    parser.add_argument(
        "--factory-root", type=Path, default=workbench_root.parent / "code_factory"
    )
    parser.add_argument("--update-existing", action="store_true")
    parser.add_argument("--allow-dirty-source", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not PROJECT_RE.fullmatch(args.project):
        parser.error("--project must contain only letters, numbers, underscores, or hyphens")
    case_root = args.case.resolve()
    source = case_root / "global_spec.json"
    if not source.is_file():
        print(f"design_factory_admission: error: source specification not found: {source}", file=sys.stderr)
        return 2
    report = check(
        workbench_root=workbench_root,
        source=source,
        project=args.project,
        factory_root=args.factory_root,
        case_root=case_root,
        update_existing=args.update_existing,
        allow_dirty_source=args.allow_dirty_source,
    )
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        summary = report["summary"]
        print(
            f"Factory admission: status={report['status']} "
            f"passes={summary['passes']} blocks={summary['blocks']} warnings={summary['warnings']}"
        )
        for item in report["checks"]:
            print(f"{item['id']}: {item['status']} — {item['summary']}")
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
