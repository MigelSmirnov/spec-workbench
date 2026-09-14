#!/usr/bin/env python3
"""Execute the Cabinet_web no-MIME/no-hash source-attachment canary."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import uuid
from dataclasses import asdict, dataclass
from typing import Any

from cabinet_web_source_attach_adapter import CabinetWebSourceAttachAdapter
from invoice_source_attach_models import INVOICE_NAMESPACE, PUBLICATION_NAMESPACE, empty_source_state
from invoice_source_attach_runtime import (
    InvoiceSourceAttachExecutionError,
    InvoiceSourceAttachExecutor,
    InvoiceSourceAttachRejected,
    publication_resource_id,
)
from invoice_source_attach_runtime_probe import (
    AGENT_SECRET,
    DB_ENV,
    VAULT_ENV,
    ProbeRuntime,
    _authority,
    _FailOncePublishVault,
    _png_bytes,
    _setup_runtime,
)
from protected_configuration_kernel import ProtectedConfigurationNotReady


PROBE_SCHEMA_VERSION = "spec_workbench_cabinet_web_attach_canary.v1"


@dataclass(frozen=True)
class CanaryResult:
    probe_id: str
    status: str
    message: str


@dataclass(frozen=True)
class CanaryReport:
    schema_version: str
    status: str
    results: tuple[CanaryResult, ...]


def _canonical_card_hash(card: dict[str, Any]) -> str:
    payload = json.dumps(card, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _confirmed_card(invoice_id: str, source_id: str) -> dict[str, Any]:
    return {
        "card_type": "invoice",
        "card_version": 1,
        "id": invoice_id,
        "status": "confirmed",
        "invoice_number": "CANARY-2026-001",
        "issue_date": "2026-08-21",
        "service_date": None,
        "due_date": None,
        "currency": "EUR",
        "supplier": {"name": "Canary Supplier", "tax_id": None, "address": None},
        "buyer": {"name": None, "tax_id": None, "address": None},
        "object": {"card_id": None, "label": "Cabinet Web interop canary"},
        "lines": (
            {
                "line_id": "line-001",
                "kind": "material",
                "description_original": "Canary material",
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
            },
        ),
        "totals": {
            "net": "1.00",
            "discount": "0.00",
            "tax": "0.21",
            "gross": "1.21",
            "withholding": "0.00",
            "payable": "1.21",
        },
        "payment": {"status": "unknown", "transactions": ()},
        "source": {
            "source_id": source_id,
            "kind": "photo",
            "file_ref": None,
            "file_status": "not_stored",
            "note": "Exact media type and binary hash intentionally absent from Card facts",
        },
        "provenance": {
            "created_at": "2026-08-21T16:00:00Z",
            "confirmed_at": "2026-08-21T16:01:00Z",
            "created_by": "import",
        },
    }


def _seed_accepted_web_revision(runtime: ProbeRuntime, *, invoice_id: str, source_id: str):
    card = _confirmed_card(invoice_id, source_id)
    card_hash = _canonical_card_hash(card)
    payload = {
        "invoice_id": invoice_id,
        "accepted_archive_target": True,
        "accepted_card_document": card,
        "accepted_card_content_hash": card_hash,
        "expected_sources": {
            source_id: {
                "expected_hash": None,
                "media_type": None,
                "required": True,
            }
        },
        "source_states": {source_id: empty_source_state()},
    }
    with runtime.records.transaction() as tx:
        tx.lock_resource(INVOICE_NAMESPACE, invoice_id)
        if tx.get_record(INVOICE_NAMESPACE, invoice_id) is not None:
            raise RuntimeError("canary invoice already exists")
        tx.put_record(INVOICE_NAMESPACE, invoice_id, payload)
    return card, card_hash


def _adapter(runtime: ProbeRuntime, invoice_id: str, *, vault=None) -> CabinetWebSourceAttachAdapter:
    return CabinetWebSourceAttachAdapter(
        authority=_authority(invoice_id),
        typed_schema=runtime.typed,
        records=runtime.records,
        byte_vault=runtime.vault if vault is None else vault,
        content_validation=runtime.content,
    )


def _execute(adapter: CabinetWebSourceAttachAdapter, invoice_id: str, source_id: str, content: bytes, interaction: str):
    return adapter.execute(
        invoice_id=invoice_id,
        source_id=source_id,
        filename="misleading-name.jpg",
        content=content,
        credential_id="attach-credential",
        credential_material=AGENT_SECRET,
        interaction_id=interaction,
    )


def _pass(probe_id: str, message: str) -> CanaryResult:
    return CanaryResult(probe_id, "PASS", message)


def _fail(probe_id: str, message: str) -> CanaryResult:
    return CanaryResult(probe_id, "FAIL", message)


def _probe_success_and_card_immutability(runtime: ProbeRuntime) -> CanaryResult:
    invoice_id = f"invoice-web-canary-{uuid.uuid4().hex[:8]}"
    source_id = "source-001"
    content = _png_bytes((21, 42, 84))
    digest = hashlib.sha256(content).hexdigest()
    card, card_hash = _seed_accepted_web_revision(runtime, invoice_id=invoice_id, source_id=source_id)
    before_card = json.dumps(card, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    try:
        result = _execute(_adapter(runtime, invoice_id), invoice_id, source_id, content, "web-canary-success")
        stored = runtime.records.read_record(INVOICE_NAMESPACE, invoice_id)
        publication = runtime.records.read_record(
            PUBLICATION_NAMESPACE, publication_resource_id(invoice_id, source_id)
        )
        if stored is None or publication is None:
            return _fail("WEB-ATTACH-001", "attachment did not persist source/publication evidence")
        state = stored.payload["source_states"][source_id]
        if state["status"] != "available" or state["media_type"] != "image/png":
            return _fail("WEB-ATTACH-001", "parser-backed PNG media evidence was not persisted")
        if state["content_hash"] != digest:
            return _fail("WEB-ATTACH-001", "locally calculated SHA-256 was not persisted as source evidence")
        durable_expected = stored.payload["expected_sources"][source_id]
        if durable_expected["expected_hash"] is not None or durable_expected["media_type"] is not None:
            return _fail("WEB-ATTACH-001", "local evidence was rewritten as an upstream expectation")
        after_card = json.dumps(
            stored.payload["accepted_card_document"], ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        if after_card != before_card or stored.payload["accepted_card_content_hash"] != card_hash:
            return _fail("WEB-ATTACH-001", "confirmed Card document or revision hash changed during attachment")
        if _canonical_card_hash(stored.payload["accepted_card_document"]) != card_hash:
            return _fail("WEB-ATTACH-001", "stored confirmed Card no longer hashes to accepted revision")
        if result.items[0].result != "attached" or result.source_status.complete is not True:
            return _fail("WEB-ATTACH-001", "safe result did not report successful complete attachment")
    except Exception as exc:
        return _fail("WEB-ATTACH-001", f"canary success path failed: {type(exc).__name__}: {exc}")
    return _pass(
        "WEB-ATTACH-001",
        "no-MIME/no-hash Web source attached as parser-validated PNG with local hash evidence while confirmed Card bytes/hash stayed unchanged",
    )


def _probe_replay_and_conflict(runtime: ProbeRuntime) -> CanaryResult:
    invoice_id = f"invoice-web-replay-{uuid.uuid4().hex[:8]}"
    source_id = "source-001"
    first = _png_bytes((1, 80, 160))
    second = _png_bytes((160, 80, 1))
    _seed_accepted_web_revision(runtime, invoice_id=invoice_id, source_id=source_id)
    adapter = _adapter(runtime, invoice_id)
    try:
        _execute(adapter, invoice_id, source_id, first, "web-canary-first")
        before = runtime.records.read_record(INVOICE_NAMESPACE, invoice_id)
        replay = _execute(adapter, invoice_id, source_id, first, "web-canary-replay")
        after_replay = runtime.records.read_record(INVOICE_NAMESPACE, invoice_id)
        if replay.items[0].result != "already_attached":
            return _fail("WEB-ATTACH-002", "equivalent replay did not converge on existing attachment")
        if before is None or after_replay is None or before.version != after_replay.version:
            return _fail("WEB-ATTACH-002", "equivalent replay mutated invoice source state")
        try:
            _execute(adapter, invoice_id, source_id, second, "web-canary-conflict")
        except InvoiceSourceAttachRejected as exc:
            if exc.code != "source_content_conflict":
                return _fail("WEB-ATTACH-002", f"unexpected conflict code: {exc.code}")
        else:
            return _fail("WEB-ATTACH-002", "different bytes silently replaced the accepted source")
    except Exception as exc:
        return _fail("WEB-ATTACH-002", f"replay/conflict path failed: {type(exc).__name__}: {exc}")
    return _pass(
        "WEB-ATTACH-002",
        "no-expected-hash path remained idempotent for equal bytes and rejected conflicting bytes for the same source identity",
    )


def _probe_crash_recovery(runtime: ProbeRuntime) -> CanaryResult:
    invoice_id = f"invoice-web-recovery-{uuid.uuid4().hex[:8]}"
    source_id = "source-001"
    content = _png_bytes((90, 30, 180))
    card, card_hash = _seed_accepted_web_revision(runtime, invoice_id=invoice_id, source_id=source_id)
    before_card = json.dumps(card, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    failing_vault = _FailOncePublishVault(runtime.vault)
    try:
        try:
            _execute(
                _adapter(runtime, invoice_id, vault=failing_vault),
                invoice_id,
                source_id,
                content,
                "web-canary-recovery-crash",
            )
        except InvoiceSourceAttachExecutionError as exc:
            if str(exc) != "publication_pending_recovery":
                return _fail("WEB-ATTACH-003", f"unexpected interrupted result: {exc}")
        else:
            return _fail("WEB-ATTACH-003", "intentional publish interruption did not interrupt")

        pending = runtime.records.read_record(
            PUBLICATION_NAMESPACE, publication_resource_id(invoice_id, source_id)
        )
        interrupted = runtime.records.read_record(INVOICE_NAMESPACE, invoice_id)
        if pending is None or interrupted is None or pending.payload["state"] != "metadata_committed":
            return _fail("WEB-ATTACH-003", "interruption did not leave recoverable publication evidence")
        if interrupted.payload["source_states"][source_id]["status"] != "missing":
            return _fail("WEB-ATTACH-003", "interruption claimed source availability before publication")

        recovery = InvoiceSourceAttachExecutor(
            authority=_authority(invoice_id),
            typed_schema=runtime.typed,
            records=runtime.records,
            byte_vault=runtime.vault,
            content_validation=runtime.content,
        )
        result = recovery.recover_pending_publication(invoice_id=invoice_id, source_id=source_id)
        settled = runtime.records.read_record(INVOICE_NAMESPACE, invoice_id)
        if settled is None or result.items[0].result != "recovered":
            return _fail("WEB-ATTACH-003", "startup recovery did not settle attachment")
        if settled.payload["source_states"][source_id]["status"] != "available":
            return _fail("WEB-ATTACH-003", "recovery did not make verified source available")
        after_card = json.dumps(
            settled.payload["accepted_card_document"], ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        if after_card != before_card or settled.payload["accepted_card_content_hash"] != card_hash:
            return _fail("WEB-ATTACH-003", "crash/recovery mutated confirmed Card evidence")
    except Exception as exc:
        return _fail("WEB-ATTACH-003", f"recovery path failed: {type(exc).__name__}: {exc}")
    return _pass(
        "WEB-ATTACH-003",
        "no-MIME/no-hash path preserved pending evidence across publish failure and recovered without changing confirmed Card facts",
    )


def _probe_malformed_bytes_fail_before_effect(runtime: ProbeRuntime) -> CanaryResult:
    invoice_id = f"invoice-web-malformed-{uuid.uuid4().hex[:8]}"
    source_id = "source-001"
    _seed_accepted_web_revision(runtime, invoice_id=invoice_id, source_id=source_id)
    try:
        try:
            _execute(
                _adapter(runtime, invoice_id),
                invoice_id,
                source_id,
                b"not an image or pdf",
                "web-canary-malformed",
            )
        except Exception:
            pass
        else:
            return _fail("WEB-ATTACH-004", "malformed bytes were accepted")
        publication = runtime.records.read_record(
            PUBLICATION_NAMESPACE, publication_resource_id(invoice_id, source_id)
        )
        stored = runtime.records.read_record(INVOICE_NAMESPACE, invoice_id)
        if publication is not None:
            return _fail("WEB-ATTACH-004", "malformed bytes created publication evidence")
        if stored is None or stored.payload["source_states"][source_id]["status"] != "missing":
            return _fail("WEB-ATTACH-004", "malformed bytes changed source state")
    except Exception as exc:
        return _fail("WEB-ATTACH-004", f"malformed path failed unexpectedly: {type(exc).__name__}: {exc}")
    return _pass(
        "WEB-ATTACH-004",
        "unrecognized bytes failed before staging/publication and left accepted Card/source expectation unchanged",
    )


def run_probe(environment: dict[str, str] | None = None) -> CanaryReport:
    env = dict(os.environ if environment is None else environment)
    try:
        runtime = _setup_runtime(env)
    except ProtectedConfigurationNotReady as exc:
        results = tuple(
            CanaryResult(probe_id, "UNVERIFIED", f"protected runtime configuration unavailable: {exc}")
            for probe_id in ("WEB-ATTACH-001", "WEB-ATTACH-002", "WEB-ATTACH-003", "WEB-ATTACH-004")
        )
        return CanaryReport(PROBE_SCHEMA_VERSION, "block", results)

    results: list[CanaryResult] = []
    try:
        for probe in (
            _probe_success_and_card_immutability,
            _probe_replay_and_conflict,
            _probe_crash_recovery,
            _probe_malformed_bytes_fail_before_effect,
        ):
            results.append(probe(runtime))
    finally:
        try:
            runtime.records.drop_probe_schema()
        except Exception as exc:
            results.append(_fail("WEB-ATTACH-CLEANUP", f"database cleanup failed: {type(exc).__name__}: {exc}"))
        try:
            shutil.rmtree(runtime.vault_root)
        except FileNotFoundError:
            pass
        except Exception as exc:
            results.append(_fail("WEB-ATTACH-CLEANUP", f"vault cleanup failed: {type(exc).__name__}: {exc}"))

    status = "pass" if results and {item.status for item in results} == {"PASS"} else "fail"
    return CanaryReport(PROBE_SCHEMA_VERSION, status, tuple(results))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute Cabinet_web source attach canary")
    parser.parse_args(argv)
    report = run_probe()
    print(json.dumps(asdict(report), ensure_ascii=False, indent=2, default=str))
    if report.status == "pass":
        return 0
    if report.status == "block":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
