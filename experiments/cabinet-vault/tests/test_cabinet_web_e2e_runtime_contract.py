from __future__ import annotations

from pathlib import Path

import yaml

from cabinet_web_e2e_runtime_probe import run_probe


ROOT = Path(__file__).resolve().parents[3]
EXTENSION = ROOT / "experiments" / "cabinet-vault" / "cabinet_web_sync_box_extension_v1.yaml"
E2E = ROOT / "experiments" / "cabinet-vault" / "tools" / "cabinet_web_e2e_runtime_probe.py"


def load():
    value = yaml.safe_load(EXTENSION.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_extension_declares_revision_receipt_then_source_attach_sequence():
    extension = load()
    assert extension["real_data_canary_gate"]["sequence"] == [
        "build_delivery_from_Cabinet_web_checkout",
        "accept_revision_and_obtain_receipt",
        "attach_source_bytes_through_verified_adapter",
        "verify_Card_revision_unchanged",
        "verify_local_source_evidence_and_audit",
    ]


def test_e2e_probe_uses_same_backend_invoice_state_for_sync_and_attach():
    text = E2E.read_text(encoding="utf-8")
    assert "CabinetWebRevisionAcceptExecutor" in text
    assert "CabinetWebSourceAttachAdapter" in text
    assert "records=records" in text
    assert "accepted_card_content_hash" in text
    assert "accepted_card_document" in text
    assert "cabinet_web.revision.accept" in text
    assert "invoice.source.attach" in text


def test_e2e_probe_fails_closed_without_backend_runtime_configuration():
    report = run_probe({})
    assert report.status == "block"
    assert len(report.results) == 1
    assert report.results[0].probe_id == "WEB-E2E-001"
    assert report.results[0].status == "UNVERIFIED"
