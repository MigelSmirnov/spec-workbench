from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

INVENTORY_SCHEMA = "spec_workbench_identity_inventory.v1"
INSPECTION_SCHEMA = "spec_workbench_identity_inspection.v1"
VERIFICATION_SCHEMA = "spec_workbench_identity_verification.v1"
Identity = Literal["value", "entity"]

class IdentityWorkbenchError(ValueError):
    """Identity evidence cannot be loaded or addressed safely."""

@dataclass(frozen=True)
class SourceIdentity:
    identity: Identity
    location: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

@dataclass(frozen=True)
class Finding:
    code: str
    message: str
    model: str | None = None
    location: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value is not None}
