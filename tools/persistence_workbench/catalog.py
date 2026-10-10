from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from persistence_workbench.model import (
    CATALOG_FILE,
    CATALOG_SCHEMA,
    CATALOG_STATUSES,
    Finding,
    PersistenceBackendError,
)


CATALOG_FIELDS = frozenset({"schema_version", "status", "backend_ir"})


DATA_CLOSURE_FILE = "60_data_closure.json"


def master_models(persistence: Any) -> list[str]:
    """Models a persistence section declares ``master``: mutable truth (SPEC_STANDARD 15.5)."""
    if not isinstance(persistence, dict):
        return []
    return sorted(
        name for name, declaration in persistence.items()
        if isinstance(name, str) and isinstance(declaration, dict) and declaration.get("class") == "master"
    )


def declared_master_models(project: Path) -> list[str]:
    """``master`` models of the pre-contract data closure, before anything is assembled."""
    try:
        payload = json.loads((project / DATA_CLOSURE_FILE).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    sections = payload.get("sections") if isinstance(payload, dict) else None
    return master_models(sections.get("persistence") if isinstance(sections, dict) else None)


def required_closure_finding(masters: list[str]) -> Finding:
    """Mutable records may not reach generation as prose: their tables are a deterministic closure.

    The same rule as Factory admission FA013, raised where the closure is authored.
    """
    return Finding(
        "error",
        "persistence_closure_required",
        "master persistence " + ", ".join(masters) + " needs a closed 70_persistence_closure.json: "
        "without it the tables and repositories of mutable records are left to generation "
        "(Factory admission FA013)",
        location=CATALOG_FILE,
    )


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
