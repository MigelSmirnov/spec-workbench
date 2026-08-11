from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from router_workbench.model import CATALOG_FILE, CATALOG_SCHEMA, RouterClosureError


def load(project: Path) -> dict[str, Any]:
    """Load the Router Closure design state without interpreting route semantics."""
    path = project / CATALOG_FILE
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RouterClosureError(f"missing {CATALOG_FILE}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise RouterClosureError(f"invalid {CATALOG_FILE}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RouterClosureError(f"{CATALOG_FILE} must contain an object")
    if payload.get("schema_version") != CATALOG_SCHEMA:
        raise RouterClosureError(f"unsupported Router Closure schema; expected {CATALOG_SCHEMA!r}")
    return payload
