#!/usr/bin/env python3
"""Typed boundary models and safe status helpers for the first source-attach runtime case."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Optional


INVOICE_NAMESPACE = "cabinet.invoice_source_state"
PUBLICATION_NAMESPACE = "cabinet.source_publication"


def models():
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


def empty_source_state() -> dict[str, Any]:
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


def safe_status_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    expected_sources = payload.get("expected_sources")
    source_states = payload.get("source_states")
    if not isinstance(expected_sources, Mapping) or not isinstance(source_states, Mapping):
        raise RuntimeError("invalid invoice source state")

    available: list[str] = []
    missing: list[str] = []
    failed: list[str] = []
    for source_id, expected in expected_sources.items():
        if not isinstance(expected, Mapping) or expected.get("required") is not True:
            continue
        state = source_states.get(source_id)
        status = state.get("status") if isinstance(state, Mapping) else None
        if status == "available":
            available.append(str(source_id))
        elif status == "failed":
            failed.append(str(source_id))
        else:
            missing.append(str(source_id))

    complete = not missing and not failed
    return {
        "invoice_id": str(payload["invoice_id"]),
        "available_source_ids": tuple(sorted(available)),
        "missing_source_ids": tuple(sorted(missing)),
        "failed_source_ids": tuple(sorted(failed)),
        "completeness": "complete" if complete else "incomplete",
        "active_loss_decision_ids": (),
        "complete": complete,
        "observed_at": datetime.now(timezone.utc),
    }
