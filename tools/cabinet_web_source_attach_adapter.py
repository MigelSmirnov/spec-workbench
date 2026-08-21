#!/usr/bin/env python3
"""Disposable Cabinet_web -> local-box source-attach lowering.

This adapter accepts Cabinet_web-owned source identity plus raw bytes, derives
exact media/hash evidence from the bytes, and then calls the already verified
invoice.source.attach runtime without changing its implementation.
"""
from __future__ import annotations

from typing import Any, Mapping

from bounded_content_validation_kernel import BoundedContentValidationKernel
from bounded_media_identification import identify_exact_media_type
from invoice_source_attach_runtime import InvoiceSourceAttachExecutor


class _DetectedMediaExecutor(InvoiceSourceAttachExecutor):
    """Per-call executor that treats missing durable MIME as an unresolved expectation.

    The durable source expectation may legitimately have media_type=None. For one
    invocation, parser-backed evidence supplies the exact media type to the existing
    runtime checks. A non-null durable media type is never overridden.
    """

    def __init__(self, *args, detected_media_type: str, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._detected_media_type = detected_media_type

    def _expected_source(self, payload: Mapping[str, Any], source_id: str) -> Mapping[str, Any]:
        expected = dict(InvoiceSourceAttachExecutor._expected_source(payload, source_id))
        if expected.get("media_type") is None:
            expected["media_type"] = self._detected_media_type
        return expected


class CabinetWebSourceAttachAdapter:
    """Prepare and execute one Cabinet_web-compatible local source attachment."""

    def __init__(
        self,
        *,
        authority,
        typed_schema,
        records,
        byte_vault,
        content_validation: BoundedContentValidationKernel,
    ) -> None:
        self.authority = authority
        self.typed_schema = typed_schema
        self.records = records
        self.byte_vault = byte_vault
        self.content_validation = content_validation

    def execute(
        self,
        *,
        invoice_id: str,
        source_id: str,
        filename: str,
        content: bytes,
        credential_id: str,
        credential_material: str,
        interaction_id: str,
    ):
        """Attach bytes when Web supplied no authoritative MIME or binary hash.

        Media type and SHA-256 are derived from the caller-owned bytes before the
        capability call. The derived ContentReference therefore describes observed
        immutable bytes; it is not presented as an upstream Cabinet_web expectation.
        Archive effects and protected-data access still pass through the existing
        authority-enforced invoice.source.attach runtime.
        """
        evidence = identify_exact_media_type(content, validator=self.content_validation)

        payload = {
            "invoice_id": invoice_id,
            "files": (
                {
                    "filename": filename,
                    "media_type": evidence.media_type,
                    "content": content,
                    "expected_source_id": source_id,
                    "expected_content_hash": None,
                },
            ),
            "expected_sources": (
                {
                    "content_kind": "invoice_source",
                    "content_id": source_id,
                    "content_hash": evidence.content_hash,
                    "size_bytes": evidence.size_bytes,
                    "media_type": evidence.media_type,
                },
            ),
        }

        executor = _DetectedMediaExecutor(
            authority=self.authority,
            typed_schema=self.typed_schema,
            records=self.records,
            byte_vault=self.byte_vault,
            content_validation=self.content_validation,
            detected_media_type=evidence.media_type,
        )
        return executor.execute(
            payload,
            credential_id=credential_id,
            credential_material=credential_material,
            interaction_id=interaction_id,
        )
