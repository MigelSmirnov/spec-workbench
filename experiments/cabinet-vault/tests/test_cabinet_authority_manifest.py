from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
BOX = ROOT / "experiments" / "cabinet-vault" / "cabinet_backend_box_v0.yaml"
AUTHORITY = ROOT / "experiments" / "cabinet-vault" / "cabinet_authority_contract_v0.yaml"


def load(path: Path):
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_box_declares_required_generic_host_authority_services():
    box = load(BOX)
    requirements = set(box["host_requirements"])

    assert {
        "principal_authentication",
        "bounded_capability_grants",
        "exact_resource_scope_authorization",
        "effect_policy_enforcement",
        "disclosure_policy_enforcement",
        "audit_and_provenance",
    } <= requirements


def test_every_capability_declares_grant_scope_effect_disclosure_and_audit():
    box = load(BOX)

    for name, capability in box["capabilities"].items():
        requires = capability.get("requires")
        assert isinstance(requires, list), name
        assert "authenticated_principal" in requires, name
        assert any(item == f"grant:{name}" for item in requires), name
        assert any(isinstance(item, str) and item.startswith("scope:") for item in requires), name

        assert isinstance(capability.get("effects"), list), name

        disclosure = capability.get("disclosure")
        assert isinstance(disclosure, dict), name
        assert isinstance(disclosure.get("allow"), list), name
        assert isinstance(disclosure.get("deny"), list), name

        audit = capability.get("audit")
        assert isinstance(audit, dict), name
        assert audit.get("required") is True, name
        assert isinstance(audit.get("record"), list) and audit["record"], name


def test_disclosure_policy_is_default_deny_and_protects_host_authority_material():
    box = load(BOX)
    disclosure = box["policies"]["disclosure"]

    assert disclosure["default"] == "deny"
    never = set(disclosure["never_disclose"])
    assert "host_credential_material" in never
    assert "database_credentials" in never
    assert "storage_reference" in never


def test_caller_input_schemas_do_not_accept_host_owned_authority_evidence():
    box = load(BOX)
    protected = set(load(AUTHORITY)["protected_host_values"])

    for name, capability in box["capabilities"].items():
        schema_name = capability["input"]
        schema = box["schemas"][schema_name]
        fields = set(schema.get("fields", {}))
        overlap = fields & protected
        assert overlap == set(), f"{name} accepts host-owned fields: {sorted(overlap)}"


def test_effectful_capabilities_bind_actor_from_authenticated_host_context():
    box = load(BOX)

    for name, capability in box["capabilities"].items():
        if not capability.get("effects"):
            continue

        schema = box["schemas"][capability["input"]]
        capability_binding = capability.get("host_binding", {})
        schema_binding = schema.get("host_binds", {})
        actor_binding = capability_binding.get("actor") or schema_binding.get("actor")
        authorization_binding = (
            capability_binding.get("authorization") or schema_binding.get("authorization")
        )

        assert actor_binding == "authenticated_principal", name
        assert authorization_binding == "exact_operation_grant", name


def test_classical_access_control_implementation_names_are_not_box_dependencies():
    box = load(BOX)
    serialized = yaml.safe_dump(
        {
            "external_dependencies": box["external_dependencies"],
            "host_requirements": box["host_requirements"],
            "capabilities": box["capabilities"],
        },
        sort_keys=True,
    )

    for forbidden in (
        "PostgresAccessControlBackend",
        "Argon2id",
        "LocalServiceCredential",
        "request.app.state",
    ):
        assert forbidden not in serialized
