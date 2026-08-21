from __future__ import annotations

from pathlib import Path

import yaml

from cabinet_web_checkout_sync_adapter import (
    EXPECTED_SCHEMA_BLOB_SHA,
    EXPECTED_SERVICE_BLOB_SHA,
    EXPECTED_VALIDATOR_BLOB_SHA,
)
from cabinet_web_revision_accept_runtime import (
    CAPABILITY,
    canonical_content_hash,
)
from cabinet_web_revision_accept_runtime_probe import run_probe


ROOT = Path(__file__).resolve().parents[1]
EXTENSION = ROOT / "experiments" / "cabinet-vault" / "cabinet_web_sync_box_extension_v1.yaml"
BASE_BOX = ROOT / "experiments" / "cabinet-vault" / "cabinet_backend_box_v0.yaml"
RUNTIME = ROOT / "tools" / "cabinet_web_revision_accept_runtime.py"
ADAPTER = ROOT / "tools" / "cabinet_web_checkout_sync_adapter.py"


def load(path: Path):
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_sync_extension_declares_new_revision_ingress_without_reenabling_classical_manifest_ingest():
    extension = load(EXTENSION)
    base = load(BASE_BOX)

    capability = extension["capabilities"]["invoice.archive.accept_revision"]
    assert CAPABILITY == "invoice.archive.accept_revision"
    assert capability["input"] == "CabinetWebInvoiceRevisionDelivery"
    assert capability["output"] == "CabinetBackendInvoiceRevisionReceipt"
    assert set(capability["effects"]) == {
        "archive_revision_write",
        "archive_source_expectation_write",
    }
    assert extension["classical_transfer_boundary"]["InvoiceTransferManifest_ingest_reenabled"] is False
    assert base["experiment_boundaries"]["archive_transfer_ingest_in_this_slice"] is False


def test_sync_extension_pins_reviewed_cabinet_web_executable_contract():
    extension = load(EXTENSION)
    fingerprints = extension["source_contract"]["reviewed_contract_fingerprints"]
    assert fingerprints == {
        "invoice_validation_py": EXPECTED_VALIDATOR_BLOB_SHA,
        "invoice_card_v1_schema_json": EXPECTED_SCHEMA_BLOB_SHA,
        "invoice_service_py": EXPECTED_SERVICE_BLOB_SHA,
    }


def test_runtime_does_not_import_classical_transport_or_web_runtime_ownership():
    text = RUNTIME.read_text(encoding="utf-8")
    forbidden = (
        "InvoiceTransferManifest",
        "InvoiceSynchronization",
        "DurableArchiveService",
        "RegistryClient",
        "FastAPI",
        "from tools.invoice_validation",
        "Cabinet_web.tools",
    )
    assert all(item not in text for item in forbidden)


def test_local_checkout_adapter_invokes_pinned_web_validator_as_disposable_boundary():
    text = ADAPTER.read_text(encoding="utf-8")
    assert "invoice_validation.py" in text
    assert "subprocess.run" in text
    assert "git_blob_sha" in text
    assert "git", "-C"
    assert "build_delivery_from_checkout" in text


def test_canonical_hash_matches_sync_contract_serialization():
    card = {"z": "á", "a": {"b": 1}}
    first = canonical_content_hash(card)
    second = canonical_content_hash({"a": {"b": 1}, "z": "á"})
    assert first == second
    assert first.startswith("sha256:")
    assert len(first) == 71


def test_runtime_probe_fails_closed_without_postgres_configuration():
    report = run_probe({})
    assert report.status == "block"
    assert len(report.results) == 4
    assert {item.status for item in report.results} == {"UNVERIFIED"}
