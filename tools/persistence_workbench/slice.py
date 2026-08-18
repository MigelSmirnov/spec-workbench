from __future__ import annotations

from typing import Any

from persistence_workbench.contract_validation import deterministic_method_scopes
from persistence_workbench.model import PersistenceBackendError


def _rules_backend(spec: dict[str, Any]) -> dict[str, Any] | None:
    rules = spec.get("rules")
    if not isinstance(rules, dict):
        return None
    payload = rules.get("persistence_backend")
    return payload if isinstance(payload, dict) else None


def module_slice(spec: dict[str, Any], module: str) -> dict[str, Any]:
    """Return only deterministic persistence IR owned or consumed by one module.

    The function assumes final assembly validation owns correctness. It still
    fails closed if the supposedly validated backend assigns more than one
    repository class to the requested module.
    """
    payload = _rules_backend(spec)
    if payload is None:
        return {
            "enabled": False,
            "module": module,
            "repository": None,
            "tables": [],
            "aggregates": [],
            "deterministic_method_scopes": [],
        }

    repositories = payload.get("repositories")
    rows = [
        row for row in repositories if isinstance(row, dict) and row.get("module") == module
    ] if isinstance(repositories, list) else []
    if len(rows) > 1:
        raise PersistenceBackendError(
            f"persistence backend assigns {len(rows)} repositories to module {module!r}"
        )
    if not rows:
        return {
            "enabled": True,
            "module": module,
            "backend": payload.get("backend"),
            "conventions": payload.get("conventions"),
            "repository": None,
            "tables": [],
            "aggregates": [],
            "deterministic_method_scopes": [],
        }

    repository = rows[0]
    method_rows = repository.get("methods") if repository.get("emission") == "table" else []
    method_rows = method_rows if isinstance(method_rows, list) else []
    direct_tables = {
        row.get("table") for row in method_rows
        if isinstance(row, dict) and isinstance(row.get("table"), str)
    }
    aggregate_names = {
        row.get("aggregate") for row in method_rows
        if isinstance(row, dict) and isinstance(row.get("aggregate"), str)
    }

    aggregates_payload = payload.get("aggregates")
    aggregates = [
        row for row in aggregates_payload
        if isinstance(row, dict) and row.get("aggregate") in aggregate_names
    ] if isinstance(aggregates_payload, list) else []

    aggregate_tables: set[str] = set()
    for aggregate in aggregates:
        root = aggregate.get("root")
        if isinstance(root, dict) and isinstance(root.get("table"), str):
            aggregate_tables.add(root["table"])
        relations = aggregate.get("relations")
        if isinstance(relations, list):
            aggregate_tables.update(
                relation["table"]
                for relation in relations
                if isinstance(relation, dict) and isinstance(relation.get("table"), str)
            )
    referenced_tables = direct_tables | aggregate_tables
    tables_payload = payload.get("tables")
    tables = [
        row for row in tables_payload
        if isinstance(row, dict) and row.get("table") in referenced_tables
    ] if isinstance(tables_payload, list) else []

    isolated_payload = {"repositories": [repository]}
    scopes = sorted(deterministic_method_scopes(isolated_payload))
    return {
        "enabled": True,
        "module": module,
        "backend": payload.get("backend"),
        "conventions": payload.get("conventions"),
        "repository": repository,
        "tables": tables,
        "aggregates": aggregates,
        "deterministic_method_scopes": scopes,
    }
