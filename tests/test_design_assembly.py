from __future__ import annotations

import json
import shutil
from pathlib import Path

from assembly_workbench import inspect_check, verify
from assembly_workbench.checks import _factory_storage_resolver
from assembly_workbench.model import AssemblyWorkbenchError

ROOT = Path(__file__).resolve().parents[1]
CABINET = ROOT / "examples" / "cabinet-backend"


def _copy_project(tmp_path: Path) -> Path:
    project = tmp_path / "cabinet-backend"
    shutil.copytree(CABINET, project)
    return project


def test_cabinet_assembly_stops_on_every_undecided_fact() -> None:
    # The fence: the reference case is truthfully blocked wherever a fact is
    # undecided — undeclared depth (State 3), two undeclared time sources
    # (State 6), a codec registry the persistence closure cannot reach,
    # decisions without a witness, and flow steps nothing reaches. No check
    # reports a warning; every stop carries a hint.
    report = verify(CABINET)
    assert report["schema_version"] == "spec_workbench_assembly_verification.v1"
    assert report["ready"] is False
    assert [check["name"] for check in report["checks"]] == [
        "language", "modules", "identity", "data", "contracts", "external_contracts",
        "notes", "router", "persistence", "witness", "flows",
    ]
    by_name = {check["name"]: check for check in report["checks"]}
    assert all(check["warnings"] == 0 for check in report["checks"])
    for name in ("modules", "contracts", "persistence", "witness", "flows"):
        if name == "persistence" and _factory_storage_resolver() is not None:
            assert by_name[name]["ready"] is True, name  # the factory registry proved the codec coverage
            continue
        assert by_name[name]["ready"] is False and by_name[name]["errors"] > 0, name
    for name in ("language", "identity", "data", "external_contracts", "notes", "router"):
        assert by_name[name]["ready"] is True and by_name[name]["errors"] == 0, name
    assert by_name["contracts"]["errors"] == 2
    for check in inspect_check(CABINET, "contracts")["check"]["findings"]:
        assert check["severity"] == "error" and check["hint"].startswith("not decided — decide:")


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
    # one codec registry the closure cannot reach is an undecided fact: it stops
    if _factory_storage_resolver() is not None:
        assert report["check"]["ready"] is True  # the factory registry proved the codec coverage
    else:
        assert report["check"]["ready"] is False
    assert report["check"]["summary"]["repositories"] == 8
    assert report["check"]["warnings"] == 0
    expected_errors = [] if _factory_storage_resolver() is not None else ["codec_registry_unavailable"]
    assert [f["code"] for f in report["check"]["findings"] if f["severity"] == "error"] == expected_errors


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
    assert report["check"]["summary"]["notes"] == 255
    assert report["check"]["ready"] is True


def test_identity_failure_blocks_assembly(tmp_path: Path) -> None:
    project = _copy_project(tmp_path)
    path = project / "global_spec.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["models"]["HoldedPublication"]["identity"] = "value"
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
