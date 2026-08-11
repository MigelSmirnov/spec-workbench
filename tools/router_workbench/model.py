from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


CATALOG_SCHEMA = "spec_workbench_router_closure.v1"
COVERAGE_SCHEMA = "spec_workbench_router_closure_coverage.v1"
LINT_SCHEMA = "spec_workbench_router_closure_lint.v1"
NEXT_SCHEMA = "spec_workbench_router_closure_next.v1"
CATALOG_FILE = "70_router_closure.json"
EMISSIONS = frozenset({"table", "irregular", "unresolved"})


class RouterClosureError(ValueError):
    """The Workbench catalog or its upstream design evidence is unreadable."""


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    operation: str | None = None
    location: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value is not None}
