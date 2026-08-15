from __future__ import annotations

from pathlib import Path

from module_review_workbench import build_slice, list_modules, review
from module_review_workbench.model import ModuleReviewError

ROOT = Path(__file__).resolve().parents[1]
CABINET = ROOT / "examples" / "cabinet-backend"

def test_lists_final_assembled_modules() -> None:
    report = list_modules(CABINET)
    assert report["schema_version"] == "spec_workbench_module_review_modules.v1"
    assert report["modules"] == [
        "models", "access_control", "durable_archive", "registry_context",
        "holded_gateway", "synchronization", "plan_actual",
        "holded_publication", "retention_release", "api_irregular", "api",
        "bootstrap",
    ]

def test_durable_archive_slice_connects_business_and_lowered_spec() -> None:
    packet = build_slice(CABINET, "durable_archive")
    assert packet["schema_version"] == "spec_workbench_module_review_slice.v1"
    assert packet["accepted_evidence"]["decisions"]
    assert packet["accepted_evidence"]["flows"]
    assert packet["accepted_evidence"]["public_operations"]
    assert "accept_transfer_manifest" in packet["lowered_specification"]["contracts"]
    assert "InvoiceTransferManifest" in packet["lowered_specification"]["models"]
    assert set(packet["lowered_specification"]["persistence"]) == {
        "StoredInvoiceCard", "StoredInvoiceCardRevision", "InvoiceCardValidationRecord",
        "DuplicateCandidateReview", "SourceBinary", "SourceBinaryReplica",
        "InvoiceTransferManifest", "InvoiceImport", "ImportQuarantine",
        "InvoiceTransferReceipt", "IncompleteSourceAcceptance", "SourceLossDecision",
        "ArchiveBytePublication",
    }
    assert packet["generation_constraints"]["note_count"] >= 10

def test_review_uses_all_assembled_notes() -> None:
    report = review(CABINET, "durable_archive")
    assert report["schema_version"] == "spec_workbench_module_review.v1"
    assert report["summary"]["contracts"] >= 7
    assert report["summary"]["assembled_notes"] > 0
    assert report["summary"]["blocks"] == 0
    assert report["semantic_review_required"] is True

def test_transport_module_without_state3_owner_still_slices() -> None:
    packet = build_slice(CABINET, "api")
    assert packet["accepted_evidence"]["responsibility"] is None
    assert packet["lowered_specification"]["routes"]

def test_dependency_contracts_expand_context_without_rewriting_import_edges() -> None:
    packet = build_slice(CABINET, "holded_publication")
    lowered = packet["lowered_specification"]
    assert {
        "create_holded_purchase", "get_archived_invoice", "lookup_holded_purchase",
        "HoldedGatewayService.__init__",
        "HoldedGatewayService.create_holded_purchase",
        "HoldedGatewayService.lookup_holded_purchase",
    } <= set(lowered["dependency_contracts"])
    assert {
        "HoldedPublicationAttempt", "HoldedPurchaseAttemptPayload",
        "HoldedPurchaseLookupEvidence", "StoredInvoiceCardRevision",
    } <= set(lowered["models"])
    assert lowered["dependencies"]["models"] == [
        "HoldedPublication", "AuthorizationDecision",
    ]

def test_models_slice_includes_owned_declarations_and_state1_evidence() -> None:
    packet = build_slice(CABINET, "models")
    lowered_models = set(packet["lowered_specification"]["models"])
    state1_models = {
        model["name"] for model in packet["accepted_evidence"]["state1_models"]
    }
    assert state1_models <= lowered_models
    assert lowered_models == state1_models
    assert {
        "VpsReleaseDecision", "ArchiveBytePublication",
        "HoldedRemotePurchaseDocument", "VpsInvoiceTransferPackage",
        "VpsConnectionObservation",
    } <= lowered_models

def test_unknown_assembled_module_fails_closed() -> None:
    try:
        build_slice(CABINET, "invented")
    except ModuleReviewError as error:
        assert str(error) == "Unknown assembled module: invented"
    else:
        raise AssertionError("Unknown module must fail closed.")
