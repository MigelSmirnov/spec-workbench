#!/usr/bin/env python3
"""Post-contract authoring facade for optional persistence_backend/v2 closure."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from persistence_workbench import authoring
from persistence_workbench.model import PersistenceBackendError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--coverage", action="store_true")
    action.add_argument("--handoff", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.project.is_dir():
        print(f"design_persistence_authoring: error: project directory not found: {args.project}", file=sys.stderr)
        return 2
    try:
        report = authoring.handoff(args.project) if args.handoff else authoring.coverage(args.project)
    except (PersistenceBackendError, ValueError, json.JSONDecodeError) as exc:
        print(f"design_persistence_authoring: error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        summary = report["summary"]
        print(
            "Persistence closure: "
            f"enabled={str(report['enabled']).lower()} "
            f"closed={str(summary['closed']).lower()} "
            f"repositories={summary['repositories']} "
            f"errors={summary['errors']} "
            f"handoff_ready={str(summary['handoff_ready']).lower()}"
        )
    return 0 if report["summary"]["handoff_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
