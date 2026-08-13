from __future__ import annotations

import json
import shutil
from pathlib import Path

import design_identity_closure


ROOT = Path(__file__).resolve().parents[1]
CABINET = ROOT / "examples" / "cabinet-backend"


def _copy_identity_inputs(tmp_path: Path) -> Path:
    project = tmp_path / "cabinet-backend"
    project.mkdir()
    for path in CABINET.glob("01_models*.md"):
        shutil.copy(path, project / path.name)
    for path in CABINET.glob("60_model_closure_*.json"):
        shutil.copy(path, project / path.name)
    shutil.copy(CABINET / "global_spec.json", project / "global_spec.json")
    return project


def test_cabinet_assembled_model_identity_is_closed() -> None:
    report = design_identity_closure.lint(CABINET)
    assert report["summary"]["assembled_runtime_models"] == 49
    assert report["summary"]["errors"] == 0


def test_assembled_identity_mismatch_is_rejected(tmp_path: Path) -> None:
    project = _copy_identity_inputs(tmp_path)
    path = project / "global_spec.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["models"]["VpsReleaseDecision"]["identity"] = "value"
    path.write_text(json.dumps(payload), encoding="utf-8")

    report = design_identity_closure.lint(project)
    assert {
        finding["code"] for finding in report["findings"]
        if finding["model"] == "VpsReleaseDecision"
    } == {"state1_identity_mismatch", "closure_identity_mismatch"}


def test_assembled_model_without_state1_record_is_rejected(tmp_path: Path) -> None:
    project = _copy_identity_inputs(tmp_path)
    for path in project.glob("01_models*.md"):
        text = path.read_text(encoding="utf-8")
        if "## Model M55 — PlanActualRequest" in text:
            text = text.split("## Model M55 — PlanActualRequest", 1)[0]
            path.write_text(text, encoding="utf-8")

    report = design_identity_closure.lint(project)
    assert any(
        finding["code"] == "missing_state1_model"
        and finding["model"] == "PlanActualRequest"
        for finding in report["findings"]
    )
