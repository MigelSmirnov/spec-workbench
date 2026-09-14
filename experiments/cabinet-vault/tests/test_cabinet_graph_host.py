from __future__ import annotations

import pytest

from cabinet_graph_host import CabinetGraphHost
from cabinet_host import CabinetHostError, Grant, build_demo_db


DEFINITION = {
    "cabinet": {"id": "cabinet.local.archive"},
    "schemas": {
        "InvoiceRefSet": {"opaque": True},
        "InvoiceAggregate": {"fields": {}},
    },
    "capabilities": {
        "invoice.select": {
            "input": {"project_id": "WorkObjectId"},
            "output": "InvoiceRefSet",
            "effects": [],
        },
        "invoice.filter_confirmed": {
            "input": {"source": "InvoiceRefSet"},
            "output": "InvoiceRefSet",
            "effects": [],
        },
        "invoice.filter_date": {
            "input": {"source": "InvoiceRefSet", "date_from": "Date?", "date_to": "Date?"},
            "output": "InvoiceRefSet",
            "effects": [],
        },
        "invoice.aggregate_total": {
            "input": {"source": "InvoiceRefSet"},
            "output": "InvoiceAggregate",
            "effects": [],
        },
    },
}


def grant(*caps: str, projects=("project-1",)) -> Grant:
    return Grant(
        principal_id="agent:test",
        principal_status="active",
        capabilities=frozenset(caps),
        project_ids=frozenset(projects),
    )


def all_caps_grant() -> Grant:
    return grant(
        "invoice.select",
        "invoice.filter_confirmed",
        "invoice.filter_date",
        "invoice.aggregate_total",
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


def test_preflight_derives_node_and_output_types_without_execution():
    class NoDatabaseAccess:
        def execute(self, *_args, **_kwargs):
            raise AssertionError("preflight touched the database")

    host = CabinetGraphHost(DEFINITION, NoDatabaseAccess())
    report = host.preflight_graph(all_caps_grant(), graph())

    assert report["valid"] is True
    assert [node["output_type"] for node in report["nodes"]] == [
        "InvoiceRefSet",
        "InvoiceRefSet",
        "InvoiceRefSet",
        "InvoiceAggregate",
    ]
    assert report["output_type"] == "InvoiceAggregate"


def test_graph_composes_atomic_capabilities_without_raw_rows():
    host = CabinetGraphHost(DEFINITION, build_demo_db())
    result = host.execute_graph(all_caps_grant(), graph())

    assert result["project_id"] == "project-1"
    assert result["invoice_count"] == 2
    assert result["confirmed_total"] == "200.0"
    assert result["currency"] == "EUR"
    assert "raw_source_path" not in result
    assert result["evidence"]["preflight_output_type"] == "InvoiceAggregate"
    assert len(result["evidence"]["trace"]) == 4


def test_preflight_rejects_type_mismatch_before_database_access():
    class NoDatabaseAccess:
        def execute(self, *_args, **_kwargs):
            raise AssertionError("invalid graph reached the database")

    host = CabinetGraphHost(DEFINITION, NoDatabaseAccess())
    bad = graph()
    bad["nodes"][3]["args"]["source"] = "not-a-refset"

    with pytest.raises(CabinetHostError, match="graph_type_mismatch"):
        host.execute_graph(all_caps_grant(), bad)


def test_preflight_rejects_capability_output_wired_to_wrong_input_type():
    definition = {
        **DEFINITION,
        "capabilities": {
            **DEFINITION["capabilities"],
            "invoice.aggregate_total": {
                "input": {"source": "InvoiceAggregate"},
                "output": "InvoiceAggregate",
                "effects": [],
            },
        },
    }
    host = CabinetGraphHost(definition, build_demo_db())
    with pytest.raises(CabinetHostError, match="graph_type_mismatch"):
        host.preflight_graph(all_caps_grant(), graph())


def test_preflight_rejects_missing_required_argument():
    host = CabinetGraphHost(DEFINITION, build_demo_db())
    bad = graph()
    del bad["nodes"][0]["args"]["project_id"]
    with pytest.raises(CabinetHostError, match="missing_node_argument"):
        host.preflight_graph(all_caps_grant(), bad)


def test_preflight_rejects_unexpected_argument():
    host = CabinetGraphHost(DEFINITION, build_demo_db())
    bad = graph()
    bad["nodes"][0]["args"]["sql"] = "SELECT * FROM invoices"
    with pytest.raises(CabinetHostError, match="unexpected_node_argument"):
        host.preflight_graph(all_caps_grant(), bad)


def test_graph_denies_capability_not_in_grant():
    host = CabinetGraphHost(DEFINITION, build_demo_db())
    with pytest.raises(CabinetHostError, match="capability_not_granted"):
        host.execute_graph(grant("invoice.select"), graph())


def test_graph_denies_resource_scope_expansion():
    host = CabinetGraphHost(DEFINITION, build_demo_db())
    bad = graph()
    bad["nodes"][0]["args"]["project_id"] = "project-2"
    with pytest.raises(CabinetHostError, match="resource_scope_expansion"):
        host.execute_graph(all_caps_grant(), bad)


def test_graph_rejects_unknown_node_reference():
    host = CabinetGraphHost(DEFINITION, build_demo_db())
    bad = graph()
    bad["nodes"][1]["args"]["source"] = {"from": "missing"}
    with pytest.raises(CabinetHostError, match="unknown_node_reference"):
        host.execute_graph(all_caps_grant(), bad)


def test_preflight_rejects_opaque_handle_as_public_output():
    host = CabinetGraphHost(DEFINITION, build_demo_db())
    bad = graph()
    bad["output"] = {"from": "selected"}
    with pytest.raises(CabinetHostError, match="non_opaque_intermediate_escape"):
        host.preflight_graph(all_caps_grant(), bad)


def test_manifest_exposes_only_granted_capabilities():
    host = CabinetGraphHost(DEFINITION, build_demo_db())
    manifest = host.manifest_for(grant("invoice.select"))
    assert set(manifest["capabilities"]) == {"invoice.select"}
