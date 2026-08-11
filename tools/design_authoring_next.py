#!/usr/bin/env python3
"""Deterministic post-State-5 authoring sequencer.

This is the workflow gate for the current authoring standard. Low-level
workbenches remain independently testable, but this sequencer never routes an
author into Router Closure before the canonical State 6 contract handoff is
ready and never treats Router Closure as ready unless its rows validate against
those canonical contracts.
"""
from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Any

import design_stage6_contracts
import design_stage6_data
from router_workbench import authoring as router_authoring

SCHEMA = "spec_workbench_authoring_next.v1"


def _command(*parts: str) -> str:
    return shlex.join(parts)


def next_step(project: Path) -> dict[str, Any]:
    project_text = project.as_posix()
    data = design_stage6_data.lint(project)
    if data["summary"]["errors"]:
        return {
            "schema_version": SCHEMA,
            "project_root": project.resolve().name,
            "phase": "pre_contract_structured_data_closure",
            "blocked": True,
            "reason": "Structured data closure has deterministic errors that must be repaired before State 6 contracts.",
            "next_command": _command("python", "tools/design_stage6_data.py", project_text, "--lint", "--json"),
            "summary": data["summary"],
        }

    contracts = design_stage6_contracts.handoff(project)
    if not contracts["ready"]:
        return {
            "schema_version": SCHEMA,
            "project_root": project.resolve().name,
            "phase": "state6_exact_contracts",
            "blocked": False,
            "reason": "State 6 owns canonical Python signatures and must close before Router Closure.",
            "next_command": _command("python", "tools/design_stage6_contracts.py", project_text, "--next", "--json"),
            "summary": contracts["summary"],
            "unresolved_functions": contracts["unresolved_functions"],
            "router_allowed": False,
        }

    router = router_authoring.coverage(project)
    if not router["summary"]["handoff_ready"]:
        return {
            "schema_version": SCHEMA,
            "project_root": project.resolve().name,
            "phase": "deterministic_http_router_closure",
            "blocked": bool(router["summary"]["errors"]),
            "reason": "Canonical contracts are ready; Router Closure may now bind transport semantics and must validate them against State 6.",
            "next_command": _command("python", "tools/design_router_closure.py", project_text, "--next", "--json"),
            "summary": router["summary"],
            "unresolved_operations": router["unresolved_operations"],
            "router_allowed": True,
        }

    return {
        "schema_version": SCHEMA,
        "project_root": project.resolve().name,
        "phase": "state7_notes",
        "blocked": False,
        "reason": "State 6 contracts and contract-validated deterministic Router Closure are ready; continue to State 7 notes.",
        "next_command": None,
        "summary": router["summary"],
        "router_allowed": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.project.is_dir():
        print(f"design_authoring_next: error: project directory not found: {args.project}", file=sys.stderr)
        return 2
    try:
        payload = next_step(args.project)
    except (ValueError, design_stage6_contracts.DesignStage6ContractsError) as exc:
        print(f"design_authoring_next: error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"Authoring next: {payload['phase']}")
        print(payload["reason"])
        if payload["next_command"]:
            print(payload["next_command"])
    return 1 if payload["blocked"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
