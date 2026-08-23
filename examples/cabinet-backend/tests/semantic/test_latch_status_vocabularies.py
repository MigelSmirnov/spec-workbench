"""Regression latches for status vocabularies closed as enums.

Each assertion below names a value that regenerations of the same accepted
spec used to disagree on (found by experimental/regeneration_diff.py). The
spec now fixes the value through a `kind: enum` model or a `rules.*` address;
the test binds that decision to observable runtime behaviour through the
project-provided ``semantic_runtime`` fixture.
"""

from __future__ import annotations


def test_delivered_transfer_latches_synchronization_and_receipt_vocabulary(semantic_runtime):
    """SynchronizationStatus: a delivered transfer is exactly `delivered`;
    TransferReceiptResult: a first archive acceptance is exactly `accepted`."""
    case = semantic_runtime.flow1_case(transport="delivered", archive="accepted")

    result = semantic_runtime.synchronize_invoice_to_local_archive(case)

    assert result.transport_outcome == "delivered"
    assert result.archive_receipt_state == "accepted"


def test_ambiguous_transfer_latches_unknown_outcome(semantic_runtime):
    """SynchronizationStatus: transport ambiguity is `unknown_outcome`, never a
    fabricated terminal value."""
    case = semantic_runtime.flow1_case(transport="ambiguous")

    result = semantic_runtime.synchronize_invoice_to_local_archive(case)

    assert result.transport_outcome == "unknown"
    assert result.archive_receipt_state not in {"accepted", "already_accepted"}


def test_assignment_validation_latches_review_results(semantic_runtime):
    """AssignmentValidationResult: active match is rules.registry_context.active_exact_match_result,
    archived project is rules.registry_context.archived_project_result,
    missing project is rules.registry_context.missing_project_result."""
    card = semantic_runtime.immutable_card_revision(
        invoice_id="INV-L1", content_hash="latch-hash", project_id="P1"
    )
    project = {"project_id": "P1", "display_name": "Project", "address": "A", "status": "active"}

    semantic_runtime.set_registry_observation(projects=[project])
    assert semantic_runtime.validate_card_assignment(card).result == "valid"

    semantic_runtime.set_registry_observation(projects=[dict(project, status="archived")])
    archived = semantic_runtime.validate_card_assignment(card)
    assert archived.result == "project_closed"
    assert archived.requires_review is True

    unknown_card = semantic_runtime.immutable_card_revision(
        invoice_id="INV-L2", content_hash="latch-hash-2", project_id="P-never-observed"
    )
    missing = semantic_runtime.validate_card_assignment(unknown_card)
    assert missing.result == "project_missing"
    assert missing.requires_review is True


def test_malformed_token_is_refused_before_any_throttle_or_audit_row(semantic_runtime):
    """A ValueError from parse_service_token is converted to AuthenticationRequiredError
    before the transaction begins; no audit evidence is written for a token without a
    credential id."""
    import pytest

    before = len(semantic_runtime.audit_records())
    with pytest.raises(semantic_runtime.AuthenticationRequiredError):
        semantic_runtime.authenticate("not-a-token")
    assert len(semantic_runtime.audit_records()) == before
