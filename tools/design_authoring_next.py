#!/usr/bin/env python3
"""Deterministic post-State-5 authoring sequencer.

This is the workflow gate for the current authoring standard. Low-level
workbenches remain independently testable, but this sequencer never routes an
author into Router Closure before the canonical State 6 contract handoff is
ready, never treats deterministic HTTP IR as ready until route/context closure
is complete, and never hands off State 7 notes while structural, consistency,
or semantic-stub findings remain unresolved.
"""
from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Any

import design_router_context
import design_stage6_contracts
import design_stage6_data
from notes_workbench import gate as notes_gate
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
            "reason": "Canonical contracts are ready; per-route Router Closure may now bind transport semantics and must validate them against State 6.",
            "next_command": _command("python", "tools/design_router_authoring.py", project_text, "--next", "--json"),
            "summary": router["summary"],
            "unresolved_operations": router["unresolved_operations"],
            "router_allowed": True,
        }

    context = design_router_context.coverage(project)
    if not context["summary"]["handoff_ready"]:
        return {
            "schema_version": SCHEMA,
            "project_root": project.resolve().name,
            "phase": "deterministic_http_router_context_closure",
            "blocked": bool(context["summary"]["errors"]),
            "reason": "Per-route closure is ready, but global deterministic HTTP wiring/auth/error policy is not yet closed.",
            "next_command": _command("python", "tools/design_router_context.py", project_text, "--coverage", "--json"),
            "summary": context["summary"],
            "unresolved_topics": context["unresolved_topics"],
            "router_allowed": True,
        }

    notes = notes_gate.coverage(project)
    if not notes["summary"]["handoff_ready"]:
        only_missing = notes["findings"] and all(item["code"] == "missing_notes_file" for item in notes["findings"])
        return {
            "schema_version": SCHEMA,
            "project_root": project.resolve().name,
            "phase": "state7_notes",
            "blocked": False if only_missing else bool(notes["summary"]["blocks"] or notes["summary"]["reviews"]),
            "reason": "Deterministic structures are closed; author State 7 notes and resolve all address/class/reference, cross-note consistency, and semantic-stub findings before handoff.",
            "next_command": _command("python", "tools/design_notes.py", project_text, "--gate", "--json"),
            "summary": notes["summary"],
            "findings": notes["findings"],
            "router_allowed": True,
        }

    return {
        "schema_version": SCHEMA,
        "project_root": project.resolve().name,
        "phase": "state8_assembly",
        "blocked": False,
        "reason": "State 6 contracts, deterministic Router closure, and State 7 notes gate are ready; continue to final specification assembly.",
        "next_command": None,
        "summary": notes["summary"],
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
    except (ValueError, design_stage6_contracts.DesignStage6ContractsError, design_router_context.RouterContextError, json.JSONDecodeError) as exc:
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
