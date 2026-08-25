from __future__ import annotations

import json
import shutil
from pathlib import Path

from spec_language_workbench import REPORT_SCHEMA, verify

ROOT = Path(__file__).resolve().parents[1]
CABINET = ROOT / "examples" / "cabinet-backend"


def _copy_project(tmp_path: Path) -> Path:
    project = tmp_path / "cabinet-backend"
    shutil.copytree(CABINET, project)
    return project


def _load(project: Path) -> dict:
    return json.loads((project / "global_spec.json").read_text(encoding="utf-8"))


def _write(project: Path, payload: dict) -> None:
    (project / "global_spec.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def test_current_cabinet_is_valid_v2_language() -> None:
    report = verify(CABINET)
    assert report["schema_version"] == REPORT_SCHEMA
    assert report["ready"] is True
    assert report["standard_version"] == 2
    assert report["summary"]["errors"] == 0
    assert report["findings"] == []


def test_standard_version_two_is_accepted(tmp_path: Path) -> None:
    project = _copy_project(tmp_path)
    payload = _load(project)
    payload["standard_version"] = 2
    payload.pop("adapters", None)
    _write(project, payload)

    report = verify(project)
    assert report["ready"] is True
    assert report["standard_version"] == 2
    assert report["summary"]["errors"] == 0


def test_unknown_standard_version_fails_closed(tmp_path: Path) -> None:
    project = _copy_project(tmp_path)
    payload = _load(project)
    payload["standard_version"] = 3
    payload.pop("adapters", None)
    _write(project, payload)

    report = verify(project)
    assert report["ready"] is False
    assert [item["code"] for item in report["findings"]] == [
        "unsupported_standard_version"
    ]


def test_missing_standard_version_fails_closed(tmp_path: Path) -> None:
    project = _copy_project(tmp_path)
    payload = _load(project)
    payload.pop("standard_version", None)
    payload.pop("adapters", None)
    _write(project, payload)

    report = verify(project)
    assert report["ready"] is False
    assert [item["code"] for item in report["findings"]] == [
        "missing_standard_version"
    ]


def test_legacy_adapters_are_forbidden_in_v2(tmp_path: Path) -> None:
    project = _copy_project(tmp_path)
    payload = _load(project)
    payload["standard_version"] = 2
    payload["adapters"] = {}
    _write(project, payload)

    report = verify(project)
    assert report["ready"] is False
    assert [item["code"] for item in report["findings"]] == [
        "legacy_adapters_section"
    ]
