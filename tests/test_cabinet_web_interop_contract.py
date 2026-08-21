from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "experiments" / "cabinet-vault" / "cabinet_web_interop_audit_v0.yaml"


def load():
    value = yaml.safe_load(AUDIT.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_audit_is_pinned_to_reviewed_cabinet_web_main_state():
    audit = load()
    source = audit["source_repository"]

    assert source["repository"] == "MigelSmirnov/Cabinet_web"
    assert source["ref"] == "main"
    assert source["commit_sha"] == "63f1752dc09be93156c6e7bf45f3c80e6c7f8387"
    assert source["reviewed_on"] == "2026-08-21"
    assert source["artifacts"] == {
        "architecture/README.md": "388a7e22e852616c57da438d5a7ee4a5b7f4a6bc",
        "architecture/app-architecture.yaml": "0a205c6fdec5b19001647ecea0981330cec1119e",
        "docs/01-storage/INVOICE_CARD_FORMAT.md": "fd0d5ea53d39798a8a8d1c8768fda2d106fd994c",
        "docs/02-tools/INVOICE_WORKFLOW.md": "2292211ec763f3fa3e31b178307b28eebf6cd6dc",
        "docs/02-tools/INVOICE_TOOLS_MODEL.md": "789708a756206faf26d0260611eb8f73fb327003",
        "schemas/invoice-card-v1.schema.json": "670d493cd32430f420678dea9489a2fec7cf9124",
        "tools/invoice_validation.py": "1a29a9ea9623222e4246eb23d7477e9f25f3637e",
        "tools/invoice_evidence_service.py": "b0a3951244550e5d20b4b84225a6e62b836db459",
        "tests/fixtures/invoices/obramat-cash/card.json": "089cc56fa2133bdee3cb89710a393b99d01100ef",
        "tests/test_invoice_evidence_service.py": "3101f1d64d41cc60db54854de7b2ce3d990268c9",
    }


def test_real_cabinet_web_canary_is_blocked_by_exact_known_findings():
    audit = load()
    gate = audit["gate"]
    findings = {item["id"]: item for item in audit["findings"]}

    assert gate["isolated_box_runtime_evidence"] == "PASS"
    assert gate["cabinet_web_interop_gate"] == "block"
    assert gate["real_cabinet_web_canary"] == "forbidden_until_blockers_closed"
    assert gate["blocking_findings"] == [
        "CW-SOURCE-ID-001",
        "CW-SYNC-001",
        "CW-MEDIA-001",
        "CW-HASH-001",
    ]
    assert {
        finding_id
        for finding_id, finding in findings.items()
        if finding["severity"] == "BLOCK"
    } == set(gate["blocking_findings"])


def test_source_identity_drift_belongs_to_upstream_card_contract_not_backend_adapter():
    audit = load()
    finding = next(item for item in audit["findings"] if item["id"] == "CW-SOURCE-ID-001")

    assert finding["class"] == "UPSTREAM_CONTRACT_DRIFT"
    assert finding["owner"] == "Cabinet_web/card-contracts"
    forbidden = set(finding["forbidden_resolution"])
    assert "generate_source_id_inside_backend_adapter" in forbidden
    assert "infer_source_identity_from_filename" in forbidden
    assert "infer_source_identity_from_payment_source_ref_without_contract" in forbidden


def test_lifecycle_and_authority_split_are_already_aligned():
    audit = load()
    findings = {item["id"]: item for item in audit["findings"]}

    assert findings["CW-LIFECYCLE-001"]["class"] == "ALIGNED_SPLIT"
    assert findings["CW-LIFECYCLE-001"]["severity"] == "PASS"
    assert findings["CW-AUTHORITY-001"]["class"] == "ALIGNED"
    assert findings["CW-AUTHORITY-001"]["severity"] == "PASS"


def test_media_mapping_cannot_use_kind_or_filename_as_signature_proof():
    audit = load()
    finding = next(item for item in audit["findings"] if item["id"] == "CW-MEDIA-001")

    assert finding["class"] == "LOWERING_GAP"
    assert set(finding["forbidden_resolution"]) == {
        "map_photo_to_JPEG_unconditionally",
        "trust_filename_extension",
        "trust_caller_MIME_without_parser_validation",
    }


def test_external_fingerprint_refresh_is_required_before_interop_claim_changes():
    audit = load()
    policy = audit["change_policy"]

    assert policy["Cabinet_web_source_contract_change_requires_connector_review"] is True
    assert policy["source_repository_fingerprint_drift"] == "block_and_refresh_audit"
    assert policy["backend_adapter_may_not_resolve_upstream_contract_drift"] is True
    assert policy["real_Cabinet_web_data_may_not_enter_box_until_interop_gate_passes"] is True
