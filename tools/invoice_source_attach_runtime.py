#!/usr/bin/env python3
"""First executable invoice.source.attach runtime over verified generic providers."""
from __future__ import annotations

import hashlib
import json
import uuid
from copy import deepcopy
from typing import Any, Mapping

from authority_kernel import LOCAL_AGENT_BOUNDARY, AuthorityError, AuthorityKernel, AuthorizationDecision
from bounded_content_validation_kernel import BoundedContentValidationKernel, ContentValidationRejected
from invoice_source_attach_models import (
    INVOICE_NAMESPACE,
    PUBLICATION_NAMESPACE,
    empty_source_state,
    models,
    safe_status_payload,
)
from local_private_byte_vault import ByteVaultRecoveryError, LocalPrivateByteVault
from postgres_record_kernel import PostgresRecordKernel, StoredRecord
from typed_schema_kernel import TypedSchemaKernel


CAPABILITY = "invoice.source.attach"
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


class _ExistingPublication(Exception):
    pass


def publication_resource_id(invoice_id: str, source_id: str) -> str:
    return json.dumps([invoice_id, source_id], ensure_ascii=False, separators=(",", ":"))


class InvoiceSourceAttachExecutor:
    """Execute the declared one-file expected-missing-source runtime case."""

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
    def resource_scope(invoice_id: str) -> str:
        return f"invoice:{invoice_id}"

    def _load_invoice(self, invoice_id: str) -> StoredRecord:
        record = self.records.read_record(INVOICE_NAMESPACE, invoice_id)
        if record is None or record.payload.get("accepted_archive_target") is not True:
            raise InvoiceSourceAttachRejected("accepted_archive_target_not_found")
        if record.payload.get("invoice_id") != invoice_id:
            raise InvoiceSourceAttachExecutionError("invoice_state_identity_mismatch")
        return record

    @staticmethod
    def _expected_source(payload: Mapping[str, Any], source_id: str) -> Mapping[str, Any]:
        sources = payload.get("expected_sources")
        if not isinstance(sources, Mapping) or source_id not in sources:
            raise InvoiceSourceAttachRejected("expected_source_not_found")
        value = sources[source_id]
        if not isinstance(value, Mapping):
            raise InvoiceSourceAttachExecutionError("invalid_expected_source_state")
        return value

    @staticmethod
    def _source_state(payload: Mapping[str, Any], source_id: str) -> Mapping[str, Any]:
        states = payload.get("source_states")
        if not isinstance(states, Mapping) or source_id not in states:
            raise InvoiceSourceAttachRejected("source_state_not_found")
        value = states[source_id]
        if not isinstance(value, Mapping):
            raise InvoiceSourceAttachExecutionError("invalid_source_state")
        return value

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
        _, OutputModel = models()
        return self.typed_schema.validate_output(
            OutputModel,
            {
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
                "source_status": safe_status_payload(invoice_payload),
            },
        )

    def _append_audit(
        self,
        tx,
        *,
        decision: AuthorizationDecision,
        invoice_id: str,
        source_id: str,
        content_hash: str,
        result: str,
        reason_code: str | None = None,
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

    def execute(
        self,
        payload: Mapping[str, Any],
        *,
        credential_id: str,
        credential_material: str,
        interaction_id: str,
    ):
        InputModel, _ = models()
        validated = self.typed_schema.validate_input(InputModel, payload)
        if len(validated.files) != 1:
            raise InvoiceSourceAttachRejected("execution_case_requires_exactly_one_file")

        invoice_id = str(validated.invoice_id)
        file = validated.files[0]
        source_id = file.expected_source_id
        if not source_id:
            raise InvoiceSourceAttachRejected("expected_source_id_required")
        raw_digest = hashlib.sha256(bytes(file.content)).hexdigest()

        def protected_operation(decision: AuthorizationDecision):
            try:
                return self._execute_authorized(validated, file, source_id, decision)
            except InvoiceSourceAttachRejected as exc:
                with self.records.transaction() as tx:
                    self._append_audit(
                        tx,
                        decision=decision,
                        invoice_id=invoice_id,
                        source_id=source_id,
                        content_hash=raw_digest,
                        result="rejected",
                        reason_code=exc.code,
                    )
                raise

        try:
            return self.authority.invoke(
                credential_id=credential_id,
                credential_material=credential_material,
                required_boundary=LOCAL_AGENT_BOUNDARY,
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

    def _execute_authorized(self, validated, file, source_id: str, decision: AuthorizationDecision):
        invoice_id = str(validated.invoice_id)
        invoice = self._load_invoice(invoice_id)
        expected = self._expected_source(invoice.payload, source_id)
        current_state = self._source_state(invoice.payload, source_id)

        caller_refs = [item for item in validated.expected_sources if item.content_id == source_id]
        if len(caller_refs) != 1:
            raise InvoiceSourceAttachRejected("expected_source_input_binding_required")
        caller_expected = caller_refs[0]

        expected_media_type = expected.get("media_type")
        if expected_media_type != file.media_type:
            raise InvoiceSourceAttachRejected("expected_source_media_type_mismatch")
        if caller_expected.media_type is not None and caller_expected.media_type != expected_media_type:
            raise InvoiceSourceAttachRejected("caller_expected_media_type_mismatch")

        try:
            validation = self.content_validation.validate(bytes(file.content), str(file.media_type))
        except ContentValidationRejected as exc:
            raise InvoiceSourceAttachRejected("content_validation_rejected") from exc

        content_hash = validation.content_hash
        durable_hash = expected.get("expected_hash")
        if file.expected_content_hash is not None and file.expected_content_hash != content_hash:
            raise InvoiceSourceAttachRejected("caller_expected_content_hash_mismatch")
        if caller_expected.content_hash != content_hash:
            raise InvoiceSourceAttachRejected("caller_expected_content_hash_mismatch")
        if durable_hash is not None and durable_hash != content_hash:
            raise InvoiceSourceAttachRejected("durable_expected_content_hash_mismatch")

        if current_state.get("status") == "available":
            return self._existing_available_result(
                invoice=invoice,
                file=file,
                source_id=source_id,
                content_hash=content_hash,
                decision=decision,
            )

        staged = self.byte_vault.stage(bytes(file.content), content_hash, len(file.content))
        publication_key = publication_resource_id(invoice_id, source_id)
        committed = False
        try:
            with self.records.transaction() as tx:
                tx.lock_resource(INVOICE_NAMESPACE, invoice_id)
                tx.lock_resource(PUBLICATION_NAMESPACE, publication_key)
                locked_invoice = tx.get_record(INVOICE_NAMESPACE, invoice_id)
                if locked_invoice is None or locked_invoice.payload.get("accepted_archive_target") is not True:
                    raise InvoiceSourceAttachRejected("accepted_archive_target_not_found")
                locked_expected = self._expected_source(locked_invoice.payload, source_id)
                locked_state = self._source_state(locked_invoice.payload, source_id)
                if (
                    locked_expected.get("expected_hash") != durable_hash
                    or locked_expected.get("media_type") != expected_media_type
                ):
                    raise InvoiceSourceAttachRejected("expected_source_changed_during_attachment")

                publication = tx.get_record(PUBLICATION_NAMESPACE, publication_key)
                if locked_state.get("status") == "available":
                    if locked_state.get("content_hash") == content_hash:
                        raise _ExistingPublication("available")
                    raise InvoiceSourceAttachRejected("source_content_conflict")
                if publication is not None:
                    if publication.payload.get("content_hash") != content_hash:
                        raise InvoiceSourceAttachRejected("source_content_conflict")
                    if publication.payload.get("state") in {"metadata_committed", "published"}:
                        raise _ExistingPublication(str(publication.payload.get("state")))
                    raise InvoiceSourceAttachRejected("previous_publication_failed")

                publication_id = uuid.uuid4().hex
                tx.put_record(
                    PUBLICATION_NAMESPACE,
                    publication_key,
                    {
                        "publication_id": publication_id,
                        "invoice_id": invoice_id,
                        "source_id": source_id,
                        "content_hash": content_hash,
                        "size_bytes": len(file.content),
                        "staging_reference": staged.staging_reference,
                        "final_reference": staged.final_reference,
                        "state": "metadata_committed",
                    },
                )
                next_invoice = deepcopy(locked_invoice.payload)
                next_state = deepcopy(next_invoice["source_states"][source_id])
                next_state.update(
                    {
                        "status": "missing",
                        "size_bytes": len(file.content),
                        "media_type": str(file.media_type),
                        "filename": str(file.filename),
                        "attached_by_principal_id": decision.principal_id,
                        "interaction_id": decision.actor.interaction_id,
                        "pending_publication_id": publication_id,
                        "pending_content_hash": content_hash,
                    }
                )
                next_invoice["source_states"][source_id] = next_state
                tx.put_record(
                    INVOICE_NAMESPACE,
                    invoice_id,
                    next_invoice,
                    expected_version=locked_invoice.version,
                )
                self._append_audit(
                    tx,
                    decision=decision,
                    invoice_id=invoice_id,
                    source_id=source_id,
                    content_hash=content_hash,
                    result="metadata_committed",
                )
            committed = True
        except _ExistingPublication:
            self.byte_vault.remove_staging(staged.staging_reference)
            return self._recover_or_replay_authorized(
                invoice_id=invoice_id,
                source_id=source_id,
                content_hash=content_hash,
                fallback_filename=str(file.filename),
                decision=decision,
            )
        except Exception:
            if not committed:
                self.byte_vault.remove_staging(staged.staging_reference)
            raise

        try:
            final_reference = self.byte_vault.publish(
                staged.staging_reference, content_hash, len(file.content)
            )
            if not self.byte_vault.verify(final_reference, content_hash, len(file.content)):
                raise InvoiceSourceAttachExecutionError("final_byte_verification_failed")
        except Exception as exc:
            raise InvoiceSourceAttachExecutionError("publication_pending_recovery") from exc

        return self._settle(
            invoice_id=invoice_id,
            source_id=source_id,
            content_hash=content_hash,
            size_bytes=len(file.content),
            filename=str(file.filename),
            media_type=str(file.media_type),
            decision=decision,
            result="attached",
        )

    def _existing_available_result(self, *, invoice: StoredRecord, file, source_id: str, content_hash: str, decision: AuthorizationDecision):
        publication = self.records.read_record(
            PUBLICATION_NAMESPACE,
            publication_resource_id(str(invoice.payload["invoice_id"]), source_id),
        )
        state = self._source_state(invoice.payload, source_id)
        if (
            state.get("content_hash") != content_hash
            or publication is None
            or publication.payload.get("state") != "published"
            or not self.byte_vault.verify(
                str(publication.payload["final_reference"]),
                content_hash,
                int(publication.payload["size_bytes"]),
            )
        ):
            raise InvoiceSourceAttachRejected("source_content_conflict")
        with self.records.transaction() as tx:
            self._append_audit(
                tx,
                decision=decision,
                invoice_id=str(invoice.payload["invoice_id"]),
                source_id=source_id,
                content_hash=content_hash,
                result="already_attached",
            )
        return self._safe_result(
            invoice_payload=invoice.payload,
            filename=str(file.filename),
            source_id=source_id,
            content_hash=content_hash,
            result="already_attached",
        )

    def _recover_or_replay_authorized(
        self,
        *,
        invoice_id: str,
        source_id: str,
        content_hash: str,
        fallback_filename: str,
        decision: AuthorizationDecision,
    ):
        invoice = self._load_invoice(invoice_id)
        state = self._source_state(invoice.payload, source_id)
        if state.get("status") == "available":
            return self._existing_available_result(
                invoice=invoice,
                file=type("File", (), {"filename": fallback_filename})(),
                source_id=source_id,
                content_hash=content_hash,
                decision=decision,
            )

        publication = self.records.read_record(
            PUBLICATION_NAMESPACE, publication_resource_id(invoice_id, source_id)
        )
        if publication is None or publication.payload.get("content_hash") != content_hash:
            raise InvoiceSourceAttachExecutionError("pending_publication_missing_or_conflicting")
        final_reference = self.byte_vault.recover_required(
            str(publication.payload["staging_reference"]),
            content_hash,
            int(publication.payload["size_bytes"]),
        )
        if not self.byte_vault.verify(
            final_reference, content_hash, int(publication.payload["size_bytes"])
        ):
            raise InvoiceSourceAttachExecutionError("recovered_final_bytes_failed_verification")
        return self._settle(
            invoice_id=invoice_id,
            source_id=source_id,
            content_hash=content_hash,
            size_bytes=int(publication.payload["size_bytes"]),
            filename=str(state.get("filename") or fallback_filename),
            media_type=str(state.get("media_type") or self._expected_source(invoice.payload, source_id)["media_type"]),
            decision=decision,
            result="recovered",
        )

    def _settle(
        self,
        *,
        invoice_id: str,
        source_id: str,
        content_hash: str,
        size_bytes: int,
        filename: str,
        media_type: str,
        decision: AuthorizationDecision | None,
        result: str,
    ):
        key = publication_resource_id(invoice_id, source_id)
        with self.records.transaction() as tx:
            tx.lock_resource(INVOICE_NAMESPACE, invoice_id)
            tx.lock_resource(PUBLICATION_NAMESPACE, key)
            invoice = tx.get_record(INVOICE_NAMESPACE, invoice_id)
            publication = tx.get_record(PUBLICATION_NAMESPACE, key)
            if invoice is None or publication is None:
                raise InvoiceSourceAttachExecutionError("pending_publication_state_missing")
            if publication.payload.get("content_hash") != content_hash:
                raise InvoiceSourceAttachExecutionError("pending_publication_content_changed")
            if publication.payload.get("state") not in {"metadata_committed", "published"}:
                raise InvoiceSourceAttachExecutionError("pending_publication_not_recoverable")
            if not self.byte_vault.verify(
                str(publication.payload["final_reference"]), content_hash, size_bytes
            ):
                raise InvoiceSourceAttachExecutionError("final_bytes_not_verified_during_settlement")

            if publication.payload.get("state") != "published":
                next_publication = deepcopy(publication.payload)
                next_publication["state"] = "published"
                tx.put_record(PUBLICATION_NAMESPACE, key, next_publication, expected_version=publication.version)

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
            tx.put_record(INVOICE_NAMESPACE, invoice_id, next_invoice, expected_version=invoice.version)
            if decision is None:
                tx.append_audit(
                    uuid.uuid4().hex,
                    "invoice.source.attach.recovery",
                    invoice_id,
                    {
                        "principal_id": state.get("attached_by_principal_id") or "host-recovery",
                        "capability": CAPABILITY,
                        "invoice_id": invoice_id,
                        "source_id": source_id,
                        "interaction_id": state.get("interaction_id") or "host-recovery",
                        "input_content_digest": content_hash,
                        "declared_effects": sorted(EFFECTS),
                        "result": result,
                    },
                )
            else:
                self._append_audit(
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

    def recover_pending_publication(self, *, invoice_id: str, source_id: str):
        """Host startup recovery; this is not a caller-visible authorization surface."""
        key = publication_resource_id(invoice_id, source_id)
        publication = self.records.read_record(PUBLICATION_NAMESPACE, key)
        if publication is None or publication.payload.get("state") not in {"metadata_committed", "published"}:
            raise InvoiceSourceAttachExecutionError("publication_not_pending_or_published")

        content_hash = str(publication.payload["content_hash"])
        size_bytes = int(publication.payload["size_bytes"])
        invoice = self._load_invoice(invoice_id)
        state = self._source_state(invoice.payload, source_id)
        if publication.payload.get("state") == "published" and state.get("status") == "available":
            if not self.byte_vault.verify(
                str(publication.payload["final_reference"]), content_hash, size_bytes
            ):
                raise InvoiceSourceAttachExecutionError("published_bytes_not_verified")
            return self._safe_result(
                invoice_payload=invoice.payload,
                filename=str(state.get("filename") or "recovered"),
                source_id=source_id,
                content_hash=content_hash,
                result="already_attached",
            )

        try:
            final_reference = self.byte_vault.recover_required(
                str(publication.payload["staging_reference"]), content_hash, size_bytes
            )
            if not self.byte_vault.verify(final_reference, content_hash, size_bytes):
                raise ByteVaultRecoveryError("recovered final bytes failed verification")
        except Exception as exc:
            self._mark_recovery_failed(invoice_id=invoice_id, source_id=source_id, content_hash=content_hash)
            raise InvoiceSourceAttachExecutionError("publication_recovery_failed") from exc

        return self._settle(
            invoice_id=invoice_id,
            source_id=source_id,
            content_hash=content_hash,
            size_bytes=size_bytes,
            filename=str(state.get("filename") or "recovered"),
            media_type=str(state.get("media_type") or self._expected_source(invoice.payload, source_id)["media_type"]),
            decision=None,
            result="recovered",
        )

    def _mark_recovery_failed(self, *, invoice_id: str, source_id: str, content_hash: str) -> None:
        key = publication_resource_id(invoice_id, source_id)
        with self.records.transaction() as tx:
            tx.lock_resource(INVOICE_NAMESPACE, invoice_id)
            tx.lock_resource(PUBLICATION_NAMESPACE, key)
            publication = tx.get_record(PUBLICATION_NAMESPACE, key)
            invoice = tx.get_record(INVOICE_NAMESPACE, invoice_id)
            if publication is not None and publication.payload.get("state") == "metadata_committed":
                failed = deepcopy(publication.payload)
                failed["state"] = "failed"
                tx.put_record(PUBLICATION_NAMESPACE, key, failed, expected_version=publication.version)
            if invoice is not None:
                next_invoice = deepcopy(invoice.payload)
                state = deepcopy(next_invoice["source_states"][source_id])
                state["status"] = "failed"
                state["pending_publication_id"] = None
                state["pending_content_hash"] = None
                next_invoice["source_states"][source_id] = state
                tx.put_record(INVOICE_NAMESPACE, invoice_id, next_invoice, expected_version=invoice.version)
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


def seed_expected_missing_source(
    records: PostgresRecordKernel,
    *,
    invoice_id: str,
    source_id: str,
    media_type: str,
    expected_hash: str | None,
) -> None:
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
        "source_states": {source_id: empty_source_state()},
    }
    with records.transaction() as tx:
        tx.lock_resource(INVOICE_NAMESPACE, invoice_id)
        if tx.get_record(INVOICE_NAMESPACE, invoice_id) is not None:
            raise InvoiceSourceAttachExecutionError("probe_invoice_already_exists")
        tx.put_record(INVOICE_NAMESPACE, invoice_id, payload)
