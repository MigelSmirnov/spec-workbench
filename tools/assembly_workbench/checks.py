from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import design_decision_witness
import design_stage3
import fence
import flow_closure
import design_stage6_contracts
import design_stage6_data
from external_contract_workbench import coverage as external_contract_coverage
from identity_workbench import verify as verify_identity
from notes_workbench import gate as notes_gate
from persistence_workbench import coverage as persistence_coverage
from router_workbench import service as router_service
from spec_language_workbench import verify as verify_language

from assembly_workbench.model import AssemblyWorkbenchError, CheckResult

ReportFunction = Callable[[Path], dict[str, Any]]

def _severity_count(findings: list[dict[str, Any]], values: set[str]) -> int:
    return sum(item.get("severity") in values for item in findings)

def _normalize(name: str, report: dict[str, Any]) -> CheckResult:
    summary = report.get("summary")
    findings = report.get("findings", [])
    if not isinstance(summary, dict) or not isinstance(findings, list):
        raise AssemblyWorkbenchError(f"{name} returned an invalid report shape.")
    if name == "language":
        errors = int(summary.get("errors", len(findings)))
        warnings = 0
        ready = bool(report.get("ready")) and errors == 0
    elif name == "modules":
        errors = int(summary.get("errors", 0))
        warnings = int(summary.get("warnings", 0))
        ready = errors == 0
    elif name == "identity":
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
    elif name == "external_contracts":
        errors = int(summary.get("errors", 0))
        warnings = 0
        ready = bool(summary.get("handoff_ready")) and errors == 0
    elif name == "notes":
        errors = int(summary.get("blocks", 0))
        warnings = int(summary.get("reviews", 0))
        ready = bool(summary.get("handoff_ready"))
    elif name == "router":
        errors = int(summary.get("errors", 0))
        warnings = _severity_count(findings, {"warning", "review"})
        ready = bool(summary.get("handoff_ready"))
    elif name == "persistence":
        errors = int(summary.get("errors", 0))
        warnings = _severity_count(findings, {"warning", "review"})
        ready = bool(summary.get("handoff_ready"))
    elif name in {"witness", "flows"}:
        errors = int(summary.get("errors", len(findings)))
        warnings = 0
        ready = errors == 0
    else:
        raise AssemblyWorkbenchError(f"Unknown assembly check: {name}")
    # the fence: a warning is an undecided fact; it stops the assembly
    findings = fence.enforce(findings)
    if warnings:
        errors += warnings
        warnings = 0
        ready = False
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
    "language": verify_language,
    "modules": design_stage3.lint,
    "identity": verify_identity,
    "data": design_stage6_data.lint,
    "contracts": design_stage6_contracts.lint,
    "external_contracts": external_contract_coverage,
    "notes": notes_gate.coverage,
    "router": router_service.coverage,
    "persistence": persistence_coverage,
    "witness": design_decision_witness.coverage,
    "flows": flow_closure.coverage,
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
