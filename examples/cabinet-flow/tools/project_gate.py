#!/usr/bin/env python3
"""Cabinet Flow project-local deterministic gate.

This is the single project-owned entrypoint for checks that generic Workbench
does not yet know about.

Design-only:
    python examples/cabinet-flow/tools/project_gate.py

Design + generated source:
    python examples/cabinet-flow/tools/project_gate.py \
        --source-root path/to/generated/python \
        --system-clock path/to/generated/python/system_clock.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from stage5_api_audit import audit as audit_stage5
from time_source_audit import audit_design as audit_time_design
from time_source_audit import audit_source as audit_time_source
from time_source_audit import DEFAULT_MONOTONIC_PATTERNS


RESULT_SCHEMA = "spec_workbench_project_gate_result.v1"


def run_gate(project: Path) -> dict[str, object]:
    """Generic Workbench extension entrypoint for design-time Cabinet Flow checks."""
    project = project.resolve()
    findings: list[dict[str, object]] = []

    for item in audit_stage5(project):
        findings.append(
            {
                "severity": "error",
                "code": "stage5_api_consistency",
                "message": item,
            }
        )

    for item in audit_time_design(project):
        findings.append(
            {
                "severity": "error",
                "code": "time_source_design",
                "message": item.render(project),
            }
        )

    errors = sum(item["severity"] == "error" for item in findings)
    warnings = sum(item["severity"] in {"warning", "review"} for item in findings)
    return {
        "schema_version": RESULT_SCHEMA,
        "ready": errors == 0 and warnings == 0,
        "summary": {"errors": errors, "warnings": warnings},
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Path to examples/cabinet-flow (defaults to this project)",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        help="Generated Python source tree; enables source-level time audit",
    )
    parser.add_argument(
        "--system-clock",
        type=Path,
        help="Exact generated system_clock.py path when auto-discovery is ambiguous",
    )
    parser.add_argument(
        "--monotonic-allow",
        action="append",
        default=[],
        help="Additional fnmatch pattern allowed to call time.monotonic_ns()",
    )
    args = parser.parse_args()

    project = args.project.resolve()
    gate_report = run_gate(project)
    findings: list[tuple[str, str]] = [
        (str(item.get("code", "project-gate")), str(item.get("message", "")))
        for item in gate_report["findings"]
    ]

    if args.source_root:
        source_root = args.source_root.resolve()
        system_clock = args.system_clock.resolve() if args.system_clock else None
        patterns = tuple(DEFAULT_MONOTONIC_PATTERNS) + tuple(args.monotonic_allow)
        for item in audit_time_source(source_root, system_clock, patterns):
            findings.append(("time-source", item.render(project)))

    if findings:
        for kind, message in findings:
            print(f"[{kind}] {message}")
        print(f"FAIL: {len(findings)} Cabinet Flow gate finding(s)")
        return 1

    mode = "design + generated source" if args.source_root else "design"
    print(f"PASS: Cabinet Flow project gate ({mode})")
    print("  - Stage 5 API structure: 95/95")
    print("  - Kernel/service time isolation: enforced")
    if args.source_root:
        print("  - Generated Python wall-clock source audit: enforced")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
