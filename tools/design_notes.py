#!/usr/bin/env python3
"""Thin CLI facade for the deep Notes Workbench modules."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from notes_workbench import gate, service


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--module")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--slice", action="store_true")
    action.add_argument("--review", action="store_true")
    action.add_argument("--gate", action="store_true")
    action.add_argument("--handoff", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.project.is_dir():
        print(f"design_notes: error: project directory not found: {args.project}", file=sys.stderr)
        return 2
    if (args.slice or args.review) and not args.module:
        print("design_notes: error: --module is required with --slice/--review", file=sys.stderr)
        return 2
    try:
        if args.gate:
            payload = gate.coverage(args.project)
        elif args.handoff:
            payload = gate.handoff(args.project)
        else:
            payload = service.module_slice(args.project, args.module) if args.slice else service.module_review(args.project, args.module)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"design_notes: error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        if args.slice:
            print(f"{payload['module']}: {len(payload['obligations'])} obligations")
        elif args.review:
            summary = payload["summary"]
            print(f"{payload['module']}: {summary['notes']} notes; {summary['review']} review findings; {summary['block']} block findings")
        else:
            summary = payload["summary"]
            ready = payload.get("ready", summary["handoff_ready"])
            print(f"State 7 notes: {summary['notes']} notes; {summary['blocks']} blocks; {summary['reviews']} reviews; handoff_ready={str(ready).lower()}")
    if args.gate:
        return 0 if payload["summary"]["handoff_ready"] else 1
    if args.handoff:
        return 0 if payload["ready"] else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
