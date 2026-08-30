from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

import design_stage6_contracts
from obligation_workbench import build_graph, focus, frontier, list_obligations, metrics
from obligation_workbench.factory_parity import classify_edge_sets
from obligation_workbench.registry import RULES


ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "examples" / "cabinet-web-backend"
BACKEND_CASE = ROOT / "examples" / "cabinet-backend"
FACTORY_ROOT = ROOT.parents[1]


def _snapshot(directory: Path) -> dict[str, str]:
    return {
        str(path.relative_to(directory)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


@pytest.fixture(scope="module")
def projection():
    return build_graph(CASE, factory_root=FACTORY_ROOT)


@pytest.fixture(scope="module")
def backend_projection():
    return build_graph(BACKEND_CASE, factory_root=FACTORY_ROOT)


def test_projection_is_read_only():
    before = _snapshot(CASE)
    build_graph(CASE)
    assert _snapshot(CASE) == before


def test_public_api_views_are_transport_neutral(projection):
    assert list_obligations(projection)["schema_version"] == "spec_workbench_obligations_list.v1"
    assert frontier(projection)["schema_version"] == "spec_workbench_obligations_frontier.v1"
    assert metrics(projection)["schema_version"] == "spec_workbench_obligations_metrics.v1"


def test_obligations_have_stable_identity_cause_and_addressability(projection):
    ids = [item.id for item in projection.obligations]
    assert len(ids) == len(set(ids))
    assert all(item.caused_by for item in projection.obligations)
    for item in projection.obligations:
        assert item.kind in RULES
        if item.category == "engineering":
            assert item.addressed_to
            assert set(item.addressed_to) <= set(projection.graph.nodes)


def test_one_reachability_cause_keeps_many_addressees(projection):
    candidates = [
        item for item in projection.obligations
        if item.kind == "capability_unreachable"
        and item.required_from == ("capability:effect_journal.begin_effect",)
    ]
    assert len(candidates) == 1
    assert len(candidates[0].addressed_to) > 1


def test_focus_looks_both_directions_and_does_not_hide_incoming_work(projection):
    payload = focus(projection, "module:effect_journal")
    incoming = payload["INCOMING"]["evidence_edges"]
    assert incoming
    assert any(item["target"].startswith("capability:effect_journal.") for item in incoming)
    assert "OUTGOING" in payload and "BLOCKERS" in payload and "OWNED" in payload
    assert payload["state"]["globally_settled"] is False
    assert payload["state"]["status"] in {"READY", "BLOCKED"}
    with pytest.raises(KeyError):
        focus(projection, "module:not_a_real_module")


def test_local_completion_is_separate_from_global_settlement(projection):
    blocked_contracts = [
        state for state in projection.states.values()
        if state.kind == "contract" and state.locally_complete and not state.globally_settled
    ]
    assert blocked_contracts
    by_id = {item.id: item for item in projection.obligations}
    assert all(
        by_id[blocker].precedence_class == "defining"
        for state in blocked_contracts
        for blocker in state.blocked_by
    )


def test_outcomes_are_not_joined_to_flows_by_text_similarity(projection):
    outcomes = {key for key, node in projection.graph.nodes.items() if node.kind == "outcome"}
    assert outcomes
    assert not [edge for edge in projection.graph.edges if edge.kind == "implemented_by_flow"]
    unresolved = {
        address
        for item in projection.obligations
        if item.kind == "outcome_flow_mapping_unresolved"
        for address in item.addressed_to
    }
    assert unresolved == outcomes


def test_explicit_state0_boundary_headings_are_first_class_nodes(projection):
    boundary = projection.graph.nodes["boundary:external-systems-and-trust-boundaries"]
    assert boundary.kind == "boundary"
    assert any(item.source == "state0" for item in boundary.evidence)
    child = projection.graph.nodes["boundary:upload-file-boundary"]
    assert any(item.source == "state0" for item in child.evidence)


def test_factory_parity_filters_only_consumer_to_models_context():
    workbench = {("declared", "provider")}
    merged = {
        ("declared", "provider"),
        ("invoice_exchange", "invoice_catalogue"),
        ("source_custody", "invoice_catalogue"),
        ("models", "access_control"),
        ("api", "synchronization"),
        ("api", "models"),
    }
    compiler, undesigned, missing = classify_edge_sets(workbench, merged)
    assert compiler == {("api", "models")}
    assert {
        ("invoice_exchange", "invoice_catalogue"),
        ("source_custody", "invoice_catalogue"),
        ("models", "access_control"),
        ("api", "synchronization"),
    } <= undesigned
    assert not missing


def test_cabinet_regression_corpus_preserves_semantic_relations(projection, backend_projection):
    web_kinds = {item.kind for item in projection.obligations}
    assert {
        "route_without_designed_boundary",
        "model_without_design_source",
        "capability_unreachable",
    } <= web_kinds
    if projection.factory_parity["available"]:
        assert "dependency_not_designed" in web_kinds
        assert {
            ("invoice_exchange", "invoice_catalogue"),
            ("source_custody", "invoice_catalogue"),
        } <= {tuple(edge) for edge in projection.factory_parity["dependency_not_designed"]}

    backend_kinds = {item.kind for item in backend_projection.obligations}
    assert {"module_cut_undecided", "model_without_design_source"} <= backend_kinds
    if backend_projection.factory_parity["available"]:
        assert "dependency_not_designed" in backend_kinds
        assert {
            ("models", "access_control"),
            ("api", "synchronization"),
        } <= {tuple(edge) for edge in backend_projection.factory_parity["dependency_not_designed"]}
    assert not [item for item in backend_projection.obligations if item.kind == "unclassified_finding"]


def test_tool_level_codec_diagnostic_has_no_fake_design_node(projection):
    codec = [item for item in projection.obligations if item.kind == "codec_registry_unavailable"]
    if codec:
        assert all(item.category == "tool" and not item.addressed_to for item in codec)


def test_known_message_only_findings_now_have_structured_addresses():
    findings = design_stage6_contracts.coverage(CASE)["findings"]
    timestamp = [item for item in findings if item["code"] == "fresh_timestamp_without_source"]
    surfaces = [item for item in findings if item["code"] == "module_surface_not_deep"]
    assert timestamp and all(item.get("contract") for item in timestamp)
    assert surfaces and all(item.get("module") for item in surfaces)


def test_cli_json_contract():
    run = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "obligations.py"), str(CASE), "--next", "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(run.stdout)
    assert payload["schema_version"] == "spec_workbench_obligations_frontier.v1"
    assert set(payload) >= {"READY", "BLOCKED", "SETTLED"}
