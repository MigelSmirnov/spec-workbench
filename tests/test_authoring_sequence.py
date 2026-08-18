from __future__ import annotations

import json
from pathlib import Path

import design_stage6_data


ROOT = Path(__file__).resolve().parents[1]
SEQUENCE = ROOT / "skills" / "spec-authoring" / "authoring_sequence.json"


def _sequence() -> dict[str, object]:
    return json.loads(SEQUENCE.read_text(encoding="utf-8"))


def test_semantic_state_numbers_are_frozen() -> None:
    payload = _sequence()
    states = {entry["state"]: entry["id"] for entry in payload["semantic_states"]}
    assert states == {
        0: "product_frame",
        1: "models",
        2: "rules_decisions",
        3: "module_responsibilities",
        4: "reviewed_flows",
        5: "public_module_operations",
        6: "exact_contracts_internal_functions",
        7: "notes",
    }


def test_intermediate_closures_do_not_consume_state_numbers() -> None:
    payload = _sequence()
    phases = {entry["id"]: entry for entry in payload["intermediate_phases"]}
    data = phases["pre_contract_structured_data_closure"]
    persistence = phases["deterministic_persistence_backend_closure"]
    routes = phases["deterministic_http_route_closure"]
    context = phases["deterministic_http_router_context_closure"]
    assembly = phases["deterministic_http_router_ir_assembly"]
    assert data["after"] == "public_module_operations"
    assert data["before"] == "exact_contracts_internal_functions"
    assert persistence["after"] == "exact_contracts_internal_functions"
    assert persistence["before"] == "deterministic_http_route_closure"
    assert persistence["conditional"] == "rules.persistence_backend is used"
    assert persistence["compatibility_artifacts"] == ["70_persistence_closure.json"]
    assert persistence["deterministic_tool"] == "tools/design_persistence_authoring.py"
    assert routes["after"] == "deterministic_persistence_backend_closure"
    assert routes["before"] == "deterministic_http_router_context_closure"
    assert context["after"] == "deterministic_http_route_closure"
    assert context["before"] == "deterministic_http_router_ir_assembly"
    assert assembly["after"] == "deterministic_http_router_context_closure"
    assert assembly["before"] == "notes"
    assert payload["invariants"]["artifact_prefixes_define_semantic_state"] is False


def test_factory_admission_is_stage_9_not_a_semantic_state() -> None:
    payload = _sequence()
    stages = {entry["stage"]: entry for entry in payload["operational_stages"]}
    assert stages["9"] == {
        "stage": "9",
        "id": "factory_admission_and_handoff",
        "after": "assembled_module_review",
        "read_only_gate": "tools/design_factory_admission.py",
        "mutation_tool": "tools/export_to_factory.py",
        "ends_before": "factory_route_b",
    }
    assert payload["invariants"]["factory_handoff_requires_admission"] is True
    assert payload["invariants"]["factory_route_b_is_outside_stage_9"] is True


def test_deterministic_backends_cannot_be_signature_sources() -> None:
    invariants = _sequence()["invariants"]
    assert invariants["canonical_python_signatures_owner"] == "exact_contracts_internal_functions"
    assert invariants["pre_contract_data_may_define_contract_dependent_backend_ir"] is False
    assert invariants["persistence_requires_canonical_contracts"] is True
    assert invariants["persistence_may_define_signatures"] is False
    assert invariants["persistence_final_ir_is_deterministic_projection"] is True
    assert invariants["invalid_persistence_backend_allows_llm_fallback"] is False
    assert invariants["router_requires_canonical_contracts"] is True
    assert invariants["router_requires_canonical_handler_per_external_operation"] is True
    assert invariants["router_may_define_signatures"] is False
    assert invariants["router_final_ir_is_deterministic_projection"] is True
    assert invariants["legacy_router_is_evidence_only"] is True


def test_legacy_named_data_tool_declares_pre_contract_role() -> None:
    doc = design_stage6_data.__doc__ or ""
    assert "pre-contract" in doc.casefold()
    assert "semantic state 6 is exact contracts" in doc.casefold()
