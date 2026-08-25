from __future__ import annotations

import hashlib
import json
from pathlib import Path

from factory_admission_workbench import check
from factory_admission_workbench.service import (
    _review_check,
    _runtime_persistence_check,
    _target_identity_check,
)


ROOT = Path(__file__).resolve().parents[1]
STANDARD = (ROOT / "skills/spec-authoring/SPEC_STANDARD.md").read_text(encoding="utf-8")
CLEAN_GIT = {
    "commit": "a" * 40,
    "branch": "agent/test",
    "remote": "https://example.test/spec-workbench.git",
    "dirty": False,
}


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, payload: object) -> None:
    _write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _factory(
    tmp_path: Path, *, valid: bool = True, inspector_valid: bool = True
) -> Path:
    root = tmp_path / "code_factory"
    _write(root / "SPEC_STANDARD.md", STANDARD)
    _write(root / "tools/bootstrap_project.py", "# test fixture\n")
    _write_json(root / "project_index/structure.json", {})
    status = "PASS" if valid else "FINDINGS_PRESENT"
    errors = 0 if valid else 1
    returncode = 0 if valid else 1
    _write(
        root / "tools/validate_spec.py",
        f"""import argparse, hashlib, json
p = argparse.ArgumentParser()
p.add_argument('spec')
p.add_argument('--out', required=True)
p.add_argument('--quiet', action='store_true')
a = p.parse_args()
s = json.load(open(a.spec, encoding='utf-8'))
payload = json.dumps(s, sort_keys=True, ensure_ascii=False).encode()
report = {{
    'status': '{status}',
    'summary': {{'error': {errors}, 'warning': 0}},
    'spec_sha': 'sha256:' + hashlib.sha256(payload).hexdigest(),
    'findings': [] if {str(valid)} else [{{'id': 'SV-TEST', 'severity': 'error'}}],
}}
open(a.out, 'w', encoding='utf-8').write(json.dumps(report))
raise SystemExit({returncode})
""",
    )
    inspector_status = "PASS" if inspector_valid else "FINDINGS_PRESENT"
    inspector_blocks = 0 if inspector_valid else 1
    inspector_returncode = 0 if inspector_valid else 1
    _write(
        root / "tools/run_spec_inspector_preflight.py",
        f"""import argparse, hashlib, json
p = argparse.ArgumentParser()
p.add_argument('--project', required=True)
p.add_argument('--spec', required=True)
p.add_argument('--out', required=True)
a = p.parse_args()
raw = open(a.spec, 'rb').read()
report = {{
    'status': '{inspector_status}',
    'summary': {{'BLOCK': {inspector_blocks}, 'WARN': 0, 'INFO': 0}},
    'spec_sha': 'sha256:' + hashlib.sha256(raw).hexdigest(),
    'findings': [] if {str(inspector_valid)} else [{{
        'id': 'SI-TEST',
        'severity': 'BLOCK',
        'type': 'module_type_surface_incomplete',
    }}],
    'exit_policy': {{'exit_code': {inspector_returncode}}},
}}
open(a.out, 'w', encoding='utf-8').write(json.dumps(report))
raise SystemExit({inspector_returncode})
""",
    )
    return root


def _run(
    tmp_path: Path,
    *,
    valid: bool = True,
    inspector_valid: bool = True,
    update_existing: bool = False,
) -> dict:
    workbench = tmp_path / "spec-workbench"
    _write(workbench / "skills/spec-authoring/SPEC_STANDARD.md", STANDARD)
    source = workbench / "accepted/global_spec.json"
    _write_json(source, {"standard_version": 2, "contracts": {}})
    factory = _factory(tmp_path, valid=valid, inspector_valid=inspector_valid)
    return check(
        workbench_root=workbench,
        source=source,
        project="demo",
        factory_root=factory,
        update_existing=update_existing,
        source_git=CLEAN_GIT,
    )


def test_explicit_spec_is_ready_when_factory_accepts_it(tmp_path: Path) -> None:
    report = _run(tmp_path)
    assert report["schema_version"] == "spec_workbench_factory_admission.v1"
    assert report["stage"] == "9"
    assert report["status"] == "READY_TO_EXPORT"
    assert report["ready"] is True
    assert report["source"]["standard_version"] == 2
    assert report["admission_target"] == {
        "case": None,
        "case_path": None,
        "factory_project": "demo",
        "factory_project_path": str((tmp_path / "code_factory/projects/demo").resolve()),
    }
    assert report["summary"]["blocks"] == 0
    assert report["codec_coverage"]["status"] == "not_applicable"
    assert report["codec_coverage"]["complete"] is True
    language = next(item for item in report["checks"] if item["id"] == "FA009")
    assert language["status"] == "PASS"
    assert language["evidence"]["standard_version"] == 2
    external = next(item for item in report["checks"] if item["id"] == "FA011")
    assert external["status"] == "NOT_APPLICABLE"


def test_case_target_manifest_pins_factory_project(tmp_path: Path) -> None:
    case_root = tmp_path / "cabinet-backend"
    _write_json(
        case_root / "90_factory_target.json",
        {
            "schema_version": "spec_workbench_factory_target.v1",
            "case": "cabinet-backend",
            "factory_project": "cabinet_backend",
        },
    )

    result = _target_identity_check(case_root, "cabinet_backend")

    assert result.status == "PASS"
    assert result.evidence["declared_factory_project"] == "cabinet_backend"


def test_case_target_manifest_blocks_similar_wrong_project(tmp_path: Path) -> None:
    case_root = tmp_path / "cabinet-backend"
    _write_json(
        case_root / "90_factory_target.json",
        {
            "schema_version": "spec_workbench_factory_target.v1",
            "case": "cabinet-backend",
            "factory_project": "cabinet_backend",
        },
    )

    result = _target_identity_check(case_root, "Cabinet_web")

    assert result.status == "BLOCK"
    assert result.evidence["requested_factory_project"] == "Cabinet_web"
    assert result.evidence["declared_factory_project"] == "cabinet_backend"


def test_case_without_stage81_ledger_is_blocked(tmp_path: Path) -> None:
    result = _review_check(tmp_path / "case")

    assert result.status == "BLOCK"
    assert "implementation readiness is unproven" in result.summary


def test_master_persistence_without_backend_closure_is_blocked(tmp_path: Path) -> None:
    result = _runtime_persistence_check(
        {
            "persistence": {"InvoiceCardV1": {"class": "master"}},
            "rules": {},
        },
        tmp_path / "case",
    )

    assert result.status == "BLOCK"
    assert result.evidence == {
        "persistent_masters": ["InvoiceCardV1"],
        "missing": "rules.persistence_backend",
        "revision_entrypoint": "Stage 8.1 module review",
        "repair_policy": "return each open decision to its earliest owning design state",
    }


def test_master_persistence_with_backend_closure_passes(tmp_path: Path) -> None:
    case_root = tmp_path / "case"
    _write_json(case_root / "70_persistence_closure.json", {"status": "closed"})
    result = _runtime_persistence_check(
        {
            "persistence": {"InvoiceCardV1": {"class": "master"}},
            "rules": {
                "persistence_backend": {
                    "kind": "persistence_backend",
                    "schema_version": 2,
                    "tables": [{"table": "invoice_cards"}],
                    "repositories": [{"repository": "InvoiceRepository"}],
                }
            },
        },
        case_root,
    )

    assert result.status == "PASS"


def test_master_persistence_with_empty_backend_marker_is_blocked(tmp_path: Path) -> None:
    result = _runtime_persistence_check(
        {
            "persistence": {"InvoiceCardV1": {"class": "master"}},
            "rules": {
                "persistence_backend": {
                    "kind": "persistence_backend",
                    "schema_version": 3,
                    "tables": [],
                    "repositories": [],
                }
            },
        },
        tmp_path / "case",
    )

    assert result.status == "BLOCK"
    assert "no concrete table/repository lowering" in result.summary


def test_master_persistence_with_open_authoring_closure_is_blocked(tmp_path: Path) -> None:
    case_root = tmp_path / "case"
    _write_json(case_root / "70_persistence_closure.json", {"status": "open"})
    result = _runtime_persistence_check(
        {
            "persistence": {"CabinetEffect": {"class": "master"}},
            "rules": {
                "persistence_backend": {
                    "kind": "persistence_backend",
                    "schema_version": 3,
                    "tables": [{"table": "cabinet_effects"}],
                    "repositories": [{"repository": "PostgresCabinetUnitOfWork"}],
                }
            },
        },
        case_root,
    )

    assert result.status == "BLOCK"
    assert result.evidence["closure_status"] == "open"


def test_missing_standard_version_blocks_admission_before_handoff(tmp_path: Path) -> None:
    report = _run(tmp_path)
    source = tmp_path / "spec-workbench/accepted/global_spec.json"
    _write_json(source, {"contracts": {}})
    blocked = check(
        workbench_root=tmp_path / "spec-workbench",
        source=source,
        project="demo",
        factory_root=Path(report["factory_root"]),
        source_git=CLEAN_GIT,
    )
    language = next(item for item in blocked["checks"] if item["id"] == "FA009")
    assert blocked["ready"] is False
    assert language["status"] == "BLOCK"
    assert language["evidence"]["findings"][0]["code"] == "missing_standard_version"


def test_factory_validator_findings_block_admission(tmp_path: Path) -> None:
    report = _run(tmp_path, valid=False)
    validation = next(item for item in report["checks"] if item["id"] == "FA005")
    assert report["status"] == "BLOCKED"
    assert validation["status"] == "BLOCK"
    assert validation["evidence"]["findings"] == [
        {"id": "SV-TEST", "severity": "error"}
    ]


def test_factory_inspector_findings_block_admission(tmp_path: Path) -> None:
    report = _run(tmp_path, inspector_valid=False)
    inspector = next(item for item in report["checks"] if item["id"] == "FA015")
    assert report["status"] == "BLOCKED"
    assert inspector["status"] == "BLOCK"
    assert inspector["evidence"]["summary"]["BLOCK"] == 1
    assert inspector["evidence"]["findings"] == [
        {
            "id": "SI-TEST",
            "severity": "BLOCK",
            "type": "module_type_surface_incomplete",
        }
    ]


def _implementation_spec(*, concrete_methods: bool, obligations: bool = True) -> dict:
    contracts = {
        "WorkerPort.run": "(self, item: str) -> bool",
        "Service.__init__": "(self, worker: WorkerPort) -> None",
        "LocalWorker.__init__": "(self) -> None",
    }
    if concrete_methods:
        contracts["LocalWorker.run"] = "(self, item: str) -> bool"
    spec = {
        "standard_version": 2,
        "contracts": contracts,
        "models": {
            "role": "data",
            "schema_version": 1,
            "WorkerPort": {"kind": "interface"},
        },
        "module_functions": {"workers": ["WorkerPort", "Service", "LocalWorker"]},
    }
    if obligations:
        spec["implementation_obligations"] = {
            "WorkerPort": {
                "disposition": "local",
                "implementations": ["LocalWorker"],
            }
        }
    return spec


def test_missing_interface_implementation_disposition_blocks_admission(tmp_path: Path) -> None:
    report = _run(tmp_path)
    source = tmp_path / "spec-workbench/accepted/global_spec.json"
    _write_json(source, _implementation_spec(concrete_methods=True, obligations=False))
    blocked = check(
        workbench_root=tmp_path / "spec-workbench",
        source=source,
        project="demo",
        factory_root=Path(report["factory_root"]),
        source_git=CLEAN_GIT,
    )
    implementation = next(item for item in blocked["checks"] if item["id"] == "FA010")
    assert blocked["ready"] is False
    assert implementation["status"] == "BLOCK"
    assert implementation["evidence"]["findings"][0]["code"] == "missing_implementation_disposition"


def test_local_implementation_without_port_methods_blocks_admission(tmp_path: Path) -> None:
    report = _run(tmp_path)
    source = tmp_path / "spec-workbench/accepted/global_spec.json"
    _write_json(source, _implementation_spec(concrete_methods=False))
    blocked = check(
        workbench_root=tmp_path / "spec-workbench",
        source=source,
        project="demo",
        factory_root=Path(report["factory_root"]),
        source_git=CLEAN_GIT,
    )
    implementation = next(item for item in blocked["checks"] if item["id"] == "FA010")
    assert implementation["status"] == "BLOCK"
    assert implementation["evidence"]["findings"] == [{
        "code": "missing_concrete_method_contract",
        "interface": "WorkerPort",
        "concrete": "LocalWorker",
        "method": "run",
        "expected_contract": "(self, item: str) -> bool",
    }]


def test_complete_local_implementation_obligation_passes_admission(tmp_path: Path) -> None:
    report = _run(tmp_path)
    source = tmp_path / "spec-workbench/accepted/global_spec.json"
    _write_json(source, _implementation_spec(concrete_methods=True))
    admitted = check(
        workbench_root=tmp_path / "spec-workbench",
        source=source,
        project="demo",
        factory_root=Path(report["factory_root"]),
        source_git=CLEAN_GIT,
    )
    implementation = next(item for item in admitted["checks"] if item["id"] == "FA010")
    assert implementation["status"] == "PASS"
    assert implementation["evidence"]["findings"] == []


def test_existing_different_target_requires_explicit_update(tmp_path: Path) -> None:
    report = _run(tmp_path)
    factory = Path(report["factory_root"])
    _write_json(
        factory / "projects/demo/specs/base/global_spec.json",
        {"standard_version": 2, "contracts": {"old": "() -> None"}},
    )
    workbench = tmp_path / "spec-workbench"
    blocked = check(
        workbench_root=workbench,
        source=workbench / "accepted/global_spec.json",
        project="demo",
        factory_root=factory,
        source_git=CLEAN_GIT,
    )
    target = next(item for item in blocked["checks"] if item["id"] == "FA007")
    assert target["status"] == "BLOCK"
    assert target["evidence"]["action"] == "blocked_update"

    admitted = check(
        workbench_root=workbench,
        source=workbench / "accepted/global_spec.json",
        project="demo",
        factory_root=factory,
        update_existing=True,
        source_git=CLEAN_GIT,
    )
    assert admitted["ready"] is True
    target = next(item for item in admitted["checks"] if item["id"] == "FA007")
    assert target["evidence"]["action"] == "update"
    assert target["evidence"]["source_standard_version"] == 2
    assert target["evidence"]["canonical_standard_version"] == 2


def test_formatting_only_target_difference_requires_lineage_acceptance(tmp_path: Path) -> None:
    report = _run(tmp_path)
    factory = Path(report["factory_root"])
    source = tmp_path / "spec-workbench/accepted/global_spec.json"
    canonical = factory / "projects/demo/specs/base/global_spec.json"
    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_text(
        json.dumps(json.loads(source.read_text(encoding="utf-8")), separators=(",", ":")),
        encoding="utf-8",
    )
    admitted = check(
        workbench_root=tmp_path / "spec-workbench",
        source=source,
        project="demo",
        factory_root=factory,
        source_git=CLEAN_GIT,
    )
    target = next(item for item in admitted["checks"] if item["id"] == "FA007")
    assert admitted["ready"] is True
    assert target["evidence"]["action"] == "accept_lineage"
    assert target["evidence"]["source_sha256"] != target["evidence"]["canonical_sha256"]
    assert target["evidence"]["source_spec_sha"] == target["evidence"]["canonical_spec_sha"]
    assert target["evidence"]["source_standard_version"] == 2


def test_old_lineage_without_standard_version_is_not_fresh(tmp_path: Path) -> None:
    report = _run(tmp_path)
    factory = Path(report["factory_root"])
    source = tmp_path / "spec-workbench/accepted/global_spec.json"
    canonical = factory / "projects/demo/specs/base/global_spec.json"
    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    lineage_path = factory / "projects/demo/specs/working/spec_editor_manifest.json"
    _write_json(lineage_path, {
        "accepted": True,
        "status": "pass",
        "verdict": "PASS",
        "inputs": {},
        "outputs": {"base_spec_sha256_after": hashlib.sha256(canonical.read_bytes()).hexdigest()},
        "change_summary": {"changed_modules": ["global"]},
    })
    admitted = check(
        workbench_root=tmp_path / "spec-workbench",
        source=source,
        project="demo",
        factory_root=factory,
        source_git=CLEAN_GIT,
    )
    target = next(item for item in admitted["checks"] if item["id"] == "FA007")
    assert target["evidence"]["action"] == "accept_lineage"
    assert target["evidence"]["lineage_fresh"] is False
    assert target["evidence"]["lineage_standard_version"] is None


def test_old_lineage_without_codec_snapshot_is_not_fresh(tmp_path: Path) -> None:
    report = _run(tmp_path)
    factory = Path(report["factory_root"])
    source = tmp_path / "spec-workbench/accepted/global_spec.json"
    canonical = factory / "projects/demo/specs/base/global_spec.json"
    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    lineage_path = factory / "projects/demo/specs/working/spec_editor_manifest.json"
    _write_json(lineage_path, {
        "accepted": True,
        "status": "pass",
        "verdict": "PASS",
        "inputs": {"standard_version": 2},
        "outputs": {"base_spec_sha256_after": hashlib.sha256(canonical.read_bytes()).hexdigest()},
        "change_summary": {"changed_modules": ["global"]},
    })
    admitted = check(
        workbench_root=tmp_path / "spec-workbench",
        source=source,
        project="demo",
        factory_root=factory,
        source_git=CLEAN_GIT,
    )
    target = next(item for item in admitted["checks"] if item["id"] == "FA007")
    assert target["evidence"]["action"] == "accept_lineage"
    assert target["evidence"]["lineage_fresh"] is False
    assert target["evidence"]["source_codec_coverage"] == admitted["codec_coverage"]
    assert target["evidence"]["lineage_codec_coverage"] is None


def test_dirty_source_is_blocked_unless_explicitly_allowed(tmp_path: Path) -> None:
    report = _run(tmp_path)
    workbench = tmp_path / "spec-workbench"
    dirty = {**CLEAN_GIT, "dirty": True}
    blocked = check(
        workbench_root=workbench,
        source=workbench / "accepted/global_spec.json",
        project="demo",
        factory_root=Path(report["factory_root"]),
        source_git=dirty,
    )
    assert blocked["ready"] is False

    allowed = check(
        workbench_root=workbench,
        source=workbench / "accepted/global_spec.json",
        project="demo",
        factory_root=Path(report["factory_root"]),
        allow_dirty_source=True,
        source_git=dirty,
    )
    source_check = next(item for item in allowed["checks"] if item["id"] == "FA001")
    assert allowed["ready"] is True
    assert source_check["status"] == "WARNING"
