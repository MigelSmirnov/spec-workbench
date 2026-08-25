"""Stage 7.1 runtime acceptance oracle for Flow 2.

The project-provided ``semantic_runtime`` fixture binds generated public APIs to
this implementation-independent oracle. The assertions are authored from the
semantic-closed specification and must not be weakened to match generated code.
"""

from __future__ import annotations


def test_valid_attachment_changes_source_evidence_not_invoice_revision(semantic_runtime):
    """A1: accepted local source evidence must not rewrite immutable Card facts."""
    case = semantic_runtime.flow2_case(
        invoice="accepted",
        files=("valid_photo",),
    )

    before = semantic_runtime.invoice_revision_fingerprint(case)
    result = semantic_runtime.accept_local_source_attachment(case)
    after = semantic_runtime.invoice_revision_fingerprint(case)

    assert result.item_results == ("attached",)
    assert result.source_available is True
    assert before == after


def test_unknown_invoice_raises_without_creating_placeholder_state(semantic_runtime):
    """A2: an unresolved stable invoice target is a hard target-resolution error."""
    case = semantic_runtime.flow2_case(
        invoice="missing",
        files=("valid_photo",),
    )

    error = semantic_runtime.capture_error(
        lambda: semantic_runtime.accept_local_source_attachment(case)
    )

    assert error.type_name == "InvoiceNotFoundError"
    assert semantic_runtime.placeholder_invoice_created(case) is False
    assert semantic_runtime.placeholder_source_state_created(case) is False


def test_repeated_identical_bytes_are_idempotent_and_preserve_provenance(semantic_runtime):
    """A3: equivalent content reuses accepted source identity without replacement."""
    case = semantic_runtime.flow2_case(
        invoice="accepted",
        files=("valid_photo",),
    )

    first = semantic_runtime.accept_local_source_attachment(case)
    provenance_before = semantic_runtime.source_provenance(case)
    replica_count_before = semantic_runtime.source_binary_replica_count(case)

    second = semantic_runtime.accept_local_source_attachment(case)

    assert second.item_results[0] in {"attached", "already_attached"}
    assert semantic_runtime.source_binary_replica_count(case) == replica_count_before
    assert semantic_runtime.source_provenance(case).preserves(provenance_before)
    assert second.source_identity == first.source_identity


def test_mixed_batch_preserves_valid_sibling_and_reports_rejected_item(semantic_runtime):
    """Stage 7.1 repair: file-local rejection must not abort a valid sibling."""
    case = semantic_runtime.flow2_case(
        invoice="accepted",
        files=("valid_photo", "hash_mismatch_pdf"),
    )

    result = semantic_runtime.accept_local_source_attachment(case)

    assert result.item_results == ("attached", "rejected")
    assert semantic_runtime.valid_source_is_accepted(case, index=0) is True
    assert semantic_runtime.rejected_source_replaced_existing_evidence(case, index=1) is False


def test_irregular_http_handler_remains_transport_only(semantic_runtime):
    """A4: multipart lowering may not duplicate archive or authorization policy."""
    observation = semantic_runtime.observe_flow2_http_boundary(
        invoice="accepted",
        files=("valid_photo",),
    )

    assert observation.multipart_transformation_performed is True
    assert observation.authorization_delegated is True
    assert observation.archive_policy_delegated is True
    assert observation.persistence_policy_in_handler is False
    assert observation.source_acceptance_policy_in_handler is False
