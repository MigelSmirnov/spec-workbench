from __future__ import annotations

import json
import shutil
from pathlib import Path

from assembly_workbench import inspect_check, verify
from assembly_workbench.model import AssemblyWorkbenchError

ROOT = Path(__file__).resolve().parents[1]
CABINET = ROOT / "examples" / "cabinet-backend"


def _copy_project(tmp_path: Path) -> Path:
    project = tmp_path / "cabinet-backend"
    shutil.copytree(CABINET, project)
    return project


def test_cabinet_assembly_is_ready_after_v2_language_migration() -> None:
    report = verify(CABINET)
    assert report["schema_version"] == "spec_workbench_assembly_verification.v1"
    assert report["ready"] is True
    assert report["summary"] == {
        "checks": 8,
        "ready_checks": 8,
        "errors": 0,
        # codec_registry_unavailable: the Workbench does not embed the emitter's
        # domain/storage registry, so codec completeness stays an advisory warning.
        "warnings": 1,
    }
    assert [check["name"] for check in report["checks"]] == [
        "language", "identity", "data", "contracts", "external_contracts",
        "notes", "router", "persistence"
    ]
    language = report["checks"][0]
    assert language["ready"] is True
    assert language["errors"] == 0
    persistence = report["checks"][-1]
    assert persistence["ready"] is True
    assert persistence["summary"]["handoff_ready"] is True


def test_language_check_inspection_preserves_ready_owner_report() -> None:
    report = inspect_check(CABINET, "language")
    assert report["schema_version"] == "spec_workbench_assembly_check.v1"
    assert report["check"]["schema_version"] == "spec_workbench_language_gate.v1"
    assert report["check"]["ready"] is True
    assert report["check"]["errors"] == 0


def test_persistence_check_covers_seven_deterministic_repositories() -> None:
    report = inspect_check(CABINET, "persistence")
    assert report["schema_version"] == "spec_workbench_assembly_check.v1"
    assert report["check"]["schema_version"] == "spec_workbench_persistence_backend_coverage.v1"
    assert report["check"]["ready"] is True
    assert report["check"]["summary"]["repositories"] == 8
    assert report["check"]["summary"]["errors"] == 0


def test_external_contract_check_preserves_content_addressed_evidence() -> None:
    report = inspect_check(CABINET, "external_contracts")
    assert report["schema_version"] == "spec_workbench_assembly_check.v1"
    assert report["check"]["schema_version"] == "spec_workbench_external_contract_coverage.v1"
    assert report["check"]["ready"] is True
    assert report["check"]["summary"]["active"] == 1
    assert report["check"]["summary"]["bindings"] == 12


def test_check_inspection_preserves_owner_report() -> None:
    report = inspect_check(CABINET, "notes")
    assert report["schema_version"] == "spec_workbench_assembly_check.v1"
    assert report["check"]["schema_version"] == "spec_workbench_state7_notes_gate.v1"
    assert report["check"]["summary"]["notes"] == 244
    assert report["check"]["ready"] is True


def test_identity_failure_blocks_assembly(tmp_path: Path) -> None:
    project = _copy_project(tmp_path)
    path = project / "global_spec.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["models"]["VpsReleaseDecision"]["identity"] = "value"
    path.write_text(json.dumps(payload), encoding="utf-8")
    report = verify(project)
    assert report["ready"] is False
    identity = next(check for check in report["checks"] if check["name"] == "identity")
    assert identity["ready"] is False
    assert identity["errors"] == 2


def test_unknown_check_fails_closed() -> None:
    try:
        inspect_check(CABINET, "invented")
    except AssemblyWorkbenchError as error:
        assert str(error) == "Unknown assembly check: invented"
    else:
        raise AssertionError("Unknown check must fail closed.")
