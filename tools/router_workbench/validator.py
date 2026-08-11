from __future__ import annotations

from typing import Any

from router_workbench.model import CATALOG_SCHEMA, EMISSIONS, Finding
from router_workbench.refs import validate_argument_refs


ROOT_FIELDS = frozenset({"schema_version", "irregular_ownership", "items"})
COMMON_ROUTE_FIELDS = frozenset({
    "operation", "handler", "method", "path", "auth", "success_status",
    "response_mode", "emission",
})
TABLE_FIELDS = COMMON_ROUTE_FIELDS | frozenset({"authorize", "delegate", "projection", "returns"})
IRREGULAR_FIELDS = COMMON_ROUTE_FIELDS | frozenset({"irregular_reason"})
UNRESOLVED_FIELDS = frozenset({"operation", "emission"})
HIDDEN_CODE_FIELDS = frozenset({
    "body", "callable", "code", "implementation", "lambda", "pseudo_code",
    "pseudocode", "python", "python_body", "signature", "source",
})


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _hidden_code_findings(node: Any, operation: str | None, location: str = "item") -> list[Finding]:
    findings: list[Finding] = []
    if isinstance(node, dict):
        for key, value in node.items():
            child = f"{location}.{key}"
            if key in HIDDEN_CODE_FIELDS:
                findings.append(Finding("error", "hidden_python_body", f"executable/signature field {key!r} is forbidden in Router Closure", operation, child))
            findings.extend(_hidden_code_findings(value, operation, child))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            findings.extend(_hidden_code_findings(value, operation, f"{location}[{index}]"))
    return findings


def validate(payload: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    extra_root = sorted(set(payload) - ROOT_FIELDS)
    if extra_root:
        findings.append(Finding("error", "unknown_catalog_field", f"unknown catalog fields: {extra_root}"))
    if payload.get("schema_version") != CATALOG_SCHEMA:
        findings.append(Finding("error", "unsupported_schema", f"expected {CATALOG_SCHEMA!r}"))
    items = payload.get("items")
    if not isinstance(items, list):
        return findings + [Finding("error", "invalid_items", "items must be a list")]

    irregular_count = 0
    for index, item in enumerate(items):
        location = f"items[{index}]"
        if not isinstance(item, dict):
            findings.append(Finding("error", "invalid_item", "closure item must be an object", location=location))
            continue
        operation = item.get("operation") if isinstance(item.get("operation"), str) else None
        if operation is None or not operation.startswith("public_op:"):
            findings.append(Finding("error", "invalid_operation_ref", "item operation must be a canonical public_op:* reference", operation, location))
        emission = item.get("emission")
        if emission not in EMISSIONS:
            findings.append(Finding("error", "invalid_emission", f"emission must be one of {sorted(EMISSIONS)}", operation, location))
            allowed = frozenset({"operation", "emission"})
            required = allowed
        elif emission == "unresolved":
            allowed = required = UNRESOLVED_FIELDS
        elif emission == "table":
            allowed = required = TABLE_FIELDS
            findings.extend(validate_argument_refs(item, operation=operation, location=location))
        else:
            irregular_count += 1
            allowed = required = IRREGULAR_FIELDS
            if not _non_empty_string(item.get("irregular_reason")):
                findings.append(Finding("error", "missing_irregular_reason", "irregular closure requires a non-empty irregular_reason", operation, location))

        extra = sorted(set(item) - allowed)
        missing = sorted(required - set(item))
        if extra:
            findings.append(Finding("error", "unknown_item_field", f"fields are not part of the {emission!r} closure shape: {extra}", operation, location))
        if missing:
            findings.append(Finding("error", "missing_item_field", f"required {emission!r} fields are absent: {missing}", operation, location))
        findings.extend(_hidden_code_findings(item, operation, location))

    ownership = payload.get("irregular_ownership")
    if ownership is not None:
        if not isinstance(ownership, dict) or set(ownership) != {"module"} or not _non_empty_string(ownership.get("module")):
            findings.append(Finding("error", "invalid_irregular_ownership", "irregular_ownership must be null or exactly {'module': <non-empty string>}"))
    if irregular_count and ownership is None:
        findings.append(Finding("error", "missing_irregular_ownership", "irregular items require companion ownership"))
    return findings
