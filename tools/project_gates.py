"""Generic runner for project-declared deterministic gates."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import project_extensions


REPORT_SCHEMA = "spec_workbench_project_gates.v1"
RESULT_SCHEMA = "spec_workbench_project_gate_result.v1"


def _error_finding(gate_id: str, code: str, message: str) -> dict[str, Any]:
    return {
        "severity": "error",
        "code": code,
        "gate": gate_id,
        "message": message,
        "hint": "repair the project-owned gate or the project design before continuing",
    }


def _validate_result(gate_id: str, report: Any) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    findings: list[dict[str, Any]] = []
    if not isinstance(report, dict):
        return None, [_error_finding(gate_id, "invalid_gate_report", "gate returned a non-object report")]
    if report.get("schema_version") != RESULT_SCHEMA:
        findings.append(
            _error_finding(
                gate_id,
                "invalid_gate_schema",
                f"expected schema_version {RESULT_SCHEMA}, got {report.get('schema_version')!r}",
            )
        )
    if not isinstance(report.get("ready"), bool):
        findings.append(_error_finding(gate_id, "invalid_gate_ready", "gate report needs boolean ready"))
    summary = report.get("summary")
    if not isinstance(summary, dict):
        findings.append(_error_finding(gate_id, "invalid_gate_summary", "gate report needs summary object"))
        summary = {}
    errors = summary.get("errors", 0)
    warnings = summary.get("warnings", 0)
    if not isinstance(errors, int) or errors < 0:
        findings.append(_error_finding(gate_id, "invalid_gate_errors", "summary.errors must be a non-negative integer"))
    if not isinstance(warnings, int) or warnings < 0:
        findings.append(_error_finding(gate_id, "invalid_gate_warnings", "summary.warnings must be a non-negative integer"))
    gate_findings = report.get("findings")
    if not isinstance(gate_findings, list) or any(not isinstance(item, dict) for item in gate_findings):
        findings.append(_error_finding(gate_id, "invalid_gate_findings", "gate findings must be a list of objects"))
    return report, findings


def coverage(project: Path) -> dict[str, Any]:
    """Run every gate declared by one project and return a normalized aggregate report."""
    project = project.resolve()
    findings: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []

    try:
        gates = project_extensions.project_gates(project)
    except project_extensions.ProjectExtensionError as exc:
        findings.append(_error_finding("manifest", "project_gate_manifest_invalid", str(exc)))
        gates = []

    for gate in gates:
        try:
            raw = gate.run_gate(project)
        except Exception as exc:  # project code is an extension boundary; fail closed
            findings.append(_error_finding(gate.id, "project_gate_crashed", f"{type(exc).__name__}: {exc}"))
            continue
        report, validation = _validate_result(gate.id, raw)
        findings.extend(validation)
        if report is None or validation:
            continue
        summary = report["summary"]
        gate_findings = report["findings"]
        for item in gate_findings:
            normalized = dict(item)
            normalized.setdefault("gate", gate.id)
            normalized.setdefault("severity", "error")
            findings.append(normalized)
        results.append(
            {
                "id": gate.id,
                "ready": bool(report["ready"]),
                "errors": int(summary.get("errors", 0)),
                "warnings": int(summary.get("warnings", 0)),
                "schema_version": report["schema_version"],
            }
        )

    errors = sum(item.get("severity") == "error" for item in findings)
    warnings = sum(item.get("severity") in {"warning", "review"} for item in findings)
    declared = len(gates)
    ready = errors == 0 and warnings == 0 and all(item["ready"] for item in results) and len(results) == declared
    return {
        "schema_version": REPORT_SCHEMA,
        "ready": ready,
        "summary": {
            "gates": declared,
            "ready_gates": sum(item["ready"] for item in results),
            "errors": errors,
            "warnings": warnings,
            "handoff_ready": ready,
        },
        "results": results,
        "findings": findings,
    }
