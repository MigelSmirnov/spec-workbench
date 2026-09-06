#!/usr/bin/env python3
"""Executable Cabinet_web -> local-box confirmed revision acceptance.

The runtime implements the transport-independent cabinet-web-sync-v1 relation.
It receives one exact confirmed Card revision, validates it through an injected
Cabinet_web-contract validator, persists an immutable revision plus current
invoice/source expectation state, and returns a bounded idempotent receipt.
"""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Sequence

from authority_kernel import (
    SYNCHRONIZATION_BOUNDARY,
    AuthorityError,
    AuthorityKernel,
    AuthorizationDecision,
)
from cabinet_web_revision_accept_models import DELIVERY_NAMESPACE, REVISION_NAMESPACE, models
from invoice_source_attach_models import INVOICE_NAMESPACE, empty_source_state
from postgres_record_kernel import PostgresRecordKernel
from typed_schema_kernel import TypedSchemaKernel


CAPABILITY = "invoice.archive.accept_revision"
EFFECTS = frozenset({"archive_revision_write", "archive_source_expectation_write"})
DISCLOSURES = frozenset({"revision_acceptance_receipt", "consumer_current_revision_hash"})
_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")

CardValidator = Callable[[dict[str, Any]], Sequence[Mapping[str, Any]]]


class CabinetWebRevisionAcceptError(RuntimeError):
    pass


class CabinetWebRevisionAcceptRejected(CabinetWebRevisionAcceptError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def canonical_content_hash(card: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        dict(card),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def revision_resource_id(invoice_id: str, content_hash: str) -> str:
    return json.dumps([invoice_id, content_hash], ensure_ascii=True, separators=(",", ":"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _is_timezone_datetime(value: str) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


class CabinetWebRevisionAcceptExecutor:
    def __init__(
        self,
        *,
        authority: AuthorityKernel,
        typed_schema: TypedSchemaKernel,
        records: PostgresRecordKernel,
        card_validator: CardValidator,
    ) -> None:
        self.authority = authority
        self.typed_schema = typed_schema
        self.records = records
        self.card_validator = card_validator

    @staticmethod
    def resource_scope(invoice_id: str) -> str:
        return f"invoice:{invoice_id}"

    def _receipt(
        self,
        *,
        delivery_id: str,
        invoice_id: str,
        card_content_hash: str,
        source_git_commit_sha: str,
        outcome: str,
        accepted_at: str | None,
        backend_current_content_hash: str | None,
        error_code: str | None = None,
    ):
        _, OutputModel = models()
        return self.typed_schema.validate_output(
            OutputModel,
            {
                "contract_version": "cabinet-backend-sync-receipt-v1",
                "delivery_id": delivery_id,
                "invoice_id": invoice_id,
                "card_content_hash": card_content_hash,
                "source_git_commit_sha": source_git_commit_sha,
                "outcome": outcome,
                "accepted_at": accepted_at,
                "backend_current_content_hash": backend_current_content_hash,
                "error_code": error_code,
            },
        )

    def _append_audit(
        self,
        tx,
        *,
        decision: AuthorizationDecision,
        invoice_id: str,
        delivery_id: str,
        card_content_hash: str,
        result: str,
        reason_code: str | None = None,
    ) -> None:
        tx.append_audit(
            uuid.uuid4().hex,
            "cabinet_web.revision.accept",
            invoice_id,
            {
                "principal_id": decision.principal_id,
                "capability": CAPABILITY,
                "invoice_id": invoice_id,
                "delivery_id": delivery_id,
                "card_content_hash": card_content_hash,
                "interaction_id": decision.actor.interaction_id,
                "declared_effects": sorted(decision.effects),
                "result": result,
                "reason_code": reason_code,
            },
        )

    def _persist_authority_refusal(self) -> None:
        if not self.authority.audit_evidence:
            return
        event = self.authority.audit_evidence[-1]
        with self.records.transaction() as tx:
            tx.append_audit(
                uuid.uuid4().hex,
                "authority.refusal",
                event.resource_scope_or_target,
                {
                    "principal_id_or_unknown": event.principal_id_or_unknown,
                    "capability": event.capability_or_operation,
                    "result": event.result,
                    "reason_code": event.reason_code,
                    "declared_effects": list(event.declared_effects),
                },
            )

    @staticmethod
    def _validate_envelope(delivery) -> None:
        if delivery.contract_version != "cabinet-web-sync-v1":
            raise CabinetWebRevisionAcceptRejected("unsupported_sync_contract")
        if delivery.producer_repository != "MigelSmirnov/Cabinet_web":
            raise CabinetWebRevisionAcceptRejected("unexpected_producer_repository")
        if not delivery.delivery_id:
            raise CabinetWebRevisionAcceptRejected("delivery_id_required")
        if not delivery.invoice_id.startswith("invoice-"):
            raise CabinetWebRevisionAcceptRejected("invalid_invoice_id")
        if delivery.card_contract_version != 1:
            raise CabinetWebRevisionAcceptRejected("unsupported_card_version")
        if delivery.card_status != "confirmed":
            raise CabinetWebRevisionAcceptRejected("card_not_confirmed")
        if not _HASH_RE.fullmatch(delivery.card_content_hash):
            raise CabinetWebRevisionAcceptRejected("invalid_card_content_hash")
        if delivery.base_backend_content_hash is not None and not _HASH_RE.fullmatch(
            delivery.base_backend_content_hash
        ):
            raise CabinetWebRevisionAcceptRejected("invalid_base_backend_content_hash")
        if not _COMMIT_RE.fullmatch(delivery.source_git_commit_sha):
            raise CabinetWebRevisionAcceptRejected("invalid_source_git_commit_sha")
        if delivery.card_repository_path != f"data/cards/{delivery.invoice_id}/card.json":
            raise CabinetWebRevisionAcceptRejected("card_repository_path_mismatch")
        if not _is_timezone_datetime(delivery.emitted_at):
            raise CabinetWebRevisionAcceptRejected("invalid_emitted_at")

    def _validate_card(self, delivery) -> tuple[Mapping[str, Any], ...]:
        card = delivery.card_document
        if card.get("id") != delivery.invoice_id:
            raise CabinetWebRevisionAcceptRejected("card_invoice_identity_mismatch")
        if card.get("card_type") != "invoice" or card.get("card_version") != 1:
            raise CabinetWebRevisionAcceptRejected("card_contract_mismatch")
        if card.get("status") != "confirmed":
            raise CabinetWebRevisionAcceptRejected("card_not_confirmed")
        if canonical_content_hash(card) != delivery.card_content_hash:
            raise CabinetWebRevisionAcceptRejected("card_content_hash_mismatch")

        issues = tuple(dict(item) for item in self.card_validator(deepcopy(card)))
        if any(item.get("severity", "error") == "error" for item in issues):
            raise CabinetWebRevisionAcceptRejected("cabinet_web_card_validation_failed")

        source = card.get("source")
        if not isinstance(source, Mapping) or not isinstance(source.get("source_id"), str):
            raise CabinetWebRevisionAcceptRejected("source_identity_missing")
        return issues

    @staticmethod
    def _source_expectation(card: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
        source = card["source"]
        source_id = str(source["source_id"])
        return source_id, {
            "expected_hash": None,
            "media_type": None,
            "required": source.get("file_status") == "stored",
            "card_source_kind": source.get("kind"),
        }

    def execute(
        self,
        payload: Mapping[str, Any],
        *,
        credential_id: str,
        credential_material: str,
        interaction_id: str,
    ):
        InputModel, _ = models()
        delivery = self.typed_schema.validate_input(InputModel, payload)
        invoice_id = str(delivery.invoice_id)

        def protected_operation(decision: AuthorizationDecision):
            try:
                self._validate_envelope(delivery)
                validation_issues = self._validate_card(delivery)
                return self._accept_authorized(delivery, validation_issues, decision)
            except CabinetWebRevisionAcceptRejected as exc:
                current = self.records.read_record(INVOICE_NAMESPACE, invoice_id)
                current_hash = None if current is None else current.payload.get("current_content_hash")
                with self.records.transaction() as tx:
                    self._append_audit(
                        tx,
                        decision=decision,
                        invoice_id=invoice_id,
                        delivery_id=str(delivery.delivery_id),
                        card_content_hash=str(delivery.card_content_hash),
                        result="rejected",
                        reason_code=exc.code,
                    )
                return self._receipt(
                    delivery_id=str(delivery.delivery_id),
                    invoice_id=invoice_id,
                    card_content_hash=str(delivery.card_content_hash),
                    source_git_commit_sha=str(delivery.source_git_commit_sha),
                    outcome="rejected_card" if exc.code.startswith("card_") or exc.code.startswith("cabinet_web_") or exc.code == "source_identity_missing" else "rejected_contract",
                    accepted_at=None,
                    backend_current_content_hash=None if current_hash is None else str(current_hash),
                    error_code=exc.code,
                )

        try:
            return self.authority.invoke(
                credential_id=credential_id,
                credential_material=credential_material,
                required_boundary=SYNCHRONIZATION_BOUNDARY,
                capability=CAPABILITY,
                resource_scope=self.resource_scope(invoice_id),
                interaction_id=interaction_id,
                requested_effects=EFFECTS,
                requested_disclosures=DISCLOSURES,
                operation=protected_operation,
            )
        except AuthorityError:
            self._persist_authority_refusal()
            raise

    def _accept_authorized(self, delivery, validation_issues, decision: AuthorizationDecision):
        invoice_id = str(delivery.invoice_id)
        delivery_id = str(delivery.delivery_id)
        content_hash = str(delivery.card_content_hash)
        revision_key = revision_resource_id(invoice_id, content_hash)
        accepted_at = _now()

        with self.records.transaction() as tx:
            tx.lock_resource(DELIVERY_NAMESPACE, delivery_id)
            tx.lock_resource(INVOICE_NAMESPACE, invoice_id)
            tx.lock_resource(REVISION_NAMESPACE, revision_key)

            prior_delivery = tx.get_record(DELIVERY_NAMESPACE, delivery_id)
            current = tx.get_record(INVOICE_NAMESPACE, invoice_id)
            current_hash = None if current is None else current.payload.get("current_content_hash")

            if prior_delivery is not None:
                if (
                    prior_delivery.payload.get("invoice_id") != invoice_id
                    or prior_delivery.payload.get("card_content_hash") != content_hash
                ):
                    self._append_audit(
                        tx,
                        decision=decision,
                        invoice_id=invoice_id,
                        delivery_id=delivery_id,
                        card_content_hash=content_hash,
                        result="delivery_identity_conflict",
                        reason_code="delivery_identity_conflict",
                    )
                    return self._receipt(
                        delivery_id=delivery_id,
                        invoice_id=invoice_id,
                        card_content_hash=content_hash,
                        source_git_commit_sha=str(delivery.source_git_commit_sha),
                        outcome="delivery_identity_conflict",
                        accepted_at=None,
                        backend_current_content_hash=None if current_hash is None else str(current_hash),
                        error_code="delivery_identity_conflict",
                    )
                return self._receipt(
                    delivery_id=delivery_id,
                    invoice_id=invoice_id,
                    card_content_hash=content_hash,
                    source_git_commit_sha=str(prior_delivery.payload["source_git_commit_sha"]),
                    outcome="already_accepted",
                    accepted_at=str(prior_delivery.payload["accepted_at"]),
                    backend_current_content_hash=None if current_hash is None else str(current_hash),
                    error_code=None,
                )

            if current is None:
                if delivery.base_backend_content_hash is not None:
                    self._append_audit(
                        tx,
                        decision=decision,
                        invoice_id=invoice_id,
                        delivery_id=delivery_id,
                        card_content_hash=content_hash,
                        result="reconciliation_required",
                        reason_code="unexpected_non_null_base",
                    )
                    return self._receipt(
                        delivery_id=delivery_id,
                        invoice_id=invoice_id,
                        card_content_hash=content_hash,
                        source_git_commit_sha=str(delivery.source_git_commit_sha),
                        outcome="reconciliation_required",
                        accepted_at=None,
                        backend_current_content_hash=None,
                        error_code="unexpected_non_null_base",
                    )
            elif current_hash != content_hash:
                if delivery.base_backend_content_hash != current_hash:
                    self._append_audit(
                        tx,
                        decision=decision,
                        invoice_id=invoice_id,
                        delivery_id=delivery_id,
                        card_content_hash=content_hash,
                        result="reconciliation_required",
                        reason_code="backend_base_revision_mismatch",
                    )
                    return self._receipt(
                        delivery_id=delivery_id,
                        invoice_id=invoice_id,
                        card_content_hash=content_hash,
                        source_git_commit_sha=str(delivery.source_git_commit_sha),
                        outcome="reconciliation_required",
                        accepted_at=None,
                        backend_current_content_hash=str(current_hash),
                        error_code="backend_base_revision_mismatch",
                    )
            else:
                tx.put_record(
                    DELIVERY_NAMESPACE,
                    delivery_id,
                    {
                        "invoice_id": invoice_id,
                        "card_content_hash": content_hash,
                        "source_git_commit_sha": str(delivery.source_git_commit_sha),
                        "accepted_at": accepted_at,
                    },
                )
                self._append_audit(
                    tx,
                    decision=decision,
                    invoice_id=invoice_id,
                    delivery_id=delivery_id,
                    card_content_hash=content_hash,
                    result="already_accepted",
                )
                return self._receipt(
                    delivery_id=delivery_id,
                    invoice_id=invoice_id,
                    card_content_hash=content_hash,
                    source_git_commit_sha=str(delivery.source_git_commit_sha),
                    outcome="already_accepted",
                    accepted_at=accepted_at,
                    backend_current_content_hash=content_hash,
                    error_code=None,
                )

            prior_revision = tx.get_record(REVISION_NAMESPACE, revision_key)
            if prior_revision is None:
                tx.put_record(
                    REVISION_NAMESPACE,
                    revision_key,
                    {
                        "invoice_id": invoice_id,
                        "card_content_hash": content_hash,
                        "card_version": int(delivery.card_contract_version),
                        "card_status": str(delivery.card_status),
                        "card_document": deepcopy(delivery.card_document),
                        "source_git_commit_sha": str(delivery.source_git_commit_sha),
                        "card_repository_path": str(delivery.card_repository_path),
                        "received_at": accepted_at,
                        "received_by_principal_id": decision.principal_id,
                        "predecessor_content_hash": None if current_hash is None else str(current_hash),
                        "validation_issues": [dict(item) for item in validation_issues],
                    },
                )

            source_id, expected = self._source_expectation(delivery.card_document)
            source_states: dict[str, Any] = {}
            prior_revisions: list[str] = []
            if current is not None:
                prior_revisions = [str(item) for item in current.payload.get("accepted_revision_hashes", [])]
                prior_states = current.payload.get("source_states")
                if isinstance(prior_states, Mapping) and source_id in prior_states:
                    source_states[source_id] = deepcopy(prior_states[source_id])
            if source_id not in source_states:
                source_states[source_id] = empty_source_state()
            if content_hash not in prior_revisions:
                prior_revisions.append(content_hash)

            next_invoice = {
                "invoice_id": invoice_id,
                "accepted_archive_target": True,
                "current_content_hash": content_hash,
                "accepted_revision_hashes": prior_revisions,
                "accepted_card_document": deepcopy(delivery.card_document),
                "accepted_card_content_hash": content_hash,
                "source_git_commit_sha": str(delivery.source_git_commit_sha),
                "card_repository_path": str(delivery.card_repository_path),
                "expected_sources": {source_id: expected},
                "source_states": source_states,
            }
            tx.put_record(
                INVOICE_NAMESPACE,
                invoice_id,
                next_invoice,
                expected_version=None if current is None else current.version,
            )
            tx.put_record(
                DELIVERY_NAMESPACE,
                delivery_id,
                {
                    "invoice_id": invoice_id,
                    "card_content_hash": content_hash,
                    "source_git_commit_sha": str(delivery.source_git_commit_sha),
                    "accepted_at": accepted_at,
                },
            )
            self._append_audit(
                tx,
                decision=decision,
                invoice_id=invoice_id,
                delivery_id=delivery_id,
                card_content_hash=content_hash,
                result="accepted",
            )

        return self._receipt(
            delivery_id=delivery_id,
            invoice_id=invoice_id,
            card_content_hash=content_hash,
            source_git_commit_sha=str(delivery.source_git_commit_sha),
            outcome="accepted",
            accepted_at=accepted_at,
            backend_current_content_hash=content_hash,
            error_code=None,
        )
