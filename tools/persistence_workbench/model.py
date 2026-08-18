from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


COVERAGE_SCHEMA = "spec_workbench_persistence_backend_coverage.v1"
SUPPORTED_SCHEMA_VERSION = 2
SUPPORTED_ENGINE = "sqlite"
SUPPORTED_EMITTER = "sqlite_sync_v2"


class PersistenceBackendError(ValueError):
    """The assembled persistence backend IR cannot be inspected safely."""


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    repository: str | None = None
    location: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value is not None}
