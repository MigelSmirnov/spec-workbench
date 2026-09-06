from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from cabinet_boundary_audit import (
    CLASS_DISPOSITIONS,
    KEEP_AND_CLOSE_IN_CABINET_SEMANTIC_SPEC,
    MOVE_TO_GENERIC_HOST_LOWERING,
    REMOVE_FROM_CABINET_PRODUCT_SPEC,
    SUPPORTED_EVIDENCE_VERSION,
    audit_evidence,
    audit_path,
)


ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "experiments" / "cabinet-vault" / "generated_backend_failure_evidence_v0.yaml"


def finding(
    finding_id: str,
    finding_class: str,
    *,
    status: str | None = "PASS",
    required: bool = True,
    summary: str = "Synthetic audit evidence.",
):
    verification = {"required": required}
    if status is not None:
        verification["status"] = status
    return {
        "id": finding_id,
        "summary": summary,
        "finding_class": finding_class,
        "evidence": ["synthetic test evidence"],
        "verification": verification,
    }


def definition(*findings):
    return {
        "evidence_version": SUPPORTED_EVIDENCE_VERSION,
        "findings": list(findings),
    }


def test_audit_supports_the_handoff_classes_with_three_explicit_dispositions():
    assert CLASS_DISPOSITIONS == {
        "LANGUAGE_RELATION_GAP": MOVE_TO_GENERIC_HOST_LOWERING,
        "PROJECTION_GAP": MOVE_TO_GENERIC_HOST_LOWERING,
        "VERIFICATION_NOT_EXECUTED": MOVE_TO_GENERIC_HOST_LOWERING,
        "BOUNDARY_LEAK": REMOVE_FROM_CABINET_PRODUCT_SPEC,
        "LOWERING_GAP": MOVE_TO_GENERIC_HOST_LOWERING,
        "AUTHORITY_SEMANTIC_GAP": KEEP_AND_CLOSE_IN_CABINET_SEMANTIC_SPEC,
        "DOMAIN_SEMANTIC_GAP": KEEP_AND_CLOSE_IN_CABINET_SEMANTIC_SPEC,
    }


def test_real_generated_backend_evidence_is_classified_without_repairing_code():
    report = audit_path(EVIDENCE)

    assert report.status == "classified"
    assert report.verification_gate == "block"
    assert report.issues == ()

    by_id = {item.finding_id: item for item in report.findings}
    assert by_id["interface-relation-missing"].disposition == MOVE_TO_GENERIC_HOST_LOWERING
    assert by_id["psycopg-projection-lost"].disposition == MOVE_TO_GENERIC_HOST_LOWERING
    assert by_id["external-boundary-stub-concentration"].disposition == REMOVE_FROM_CABINET_PRODUCT_SPEC
    assert by_id["authority-construction-mismatch"].disposition == KEEP_AND_CLOSE_IN_CABINET_SEMANTIC_SPEC
    assert by_id["plan-actual-domain-unresolved"].disposition == KEEP_AND_CLOSE_IN_CABINET_SEMANTIC_SPEC
    assert by_id["retention-release-domain-unresolved"].disposition == KEEP_AND_CLOSE_IN_CABINET_SEMANTIC_SPEC


def test_required_skip_is_normalized_to_unverified_and_blocks_gate():
    report = audit_evidence(
        definition(
            finding(
                "verification-skipped",
                "VERIFICATION_NOT_EXECUTED",
                status="SKIP",
            )
        )
    )

    assert report.status == "classified"
    assert report.findings[0].declared_verification_status == "SKIP"
    assert report.findings[0].verification_status == "UNVERIFIED"
    assert report.verification_gate == "block"


def test_missing_required_verification_status_is_unverified_not_pass():
    report = audit_evidence(
        definition(
            finding(
                "verification-missing",
                "LOWERING_GAP",
                status=None,
            )
        )
    )

    assert report.status == "classified"
    assert report.findings[0].declared_verification_status is None
    assert report.findings[0].verification_status == "UNVERIFIED"
    assert report.verification_gate == "block"


def test_unknown_class_is_invalid_and_is_not_guessed_from_product_names():
    report = audit_evidence(
        definition(
            finding(
                "unknown",
                "HOLDED_HTTP_PROBLEM",
                summary="Holded HTTP client is stubbed.",
            )
        )
    )

    assert report.status == "invalid"
    assert report.verification_gate == "block"
    assert report.findings == ()
    assert any(issue.code == "UNKNOWN_FINDING_CLASS" for issue in report.issues)


def test_disposition_is_driven_by_explicit_class_not_summary_text():
    first = finding(
        "first",
        "BOUNDARY_LEAK",
        summary="Looks like a PostgreSQL implementation detail.",
    )
    second = finding(
        "second",
        "BOUNDARY_LEAK",
        summary="Looks like an authority decision.",
    )

    report = audit_evidence(definition(first, second))

    assert report.status == "classified"
    assert {item.disposition for item in report.findings} == {REMOVE_FROM_CABINET_PRODUCT_SPEC}


def test_verification_gate_passes_only_when_every_required_probe_passes():
    base = definition(
        finding("one", "LOWERING_GAP"),
        finding("two", "DOMAIN_SEMANTIC_GAP"),
    )

    passed = audit_evidence(base)
    assert passed.verification_gate == "pass"

    failed_definition = deepcopy(base)
    failed_definition["findings"][1]["verification"]["status"] = "FAIL"
    failed = audit_evidence(failed_definition)

    assert failed.verification_gate == "block"
