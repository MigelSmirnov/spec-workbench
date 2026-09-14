from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "experiments" / "cabinet-vault" / "generic_host_lowering_contract_v0.yaml"


def load_contract():
    value = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_contract_owns_only_generic_failure_classes():
    contract = load_contract()

    assert contract["finding_dispositions"] == {
        "LANGUAGE_RELATION_GAP": "generic_host_lowering_contract",
        "PROJECTION_GAP": "generic_host_lowering_contract",
        "VERIFICATION_NOT_EXECUTED": "generic_host_lowering_contract",
        "LOWERING_GAP": "generic_host_lowering_contract",
    }
    assert contract["excluded_finding_dispositions"] == {
        "BOUNDARY_LEAK": "remove_from_cabinet_product_spec",
        "AUTHORITY_SEMANTIC_GAP": "keep_and_close_in_cabinet_semantic_spec",
        "DOMAIN_SEMANTIC_GAP": "keep_and_close_in_cabinet_semantic_spec",
    }


def test_required_verification_is_fail_closed():
    contract = load_contract()
    verification = contract["machine_contracts"]["GHL-VERIFY-001"]
    aggregate = contract["machine_contracts"]["GHL-VERIFY-002"]

    assert verification["statuses"] == {
        "PASS": "required_evidence_executed_and_passed",
        "FAIL": "required_evidence_executed_and_failed",
        "UNVERIFIED": "required_evidence_not_obtained",
        "SKIP": "evidence_not_executed_and_never_equivalent_to_pass",
    }
    assert verification["normalization"] == {
        "required_missing": "UNVERIFIED",
        "required_skip": "UNVERIFIED",
    }
    assert aggregate["pass_condition"] == "all_required_probes_are_PASS"


def test_host_contract_declares_relation_and_dependency_projection_proofs():
    contract = load_contract()
    machine_contracts = contract["machine_contracts"]

    assert machine_contracts["GHL-REL-001"]["failure"] == "block_lowering"
    assert machine_contracts["GHL-PROJ-001"]["failure"] == "block_lowering"
    assert "implementation_relation" in machine_contracts["GHL-REL-001"]["evidence_required"]
    assert "projected_runtime_dependencies" in machine_contracts["GHL-PROJ-001"]["evidence_required"]


def test_generic_lowering_must_not_choose_product_semantics():
    contract = load_contract()
    semantic_guard = contract["machine_contracts"]["GHL-SEM-001"]

    assert semantic_guard["on_missing_meaning"] == "return_semantic_gap"
    assert set(semantic_guard["forbidden_fallbacks"]) == {
        "field_name_guess",
        "type_only_guess",
        "hidden_default",
        "product_specific_adapter_heuristic",
    }


def test_contract_has_no_product_specific_dependencies():
    contract = load_contract()

    assert contract["product_specific_dependencies"] == []
    primitives = "\n".join(contract["required_host_primitives"]).lower()
    for product_name in ("registry", "presupro", "holded", "vps"):
        assert product_name not in primitives
