from __future__ import annotations

import json

from persistence_workbench import authoring
from persistence_workbench import contract_validation


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
        "tables": [{
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
        }],
        "aggregates": [],
        "repositories": [{
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
        }],
    }


def _state6_handoff() -> dict:
    return {
        "ready": True,
        "contracts": {
            "create_invoice_schema": {
                "module": "module:invoice_repository",
                "visibility": "internal",
                "signature": "() -> None",
            },
            "InvoiceRepository.get_invoice": {
                "module": "module:invoice_repository",
                "visibility": "internal",
                "signature": "(self, invoice_id: str) -> Invoice | None",
            },
        },
    }


def _write_closure(tmp_path, status: str) -> None:
    (tmp_path / "70_persistence_closure.json").write_text(
        json.dumps({
            "schema_version": "spec_workbench_persistence_closure.v1",
            "status": status,
            "backend_ir": _backend(),
        }),
        encoding="utf-8",
    )


def test_absent_closure_selects_ordinary_generation_path(tmp_path) -> None:
    report = authoring.coverage(tmp_path)
    assert report["enabled"] is False
    assert report["ready"] is True
    assert report["summary"]["handoff_ready"] is True
    assert report["deterministic_method_scopes"] == []


def test_open_valid_closure_is_not_handoff_ready(tmp_path, monkeypatch) -> None:
    _write_closure(tmp_path, "open")
    monkeypatch.setattr(contract_validation.design_stage6_contracts, "handoff", lambda project: _state6_handoff())
    report = authoring.coverage(tmp_path)
    assert report["enabled"] is True
    assert report["summary"]["errors"] == 0
    assert report["summary"]["closed"] is False
    assert report["summary"]["handoff_ready"] is False
    assert report["deterministic_method_scopes"] == ["InvoiceRepository.get_invoice"]


def test_closed_contract_bound_closure_emits_exact_backend_ir(tmp_path, monkeypatch) -> None:
    _write_closure(tmp_path, "closed")
    monkeypatch.setattr(contract_validation.design_stage6_contracts, "handoff", lambda project: _state6_handoff())
    report = authoring.handoff(tmp_path)
    assert report["enabled"] is True
    assert report["ready"] is True
    assert report["summary"]["handoff_ready"] is True
    assert report["backend_ir"] == _backend()
    assert report["deterministic_method_scopes"] == ["InvoiceRepository.get_invoice"]


def test_closure_blocks_when_state6_is_not_ready(tmp_path, monkeypatch) -> None:
    _write_closure(tmp_path, "closed")
    monkeypatch.setattr(contract_validation.design_stage6_contracts, "handoff", lambda project: {"ready": False})
    report = authoring.coverage(tmp_path)
    assert report["ready"] is False
    assert any(item["code"] == "state6_contracts_not_ready" for item in report["findings"])


def test_closure_blocks_repository_method_owned_by_other_state6_module(tmp_path, monkeypatch) -> None:
    _write_closure(tmp_path, "closed")
    handoff = _state6_handoff()
    handoff["contracts"]["InvoiceRepository.get_invoice"]["module"] = "module:other_repository"
    monkeypatch.setattr(contract_validation.design_stage6_contracts, "handoff", lambda project: handoff)
    report = authoring.coverage(tmp_path)
    assert report["ready"] is False
    assert any(item["code"] == "repository_state6_owner_mismatch" for item in report["findings"])
