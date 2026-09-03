#!/usr/bin/env python3
"""Deterministically project closed authoring handoffs into global_spec.json."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from spec_projection_workbench import apply, build_plan, render_diff, verify
from spec_projection_workbench.model import SpecProjectionError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--plan", action="store_true")
    action.add_argument("--diff", action="store_true")
    action.add_argument("--apply", action="store_true")
    action.add_argument("--verify", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.plan:
            payload = build_plan(args.project)
        elif args.diff:
            text = render_diff(args.project)
            print(text, end="")
            plan = build_plan(args.project)
            return 0 if plan["ready_to_apply"] else 1
        elif args.apply:
            payload = apply(args.project)
        else:
            payload = verify(args.project)
    except (SpecProjectionError, ValueError, OSError) as exc:
        print(f"design_spec_projection: error: {exc}", file=sys.stderr)
        return 2

    if args.json or args.plan or args.verify:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        if args.apply:
            print(
                f"Spec projection: applied_changes={payload['applied_changes']}; "
                f"in_sync={str(payload['in_sync']).lower()}"
            )
        else:
            summary = payload["summary"]
            print(
                f"Spec projection: changes={summary['changes']}; "
                f"blocks={summary['blocks']}; "
                f"in_sync={str(payload['in_sync']).lower()}"
            )

    if args.plan:
        return 0 if payload["ready_to_apply"] else 1
    if args.verify:
        return 0 if payload["ready"] and payload["in_sync"] else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
