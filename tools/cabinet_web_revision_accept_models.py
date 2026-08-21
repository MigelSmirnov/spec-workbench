#!/usr/bin/env python3
"""Typed boundary models for Cabinet_web -> local box revision acceptance."""
from __future__ import annotations

from typing import Any, Optional


REVISION_NAMESPACE = "cabinet.invoice_revision"
DELIVERY_NAMESPACE = "cabinet.web_sync_delivery"


def models():
    from pydantic import BaseModel, ConfigDict, StrictInt, StrictStr  # type: ignore

    class ClosedModel(BaseModel):
        model_config = ConfigDict(extra="forbid")

    class CabinetWebInvoiceRevisionDeliveryModel(ClosedModel):
        contract_version: StrictStr
        delivery_id: StrictStr
        emitted_at: StrictStr
        producer_repository: StrictStr
        invoice_id: StrictStr
        card_contract_version: StrictInt
        card_status: StrictStr
        card_content_hash: StrictStr
        source_git_commit_sha: StrictStr
        card_repository_path: StrictStr
        base_backend_content_hash: Optional[StrictStr] = None
        card_document: dict[str, Any]

    class CabinetBackendInvoiceRevisionReceiptModel(ClosedModel):
        contract_version: StrictStr
        delivery_id: StrictStr
        invoice_id: StrictStr
        card_content_hash: StrictStr
        source_git_commit_sha: StrictStr
        outcome: StrictStr
        accepted_at: Optional[StrictStr] = None
        backend_current_content_hash: Optional[StrictStr] = None
        error_code: Optional[StrictStr] = None

    return CabinetWebInvoiceRevisionDeliveryModel, CabinetBackendInvoiceRevisionReceiptModel
