#!/usr/bin/env python3
"""First executable invoice.source.attach case over verified generic providers."""
from __future__ import annotations

import hashlib
import json
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Mapping, Optional

from authority_kernel import (
    LOCAL_AGENT_BOUNDARY,
    AuthorityError,
    AuthorityKernel,
    AuthorizationDecision,
)
from bounded_content_validation_kernel import (
    BoundedContentValidationKernel,
    ContentValidationRejected,
)
from local_private_byte_vault import ByteVaultError, ByteVaultRecoveryError, LocalPrivateByteVault
from postgres_record_kernel import PostgresRecordKernel, StoredRecord
from typed_schema_kernel import TypedSchemaKernel, TypedSchemaValidationError


CAPABILITY = "invoice.source.attach"
INVOICE_NAMESPACE = "cabinet.invoice_source_state"
PUBLICATION_NAMESPACE = "cabinet.source_publication"
EFFECTS = frozenset({"source_byte_write", "archive_source_evidence_write"})
DISCLOSURES = frozenset(
    {"per_file_safe_result", "source_ids", "content_hashes", "resulting_source_status"}
)


class InvoiceSourceAttachError(RuntimeError):
    pass


class InvoiceSourceAttachRejected(InvoiceSourceAttachError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class InvoiceSourceAttachExecutionError(InvoiceSourceAttachError):
    pass


class _PendingPublicationFound(Exception):
    pass


def _models():
    from pydantic import BaseModel, StrictBytes, StrictInt, StrictStr  # type: ignore

    if hasattr(BaseModel, "model_validate"):
        from pydantic import ConfigDict  # type: ignore

        class ClosedModel(BaseModel):
            model_config = ConfigDict(extra="forbid")

    else:

        class ClosedModel(BaseModel):
            class Config:
                extra = "forbid"

    class LocalSourceFileModel(ClosedModel):
        filename: StrictStr
        media_type: StrictStr
        content: StrictBytes
        expected_source_id: Optional[StrictStr] = None
        expected_content_hash: Optional[StrictStr] = None

    class ContentReferenceModel(ClosedModel):
        content_kind: StrictStr
        content_id: StrictStr
        content_hash: StrictStr
        size_bytes: Optional[StrictInt] = None
        media_type: Optional[StrictStr] = None

    class AttachLocalSourceInputModel(ClosedModel):
        invoice_id: StrictStr
        files: tuple[LocalSourceFileModel, ...]
        expected_sources: tuple[ContentReferenceModel, ...]

    class SourceAttachmentItemResultModel(ClosedModel):
        filename: StrictStr
        source_id: Optional[StrictStr] = None
        content_hash: StrictStr
        result: StrictStr
        safe_error_code: Optional[StrictStr] = None

    class SourceStatusModel(ClosedModel):
        invoice_id: StrictStr
        available_source_ids: tuple[StrictStr, ...]
        missing_source_ids: tuple[StrictStr, ...]
        failed_source_ids: tuple[StrictStr, ...]
        completeness: StrictStr
        active_loss_decision_ids: tuple[StrictStr, ...]
        complete: bool
        observed_at: datetime

    class SourceAttachmentBatchResultModel(ClosedModel):
        invoice_id: StrictStr
        items: tuple[SourceAttachmentItemResultModel, ...]
        source_status: SourceStatusModel

    return AttachLocalSourceInputModel, SourceAttachmentBatchResultModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _publication_resource_id(invoice_id: str, source_id: str) -> str:
    return json.dumps([invoice_id, source_id], ensure_ascii=False, separators=(",", ":"))


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _empty_source_state() -> dict[str, Any]:
    return {
        "status": "missing",
        "content_hash": None,
        "size_bytes": None,
        "media_type": None,
        "filename": None,
        "attached_by_principal_id": None,
        "interaction_id": None,
        "pending_publication_id": None,
        "pending_content_hash": None,
    }


class InvoiceSourceAttachExecutor:
    """Execute the declared single expected-source attachment case."""

    def __init__(
        self,
        *,
        authority: AuthorityKernel,
        typed_schema: TypedSchemaKernel,
        records: PostgresRecordKernel,
        byte_vault: LocalPrivateByteVault,
        content_validation: BoundedContentValidationKernel,
    ) -> None:
        self.authority = authority
        self.typed_schema = typed_schema
        self.records = records
        self.byte_vault = byte_vault
        self.content_validation = content_validation

    @staticmethod
    def _resource_scope(invoice_id: str) -> str:
        return f"invoice:{invoice_id}"

    def _load_invoice(self, invoice_id: str) -> StoredRecord:
        record = self.records.read_record(INVOICE_NAMESPACE, invoice_id)
        if record is None or record.payload.get("accepted_archive_target") is not True:
            raise InvoiceSourceAttachRejected("accepted_archive_target_not_found")
        if record.payload.get("invoice_id") != invoice_id:
            raise InvoiceSourceAttachExecutionError("invoice state identity mismatch")
        return record

    @staticmethod
    def _expected_source(payload: Mapping[str, Any], source_id: str) -> Mapping[str, Any]:
        expected_sources = payload.get("expected_sources")
        if not isinstance(expected_sources, Mapping) or source_id not in expected_sources:
            raise InvoiceSourceAttachRejected("expected_source_not_found")
        expected = expected_sources[source_id]
        if not isinstance(expected, Mapping):
            raise InvoiceSourceAttachExecutionError("expected source state is invalid")
        return expected

    @staticmethod
    def _source_state(payload: Mapping[str, Any], source_id: str) -> Mapping[str, Any]:
        states = payload.get("source_states")
        if not isinstance(states, Mapping) or source_id not in states:
            raise InvoiceSourceAttachRejected("source_state_not_found")
        state = states[source_id]
        if not isinstance(state, Mapping):
            raise InvoiceSourceAttachExecutionError("source state is invalid")
        return state

    @staticmethod
    def _safe_status_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
        invoice_id = str(payload["invoice_id"])
        expected_sources = payload.get("expected_sources", {})
        source_states = payload.get("source_states", {})
        if not isinstance(expected_sources, Mapping) or not isinstance(source_states, Mapping):
            raise InvoiceSourceAttachExecutionError("invoice source state shape is invalid")

        available: list[str] = []
        missing: list[str] = []
        failed: list[str] = []
        for source_id, expected in expected_sources.items():
            if not isinstance(expected, Mapping) or expected.get("required") is not True:
                continue
            state = source_states.get(source_id, {})
            status = state.get("status") if isinstance(state, Mapping) else None
            if status == "available":
                available.append(str(source_id))
            elif status == "failed":
                failed.append(str(source_id))
            else:
                missing.append(str(source_id))

        complete = not missing and not failed
        return {
            "invoice_id": invoice_id,
            "available_source_ids": tuple(sorted(available)),
            "missing_source_ids": tuple(sorted(missing)),
            "failed_source_ids": tuple(sorted(failed)),
            "completeness": "complete" if complete else "incomplete",
            "active_loss_decision_ids": (),
            "complete": complete,
            "observed_at": _utcnow(),
        }

    def _safe_result(
        self,
        *,
        invoice_payload: Mapping[str, Any],
        filename: str,
        source_id: str,
        content_hash: str,
        result: str,
        safe_error_code: str | None = None,
    ):
        _, OutputModel = _models()
        payload = {
            "invoice_id": str(invoice_payload["invoice_id"]),
            "items": (
                {
                    "filename": filename,
                    "source_id": source_id,
                    "content_hash": content_hash,
                    "result": result,
                    "safe_error_code": safe_error_code,
                },
            ),
            "source_status": self._safe_status_payload(invoice_payload),
        }
        return self.typed_schema.validate_output(OutputModel, payload)

    def _persist_authority_refusal(self) -> None:
        evidence = self.authority.audit_evidence
        if not evidence:
            return
        item = evidence[-1]
        with self.records.transaction() as tx:
            tx.append_audit(
                uuid.uuid4().hex,
                "authority.refusal",
                item.resource_scope_or_target,
                {
                    "principal_id_or_unknown": item.principal_id_or_unknown,
                    "capability": item.capability_or_operation,
                    "result": item.result,
                    "reason_code": item.reason_code,
                    "declared_effects": list(item.declared_effects),
                },
            )

    def _append_effect_audit(
        self,
        tx,
        *,
        decision: AuthorizationDecision,
        invoice_id: str,
        source_id: str,
        content_hash: str,
        result: str,
    ) -> None:
        tx.append_audit(
            uuid.uuid4().hex,
            "invoice.source.attach",
            invoice_id,
            {
                "principal_id": decision.principal_id,
                "capability": CAPABILITY,
                "invoice_id": invoice_id,
                "source_id": source_id,
                "interaction_id": decision.actor.interaction_id,
                "input_content_digest": content_hash,
                "declared_effects": sorted(decision.effects),
                "result": result,
            },
        )

    def execute(
        self,
        payload: Mapping[str, Any],
        *,
        credential_id: str,
        credential_material: str,
        interaction_id: str,
    ):
        InputModel, _ = _models()
        try:
            validated = self.typed_schema.validate_input(InputModel, payload)
        except TypedSchemaValidationError:
            raise

        if len(validated.files) != 1:
            raise InvoiceSourceAttachRejected("execution_case_requires_exactly_one_file")

        invoice_id = str(validated.invoice_id)
        file = validated.files[0]
        source_id = file.expected_source_id
        if not source_id:
            raise InvoiceSourceAttachRejected("expected_source_id_required")

        def protected_operation(decision: AuthorizationDecision):
            return self._execute_authorized(validated, file, source_id, decision)

        try:
            return self.authority.invoke(
                credential_id=credential_id,
                credential_material=credential_material,
                required_boundary=LOCAL_AGENT_BOUNDARY,
                capability=CAPABILITY,
                resource_scope=self._resource_scope(invoice_id),
                interaction_id=interaction_id,
                requested_effects=EFFECTS,
                requested_disclosures=DISCLOSURES,
                operation=protected_operation,
            )
        except AuthorityError:
            self._persist_authority_refusal()
            raise

    def _execute_authorized(self, validated, file, source_id: str, decision: AuthorizationDecision):
        invoice_id = str(validated.invoice_id)
        invoice_record = self._load_invoice(invoice_id)
        expected = self._expected_source(invoice_record.payload, source_id)
        source_state = self._source_state(invoice_record.payload, source_id)

        input_matches = [item for item in validated.expected_sources if item.content_id == source_id]
        if len(input_matches) != 1:
            raise InvoiceSourceAttachRejected("expected_source_input_binding_required")
        input_expected = input_matches[0]

        expected_media_type = expected.get("media_type")
        if expected_media_type != file.media_type:
            raise InvoiceSourceAttachRejected("expected_source_media_type_mismatch")
        if input_expected.media_type is not None and input_expected.media_type != expected_media_type:
            raise InvoiceSourceAttachRejected("caller_expected_media_type_mismatch")

        try:
            validation = self.content_validation.validate(bytes(file.content), str(file.media_type))
        except ContentValidationRejected as exc:
            raise InvoiceSourceAttachRejected("content_validation_rejected") from exc

        calculated_hash = validation.content_hash
        durable_expected_hash = expected.get("expected_hash")
        caller_hashes = [
            value
            for value in (file.expected_content_hash, input_expected.content_hash)
            if value is not None
        ]
        if any(value != calculated_hash for value in caller_hashes):
            raise InvoiceSourceAttachRejected("caller_expected_content_hash_mismatch")
        if durable_expected_hash is not None and durable_expected_hash != calculated_hash:
            raise InvoiceSourceAttachRejected("durable_expected_content_hash_mismatch")

        if source_state.get("status") == "available":
            publication = self.records.read_record(
                PUBLICATION_NAMESPACE, _publication_resource_id(invoice_id, source_id)
            )
            if (
                source_state.get("content_hash") == calculated_hash
                and publication is not None
                and publication.payload.get("state") == "published"
                and self.byte_vault.verify(
                    str(publication.payload["final_reference"]),
                    calculated_hash,
                    len(file.content),
                )
            ):
                with self.records.transaction() as tx:
                    self._append_effect_audit(
                        tx,
                        decision=decision,
                        invoice_id=invoice_id,
                        source_id=source_id,
                        content_hash=calculated_hash,
                        result="already_attached",
                    )
                return self._safe_result(
                    invoice_payload=invoice_record.payload,
                    filename=str(file.filename),
                    source_id=source_id,
                    content_hash=calculated_hash,
                    result="already_attached",
                )
            raise InvoiceSourceAttachRejected("source_content_conflict")

        staged = self.byte_vault.stage(bytes(file.content), calculated_hash, len(file.content))
        metadata_committed = False
        publication_key = _publication_resource_id(invoice_id, source_id)

        try:
            with self.records.transaction() as tx:
                tx.lock_resource(INVOICE_NAMESPACE, invoice_id)
                tx.lock_resource(PUBLICATION_NAMESPACE, publication_key)

                locked_invoice = tx.get_record(INVOICE_NAMESPACE, invoice_id)
                if locked_invoice is None or locked_invoice.payload.get("accepted_archive_target") is not True:
                    raise InvoiceSourceAttachRejected("accepted_archive_target_not_found")
                locked_expected = self._expected_source(locked_invoice.payload, source_id)
                locked_state = self._source_state(locked_invoice.payload, source_id)
                if locked_expected.get("expected_hash") != durable_expected_hash:
                    raise InvoiceSourceAttachRejected("expected_source_changed_during_attachment")
                if locked_expected.get("media_type") != expected_media_type:
                    raise InvoiceSourceAttachRejected("expected_source_changed_during_attachment")

                existing_publication = tx.get_record(PUBLICATION_NAMESPACE, publication_key)
                if locked_state.get("status") == "available":
                    if locked_state.get("content_hash") == calculated_hash:
                        raise _PendingPublicationFound("published_or_settled")
                    raise InvoiceSourceAttachRejected("source_content_conflict")

                if existing_publication is not None:
                    state = existing_publication.payload.get("state")
                    existing_hash = existing_publication.payload.get("content_hash")
                    if existing_hash != calculated_hash:
                        raise InvoiceSourceAttachRejected("source_content_conflict")
                    if state in {"metadata_committed", "published"}:
                        raise _PendingPublicationFound(state)
                    raise InvoiceSourceAttachRejected("previous_publication_failed")

                publication_id = uuid.uuid4().hex
                publication_payload = {
                    "publication_id": publication_id,
                    "invoice_id": invoice_id,
                    "source_id": source_id,
                    "content_hash": calculated_hash,
                    "size_bytes": len(file.content),
                    "staging_reference": staged.staging_reference,
                    "final_reference": staged.final_reference,
                    "state": "metadata_committed",
                }
                tx.put_record(PUBLICATION_NAMESPACE, publication_key, publication_payload)

                next_invoice = deepcopy(locked_invoice.payload)
                next_state = deepcopy(next_invoice["source_states"][source_id])
                next_state.update(
                    {
                        "status": "missing",
                        "pending_publication_id": publication_id,
                        "pending_content_hash": calculated_hash,
                        "attached_by_principal_id": decision.principal_id,
                        "interaction_id": decision.actor.interaction_id,
                    }
                )
                next_invoice["source_states"][source_id] = next_state
                tx.put_record(
                    INVOICE_NAMESPACE,
                    invoice_id,
                    next_invoice,
                    expected_version=locked_invoice.version,
                )
                self._append_effect_audit(
                    tx,
                    decision=decision,
                    invoice_id=invoice_id,
                    source_id=source_id,
                    content_hash=calculated_hash,
                    result="metadata_committed",
                )
            metadata_committed = True
        except _PendingPublicationFound:
            self.byte_vault.remove_staging(staged.staging_reference)
            return self._recover_pending_authorized(
                invoice_id=invoice_id,
                source_id=source_id,
                decision=decision,
                filename=str(file.filename),
                expected_content_hash=calculated_hash,
            )
        except Exception:
            if not metadata_committed:
                self.byte_vault.remove_staging(staged.staging_reference)
            raise

        try:
            final_reference = self.byte_vault.publish(
                staged.staging_reference,
                calculated_hash,
                len(file.content),
            )
            if not self.byte_vault.verify(final_reference, calculated_hash, len(file.content)):
                raise InvoiceSourceAttachExecutionError("final_byte_verification_failed")
        except Exception as exc:
            raise InvoiceSourceAttachExecutionError("publication_pending_recovery") from exc

        return self._settle_published(
            invoice_id=invoice_id,
            source_id=source_id,
            content_hash=calculated_hash,
            filename=str(file.filename),
            media_type=str(file.media_type),
            size_bytes=len(file.content),
            decision=decision,
            result="attached",
        )

    def _settle_published(
        self,
        *,
        invoice_id: str,
        source_id: str,
        content_hash: str,
        filename: str,
        media_type: str,
        size_bytes: int,
        decision: AuthorizationDecision | None,
        result: str,
    ):
        publication_key = _publication_resource_id(invoice_id, source_id)
        with self.records.transaction() as tx:
            tx.lock_resource(INVOICE_NAMESPACE, invoice_id)
            tx.lock_resource(PUBLICATION_NAMESPACE, publication_key)
            invoice = tx.get_record(INVOICE_NAMESPACE, invoice_id)
            publication = tx.get_record(PUBLICATION_NAMESPACE, publication_key)
            if invoice is None or publication is None:
                raise InvoiceSourceAttachExecutionError("pending publication state missing")
            if publication.payload.get("content_hash") != content_hash:
                raise InvoiceSourceAttachExecutionError("pending publication content changed")
            if publication.payload.get("state") not in {"metadata_committed", "published"}:
                raise InvoiceSourceAttachExecutionError("pending publication is not recoverable")
            if not self.byte_vault.verify(
                str(publication.payload["final_reference"]), content_hash, size_bytes
            ):
                raise InvoiceSourceAttachExecutionError("final bytes not verified during settlement")

            if publication.payload.get("state") != "published":
                next_publication = deepcopy(publication.payload)
                next_publication["state"] = "published"
                tx.put_record(
                    PUBLICATION_NAMESPACE,
                    publication_key,
                    next_publication,
                    expected_version=publication.version,
                )

            next_invoice = deepcopy(invoice.payload)
            state = deepcopy(next_invoice["source_states"][source_id])
            state.update(
                {
                    "status": "available",
                    "content_hash": content_hash,
                    "size_bytes": size_bytes,
                    "media_type": media_type,
                    "filename": filename,
                    "pending_publication_id": None,
                    "pending_content_hash": None,
                }
            )
            next_invoice["source_states"][source_id] = state
            tx.put_record(
                INVOICE_NAMESPACE,
                invoice_id,
                next_invoice,
                expected_version=invoice.version,
            )
            principal_id = state.get("attached_by_principal_id") or "host-recovery"
            interaction = state.get("interaction_id") or "host-recovery"
            if decision is None:
                recovery_payload = {
                    "principal_id": principal_id,
                    "capability": CAPABILITY,
                    "invoice_id": invoice_id,
                    "source_id": source_id,
                    "interaction_id": interaction,
                    "input_content_digest": content_hash,
                    "declared_effects": sorted(EFFECTS),
                    "result": result,
                }
                tx.append_audit(
                    uuid.uuid4().hex,
                    "invoice.source.attach.recovery",
                    invoice_id,
                    recovery_payload,
                )
            else:
                self._append_effect_audit(
                    tx,
                    decision=decision,
                    invoice_id=invoice_id,
                    source_id=source_id,
                    content_hash=content_hash,
                    result=result,
                )

        settled = self._load_invoice(invoice_id)
        return self._safe_result(
            invoice_payload=settled.payload,
            filename=filename,
            source_id=source_id,
            content_hash=content_hash,
            result=result,
        )

    def _recover_pending_authorized(
        self,
        *,
        invoice_id: str,
        source_id: str,
        decision: AuthorizationDecision,
        filename: str,
        expected_content_hash: str,
    ):
        publication = self.records.read_record(
            PUBLICATION_NAMESPACE, _publication_resource_id(invoice_id, source_id)
        )
        if publication is None:
            current = self._load_invoice(invoice_id)
            state = self._source_state(current.payload, source_id)
            if state.get("status") == "available" and state.get("content_hash") == expected_content_hash:
                return self._safe_result(
                    invoice_payload=current.payload,
                    filename=filename,
                    source_id=source_id,
                    content_hash=expected_content_hash,
                    result="already_attached",
                )
            raise InvoiceSourceAttachExecutionError("pending publication missing")
        if publication.payload.get("content_hash") != expected_content_hash:
            raise InvoiceSourceAttachRejected("source_content_conflict")
        final_reference = self.byte_vault.recover_required(
            str(publication.payload["staging_reference"]),
            expected_content_hash,
            int(publication.payload["size_bytes"]),
        )
        if not self.byte_vault.verify(
            final_reference, expected_content_hash, int(publication.payload["size_bytes"])
        ):
            raise InvoiceSourceAttachExecutionError("recovered final bytes failed verification")
        invoice = self._load_invoice(invoice_id)
        state = self._source_state(invoice.payload, source_id)
        return self._settle_published(
            invoice_id=invoice_id,
            source_id=source_id,
            content_hash=expected_content_hash,
            filename=str(state.get("filename") or filename),
            media_type=str(state.get("media_type") or self._expected_source(invoice.payload, source_id)["media_type"]),
            size_bytes=int(publication.payload["size_bytes"]),
            decision=decision,
            result="recovered",
        )

    def recover_pending_publication(self, *, invoice_id: str, source_id: str):
        """Host startup recovery for a previously committed publication; no caller authority surface."""
        publication_key = _publication_resource_id(invoice_id, source_id)
        publication = self.records.read_record(PUBLICATION_NAMESPACE, publication_key)
        if publication is None:
            raise InvoiceSourceAttachExecutionError("pending publication missing")
        if publication.payload.get("state") == "published":
            invoice = self._load_invoice(invoice_id)
            state = self._source_state(invoice.payload, source_id)
            return self._safe_result(
                invoice_payload=invoice.payload,
                filename=str(state.get("filename") or "recovered"),
                source_id=source_id,
                content_hash=str(publication.payload["content_hash"]),
                result="already_attached",
            )
        if publication.payload.get("state") != "metadata_committed":
            raise InvoiceSourceAttachExecutionError("publication is not pending recovery")

        content_hash = str(publication.payload["content_hash"])
        size_bytes = int(publication.payload["size_bytes"])
        try:
            final_reference = self.byte_vault.recover_required(
                str(publication.payload["staging_reference"]),
                content_hash,
                size_bytes,
            )
            if not self.byte_vault.verify(final_reference, content_hash, size_bytes):
                raise ByteVaultRecoveryError("recovered final bytes failed verification")
        except Exception as exc:
            with self.records.transaction() as tx:
                tx.lock_resource(INVOICE_NAMESPACE, invoice_id)
                tx.lock_resource(PUBLICATION_NAMESPACE, publication_key)
                current_publication = tx.get_record(PUBLICATION_NAMESPACE, publication_key)
                current_invoice = tx.get_record(INVOICE_NAMESPACE, invoice_id)
                if current_publication is not None and current_publication.payload.get("state") == "metadata_committed":
                    failed = deepcopy(current_publication.payload)
                    failed["state"] = "failed"
                    tx.put_record(
                        PUBLICATION_NAMESPACE,
                        publication_key,
                        failed,
                        expected_version=current_publication.version,
                    )
                if current_invoice is not None:
                    next_invoice = deepcopy(current_invoice.payload)
                    state = deepcopy(next_invoice["source_states"][source_id])
                    state["status"] = "failed"
                    state["pending_publication_id"] = None
                    state["pending_content_hash"] = None
                    next_invoice["source_states"][source_id] = state
                    tx.put_record(
                        INVOICE_NAMESPACE,
                        invoice_id,
                        next_invoice,
                        expected_version=current_invoice.version,
                    )
                tx.append_audit(
                    uuid.uuid4().hex,
                    "invoice.source.attach.recovery",
                    invoice_id,
                    {
                        "principal_id": "host-recovery",
                        "capability": CAPABILITY,
                        "invoice_id": invoice_id,
                        "source_id": source_id,
                        "input_content_digest": content_hash,
                        "declared_effects": sorted(EFFECTS),
                        "result": "failed",
                    },
                )
            raise InvoiceSourceAttachExecutionError("publication recovery failed") from exc

        invoice = self._load_invoice(invoice_id)
        state = self._source_state(invoice.payload, source_id)
        expected = self._expected_source(invoice.payload, source_id)
        return self._settle_published(
            invoice_id=invoice_id,
            source_id=source_id,
            content_hash=content_hash,
            filename=str(state.get("filename") or "recovered"),
            media_type=str(state.get("media_type") or expected["media_type"]),
            size_bytes=size_bytes,
            decision=None,
            result="recovered",
        )


def seed_expected_missing_source(
    records: PostgresRecordKernel,
    *,
    invoice_id: str,
    source_id: str,
    media_type: str,
    expected_hash: str | None,
) -> None:
    """Probe fixture helper: seed one already-accepted invoice with one expected missing source."""
    payload = {
        "invoice_id": invoice_id,
        "accepted_archive_target": True,
        "expected_sources": {
            source_id: {
                "expected_hash": expected_hash,
                "media_type": media_type,
                "required": True,
            }
        },
        "source_states": {source_id: _empty_source_state()},
    }
    with records.transaction() as tx:
        tx.lock_resource(INVOICE_NAMESPACE, invoice_id)
        current = tx.get_record(INVOICE_NAMESPACE, invoice_id)
        if current is not None:
            raise InvoiceSourceAttachExecutionError("probe invoice already exists")
        tx.put_record(INVOICE_NAMESPACE, invoice_id, payload)
