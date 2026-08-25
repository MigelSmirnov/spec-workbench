from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
AUDIT = ROOT / "experiments" / "cabinet-vault" / "cabinet_web_interop_audit_v0.yaml"
ASSURANCE = ROOT / "experiments" / "cabinet-vault" / "F260001_REAL_RUN_ASSURANCE_REVIEW_2026-08-21.md"


def load():
    value = yaml.safe_load(AUDIT.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_audit_keeps_functional_real_data_pass_but_assurance_partial():
    audit = load()
    assert audit["audit_version"] == "cabinet_web_backend_interop.v5"
    assert audit["status"] == "functional_real_data_pass_assurance_partial"
    gate = audit["gate"]
    assert gate["cabinet_web_interop_gate"] == "pass"
    assert gate["functional_real_cabinet_web_data_canary"] == "PASS"
    assert gate["real_user_data_canary_executed"] is True
    assert gate["trusted_bridge_ci_assurance"] == "PASS"
    assert gate["exact_real_run_assurance_gate"] == "partial"
    assert gate["all_guarantees_proven_by_exact_real_run"] is False
    assert "CW-TRANSPORT-001" in gate["assurance_blocking_findings"]
    assert ASSURANCE.is_file()


def test_real_data_functional_evidence_remains_exact():
    real = load()["real_data_execution"]
    assert real["functional_result"] == "PASS"
    assert real["invoice_id"] == "invoice-f260001"
    assert real["card_content_hash"] == "sha256:e52e9d1fe3ff273b1510fd45d516daf576df4404320f75db4dfabc51c8f8a0cf"
    assert real["source_id"] == "source-f260001"
    assert real["revision_receipt_outcome"] == "accepted"
    assert real["source_attachment_result"] == "attached"
    assert real["durable_acceptance_audit_present"] is True
    assert real["durable_attachment_audit_present"] is True


def test_exact_grant_enforcement_is_not_misattributed_to_successful_real_run():
    findings = {item["id"]: item for item in load()["findings"]}
    grant = findings["CW-AUTH-GRANT-001"]
    assert grant["severity"] == "PASS"
    assert grant["evidence_class"] == "PINNED_CODE_PLUS_CI_PROBE"
    assert "successful private real run itself contains no negative grant test" in grant["statement"]


def test_source_byte_pre_authorization_and_transport_gaps_are_explicit():
    findings = {item["id"]: item for item in load()["findings"]}
    assert findings["CW-PREAUTH-001"]["severity"] == "PARTIAL"
    assert "parser identification before AuthorityKernel.invoke()" in findings["CW-PREAUTH-001"]["statement"]
    assert findings["CW-TRANSPORT-001"]["severity"] == "BLOCK_FOR_ASSURANCE"
    assert "invoked methods in-process" in findings["CW-TRANSPORT-001"]["statement"]


def test_real_audit_existence_and_audit_attestation_are_separate_claims():
    findings = {item["id"]: item for item in load()["findings"]}
    assert findings["CW-REAL-DATA-001"]["severity"] == "PASS"
    audit = findings["CW-AUDIT-ASSURANCE-001"]
    assert audit["severity"] == "PARTIAL"
    assert "retained only booleans" in audit["statement"]


def test_invoice_refset_is_not_part_of_f260001_real_path():
    finding = next(item for item in load()["findings"] if item["id"] == "CW-INVOICEREFSET-001")
    assert finding["severity"] == "INFO"
    assert finding["class"] == "NOT_APPLICABLE_TO_F260001_REAL_PATH"


def test_policy_forbids_functional_success_becoming_assurance_by_relabeling():
    policy = load()["change_policy"]
    assert policy["functional_success_may_not_be_relabelled_as_assurance_closure_without_property_evidence"] is True
    assert policy["trusted_bridge_may_not_expand_scope_or_capability_surface_without_review"] is True
