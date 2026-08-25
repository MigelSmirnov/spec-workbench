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
    phases = {entry["id"]: entry for entry in payload["phases"]}
    data = phases["pre_contract_structured_data_closure"]
    persistence = phases["deterministic_persistence_closure"]
    routes = phases["deterministic_http_router_closure"]
    context = phases["deterministic_http_router_context_closure"]
    assembly = phases["deterministic_http_router_ir_assembly"]
    assert phases["state5_public_module_operations"]["next"] == "pre_contract_structured_data_closure"
    assert "semantic_state" not in data
    assert data["next"] == "state6_exact_contracts"
    assert phases["state6_exact_contracts"]["semantic_state"] == 6
    assert persistence["conditional"] == "rules.persistence_backend is used"
    assert persistence["compatibility_artifacts"] == ["70_persistence_closure.json"]
    assert persistence["gate_tool"] == "tools/design_persistence_authoring.py"
    assert persistence["next"] == "deterministic_http_router_closure"
    assert routes["next"] == "deterministic_http_router_context_closure"
    assert context["next"] == "deterministic_http_router_ir_assembly"
    assert assembly["next"] == "state7_notes"
    assert phases["state7_notes"]["semantic_state"] == 7
    assert all("semantic_state" not in phases[p] for p in (
        "deterministic_persistence_closure", "deterministic_http_router_closure",
        "deterministic_http_router_context_closure", "deterministic_http_router_ir_assembly",
    ))
    assert payload["invariants"]["artifact_prefixes_define_semantic_state"] is False


def test_one_machine_sequence_is_linear_and_every_tool_exists() -> None:
    payload = _sequence()
    phases = payload["phases"]
    assert payload["machine_source_of_truth"] is True
    assert [p["id"] for p in phases[:7]] == [
        "state0_product_frame", "state1_models", "state2_rules_decisions",
        "state3_module_responsibilities", "state2_to_state3_trace",
        "state4_reviewed_flows", "state5_public_module_operations",
    ]
    for previous, current in zip(phases, phases[1:]):
        assert previous["next"] == current["id"], previous["id"]
    assert "next" not in phases[-1]
    for phase in phases:
        assert phase["status"] == "available", phase["id"]
        for key in ("inspect_tool", "gate_tool", "edit_tool", "projection_tool", "mutation_tool"):
            tool = phase.get(key)
            if tool:
                assert (ROOT / tool).is_file(), f"missing {key} for {phase['id']}: {tool}"


def test_factory_admission_is_stage_9_not_a_semantic_state() -> None:
    payload = _sequence()
    stages = {entry["stage"]: entry for entry in payload["phases"] if "stage" in entry}
    assert set(stages) == {"8", "8.1", "9"}
    assert stages["8.1"]["next"] == "stage9_factory_admission"
    assert stages["9"] == {
        "id": "stage9_factory_admission",
        "stage": "9",
        "status": "available",
        "mode": "read_only_gate",
        "gate_tool": "tools/design_factory_admission.py",
        "gate_args": [],
        "mutation_tool": "tools/export_to_factory.py",
        "ends_before": "factory_route_b",
    }
    assert "semantic_state" not in stages["9"]
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
