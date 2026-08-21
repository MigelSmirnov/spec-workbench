from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "experiments" / "cabinet-vault" / "cabinet_web_interop_audit_v0.yaml"
ATTACH_EVIDENCE = ROOT / "experiments" / "cabinet-vault" / "CABINET_WEB_ATTACH_CANARY_RUNTIME_EVIDENCE.md"
SYNC_EVIDENCE = ROOT / "experiments" / "cabinet-vault" / "CABINET_WEB_SYNC_RUNTIME_EVIDENCE.md"


def load():
    value = yaml.safe_load(AUDIT.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_audit_is_pinned_to_reviewed_cabinet_web_main_state():
    audit = load()
    source = audit["source_repository"]

    assert audit["audit_version"] == "cabinet_web_backend_interop.v3"
    assert audit["status"] == "ready_for_real_data_canary"
    assert source["repository"] == "MigelSmirnov/Cabinet_web"
    assert source["ref"] == "main"
    assert source["commit_sha"] == "d4419e3b948d49bd85a99a0941a350a73494cd27"
    assert source["reviewed_on"] == "2026-08-21"
    assert source["accepted_source_identity_via_pull_request"] == 16
    assert source["artifacts"] == {
        "architecture/README.md": "388a7e22e852616c57da438d5a7ee4a5b7f4a6bc",
        "architecture/app-architecture.yaml": "0a205c6fdec5b19001647ecea0981330cec1119e",
        "docs/00-product-discovery/DOMAIN_MODEL.md": "cd6747fca920f589cdbc340f39381739eac83f51",
        "docs/01-storage/INVOICE_CARD_FORMAT.md": "56c4a42bf51fac025410d5f6a232b99e4a2835d7",
        "docs/01-storage/STORAGE_MODEL.md": "62965e9e69d525dfdb69fb738c55b522f8f97f17",
        "docs/02-tools/INVOICE_WORKFLOW.md": "2292211ec763f3fa3e31b178307b28eebf6cd6dc",
        "docs/02-tools/INVOICE_TOOLS_MODEL.md": "789708a756206faf26d0260611eb8f73fb327003",
        "schemas/invoice-card-v1.schema.json": "25042abe5d0387671d836f4e39601b1e5d63be2e",
        "tools/invoice_service.py": "c7649351f4c5e833d7a49fd4738f47042b27e417",
        "tools/invoice_draft_service.py": "e8cfb81d1a15dd31a57e008aaafcc65d0395f209",
        "tools/invoice_validation.py": "f2337466024fe64cda27f9170d42f9c1673466b5",
        "tools/invoice_evidence_service.py": "2670fa3fe7e37f6f90064a45b336b8e0374b661b",
        "tests/fixtures/invoices/obramat-cash/card.json": "2a084aad5a285b306f0b0be07f188c686b4e4d5c",
        "tests/test_invoice_draft_service.py": "3a1842a161ae6259475fc392ab850396c2281590",
        "tests/test_invoice_evidence_service.py": "9854611880d2dde44fa2d6db67fc2062127f2980",
        "tests/test_invoice_validation.py": "6550d5dfe91b6b72e23a1b7db4d4b80f51356406",
    }


def test_all_known_interop_findings_are_closed_but_real_data_canary_is_not_yet_executed():
    audit = load()
    gate = audit["gate"]
    findings = {item["id"]: item for item in audit["findings"]}

    assert gate["isolated_box_runtime_evidence"] == "PASS"
    assert gate["cabinet_web_source_identity_contract"] == "PASS"
    assert gate["cabinet_web_sync_contract_design"] == "PASS"
    assert gate["cabinet_web_sync_acceptance_runtime"] == "PASS"
    assert gate["cabinet_web_same_invoice_e2e_runtime"] == "PASS"
    assert gate["cabinet_web_media_lowering_runtime"] == "PASS"
    assert gate["cabinet_web_no_expected_hash_runtime"] == "PASS"
    assert gate["cabinet_web_interop_gate"] == "pass"
    assert gate["real_cabinet_web_data_canary"] == "allowed_not_executed"
    assert gate["real_user_data_canary_executed"] is False
    assert gate["blocking_findings"] == []
    assert {finding["severity"] for finding in findings.values()} == {"PASS"}


def test_source_identity_is_owned_by_upstream_card_contract_not_backend_adapter():
    finding = next(item for item in load()["findings"] if item["id"] == "CW-SOURCE-ID-001")
    assert finding["class"] == "UPSTREAM_CONTRACT_ALIGNED"
    assert finding["owner"] == "Cabinet_web/card-contracts"
    assert set(finding["forbidden_regression"]) == {
        "generate_source_id_inside_backend_adapter",
        "infer_source_identity_from_filename",
        "replace_source_identity_when_storage_metadata_changes",
    }


def test_sync_runtime_preserves_revision_and_authority_rules():
    audit = load()
    finding = next(item for item in audit["findings"] if item["id"] == "CW-SYNC-001")
    executed = audit["executed_sync_evidence"]

    assert finding["class"] == "INTEGRATION_RUNTIME_VERIFIED"
    assert finding["severity"] == "PASS"
    assert finding["contract"]["machine"] == "experiments/cabinet-vault/cabinet_web_sync_contract_v1.yaml"
    assert finding["contract"]["box_extension"] == "experiments/cabinet-vault/cabinet_web_sync_box_extension_v1.yaml"
    assert finding["runtime_evidence"] == "experiments/cabinet-vault/CABINET_WEB_SYNC_RUNTIME_EVIDENCE.md"
    assert {
        "Cabinet_web_remains_authority_for_confirmed_Card_facts",
        "backend_accepts_exact_revision_without_rewriting_it",
        "same_delivery_same_revision_is_idempotent",
        "same_delivery_different_revision_is_conflict",
        "stale_base_requires_reconciliation_without_overwrite",
        "accepted_new_revision_never_deletes_previous_immutable_revision",
        "Card_acceptance_does_not_claim_source_bytes_are_attached",
        "classical_InvoiceTransferManifest_ingest_remains_deferred",
    } == set(finding["preserved_rules"])
    assert executed["workflow"]["run_id"] == 32514048863
    assert executed["workflow"]["conclusion"] == "success"
    assert executed["artifact"]["artifact_id"] == 9458097099
    assert executed["artifact"]["digest"] == "sha256:4f09fd9fc9eef2d12df7211eb46661eb152874c01c37533a940220c797c955e7"
    assert set(executed["probes"].values()) == {"PASS"}
    assert SYNC_EVIDENCE.is_file()


def test_media_and_no_expected_hash_findings_are_pinned_to_executed_evidence():
    audit = load()
    findings = {item["id"]: item for item in audit["findings"]}
    executed = audit["executed_attach_evidence"]

    assert findings["CW-MEDIA-001"]["class"] == "PARSER_BACKED_LOWERING_VERIFIED"
    assert findings["CW-MEDIA-001"]["severity"] == "PASS"
    assert findings["CW-HASH-001"]["class"] == "NO_EXPECTED_HASH_RUNTIME_VERIFIED"
    assert findings["CW-HASH-001"]["severity"] == "PASS"
    assert executed["workflow"]["run_id"] == 32507028221
    assert executed["workflow"]["conclusion"] == "success"
    assert executed["artifact"]["artifact_id"] == 9455627318
    assert executed["artifact"]["digest"] == "sha256:1f7bcc1cabd2e8d4f58cb8310b915fc47944385d6f53d20d27e81a726b11c33e"
    assert set(executed["probes"].values()) == {"PASS"}
    assert ATTACH_EVIDENCE.is_file()


def test_lifecycle_and_authority_split_remain_aligned():
    findings = {item["id"]: item for item in load()["findings"]}
    assert findings["CW-LIFECYCLE-001"]["class"] == "ALIGNED_SPLIT"
    assert findings["CW-LIFECYCLE-001"]["severity"] == "PASS"
    assert findings["CW-AUTHORITY-001"]["class"] == "ALIGNED"
    assert findings["CW-AUTHORITY-001"]["severity"] == "PASS"


def test_external_fingerprint_and_fact_ownership_guards_remain_fail_closed():
    policy = load()["change_policy"]
    assert policy["Cabinet_web_source_contract_change_requires_connector_review"] is True
    assert policy["source_repository_fingerprint_drift"] == "block_and_refresh_audit"
    assert policy["backend_adapter_may_not_resolve_upstream_contract_drift"] is True
    assert policy["synchronization_transport_may_not_own_business_semantics"] is True
    assert policy["detected_media_and_local_hash_may_not_become_Cabinet_web_facts_without_new_Card_revision"] is True
    assert policy["real_Cabinet_web_data_may_enter_box_only_when_interop_gate_passes"] is True
