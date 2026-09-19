from __future__ import annotations

import json
from pathlib import Path

import project_gates


RESULT_SCHEMA = "spec_workbench_project_gate_result.v1"


def _write_gate(project: Path, body: str) -> None:
    tools = project / "tools"
    tools.mkdir(parents=True, exist_ok=True)
    (tools / "gate.py").write_text(body, encoding="utf-8")
    (project / "workbench_extensions.json").write_text(
        json.dumps(
            {
                "schema_version": "spec_workbench_project_extensions.v1",
                "project_gates": [{"id": "demo_gate", "module": "tools/gate.py"}],
            }
        ),
        encoding="utf-8",
    )


def test_project_without_declared_gates_passes(tmp_path: Path) -> None:
    report = project_gates.coverage(tmp_path)
    assert report["ready"] is True
    assert report["summary"] == {
        "gates": 0,
        "ready_gates": 0,
        "errors": 0,
        "warnings": 0,
        "handoff_ready": True,
    }


def test_declared_project_gate_passes(tmp_path: Path) -> None:
    _write_gate(
        tmp_path,
        f"""
def run_gate(project):
    return {{
        "schema_version": {RESULT_SCHEMA!r},
        "ready": True,
        "summary": {{"errors": 0, "warnings": 0}},
        "findings": [],
    }}
""",
    )
    report = project_gates.coverage(tmp_path)
    assert report["ready"] is True
    assert report["summary"]["gates"] == 1
    assert report["summary"]["ready_gates"] == 1
    assert report["findings"] == []


def test_declared_project_gate_failure_blocks(tmp_path: Path) -> None:
    _write_gate(
        tmp_path,
        f"""
def run_gate(project):
    return {{
        "schema_version": {RESULT_SCHEMA!r},
        "ready": False,
        "summary": {{"errors": 1, "warnings": 0}},
        "findings": [
            {{
                "severity": "error",
                "code": "demo_failure",
                "message": "demo gate failed",
            }}
        ],
    }}
""",
    )
    report = project_gates.coverage(tmp_path)
    assert report["ready"] is False
    assert report["summary"]["errors"] == 1
    assert report["findings"][0]["gate"] == "demo_gate"
    assert report["findings"][0]["code"] == "demo_failure"


def test_malformed_gate_report_fails_closed(tmp_path: Path) -> None:
    _write_gate(
        tmp_path,
        """
def run_gate(project):
    return {"ready": True, "summary": {}, "findings": []}
""",
    )
    report = project_gates.coverage(tmp_path)
    assert report["ready"] is False
    assert any(item["code"] == "invalid_gate_schema" for item in report["findings"])
