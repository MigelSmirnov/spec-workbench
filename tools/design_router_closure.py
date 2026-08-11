#!/usr/bin/env python3
"""Official Router Closure authoring entrypoint.

The low-level router_workbench package can validate its closed DSL in isolation,
but authoring through this CLI is fail-closed until State 6 exact contracts have
a ready handoff. This preserves the normative sequence in AUTHORING_SEQUENCE.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import design_stage6_contracts
from router_workbench import service
from router_workbench.model import RouterClosureError

PREREQUISITE_SCHEMA = "spec_workbench_router_closure_prerequisite.v1"


def _human(action: str, payload: dict[str, object]) -> str:
    if payload.get("schema_version") == PREREQUISITE_SCHEMA:
        return (
            "Router Closure blocked: State 6 exact contracts are not ready.\n"
            "Run: python tools/design_stage6_contracts.py <project> --next --json\n"
        )
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


def _prerequisite(project: Path) -> dict[str, object] | None:
    handoff = design_stage6_contracts.handoff(project)
    if handoff["ready"]:
        return None
    return {
        "schema_version": PREREQUISITE_SCHEMA,
        "project_root": project.resolve().name,
        "blocked": True,
        "requires": "state6_exact_contracts",
        "message": "Router Closure requires a ready State 6 exact-contract handoff.",
        "contract_summary": handoff["summary"],
        "unresolved_functions": handoff["unresolved_functions"],
        "findings": handoff["findings"],
    }


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
        blocked = _prerequisite(args.project)
        payload = blocked or getattr(service, selected if selected != "next" else "next_operation")(args.project)
    except (RouterClosureError, design_stage6_contracts.DesignStage6ContractsError) as exc:
        print(f"design_router_closure: error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) if args.json else _human(selected, payload))
    if blocked is not None:
        return 1
    if selected == "lint":
        return 1 if payload["summary"]["errors"] else 0
    if selected == "coverage":
        return 0 if payload["summary"]["handoff_ready"] else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
