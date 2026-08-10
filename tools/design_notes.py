#!/usr/bin/env python3
"""Thin CLI facade for the deep Notes Workbench modules."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from notes_workbench import service


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--module", required=True)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--slice", action="store_true")
    action.add_argument("--review", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.project.is_dir():
        print(f"design_notes: error: project directory not found: {args.project}", file=sys.stderr)
        return 2
    try:
        payload = service.module_slice(args.project, args.module) if args.slice else service.module_review(args.project, args.module)
    except ValueError as exc:
        print(f"design_notes: error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        if args.slice:
            print(f"{payload['module']}: {len(payload['obligations'])} obligations")
        else:
            summary = payload["summary"]
            print(f"{payload['module']}: {summary['notes']} notes; {summary['review']} review findings; {summary['block']} block findings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
