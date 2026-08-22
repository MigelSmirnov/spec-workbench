from __future__ import annotations

from typing import Any

from persistence_workbench.model import Finding


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _lookup(root: Any, dotted: str) -> tuple[bool, Any]:
    current = root
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]
    return True, current


def _model_fields(models: dict[str, Any], name: Any) -> dict[str, Any] | None:
    if not _text(name):
        return None
    row = models.get(name)
    if not isinstance(row, dict) or row.get("kind") is not None:
        return None
    fields = row.get("fields")
    return fields if isinstance(fields, dict) else None


def _declared_type(fields: dict[str, Any], field: str) -> str | None:
    value = fields.get(field)
    if not isinstance(value, str):
        return None
    return value.split("=", 1)[0].strip()


def _repository_modules(payload: dict[str, Any]) -> set[str]:
    repositories = payload.get("repositories")
    if not isinstance(repositories, list):
        return set()
    return {
        row["module"]
        for row in repositories
        if isinstance(row, dict) and _text(row.get("module"))
    }


def validate_projection(spec: dict[str, Any], payload: dict[str, Any]) -> list[Finding]:
    """Resolve v2 table/aggregate projection cells against assembled spec data.

    This validator deliberately does not interpret the still separately closed
    query/filter/check DSL. It owns references whose target is unambiguous from
    the normative top-level spec: config addresses, runtime models, model fields,
    module names, table/model correspondence, and aggregate field coverage.
    """
    findings: list[Finding] = []
    models = spec.get("models")
    config = spec.get("config")
    module_functions = spec.get("module_functions")
    if not isinstance(models, dict):
        return [Finding("error", "invalid_models_container", "models must be an object", location="models")]
    if not isinstance(config, dict):
        return [Finding("error", "invalid_config_container", "config must be an object", location="config")]
    if not isinstance(module_functions, dict):
        return [Finding("error", "invalid_module_functions_container", "module_functions must be an object", location="module_functions")]

    tables = payload.get("tables") if isinstance(payload.get("tables"), list) else []
    table_by_name: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(tables):
        if not isinstance(row, dict):
            continue
        location = f"rules.persistence_backend.tables[{index}]"
        table = row.get("table")
        if _text(table):
            table_by_name[table] = row
        model = row.get("model")
        fields = _model_fields(models, model)
        if fields is None:
            findings.append(Finding(
                "error", "unknown_table_model",
                f"table model {model!r} must resolve to a runtime model with fields",
                location=location + ".model",
            ))
            fields = {}

        table_name_ref = row.get("table_name_ref")
        if _text(table_name_ref):
            # The Factory gate (tools/persistence_ir.py) reads table_name_ref as an
            # identifier under config.persistence; a full config.* address is also
            # accepted so older authoring stays valid. Both must resolve.
            address = (
                table_name_ref if table_name_ref.startswith("config.")
                else f"config.persistence.{table_name_ref}"
            )
            if "." in table_name_ref and not table_name_ref.startswith("config."):
                findings.append(Finding(
                    "error", "invalid_table_name_ref_namespace",
                    "table_name_ref must be a config.persistence identifier or a config.* address",
                    location=location + ".table_name_ref",
                ))
            else:
                exists, value = _lookup(spec, address)
                if not exists:
                    findings.append(Finding(
                        "error", "unresolved_table_name_ref",
                        f"table_name_ref does not resolve: {table_name_ref}",
                        location=location + ".table_name_ref",
                    ))
                elif not _text(value):
                    findings.append(Finding(
                        "error", "invalid_table_name_value",
                        f"{table_name_ref} must resolve to a non-empty table-name string",
                        location=location + ".table_name_ref",
                    ))

        read_by = row.get("read_by")
        if _text(read_by) and read_by not in module_functions:
            findings.append(Finding(
                "error", "unknown_table_reader_module",
                f"read_by module {read_by!r} is absent from module_functions",
                location=location + ".read_by",
            ))

        columns = row.get("columns") if isinstance(row.get("columns"), list) else []
        for column_index, column in enumerate(columns):
            if not isinstance(column, dict):
                continue
            column_location = f"{location}.columns[{column_index}]"
            field = column.get("field")
            if _text(field) and field not in fields:
                findings.append(Finding(
                    "error", "unknown_model_field",
                    f"field {field!r} is absent from model {model!r}",
                    location=column_location + ".field",
                ))
            element_model = column.get("element_model")
            if _text(element_model) and _model_fields(models, element_model) is None:
                findings.append(Finding(
                    "error", "unknown_element_model",
                    f"element_model {element_model!r} must resolve to a runtime model with fields",
                    location=column_location + ".element_model",
                ))

    aggregates = payload.get("aggregates") if isinstance(payload.get("aggregates"), list) else []
    for index, row in enumerate(aggregates):
        if not isinstance(row, dict):
            continue
        location = f"rules.persistence_backend.aggregates[{index}]"
        aggregate_name = row.get("aggregate")
        aggregate_fields = _model_fields(models, aggregate_name)
        if aggregate_fields is None:
            findings.append(Finding(
                "error", "unknown_aggregate_model",
                f"aggregate {aggregate_name!r} must resolve to a runtime model with fields",
                location=location + ".aggregate",
            ))
            aggregate_fields = {}

        covered: list[str] = []
        root = row.get("root")
        if isinstance(root, dict):
            root_field = root.get("field")
            root_model = root.get("model")
            root_table = root.get("table")
            if _text(root_field):
                covered.append(root_field)
                if root_field not in aggregate_fields:
                    findings.append(Finding(
                        "error", "unknown_aggregate_root_field",
                        f"root field {root_field!r} is absent from aggregate model {aggregate_name!r}",
                        location=location + ".root.field",
                    ))
                else:
                    declared = _declared_type(aggregate_fields, root_field)
                    if declared is not None and declared != root_model:
                        findings.append(Finding(
                            "error", "aggregate_root_type_mismatch",
                            f"aggregate field {root_field!r} has type {declared!r}, expected {root_model!r}",
                            location=location + ".root",
                        ))
            if _model_fields(models, root_model) is None:
                findings.append(Finding(
                    "error", "unknown_aggregate_root_model",
                    f"root model {root_model!r} must resolve to a runtime model with fields",
                    location=location + ".root.model",
                ))
            table_row = table_by_name.get(root_table) if _text(root_table) else None
            if table_row is not None and table_row.get("model") != root_model:
                findings.append(Finding(
                    "error", "aggregate_root_table_model_mismatch",
                    f"table {root_table!r} projects model {table_row.get('model')!r}, not {root_model!r}",
                    location=location + ".root.table",
                ))

        relations = row.get("relations") if isinstance(row.get("relations"), list) else []
        for relation_index, relation in enumerate(relations):
            if not isinstance(relation, dict):
                continue
            relation_location = f"{location}.relations[{relation_index}]"
            field = relation.get("field")
            model = relation.get("model")
            table = relation.get("table")
            cardinality = relation.get("cardinality")
            if _text(field):
                covered.append(field)
                if field not in aggregate_fields:
                    findings.append(Finding(
                        "error", "unknown_aggregate_relation_field",
                        f"relation field {field!r} is absent from aggregate model {aggregate_name!r}",
                        location=relation_location + ".field",
                    ))
                else:
                    declared = _declared_type(aggregate_fields, field)
                    expected = model if cardinality == "one" else f"list[{model}]" if cardinality == "many" else None
                    if declared is not None and expected is not None and declared != expected:
                        findings.append(Finding(
                            "error", "aggregate_relation_type_mismatch",
                            f"aggregate field {field!r} has type {declared!r}, expected {expected!r}",
                            location=relation_location,
                        ))
            if _model_fields(models, model) is None:
                findings.append(Finding(
                    "error", "unknown_aggregate_relation_model",
                    f"relation model {model!r} must resolve to a runtime model with fields",
                    location=relation_location + ".model",
                ))
            table_row = table_by_name.get(table) if _text(table) else None
            if table_row is not None and table_row.get("model") != model:
                findings.append(Finding(
                    "error", "aggregate_relation_table_model_mismatch",
                    f"table {table!r} projects model {table_row.get('model')!r}, not {model!r}",
                    location=relation_location + ".table",
                ))

        if aggregate_fields:
            missing = sorted(set(aggregate_fields) - set(covered))
            duplicate = sorted({field for field in covered if covered.count(field) > 1})
            if missing:
                findings.append(Finding(
                    "error", "aggregate_fields_not_covered",
                    f"aggregate fields are not covered by root/relations: {missing}",
                    location=location,
                ))
            if duplicate:
                findings.append(Finding(
                    "error", "aggregate_fields_multiply_covered",
                    f"aggregate fields are covered more than once: {duplicate}",
                    location=location,
                ))

    repository_modules = _repository_modules(payload)
    for module in sorted(repository_modules - set(module_functions)):
        findings.append(Finding(
            "error", "unknown_repository_module",
            f"repository module {module!r} is absent from module_functions",
            location="rules.persistence_backend.repositories",
        ))

    return findings
