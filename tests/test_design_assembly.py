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
        "language", "modules", "identity", "fields", "data", "contracts", "external_contracts",
        "notes", "closure_gaps", "router", "persistence", "witness", "flows", "factory",
    ]
    by_name = {check["name"]: check for check in report["checks"]}
    assert all(check["warnings"] == 0 for check in report["checks"])
    for name in ("modules", "contracts", "closure_gaps", "persistence", "witness", "flows"):
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


def test_closure_gap_check_blocks_unnamed_time_sources() -> None:
    report = inspect_check(CABINET, "closure_gaps")
    assert report["schema_version"] == "spec_workbench_assembly_check.v1"
    check = report["check"]
    assert check["schema_version"] == "design_closure_gaps.v1"
    assert check["ready"] is False
    assert check["errors"] > 0
    codes = {item["code"] for item in check["findings"]}
    assert "fresh_timestamp_without_source" in codes
    assert all(item["severity"] == "error" for item in check["findings"])


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


def test_factory_check_is_the_factory_validator(tmp_path: Path, monkeypatch) -> None:
    """SPEC_STANDARD 12-14 are held by the Factory validator; assembly asks it, not Stage 9 alone."""
    from assembly_workbench.checks import factory_validation

    case = tmp_path / "case"
    case.mkdir()
    spec = {"standard_version": 2, "contracts": {}}
    (case / "global_spec.json").write_text(json.dumps(spec), encoding="utf-8")

    without = factory_validation(case, factory_root=None)
    assert without["summary"]["errors"] == 1
    assert without["findings"][0]["code"] == "factory_unavailable"

    factory = tmp_path / "code_factory"
    (factory / "tools").mkdir(parents=True)
    (factory / "tools" / "validate_spec.py").write_text(
        """import argparse, hashlib, json
p = argparse.ArgumentParser()
p.add_argument('spec'); p.add_argument('--out', required=True); p.add_argument('--quiet', action='store_true')
a = p.parse_args()
s = json.load(open(a.spec, encoding='utf-8'))
sha = 'sha256:' + hashlib.sha256(json.dumps(s, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
bad = s.get('_reject')
open(a.out, 'w', encoding='utf-8').write(json.dumps({
    'status': 'FINDINGS_PRESENT' if bad else 'PASS',
    'summary': {'error': 1 if bad else 0, 'warning': 0},
    'spec_sha': sha,
    'findings': [{'id': 'SV-TEST', 'severity': 'error', 'message': 'unknown type Foo'}] if bad else [],
}))
raise SystemExit(1 if bad else 0)
""",
        encoding="utf-8",
    )
    clean = factory_validation(case, factory_root=factory)
    assert clean["summary"]["errors"] == 0 and clean["summary"]["status"] == "PASS"

    (case / "global_spec.json").write_text(json.dumps({**spec, "_reject": True}), encoding="utf-8")
    rejected = factory_validation(case, factory_root=factory)
    assert rejected["summary"]["errors"] == 1
    assert rejected["findings"][0]["code"] == "SV-TEST"
    assert "unknown type Foo" in rejected["findings"][0]["message"]
