"""The authored half of the closure: decisions the design states cannot imply."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from value_flow_workbench.model import CLOSURE_FILE, CLOSURE_SCHEMA, CLOSURE_STATUSES, ValueFlowError

FIELDS = frozenset({"schema_version", "status", "outputs", "inputs"})


def load_optional(project: Path) -> dict[str, Any] | None:
    path = project / CLOSURE_FILE
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueFlowError(f"invalid {CLOSURE_FILE}: {exc}") from exc
    if not isinstance(payload, dict) or set(payload) != FIELDS:
        raise ValueFlowError(f"{CLOSURE_FILE} must carry exactly {sorted(FIELDS)}")
    if payload["schema_version"] != CLOSURE_SCHEMA:
        raise ValueFlowError(f"unsupported value-flow closure schema; expected {CLOSURE_SCHEMA!r}")
    if payload["status"] not in CLOSURE_STATUSES:
        raise ValueFlowError(f"value-flow closure status must be one of {sorted(CLOSURE_STATUSES)}")
    for section in ("outputs", "inputs"):
        rows = payload[section]
        if not isinstance(rows, dict) or not all(isinstance(row, dict) for row in rows.values()):
            raise ValueFlowError(f"{CLOSURE_FILE}.{section} must map a function to its declarations")
    return payload
