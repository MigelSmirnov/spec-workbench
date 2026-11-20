#!/usr/bin/env python3
"""Stage 7.1: the semantic runtime-test handoff of a case.

A case that declares ``71_semantic_test_export.json`` hands its acceptance
tests to the Factory byte-exact at export. Stage 9 admission (FA006) and
``export_to_factory.py`` refuse a manifest that is not ``semantic_closed``;
this gate runs the same check where the work belongs, after the decision
witnesses and before the imports closure, so the sequencer names it instead
of leaving it to be found at admission (STAGE_7_1_SEMANTIC_HANDOFF.md,
"Handoff result"). A case without the manifest declares no handoff and the
phase does not apply.

    python tools/design_semantic_handoff.py examples/<case> [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from factory_admission_workbench.model import CHECK_BLOCK, CHECK_NOT_APPLICABLE
from factory_admission_workbench.service import SEMANTIC_EXPORT_MANIFEST, semantic_check


def coverage(project: Path) -> dict[str, Any]:
    check = semantic_check(project)
    errors = list(check.evidence.get("errors") or [])
    return {
        "manifest": SEMANTIC_EXPORT_MANIFEST,
        "check": check.to_dict(),
        "summary": {
            "declared": check.status != CHECK_NOT_APPLICABLE,
            "errors": len(errors),
            "handoff_ready": check.status != CHECK_BLOCK,
        },
        "findings": [
            {"code": "semantic_handoff_open", "severity": "error", "message": error} for error in errors
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.project.is_dir():
        print(f"design_semantic_handoff: error: project directory not found: {args.project}", file=sys.stderr)
        return 2
    report = coverage(args.project)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        summary = report["summary"]
        print(f"Semantic handoff: {report['check']['summary']} handoff_ready={str(summary['handoff_ready']).lower()}")
        for finding in report["findings"]:
            print(f"  ✗ {finding['message']}")
    return 0 if report["summary"]["handoff_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
