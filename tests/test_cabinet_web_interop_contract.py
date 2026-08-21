from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "experiments" / "cabinet-vault" / "cabinet_web_interop_audit_v0.yaml"
ATTACH_EVIDENCE = ROOT / "experiments" / "cabinet-vault" / "CABINET_WEB_ATTACH_CANARY_RUNTIME_EVIDENCE.md"
SYNC_EVIDENCE = ROOT / "experiments" / "cabinet-vault" / "CABINET_WEB_SYNC_RUNTIME_EVIDENCE.md"
REAL_EVIDENCE = ROOT / "experiments" / "cabinet-vault" / "F260001_REAL_DATA_CANARY_PASS_EVIDENCE_2026-08-21.md"


def load():
    value = yaml.safe_load(AUDIT.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_audit_promotes_interop_after_real_user_data_canary():
    audit = load()
    source = audit["source_repository"]

    assert audit["audit_version"] == "cabinet_web_backend_interop.v4"
    assert audit["status"] == "real_data_canary_verified"
    assert source["repository"] == "MigelSmirnov/Cabinet_web"
    assert source["ref"] == "main"
    assert source["current_main_commit_sha"] == "d3fac8e5d2b85c12904cba24060717b84e2757c2"
    assert source["reviewed_contract_commit_sha"] == "d4419e3b948d49bd85a99a0941a350a73494cd27"
    assert source["accepted_source_identity_via_pull_request"] == 16
    assert source["normalized_real_invoice_via_pull_request"] == 17
    assert source["contract_fingerprints_changed_since_review"] is False


def test_real_data_gate_is_pass_and_execution_is_explicit():
    audit = load()
    gate = audit["gate"]
    findings = {item["id"]: item for item in audit["findings"]}

    assert gate == {
        "isolated_box_runtime_evidence": "PASS",
        "cabinet_web_source_identity_contract": "PASS",
        "cabinet_web_sync_contract_design": "PASS",
        "cabinet_web_sync_acceptance_runtime": "PASS",
        "cabinet_web_same_invoice_e2e_runtime": "PASS",
        "cabinet_web_media_lowering_runtime": "PASS",
        "cabinet_web_no_expected_hash_runtime": "PASS",
        "trusted_local_capability_bridge": "PASS",
        "cabinet_web_interop_gate": "pass",
        "real_cabinet_web_data_canary": "PASS",
        "real_user_data_canary_executed": True,
        "blocking_findings": [],
    }
    assert findings["CW-REAL-DATA-001"]["class"] == "REAL_USER_DATA_INTEROP_VERIFIED"
    assert {finding["severity"] for finding in findings.values()} == {"PASS"}


def test_bridge_execution_is_pinned_to_github_evidence_and_exact_scope():
    executed = load()["executed_bridge_evidence"]
    assert executed["implementation_commit"] == "bc872b605c3e4b3774749cdf1711eeeb35399eaf"
    assert executed["entrypoint"] == "tools/local_capability_bridge.py"
    assert executed["transport"] == "local_cli_stdio"
    assert executed["workflow"]["run_id"] == 32529515458
    assert executed["workflow"]["conclusion"] == "success"
    assert executed["artifact"]["artifact_id"] == 9463368772
    assert executed["artifact"]["digest"] == "sha256:6f81d77d2e5747d19608bf438f9551f333cc309f0feebbc95d30d95f064dfdb2"
    assert executed["protected_boundaries"]["revision_acceptance"]["resource_scope"] == "invoice:invoice-f260001"
    assert executed["protected_boundaries"]["source_attachment"]["resource_scope"] == "invoice:invoice-f260001"
    assert executed["protected_boundaries"]["revision_acceptance"]["credential_class"] == "synchronization"
    assert executed["protected_boundaries"]["source_attachment"]["credential_class"] == "local_agent"


def test_real_f260001_execution_proves_card_immutability_source_and_audit():
    executed = load()["executed_real_data_evidence"]
    assert executed["execution_class"] == "private_local_real_user_data_canary"
    assert executed["invoice_id"] == "invoice-f260001"
    assert executed["card_content_hash"] == "sha256:e52e9d1fe3ff273b1510fd45d516daf576df4404320f75db4dfabc51c8f8a0cf"
    assert executed["source_id"] == "source-f260001"
    assert executed["revision_receipt_outcome"] == "accepted"
    assert executed["backend_current_content_hash"] == executed["card_content_hash"]
    assert executed["source_attachment_result"] == "attached"
    assert executed["parser_validated_media_type"] == "application/pdf"
    assert executed["local_calculated_source_sha256"] == "sha256:b1ad4b4f15ddcba8c91f0f2d17f8a45ab58fd4febcd1064360aed758f14dec66"
    assert executed["card_unchanged"] is True
    assert executed["acceptance_audit_present"] is True
    assert executed["attachment_audit_present"] is True
    assert REAL_EVIDENCE.is_file()


def test_prior_sync_and_attach_runtime_evidence_remains_pinned():
    audit = load()
    sync = audit["executed_sync_evidence"]
    attach = audit["executed_attach_evidence"]

    assert sync["workflow"]["run_id"] == 32514048863
    assert sync["artifact"]["artifact_id"] == 9458097099
    assert set(sync["probes"].values()) == {"PASS"}
    assert SYNC_EVIDENCE.is_file()

    assert attach["workflow"]["run_id"] == 32507028221
    assert attach["artifact"]["artifact_id"] == 9455627318
    assert set(attach["probes"].values()) == {"PASS"}
    assert ATTACH_EVIDENCE.is_file()


def test_authority_and_fact_ownership_guards_remain_fail_closed_after_success():
    audit = load()
    policy = audit["change_policy"]
    findings = {item["id"]: item for item in audit["findings"]}

    assert findings["CW-AUTHORITY-001"]["severity"] == "PASS"
    assert findings["CW-SOURCE-ID-001"]["severity"] == "PASS"
    assert policy["Cabinet_web_source_contract_change_requires_connector_review"] is True
    assert policy["source_repository_fingerprint_drift"] == "block_and_refresh_audit"
    assert policy["backend_adapter_may_not_resolve_upstream_contract_drift"] is True
    assert policy["synchronization_transport_may_not_own_business_semantics"] is True
    assert policy["detected_media_and_local_hash_may_not_become_Cabinet_web_facts_without_new_Card_revision"] is True
    assert policy["trusted_bridge_may_not_expand_scope_or_capability_surface_without_review"] is True


def test_unrelated_full_suite_failures_remain_separate_from_interop_gate():
    note = load()["full_suite_note"]
    assert note["reported_passed"] == 605
    assert note["reported_failed"] == 6
    assert note["classification"] == "pre_existing_unrelated_state5_state6_assembly_count_assertions"
    assert note["canary_gate_effect"] == "none"
