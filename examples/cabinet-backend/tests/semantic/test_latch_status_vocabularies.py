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


def test_match_proposals_follow_the_declared_heuristic(semantic_runtime):
    """rules.plan_actual.proposal_*: unit and currency must match; score = 0.5 for equal
    quantity + 0.5 * unit-price proximity; ordered by score desc; descriptions ignored."""
    from decimal import Decimal

    scenario = semantic_runtime.plan_actual_scenario(
        project_id="P-proposals",
        estimate_items=[
            {"estimate_item_id": "A", "quantity": Decimal("10"), "unit": "m2", "currency": "EUR", "monetary_basis": "net", "total": Decimal("100.00")},
            {"estimate_item_id": "B", "quantity": Decimal("5"), "unit": "kg", "currency": "EUR", "monetary_basis": "net", "total": Decimal("50.00")},
            {"estimate_item_id": "C", "quantity": Decimal("4"), "unit": "m2", "currency": "EUR", "monetary_basis": "net", "total": Decimal("200.00")},
        ],
        invoice_lines=[
            {"invoice_line_id": "L1", "quantity": Decimal("10"), "unit": "m2", "currency": "EUR", "monetary_basis": "net", "total": Decimal("110.00")},
        ],
        confirmed_matches=[],
    )

    proposals = semantic_runtime.propose_line_matches(scenario)

    assert [p.estimate_item_id for p in proposals] == ["A", "C"]
    first, second = proposals
    assert first.score == Decimal("0.9545")
    assert set(str(getattr(c, "value", c)) for c in first.reason_codes) == {"unit_match", "currency_match", "quantity_equal", "unit_price_close"}
    assert second.score == Decimal("0.1100")  # 1 - |11 - 50| / 50 = 0.22
    assert set(str(getattr(c, "value", c)) for c in second.reason_codes) == {"unit_match", "currency_match"}
