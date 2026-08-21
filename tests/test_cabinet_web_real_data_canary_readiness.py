from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
READINESS = ROOT / "experiments" / "cabinet-vault" / "cabinet_web_real_data_canary_readiness_v1.yaml"
F260001_TASK = ROOT / "experiments" / "cabinet-vault" / "LOCAL_AGENT_F260001_REAL_CANARY_TASK.md"
BRIDGE_TASK = ROOT / "experiments" / "cabinet-vault" / "LOCAL_AGENT_AUTHORIZED_CAPABILITY_BRIDGE_TASK.md"
CONNECTION_EVIDENCE = ROOT / "experiments" / "cabinet-vault" / "F260001_REAL_CANARY_CONNECTION_PREFLIGHT_EVIDENCE_2026-08-21.md"


def load():
    value = yaml.safe_load(READINESS.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_real_candidate_is_ready_but_authorized_local_connection_is_the_only_current_block():
    readiness = load()
    assert readiness["readiness_id"] == "cabinet_web_real_data_canary.v6"
    assert readiness["status"] == "blocked_authorized_backend_connection_unavailable"
    assert readiness["real_candidate"]["readiness"] == "PASS"
    assert readiness["blocking_condition"] == {
        "id": "CW-LOCAL-CONNECTION-001",
        "class": "AUTHORIZED_CAPABILITY_TRANSPORT_UNAVAILABLE",
        "statement": readiness["blocking_condition"]["statement"],
        "owner": "local_box_host_wiring",
        "severity": "BLOCK",
    }


def test_f260001_is_pinned_to_merged_cabinet_web_main_revision():
    readiness = load()
    source = readiness["source_repository"]
    candidate = readiness["real_candidate"]

    assert source["repository"] == "MigelSmirnov/Cabinet_web"
    assert source["ref"] == "main"
    assert source["current_head_commit_sha"] == "d3fac8e5d2b85c12904cba24060717b84e2757c2"
    assert source["normalization_pull_request"] == 17
    assert source["contract_fingerprints_changed"] is False

    assert candidate["invoice_id"] == "invoice-f260001"
    assert candidate["invoice_card_path"] == "data/cards/invoice-f260001/card.json"
    assert candidate["status"] == "confirmed"
    assert candidate["source_id"] == "source-f260001"
    assert candidate["source_kind"] == "pdf"
    assert candidate["card_content_hash"] == "sha256:e52e9d1fe3ff273b1510fd45d516daf576df4404320f75db4dfabc51c8f8a0cf"
    assert candidate["source_git_commit_sha"] == "386134cbb28e3689fec8ffb49815db9416ebe9a8"
    assert candidate["real_pdf_local_sha256"] == "sha256:b1ad4b4f15ddcba8c91f0f2d17f8a45ab58fd4febcd1064360aed758f14dec66"
    assert candidate["validation"] == {"status": "PASS", "errors": 0, "warnings": 0}


def test_latest_local_preflight_stopped_before_every_backend_effect():
    preflight = load()["latest_local_preflight"]
    assert preflight["result"] == "PASS_FAIL_CLOSED_AUTHORIZED_CONNECTION_UNAVAILABLE"
    assert preflight["delivery_created"] is False
    assert preflight["backend_invocation_performed"] is False
    assert preflight["postgres_effect_performed"] is False
    assert preflight["source_attachment_performed"] is False
    assert preflight["parser_validation_performed"] is False
    assert preflight["acceptance_audit_present"] is False
    assert preflight["attachment_audit_present"] is False
    assert preflight["card_unchanged"] is True
    assert CONNECTION_EVIDENCE.is_file()


def test_connection_repair_preserves_both_executor_authority_boundaries():
    repair = load()["required_connection_repair"]
    assert "preserve_SYNCHRONIZATION_BOUNDARY_for_invoice.archive.accept_revision" in repair["authority"]
    assert "preserve_LOCAL_AGENT_BOUNDARY_for_invoice.source.attach" in repair["authority"]
    assert "grant_resource_scope_exactly_invoice:invoice-f260001_for_the_canary" in repair["authority"]
    assert "use_verified_PostgresRecordKernel" in repair["providers"]
    assert "use_verified_LocalPrivateByteVault" in repair["providers"]
    assert "use_ProtectedConfigurationKernel_or_equivalent_host_owned_secret_resolution" in repair["providers"]


def test_no_direct_database_preflight_read_is_required_for_first_delivery():
    readiness = load()
    rule = readiness["base_revision_rule"]
    assert "base_backend_content_hash may be null" in rule
    assert "reconciliation_required" in rule
    assert "perform no overwrite" in rule


def test_bridge_task_is_narrow_and_forbids_authority_bypass():
    text = BRIDGE_TASK.read_text(encoding="utf-8")
    assert "invoice.archive.accept_revision" in text
    assert "invoice.source.attach" in text
    assert "local_tool" in text
    assert "Do not route the real canary through `cabinet_host.py` or `cabinet_graph_host.py`" in text
    assert "The bridge must not call protected executor internals that bypass `AuthorityKernel.invoke()`" in text
    assert "invoice:invoice-f260001" in text
    assert "Do not add arbitrary SQL" in text
    assert F260001_TASK.is_file()
