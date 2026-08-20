from __future__ import annotations

import pytest

from cabinet_graph_host import CabinetGraphHost, InvoiceRefSet
from cabinet_host import CabinetHostError, Grant, build_demo_db


DEFINITION = {
    "cabinet": {"id": "cabinet.local.archive"},
    "schemas": {"InvoiceRefSet": {"opaque": True}},
    "capabilities": {
        "invoice.select": {"effects": []},
        "invoice.filter_confirmed": {"effects": []},
        "invoice.filter_date": {"effects": []},
        "invoice.aggregate_total": {"effects": []},
    },
}


def grant(*caps: str, projects=("project-1",)) -> Grant:
    return Grant(
        principal_id="agent:test",
        principal_status="active",
        capabilities=frozenset(caps),
        project_ids=frozenset(projects),
    )


def graph():
    return {
        "nodes": [
            {"id": "selected", "capability": "invoice.select", "args": {"project_id": "project-1"}},
            {"id": "confirmed", "capability": "invoice.filter_confirmed", "args": {"source": {"from": "selected"}}},
            {
                "id": "dated",
                "capability": "invoice.filter_date",
                "args": {
                    "source": {"from": "confirmed"},
                    "date_from": "2026-07-01",
                    "date_to": "2026-07-31",
                },
            },
            {"id": "result", "capability": "invoice.aggregate_total", "args": {"source": {"from": "dated"}}},
        ],
        "output": {"from": "result"},
    }


def test_graph_composes_atomic_capabilities_without_raw_rows():
    host = CabinetGraphHost(DEFINITION, build_demo_db())
    result = host.execute_graph(
        grant(
            "invoice.select",
            "invoice.filter_confirmed",
            "invoice.filter_date",
            "invoice.aggregate_total",
        ),
        graph(),
    )

    assert result["project_id"] == "project-1"
    assert result["invoice_count"] == 2
    assert result["confirmed_total"] == "200.0"
    assert result["currency"] == "EUR"
    assert "raw_source_path" not in result
    assert len(result["evidence"]["trace"]) == 4


def test_graph_denies_capability_not_in_grant():
    host = CabinetGraphHost(DEFINITION, build_demo_db())
    with pytest.raises(CabinetHostError, match="capability_not_granted"):
        host.execute_graph(grant("invoice.select"), graph())


def test_graph_denies_resource_scope_expansion():
    host = CabinetGraphHost(DEFINITION, build_demo_db())
    bad = graph()
    bad["nodes"][0]["args"]["project_id"] = "project-2"
    with pytest.raises(CabinetHostError, match="resource_scope_expansion"):
        host.execute_graph(
            grant(
                "invoice.select",
                "invoice.filter_confirmed",
                "invoice.filter_date",
                "invoice.aggregate_total",
            ),
            bad,
        )


def test_graph_rejects_unknown_node_reference():
    host = CabinetGraphHost(DEFINITION, build_demo_db())
    bad = graph()
    bad["nodes"][1]["args"]["source"] = {"from": "missing"}
    with pytest.raises(CabinetHostError, match="unknown_node_reference"):
        host.execute_graph(
            grant(
                "invoice.select",
                "invoice.filter_confirmed",
                "invoice.filter_date",
                "invoice.aggregate_total",
            ),
            bad,
        )


def test_graph_rejects_opaque_handle_as_public_output():
    host = CabinetGraphHost(DEFINITION, build_demo_db())
    bad = graph()
    bad["output"] = {"from": "selected"}
    with pytest.raises(CabinetHostError, match="non_opaque_intermediate_escape"):
        host.execute_graph(
            grant(
                "invoice.select",
                "invoice.filter_confirmed",
                "invoice.filter_date",
                "invoice.aggregate_total",
            ),
            bad,
        )


def test_manifest_exposes_only_granted_capabilities():
    host = CabinetGraphHost(DEFINITION, build_demo_db())
    manifest = host.manifest_for(grant("invoice.select"))
    assert set(manifest["capabilities"]) == {"invoice.select"}
