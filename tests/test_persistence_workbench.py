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
        "contracts": contracts or {},
        "module_functions": module_functions or {},
    }
    (project / "global_spec.json").write_text(json.dumps(payload), encoding="utf-8")
    return project


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
    )
    report = coverage(project)
    assert report["ready"] is True
    assert report["deterministic_modules"] == ["invoice_repository"]
    assert report["summary"]["errors"] == 0


def test_missing_repository_method_contract_blocks_coverage(tmp_path: Path) -> None:
    project = _write_project(
        tmp_path,
        persistence_backend=_table_backend(),
        contracts={"create_invoice_schema": "() -> None"},
        module_functions={
            "invoice_repository": ["InvoiceRepository", "create_invoice_schema"],
        },
    )
    report = coverage(project)
    assert report["ready"] is False
    assert any(item["code"] == "missing_repository_method_contract" for item in report["findings"])


def test_transaction_methods_are_not_deterministic_backend_owned(tmp_path: Path) -> None:
    payload = _table_backend()
    payload["repositories"][0]["methods"][0]["method"] = "commit"
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
    )
    report = coverage(project)
    assert report["ready"] is False
    assert any(item["code"] == "backend_owns_transaction_method" for item in report["findings"])
