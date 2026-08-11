from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import design_stage5_exposure
import design_stage6_contracts
from notes_workbench import service as notes_service
from router_workbench.model import RouterClosureError


@dataclass(frozen=True)
class ExposureBoundary:
    external: tuple[str, ...]
    internal_only: tuple[str, ...]

    @property
    def known(self) -> frozenset[str]:
        return frozenset((*self.external, *self.internal_only))


def exposure_boundary(project: Path) -> ExposureBoundary:
    """Project the validated State-5 exposure boundary into Router Closure."""
    report = design_stage5_exposure.lint(project)
    if report["summary"]["errors"]:
        codes = ", ".join(sorted({item["code"] for item in report["findings"]}))
        raise RouterClosureError(f"State-5 exposure is invalid: {codes}")
    return ExposureBoundary(
        external=tuple(report["external_operations"]),
        internal_only=tuple(report["internal_only_operations"]),
    )


def semantic_operation_slice(project: Path, operation: str) -> dict[str, Any]:
    """Return bounded accepted semantics plus the canonical State 6 contract."""
    if not operation.startswith("public_op:") or "." not in operation:
        raise RouterClosureError(f"invalid public operation key: {operation!r}")
    module = operation.removeprefix("public_op:").split(".", 1)[0]
    payload = notes_service.module_slice(project, module)
    public_operation = next(
        (item for item in payload["public_operations"] if item["key"] == operation),
        None,
    )
    if public_operation is None:
        raise RouterClosureError(f"operation is absent from its semantic module slice: {operation}")

    contracts = design_stage6_contracts.handoff(project)
    if not contracts["ready"]:
        raise RouterClosureError("State 6 exact contracts are not ready for Router Closure")
    canonical_contract = next(
        (value for value in contracts["contracts"].values() if value["public_operation"] == operation),
        None,
    )
    if canonical_contract is None:
        raise RouterClosureError(f"canonical State 6 contract is missing for external operation: {operation}")

    return {
        "schema_version": payload["schema_version"],
        "module": payload["module"],
        "responsibility": payload["responsibility"],
        "capabilities": payload["capabilities"],
        "flows": payload["flows"],
        "public_operation": public_operation,
        "canonical_contract": canonical_contract,
        "structured_refs": payload["structured_refs"],
    }
