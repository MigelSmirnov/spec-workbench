from __future__ import annotations

import json
from pathlib import Path

from cabinet_host import load_definition


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "experiments" / "cabinet-vault" / "cabinet_backend_box_v0.yaml"


def manifest():
    return load_definition(MANIFEST)


def test_real_box_slice_is_local_and_has_no_permanent_external_dependency():
    definition = manifest()

    assert definition["manifest_version"] == "cabinet_box.v0"
    assert definition["cabinet"]["slice"] == "archive_inspection_and_local_source_custody"
    assert definition["external_dependencies"] == []
    assert definition["experiment_boundaries"]["cross_box_clients_allowed_in_cabinet"] is False


def test_capability_surface_contains_only_cabinet_owned_archive_and_source_semantics():
    definition = manifest()
    capabilities = definition["capabilities"]

    assert set(capabilities) == {
        "invoice.archive.get",
        "invoice.archive.verify_acceptance",
        "invoice.source.status",
        "invoice.source.attach",
        "invoice.source.accept_incomplete",
        "invoice.source.record_loss",
    }

    semantic_surface = json.dumps(capabilities, sort_keys=True).lower()
    for forbidden in (
        "registryclient",
        "presuproclient",
        "holdedgateway",
        "httpx",
        "fastapi",
        "postgres",
        "app.state",
    ):
        assert forbidden not in semantic_surface


def test_every_capability_declares_typed_authority_effect_disclosure_and_audit_boundaries():
    definition = manifest()
    schemas = definition["schemas"]

    for name, capability in definition["capabilities"].items():
        assert capability["input"] in schemas, name
        assert capability["output"] in schemas, name
        assert isinstance(capability["effects"], list), name
        assert capability["requires"], name
        assert "authenticated_principal" in capability["requires"], name
        assert any(str(item).startswith("grant:") for item in capability["requires"]), name
        assert capability["disclosure"]["allow"], name
        assert capability["disclosure"]["deny"], name
        assert capability["audit"]["required"] is True, name
        assert capability["audit"]["record"], name


def test_agent_visible_inputs_cannot_supply_authority_or_host_storage_references():
    definition = manifest()
    schemas = definition["schemas"]
    forbidden_fields = {
        "authorization",
        "authorization_decision",
        "authenticated_principal",
        "actor",
        "storage_reference",
        "staging_reference",
        "final_reference",
        "database_url",
        "filesystem_root",
    }

    for name, capability in definition["capabilities"].items():
        input_schema = schemas[capability["input"]]
        fields = set(input_schema.get("fields", {}))
        assert not fields.intersection(forbidden_fields), (name, fields)


def test_source_mutations_bind_actor_and_authorization_inside_the_host():
    definition = manifest()
    schemas = definition["schemas"]

    attach = schemas["AttachLocalSourceInput"]
    assert attach["host_binds"]["authorization"] == "exact_operation_grant"
    assert attach["host_binds"]["actor"] == "authenticated_principal"

    for capability_name in (
        "invoice.source.accept_incomplete",
        "invoice.source.record_loss",
    ):
        binding = definition["capabilities"][capability_name]["host_binding"]
        assert binding["actor"] == "authenticated_principal"
        assert binding["authorization"] == "exact_operation_grant"


def test_disclosure_never_allows_host_owned_storage_locations():
    definition = manifest()
    forbidden = {
        "storage_reference",
        "staging_reference",
        "final_reference",
        "raw_filesystem_path",
        "source_vault_storage_reference",
    }

    for name, capability in definition["capabilities"].items():
        allowed = set(capability["disclosure"]["allow"])
        assert not allowed.intersection(forbidden), name


def test_manifest_marks_classical_archive_classes_as_lowering_not_semantic_identity():
    definition = manifest()
    removable = set(definition["lowering_constraints"]["semantic_surface_must_not_require"])

    assert "DurableArchiveService" in removable
    assert "ArchiveUnitOfWork" in removable
    assert "PostgresArchiveUnitOfWork" in removable
    assert "LocalFilesystemSourceByteStore" in removable
    assert "FastAPI" in removable


def test_runtime_policy_forbids_code_query_and_path_selection_from_agent_data():
    definition = manifest()
    rules = set(definition["policies"]["runtime_input"]["rules"])

    assert "runtime_values_are_data_not_code" in rules
    assert "only_declared_typed_capabilities_may_execute" in rules
    assert "no_runtime_value_selects_sql_command_module_tool_or_filesystem_path" in rules
    assert definition["experiment_boundaries"]["arbitrary_agent_sql_allowed"] is False
    assert definition["experiment_boundaries"]["arbitrary_agent_code_allowed"] is False
