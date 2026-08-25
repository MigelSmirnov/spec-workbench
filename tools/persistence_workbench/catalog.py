from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from persistence_workbench.model import (
    CATALOG_FILE,
    CATALOG_SCHEMA,
    CATALOG_STATUSES,
    PersistenceBackendError,
)


CATALOG_FIELDS = frozenset({"schema_version", "status", "backend_ir"})


def load_optional(project: Path) -> dict[str, Any] | None:
    """Load the optional post-contract persistence closure without inference."""
    path = project / CATALOG_FILE
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PersistenceBackendError(f"invalid {CATALOG_FILE}: {exc}") from exc
    if not isinstance(payload, dict):
        raise PersistenceBackendError(f"{CATALOG_FILE} must contain an object")
    if set(payload) != CATALOG_FIELDS:
        extra = sorted(set(payload) - CATALOG_FIELDS)
        missing = sorted(CATALOG_FIELDS - set(payload))
        raise PersistenceBackendError(
            f"invalid {CATALOG_FILE} fields: extra={extra}, missing={missing}"
        )
    if payload.get("schema_version") != CATALOG_SCHEMA:
        raise PersistenceBackendError(
            f"unsupported persistence closure schema; expected {CATALOG_SCHEMA!r}"
        )
    if payload.get("status") not in CATALOG_STATUSES:
        raise PersistenceBackendError(
            f"persistence closure status must be one of {sorted(CATALOG_STATUSES)}"
        )
    if not isinstance(payload.get("backend_ir"), dict):
        raise PersistenceBackendError("persistence closure backend_ir must be an object")
    return payload
