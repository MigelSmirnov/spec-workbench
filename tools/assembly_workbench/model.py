from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

REPORT_SCHEMA = "spec_workbench_assembly_verification.v1"
INSPECTION_SCHEMA = "spec_workbench_assembly_check.v1"
CHECK_ORDER = (
    "language", "modules", "identity", "data", "contracts", "external_contracts",
    "notes", "router", "persistence", "factory",
)

class AssemblyWorkbenchError(ValueError):
    """Assembly verification cannot be completed safely."""

@dataclass(frozen=True)
class CheckResult:
    name: str
    ready: bool
    schema_version: str | None
    errors: int
    warnings: int
    summary: dict[str, Any]
    findings: list[dict[str, Any]]

    def to_dict(self, *, include_findings: bool = True) -> dict[str, Any]:
        payload = asdict(self)
        if not include_findings:
            payload.pop("findings")
        return payload
