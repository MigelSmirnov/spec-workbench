from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import design_stage6_contracts
import design_stage6_data
from identity_workbench import verify as verify_identity
from notes_workbench import gate as notes_gate
from router_workbench import service as router_service

from assembly_workbench.model import AssemblyWorkbenchError, CheckResult

ReportFunction = Callable[[Path], dict[str, Any]]

def _severity_count(findings: list[dict[str, Any]], values: set[str]) -> int:
    return sum(item.get("severity") in values for item in findings)

def _normalize(name: str, report: dict[str, Any]) -> CheckResult:
    summary = report.get("summary")
    findings = report.get("findings", [])
    if not isinstance(summary, dict) or not isinstance(findings, list):
        raise AssemblyWorkbenchError(f"{name} returned an invalid report shape.")
    if name == "identity":
        errors = int(summary.get("errors", len(findings)))
        warnings = 0
        ready = errors == 0
    elif name == "data":
        errors = int(summary.get("errors", 0))
        warnings = _severity_count(findings, {"warning", "review"})
        ready = errors == 0
    elif name == "contracts":
        errors = int(summary.get("errors", 0))
        warnings = int(summary.get("warnings", _severity_count(findings, {"warning"})))
        ready = bool(summary.get("handoff_ready"))
    elif name == "notes":
        errors = int(summary.get("blocks", 0))
        warnings = int(summary.get("reviews", 0))
        ready = bool(summary.get("handoff_ready"))
    elif name == "router":
        errors = int(summary.get("errors", 0))
        warnings = _severity_count(findings, {"warning", "review"})
        ready = bool(summary.get("handoff_ready"))
    else:
        raise AssemblyWorkbenchError(f"Unknown assembly check: {name}")
    return CheckResult(
        name=name,
        ready=ready,
        schema_version=report.get("schema_version"),
        errors=errors,
        warnings=warnings,
        summary=summary,
        findings=findings,
    )

CHECKS: dict[str, ReportFunction] = {
    "identity": verify_identity,
    "data": design_stage6_data.lint,
    "contracts": design_stage6_contracts.lint,
    "notes": notes_gate.coverage,
    "router": router_service.coverage,
}

def run(project: Path, name: str) -> CheckResult:
    function = CHECKS.get(name)
    if function is None:
        raise AssemblyWorkbenchError(f"Unknown assembly check: {name}")
    try:
        report = function(project)
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise AssemblyWorkbenchError(f"{name} check failed to load: {error}") from error
    return _normalize(name, report)
