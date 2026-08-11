from __future__ import annotations

from pathlib import Path
from typing import Any

import design_stage6_contracts
from router_workbench import catalog
from router_workbench.coverage import build as build_coverage
from router_workbench.model import LINT_SCHEMA, NEXT_SCHEMA
from router_workbench.slice import exposure_boundary, semantic_operation_slice


def coverage(project: Path) -> dict[str, Any]:
    payload = catalog.load(project)
    boundary = exposure_boundary(project)
    report = build_coverage(payload, boundary, project_root=project.resolve().name)
    contracts = design_stage6_contracts.handoff(project)
    if not contracts["ready"]:
        report["findings"].append({
            "severity": "error",
            "code": "state6_contract_handoff_not_ready",
            "message": "Router Closure requires closed exact State 6 contracts before route design.",
        })
        report["summary"]["errors"] += 1
        report["summary"]["handoff_ready"] = False
    return report


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
    contract_blocked = any(item.get("code") == "state6_contract_handoff_not_ready" for item in report["findings"])
    operation = None if contract_blocked else (report["unresolved_operations"][0] if report["unresolved_operations"] else None)
    return {
        "schema_version": NEXT_SCHEMA,
        "project_root": report["project_root"],
        "complete": operation is None and not contract_blocked and report["summary"]["handoff_ready"],
        "blocked": contract_blocked,
        "next": None if operation is None else {
            "operation": operation,
            "semantic_slice": semantic_operation_slice(project, operation),
        },
        "summary": report["summary"],
        "findings": report["findings"] if contract_blocked else [],
    }
