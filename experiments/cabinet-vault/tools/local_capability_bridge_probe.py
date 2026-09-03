#!/usr/bin/env python3
"""Executable real-provider verification for the trusted local capability bridge."""
from __future__ import annotations

import base64
import json
import os
import shutil
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from authority_kernel import (
    SYNCHRONIZATION_BOUNDARY,
    AuthenticationDenied,
    AuthorityKernel,
    AuthorizationDenied,
    CapabilityPolicy,
    CredentialRecord,
    GrantRecord,
    PrincipalRecord,
    credential_digest,
)
from cabinet_web_revision_accept_runtime import (
    CAPABILITY as ACCEPT_CAPABILITY,
    DISCLOSURES as ACCEPT_DISCLOSURES,
    EFFECTS as ACCEPT_EFFECTS,
    CabinetWebRevisionAcceptExecutor,
    canonical_content_hash,
)
from invoice_source_attach_runtime import InvoiceSourceAttachExecutionError
from local_capability_bridge import (
    TARGET_INVOICE_ID,
    TARGET_RESOURCE_SCOPE,
    TARGET_SOURCE_ID,
    TrustedLocalCapabilityBridge,
)
from protected_configuration_kernel import ProtectedConfigurationNotReady


DB_ENV = "SPEC_WORKBENCH_TEST_POSTGRES_DSN"
VAULT_ENV = "SPEC_WORKBENCH_ATTACH_VAULT_ROOT"
CHECKOUT_ENV = "SPEC_WORKBENCH_CABINET_WEB_ROOT"


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


def _fail(probe_id: str, exc: Exception) -> ProbeResult:
    return ProbeResult(probe_id, "FAIL", f"{type(exc).__name__}: bounded probe failure")


def _pdf_bytes() -> bytes:
    from pypdf import PdfWriter  # type: ignore

    output = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.write(output)
    return output.getvalue()


def _test_card() -> dict:
    return {
        "card_type": "invoice",
        "card_version": 1,
        "id": TARGET_INVOICE_ID,
        "status": "confirmed",
        "invoice_number": "BRIDGE-PROBE-ONLY",
        "issue_date": "2026-08-21",
        "service_date": None,
        "due_date": None,
        "currency": "EUR",
        "supplier": {"name": "Bridge Probe Supplier", "tax_id": None, "address": None},
        "buyer": {"name": None, "tax_id": None, "address": None},
        "object": {"card_id": None, "label": "Bridge probe object"},
        "lines": [
            {
                "line_id": "line-probe",
                "kind": "material",
                "description_original": "Bridge probe item",
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
            }
        ],
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
            "source_id": TARGET_SOURCE_ID,
            "kind": "pdf",
            "file_ref": None,
            "file_status": "not_stored",
            "note": "synthetic isolated bridge probe; never real canary input",
        },
        "provenance": {
            "created_at": "2026-08-21T18:00:00+02:00",
            "confirmed_at": "2026-08-21T18:01:00+02:00",
            "created_by": "bridge-probe",
        },
    }


def _test_delivery() -> dict:
    card = _test_card()
    return {
        "contract_version": "cabinet-web-sync-v1",
        "delivery_id": f"bridge-probe-{uuid.uuid4().hex}",
        "emitted_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "producer_repository": "MigelSmirnov/Cabinet_web",
        "invoice_id": TARGET_INVOICE_ID,
        "card_contract_version": 1,
        "card_status": "confirmed",
        "card_content_hash": canonical_content_hash(card),
        "source_git_commit_sha": "b" * 40,
        "card_repository_path": f"data/cards/{TARGET_INVOICE_ID}/card.json",
        "base_backend_content_hash": None,
        "card_document": card,
    }


def _bridge_environment(dsn: str, vault_root: Path, checkout_root: str, schema: str) -> dict[str, str]:
    return {
        "CABINET_BRIDGE_POSTGRES_DSN": dsn,
        "CABINET_BRIDGE_POSTGRES_SCHEMA": schema,
        "CABINET_BRIDGE_VAULT_ROOT": str(vault_root),
        "CABINET_BRIDGE_CABINET_WEB_ROOT": checkout_root,
        "CABINET_BRIDGE_SYNC_CREDENTIAL_ID": "bridge-probe-sync-id",
        "CABINET_BRIDGE_SYNC_CREDENTIAL_MATERIAL": "bridge-probe-sync-material",
        "CABINET_BRIDGE_LOCAL_AGENT_CREDENTIAL_ID": "bridge-probe-local-id",
        "CABINET_BRIDGE_LOCAL_AGENT_CREDENTIAL_MATERIAL": "bridge-probe-local-material",
    }


def run_probe(environment=None) -> ProbeReport:
    env = dict(os.environ if environment is None else environment)
    dsn = env.get(DB_ENV)
    vault_parent = env.get(VAULT_ENV)
    checkout_root = env.get(CHECKOUT_ENV)
    if not dsn or not vault_parent or not checkout_root:
        return ProbeReport(
            "spec_workbench_local_capability_bridge.v1",
            "block",
            tuple(
                ProbeResult(f"BRIDGE-{index:03d}", "UNVERIFIED", "protected runtime configuration required")
                for index in range(1, 12)
            ),
        )

    schema = f"cabinet_bridge_probe_{uuid.uuid4().hex[:12]}"
    vault_root = Path(vault_parent).expanduser().resolve() / schema
    bridge_env = _bridge_environment(dsn, vault_root, checkout_root, schema)
    results: list[ProbeResult] = []
    bridge: TrustedLocalCapabilityBridge | None = None
    try:
        try:
            missing = dict(bridge_env)
            missing.pop("CABINET_BRIDGE_POSTGRES_DSN")
            TrustedLocalCapabilityBridge.from_environment(missing).start()
            raise RuntimeError("missing protected configuration did not block startup")
        except ProtectedConfigurationNotReady:
            results.append(_pass("BRIDGE-001", "missing protected configuration blocks startup"))

        bridge = TrustedLocalCapabilityBridge.from_environment(bridge_env)
        bridge.start()
        health = bridge.readiness()
        serialized_health = repr(health)
        forbidden = tuple(bridge_env.values()) + tuple(bridge_env.keys())
        if not health["ready"] or any(value in serialized_health for value in forbidden):
            raise RuntimeError("readiness was false or disclosed protected configuration")
        results.append(_pass("BRIDGE-002", "readiness is bounded and contains no protected values or source keys"))

        assert bridge._accept_executor is not None
        # The production bridge retains its pinned disposable checkout validator.
        # This isolated provider probe replaces only that external validation
        # callback; validator fingerprint/interop behavior is covered separately.
        bridge._accept_executor.card_validator = lambda _card: ()
        delivery = _test_delivery()
        try:
            bridge._accept_executor.execute(
                delivery,
                credential_id=bridge_env["CABINET_BRIDGE_LOCAL_AGENT_CREDENTIAL_ID"],
                credential_material=bridge_env["CABINET_BRIDGE_LOCAL_AGENT_CREDENTIAL_MATERIAL"],
                interaction_id="bridge-probe-cross-class",
            )
            raise RuntimeError("local-agent credential crossed synchronization boundary")
        except AuthenticationDenied:
            pass
        assert bridge._attach_adapter is not None
        try:
            bridge._attach_adapter.execute(
                invoice_id=TARGET_INVOICE_ID,
                source_id=TARGET_SOURCE_ID,
                filename="cross-boundary.pdf",
                content=_pdf_bytes(),
                credential_id=bridge_env["CABINET_BRIDGE_SYNC_CREDENTIAL_ID"],
                credential_material=bridge_env["CABINET_BRIDGE_SYNC_CREDENTIAL_MATERIAL"],
                interaction_id="bridge-probe-cross-class-reverse",
            )
            raise RuntimeError("synchronization credential crossed local-agent boundary")
        except AuthenticationDenied:
            pass
        results.append(_pass("BRIDGE-003", "credential classes cannot cross executor trust boundaries"))

        wrong_invoice = dict(delivery)
        wrong_invoice["invoice_id"] = "invoice-other"
        try:
            bridge.accept_revision({"delivery": wrong_invoice, "interaction_id": "wrong-scope"})
            raise RuntimeError("missing exact target grant was not denied")
        except Exception as exc:
            if str(exc) != "exact_invoice_scope_required":
                raise
        results.append(_pass("BRIDGE-004", "missing exact invoice scope is denied before effects"))

        assert bridge._authority is not None
        principal = bridge._authority.authenticate(
            bridge_env["CABINET_BRIDGE_SYNC_CREDENTIAL_ID"],
            bridge_env["CABINET_BRIDGE_SYNC_CREDENTIAL_MATERIAL"],
            required_boundary="synchronization",
        )
        try:
            bridge._authority.authorize(
                principal,
                capability="invoice.archive.accept_revision",
                resource_scope="invoice:invoice-other",
                requested_effects=frozenset({"archive_revision_write", "archive_source_expectation_write"}),
                requested_disclosures=frozenset({"revision_acceptance_receipt", "consumer_current_revision_hash"}),
                interaction_id="other-invoice-grant",
            )
            raise RuntimeError("grant scope was treated as wildcard")
        except AuthorizationDenied:
            pass

        other_scope_authority = AuthorityKernel(
            principals=(PrincipalRecord("other-sync-principal", "service"),),
            credentials=(
                CredentialRecord(
                    "other-sync-credential",
                    "other-sync-principal",
                    SYNCHRONIZATION_BOUNDARY,
                    credential_digest("other-sync-material"),
                ),
            ),
            grants=(
                GrantRecord(
                    "other-invoice-only",
                    "other-sync-principal",
                    ACCEPT_CAPABILITY,
                    "invoice:invoice-other",
                    effect_scope=ACCEPT_EFFECTS,
                    disclosure_scope=ACCEPT_DISCLOSURES,
                ),
            ),
            policies=(
                CapabilityPolicy(
                    ACCEPT_CAPABILITY,
                    effects=ACCEPT_EFFECTS,
                    disclosure_allow=ACCEPT_DISCLOSURES,
                ),
            ),
        )
        other_scope_executor = CabinetWebRevisionAcceptExecutor(
            authority=other_scope_authority,
            typed_schema=bridge._accept_executor.typed_schema,
            records=bridge._records,
            card_validator=lambda _card: (),
        )
        try:
            other_scope_executor.execute(
                delivery,
                credential_id="other-sync-credential",
                credential_material="other-sync-material",
                interaction_id="other-grant-target-attempt",
            )
            raise RuntimeError("another invoice grant invoked F260001")
        except AuthorizationDenied:
            pass
        results.append(_pass("BRIDGE-005", "an invoice grant cannot authorize another invoice"))

        protected_request = {
            "delivery": delivery,
            "interaction_id": "protected-field-attempt",
            "principal": "caller-selected",
        }
        try:
            bridge.accept_revision(protected_request)
            raise RuntimeError("caller supplied a protected authority field")
        except Exception as exc:
            if str(exc) != "undeclared_request_fields":
                raise
        results.append(_pass("BRIDGE-006", "caller cannot supply authority or provider identities"))

        receipt = bridge.accept_revision(
            {"delivery": delivery, "interaction_id": "bridge-probe-accept"}
        )
        if receipt["outcome"] != "accepted" or receipt["invoice_id"] != TARGET_INVOICE_ID:
            raise RuntimeError("bounded revision receipt semantics changed")
        results.append(_pass("BRIDGE-007", "revision acceptance returns the verified bounded receipt"))

        content = _pdf_bytes()
        attach_request = {
            "invoice_id": TARGET_INVOICE_ID,
            "source_id": TARGET_SOURCE_ID,
            "filename": "bridge-probe.pdf",
            "content_base64": base64.b64encode(content).decode("ascii"),
            "interaction_id": "bridge-probe-attach",
        }
        original_publish = bridge._attach_adapter.byte_vault.publish

        def fail_after_metadata(*_args, **_kwargs):
            raise RuntimeError("simulated publication interruption")

        bridge._attach_adapter.byte_vault.publish = fail_after_metadata
        interrupted = False
        try:
            bridge.attach_source(attach_request)
        except InvoiceSourceAttachExecutionError:
            interrupted = True
        finally:
            bridge._attach_adapter.byte_vault.publish = original_publish
        if not interrupted:
            raise RuntimeError("simulated publication interruption did not interrupt")

        restarted = TrustedLocalCapabilityBridge.from_environment(bridge_env)
        restarted.start()
        attachment = restarted.attach_source(
            {**attach_request, "interaction_id": "bridge-probe-attach-replay"}
        )
        if attachment["items"][0]["result"] != "already_attached":
            raise RuntimeError("source adapter replay did not return bounded attached state")
        if str(vault_root) in repr(attachment):
            raise RuntimeError("attachment output disclosed vault path")
        results.append(_pass("BRIDGE-008", "source attachment uses protected adapter semantics without storage disclosure"))

        if hasattr(restarted, "invoke") or hasattr(restarted, "execute_module"):
            raise RuntimeError("generic caller-selected invocation surface exists")
        if tuple(restarted.readiness()["public_operations"]) != (
            "health/readiness",
            "invoice.archive.accept_revision",
            "invoice.source.attach",
        ):
            raise RuntimeError("bridge operation set is not closed")
        results.append(_pass("BRIDGE-009", "generic capability, module and function selection is impossible"))

        if not restarted.readiness()["recovery_complete"] or not restarted.readiness()["ready"]:
            raise RuntimeError("readiness preceded startup recovery")
        results.append(_pass("BRIDGE-010", "pending publication recovery completes before readiness"))

        events = restarted._records.read_audit()
        event_types = {event.event_type for event in events}
        if not {"cabinet_web.revision.accept", "invoice.source.attach", "invoice.source.attach.recovery"}.issubset(event_types):
            raise RuntimeError("durable executor audit evidence is incomplete")
        if restarted._authority is None or not restarted._authority.audit_evidence:
            raise RuntimeError("AuthorityKernel.invoke evidence is absent")
        results.append(_pass("BRIDGE-011", "both effects retain authority and durable audit evidence"))
        bridge = restarted
    except Exception as exc:
        next_id = f"BRIDGE-{len(results) + 1:03d}"
        results.append(_fail(next_id, exc))
    finally:
        if bridge is not None and bridge._records is not None:
            bridge._records.drop_probe_schema()
        shutil.rmtree(vault_root, ignore_errors=True)

    status = "pass" if len(results) == 11 and all(item.status == "PASS" for item in results) else "fail"
    return ProbeReport("spec_workbench_local_capability_bridge.v1", status, tuple(results))


def main() -> int:
    report = run_probe()
    print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    return 0 if report.status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
