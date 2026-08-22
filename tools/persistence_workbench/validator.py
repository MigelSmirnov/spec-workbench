from __future__ import annotations

from collections import Counter
from typing import Any

from persistence_workbench.model import (
    Finding,
    SUPPORTED_BACKENDS,
    SUPPORTED_SCHEMA_VERSIONS,
    TRANSACTION_MODES,
)


ROOT_FIELDS = frozenset({
    "kind", "schema_version", "backend", "conventions",
    "tables", "aggregates", "repositories",
})
BACKEND_FIELDS = frozenset({"engine", "emitter"})
CONVENTION_FIELDS = frozenset({
    "assert_open", "guard_reraise", "codec_naming", "primary_key_not_null",
})
CONVENTIONS = {
    "assert_open": "inside_try",
    "guard_reraise": "unchanged",
    "codec_naming": "row_to_snake_model",
    "primary_key_not_null": "always",
}
TABLE_FIELDS = frozenset({
    "table", "table_name_ref", "model", "read_by", "columns", "primary_key", "unique",
})
COLUMN_FIELDS = frozenset({
    "column", "field", "storage", "nullable", "check", "element_model",
})
AGGREGATE_FIELDS = frozenset({"aggregate", "root", "relations"})
ROOT_AGGREGATE_FIELDS = frozenset({"field", "model", "table", "key"})
RELATION_FIELDS = frozenset({
    "field", "model", "table", "cardinality",
    "root_columns", "related_columns", "order_by",
})
TABLE_REPOSITORY_FIELDS = frozenset({
    "repository", "module", "schema_function", "emission", "methods",
})
IRREGULAR_REPOSITORY_FIELDS = frozenset({
    "repository", "module", "schema_function", "emission", "irregular_reason",
})
STORAGE_REPRESENTATIONS = frozenset({
    "text", "integer", "real", "blob", "uuid", "datetime", "decimal", "enum", "json",
})
TABLE_QUERY_FIELDS: dict[str, frozenset[str]] = {
    "insert": frozenset({"table", "columns"}),
    "insert_many": frozenset({"table", "columns"}),
    "get_by_key": frozenset({"table", "filter", "select"}),
    "get_unique": frozenset({"table", "filter", "select", "on_multiple"}),
    "list_by": frozenset({"table", "filter", "select", "order_by"}),
    "update_fields": frozenset({"table", "filter", "updates", "require_existing"}),
    "update_many": frozenset({"table", "filter", "updates", "require_existing"}),
    "upsert": frozenset({"table", "columns", "conflict", "updates"}),
}
AGGREGATE_QUERY_FIELDS: dict[str, frozenset[str]] = {
    "get_aggregate_by_key": frozenset({"aggregate", "filter"}),
    "get_aggregate_by_unique": frozenset({"aggregate", "filter", "on_multiple"}),
    "list_aggregates_by": frozenset({"aggregate", "filter", "order_by"}),
    "insert_aggregate": frozenset({"aggregate"}),
    "replace_aggregate": frozenset({"aggregate"}),
}
QUERY_FIELDS = {**TABLE_QUERY_FIELDS, **AGGREGATE_QUERY_FIELDS}
# v3 only: a transaction-scoped lock over (scope, keys); no table, no filter.
LOCK_QUERY_FIELDS: dict[str, frozenset[str]] = {"lock": frozenset({"scope", "keys"})}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _scalar(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


def _shape(
    value: Any,
    expected: frozenset[str],
    *,
    location: str,
    code_prefix: str,
    repository: str | None = None,
) -> list[Finding]:
    if not isinstance(value, dict):
        return [Finding("error", f"invalid_{code_prefix}", f"{location} must be an object", repository, location)]
    findings: list[Finding] = []
    extra = sorted(set(value) - expected)
    missing = sorted(expected - set(value))
    if extra:
        findings.append(Finding(
            "error", f"unknown_{code_prefix}_field",
            f"unexpected fields: {extra}", repository, location,
        ))
    if missing:
        findings.append(Finding(
            "error", f"missing_{code_prefix}_field",
            f"required fields are absent: {missing}", repository, location,
        ))
    return findings


def _string_list(value: Any, *, location: str, allow_empty: bool = False) -> tuple[list[str], list[Finding]]:
    if not isinstance(value, list) or (not allow_empty and not value) or not all(_text(item) for item in value):
        qualifier = "a string list" if allow_empty else "a non-empty string list"
        return [], [Finding("error", "invalid_name_list", f"{location} must be {qualifier}", location=location)]
    return list(value), []


def _validate_table(row: Any, index: int) -> tuple[list[Finding], str | None, set[str]]:
    location = f"rules.persistence_backend.tables[{index}]"
    findings = _shape(row, TABLE_FIELDS, location=location, code_prefix="table")
    if not isinstance(row, dict):
        return findings, None, set()

    table = row.get("table")
    if not _text(table):
        findings.append(Finding("error", "invalid_table_id", "table must be a non-empty string", location=location + ".table"))
        table = None
    for field in ("table_name_ref", "model"):
        if not _text(row.get(field)):
            findings.append(Finding("error", f"invalid_{field}", f"{field} must be a non-empty string", location=location + f".{field}"))
    read_by = row.get("read_by")
    if read_by is not None and not _text(read_by):
        findings.append(Finding("error", "invalid_read_by", "read_by must be a module name or null", location=location + ".read_by"))

    columns = row.get("columns")
    column_names: list[str] = []
    if not isinstance(columns, list):
        findings.append(Finding("error", "invalid_columns", "columns must be a list", location=location + ".columns"))
    else:
        for column_index, column in enumerate(columns):
            column_location = f"{location}.columns[{column_index}]"
            findings.extend(_shape(column, COLUMN_FIELDS, location=column_location, code_prefix="column"))
            if not isinstance(column, dict):
                continue
            name = column.get("column")
            if not _text(name):
                findings.append(Finding("error", "invalid_column_id", "column must be a non-empty string", location=column_location + ".column"))
            else:
                column_names.append(name)
            if not _text(column.get("field")):
                findings.append(Finding("error", "invalid_column_field", "field must be a non-empty model-field name", location=column_location + ".field"))
            storage = column.get("storage")
            if storage is not None and storage not in STORAGE_REPRESENTATIONS:
                findings.append(Finding(
                    "error", "unsupported_storage_representation",
                    f"storage must be null or one of {sorted(STORAGE_REPRESENTATIONS)}",
                    location=column_location + ".storage",
                ))
            if not isinstance(column.get("nullable"), bool):
                findings.append(Finding("error", "invalid_nullable", "nullable must be boolean", location=column_location + ".nullable"))
            element_model = column.get("element_model")
            if element_model is not None and not _text(element_model):
                findings.append(Finding("error", "invalid_element_model", "element_model must be a model name or null", location=column_location + ".element_model"))

    counts = Counter(column_names)
    for name, count in sorted(counts.items()):
        if count > 1:
            findings.append(Finding("error", "duplicate_column", f"column {name!r} occurs {count} times", location=location + ".columns"))
    declared = set(column_names)

    primary_key, errors = _string_list(row.get("primary_key"), location=location + ".primary_key")
    findings.extend(errors)
    for name in primary_key:
        if name not in declared:
            findings.append(Finding("error", "unknown_primary_key_column", f"unknown column {name!r}", location=location + ".primary_key"))

    unique = row.get("unique")
    if not isinstance(unique, list):
        findings.append(Finding("error", "invalid_unique", "unique must be a list of non-empty column-name lists", location=location + ".unique"))
    else:
        for unique_index, item in enumerate(unique):
            names, errors = _string_list(item, location=f"{location}.unique[{unique_index}]")
            findings.extend(errors)
            for name in names:
                if name not in declared:
                    findings.append(Finding("error", "unknown_unique_column", f"unknown column {name!r}", location=f"{location}.unique[{unique_index}]"))

    return findings, table, declared


def _validate_aggregate(row: Any, index: int, table_names: set[str]) -> tuple[list[Finding], str | None]:
    location = f"rules.persistence_backend.aggregates[{index}]"
    findings = _shape(row, AGGREGATE_FIELDS, location=location, code_prefix="aggregate")
    if not isinstance(row, dict):
        return findings, None
    aggregate = row.get("aggregate")
    if not _text(aggregate):
        findings.append(Finding("error", "invalid_aggregate_id", "aggregate must be a non-empty string", location=location + ".aggregate"))
        aggregate = None

    root = row.get("root")
    findings.extend(_shape(root, ROOT_AGGREGATE_FIELDS, location=location + ".root", code_prefix="aggregate_root"))
    if isinstance(root, dict):
        for field in ("field", "model", "table"):
            if not _text(root.get(field)):
                findings.append(Finding("error", f"invalid_root_{field}", f"{field} must be a non-empty string", location=location + f".root.{field}"))
        table = root.get("table")
        if _text(table) and table not in table_names:
            findings.append(Finding("error", "unknown_root_table", f"unknown table {table!r}", location=location + ".root.table"))
        key = root.get("key")
        if not _scalar(key) and not (isinstance(key, list) and key and all(_scalar(item) for item in key)):
            findings.append(Finding("error", "invalid_root_key", "key must be a scalar or non-empty scalar list", location=location + ".root.key"))

    relations = row.get("relations")
    if not isinstance(relations, list):
        findings.append(Finding("error", "invalid_relations", "relations must be a list", location=location + ".relations"))
    else:
        relation_fields: list[str] = []
        for relation_index, relation in enumerate(relations):
            relation_location = f"{location}.relations[{relation_index}]"
            findings.extend(_shape(relation, RELATION_FIELDS, location=relation_location, code_prefix="relation"))
            if not isinstance(relation, dict):
                continue
            for field in ("field", "model", "table"):
                if not _text(relation.get(field)):
                    findings.append(Finding("error", f"invalid_relation_{field}", f"{field} must be a non-empty string", location=relation_location + f".{field}"))
            if _text(relation.get("field")):
                relation_fields.append(relation["field"])
            table = relation.get("table")
            if _text(table) and table not in table_names:
                findings.append(Finding("error", "unknown_relation_table", f"unknown table {table!r}", location=relation_location + ".table"))
            if relation.get("cardinality") not in {"one", "many"}:
                findings.append(Finding("error", "invalid_cardinality", "cardinality must be 'one' or 'many'", location=relation_location + ".cardinality"))
            roots = relation.get("root_columns")
            related = relation.get("related_columns")
            roots_valid = isinstance(roots, list) and bool(roots) and all(_scalar(item) for item in roots)
            related_valid = isinstance(related, list) and bool(related) and all(_scalar(item) for item in related)
            if not roots_valid:
                findings.append(Finding("error", "invalid_root_columns", "root_columns must be a non-empty scalar list", location=relation_location + ".root_columns"))
            if not related_valid:
                findings.append(Finding("error", "invalid_related_columns", "related_columns must be a non-empty scalar list", location=relation_location + ".related_columns"))
            if roots_valid and related_valid and len(roots) != len(related):
                findings.append(Finding("error", "relation_column_arity_mismatch", "root_columns and related_columns must have equal length", location=relation_location))
        counts = Counter(relation_fields)
        for field, count in sorted(counts.items()):
            if count > 1:
                findings.append(Finding("error", "duplicate_relation_field", f"aggregate relation field {field!r} occurs {count} times", location=location + ".relations"))
    return findings, aggregate


def _validate_method(
    row: Any,
    *,
    repository: str | None,
    location: str,
    table_names: set[str],
    aggregate_names: set[str],
    table_columns: dict[str, set[str]],
    version: int = 2,
) -> tuple[list[Finding], str | None]:
    if not isinstance(row, dict):
        return [Finding("error", "invalid_method", "repository method must be an object", repository, location)], None
    findings: list[Finding] = []
    method = row.get("method")
    query = row.get("query")
    if not _text(method):
        findings.append(Finding("error", "invalid_method_id", "method must be a non-empty string", repository, location + ".method"))
        method = None
    if version >= 3 and query in LOCK_QUERY_FIELDS:
        findings.extend(_shape(row, frozenset({"method", "query"}) | LOCK_QUERY_FIELDS[query], location=location, code_prefix="method", repository=repository))
        if not _text(row.get("scope")):
            findings.append(Finding("error", "invalid_lock_scope", "lock scope must be a non-empty string", repository, location + ".scope"))
        keys = row.get("keys")
        if not (isinstance(keys, list) and keys and all(_text(item) for item in keys)):
            findings.append(Finding("error", "invalid_lock_keys", "lock keys must be a non-empty list of argument names", repository, location + ".keys"))
        return findings, method
    if query not in QUERY_FIELDS:
        findings.append(Finding("error", "unsupported_query", f"unsupported persistence query: {query!r}", repository, location + ".query"))
        return findings, method

    expected = frozenset({"method", "query"}) | QUERY_FIELDS[query]
    findings.extend(_shape(row, expected, location=location, code_prefix="method", repository=repository))
    if query in TABLE_QUERY_FIELDS:
        table = row.get("table")
        if not _text(table):
            findings.append(Finding("error", "invalid_method_table", "table must be a non-empty string", repository, location + ".table"))
        elif table not in table_names:
            findings.append(Finding("error", "unknown_method_table", f"unknown table {table!r}", repository, location + ".table"))
        columns = row.get("columns")
        if query in {"insert", "insert_many", "upsert"}:
            names, errors = _string_list(columns, location=location + ".columns")
            findings.extend(Finding(item.severity, item.code, item.message, repository, item.location) for item in errors)
            if _text(table) and table in table_columns:
                for name in names:
                    if name not in table_columns[table]:
                        findings.append(Finding("error", "unknown_method_column", f"unknown column {name!r} for table {table!r}", repository, location + ".columns"))
    else:
        aggregate = row.get("aggregate")
        if not _text(aggregate):
            findings.append(Finding("error", "invalid_method_aggregate", "aggregate must be a non-empty string", repository, location + ".aggregate"))
        elif aggregate not in aggregate_names:
            findings.append(Finding("error", "unknown_method_aggregate", f"unknown aggregate {aggregate!r}", repository, location + ".aggregate"))
    return findings, method


def validate(payload: Any) -> list[Finding]:
    """Validate the closed structural surface of SPEC_STANDARD persistence_backend/v2.

    Version-specific nested forms such as filter/order_by/check are deliberately
    not interpreted here until their closed registries are explicit in the
    normative standard. The validator therefore owns shape, identity, references
    that are resolvable inside the IR, and repository ownership only.
    """
    if not isinstance(payload, dict):
        return [Finding("error", "invalid_persistence_backend", "rules.persistence_backend must be an object", location="rules.persistence_backend")]

    findings = _shape(payload, ROOT_FIELDS, location="rules.persistence_backend", code_prefix="persistence_backend")
    if payload.get("kind") != "persistence_backend":
        findings.append(Finding("error", "invalid_backend_kind", "kind must be 'persistence_backend'", location="rules.persistence_backend.kind"))
    version = payload.get("schema_version")
    if version not in SUPPORTED_SCHEMA_VERSIONS:
        findings.append(Finding(
            "error", "unsupported_persistence_schema",
            f"schema_version must be one of {sorted(SUPPORTED_SCHEMA_VERSIONS)}",
            location="rules.persistence_backend.schema_version",
        ))
        version = 2

    backend = payload.get("backend")
    findings.extend(_shape(backend, BACKEND_FIELDS, location="rules.persistence_backend.backend", code_prefix="backend"))
    if isinstance(backend, dict):
        pairs = SUPPORTED_BACKENDS[version]
        pair = (backend.get("engine"), backend.get("emitter"))
        if pair not in pairs:
            allowed = ", ".join(f"{engine}/{emitter}" for engine, emitter in pairs)
            findings.append(Finding(
                "error", "unsupported_persistence_engine",
                f"persistence_backend/v{version} accepts backend pairs {allowed}; got {pair[0]!r}/{pair[1]!r}",
                location="rules.persistence_backend.backend",
            ))

    conventions = payload.get("conventions")
    findings.extend(_shape(conventions, CONVENTION_FIELDS, location="rules.persistence_backend.conventions", code_prefix="convention"))
    if isinstance(conventions, dict):
        for key, expected in CONVENTIONS.items():
            if conventions.get(key) != expected:
                findings.append(Finding("error", "unsupported_convention", f"{key} must be {expected!r}", location=f"rules.persistence_backend.conventions.{key}"))

    tables = payload.get("tables")
    table_names: list[str] = []
    table_columns: dict[str, set[str]] = {}
    if not isinstance(tables, list):
        findings.append(Finding("error", "invalid_tables", "tables must be a list", location="rules.persistence_backend.tables"))
        tables = []
    for index, row in enumerate(tables):
        row_findings, table, columns = _validate_table(row, index)
        findings.extend(row_findings)
        if table is not None:
            table_names.append(table)
            table_columns.setdefault(table, columns)
    for table, count in sorted(Counter(table_names).items()):
        if count > 1:
            findings.append(Finding("error", "duplicate_table", f"table {table!r} occurs {count} times", location="rules.persistence_backend.tables"))
    table_name_set = set(table_names)

    aggregates = payload.get("aggregates")
    aggregate_names: list[str] = []
    if not isinstance(aggregates, list):
        findings.append(Finding("error", "invalid_aggregates", "aggregates must be a list", location="rules.persistence_backend.aggregates"))
        aggregates = []
    for index, row in enumerate(aggregates):
        row_findings, aggregate = _validate_aggregate(row, index, table_name_set)
        findings.extend(row_findings)
        if aggregate is not None:
            aggregate_names.append(aggregate)
    for aggregate, count in sorted(Counter(aggregate_names).items()):
        if count > 1:
            findings.append(Finding("error", "duplicate_aggregate", f"aggregate {aggregate!r} occurs {count} times", location="rules.persistence_backend.aggregates"))
    aggregate_name_set = set(aggregate_names)

    repositories = payload.get("repositories")
    repository_names: list[str] = []
    modules: list[str] = []
    method_names: list[str] = []
    if not isinstance(repositories, list):
        findings.append(Finding("error", "invalid_repositories", "repositories must be a list", location="rules.persistence_backend.repositories"))
        repositories = []
    for index, row in enumerate(repositories):
        location = f"rules.persistence_backend.repositories[{index}]"
        if not isinstance(row, dict):
            findings.append(Finding("error", "invalid_repository", "repository must be an object", location=location))
            continue
        repository = row.get("repository") if _text(row.get("repository")) else None
        emission = row.get("emission")
        expected = TABLE_REPOSITORY_FIELDS if emission == "table" else IRREGULAR_REPOSITORY_FIELDS if emission == "irregular" else None
        if expected is not None and version >= 3:
            expected = expected | {"transaction"}
        if expected is None:
            findings.append(Finding("error", "invalid_repository_emission", "emission must be 'table' or 'irregular'", repository, location + ".emission"))
        else:
            findings.extend(_shape(row, expected, location=location, code_prefix="repository", repository=repository))
        if version >= 3 and row.get("transaction") not in TRANSACTION_MODES:
            findings.append(Finding("error", "invalid_repository_transaction", f"transaction must be one of {sorted(TRANSACTION_MODES)}", repository, location + ".transaction"))
        for field in ("repository", "module", "schema_function"):
            if not _text(row.get(field)):
                findings.append(Finding("error", f"invalid_repository_{field}", f"{field} must be a non-empty string", repository, location + f".{field}"))
        if repository is not None:
            repository_names.append(repository)
        if _text(row.get("module")):
            modules.append(row["module"])

        if emission == "irregular":
            if not _text(row.get("irregular_reason")):
                findings.append(Finding("error", "missing_irregular_reason", "irregular repository requires a non-empty irregular_reason", repository, location + ".irregular_reason"))
            continue
        if emission != "table":
            continue
        methods = row.get("methods")
        if not isinstance(methods, list):
            findings.append(Finding("error", "invalid_methods", "table repository methods must be a list", repository, location + ".methods"))
            continue
        for method_index, method_row in enumerate(methods):
            method_findings, method = _validate_method(
                method_row,
                repository=repository,
                location=f"{location}.methods[{method_index}]",
                table_names=table_name_set,
                aggregate_names=aggregate_name_set,
                table_columns=table_columns,
                version=version,
            )
            findings.extend(method_findings)
            if method is not None:
                method_names.append(method)

    for name, count in sorted(Counter(repository_names).items()):
        if count > 1:
            findings.append(Finding("error", "duplicate_repository", f"repository {name!r} occurs {count} times", location="rules.persistence_backend.repositories"))
    for module, count in sorted(Counter(modules).items()):
        if count > 1:
            findings.append(Finding("error", "duplicate_repository_module", f"persistence module {module!r} owns {count} repositories; v2 requires exactly one repository class per module", location="rules.persistence_backend.repositories"))
    for method, count in sorted(Counter(method_names).items()):
        if count > 1:
            findings.append(Finding("error", "duplicate_repository_method", f"repository method {method!r} occurs {count} times", location="rules.persistence_backend.repositories"))

    return findings
