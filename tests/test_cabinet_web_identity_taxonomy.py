import json
from pathlib import Path


CASE = Path(__file__).parents[1] / "examples" / "cabinet-web-backend"


def _spec() -> dict:
    return json.loads((CASE / "global_spec.json").read_text(encoding="utf-8"))


def test_identity_taxonomy_has_one_models_home() -> None:
    spec = _spec()

    assert spec["models"]["ActorType"] == {
        "kind": "enum",
        "values": ["human", "agent", "service", "operator", "system"],
    }
    assert spec["models"]["PrincipalKind"] == {
        "kind": "enum",
        "values": ["cabinet_owner", "local_backend_node", "operator"],
    }
    assert spec["models"]["CredentialSubjectKind"] == {
        "kind": "enum",
        "values": ["principal", "node"],
    }
    assert spec["models"]["CabinetNodeKind"] == {
        "kind": "enum",
        "values": ["vps_cabinet", "local_backend"],
    }

    assert spec["rules"]["principal_catalogue"] == {
        "node_contract_version": "cabinet-web-sync-v1"
    }
    assert "connection_initiator" not in spec["rules"]["synchronization"]


def test_identity_taxonomy_is_the_typed_runtime_surface() -> None:
    spec = _spec()
    models = spec["models"]

    assert models["ActorReference"]["fields"]["actor_type"] == "ActorType"
    assert models["CabinetPrincipal"]["fields"]["principal_kind"] == "PrincipalKind"
    assert models["CabinetNodeIdentity"]["fields"]["node_kind"] == "CabinetNodeKind"
    assert models["PrincipalEnrollmentCommand"]["fields"]["principal_kind"] == "PrincipalKind"
    assert models["AccessCredentialRecord"]["fields"]["subject_kind"] == "CredentialSubjectKind"
    assert models["SecurityAuditRecord"]["fields"]["subject_kind"] == "str | None"

    imports = spec["imports"]["module_internal"]
    assert "ActorType" in imports["source_custody"]["models"]
    assert "PrincipalKind" in imports["access_control"]["models"]
    assert "CredentialSubjectKind" in imports["principal_lifecycle"]["models"]
    assert "CabinetNodeKind" in imports["authentication_admission"]["models"]


def test_notes_use_typed_symbols_and_keep_contract_policy_external() -> None:
    spec = _spec()
    notes = "\n".join(spec["notes"])
    removed_addresses = (
        "rules.principal_catalogue.credential_subject_kinds",
        "rules.principal_catalogue.human_kinds",
        "rules.principal_catalogue.node_kind",
        "rules.principal_catalogue.owner_kind",
        "rules.synchronization.connection_initiator",
    )

    assert not any(address in notes for address in removed_addresses)
    assert "ActorType.human from = models.ActorType" in notes
    assert "CredentialSubjectKind.principal from = models.CredentialSubjectKind" in notes
    assert "PrincipalKind.local_backend_node from = models.PrincipalKind" in notes
    assert "CabinetNodeKind.local_backend from = models.CabinetNodeKind" in notes
    assert "= rules.principal_catalogue.node_contract_version" in notes
