#!/usr/bin/env python3
"""Prove one same-invoice Cabinet_web revision -> receipt -> source attach sequence."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from authority_kernel import (
    LOCAL_AGENT_BOUNDARY,
    SYNCHRONIZATION_BOUNDARY,
    AuthorityKernel,
    CapabilityPolicy,
    CredentialRecord,
    GrantRecord,
    PrincipalRecord,
    credential_digest,
)
from bounded_content_validation_kernel import BoundedContentValidationKernel
from cabinet_web_revision_accept_models import REVISION_NAMESPACE
from cabinet_web_revision_accept_runtime import (
    CAPABILITY as SYNC_CAPABILITY,
    DISCLOSURES as SYNC_DISCLOSURES,
    EFFECTS as SYNC_EFFECTS,
    CabinetWebRevisionAcceptExecutor,
    canonical_content_hash,
    revision_resource_id,
)
from cabinet_web_source_attach_adapter import CabinetWebSourceAttachAdapter
from invoice_source_attach_models import INVOICE_NAMESPACE
from invoice_source_attach_runtime import (
    CAPABILITY as ATTACH_CAPABILITY,
    DISCLOSURES as ATTACH_DISCLOSURES,
    EFFECTS as ATTACH_EFFECTS,
    InvoiceSourceAttachExecutor,
)
from local_private_byte_vault import LocalPrivateByteVault
from postgres_record_kernel import PostgresRecordKernel
from typed_schema_kernel import TypedSchemaKernel


DB_ENV = "SPEC_WORKBENCH_TEST_POSTGRES_DSN"
VAULT_ENV = "SPEC_WORKBENCH_ATTACH_VAULT_ROOT"
SYNC_SECRET = "e2e-sync-secret-c8d5"
ATTACH_SECRET = "e2e-attach-secret-a3b1"
ACCEPTED_MEDIA = frozenset({"image/jpeg", "image/png", "application/pdf"})


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


def _card(invoice_id: str) -> dict:
    return {
        "card_type": "invoice",
        "card_version": 1,
        "id": invoice_id,
        "status": "confirmed",
        "invoice_number": "E2E-001",
        "issue_date": "2026-08-21",
        "service_date": None,
        "due_date": None,
        "currency": "EUR",
        "supplier": {"name": "E2E Supplier", "tax_id": None, "address": None},
        "buyer": {"name": None, "tax_id": None, "address": None},
        "object": {"card_id": None, "label": "E2E object"},
        "lines": [{
            "line_id": "line-001",
            "kind": "material",
            "description_original": "E2E item",
            "description_normalized": None,
            "supplier_sku": None,
            "matched_material_id": None,
            "quantity": "1",
            "unit": "unit",
            "unit_price_net": "1.00",
            "discount_percent": "0",
            "discount_amount": "0.00",
            "net_amount": "1.00",
            "tax_rate": "21",
            "tax_amount": "0.21",
            "gross_amount": "1.21",
        }],
        "totals": {
            "net": "1.00",
            "discount": "0.00",
            "tax": "0.21",
            "gross": "1.21",
            "withholding": "0.00",
            "payable": "1.21",
        },
        "payment": {"status": "unknown", "transactions": []},
        "source": {
            "source_id": "source-001",
            "kind": "photo",
            "file_ref": None,
            "file_status": "not_stored",
            "note": "source bytes arrive later through local custody",
        },
        "provenance": {
            "created_at": "2026-08-21T18:00:00+02:00",
            "confirmed_at": "2026-08-21T18:01:00+02:00",
            "created_by": "assistant",
        },
    }


def _delivery(invoice_id: str, card: dict) -> dict:
    return {
        "contract_version": "cabinet-web-sync-v1",
        "delivery_id": f"delivery-{uuid.uuid4().hex}",
        "emitted_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "producer_repository": "MigelSmirnov/Cabinet_web",
        "invoice_id": invoice_id,
        "card_contract_version": 1,
        "card_status": "confirmed",
        "card_content_hash": canonical_content_hash(card),
        "source_git_commit_sha": "b" * 40,
        "card_repository_path": f"data/cards/{invoice_id}/card.json",
        "base_backend_content_hash": None,
        "card_document": card,
    }


def _png_bytes() -> bytes:
    from PIL import Image  # type: ignore

    buffer = BytesIO()
    Image.new("RGB", (8, 8), (17, 29, 43)).save(buffer, format="PNG")
    return buffer.getvalue()


def _sync_authority(invoice_id: str) -> AuthorityKernel:
    return AuthorityKernel(
        principals=(PrincipalRecord("sync-agent", "agent"),),
        credentials=(CredentialRecord(
            "sync-credential", "sync-agent", SYNCHRONIZATION_BOUNDARY, credential_digest(SYNC_SECRET)
        ),),
        grants=(GrantRecord(
            "sync-grant",
            "sync-agent",
            SYNC_CAPABILITY,
            CabinetWebRevisionAcceptExecutor.resource_scope(invoice_id),
            effect_scope=SYNC_EFFECTS,
            disclosure_scope=SYNC_DISCLOSURES,
        ),),
        policies=(CapabilityPolicy(
            SYNC_CAPABILITY,
            effects=SYNC_EFFECTS,
            disclosure_allow=SYNC_DISCLOSURES,
        ),),
    )


def _attach_authority(invoice_id: str) -> AuthorityKernel:
    return AuthorityKernel(
        principals=(PrincipalRecord("attach-agent", "agent"),),
        credentials=(CredentialRecord(
            "attach-credential", "attach-agent", LOCAL_AGENT_BOUNDARY, credential_digest(ATTACH_SECRET)
        ),),
        grants=(GrantRecord(
            "attach-grant",
            "attach-agent",
            ATTACH_CAPABILITY,
            InvoiceSourceAttachExecutor.resource_scope(invoice_id),
            effect_scope=ATTACH_EFFECTS,
            disclosure_scope=ATTACH_DISCLOSURES,
        ),),
        policies=(CapabilityPolicy(
            ATTACH_CAPABILITY,
            effects=ATTACH_EFFECTS,
            disclosure_allow=ATTACH_DISCLOSURES,
        ),),
    )


def run_probe(environment=None) -> ProbeReport:
    env = dict(os.environ if environment is None else environment)
    dsn = env.get(DB_ENV)
    vault_parent = env.get(VAULT_ENV)
    if not dsn or not vault_parent:
        return ProbeReport(
            "spec_workbench_cabinet_web_e2e_runtime.v1",
            "block",
            (ProbeResult(
                "WEB-E2E-001",
                "UNVERIFIED",
                f"{DB_ENV} and {VAULT_ENV} are required",
            ),),
        )

    schema = f"spec_workbench_web_e2e_{uuid.uuid4().hex[:12]}"
    records = PostgresRecordKernel(dsn, schema=schema)
    records.initialize()
    vault_root = Path(vault_parent).expanduser().resolve() / f"web-e2e-{uuid.uuid4().hex[:12]}"
    vault_root.parent.mkdir(parents=True, exist_ok=True)
    vault = LocalPrivateByteVault(vault_root)
    result: ProbeResult

    try:
        invoice_id = f"invoice-e2e-{uuid.uuid4().hex[:8]}"
        card = _card(invoice_id)
        card_before = json.dumps(card, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        delivery = _delivery(invoice_id, card)

        sync = CabinetWebRevisionAcceptExecutor(
            authority=_sync_authority(invoice_id),
            typed_schema=TypedSchemaKernel(),
            records=records,
            card_validator=lambda _card: (),
        )
        receipt = sync.execute(
            delivery,
            credential_id="sync-credential",
            credential_material=SYNC_SECRET,
            interaction_id="web-e2e-sync",
        )
        if receipt.outcome != "accepted":
            raise RuntimeError(f"revision acceptance returned {receipt.outcome}")

        content = _png_bytes()
        content_digest = hashlib.sha256(content).hexdigest()
        attach = CabinetWebSourceAttachAdapter(
            authority=_attach_authority(invoice_id),
            typed_schema=TypedSchemaKernel(),
            records=records,
            byte_vault=vault,
            content_validation=BoundedContentValidationKernel(
                max_size_bytes=1024 * 1024,
                accepted_media_types=ACCEPTED_MEDIA,
            ),
        )
        attached = attach.execute(
            invoice_id=invoice_id,
            source_id="source-001",
            filename="source-with-untrusted-extension.bin",
            content=content,
            credential_id="attach-credential",
            credential_material=ATTACH_SECRET,
            interaction_id="web-e2e-attach",
        )
        if attached.items[0].result != "attached":
            raise RuntimeError("source attachment did not return attached")

        state = records.read_record(INVOICE_NAMESPACE, invoice_id)
        revision = records.read_record(
            REVISION_NAMESPACE,
            revision_resource_id(invoice_id, delivery["card_content_hash"]),
        )
        if state is None or revision is None:
            raise RuntimeError("accepted invoice or revision disappeared after source attachment")
        if state.payload["accepted_card_content_hash"] != delivery["card_content_hash"]:
            raise RuntimeError("source attachment changed accepted Card revision hash")
        card_after = json.dumps(
            state.payload["accepted_card_document"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        if card_after != card_before or revision.payload["card_document"] != card:
            raise RuntimeError("source attachment rewrote accepted Card facts")
        source_state = state.payload["source_states"]["source-001"]
        if source_state["status"] != "available":
            raise RuntimeError("source did not become available")
        if source_state["content_hash"] != content_digest:
            raise RuntimeError("local source hash does not match attached bytes")
        if source_state["media_type"] != "image/png":
            raise RuntimeError("parser-derived media type was not persisted as local evidence")
        if state.payload["expected_sources"]["source-001"]["expected_hash"] is not None:
            raise RuntimeError("local hash was converted into fabricated upstream expectation")
        if state.payload["expected_sources"]["source-001"]["media_type"] is not None:
            raise RuntimeError("detected media type was converted into fabricated upstream expectation")

        event_types = {event.event_type for event in records.read_audit()}
        if "cabinet_web.revision.accept" not in event_types or "invoice.source.attach" not in event_types:
            raise RuntimeError("E2E sequence did not persist both acceptance and attachment audit events")

        result = ProbeResult(
            "WEB-E2E-001",
            "PASS",
            "one invoice revision was accepted with a bounded receipt, then the same backend state accepted parser-validated source bytes without changing Card facts",
        )
    except Exception as exc:
        result = ProbeResult("WEB-E2E-001", "FAIL", f"{type(exc).__name__}: {exc}")
    finally:
        records.drop_probe_schema()
        shutil.rmtree(vault_root, ignore_errors=True)

    return ProbeReport(
        "spec_workbench_cabinet_web_e2e_runtime.v1",
        "pass" if result.status == "PASS" else "fail",
        (result,),
    )


def main() -> int:
    report = run_probe()
    print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    return 0 if report.status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
