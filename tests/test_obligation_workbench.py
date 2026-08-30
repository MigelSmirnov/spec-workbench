from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

import design_stage6_contracts
from obligation_workbench import SemanticClaim, build_graph, focus, frontier, list_obligations, metrics
from obligation_workbench.factory_parity import classify_edge_sets
from obligation_workbench.model import EvidenceRef
from obligation_workbench.ownership import find_ownership_conflicts
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


@pytest.fixture(scope="module")
def ownership_projection():
    reason = "Multipart streaming and bounded content identification remain an irregular boundary transformation."
    claims = (
        SemanticClaim(
            id="fixture:bounded_content_identification:canonical",
            semantic_key="bounded_content_identification",
            expressed_by="public_op:web_gateway.accept_source_upload",
            semantic_owner="boundary:web_gateway",
            evidence=(EvidenceRef("fixture:router", "accept_source_upload"),),
            canonical=True,
            implementation_mode="irregular",
            irregular_reason=reason,
            applies_to=("module:source_custody",),
        ),
        SemanticClaim(
            id="fixture:bounded_content_identification:downstream",
            semantic_key="bounded_content_identification",
            expressed_by="function:source_custody.store_original_source",
            semantic_owner="module:source_custody",
            evidence=(EvidenceRef("fixture:downstream", "store_original_source"),),
            canonical=False,
        ),
    )
    return build_graph(CASE, factory_root=FACTORY_ROOT, semantic_claims=claims)


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
        assert set(item.to_dict()) >= {
            "kind",
            "addressed_to",
            "semantic_owner",
            "resolution_owner",
            "caused_by",
            "precedence_class",
            "implementation_mode",
            "source",
            "blocked_by",
        }


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
    assert set(payload) >= {"OWNED", "INCOMING", "OUTGOING", "NOT_OWNED", "BLOCKERS"}
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


def test_irregular_router_decision_is_projected_without_becoming_a_defect(projection):
    irregular = [
        claim for claim in projection.semantic_claims if claim.implementation_mode == "irregular"
    ]
    assert len(irregular) == 1
    claim = irregular[0]
    assert claim.semantic_owner == "boundary:web_gateway"
    assert "bounded content identification" in (claim.irregular_reason or "")
    assert "module:source_custody" in claim.applies_to
    assert not [item for item in projection.obligations if item.kind == "structured_lowering_candidate"]
    assert not [item for item in projection.obligations if item.kind == "duplicate_semantic_ownership"]


def test_source_custody_focus_sees_irregular_transport_as_not_owned(projection):
    payload = focus(projection, "module:source_custody")
    claims = payload["NOT_OWNED"]["semantic_claims"]
    assert any(
        item["semantic_owner"] == "boundary:web_gateway"
        and item["implementation_mode"] == "irregular"
        and "bounded content identification" in item["irregular_reason"]
        for item in claims
    )


def test_structured_duplicate_ownership_becomes_one_wrong_owner_obligation(ownership_projection):
    conflicts = [
        item
        for item in ownership_projection.obligations
        if item.kind == "duplicate_semantic_ownership"
    ]
    assert len(conflicts) == 1
    conflict = conflicts[0]
    assert conflict.semantic_owner == "boundary:web_gateway"
    assert conflict.ownership_status == "wrong_owner"
    assert conflict.implementation_mode == "irregular"
    assert conflict.addressed_to == ("function:source_custody.store_original_source",)
    payload = focus(ownership_projection, "module:source_custody")
    assert conflict.id in {item["id"] for item in payload["NOT_OWNED"]["obligations"]}
    assert conflict.id not in {item["id"] for item in payload["OWNED"]["obligations"]}


def test_explicit_shared_ownership_is_not_reported_as_a_conflict():
    claims = tuple(
        SemanticClaim(
            id=f"shared:{owner}",
            semantic_key="joint_transaction_boundary",
            expressed_by=owner,
            semantic_owner=owner,
            evidence=(EvidenceRef("fixture", owner),),
            canonical=True,
            shared_owner_group="joint_transaction_boundary:v1",
        )
        for owner in ("module:source_custody", "module:effect_journal")
    )
    assert find_ownership_conflicts(claims) == ()


def test_recovery_regression_classes_fit_the_obligation_registry():
    assert {
        "cross_call_identity_undefined",
        "derived_identifier_semantics_undefined",
        "downstream_semantic_conflict",
        "runtime_config_binding_missing",
        "protocol_assumption_not_backed_by_contract",
        "production_entrypoint_not_exercised",
    } <= set(RULES)


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
