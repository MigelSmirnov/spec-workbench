from __future__ import annotations

from pathlib import Path
from typing import Any

from persistence_workbench import catalog
from persistence_workbench.contract_validation import (
    deterministic_method_scopes,
    validate_authoring_contracts,
)
from persistence_workbench.model import AUTHORING_SCHEMA
from persistence_workbench.validator import validate


def coverage(project: Path) -> dict[str, Any]:
    """Validate the optional post-State-6 persistence closure."""
    closure = catalog.load_optional(project)
    if closure is None:
        return {
            "schema_version": AUTHORING_SCHEMA,
            "project_root": project.resolve().name,
            "enabled": False,
            "status": None,
            "ready": True,
            "summary": {
                "repositories": 0,
                "deterministic_methods": 0,
                "errors": 0,
                "closed": True,
                "handoff_ready": True,
            },
            "deterministic_method_scopes": [],
            "findings": [],
        }

    backend_ir = closure["backend_ir"]
    findings = validate(backend_ir)
    structural_errors = sum(item.severity == "error" for item in findings)
    if structural_errors == 0:
        findings.extend(validate_authoring_contracts(project, backend_ir))
    errors = sum(item.severity == "error" for item in findings)
    scopes = sorted(deterministic_method_scopes(backend_ir))
    repositories = backend_ir.get("repositories")
    repository_count = len(repositories) if isinstance(repositories, list) else 0
    closed = closure["status"] == "closed"
    ready = closed and errors == 0
    return {
        "schema_version": AUTHORING_SCHEMA,
        "project_root": project.resolve().name,
        "enabled": True,
        "status": closure["status"],
        "ready": ready,
        "summary": {
            "repositories": repository_count,
            "deterministic_methods": len(scopes),
            "errors": errors,
            "closed": closed,
            "handoff_ready": ready,
        },
        "deterministic_method_scopes": scopes,
        "findings": [item.to_dict() for item in findings],
    }


def handoff(project: Path) -> dict[str, Any]:
    report = coverage(project)
    closure = catalog.load_optional(project)
    return {
        "schema_version": "spec_workbench_persistence_closure_handoff.v1",
        "project_root": report["project_root"],
        "enabled": report["enabled"],
        "ready": report["ready"],
        "summary": report["summary"],
        "backend_ir": closure["backend_ir"] if closure is not None and report["ready"] else None,
        "deterministic_method_scopes": report["deterministic_method_scopes"],
        "findings": report["findings"],
    }
