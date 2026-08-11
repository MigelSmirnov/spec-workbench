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
    router = phases["deterministic_http_router_closure"]
    assert data["after"] == "public_module_operations"
    assert data["before"] == "exact_contracts_internal_functions"
    assert router["after"] == "exact_contracts_internal_functions"
    assert router["before"] == "notes"
    assert payload["invariants"]["artifact_prefixes_define_semantic_state"] is False


def test_router_cannot_be_signature_source() -> None:
    invariants = _sequence()["invariants"]
    assert invariants["canonical_python_signatures_owner"] == "exact_contracts_internal_functions"
    assert invariants["router_requires_canonical_contracts"] is True
    assert invariants["router_may_define_signatures"] is False
    assert invariants["legacy_router_is_evidence_only"] is True


def test_legacy_named_data_tool_declares_pre_contract_role() -> None:
    doc = design_stage6_data.__doc__ or ""
    assert "pre-contract" in doc.casefold()
    assert "semantic State 6 is exact contracts" in doc
