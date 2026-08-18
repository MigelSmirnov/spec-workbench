from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


COVERAGE_SCHEMA = "spec_workbench_persistence_backend_coverage.v1"
AUTHORING_SCHEMA = "spec_workbench_persistence_closure_coverage.v1"
CATALOG_SCHEMA = "spec_workbench_persistence_closure.v1"
CATALOG_FILE = "70_persistence_closure.json"
CATALOG_STATUSES = frozenset({"open", "closed"})
SUPPORTED_SCHEMA_VERSION = 2
SUPPORTED_ENGINE = "sqlite"
SUPPORTED_EMITTER = "sqlite_sync_v2"


class PersistenceBackendError(ValueError):
    """The persistence backend IR or its authoring closure cannot be inspected safely."""


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    repository: str | None = None
    location: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value is not None}
