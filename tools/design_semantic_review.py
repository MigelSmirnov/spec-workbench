#!/usr/bin/env python3
"""Deterministic context builder for Stage 7.1 semantic E2E review."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from semantic_review import flow_slice


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--flow", required=True)
    parser.add_argument("--slice", action="store_true", help="Build the Stage 7.1 flow review slice.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if not args.project.is_dir():
        print(f"design_semantic_review: error: project directory not found: {args.project}", file=sys.stderr)
        return 2
    if not args.slice:
        print("design_semantic_review: error: --slice is currently required", file=sys.stderr)
        return 2

    try:
        payload = flow_slice.build(args.project, args.flow)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"design_semantic_review: error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        flow = payload["flow"]["key"]
        print(
            f"{flow}: {len(payload['modules'])} modules; "
            f"{len(payload['contracts'])} contracts; {len(payload['notes'])} notes"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
