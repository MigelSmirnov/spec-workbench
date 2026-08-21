from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "experiments" / "cabinet-vault" / "cabinet_web_sync_contract_v1.yaml"


def load():
    value = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_sync_contract_preserves_autonomous_authority_split():
    contract = load()
    participants = contract["participants"]

    assert participants["producer"]["id"] == "Cabinet_web"
    assert "Invoice_Card_facts" in participants["producer"]["authority"]
    assert participants["consumer"]["id"] == "cabinet_backend_local_box"
    assert "durable_local_replica" in participants["consumer"]["authority"]

    forbidden = set(contract["forbidden_ownership_transfer"])
    assert "backend_rewrites_confirmed_Card_facts" in forbidden
    assert "Cabinet_web_imports_backend_database_or_runtime_model" in forbidden
    assert "backend_generates_or_replaces_Cabinet_web_source_id" in forbidden


def test_delivery_binds_exact_confirmed_card_revision_and_git_provenance():
    contract = load()
    fields = contract["delivery"]["fields"]

    assert fields["contract_version"]["value"] == "cabinet-web-sync-v1"
    assert fields["card_contract_version"]["value"] == 1
    assert fields["card_status"]["value"] == "confirmed"
    assert fields["card_content_hash"]["semantic"] == "invoice.card_revision.content_hash"
    assert fields["source_git_commit_sha"]["semantic"] == "invoice.card_revision.git_commit"
    assert fields["card_document"]["schema_owner"] == "Cabinet_web"
    assert fields["card_document"]["schema_ref"] == "schemas/invoice-card-v1.schema.json"
    assert "canonical_hash_equals_card_content_hash" in fields["card_document"]["constraints"]


def test_revision_hash_reuses_cabinet_web_canonical_hash_semantics():
    contract = load()
    revision_hash = contract["canonical_revision_hash"]

    assert revision_hash["algorithm"] == "sha256"
    assert revision_hash["output_format"] == "sha256:<64 lowercase hex>"
    assert "sort_keys=true" in revision_hash["serialization"]
    assert "separators=(comma,colon)" in revision_hash["serialization"]
    assert "tools.invoice_service.canonical_json/content_hash" in revision_hash["serialization"]


def test_source_expectation_is_derived_from_card_and_does_not_claim_byte_attachment():
    contract = load()
    relation = contract["source_expectation_relation"]

    assert relation["source_set_owner"] == "Cabinet_web_Card"
    assert "source.source_id" in relation["current_invoice_v1_projection"]["fields"]

    byte_semantics = relation["byte_attachment_semantics"]
    assert byte_semantics["card_acceptance_implies_source_bytes_attached"] is False
    assert byte_semantics["source_bytes_are_separate_local_box_effect"] is True
    assert byte_semantics["exact_media_type_must_be_parser_validated"] is True
    assert byte_semantics["expected_binary_sha256_may_be_absent_from_Card"] is True
    assert byte_semantics["locally_calculated_sha256_is_backend_evidence_only_when_upstream_hash_absent"] is True


def test_retry_and_revision_reconciliation_fail_closed():
    contract = load()
    acceptance = contract["acceptance"]
    reconciliation = acceptance["reconciliation"]

    assert reconciliation["revision_identity"] == ["invoice_id", "card_content_hash"]
    assert reconciliation["retry_identity"] == "delivery_id"
    rules = set(reconciliation["rules"])
    assert "when_same_delivery_id_and_same_revision_then_return_already_accepted" in rules
    assert "when_same_delivery_id_and_different_revision_then_delivery_identity_conflict" in rules
    assert "when_base_backend_content_hash_mismatches_then_reconciliation_required_without_overwrite" in rules
    assert "accepted_new_revision_never_deletes_previous_immutable_replica" in rules
    assert "receipt_delivery_order_does_not_establish_Git_history_order" in rules


def test_receipt_is_bounded_and_does_not_disclose_backend_storage_model():
    contract = load()
    receipt = contract["receipt"]
    outcomes = set(receipt["fields"]["outcome"]["values"])

    assert {
        "accepted",
        "already_accepted",
        "rejected_contract",
        "rejected_card",
        "delivery_identity_conflict",
        "reconciliation_required",
    } == outcomes

    forbidden = set(receipt["disclosure"]["forbidden"])
    assert forbidden == {
        "database_primary_keys",
        "filesystem_paths",
        "vault_object_paths",
        "credentials",
        "raw_audit_storage",
    }


def test_transport_is_not_semantic_owner_and_remaining_canary_blocks_stay_visible():
    contract = load()
    transport = contract["transport_policy"]

    assert set(transport["semantic_contract_must_not_depend_on"]) == {
        "HTTP",
        "MCP",
        "local_IPC",
        "filesystem_drop",
        "agent_transport",
    }
    assert transport["adapters_must_be_thin"] is True
    assert "resolve_revision_conflict_by_last_write_wins" in transport["adapters_must_not"]

    gate = contract["interop_gate_effect"]
    assert gate["closes_design_gap"] == "CW-SYNC-001"
    assert set(gate["does_not_close"]) == {
        "CW-SOURCE-ID-001_until_upstream_PR_is_in_main",
        "CW-MEDIA-001",
        "CW-HASH-001_runtime_evidence",
    }
    assert gate["real_Cabinet_web_canary_allowed"] is False


def test_upstream_source_identity_pr_is_pinned_until_main_accepts_it():
    contract = load()
    prerequisite = contract["upstream_prerequisite"]

    assert prerequisite["repository"] == "MigelSmirnov/Cabinet_web"
    assert prerequisite["branch"] == "agent/source-id-contract-repair"
    assert prerequisite["pull_request"] == 16
    assert prerequisite["head_sha"] == "4a8a375dcb82ddb0f24e62c1a11eb6ae9e05e573"
    assert prerequisite["main_must_contain_decision_before_real_canary"] is True
