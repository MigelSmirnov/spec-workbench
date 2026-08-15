from __future__ import annotations

import json
from pathlib import Path

import design_stage5_exposure


PROJECT = Path(__file__).resolve().parents[1] / "examples" / "cabinet-backend"


def test_cabinet_exposure_plan_is_complete_and_valid():
    report = design_stage5_exposure.lint(PROJECT)
    assert report["summary"]["operations"] == 26
    assert report["summary"]["classified"] == 26
    assert report["summary"]["errors"] == 0
    assert "public_op:holded_gateway.create_holded_purchase" in report["internal_only_operations"]
    assert "public_op:durable_archive.attach_local_source" in report["external_operations"]


def test_forced_internal_operation_cannot_be_external(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    # Reuse the real State 5 artifacts via copies so design_stage5 coverage remains authoritative.
    for name in ("30_modules.md", "40_flows.md", "40_flow_plan.json", "50_api_plan.json", "50_public_apis.md"):
        (project / name).write_text((PROJECT / name).read_text(encoding="utf-8"), encoding="utf-8")
    exposure = json.loads((PROJECT / "50_exposure_plan.json").read_text(encoding="utf-8"))
    exposure["operations"]["public_op:holded_gateway.create_holded_purchase"] = "external"
    (project / "50_exposure_plan.json").write_text(json.dumps(exposure), encoding="utf-8")
    # Stage 3 trace is not needed for exposure semantics but design_stage5 coverage consumes it indirectly.
    (project / "30_trace.json").write_text((PROJECT / "30_trace.json").read_text(encoding="utf-8"), encoding="utf-8")
    report = design_stage5_exposure.lint(project)
    assert any(f["code"] == "forbidden_external_boundary" for f in report["findings"])
