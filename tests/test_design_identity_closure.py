from __future__ import annotations

import json
import shutil
from pathlib import Path

import design_identity_closure
from identity_workbench import inspect_model, inventory
from identity_workbench.model import IdentityWorkbenchError


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
    assert report["summary"]["assembled_runtime_models"] == 70
    assert report["summary"]["errors"] == 0


def test_inventory_is_stable_for_mcp_consumers() -> None:
    report = inventory(CABINET)
    assert report["schema_version"] == "spec_workbench_identity_inventory.v1"
    assert report["summary"] == {
        "models": 76,
        "state1_models": 76,
        "closure_models": 70,
        "assembled_runtime_models": 70,
        "source_errors": 0,
    }
    assert [model["name"] for model in report["models"]] == sorted(
        model["name"] for model in report["models"]
    )


def test_model_inspection_exposes_source_locations() -> None:
    report = inspect_model(CABINET, "VpsReleaseDecision")
    assert report["consistent"] is True
    assert {
        key: value["identity"] for key, value in report["sources"].items()
    } == {"state1": "entity", "closure": "entity", "assembled": "entity"}
    assert report["sources"]["state1"]["location"].startswith(
        "01_models_contract_support.md:"
    )


def test_unknown_model_inspection_fails_closed() -> None:
    try:
        inspect_model(CABINET, "InventedModel")
    except IdentityWorkbenchError as error:
        assert str(error) == "Unknown model: InventedModel"
    else:
        raise AssertionError("Unknown model must not produce an empty inspection.")


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
