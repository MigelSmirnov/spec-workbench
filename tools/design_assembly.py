#!/usr/bin/env python3
"""Thin CLI facade for complete post-assembly verification."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from assembly_workbench import inspect_check, verify
from assembly_workbench.model import AssemblyWorkbenchError, CHECK_ORDER

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--check", choices=CHECK_ORDER)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--factory-root", type=Path, help="Factory checkout for canonical validation")
    args = parser.parse_args(argv)
    try:
        report = (inspect_check(args.project, args.check, factory_root=args.factory_root)
                  if args.check else verify(args.project, factory_root=args.factory_root))
    except AssemblyWorkbenchError as error:
        print(f"design_assembly: error: {error}", file=sys.stderr)
        return 2
    if args.json or args.check:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        summary = report["summary"]
        print(
            f"Assembly verification: {summary['ready_checks']}/{summary['checks']} checks ready; "
            f"{summary['errors']} errors; {summary['warnings']} warnings; "
            f"ready={str(report['ready']).lower()}"
        )
        for check in report["checks"]:
            print(
                f"{check['name']}: ready={str(check['ready']).lower()} "
                f"errors={check['errors']} warnings={check['warnings']}"
            )
    if args.check:
        return 0 if report["check"]["ready"] else 1
    return 0 if report["ready"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
