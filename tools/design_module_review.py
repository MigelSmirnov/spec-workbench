#!/usr/bin/env python3
"""Build complete module review packets for final semantic review."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from module_review_workbench import build_slice, list_modules, review
from module_review_workbench.model import ModuleReviewError

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--module")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--list", action="store_true")
    action.add_argument("--slice", action="store_true")
    action.add_argument("--review", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if (args.slice or args.review) and not args.module:
        parser.error("--module is required with --slice/--review")
    try:
        payload = list_modules(args.project) if args.list else (
            build_slice(args.project, args.module) if args.slice else review(args.project, args.module)
        )
    except (ModuleReviewError, ValueError) as error:
        print(f"design_module_review: error: {error}", file=sys.stderr)
        return 2
    if args.json or args.list or args.slice:
        print(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        summary = payload["summary"]
        print(
            f"Module review {payload['module']}: {summary['contracts']} contracts; "
            f"{summary['assembled_notes']} notes; {summary['blocks']} blocks; "
            f"{summary['reviews']} review prompts"
        )
    return 1 if args.review and payload["summary"]["blocks"] else 0

if __name__ == "__main__":
    raise SystemExit(main())
