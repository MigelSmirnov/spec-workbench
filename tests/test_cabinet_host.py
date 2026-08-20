from __future__ import annotations

import pytest

from cabinet_host import CabinetHost, CabinetHostError, Grant, build_demo_db


DEFINITION = {
    "cabinet": {"id": "cabinet.local.archive", "schema_version": 0},
    "schemas": {
        "InvoiceSummaryRequest": {"fields": {"project_id": {"type": "WorkObjectId"}}},
        "InvoiceSummary": {"fields": {"confirmed_total": {"type": "Decimal"}}},
    },
    "capabilities": {
        "invoice.summary": {
            "input": "InvoiceSummaryRequest",
            "output": "InvoiceSummary",
            "effects": [],
        }
    },
}


def grant(*, projects: set[str] | None = None, capabilities: set[str] | None = None) -> Grant:
    return Grant(
        principal_id="agent:test",
        principal_status="active",
        capabilities=frozenset(capabilities or {"invoice.summary"}),
        project_ids=frozenset(projects or {"project-1"}),
    )


def test_manifest_only_exposes_granted_capabilities() -> None:
    host = CabinetHost(DEFINITION, build_demo_db())
    manifest = host.manifest_for(grant())
    assert set(manifest["capabilities"]) == {"invoice.summary"}


def test_invoice_summary_executes_inside_cabinet_and_returns_no_raw_rows() -> None:
    host = CabinetHost(DEFINITION, build_demo_db())
    result = host.execute(
        grant(),
        {"invoke": {"capability": "invoice.summary", "args": {"project_id": "project-1"}}},
    )

    assert result["invoice_count"] == 2
    assert result["confirmed_total"] == "200.0"
    assert result["currency"] == "EUR"
    assert "raw_source_path" not in result
    assert "evidence" in result
    assert len(host.audit_log) == 1


def test_unconfirmed_invoice_does_not_contribute() -> None:
    host = CabinetHost(DEFINITION, build_demo_db())
    result = host.execute(
        grant(),
        {
            "invoke": {
                "capability": "invoice.summary",
                "args": {
                    "project_id": "project-1",
                    "date_from": "2026-07-15",
                    "date_to": "2026-07-31",
                },
            }
        },
    )
    assert result["invoice_count"] == 0
    assert result["confirmed_total"] == "0"


def test_resource_scope_expansion_fails_closed() -> None:
    host = CabinetHost(DEFINITION, build_demo_db())
    with pytest.raises(CabinetHostError, match="resource_scope_expansion"):
        host.execute(
            grant(projects={"project-1"}),
            {"invoke": {"capability": "invoice.summary", "args": {"project_id": "project-2"}}},
        )


def test_unknown_capability_fails_closed() -> None:
    host = CabinetHost(DEFINITION, build_demo_db())
    with pytest.raises(CabinetHostError, match="unknown_capability"):
        host.execute(
            grant(),
            {"invoke": {"capability": "invoice.raw_sql", "args": {"project_id": "project-1"}}},
        )


def test_revoked_principal_cannot_discover_manifest() -> None:
    host = CabinetHost(DEFINITION, build_demo_db())
    revoked = Grant(
        principal_id="agent:test",
        principal_status="revoked",
        capabilities=frozenset({"invoice.summary"}),
        project_ids=frozenset({"project-1"}),
    )
    with pytest.raises(CabinetHostError, match="inactive_or_revoked_principal"):
        host.manifest_for(revoked)
