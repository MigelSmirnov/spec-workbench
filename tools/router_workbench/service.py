from __future__ import annotations

from pathlib import Path
from typing import Any

from router_workbench import catalog
from router_workbench.coverage import build as build_coverage
from router_workbench.model import LINT_SCHEMA, NEXT_SCHEMA
from router_workbench.slice import exposure_boundary, semantic_operation_slice


def coverage(project: Path) -> dict[str, Any]:
    payload = catalog.load(project)
    boundary = exposure_boundary(project)
    return build_coverage(payload, boundary, project_root=project.resolve().name)


def lint(project: Path) -> dict[str, Any]:
    report = coverage(project)
    findings = list(report["findings"])
    findings.extend({
        "severity": "warning",
        "code": "unresolved_closure",
        "message": "operation is not ready for Factory handoff",
        "operation": operation,
    } for operation in report["unresolved_operations"])
    return {
        "schema_version": LINT_SCHEMA,
        "project_root": report["project_root"],
        "summary": {
            **report["summary"],
            "warnings": sum(item["severity"] == "warning" for item in findings),
        },
        "findings": findings,
    }


def next_operation(project: Path) -> dict[str, Any]:
    report = coverage(project)
    operation = report["unresolved_operations"][0] if report["unresolved_operations"] else None
    return {
        "schema_version": NEXT_SCHEMA,
        "project_root": report["project_root"],
        "complete": operation is None and report["summary"]["handoff_ready"],
        "next": None if operation is None else {
            "operation": operation,
            "semantic_slice": semantic_operation_slice(project, operation),
        },
        "summary": report["summary"],
    }
