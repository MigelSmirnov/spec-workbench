"""Runtime acceptance oracle for Stage 7.1 Flow 5.

The Factory project supplies the ``semantic_runtime`` pytest fixture. The fixture
binds these implementation-independent scenarios to generated public operations
without changing the assertions below.
"""


def _eligible_card(semantic_runtime):
    return semantic_runtime.eligible_holded_invoice_revision(
        invoice_id="INV-H-1",
        content_hash="card-hash-h1",
        supplier_name="Proveedor Uno",
        supplier_invoice_number="FAC-100",
        document_date="2026-08-13",
        currency="EUR",
        lines=[
            {"name": "Material A", "quantity": "2", "tax": "21", "gross": "121.00"},
            {"name": "Material B", "quantity": "1", "tax": "10", "gross": "55.00"},
        ],
        gross_total="176.00",
        source_complete=True,
        project_assignment_resolved=True,
    )


def test_clear_create_requires_exact_document_readback_before_success(semantic_runtime):
    card = _eligible_card(semantic_runtime)
    before = semantic_runtime.card_snapshot(card)

    semantic_runtime.holded_create_result(document_id="DOC-1", outcome="success")
    semantic_runtime.holded_document(
        document_id="DOC-1",
        supplier_name="Proveedor Uno",
        supplier_invoice_number="FAC-100",
        document_date="2026-08-13",
        currency="EUR",
        lines=[
            {"name": "Material A", "quantity": "2", "tax": "21"},
            {"name": "Material B", "quantity": "1", "tax": "10"},
        ],
        gross_total="176.00",
        raw_status=7,
    )

    publication = semantic_runtime.request_holded_publication(card)

    assert semantic_runtime.holded_post_count() == 1
    assert semantic_runtime.holded_get_count(document_id="DOC-1") == 1
    assert publication.is_verified_success is True
    assert publication.holded_document_id == "DOC-1"
    assert publication.invoice_revision_hash == "card-hash-h1"
    assert semantic_runtime.card_snapshot(card) == before
    assert semantic_runtime.interpreted_holded_status("DOC-1") is None


def test_clear_create_business_mismatch_is_not_publication_success_and_never_reposts(semantic_runtime):
    card = _eligible_card(semantic_runtime)
    before = semantic_runtime.card_snapshot(card)

    semantic_runtime.holded_create_result(document_id="DOC-2", outcome="success")
    semantic_runtime.holded_document(
        document_id="DOC-2",
        supplier_name="Proveedor Uno",
        supplier_invoice_number="FAC-100",
        document_date="2026-08-13",
        currency="EUR",
        lines=[
            {"name": "Material A", "quantity": "2", "tax": "21"},
            {"name": "Material B", "quantity": "1", "tax": "10"},
        ],
        gross_total="176.02",
        raw_status=7,
    )

    publication = semantic_runtime.request_holded_publication(card)

    assert semantic_runtime.holded_post_count() == 1
    assert semantic_runtime.holded_get_count(document_id="DOC-2") == 1
    assert publication.is_verified_success is False
    assert publication.requires_reconciliation is True
    assert semantic_runtime.card_snapshot(card) == before


def test_ambiguous_create_uses_read_only_marker_recovery_and_verified_unique_candidate(semantic_runtime):
    card = _eligible_card(semantic_runtime)
    before = semantic_runtime.card_snapshot(card)

    semantic_runtime.holded_create_result(outcome="ambiguous")
    marker = semantic_runtime.expected_holded_attempt_marker(card)
    semantic_runtime.holded_marker_matches(marker, ["DOC-RECOVERED"])
    semantic_runtime.holded_document(
        document_id="DOC-RECOVERED",
        supplier_name="Proveedor Uno",
        supplier_invoice_number="FAC-100",
        document_date="2026-08-13",
        currency="EUR",
        lines=[
            {"name": "Material A", "quantity": "2", "tax": "21"},
            {"name": "Material B", "quantity": "1", "tax": "10"},
        ],
        gross_total="176.00",
        raw_status=11,
    )

    pending = semantic_runtime.request_holded_publication(card)
    settled = semantic_runtime.reconcile_holded_publication(pending)

    assert semantic_runtime.holded_post_count() == 1
    assert semantic_runtime.holded_mutation_count_after_create() == 0
    assert settled.is_verified_success is True
    assert settled.holded_document_id == "DOC-RECOVERED"
    assert semantic_runtime.card_snapshot(card) == before
    assert semantic_runtime.interpreted_holded_status("DOC-RECOVERED") is None


def test_zero_multiple_or_mismatched_recovery_candidates_never_settle_success(semantic_runtime):
    for case, matches, mismatch in (
        ("zero", [], False),
        ("multiple", ["DOC-A", "DOC-B"], False),
        ("mismatch", ["DOC-X"], True),
    ):
        semantic_runtime.reset_holded_gateway()
        card = _eligible_card(semantic_runtime)
        semantic_runtime.holded_create_result(outcome="ambiguous")
        marker = semantic_runtime.expected_holded_attempt_marker(card)
        semantic_runtime.holded_marker_matches(marker, matches)
        if mismatch:
            semantic_runtime.holded_document(
                document_id="DOC-X",
                supplier_name="Proveedor Uno",
                supplier_invoice_number="FAC-100",
                document_date="2026-08-13",
                currency="EUR",
                lines=[
                    {"name": "Material A", "quantity": "2", "tax": "21"},
                    {"name": "Material B", "quantity": "1", "tax": "10"},
                ],
                gross_total="999.99",
                raw_status=3,
            )

        pending = semantic_runtime.request_holded_publication(card)
        settled = semantic_runtime.reconcile_holded_publication(pending)

        assert semantic_runtime.holded_post_count() == 1, case
        assert semantic_runtime.holded_mutation_count_after_create() == 0, case
        assert settled.is_verified_success is False, case
        assert settled.outcome in {
            "outcome_unknown",
            "duplicate_conflict",
            "reconciliation_required",
        }, case
