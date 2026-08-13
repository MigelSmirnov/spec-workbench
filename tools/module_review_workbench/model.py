from __future__ import annotations

SLICE_SCHEMA = "spec_workbench_module_review_slice.v1"
REVIEW_SCHEMA = "spec_workbench_module_review.v1"
MODULES_SCHEMA = "spec_workbench_module_review_modules.v1"

class ModuleReviewError(ValueError):
    """A complete module review packet cannot be built safely."""
