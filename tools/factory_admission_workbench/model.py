from __future__ import annotations

from dataclasses import dataclass
from typing import Any


REPORT_SCHEMA = "spec_workbench_factory_admission.v1"
CHECK_PASS = "PASS"
CHECK_BLOCK = "BLOCK"
CHECK_WARNING = "WARNING"
CHECK_NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True)
class AdmissionCheck:
    check_id: str
    status: str
    summary: str
    evidence: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.check_id,
            "status": self.status,
            "summary": self.summary,
            "evidence": self.evidence,
        }
