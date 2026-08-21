from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
READINESS = ROOT / "experiments" / "cabinet-vault" / "cabinet_web_real_data_canary_readiness_v1.yaml"
PASS_EVIDENCE = ROOT / "experiments" / "cabinet-vault" / "F260001_REAL_DATA_CANARY_PASS_EVIDENCE_2026-08-21.md"
HANDOFF = ROOT / "experiments" / "cabinet-vault" / "NEXT_SESSION_HANDOFF.md"
BRIDGE = ROOT / "tools" / "local_capability_bridge.py"
RUNNER = ROOT / "tools" / "f260001_real_canary_via_bridge.py"


def load():
    value = yaml.safe_load(READINESS.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_real_f260001_canary_is_pass_and_has_no_current_blocker():
    readiness = load()
    assert readiness["readiness_id"] == "cabinet_web_real_data_canary.v7"
    assert readiness["status"] == "real_data_canary_pass"
    assert readiness["blocking_condition"] is None
    assert readiness["real_execution"]["result"] == "PASS"
    assert readiness["real_execution"]["real_user_data_canary_executed"] is True
    assert PASS_EVIDENCE.is_file()


def test_f260001_exact_web_revision_and_real_pdf_evidence_are_pinned():
    readiness = load()
    source = readiness["source_repository"]
    candidate = readiness["real_candidate"]

    assert source["current_head_commit_sha"] == "d3fac8e5d2b85c12904cba24060717b84e2757c2"
    assert source["reviewed_contract_commit_sha"] == "d4419e3b948d49bd85a99a0941a350a73494cd27"
    assert source["contract_fingerprints_changed"] is False
    assert source["normalization_pull_request"] == 17

    assert candidate["invoice_id"] == "invoice-f260001"
    assert candidate["invoice_card_path"] == "data/cards/invoice-f260001/card.json"
    assert candidate["status"] == "confirmed"
    assert candidate["source_id"] == "source-f260001"
    assert candidate["card_content_hash"] == "sha256:e52e9d1fe3ff273b1510fd45d516daf576df4404320f75db4dfabc51c8f8a0cf"
    assert candidate["source_git_commit_sha"] == "386134cbb28e3689fec8ffb49815db9416ebe9a8"
    assert candidate["real_pdf_local_sha256"] == "sha256:b1ad4b4f15ddcba8c91f0f2d17f8a45ab58fd4febcd1064360aed758f14dec66"
    assert candidate["validation"] == {"status": "PASS", "errors": 0, "warnings": 0}


def test_trusted_bridge_preserves_exact_authority_boundaries():
    bridge = load()["trusted_bridge"]
    assert bridge["readiness"] == "PASS"
    assert bridge["implementation_commit"] == "bc872b605c3e4b3774749cdf1711eeeb35399eaf"
    assert bridge["transport"] == "local_cli_stdio"
    assert bridge["startup_recovery_before_ready"] is True
    assert bridge["authority"]["revision_acceptance"] == {
        "credential_class": "synchronization",
        "grant": "invoice.archive.accept_revision",
        "resource_scope": "invoice:invoice-f260001",
    }
    assert bridge["authority"]["source_attachment"] == {
        "credential_class": "local_agent",
        "grant": "invoice.source.attach",
        "resource_scope": "invoice:invoice-f260001",
    }
    assert BRIDGE.is_file()
    assert RUNNER.is_file()


def test_bridge_ci_and_real_execution_are_distinct_evidence_classes():
    readiness = load()
    ci = readiness["bridge_ci_evidence"]
    real = readiness["real_execution"]

    assert ci["run_id"] == 32529515458
    assert ci["head_sha"] == "bc872b605c3e4b3774749cdf1711eeeb35399eaf"
    assert ci["conclusion"] == "success"
    assert ci["artifact_id"] == 9463368772
    assert ci["artifact_digest"] == "sha256:6f81d77d2e5747d19608bf438f9551f333cc309f0feebbc95d30d95f064dfdb2"

    assert real["delivery_id"] == "real-f260001-cf5972ac55c546dda6db5df0dd937931"
    assert real["revision_receipt_outcome"] == "accepted"
    assert real["source_attachment_result"] == "attached"
    assert real["parser_validated_media_type"] == "application/pdf"
    assert real["card_unchanged"] is True
    assert real["acceptance_audit_present"] is True
    assert real["attachment_audit_present"] is True


def test_local_hash_and_media_remain_local_evidence_not_web_facts():
    readiness = load()
    real = readiness["real_execution"]
    guards = set(readiness["preserved_guards"])

    assert real["local_calculated_source_sha256"] == "sha256:b1ad4b4f15ddcba8c91f0f2d17f8a45ab58fd4febcd1064360aed758f14dec66"
    assert "local_parser_media_and_binary_hash_remain_local_evidence" in guards
    assert "backend_does_not_rewrite_confirmed_Card_document_or_hash" in guards
    assert "direct_PostgreSQL_or_vault_bypass_remains_forbidden" in guards


def test_unrelated_full_suite_failures_are_not_relabelled_as_canary_passes():
    note = load()["full_suite_note"]
    assert note["reported_passed"] == 605
    assert note["reported_failed"] == 6
    assert note["canary_gate_effect"] == "none"
    assert "pre_existing_unrelated" in note["relation_to_canary"]


def test_next_handoff_moves_to_relationship_projection_repair_not_another_first_canary():
    text = HANDOFF.read_text(encoding="utf-8")
    assert "REAL DATA PASS" in text
    assert "real_user_data_canary_executed    true" in text
    assert "Recommended next product-data repair" in text
    assert "Client/Project Cards keep stable links/projections only" in text
