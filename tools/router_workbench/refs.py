from __future__ import annotations

from typing import Any

from router_workbench.model import Finding


REF_FIELDS = {
    "slot": frozenset({"ref", "name"}),
    "credential": frozenset({"ref", "name"}),
    "parameter": frozenset({"ref", "path"}),
    "enum": frozenset({"ref", "type", "member"}),
    "literal": frozenset({"ref", "value"}),
}


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_ref(value: Any, *, operation: str | None, location: str) -> list[Finding]:
    if isinstance(value, str):
        return [Finding("error", "python_string_arg", "call arguments must use typed refs, not Python-like strings", operation, location)]
    if not isinstance(value, dict):
        return [Finding("error", "invalid_ref", "call argument must be a typed-ref object", operation, location)]
    kind = value.get("ref")
    if kind not in REF_FIELDS:
        return [Finding("error", "unknown_ref_kind", f"unknown typed ref kind: {kind!r}", operation, location)]
    findings: list[Finding] = []
    expected = REF_FIELDS[kind]
    extra = sorted(set(value) - expected)
    missing = sorted(expected - set(value))
    if extra:
        findings.append(Finding("error", "unknown_ref_field", f"unexpected fields for {kind} ref: {extra}", operation, location))
    if missing:
        findings.append(Finding("error", "missing_ref_field", f"missing fields for {kind} ref: {missing}", operation, location))
        return findings
    if kind in {"slot", "credential"} and not _non_empty_string(value["name"]):
        findings.append(Finding("error", "invalid_ref_name", f"{kind} ref name must be a non-empty string", operation, location))
    elif kind == "parameter":
        path = value["path"]
        if not isinstance(path, list) or not path or not all(_non_empty_string(part) for part in path):
            findings.append(Finding("error", "invalid_parameter_path", "parameter ref path must be a non-empty string list", operation, location))
    elif kind == "enum":
        if not _non_empty_string(value["type"]) or not _non_empty_string(value["member"]):
            findings.append(Finding("error", "invalid_enum_ref", "enum ref type and member must be non-empty strings", operation, location))
    elif kind == "literal" and isinstance(value["value"], (dict, list)):
        findings.append(Finding("error", "invalid_literal_ref", "literal ref value must be a JSON scalar or null", operation, location))
    return findings


def validate_argument_refs(node: Any, *, operation: str | None, location: str = "item") -> list[Finding]:
    """Validate every normative call args list found in a table route row."""
    findings: list[Finding] = []
    if isinstance(node, dict):
        for key, value in node.items():
            child_location = f"{location}.{key}"
            if key == "args":
                if not isinstance(value, list):
                    findings.append(Finding("error", "invalid_args", "args must be a list of typed refs", operation, child_location))
                else:
                    for index, argument in enumerate(value):
                        findings.extend(validate_ref(argument, operation=operation, location=f"{child_location}[{index}]"))
            else:
                findings.extend(validate_argument_refs(value, operation=operation, location=child_location))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            findings.extend(validate_argument_refs(value, operation=operation, location=f"{location}[{index}]"))
    return findings
