from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "experiments" / "cabinet-vault" / "cabinet_authority_contract_v0.yaml"


def load_contract():
    value = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_authority_contract_separates_principal_credential_and_sync_boundaries():
    contract = load_contract()
    principal = contract["principal_contract"]

    assert set(principal["principal_kinds"]) == {
        "human",
        "agent",
        "service",
        "synchronization_node",
    }
    assert principal["principal_identity"]["stable_across_credential_rotation"] is True
    rules = set(principal["separation_rules"])
    assert "synchronization_node_identity_cannot_authorize_local_agent_operations" in rules
    assert "local_agent_or_service_identity_cannot_authorize_synchronization" in rules


def test_exact_capability_and_resource_scope_are_required_and_default_deny():
    contract = load_contract()
    grant = contract["resource_grant_contract"]

    assert grant["default"] == "deny"
    assert grant["required_dimensions"] == [
        "principal_id",
        "capability",
        "resource_scope",
    ]
    assert "capability_match_is_exact" in grant["rules"]
    assert "resource_scope_must_cover_exact_target" in grant["rules"]


def test_actor_and_authorization_evidence_are_host_bound_not_caller_proof():
    contract = load_contract()
    actor = contract["actor_binding_contract"]
    protected = set(contract["protected_host_values"])

    assert actor["host_constructed"] is True
    assert "caller_cannot_supply_authorization_decision_as_proof" in actor["rules"]
    assert "caller_cannot_self_assert_delegated_by" in actor["rules"]
    assert "authorization_decision" in protected
    assert "actor_from_authenticated_principal" in protected
    assert "grant_state" in protected


def test_effect_and_disclosure_authority_are_declared_per_capability():
    contract = load_contract()
    policy = contract["capability_policy_contract"]

    assert policy["each_capability_declares"] == [
        "required_grant",
        "resource_scope_rule",
        "effects",
        "disclosure_allow",
        "disclosure_deny",
        "audit_requirement",
    ]
    assert policy["defaults"] == {
        "effect": "deny_unless_declared",
        "disclosure": "deny_unless_allowed",
    }


def test_authentication_mechanisms_are_not_cabinet_semantic_identity():
    contract = load_contract()
    lowering = set(contract["classical_lowering_not_durable_identity"])
    credential_mechanisms = set(
        contract["credential_contract"]["host_mechanisms_not_product_semantics"]
    )

    for item in ("PostgresAccessControlBackend", "PostgreSQL", "Argon2id", "HTTP", "MCP"):
        assert item in lowering
    for item in ("verifier_algorithm", "verifier_storage_backend", "throttling_storage"):
        assert item in credential_mechanisms


def test_audit_evidence_is_append_only_non_secret_and_not_future_authority():
    contract = load_contract()
    audit = contract["security_audit_contract"]

    assert audit["append_only"] is True
    assert "audit_evidence_never_contains_reusable_secret" in audit["rules"]
    assert "audit_evidence_is_not_authority_for_a_future_invocation" in audit["rules"]
    assert "result" in audit["minimum_semantic_fields"]
    assert "reason_code" in audit["minimum_semantic_fields"]


def test_verification_obligations_cover_generated_authority_failure_surface():
    contract = load_contract()
    probes = {item["id"]: item["statement"] for item in contract["verification_obligations"]}

    assert probes["AUTH-PROBE-001"] == "caller_supplied_authorization_decision_cannot_authorize_invocation"
    assert probes["AUTH-PROBE-002"] == "revoked_principal_or_credential_cannot_authorize_new_invocation"
    assert probes["AUTH-PROBE-003"] == "capability_without_exact_resource_scope_is_denied"
    assert probes["AUTH-PROBE-007"] == "protected_mutation_binds_actor_from_authenticated_principal"
    assert probes["AUTH-PROBE-008"] == "audit_evidence_contains_no_reusable_credential_material"
