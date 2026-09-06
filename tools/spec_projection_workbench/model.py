from __future__ import annotations

PLAN_SCHEMA = "spec_workbench_projection_plan.v1"
VERIFY_SCHEMA = "spec_workbench_projection_verify.v1"


class SpecProjectionError(ValueError):
    """A canonical specification projection could not be planned or applied."""
