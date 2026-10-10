from __future__ import annotations

import json
from pathlib import Path

from persistence_workbench import authoring, coverage


def _case(tmp_path: Path, persistence: dict) -> Path:
    (tmp_path / "60_data_closure.json").write_text(json.dumps({
        "schema_version": "spec_workbench_state6_data_closure.v1", "status": "closed",
        "sections": {"config": {}, "rules": {}, "persistence": persistence,
                     "properties": {}, "determinism": {}},
        "placements": [], "unresolved": [],
    }), encoding="utf-8")
    (tmp_path / "global_spec.json").write_text(json.dumps({
        "rules": {}, "persistence": persistence,
    }), encoding="utf-8")
    return tmp_path


def test_master_persistence_without_closure_stops_authoring_and_assembly(tmp_path):
    case = _case(tmp_path, {"Run": {"class": "master"}, "Flow": {"class": "issued"}})
    authored = authoring.coverage(case)
    assert authored["ready"] is False
    assert [f["code"] for f in authored["findings"]] == ["persistence_closure_required"]
    assert "Run" in authored["findings"][0]["message"] and "Flow" not in authored["findings"][0]["message"]
    assembled = coverage(case)
    assert assembled["summary"]["handoff_ready"] is False
    assert [f["code"] for f in assembled["findings"]] == ["persistence_closure_required"]


def test_no_master_persistence_keeps_the_closure_optional(tmp_path):
    case = _case(tmp_path, {"Flow": {"class": "issued"}})
    assert authoring.coverage(case)["ready"] is True
    assert coverage(case)["summary"]["handoff_ready"] is True
