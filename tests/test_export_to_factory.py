from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

import export_to_factory


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, data: object) -> None:
    _write(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def _fake_factory(tmp_path: Path, standard: str) -> Path:
    factory = tmp_path / "code_factory"
    _write(factory / "SPEC_STANDARD.md", standard)
    _write_json(
        factory / "project_index/structure.json",
        {
            "root": str(factory),
            "projects_dir": "projects",
            "dirs": {
                "base": "specs/base",
                "normalized": "specs/normalized",
                "working": "specs/working",
                "local_specs": "specs/local_specs",
                "draft": "specs/draft",
                "build": "build",
            },
            "files": {"global_spec": "specs/base/global_spec.json"},
        },
    )
    _write(
        factory / "tools/validate_spec.py",
        """import argparse, hashlib, json
p = argparse.ArgumentParser()
p.add_argument('spec')
p.add_argument('--out', required=True)
p.add_argument('--quiet', action='store_true')
a = p.parse_args()
s = json.load(open(a.spec, encoding='utf-8'))
payload = json.dumps(s, sort_keys=True, ensure_ascii=False).encode()
r = {'status': 'PASS', 'summary': {'error': 0}, 'spec_sha': 'sha256:' + hashlib.sha256(payload).hexdigest()}
open(a.out, 'w', encoding='utf-8').write(json.dumps(r))
""",
    )
    _write(
        factory / "tools/run_spec_inspector_preflight.py",
        """import argparse, hashlib, json
p = argparse.ArgumentParser()
p.add_argument('--project', required=True)
p.add_argument('--spec', required=True)
p.add_argument('--out', required=True)
a = p.parse_args()
raw = open(a.spec, 'rb').read()
r = {
    'status': 'PASS',
    'summary': {'BLOCK': 0, 'WARN': 0, 'INFO': 0},
    'spec_sha': 'sha256:' + hashlib.sha256(raw).hexdigest(),
    'findings': [],
    'exit_policy': {'exit_code': 0},
}
open(a.out, 'w', encoding='utf-8').write(json.dumps(r))
""",
    )
    _write(
        factory / "tools/bootstrap_project.py",
        """import argparse, json, pathlib, shutil
p = argparse.ArgumentParser()
p.add_argument('--project', required=True)
p.add_argument('--spec', required=True)
p.add_argument('--allow-existing', action='store_true')
p.add_argument('--force-spec', action='store_true')
a = p.parse_args()
root = pathlib.Path.cwd()
s = json.load(open(root / 'project_index/structure.json', encoding='utf-8'))
project = root / s['projects_dir'] / a.project
for rel in s['dirs'].values():
    (project / rel).mkdir(parents=True, exist_ok=True)
shutil.copyfile(a.spec, project / s['files']['global_spec'])
""",
    )
    return factory


def _clean_git_metadata(root: Path) -> dict[str, object]:
    return {
        "commit": "a" * 40,
        "branch": "agent/test",
        "remote": "https://example.test/repo.git",
        "dirty": False,
    }


def test_export_creates_canonical_spec_and_bound_handoff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_workbench_root = Path(export_to_factory.__file__).resolve().parents[1]
    standard = (real_workbench_root / "skills/spec-authoring/SPEC_STANDARD.md").read_text(encoding="utf-8")
    workbench_root = tmp_path / "spec-workbench"
    _write(workbench_root / "skills/spec-authoring/SPEC_STANDARD.md", standard)
    factory = _fake_factory(tmp_path, standard)
    source = workbench_root / "examples/demo/global_spec.json"
    spec = {
        "standard_version": 2,
        "contracts": {"main": "() -> None"},
        "module_functions": {"app": ["main"]},
        "imports": {"stdlib": [], "third_party": [], "internal": {}},
        "module_order": ["app"],
    }
    _write_json(source, spec)
    monkeypatch.setattr(export_to_factory, "__file__", str(workbench_root / "tools/export_to_factory.py"))
    monkeypatch.setattr(export_to_factory, "git_metadata", _clean_git_metadata)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "export_to_factory.py",
            "--spec",
            str(source),
            "--project",
            "demo",
            "--factory-root",
            str(factory),
        ],
    )

    assert export_to_factory.main() == 0
    canonical = factory / "projects/demo/specs/base/global_spec.json"
    manifest_path = factory / "projects/demo/specs/working/spec_workbench_handoff.json"
    admission_path = factory / "projects/demo/specs/working/spec_workbench_factory_admission.json"
    lineage_path = factory / "projects/demo/specs/working/spec_editor_manifest.json"
    assert json.loads(canonical.read_text(encoding="utf-8")) == spec
    admission = json.loads(admission_path.read_text(encoding="utf-8"))
    codec_coverage = admission["codec_coverage"]
    assert codec_coverage["status"] == "not_applicable"
    assert codec_coverage["complete"] is True
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "spec_workbench_handoff.v1"
    assert manifest["source"]["spec_sha256"] == export_to_factory.sha256_file(canonical)
    assert manifest["source"]["standard_version"] == 2
    assert manifest["factory"]["standard_version"] == 2
    assert manifest["factory"]["validation_status"] == "PASS"
    assert manifest["codec_coverage"] == codec_coverage
    lineage = json.loads(lineage_path.read_text(encoding="utf-8"))
    assert lineage["accepted"] is True
    assert lineage["status"] == "pass"
    assert lineage["verdict"] == "PASS"
    assert lineage["producer"]["route"] == "spec_workbench_stage9"
    assert lineage["inputs"]["standard_version"] == 2
    assert lineage["inputs"]["codec_coverage"] == codec_coverage
    assert lineage["change_summary"]["changed_modules"] == ["global"]
    assert lineage["outputs"]["base_spec_sha256_after"] == export_to_factory.sha256_file(canonical)


def test_export_blocks_standard_drift_before_project_creation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_workbench_root = Path(export_to_factory.__file__).resolve().parents[1]
    standard = (real_workbench_root / "skills/spec-authoring/SPEC_STANDARD.md").read_text(encoding="utf-8")
    workbench_root = tmp_path / "spec-workbench"
    _write(workbench_root / "skills/spec-authoring/SPEC_STANDARD.md", standard)
    factory = _fake_factory(tmp_path, "# incompatible standard\n")
    source = workbench_root / "examples/demo/global_spec.json"
    _write_json(source, {"standard_version": 2})
    monkeypatch.setattr(export_to_factory, "__file__", str(workbench_root / "tools/export_to_factory.py"))
    monkeypatch.setattr(export_to_factory, "git_metadata", _clean_git_metadata)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "export_to_factory.py",
            "--spec",
            str(source),
            "--project",
            "demo",
            "--factory-root",
            str(factory),
        ],
    )

    with pytest.raises(SystemExit, match="SPEC_STANDARD mismatch"):
        export_to_factory.main()
    assert not (factory / "projects/demo").exists()


def test_export_blocks_note_drift_before_factory_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_workbench_root = Path(export_to_factory.__file__).resolve().parents[1]
    standard = (real_workbench_root / "skills/spec-authoring/SPEC_STANDARD.md").read_text(encoding="utf-8")
    workbench_root = tmp_path / "spec-workbench"
    _write(workbench_root / "skills/spec-authoring/SPEC_STANDARD.md", standard)
    factory = _fake_factory(tmp_path, standard)
    case_root = workbench_root / "examples/cabinet-web-backend"
    source = case_root / "global_spec.json"
    _write(case_root / "80_notes.md", "find_invoice_duplicates: [BEHAVIOR] MUST apply = rules.invoice_duplicate_matching.\n")
    _write_json(source, {"standard_version": 2, "notes": ["find_invoice_duplicates: [BEHAVIOR] legacy"]})
    monkeypatch.setattr(export_to_factory, "__file__", str(workbench_root / "tools/export_to_factory.py"))
    monkeypatch.setattr(
        export_to_factory.notes_propagation,
        "propagate",
        lambda *args, **kwargs: {
            "ready": False,
            "findings": [{"severity": "block", "message": "canonical note is missing"}],
        },
    )
    monkeypatch.setattr(sys, "argv", [
        "export_to_factory.py", "--case", "cabinet-web-backend", "--project", "demo",
        "--factory-root", str(factory),
    ])

    with pytest.raises(SystemExit, match="note propagation blocked export"):
        export_to_factory.main()
