#!/usr/bin/env python3
"""Thin CLI facade for the deep Notes Workbench modules."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from notes_workbench import gate, language, propagation, service


def _propagation_human(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    lines = [
        "Notes propagation: "
        f"{summary['changes']} changes; "
        f"Factory blockers {summary['factory_coverage_blocks_before']}"
        f"->{summary['factory_coverage_blocks_after']}; "
        f"dependency blockers {summary['dependency_binding_blocks_before']}"
        f"->{summary['dependency_binding_blocks_after']}; "
        f"status={payload['status']}"
    ]
    for finding in payload.get("findings", []):
        lines.append(
            f"{finding['severity'].upper()} {finding['code']} - {finding['message']}"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--module")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--slice", action="store_true")
    action.add_argument("--review", action="store_true")
    action.add_argument("--gate", action="store_true")
    action.add_argument("--handoff", action="store_true")
    action.add_argument("--language", action="store_true")
    action.add_argument("--propagate", action="store_true")
    parser.add_argument(
        "--base-ref",
        default="HEAD",
        help=(
            "Git revision containing the pre-edit 80_notes.md used by "
            "--propagate (default: HEAD)"
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="With --propagate, report drift without writing global_spec.json.",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.project.is_dir():
        print(f"design_notes: error: project directory not found: {args.project}", file=sys.stderr)
        return 2
    if (args.slice or args.review) and not args.module:
        print("design_notes: error: --module is required with --slice/--review", file=sys.stderr)
        return 2
    if args.check and not args.propagate:
        print("design_notes: error: --check is valid only with --propagate", file=sys.stderr)
        return 2
    if args.base_ref != "HEAD" and not args.propagate:
        print("design_notes: error: --base-ref is valid only with --propagate", file=sys.stderr)
        return 2
    try:
        if args.gate:
            payload = gate.coverage(args.project)
        elif args.language:
            payload = language.report(args.project)
        elif args.handoff:
            payload = gate.handoff(args.project)
        elif args.propagate:
            payload = propagation.propagate(
                args.project,
                base_ref=args.base_ref,
                write=not args.check,
            )
        else:
            payload = service.module_slice(args.project, args.module) if args.slice else service.module_review(args.project, args.module)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"design_notes: error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        if args.language:
            summary = payload["summary"]
            print(f"Notes language: {summary['findings']} findings; {summary['blocking']} blocking")
            for code, count in sorted(summary["by_code"].items()):
                print(f"  {code}: {count}")
        elif args.propagate:
            print(_propagation_human(payload))
        elif args.slice:
            print(f"{payload['module']}: {len(payload['obligations'])} obligations")
        elif args.review:
            summary = payload["summary"]
            print(f"{payload['module']}: {summary['notes']} notes; {summary['review']} review findings; {summary['block']} block findings")
        else:
            summary = payload["summary"]
            ready = payload.get("ready", summary["handoff_ready"])
            print(f"State 7 notes: {summary['notes']} notes; {summary['blocks']} blocks; {summary['reviews']} reviews; handoff_ready={str(ready).lower()}")
    if args.propagate:
        if not payload["ready"]:
            return 2
        if args.check:
            return 1 if payload["changed"] else 0
        return 0
    if args.language:
        return 0 if payload["status"] == "pass" else 1
    if args.gate:
        return 0 if payload["summary"]["handoff_ready"] else 1
    if args.handoff:
        return 0 if payload["ready"] else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
