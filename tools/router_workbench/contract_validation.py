from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import design_stage6_contracts
from router_workbench.model import Finding, RouterClosureError


PATH_PARAM_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")
PARAM_RE = re.compile(r"(?:^|,\s*)([A-Za-z_][A-Za-z0-9_]*)(?:\s*:\s*([^,=]+))?(?:\s*=\s*[^,]+)?")


def _signature_parameters(signature: str) -> list[tuple[str, bool]]:
    inside = signature.split("->", 1)[0].strip()
    if not (inside.startswith("(") and inside.endswith(")")):
        return []
    body = inside[1:-1].strip()
    if not body:
        return []
    result: list[tuple[str, bool]] = []
    depth = 0
    start = 0
    parts: list[str] = []
    for index, char in enumerate(body):
        if char in "([":
            depth += 1
        elif char in ")]":
            depth -= 1
        elif char == "," and depth == 0:
            parts.append(body[start:index].strip())
            start = index + 1
    parts.append(body[start:].strip())
    for part in parts:
        if not part:
            continue
        name = part.split(":", 1)[0].split("=", 1)[0].strip()
        if name == "self":
            continue
        result.append((name, "=" in part))
    return result


def _arity(signature: str) -> tuple[int, int]:
    params = _signature_parameters(signature)
    required = sum(not has_default for _, has_default in params)
    return required, len(params)


def _parameter_names(signature: str) -> set[str]:
    return {name for name, _ in _signature_parameters(signature)}


def _walk_parameter_refs(node: Any, location: str = "item") -> list[tuple[str, list[str]]]:
    result: list[tuple[str, list[str]]] = []
    if isinstance(node, dict):
        if node.get("ref") == "parameter" and isinstance(node.get("path"), list):
            result.append((location, node["path"]))
        for key, value in node.items():
            result.extend(_walk_parameter_refs(value, f"{location}.{key}"))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            result.extend(_walk_parameter_refs(value, f"{location}[{index}]"))
    return result


def _contracts(project: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    handoff = design_stage6_contracts.handoff(project)
    if not handoff["ready"]:
        raise RouterClosureError("State 6 contract handoff is not ready; Router Closure is post-contract")
    all_contracts: dict[str, dict[str, Any]] = handoff["contracts"]
    by_public = {
        value["public_operation"]: {"function": name, **value}
        for name, value in all_contracts.items()
        if value.get("public_operation") is not None
    }
    by_router = {
        value["router_operation"]: {"function": name, **value}
        for name, value in all_contracts.items()
        if value.get("router_operation") is not None
    }
    return handoff, by_public, by_router


def validate(project: Path, payload: dict[str, Any]) -> list[Finding]:
    """Validate resolved Router Closure rows against canonical State 6 contracts."""
    _, operations, handlers = _contracts(project)
    findings: list[Finding] = []
    items = payload.get("items") if isinstance(payload.get("items"), list) else []
    ownership = payload.get("irregular_ownership")

    for index, item in enumerate(items):
        if not isinstance(item, dict) or item.get("emission") == "unresolved":
            continue
        operation = item.get("operation")
        if not isinstance(operation, str):
            continue
        location = f"items[{index}]"
        operation_contract = operations.get(operation)
        handler_contract = handlers.get(operation)
        if operation_contract is None:
            findings.append(Finding("error", "missing_operation_contract", "resolved route has no canonical State 6 public-operation contract", operation, location))
            continue
        if handler_contract is None:
            findings.append(Finding("error", "missing_handler_contract", "resolved route has no canonical State 6 handler contract", operation, location))
            continue

        expected_handler = handler_contract["function"]
        if item.get("handler") != expected_handler:
            findings.append(Finding("error", "handler_contract_mismatch", f"handler must be canonical State 6 handler {expected_handler!r}", operation, f"{location}.handler"))

        handler_signature = handler_contract["signature"]
        handler_parameters = _parameter_names(handler_signature)
        path_params = set(PATH_PARAM_RE.findall(item.get("path", "") if isinstance(item.get("path"), str) else ""))
        missing_path = sorted(path_params - handler_parameters)
        if missing_path:
            findings.append(Finding("error", "unknown_handler_path_parameter", f"path parameters are absent from canonical handler contract: {missing_path}", operation, f"{location}.path"))

        for ref_location, path in _walk_parameter_refs(item, location):
            if path and path[0] not in handler_parameters:
                findings.append(Finding("error", "unknown_handler_parameter_ref", f"parameter ref root {path[0]!r} is absent from canonical handler contract", operation, ref_location))

        if item.get("emission") == "irregular":
            expected_module = handler_contract["module"].removeprefix("module:")
            actual_module = ownership.get("module") if isinstance(ownership, dict) else None
            if actual_module != expected_module:
                findings.append(Finding("error", "irregular_owner_contract_mismatch", f"irregular ownership must match canonical handler module {expected_module!r}", operation, "irregular_ownership.module"))
            continue

        delegate = item.get("delegate")
        if not isinstance(delegate, dict):
            continue
        expected_delegate = operation_contract["function"]
        if delegate.get("function") != expected_delegate:
            findings.append(Finding("error", "delegate_contract_mismatch", f"delegate must be canonical public function {expected_delegate!r}", operation, f"{location}.delegate.function"))
            continue
        args = delegate.get("args")
        if isinstance(args, list):
            required, maximum = _arity(operation_contract["signature"])
            if not required <= len(args) <= maximum:
                findings.append(Finding("error", "delegate_arity_mismatch", f"delegate provides {len(args)} arguments but canonical contract accepts {required}..{maximum}", operation, f"{location}.delegate.args"))

    return findings
