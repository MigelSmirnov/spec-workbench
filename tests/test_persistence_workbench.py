from __future__ import annotations

import json
from pathlib import Path

from persistence_workbench import coverage, validate


def _backend() -> dict:
    return {
        "kind": "persistence_backend",
        "schema_version": 2,
        "backend": {"engine": "sqlite", "emitter": "sqlite_sync_v2"},
        "conventions": {
            "assert_open": "inside_try",
            "guard_reraise": "unchanged",
            "codec_naming": "row_to_snake_model",
            "primary_key_not_null": "always",
        },
        "tables": [],
        "aggregates": [],
        "repositories": [],
    }


def _table_backend() -> dict:
    payload = _backend()
    payload["tables"] = [{
        "table": "invoices",
        "table_name_ref": "config.storage.invoice_table",
        "model": "Invoice",
        "read_by": "invoice_repository",
        "columns": [{
            "column": "invoice_id",
            "field": "invoice_id",
            "storage": "text",
            "nullable": False,
            "check": None,
            "element_model": None,
        }],
        "primary_key": ["invoice_id"],
        "unique": [],
    }]
    payload["repositories"] = [{
        "repository": "InvoiceRepository",
        "module": "invoice_repository",
        "schema_function": "create_invoice_schema",
        "emission": "table",
        "methods": [{
            "method": "get_invoice",
            "query": "get_by_key",
            "table": "invoices",
            "filter": {"invoice_id": "opaque-until-closed-registry-is-specified"},
            "select": ["invoice_id"],
        }],
    }]
    return payload


def _write_project(
    tmp_path: Path,
    *,
    persistence_backend: dict | None,
    rules: object | None = None,
    contracts: dict | None = None,
    module_functions: dict | None = None,
    config: dict | None = None,
    models: dict | None = None,
    write_closure: bool = True,
) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    if rules is None:
        rules_payload: object = {}
        if persistence_backend is not None:
            rules_payload = {"persistence_backend": persistence_backend}
    else:
        rules_payload = rules
    payload = {
        "standard_version": 2,
        "rules": rules_payload,
        "config": config or {"role": "data", "schema_version": 1},
        "models": models or {"role": "data", "schema_version": 1},
        "contracts": contracts or {},
        "module_functions": module_functions or {},
    }
    (project / "global_spec.json").write_text(json.dumps(payload), encoding="utf-8")
    if persistence_backend is not None and write_closure:
        (project / "70_persistence_closure.json").write_text(
            json.dumps({
                "schema_version": "spec_workbench_persistence_closure.v1",
                "status": "closed",
                "backend_ir": persistence_backend,
            }),
            encoding="utf-8",
        )
    return project


def _invoice_projection() -> dict:
    return {
        "config": {
            "role": "data",
            "schema_version": 1,
            "storage": {"invoice_table": "invoices"},
        },
        "models": {
            "role": "data",
            "schema_version": 1,
            "Invoice": {
                "identity": "entity",
                "fields": {"invoice_id": "str"},
            },
        },
    }


def test_absent_backend_keeps_llm_path_ready(tmp_path: Path) -> None:
    report = coverage(_write_project(tmp_path, persistence_backend=None))
    assert report["enabled"] is False
    assert report["ready"] is True
    assert report["summary"]["handoff_ready"] is True
    assert report["findings"] == []


def test_empty_v2_backend_is_structurally_valid(tmp_path: Path) -> None:
    report = coverage(_write_project(tmp_path, persistence_backend=_backend()))
    assert report["enabled"] is True
    assert report["ready"] is True
    assert report["summary"] == {
        "tables": 0,
        "aggregates": 0,
        "repositories": 0,
        "deterministic_repositories": 0,
        "irregular_repositories": 0,
        "errors": 0,
        "handoff_ready": True,
    }


def test_assembled_backend_without_authoring_closure_is_blocked(tmp_path: Path) -> None:
    report = coverage(_write_project(
        tmp_path,
        persistence_backend=_backend(),
        write_closure=False,
    ))
    assert report["ready"] is False
    assert any(
        item["code"] == "untracked_assembled_persistence_backend"
        for item in report["findings"]
    )


def test_closed_closure_must_match_assembled_backend_exactly(tmp_path: Path) -> None:
    project = _write_project(tmp_path, persistence_backend=_backend())
    closure = json.loads((project / "70_persistence_closure.json").read_text(encoding="utf-8"))
    closure["backend_ir"]["conventions"]["guard_reraise"] = "changed"
    (project / "70_persistence_closure.json").write_text(json.dumps(closure), encoding="utf-8")
    report = coverage(project)
    assert report["ready"] is False
    assert any(
        item["code"] == "persistence_backend_handoff_mismatch"
        for item in report["findings"]
    )


def test_closed_closure_without_assembled_backend_is_blocked(tmp_path: Path) -> None:
    project = _write_project(tmp_path, persistence_backend=None)
    (project / "70_persistence_closure.json").write_text(
        json.dumps({
            "schema_version": "spec_workbench_persistence_closure.v1",
            "status": "closed",
            "backend_ir": _backend(),
        }),
        encoding="utf-8",
    )
    report = coverage(project)
    assert report["ready"] is False
    assert any(
        item["code"] == "missing_assembled_persistence_backend"
        for item in report["findings"]
    )


def test_backend_root_is_closed() -> None:
    payload = _backend()
    payload["steps"] = []
    findings = validate(payload)
    assert any(item.code == "unknown_persistence_backend_field" for item in findings)


def test_table_identity_and_columns_are_resolved() -> None:
    payload = _backend()
    payload["tables"] = [{
        "table": "invoices",
        "table_name_ref": "config.storage.invoice_table",
        "model": "Invoice",
        "read_by": "invoice_repository",
        "columns": [{
            "column": "invoice_id",
            "field": "invoice_id",
            "storage": "text",
            "nullable": False,
            "check": None,
            "element_model": None,
        }],
        "primary_key": ["missing_column"],
        "unique": [["invoice_id"]],
    }]
    findings = validate(payload)
    assert any(item.code == "unknown_primary_key_column" for item in findings)
    assert not any(item.code == "unknown_unique_column" for item in findings)


def test_valid_table_repository_and_method() -> None:
    findings = validate(_table_backend())
    assert findings == []


def test_repository_module_cannot_be_split() -> None:
    payload = _backend()
    payload["repositories"] = [
        {
            "repository": "FirstRepository",
            "module": "storage",
            "schema_function": "create_first_schema",
            "emission": "irregular",
            "irregular_reason": "requires unsupported guarded mutation",
        },
        {
            "repository": "SecondRepository",
            "module": "storage",
            "schema_function": "create_second_schema",
            "emission": "irregular",
            "irregular_reason": "requires unsupported guarded mutation",
        },
    ]
    findings = validate(payload)
    assert any(item.code == "duplicate_repository_module" for item in findings)


def test_method_query_registry_is_closed() -> None:
    payload = _backend()
    payload["repositories"] = [{
        "repository": "InvoiceRepository",
        "module": "invoice_repository",
        "schema_function": "create_invoice_schema",
        "emission": "table",
        "methods": [{"method": "run_sql", "query": "sql", "sql": "DELETE FROM invoices"}],
    }]
    findings = validate(payload)
    assert any(item.code == "unsupported_query" for item in findings)


def test_aggregate_relation_shape_is_closed() -> None:
    payload = _backend()
    payload["tables"] = [
        {
            "table": "parents",
            "table_name_ref": "config.storage.parents_table",
            "model": "Parent",
            "read_by": "aggregate_repository",
            "columns": [{
                "column": "parent_id", "field": "parent_id", "storage": "text",
                "nullable": False, "check": None, "element_model": None,
            }],
            "primary_key": ["parent_id"],
            "unique": [],
        },
        {
            "table": "children",
            "table_name_ref": "config.storage.children_table",
            "model": "Child",
            "read_by": "aggregate_repository",
            "columns": [{
                "column": "parent_id", "field": "parent_id", "storage": "text",
                "nullable": False, "check": None, "element_model": None,
            }],
            "primary_key": ["parent_id"],
            "unique": [],
        },
    ]
    payload["aggregates"] = [{
        "aggregate": "ParentAggregate",
        "root": {"field": "parent", "model": "Parent", "table": "parents", "key": "parent_id"},
        "relations": [{
            "field": "children",
            "model": "Child",
            "table": "children",
            "cardinality": "many",
            "root_columns": ["parent_id"],
            "related_columns": ["parent_id", "extra"],
            "order_by": [],
        }],
    }]
    findings = validate(payload)
    assert any(item.code == "relation_column_arity_mismatch" for item in findings)


def test_coverage_binds_table_repository_to_canonical_contracts(tmp_path: Path) -> None:
    projection = _invoice_projection()
    project = _write_project(
        tmp_path,
        persistence_backend=_table_backend(),
        contracts={
            "create_invoice_schema": "() -> None",
            "InvoiceRepository.get_invoice": "(self, invoice_id: str) -> Invoice | None",
        },
        module_functions={
            "invoice_repository": ["InvoiceRepository", "create_invoice_schema"],
        },
        **projection,
    )
    report = coverage(project)
    assert report["ready"] is True
    assert report["deterministic_modules"] == ["invoice_repository"]
    assert report["summary"]["errors"] == 0


def test_unresolved_table_projection_blocks_coverage(tmp_path: Path) -> None:
    projection = _invoice_projection()
    projection["models"]["Invoice"]["fields"] = {"other_id": "str"}
    project = _write_project(
        tmp_path,
        persistence_backend=_table_backend(),
        contracts={
            "create_invoice_schema": "() -> None",
            "InvoiceRepository.get_invoice": "(self, invoice_id: str) -> Invoice | None",
        },
        module_functions={
            "invoice_repository": ["InvoiceRepository", "create_invoice_schema"],
        },
        **projection,
    )
    report = coverage(project)
    assert report["ready"] is False
    assert any(item["code"] == "unknown_model_field" for item in report["findings"])


def test_missing_repository_method_contract_blocks_coverage(tmp_path: Path) -> None:
    projection = _invoice_projection()
    project = _write_project(
        tmp_path,
        persistence_backend=_table_backend(),
        contracts={"create_invoice_schema": "() -> None"},
        module_functions={
            "invoice_repository": ["InvoiceRepository", "create_invoice_schema"],
        },
        **projection,
    )
    report = coverage(project)
    assert report["ready"] is False
    assert any(item["code"] == "missing_repository_method_contract" for item in report["findings"])


def test_transaction_methods_are_not_deterministic_backend_owned(tmp_path: Path) -> None:
    payload = _table_backend()
    payload["repositories"][0]["methods"][0]["method"] = "commit"
    projection = _invoice_projection()
    project = _write_project(
        tmp_path,
        persistence_backend=payload,
        contracts={
            "create_invoice_schema": "() -> None",
            "InvoiceRepository.commit": "(self) -> None",
        },
        module_functions={
            "invoice_repository": ["InvoiceRepository", "create_invoice_schema"],
        },
        **projection,
    )
    report = coverage(project)
    assert report["ready"] is False
    assert any(item["code"] == "backend_owns_transaction_method" for item in report["findings"])


# --- persistence_backend/v3 (SPEC_STANDARD §6.3) ---------------------------


def _v3_backend() -> dict:
    payload = _table_backend()
    payload["schema_version"] = 3
    payload["backend"] = {"engine": "postgres", "emitter": "postgres_sync_v1"}
    payload["repositories"][0]["transaction"] = "owned"
    payload["repositories"][0]["methods"].append(
        {"method": "lock_invoice", "query": "lock", "scope": "invoice", "keys": ["invoice_id"]},
    )
    return payload


def test_v3_postgres_owned_transaction_with_lock_is_valid() -> None:
    assert validate(_v3_backend()) == []


def test_v3_keeps_sqlite_pair() -> None:
    payload = _v3_backend()
    payload["backend"] = {"engine": "sqlite", "emitter": "sqlite_sync_v2"}
    assert validate(payload) == []


def test_v2_rejects_postgres_pair_transaction_cell_and_lock() -> None:
    payload = _v3_backend()
    payload["schema_version"] = 2
    codes = {item.code for item in validate(payload)}
    assert "unsupported_persistence_engine" in codes
    assert "unsupported_query" in codes
    assert "unknown_repository_field" in codes


def test_v3_requires_transaction_cell() -> None:
    payload = _v3_backend()
    del payload["repositories"][0]["transaction"]
    assert any(item.code == "invalid_repository_transaction" for item in validate(payload))


def test_v3_lock_has_no_table_and_needs_scope_and_keys() -> None:
    payload = _v3_backend()
    lock = payload["repositories"][0]["methods"][1]
    lock["table"] = "invoices"
    lock["keys"] = [""]
    codes = {item.code for item in validate(payload)}
    assert "invalid_lock_keys" in codes
    assert any("method" in code for code in codes - {"invalid_lock_keys"})


def test_v3_nested_storage_forms_are_version_keyed() -> None:
    payload = _v3_backend()
    payload["tables"][0]["columns"].append({
        "column": "actor", "field": "actor", "storage": "json_model",
        "nullable": False, "check": None, "element_model": "ActorReference",
    })
    assert validate(payload) == []
    payload["schema_version"] = 2
    payload["backend"] = {"engine": "sqlite", "emitter": "sqlite_sync_v2"}
    del payload["repositories"][0]["transaction"]
    payload["repositories"][0]["methods"].pop()
    assert any(item.code == "invalid_column_storage" or "storage" in item.message for item in validate(payload))


def test_v3_unique_paths_and_extra_kinds_are_version_keyed() -> None:
    payload = _v3_backend()
    payload["tables"][0]["columns"].append({
        "column": "card_revision", "field": "card_revision", "storage": "json_model",
        "nullable": False, "check": None, "element_model": "InvoiceCardRevisionReference",
    })
    payload["tables"][0]["unique"] = [[{"column": "card_revision", "path": ["invoice_id"]}, "invoice_id"]]
    payload["repositories"][0]["methods"] += [
        {"method": "all_invoices", "query": "list_all", "table": "invoices", "select": ["invoice_id"],
         "order_by": [{"column": "invoice_id", "direction": "asc"}]},
        {"method": "upsert_invoices", "query": "upsert_many", "table": "invoices",
         "columns": ["invoice_id", "card_revision"], "conflict": ["invoice_id"], "updates": ["card_revision"]},
    ]
    assert validate(payload) == []
    payload["schema_version"] = 2
    payload["backend"] = {"engine": "sqlite", "emitter": "sqlite_sync_v2"}
    codes = {item.code for item in validate(payload)}
    assert "unsupported_query" in codes
