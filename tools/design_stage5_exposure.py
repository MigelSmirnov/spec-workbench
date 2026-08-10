#!/usr/bin/env python3
"""Validate State 5 public-operation exposure intent without inventing HTTP lowering."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import design_stage5

SCHEMA = "spec_workbench_state5_exposure_lint.v1"
EXPOSURE_SCHEMA = "spec_workbench_state5_exposure.v1"
EXPOSURE_FILE = "50_exposure_plan.json"
ALLOWED = {"external", "internal-only"}
FORCED_INTERNAL_PREFIXES = (
    "public_op:access_control.",
    "public_op:holded_gateway.",
)


def lint(project: Path) -> dict[str, object]:
    plan = project / EXPOSURE_FILE
    findings: list[dict[str, str]] = []
    try:
        payload = json.loads(plan.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"schema_version": SCHEMA, "summary": {"operations": 0, "external": 0, "internal_only": 0, "errors": 1},
                "findings": [{"code": "exposure_plan_unreadable", "message": str(exc)}]}
    if payload.get("schema_version") != EXPOSURE_SCHEMA:
        findings.append({"code": "unsupported_exposure_schema", "message": f"expected {EXPOSURE_SCHEMA}"})
    mapping = payload.get("operations")
    if not isinstance(mapping, dict):
        mapping = {}
        findings.append({"code": "invalid_exposure_operations", "message": "operations must be an object"})

    state5 = design_stage5.coverage(project)
    planned = {row["key"] for row in state5["operations"]}
    classified = set(mapping)
    for key in sorted(planned - classified):
        findings.append({"code": "missing_exposure", "message": key})
    for key in sorted(classified - planned):
        findings.append({"code": "unknown_exposure_operation", "message": key})
    for key, exposure in sorted(mapping.items()):
        if exposure not in ALLOWED:
            findings.append({"code": "invalid_exposure_value", "message": f"{key}: {exposure!r}"})
        if exposure == "external" and key.startswith(FORCED_INTERNAL_PREFIXES):
            findings.append({"code": "forbidden_external_boundary", "message": key})

    external = sum(value == "external" for value in mapping.values())
    internal = sum(value == "internal-only" for value in mapping.values())
    return {
        "schema_version": SCHEMA,
        "summary": {
            "operations": len(planned),
            "classified": len(planned & classified),
            "external": external,
            "internal_only": internal,
            "errors": len(findings),
        },
        "findings": findings,
        "external_operations": sorted(key for key, value in mapping.items() if value == "external"),
        "internal_only_operations": sorted(key for key, value in mapping.items() if value == "internal-only"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = lint(args.project)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        s = report["summary"]
        print(f"State 5 exposure: {s['classified']}/{s['operations']} classified; {s['external']} external; {s['internal_only']} internal-only; {s['errors']} errors")
        for finding in report["findings"]:
            print(f"ERROR {finding['code']} - {finding['message']}")
    return 1 if report["summary"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
