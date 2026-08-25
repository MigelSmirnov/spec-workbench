from __future__ import annotations

from router_workbench.model import CATALOG_SCHEMA
from router_workbench.validator import validate


def _irregular(handler: str) -> dict:
    return {
        "schema_version": CATALOG_SCHEMA,
        "irregular_ownership": {"module": "api_irregular"},
        "items": [{
            "operation": "public_op:archive.get_archived_invoice",
            "handler": handler,
            "method": "GET",
            "path": "/invoices/{invoice_id}",
            "auth": "required",
            "success_status": 200,
            "response_mode": "model",
            "emission": "irregular",
            "irregular_reason": "requires transport behavior outside table lowering",
        }],
    }


def test_irregular_free_handler_can_use_companion_ownership() -> None:
    findings = validate(_irregular("get_archived_invoice_handler"))
    assert not any(item.code == "irregular_member_handler" for item in findings)


def test_irregular_class_member_cannot_use_companion_ownership() -> None:
    findings = validate(_irregular("ArchiveController.get_archived_invoice"))
    assert any(item.code == "irregular_member_handler" for item in findings)
