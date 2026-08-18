from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from persistence_workbench.contract_validation import validate_contracts
from persistence_workbench.model import COVERAGE_SCHEMA, PersistenceBackendError
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


def coverage(project: Path) -> dict[str, Any]:
    """Inspect the optional deterministic persistence backend in assembled spec.

    Absence is valid and means persistence remains on the ordinary generation
    path. Presence opts the project into the closed v2 backend and therefore
    must validate fail-closed.
    """
    spec = _load_spec(project)
    rules = spec.get("rules")
    if not isinstance(rules, dict):
        return {
            "schema_version": COVERAGE_SCHEMA,
            "project_root": project.resolve().name,
            "enabled": False,
            "ready": False,
            "summary": {
                "tables": 0,
                "aggregates": 0,
                "repositories": 0,
                "deterministic_repositories": 0,
                "irregular_repositories": 0,
                "errors": 1,
                "handoff_ready": False,
            },
            "deterministic_modules": [],
            "irregular_modules": [],
            "findings": [{
                "severity": "error",
                "code": "invalid_rules_container",
                "message": "rules must be an object before persistence_backend can be inspected",
                "location": "rules",
            }],
        }

    payload = rules.get("persistence_backend")
    if payload is None:
        return {
            "schema_version": COVERAGE_SCHEMA,
            "project_root": project.resolve().name,
            "enabled": False,
            "ready": True,
            "summary": {
                "tables": 0,
                "aggregates": 0,
                "repositories": 0,
                "deterministic_repositories": 0,
                "irregular_repositories": 0,
                "errors": 0,
                "handoff_ready": True,
            },
            "deterministic_modules": [],
            "irregular_modules": [],
            "findings": [],
        }

    findings = validate(payload)
    tables = payload.get("tables") if isinstance(payload, dict) and isinstance(payload.get("tables"), list) else []
    aggregates = payload.get("aggregates") if isinstance(payload, dict) and isinstance(payload.get("aggregates"), list) else []
    repositories = payload.get("repositories") if isinstance(payload, dict) and isinstance(payload.get("repositories"), list) else []
    repository_rows = [row for row in repositories if isinstance(row, dict)]
    structural_errors = sum(item.severity == "error" for item in findings)
    if structural_errors == 0 and repository_rows:
        findings.extend(validate_contracts(spec, payload))

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
        "enabled": True,
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
        "findings": [item.to_dict() for item in findings],
    }
