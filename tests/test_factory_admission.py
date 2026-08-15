from __future__ import annotations

import json
from pathlib import Path

from factory_admission_workbench import check


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


def _factory(tmp_path: Path, *, valid: bool = True) -> Path:
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
    return root


def _run(tmp_path: Path, *, valid: bool = True, update_existing: bool = False) -> dict:
    workbench = tmp_path / "spec-workbench"
    _write(workbench / "skills/spec-authoring/SPEC_STANDARD.md", STANDARD)
    source = workbench / "accepted/global_spec.json"
    _write_json(source, {"contracts": {}})
    factory = _factory(tmp_path, valid=valid)
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
    assert report["summary"]["blocks"] == 0


def test_factory_validator_findings_block_admission(tmp_path: Path) -> None:
    report = _run(tmp_path, valid=False)
    validation = next(item for item in report["checks"] if item["id"] == "FA005")
    assert report["status"] == "BLOCKED"
    assert validation["status"] == "BLOCK"
    assert validation["evidence"]["findings"] == [
        {"id": "SV-TEST", "severity": "error"}
    ]


def test_existing_different_target_requires_explicit_update(tmp_path: Path) -> None:
    report = _run(tmp_path)
    factory = Path(report["factory_root"])
    _write_json(
        factory / "projects/demo/specs/base/global_spec.json",
        {"contracts": {"old": "() -> None"}},
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
