from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
READINESS = ROOT / "experiments" / "cabinet-vault" / "cabinet_web_real_data_canary_readiness_v1.yaml"
HANDOFF = ROOT / "experiments" / "cabinet-vault" / "NEXT_SESSION_HANDOFF.md"
LOCAL_HANDOFF = ROOT / "experiments" / "cabinet-vault" / "LOCAL_AGENT_REAL_DATA_CANARY_HANDOFF.md"
HUMAN_AUDIT = ROOT / "experiments" / "cabinet-vault" / "CABINET_WEB_COMPATIBILITY_AUDIT.md"


def load():
    value = yaml.safe_load(READINESS.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_interop_runtime_is_ready_but_real_canary_is_blocked_only_by_missing_real_candidate():
    readiness = load()
    assert readiness["readiness_id"] == "cabinet_web_real_data_canary.v2"
    assert readiness["status"] == "blocked_missing_real_candidate"
    assert readiness["interop_prerequisites"] == {
        "cabinet_web_source_identity_contract": "PASS",
        "cabinet_web_sync_contract_design": "PASS",
        "cabinet_web_sync_acceptance_runtime": "PASS",
        "cabinet_web_same_invoice_e2e_runtime": "PASS",
        "cabinet_web_media_lowering_runtime": "PASS",
        "cabinet_web_no_expected_hash_runtime": "PASS",
        "cabinet_web_interop_gate": "pass",
        "evidence": [
            "experiments/cabinet-vault/cabinet_web_interop_audit_v0.yaml",
            "experiments/cabinet-vault/CABINET_WEB_SYNC_RUNTIME_EVIDENCE.md",
            "experiments/cabinet-vault/CABINET_WEB_ATTACH_CANARY_RUNTIME_EVIDENCE.md",
        ],
    }
    assert readiness["blocking_condition"]["id"] == "REAL-CANARY-DATA-001"
    assert readiness["blocking_condition"]["class"] == "MISSING_REAL_INPUT"


def test_reviewed_cabinet_web_main_has_no_invoice_card_candidate():
    readiness = load()
    source = readiness["source_repository"]
    inventory = readiness["inventory"]

    assert source == {
        "repository": "MigelSmirnov/Cabinet_web",
        "ref": "main",
        "commit_sha": "d4419e3b948d49bd85a99a0941a350a73494cd27",
        "head_verification": "identical_to_reviewed_commit",
    }
    assert inventory["observed_card_directories"] == [
        "client-uliana-kolpacheva-20260815",
        "project-uliana-floor-20260815",
        "provider-andrey-bam-20260801",
        "provider-santo-grua-20260815",
    ]
    assert inventory["invoice_card_directories"] == []
    assert inventory["confirmed_invoice_candidates"] == []
    assert inventory["exact_invoice_source_byte_candidates"] == []


def test_test_dirty_or_branch_only_data_cannot_be_relabelled_as_real_data_canary():
    forbidden = set(load()["forbidden_substitutes"])
    assert forbidden == {
        "tests_fixture_as_real_user_data",
        "synthetic_Card_as_real_user_data",
        "unconfirmed_draft_as_canary_target",
        "uncommitted_Card_as_sync_revision",
        "source_bytes_without_exact_Card_source_identity",
        "branch_only_invoice_not_accepted_into_Cabinet_web_main",
        "bypass_reviewed_Cabinet_web_validator",
    }


def test_local_agent_handoff_requires_capability_path_not_direct_database_mutation():
    text = LOCAL_HANDOFF.read_text(encoding="utf-8")
    assert "invoice.archive.accept_revision" in text
    assert "cabinet-backend-sync-receipt-v1" in text
    assert "invoice.source.attach" in text
    assert "Do not bypass the capability by writing PostgreSQL records directly" in text
    assert "real-canary-" in text
    assert "source.source_id" in text


def test_human_handoff_and_compatibility_audit_no_longer_claim_old_interop_blocks():
    handoff = HANDOFF.read_text(encoding="utf-8")
    audit = HUMAN_AUDIT.read_text(encoding="utf-8")

    assert "cabinet_web_interop_gate           PASS" in handoff
    assert "ALLOWED_NOT_EXECUTED" in handoff
    assert "blocked_missing_real_candidate" not in handoff  # prose should stay human-readable
    assert "Cabinet_web interoperability         PASS" in audit
    assert "ALLOWED, NOT EXECUTED" in audit
    assert "CW-SOURCE-ID-001 — PASS" in audit
    assert "CW-SYNC-001 — PASS" in audit
    assert "CW-MEDIA-001 — PASS" in audit
    assert "CW-HASH-001 — PASS" in audit
