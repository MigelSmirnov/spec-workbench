from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from persistence_workbench import catalog
from persistence_workbench.codec_coverage import evaluate_codec_coverage
from persistence_workbench.contract_validation import validate_contracts
from persistence_workbench.model import COVERAGE_SCHEMA, Finding, PersistenceBackendError
from persistence_workbench.projection_validation import validate_projection
from persistence_workbench.validator import validate


def _load_spec(project: Path) -> dict[str, Any]:
    path = project / "global_spec.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PersistenceBackendError("missing global_spec.json") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise PersistenceBackendError(f"invalid global_spec.json: {exc}") from exc
    if not isinstance(payload, dict):
        raise PersistenceBackendError("global_spec.json must contain an object")
    return payload


def _report(
    project: Path,
    *,
    enabled: bool,
    payload: Any,
    findings: list[Finding],
    codec_coverage: dict[str, Any] | None = None,
) -> dict[str, Any]:
    tables = payload.get("tables") if isinstance(payload, dict) and isinstance(payload.get("tables"), list) else []
    aggregates = payload.get("aggregates") if isinstance(payload, dict) and isinstance(payload.get("aggregates"), list) else []
    repositories = payload.get("repositories") if isinstance(payload, dict) and isinstance(payload.get("repositories"), list) else []
    repository_rows = [row for row in repositories if isinstance(row, dict)]
    deterministic_modules = sorted({
        row["module"] for row in repository_rows
        if row.get("emission") == "table" and isinstance(row.get("module"), str) and row["module"]
    })
    irregular_modules = sorted({
        row["module"] for row in repository_rows
        if row.get("emission") == "irregular" and isinstance(row.get("module"), str) and row["module"]
    })
    errors = sum(item.severity == "error" for item in findings)
    ready = errors == 0
    return {
        "schema_version": COVERAGE_SCHEMA,
        "project_root": project.resolve().name,
        "enabled": enabled,
        "ready": ready,
        "summary": {
            "tables": len(tables),
            "aggregates": len(aggregates),
            "repositories": len(repository_rows),
            "deterministic_repositories": sum(row.get("emission") == "table" for row in repository_rows),
            "irregular_repositories": sum(row.get("emission") == "irregular" for row in repository_rows),
            "errors": errors,
            "handoff_ready": ready,
        },
        "deterministic_modules": deterministic_modules,
        "irregular_modules": irregular_modules,
        "codec_coverage": codec_coverage,
        "findings": [item.to_dict() for item in findings],
    }


def _codec_findings(report: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    unresolved = report.get("unresolved_columns")
    if (
        report.get("status") == "incomplete"
        and report.get("registry_resolved") is False
        and isinstance(unresolved, list)
        and any(isinstance(item, dict) and item.get("reason") == "backend_registry_unavailable" for item in unresolved)
    ):
        findings.append(Finding(
            "warning",
            "codec_registry_unavailable",
            "codec coverage cannot be proven until the deterministic backend exposes its version-bound domain/storage registry",
            location="rules.persistence_backend",
        ))
    gaps = report.get("gaps")
    if isinstance(gaps, list):
        for gap in gaps:
            if not isinstance(gap, dict):
                continue
            deterministic_module = gap.get("deterministic_module")
            llm_module = gap.get("llm_module")
            pairs = gap.get("pairs")
            findings.append(Finding(
                "warning",
                "codec_coverage_gap",
                f"deterministic module {deterministic_module!r} and LLM module {llm_module!r} share codec pairs: {pairs!r}",
                location="rules.persistence_backend",
            ))
    return findings


def coverage(project: Path) -> dict[str, Any]:
    """Verify final persistence IR and its exact post-contract authoring lineage.

    No closure plus no assembled backend is a valid ordinary-generation path.
    Once either side declares deterministic persistence, the other side must be
    present and exact: final assembly may only project the closed authoring
    ``backend_ir`` into ``rules.persistence_backend`` without semantic edits.
    Codec assurance is nonblocking evidence: until the backend-owned registry is
    available, Workbench records coverage as incomplete rather than guessing.
    """
    spec = _load_spec(project)
    rules = spec.get("rules")
    if not isinstance(rules, dict):
        return _report(
            project,
            enabled=False,
            payload=None,
            findings=[Finding(
                "error",
                "invalid_rules_container",
                "rules must be an object before persistence_backend can be inspected",
                location="rules",
            )],
            codec_coverage=None,
        )

    try:
        closure = catalog.load_optional(project)
    except PersistenceBackendError as exc:
        payload = rules.get("persistence_backend")
        return _report(
            project,
            enabled=True,
            payload=payload,
            findings=[Finding(
                "error",
                "invalid_persistence_closure",
                str(exc),
                location="70_persistence_closure.json",
            )],
            codec_coverage=evaluate_codec_coverage(spec, payload if isinstance(payload, dict) else None),
        )

    payload = rules.get("persistence_backend")
    if closure is None and payload is None:
        return _report(
            project,
            enabled=False,
            payload=None,
            findings=[],
            codec_coverage=evaluate_codec_coverage(spec),
        )

    findings: list[Finding] = []
    if closure is None:
        findings.append(Finding(
            "error",
            "untracked_assembled_persistence_backend",
            "rules.persistence_backend is present but no 70_persistence_closure.json records its post-contract authoring lineage",
            location="rules.persistence_backend",
        ))
    else:
        if closure["status"] != "closed":
            findings.append(Finding(
                "error",
                "persistence_closure_not_closed",
                "70_persistence_closure.json must be closed before final assembly",
                location="70_persistence_closure.json.status",
            ))
        authored = closure["backend_ir"]
        if payload is None:
            findings.append(Finding(
                "error",
                "missing_assembled_persistence_backend",
                "closed persistence closure exists but rules.persistence_backend is absent from global_spec.json",
                location="rules.persistence_backend",
            ))
        elif payload != authored:
            findings.append(Finding(
                "error",
                "persistence_backend_handoff_mismatch",
                "assembled rules.persistence_backend differs from the exact backend_ir in 70_persistence_closure.json",
                location="rules.persistence_backend",
            ))

    codec_report = evaluate_codec_coverage(spec, payload if isinstance(payload, dict) else None)
    if payload is not None:
        structural_findings = validate(payload)
        findings.extend(structural_findings)
        structural_errors = sum(item.severity == "error" for item in structural_findings)
        if structural_errors == 0:
            projection_findings = validate_projection(spec, payload)
            findings.extend(projection_findings)
            projection_errors = sum(item.severity == "error" for item in projection_findings)
            repositories = payload.get("repositories") if isinstance(payload, dict) else None
            repository_rows = [row for row in repositories if isinstance(row, dict)] if isinstance(repositories, list) else []
            if projection_errors == 0:
                findings.extend(_codec_findings(codec_report))
                if repository_rows:
                    findings.extend(validate_contracts(spec, payload))

    return _report(
        project,
        enabled=True,
        payload=payload,
        findings=findings,
        codec_coverage=codec_report,
    )
