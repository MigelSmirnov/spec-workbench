from __future__ import annotations

import fence

from pathlib import Path
from typing import Any

from router_workbench import catalog, service
from router_workbench.contract_validation import validate as validate_contracts
from router_workbench.model import LINT_SCHEMA, NEXT_SCHEMA
from router_workbench.slice import contract_aware_operation_slice, exposure_boundary


def coverage(project: Path) -> dict[str, Any]:
    """Project-aware Router coverage for the official post-State-6 workflow."""
    report = service.coverage(project)
    payload = catalog.load(project)
    contract_findings = [finding.to_dict() for finding in validate_contracts(project, payload)]
    findings = [*report["findings"], *contract_findings]
    errors = sum(item["severity"] == "error" for item in findings)
    summary = {
        **report["summary"],
        "errors": errors,
        "handoff_ready": report["summary"]["unresolved"] == 0 and errors == 0,
    }
    return {**report, "summary": summary, "findings": findings}


def lint(project: Path) -> dict[str, Any]:
    report = coverage(project)
    findings = list(report["findings"])
    findings.extend({
        "severity": "warning",
        "code": "unresolved_closure",
        "message": "operation is not ready for Factory handoff",
        "operation": operation,
    } for operation in report["unresolved_operations"])
    findings = fence.enforce(findings)
    return {
        "schema_version": LINT_SCHEMA,
        "project_root": report["project_root"],
        "summary": {**report["summary"], "errors": fence.stops(findings), "warnings": 0,
                    "handoff_ready": bool(report["summary"].get("handoff_ready")) and fence.stops(findings) == 0},
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
            "semantic_slice": contract_aware_operation_slice(project, operation),
        },
        "summary": report["summary"],
    }
