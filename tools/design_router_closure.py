#!/usr/bin/env python3
"""Thin CLI facade for Router Closure design/evidence state.

The low-level Router workbench remains independently testable, but the official
`--next` authoring path is contract-aware and refuses pre-contract routing.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from router_workbench import service
from router_workbench.model import RouterClosureError
from router_workbench.slice import contract_aware_operation_slice


def _human(action: str, payload: dict[str, object]) -> str:
    summary = payload["summary"]
    if action == "next":
        operation = payload["next"]["operation"] if payload["next"] else "complete"
        return f"Router Closure next: {operation}\n"
    lines = [
        f"Router Closure: {summary['resolved']}/{summary['external_operations']} resolved; "
        f"{summary['unresolved']} unresolved; {summary['errors']} errors; "
        f"handoff_ready={str(summary['handoff_ready']).lower()}"
    ]
    for finding in payload.get("findings", []):
        operation = f" {finding['operation']}" if finding.get("operation") else ""
        lines.append(f"{finding['severity'].upper()} {finding['code']}{operation} - {finding['message']}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--coverage", action="store_true")
    action.add_argument("--next", action="store_true")
    action.add_argument("--lint", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.project.is_dir():
        print(f"design_router_closure: error: project directory not found: {args.project}", file=sys.stderr)
        return 2
    selected = "coverage" if args.coverage else "next" if args.next else "lint"
    try:
        payload = getattr(service, selected if selected != "next" else "next_operation")(args.project)
        if selected == "next" and payload["next"] is not None:
            operation = payload["next"]["operation"]
            payload["next"]["semantic_slice"] = contract_aware_operation_slice(args.project, operation)
    except RouterClosureError as exc:
        print(f"design_router_closure: error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) if args.json else _human(selected, payload))
    if selected == "lint":
        return 1 if payload["summary"]["errors"] else 0
    if selected == "coverage":
        return 0 if payload["summary"]["handoff_ready"] else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
