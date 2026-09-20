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
    assert report["summary"]["assembled_runtime_models"] == 79
    assert report["summary"]["errors"] == 0


def test_inventory_is_stable_for_mcp_consumers() -> None:
    report = inventory(CABINET)
    assert report["schema_version"] == "spec_workbench_identity_inventory.v1"
    assert report["summary"] == {
        "models": 84,
        "state1_models": 84,
        "closure_models": 79,
        "contract_models": 0,
        "assembled_runtime_models": 79,
        "source_errors": 0,
    }
    assert [model["name"] for model in report["models"]] == sorted(
        model["name"] for model in report["models"]
    )


def test_model_inspection_exposes_source_locations() -> None:
    report = inspect_model(CABINET, "SourceLossDecision")
    assert report["consistent"] is True
    assert {
        key: value["identity"] for key, value in report["sources"].items() if value
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
    payload["models"]["HoldedPublication"]["identity"] = "value"
    path.write_text(json.dumps(payload), encoding="utf-8")

    report = design_identity_closure.lint(project)
    assert {
        finding["code"] for finding in report["findings"]
        if finding["model"] == "HoldedPublication"
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


def test_contract_only_model_closure_does_not_require_state1_identity(tmp_path: Path) -> None:
    project = _copy_identity_inputs(tmp_path)
    spec_path = project / "global_spec.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    spec["models"]["RequestDto"] = {"identity": "value", "fields": {"value": "str"}}
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    (project / "60_model_closure_contract_types.json").write_text(json.dumps({
        "schema_version": "spec_workbench_model_closure.v1",
        "status": "closed",
        "identity_scope": "contract_only",
        "models": {"RequestDto": {"identity": "value", "fields": {"value": "str"}}},
    }), encoding="utf-8")

    report = design_identity_closure.lint(project)

    assert report["summary"]["contract_models"] == 1
    assert not [f for f in report["findings"] if f["model"] == "RequestDto"]
    inspected = inspect_model(project, "RequestDto")
    assert inspected["consistent"] is True
    assert inspected["sources"]["state1"] is None
    assert inspected["sources"]["contract_closure"]["identity"] == "value"
