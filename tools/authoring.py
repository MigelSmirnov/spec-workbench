#!/usr/bin/env python3
"""Common Spec Workbench authoring CLI for every indexed project.

This is a thin transport facade over ``authoring_pipeline``. Future MCP tooling
must call the same library API rather than duplicate project resolution or
phase-routing logic.
"""
from __future__ import annotations

import argparse
import json
import sys

import authoring_pipeline
import design_authoring_next
import project_navigation


def _print_next(payload: dict[str, object]) -> None:
    project = payload["project"]
    authoring = payload["authoring"]
    print(f"Project: {project['title']} ({project['id']})")
    print(f"Ref:     {project['canonical_ref']}")
    print(f"Path:    {project['path']}")
    print(f"Next:    {authoring['phase']}")
    print(authoring["reason"])
    action = authoring.get("action")
    if action:
        print(f"Gate:    {action['tool']}")
        print("Args:    " + " ".join(action["args"]))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    nxt = sub.add_parser("next", help="resolve a project and report its next authoring phase")
    nxt.add_argument("project", help="project id, title, or indexed alias")
    nxt.add_argument("--json", action="store_true", help="emit stable JSON")

    seq = sub.add_parser("sequence", help="show the machine-readable authoring sequence")
    seq.add_argument("--json", action="store_true", help="emit stable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "sequence":
            payload = authoring_pipeline.sequence()
            if args.json:
                print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                for phase in payload["phases"]:
                    print(f"{phase['id']}: {phase['status']} ({phase['mode']})")
            return 0

        repo_root = authoring_pipeline.find_repo_root()
        payload = authoring_pipeline.project_next(repo_root, args.project)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            _print_next(payload)
        return 1 if payload["authoring"]["blocked"] else 0
    except (
        authoring_pipeline.AuthoringPipelineError,
        design_authoring_next.AuthoringSequenceError,
        project_navigation.NavigationError,
    ) as exc:
        print(f"authoring: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
