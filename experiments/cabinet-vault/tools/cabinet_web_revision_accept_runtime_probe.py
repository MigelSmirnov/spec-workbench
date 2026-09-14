#!/usr/bin/env python3
"""Execute sync-v1 revision acceptance probes against PostgreSQL."""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from authority_kernel import (
    SYNCHRONIZATION_BOUNDARY,
    AuthorityKernel,
    CapabilityPolicy,
    CredentialRecord,
    GrantRecord,
    PrincipalRecord,
    credential_digest,
)
from cabinet_web_revision_accept_models import DELIVERY_NAMESPACE, REVISION_NAMESPACE
from cabinet_web_revision_accept_runtime import (
    CAPABILITY,
    DISCLOSURES,
    EFFECTS,
    CabinetWebRevisionAcceptExecutor,
    canonical_content_hash,
    revision_resource_id,
)
from invoice_source_attach_models import INVOICE_NAMESPACE
from postgres_record_kernel import PostgresRecordKernel
from typed_schema_kernel import TypedSchemaKernel


DB_ENV = "SPEC_WORKBENCH_TEST_POSTGRES_DSN"
SECRET = "sync-probe-secret-59b3d8"


@dataclass(frozen=True)
class ProbeResult:
    probe_id: str
    status: str
    message: str


@dataclass(frozen=True)
class ProbeReport:
    schema_version: str
    status: str
    results: tuple[ProbeResult, ...]


def _pass(probe_id: str, message: str) -> ProbeResult:
    return ProbeResult(probe_id, "PASS", message)


def _fail(probe_id: str, message: str) -> ProbeResult:
    return ProbeResult(probe_id, "FAIL", message)


def _card(invoice_id: str, *, note: str = "real source pending local custody") -> dict:
    return {
        "card_type": "invoice",
        "card_version": 1,
        "id": invoice_id,
        "status": "confirmed",
        "invoice_number": "CANARY-001",
        "issue_date": "2026-08-21",
        "service_date": None,
        "due_date": None,
        "currency": "EUR",
        "supplier": {"name": "Canary Supplier", "tax_id": None, "address": None},
        "buyer": {"name": None, "tax_id": None, "address": None},
        "object": {"card_id": None, "label": "Canary object"},
        "lines": [
            {
                "line_id": "line-001",
                "kind": "material",
                "description_original": "Canary item",
                "description_normalized": None,
                "supplier_sku": None,
                "matched_material_id": None,
                "quantity": "1",
                "unit": "unit",
                "unit_price_net": "10.00",
                "discount_percent": "0",
                "discount_amount": "0.00",
                "net_amount": "10.00",
                "tax_rate": "21",
                "tax_amount": "2.10",
                "gross_amount": "12.10",
            }
        ],
        "totals": {
            "net": "10.00",
            "discount": "0.00",
            "tax": "2.10",
            "gross": "12.10",
            "withholding": "0.00",
            "payable": "12.10",
        },
        "payment": {"status": "unknown", "transactions": []},
        "source": {
            "source_id": "source-001",
            "kind": "photo",
            "file_ref": None,
            "file_status": "not_stored",
            "note": note,
        },
        "provenance": {
            "created_at": "2026-08-21T18:00:00+02:00",
            "confirmed_at": "2026-08-21T18:01:00+02:00",
            "created_by": "assistant",
        },
    }


def _delivery(invoice_id: str, delivery_id: str, card: dict, *, base=None) -> dict:
    return {
        "contract_version": "cabinet-web-sync-v1",
        "delivery_id": delivery_id,
        "emitted_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "producer_repository": "MigelSmirnov/Cabinet_web",
        "invoice_id": invoice_id,
        "card_contract_version": 1,
        "card_status": "confirmed",
        "card_content_hash": canonical_content_hash(card),
        "source_git_commit_sha": "a" * 40,
        "card_repository_path": f"data/cards/{invoice_id}/card.json",
        "base_backend_content_hash": base,
        "card_document": card,
    }


def _authority(invoice_id: str) -> AuthorityKernel:
    return AuthorityKernel(
        principals=(PrincipalRecord("sync-agent", "agent"),),
        credentials=(
            CredentialRecord(
                "sync-credential",
                "sync-agent",
                SYNCHRONIZATION_BOUNDARY,
                credential_digest(SECRET),
            ),
        ),
        grants=(
            GrantRecord(
                "sync-grant",
                "sync-agent",
                CAPABILITY,
                CabinetWebRevisionAcceptExecutor.resource_scope(invoice_id),
                effect_scope=EFFECTS,
                disclosure_scope=DISCLOSURES,
            ),
        ),
        policies=(
            CapabilityPolicy(
                CAPABILITY,
                effects=EFFECTS,
                disclosure_allow=DISCLOSURES,
            ),
        ),
    )


def _executor(records: PostgresRecordKernel, invoice_id: str, validator=None):
    return CabinetWebRevisionAcceptExecutor(
        authority=_authority(invoice_id),
        typed_schema=TypedSchemaKernel(),
        records=records,
        card_validator=validator or (lambda card: ()),
    )


def _invoke(executor, payload, interaction: str):
    return executor.execute(
        payload,
        credential_id="sync-credential",
        credential_material=SECRET,
        interaction_id=interaction,
    )


def _probe_accept_and_source_expectation(records: PostgresRecordKernel) -> ProbeResult:
    invoice_id = f"invoice-sync-{uuid.uuid4().hex[:8]}"
    card = _card(invoice_id)
    delivery = _delivery(invoice_id, f"delivery-{uuid.uuid4().hex}", card)
    try:
        result = _invoke(_executor(records, invoice_id), delivery, "sync-first")
        if result.outcome != "accepted":
            return _fail("SYNC-RUNTIME-001", f"unexpected outcome {result.outcome}")
        state = records.read_record(INVOICE_NAMESPACE, invoice_id)
        revision = records.read_record(
            REVISION_NAMESPACE,
            revision_resource_id(invoice_id, delivery["card_content_hash"]),
        )
        if state is None or revision is None:
            return _fail("SYNC-RUNTIME-001", "accepted revision or current invoice state missing")
        if revision.payload["card_document"] != card:
            return _fail("SYNC-RUNTIME-001", "immutable stored Card differs from delivered Card")
        expected = state.payload["expected_sources"]["source-001"]
        if expected["expected_hash"] is not None or expected["media_type"] is not None:
            return _fail("SYNC-RUNTIME-001", "sync invented binary hash or MIME expectation")
        if state.payload["accepted_card_content_hash"] != delivery["card_content_hash"]:
            return _fail("SYNC-RUNTIME-001", "current state lost exact Card revision identity")
    except Exception as exc:
        return _fail("SYNC-RUNTIME-001", f"acceptance failed: {type(exc).__name__}: {exc}")
    return _pass(
        "SYNC-RUNTIME-001",
        "exact confirmed Card revision was accepted immutably and source identity was projected without invented binary MIME/hash",
    )


def _probe_delivery_idempotency_and_conflict(records: PostgresRecordKernel) -> ProbeResult:
    invoice_id = f"invoice-idem-{uuid.uuid4().hex[:8]}"
    delivery_id = f"delivery-{uuid.uuid4().hex}"
    card = _card(invoice_id)
    first = _delivery(invoice_id, delivery_id, card)
    executor = _executor(records, invoice_id)
    try:
        a = _invoke(executor, first, "sync-idem-first")
        b = _invoke(executor, first, "sync-idem-second")
        if a.outcome != "accepted" or b.outcome != "already_accepted":
            return _fail("SYNC-RUNTIME-002", "same delivery did not converge idempotently")
        changed = _card(invoice_id, note="changed revision")
        conflicting = _delivery(invoice_id, delivery_id, changed, base=first["card_content_hash"])
        c = _invoke(executor, conflicting, "sync-idem-conflict")
        if c.outcome != "delivery_identity_conflict":
            return _fail("SYNC-RUNTIME-002", "reused delivery id with different revision was not rejected")
    except Exception as exc:
        return _fail("SYNC-RUNTIME-002", f"idempotency probe failed: {type(exc).__name__}: {exc}")
    return _pass(
        "SYNC-RUNTIME-002",
        "same delivery/revision is idempotent and delivery identity cannot be rebound to different content",
    )


def _probe_revision_reconciliation(records: PostgresRecordKernel) -> ProbeResult:
    invoice_id = f"invoice-reconcile-{uuid.uuid4().hex[:8]}"
    executor = _executor(records, invoice_id)
    first_card = _card(invoice_id)
    first = _delivery(invoice_id, f"delivery-{uuid.uuid4().hex}", first_card)
    try:
        a = _invoke(executor, first, "sync-reconcile-first")
        if a.outcome != "accepted":
            return _fail("SYNC-RUNTIME-003", "first revision was not accepted")
        second_card = _card(invoice_id, note="second confirmed revision")
        stale = _delivery(
            invoice_id,
            f"delivery-{uuid.uuid4().hex}",
            second_card,
            base="sha256:" + "0" * 64,
        )
        b = _invoke(executor, stale, "sync-reconcile-stale")
        if b.outcome != "reconciliation_required" or b.backend_current_content_hash != first["card_content_hash"]:
            return _fail("SYNC-RUNTIME-003", "stale base did not return current revision for reconciliation")
        correct = _delivery(
            invoice_id,
            f"delivery-{uuid.uuid4().hex}",
            second_card,
            base=first["card_content_hash"],
        )
        c = _invoke(executor, correct, "sync-reconcile-correct")
        if c.outcome != "accepted":
            return _fail("SYNC-RUNTIME-003", "new revision with correct base was not accepted")
        first_revision = records.read_record(
            REVISION_NAMESPACE,
            revision_resource_id(invoice_id, first["card_content_hash"]),
        )
        second_revision = records.read_record(
            REVISION_NAMESPACE,
            revision_resource_id(invoice_id, correct["card_content_hash"]),
        )
        if first_revision is None or second_revision is None:
            return _fail("SYNC-RUNTIME-003", "accepting a new revision deleted or failed to preserve revision history")
    except Exception as exc:
        return _fail("SYNC-RUNTIME-003", f"reconciliation probe failed: {type(exc).__name__}: {exc}")
    return _pass(
        "SYNC-RUNTIME-003",
        "stale bases fail closed and a correctly based new revision is accepted without deleting the previous immutable revision",
    )


def _probe_validation_and_hash_fail_closed(records: PostgresRecordKernel) -> ProbeResult:
    invoice_id = f"invoice-invalid-{uuid.uuid4().hex[:8]}"
    card = _card(invoice_id)
    bad_hash = _delivery(invoice_id, f"delivery-{uuid.uuid4().hex}", card)
    bad_hash["card_content_hash"] = "sha256:" + "f" * 64
    try:
        result = _invoke(_executor(records, invoice_id), bad_hash, "sync-bad-hash")
        if result.outcome != "rejected_card" or result.error_code != "card_content_hash_mismatch":
            return _fail("SYNC-RUNTIME-004", "canonical hash mismatch did not fail closed")
        if records.read_record(INVOICE_NAMESPACE, invoice_id) is not None:
            return _fail("SYNC-RUNTIME-004", "rejected Card created accepted invoice state")

        validation_delivery = _delivery(invoice_id, f"delivery-{uuid.uuid4().hex}", card)
        validator = lambda _card: ({"severity": "error", "code": "test_invalid", "path": "$"},)
        result2 = _invoke(_executor(records, invoice_id, validator=validator), validation_delivery, "sync-validator-reject")
        if result2.outcome != "rejected_card" or result2.error_code != "cabinet_web_card_validation_failed":
            return _fail("SYNC-RUNTIME-004", "Cabinet_web validator errors did not block acceptance")
        if records.read_record(INVOICE_NAMESPACE, invoice_id) is not None:
            return _fail("SYNC-RUNTIME-004", "validator rejection created accepted invoice state")
    except Exception as exc:
        return _fail("SYNC-RUNTIME-004", f"validation probe failed: {type(exc).__name__}: {exc}")
    return _pass(
        "SYNC-RUNTIME-004",
        "canonical hash mismatch and Cabinet_web validator errors fail before durable revision acceptance",
    )


def run_probe(environment=None) -> ProbeReport:
    env = dict(os.environ if environment is None else environment)
    dsn = env.get(DB_ENV)
    if not dsn:
        results = tuple(
            ProbeResult(f"SYNC-RUNTIME-{index:03d}", "UNVERIFIED", f"{DB_ENV} is required")
            for index in range(1, 5)
        )
        return ProbeReport("spec_workbench_cabinet_web_sync_runtime.v1", "block", results)

    schema = f"spec_workbench_web_sync_{uuid.uuid4().hex[:12]}"
    records = PostgresRecordKernel(dsn, schema=schema)
    records.initialize()
    results: list[ProbeResult] = []
    try:
        for probe in (
            _probe_accept_and_source_expectation,
            _probe_delivery_idempotency_and_conflict,
            _probe_revision_reconciliation,
            _probe_validation_and_hash_fail_closed,
        ):
            results.append(probe(records))
    finally:
        records.drop_probe_schema()
    status = "pass" if results and all(item.status == "PASS" for item in results) else "fail"
    return ProbeReport("spec_workbench_cabinet_web_sync_runtime.v1", status, tuple(results))


def main() -> int:
    report = run_probe()
    print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    return 0 if report.status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
