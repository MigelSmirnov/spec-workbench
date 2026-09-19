#!/usr/bin/env python3
"""Run deterministic project-local gates declared through workbench_extensions.json."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import project_gates


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    report = project_gates.coverage(args.project)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        summary = report["summary"]
        print(
            f"Project gates: {summary['ready_gates']}/{summary['gates']} ready; "
            f"{summary['errors']} errors; {summary['warnings']} warnings"
        )
        for finding in report["findings"]:
            print(
                f"{finding.get('severity', 'error')}: "
                f"{finding.get('gate', 'unknown')}: "
                f"{finding.get('code', 'project_gate')}: "
                f"{finding.get('message', '')}"
            )
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
