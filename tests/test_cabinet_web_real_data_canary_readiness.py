from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
READINESS = ROOT / "experiments" / "cabinet-vault" / "cabinet_web_real_data_canary_readiness_v1.yaml"
FUNCTIONAL_EVIDENCE = ROOT / "experiments" / "cabinet-vault" / "F260001_REAL_DATA_CANARY_PASS_EVIDENCE_2026-08-21.md"
ASSURANCE_REVIEW = ROOT / "experiments" / "cabinet-vault" / "F260001_REAL_RUN_ASSURANCE_REVIEW_2026-08-21.md"


def load():
    value = yaml.safe_load(READINESS.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_real_execution_pass_does_not_imply_assurance_closure():
    readiness = load()
    assert readiness["readiness_id"] == "cabinet_web_real_data_canary.v8"
    assert readiness["status"] == "real_data_execution_pass_assurance_partial"
    assert readiness["real_execution"]["functional_result"] == "PASS"
    assert readiness["real_execution"]["real_user_data_canary_executed"] is True
    assert readiness["assurance_review"]["overall"] == "PARTIAL"
    assert readiness["assurance_review"]["all_guarantees_proven_by_exact_real_run"] is False
    assert FUNCTIONAL_EVIDENCE.is_file()
    assert ASSURANCE_REVIEW.is_file()


def test_exact_real_card_and_source_functional_evidence_remains_pinned():
    readiness = load()
    candidate = readiness["real_candidate"]
    real = readiness["real_execution"]
    assert candidate["invoice_id"] == "invoice-f260001"
    assert candidate["source_id"] == "source-f260001"
    assert candidate["card_content_hash"] == "sha256:e52e9d1fe3ff273b1510fd45d516daf576df4404320f75db4dfabc51c8f8a0cf"
    assert candidate["real_pdf_local_sha256"] == "sha256:b1ad4b4f15ddcba8c91f0f2d17f8a45ab58fd4febcd1064360aed758f14dec66"
    assert real["revision_receipt_outcome"] == "accepted"
    assert real["source_attachment_result"] == "attached"
    assert real["parser_validated_media_type"] == "application/pdf"
    assert real["card_unchanged"] is True
    assert real["durable_acceptance_audit_present"] is True
    assert real["durable_attachment_audit_present"] is True


def test_grant_claims_are_classified_by_evidence_class_not_real_success():
    readiness = load()
    properties = readiness["assurance_review"]["properties"]
    assert properties["exact_non_wildcard_grant_configuration"] == {
        "status": "PASS",
        "evidence_class": "PINNED_CODE",
    }
    enforcement = properties["exact_scope_and_credential_class_negative_enforcement"]
    assert enforcement["status"] == "PASS"
    assert enforcement["evidence_class"] == "CI_PROBE"
    assert enforcement["real_run_negative_case_executed"] is False


def test_real_path_does_not_claim_authorization_before_source_byte_access():
    prop = load()["assurance_review"]["properties"]["authorization_before_source_byte_read_or_parser_access"]
    assert prop["status"] == "FAIL"
    assert "reads PDF bytes before bridge invocation" in prop["reason"]
    assert "before AuthorityKernel.invoke()" in prop["reason"]


def test_real_path_did_not_exercise_declared_stdio_isolation():
    properties = load()["assurance_review"]["properties"]
    assert properties["declared_local_cli_stdio_transport_exercised_by_real_run"]["status"] == "FAIL"
    assert properties["real_agent_confined_from_bridge_internals"]["status"] == "UNVERIFIED"
    assert properties["credentials_independently_host_owned_relative_to_runner"]["status"] == "PARTIAL"


def test_invoice_refset_is_not_claimed_by_f260001_evidence():
    prop = load()["assurance_review"]["properties"]["InvoiceRefSet_opaque_in_this_real_run"]
    assert prop["status"] == "NOT_APPLICABLE"
    assert "CabinetGraphHost" in prop["reason"]


def test_assurance_closure_has_explicit_block_and_required_run():
    readiness = load()
    block = readiness["assurance_closure_condition"]
    assert block["id"] == "CW-ASSURANCE-001"
    assert block["class"] == "REAL_RUN_ASSURANCE_INCOMPLETE"
    assert block["severity"] == "BLOCK_FOR_ASSURANCE_CLOSURE"
    required = set(readiness["required_assurance_run"])
    assert "execute_agent_and_bridge_as_separate_processes_over_actual_local_transport" in required
    assert "persist_bounded_non_secret_audit_event_ids_or_digests_and_exact_decision_fields" in required
