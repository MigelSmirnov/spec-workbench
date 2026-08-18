from __future__ import annotations

from typing import Any

from persistence_workbench.model import Finding


TRANSACTION_METHODS = frozenset({"begin", "commit", "rollback", "close"})


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _method_contract(repository: str, method: str) -> tuple[str | None, str | None]:
    """Return canonical contract key and an ownership error, if any.

    The v2 IR may use a bare method identifier. Accept an already-qualified
    identifier as input as well, but never let it point at a different class.
    """
    if "." not in method:
        return f"{repository}.{method}", None
    owner, _, leaf = method.partition(".")
    if owner != repository or not leaf:
        return None, f"method {method!r} is not owned by repository {repository!r}"
    return method, None


def validate_contracts(spec: dict[str, Any], payload: dict[str, Any]) -> list[Finding]:
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
