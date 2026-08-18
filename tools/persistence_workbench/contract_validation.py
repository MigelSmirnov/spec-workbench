from __future__ import annotations

from pathlib import Path
from typing import Any

import design_stage6_contracts

from persistence_workbench.model import Finding


TRANSACTION_METHODS = frozenset({"begin", "commit", "rollback", "close"})


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _method_contract(repository: str, method: str) -> tuple[str | None, str | None]:
    """Return canonical contract key and an ownership error, if any."""
    if "." not in method:
        return f"{repository}.{method}", None
    owner, _, leaf = method.partition(".")
    if owner != repository or not leaf:
        return None, f"method {method!r} is not owned by repository {repository!r}"
    return method, None


def deterministic_method_scopes(payload: dict[str, Any]) -> set[str]:
    """Return canonical contract scopes owned by table-emitted repositories."""
    result: set[str] = set()
    repositories = payload.get("repositories")
    if not isinstance(repositories, list):
        return result
    for row in repositories:
        if not isinstance(row, dict) or row.get("emission") != "table":
            continue
        repository = row.get("repository")
        methods = row.get("methods")
        if not _text(repository) or not isinstance(methods, list):
            continue
        for method_row in methods:
            method = method_row.get("method") if isinstance(method_row, dict) else None
            if not _text(method):
                continue
            contract_name, error = _method_contract(repository, method)
            if error is None and contract_name is not None:
                result.add(contract_name)
    return result


def validate_authoring_contracts(project: Path, payload: dict[str, Any]) -> list[Finding]:
    """Bind a post-contract persistence closure to the canonical State 6 handoff."""
    handoff = design_stage6_contracts.handoff(project)
    if not handoff["ready"]:
        return [Finding(
            "error", "state6_contracts_not_ready",
            "persistence closure is post-contract and requires a ready State 6 handoff",
            location="60_contracts.json",
        )]
    contracts = handoff.get("contracts")
    if not isinstance(contracts, dict):
        return [Finding(
            "error", "invalid_state6_contract_handoff",
            "State 6 handoff did not provide canonical contracts",
            location="60_contracts.json",
        )]

    findings: list[Finding] = []
    repositories = payload.get("repositories")
    if not isinstance(repositories, list):
        return findings

    for index, row in enumerate(repositories):
        if not isinstance(row, dict):
            continue
        location = f"70_persistence_closure.json:backend_ir.repositories[{index}]"
        repository = row.get("repository")
        module = row.get("module")
        schema_function = row.get("schema_function")
        repository_name = repository if _text(repository) else None
        if not (_text(repository) and _text(module) and _text(schema_function)):
            continue

        class_contracts = {
            name: entry
            for name, entry in contracts.items()
            if isinstance(name, str) and name.startswith(repository + ".") and isinstance(entry, dict)
        }
        if not class_contracts:
            findings.append(Finding(
                "error", "missing_repository_class_contracts",
                f"repository class {repository!r} has no canonical State 6 method contracts",
                repository_name, location + ".repository",
            ))
        else:
            wrong = sorted(
                name for name, entry in class_contracts.items()
                if str(entry.get("module", "")).removeprefix("module:") != module
            )
            if wrong:
                findings.append(Finding(
                    "error", "repository_state6_owner_mismatch",
                    f"repository class contracts are not all owned by module {module!r}: {wrong}",
                    repository_name, location + ".module",
                ))

        schema_contract = contracts.get(schema_function)
        if not isinstance(schema_contract, dict):
            findings.append(Finding(
                "error", "missing_schema_function_contract",
                f"schema function {schema_function!r} has no canonical State 6 contract",
                repository_name, location + ".schema_function",
            ))
        elif str(schema_contract.get("module", "")).removeprefix("module:") != module:
            findings.append(Finding(
                "error", "schema_function_state6_owner_mismatch",
                f"schema function {schema_function!r} is not owned by module {module!r}",
                repository_name, location + ".schema_function",
            ))

        if row.get("emission") != "table":
            continue
        methods = row.get("methods")
        if not isinstance(methods, list):
            continue
        for method_index, method_row in enumerate(methods):
            if not isinstance(method_row, dict):
                continue
            method = method_row.get("method")
            if not _text(method):
                continue
            method_location = f"{location}.methods[{method_index}].method"
            leaf = method.rsplit(".", 1)[-1]
            if leaf in TRANSACTION_METHODS:
                findings.append(Finding(
                    "error", "backend_owns_transaction_method",
                    f"persistence_backend/v2 does not own repository transaction method {leaf!r}",
                    repository_name, method_location,
                ))
            contract_name, ownership_error = _method_contract(repository, method)
            if ownership_error is not None:
                findings.append(Finding(
                    "error", "repository_method_owner_mismatch",
                    ownership_error,
                    repository_name, method_location,
                ))
                continue
            contract = contracts.get(contract_name)
            if not isinstance(contract, dict):
                findings.append(Finding(
                    "error", "missing_repository_method_contract",
                    f"repository method {contract_name!r} has no canonical State 6 contract",
                    repository_name, method_location,
                ))
            elif str(contract.get("module", "")).removeprefix("module:") != module:
                findings.append(Finding(
                    "error", "repository_method_state6_owner_mismatch",
                    f"repository method {contract_name!r} is not owned by module {module!r}",
                    repository_name, method_location,
                ))
    return findings


def validate_contracts(spec: dict[str, Any], payload: dict[str, Any]) -> list[Finding]:
    """Bind assembled backend IR to final contracts and module_functions."""
    findings: list[Finding] = []
    contracts = spec.get("contracts")
    module_functions = spec.get("module_functions")
    if not isinstance(contracts, dict):
        return [Finding(
            "error", "invalid_contracts_container",
            "contracts must be an object before persistence ownership can be verified",
            location="contracts",
        )]
    if not isinstance(module_functions, dict):
        return [Finding(
            "error", "invalid_module_functions_container",
            "module_functions must be an object before persistence ownership can be verified",
            location="module_functions",
        )]

    repositories = payload.get("repositories")
    if not isinstance(repositories, list):
        return findings

    for index, row in enumerate(repositories):
        if not isinstance(row, dict):
            continue
        location = f"rules.persistence_backend.repositories[{index}]"
        repository = row.get("repository")
        module = row.get("module")
        schema_function = row.get("schema_function")
        repository_name = repository if _text(repository) else None
        if not (_text(repository) and _text(module) and _text(schema_function)):
            continue

        owned = module_functions.get(module)
        if not isinstance(owned, list):
            findings.append(Finding(
                "error", "unknown_repository_module",
                f"module_functions has no module {module!r}",
                repository_name, location + ".module",
            ))
            owned_symbols: set[str] = set()
        else:
            owned_symbols = {item for item in owned if isinstance(item, str)}

        if repository not in owned_symbols:
            findings.append(Finding(
                "error", "repository_owner_mismatch",
                f"repository class {repository!r} must be owned by module {module!r}",
                repository_name, location + ".repository",
            ))
        if schema_function not in owned_symbols:
            findings.append(Finding(
                "error", "schema_function_owner_mismatch",
                f"schema function {schema_function!r} must be owned by module {module!r}",
                repository_name, location + ".schema_function",
            ))
        if schema_function not in contracts:
            findings.append(Finding(
                "error", "missing_schema_function_contract",
                f"schema function {schema_function!r} has no canonical contract",
                repository_name, location + ".schema_function",
            ))

        if row.get("emission") != "table":
            continue
        methods = row.get("methods")
        if not isinstance(methods, list):
            continue
        for method_index, method_row in enumerate(methods):
            if not isinstance(method_row, dict):
                continue
            method = method_row.get("method")
            if not _text(method):
                continue
            method_location = f"{location}.methods[{method_index}].method"
            leaf = method.rsplit(".", 1)[-1]
            if leaf in TRANSACTION_METHODS:
                findings.append(Finding(
                    "error", "backend_owns_transaction_method",
                    f"persistence_backend/v2 does not own repository transaction method {leaf!r}",
                    repository_name, method_location,
                ))
            contract_name, ownership_error = _method_contract(repository, method)
            if ownership_error is not None:
                findings.append(Finding(
                    "error", "repository_method_owner_mismatch",
                    ownership_error,
                    repository_name, method_location,
                ))
                continue
            if contract_name not in contracts:
                findings.append(Finding(
                    "error", "missing_repository_method_contract",
                    f"repository method {contract_name!r} has no canonical contract",
                    repository_name, method_location,
                ))

    return findings
