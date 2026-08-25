"""Stage 7.1 runtime acceptance oracle for Flow 1.

These tests are authored from semantic-closed scenarios before implementation.
They intentionally depend on a project-provided ``semantic_runtime`` pytest
fixture rather than importing generated implementation modules directly.

The runtime binding is allowed to adapt public generated APIs to this test
protocol. It must not weaken, reinterpret, or rewrite the assertions below.
"""

from __future__ import annotations


FLOW_ID = "flow:synchronize_invoice_to_local_archive"


def test_successful_transfer_requires_archive_acceptance_and_durable_verification(semantic_runtime):
    """S1: delivery alone is never the terminal accepted business outcome."""
    case = semantic_runtime.flow1_case(
        transport="delivered",
        archive="accepted",
    )

    result = semantic_runtime.synchronize_invoice_to_local_archive(case)

    assert result.transport_delivered is True
    assert result.archive_acceptance_attempted is True
    assert result.archive_receipt_state in {"accepted", "already_accepted"}
    assert result.durable_verification_attempted is True
    assert result.durable_acceptance_proved is True
    assert result.transport_evidence_is_acceptance_proof is False


def test_ambiguous_transport_remains_reconcilable_without_fabricated_acceptance(semantic_runtime):
    """S2: an unknown transport outcome cannot manufacture archive truth."""
    case = semantic_runtime.flow1_case(transport="ambiguous")

    result = semantic_runtime.synchronize_invoice_to_local_archive(case)

    assert result.transport_outcome in {"unknown", "ambiguous", "unresolved"}
    assert result.reconciliation_required is True
    assert result.archive_acceptance_attempted is False
    assert result.durable_acceptance_proved is False
    assert result.correlation_identity_preserved is True


def test_rejected_archive_evidence_never_becomes_partial_normal_acceptance(semantic_runtime):
    """S3: classified archive refusal cannot leak a partial accepted set."""
    case = semantic_runtime.flow1_case(
        transport="delivered",
        archive="rejected_integrity",
    )

    result = semantic_runtime.synchronize_invoice_to_local_archive(case)

    assert result.archive_acceptance_attempted is True
    assert result.archive_receipt_state in {
        "rejected",
        "quarantined",
        "incomplete",
        "conflicting",
        "duplicate_review",
    }
    assert result.normal_archive_truth_created is False
    assert result.durable_acceptance_proved is False


def test_repeated_equivalent_archive_acceptance_is_idempotent(semantic_runtime):
    """S4: replay of equivalent accepted evidence creates no second acceptance."""
    case = semantic_runtime.flow1_case(
        transport="delivered",
        archive="already_accepted",
    )

    first = semantic_runtime.synchronize_invoice_to_local_archive(case)
    second = semantic_runtime.synchronize_invoice_to_local_archive(case)

    assert second.archive_receipt_state in {"accepted", "already_accepted"}
    assert second.logical_acceptance_identity == first.logical_acceptance_identity
    assert second.logical_acceptance_count == first.logical_acceptance_count
    assert second.durable_acceptance_proved is True
