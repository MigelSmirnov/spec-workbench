from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable


CODEC_COVERAGE_SCHEMA = "spec_workbench_codec_coverage.v1"
StorageResolver = Callable[[str, str | None, str | None], str]


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _runtime_fields(models: Any, model: Any) -> dict[str, Any] | None:
    if not isinstance(models, dict) or not _text(model):
        return None
    row = models.get(model)
    if not isinstance(row, dict) or row.get("kind") is not None:
        return None
    fields = row.get("fields")
    return fields if isinstance(fields, dict) else None


def _domain_type(fields: dict[str, Any] | None, field: Any) -> str | None:
    if fields is None or not _text(field):
        return None
    declared = fields.get(field)
    if not isinstance(declared, str):
        return None
    value = declared.split("=", 1)[0].strip()
    if value.endswith(" | None"):
        value = value[: -len(" | None")].strip()
    elif value.startswith("None | "):
        value = value[len("None | ") :].strip()
    return value or None


def _pair_dict(pair: tuple[str, str]) -> dict[str, str]:
    return {"domain_type": pair[0], "storage": pair[1]}


def _module_tables(payload: dict[str, Any]) -> tuple[set[str], set[str], dict[str, set[str]]]:
    deterministic: set[str] = set()
    llm: set[str] = set()
    module_tables: dict[str, set[str]] = defaultdict(set)

    aggregates = payload.get("aggregates") if isinstance(payload.get("aggregates"), list) else []
    aggregate_tables: dict[str, set[str]] = {}
    for row in aggregates:
        if not isinstance(row, dict) or not _text(row.get("aggregate")):
            continue
        tables: set[str] = set()
        root = row.get("root")
        if isinstance(root, dict) and _text(root.get("table")):
            tables.add(root["table"])
        relations = row.get("relations") if isinstance(row.get("relations"), list) else []
        for relation in relations:
            if isinstance(relation, dict) and _text(relation.get("table")):
                tables.add(relation["table"])
        aggregate_tables[row["aggregate"]] = tables

    repositories = payload.get("repositories") if isinstance(payload.get("repositories"), list) else []
    for row in repositories:
        if not isinstance(row, dict) or not _text(row.get("module")):
            continue
        module = row["module"]
        emission = row.get("emission")
        if emission == "table":
            deterministic.add(module)
            methods = row.get("methods") if isinstance(row.get("methods"), list) else []
            for method in methods:
                if not isinstance(method, dict):
                    continue
                if _text(method.get("table")):
                    module_tables[module].add(method["table"])
                aggregate = method.get("aggregate")
                if _text(aggregate):
                    module_tables[module].update(aggregate_tables.get(aggregate, set()))
        elif emission == "irregular":
            llm.add(module)

    tables = payload.get("tables") if isinstance(payload.get("tables"), list) else []
    for row in tables:
        if not isinstance(row, dict) or not _text(row.get("table")):
            continue
        reader = row.get("read_by")
        if not _text(reader):
            continue
        module_tables[reader].add(row["table"])
        if reader not in deterministic:
            llm.add(reader)

    return deterministic, llm, module_tables


def evaluate_codec_coverage(
    spec: dict[str, Any],
    payload: dict[str, Any] | None = None,
    *,
    storage_resolver: StorageResolver | None = None,
) -> dict[str, Any]:
    """Evaluate codec assurance from validated persistence v2 projection.

    The Workbench deliberately does not embed the sqlite_sync_v2 domain-type
    registry. A backend-owned ``storage_resolver`` must both validate explicit
    representations and derive omitted unique representations. Without that
    capability the result is nonblocking but cannot claim codec completeness.
    """
    if payload is None:
        rules = spec.get("rules")
        payload = rules.get("persistence_backend") if isinstance(rules, dict) else None
    if not isinstance(payload, dict):
        return {
            "schema_version": CODEC_COVERAGE_SCHEMA,
            "status": "not_applicable",
            "complete": True,
            "backend": None,
            "registry_resolved": True,
            "deterministic_modules": [],
            "llm_modules": [],
            "module_tables": [],
            "module_pairs": [],
            "unresolved_columns": [],
            "gaps": [],
        }

    backend = payload.get("backend") if isinstance(payload.get("backend"), dict) else {}
    backend_identity = {
        "engine": backend.get("engine"),
        "emitter": backend.get("emitter"),
    }
    deterministic, llm, module_tables = _module_tables(payload)
    models = spec.get("models")
    tables = payload.get("tables") if isinstance(payload.get("tables"), list) else []
    table_pairs: dict[str, set[tuple[str, str]]] = defaultdict(set)
    unresolved: list[dict[str, Any]] = []
    column_count = 0

    for table in tables:
        if not isinstance(table, dict) or not _text(table.get("table")):
            continue
        table_name = table["table"]
        fields = _runtime_fields(models, table.get("model"))
        columns = table.get("columns") if isinstance(table.get("columns"), list) else []
        for column in columns:
            if not isinstance(column, dict):
                continue
            column_count += 1
            domain_type = _domain_type(fields, column.get("field"))
            explicit_storage = column.get("storage") if _text(column.get("storage")) else None
            element_model = column.get("element_model") if _text(column.get("element_model")) else None
            location = {
                "table": table_name,
                "column": column.get("column"),
                "field": column.get("field"),
                "domain_type": domain_type,
                "storage": explicit_storage,
            }
            if domain_type is None:
                unresolved.append({**location, "reason": "domain_type_unresolved"})
                continue
            if storage_resolver is None:
                unresolved.append({**location, "reason": "backend_registry_unavailable"})
                continue
            try:
                resolved_storage = storage_resolver(domain_type, explicit_storage, element_model)
            except (KeyError, TypeError, ValueError) as exc:
                unresolved.append({**location, "reason": "backend_pair_unresolved", "detail": str(exc)})
                continue
            if not _text(resolved_storage):
                unresolved.append({**location, "reason": "backend_pair_unresolved"})
                continue
            table_pairs[table_name].add((domain_type, resolved_storage))

    module_pairs: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for module, owned_tables in module_tables.items():
        for table in owned_tables:
            module_pairs[module].update(table_pairs.get(table, set()))

    gaps: list[dict[str, Any]] = []
    if storage_resolver is not None and not unresolved:
        for deterministic_module in sorted(deterministic):
            for llm_module in sorted(llm):
                if deterministic_module == llm_module:
                    continue
                shared = sorted(module_pairs.get(deterministic_module, set()) & module_pairs.get(llm_module, set()))
                if shared:
                    gaps.append({
                        "deterministic_module": deterministic_module,
                        "llm_module": llm_module,
                        "pairs": [_pair_dict(pair) for pair in shared],
                    })

    registry_resolved = storage_resolver is not None and not unresolved
    complete = column_count == 0 or (registry_resolved and not gaps)
    if column_count == 0:
        status = "complete"
        registry_resolved = True
    elif complete:
        status = "complete"
    else:
        status = "incomplete"

    return {
        "schema_version": CODEC_COVERAGE_SCHEMA,
        "status": status,
        "complete": complete,
        "backend": backend_identity,
        "registry_resolved": registry_resolved,
        "deterministic_modules": sorted(deterministic),
        "llm_modules": sorted(llm),
        "module_tables": [
            {"module": module, "tables": sorted(names)}
            for module, names in sorted(module_tables.items())
        ],
        "module_pairs": [
            {"module": module, "pairs": [_pair_dict(pair) for pair in sorted(pairs)]}
            for module, pairs in sorted(module_pairs.items())
            if pairs
        ],
        "unresolved_columns": unresolved,
        "gaps": gaps,
    }
