from __future__ import annotations

from collections import Counter
from typing import Any

from router_workbench.model import CATALOG_FILE, COVERAGE_SCHEMA, Finding
from router_workbench.slice import ExposureBoundary
from router_workbench.validator import validate


def build(payload: dict[str, Any], boundary: ExposureBoundary, *, project_root: str) -> dict[str, Any]:
    findings = validate(payload)
    items = payload.get("items") if isinstance(payload.get("items"), list) else []
    rows = [item for item in items if isinstance(item, dict)]
    operations = [item.get("operation") for item in rows if isinstance(item.get("operation"), str)]
    counts = Counter(operations)
    external = set(boundary.external)
    internal = set(boundary.internal_only)

    for operation, count in sorted(counts.items()):
        if count > 1:
            findings.append(Finding("error", "duplicate_operation", "public operation has duplicate Router Closure ownership", operation, f"{CATALOG_FILE}:items"))
    for operation in boundary.external:
        if counts[operation] == 0:
            findings.append(Finding("error", "missing_external_operation", "external operation has no Router Closure item", operation, f"{CATALOG_FILE}:items"))
    for operation in sorted(set(operations)):
        if operation in internal:
            findings.append(Finding("error", "internal_only_exposed", "internal-only operation cannot appear in the route catalog", operation, f"{CATALOG_FILE}:items"))
        elif operation not in external:
            findings.append(Finding("error", "unknown_public_operation", "route catalog references an unknown public operation", operation, f"{CATALOG_FILE}:items"))

    unique_external_rows = {
        item["operation"]: item
        for item in rows
        if isinstance(item.get("operation"), str) and item["operation"] in external and counts[item["operation"]] == 1
    }
    unresolved = sorted(
        operation for operation in boundary.external
        if operation not in unique_external_rows or unique_external_rows[operation].get("emission") == "unresolved"
    )
    resolved = sum(
        item.get("emission") in {"table", "irregular"}
        for item in unique_external_rows.values()
    )
    errors = sum(finding.severity == "error" for finding in findings)
    handoff_ready = errors == 0 and not unresolved and len(unique_external_rows) == len(boundary.external)
    return {
        "schema_version": COVERAGE_SCHEMA,
        "project_root": project_root,
        "summary": {
            "external_operations": len(boundary.external),
            "catalog_items": len(rows),
            "resolved": resolved,
            "unresolved": len(unresolved),
            "errors": errors,
            "handoff_ready": handoff_ready,
        },
        "unresolved_operations": unresolved,
        "findings": [finding.to_dict() for finding in findings],
    }
