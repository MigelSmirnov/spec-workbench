from __future__ import annotations

from pathlib import Path

import design_stage5


ROOT = Path(__file__).resolve().parents[1]
CABINET = ROOT / "examples/cabinet-backend"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "demo"
    _write(project / "30_modules.md", """# State 3 — Module responsibilities

## `archive`

### Owns
- durable acceptance.
### Knows
- acceptance semantics.
### Hides
- persistence sequencing.
### Must not own
- transport.
### Candidate public capabilities
```text
accept_transfer
```
### Depth assessment
Deep module.
""")
    _write(project / "40_flows.md", """# State 4 — Key system flows

## `flow:accept_record`

### Trigger
A transfer arrives.
### Boundary
`module:archive` through `capability:archive.accept_transfer`.
### Steps
1. Accept.
### Outcomes
Accepted or rejected.
### Errors
Archive errors.
""")
    _write(project / "50_api_plan.json", """{
  "schema_version": "spec_workbench_state5_plan.v1",
  "operations": [
    {
      "key": "public_op:archive.accept_transfer",
      "capability": "capability:archive.accept_transfer",
      "flows": ["flow:accept_record"],
      "callers": ["boundary:transport"],
      "purpose": "Accept one record."
    }
  ]
}
""")
    _write(project / "50_public_apis.md", """# State 5 — Public module operations

## `public_op:archive.accept_transfer`

### Owner
`module:archive`
### Callers
`boundary:transport`
### Inputs
Exact transfer.
### Outputs
Acceptance result.
### Observable effect
May accept one record.
### Enforces
Durable acceptance.
### Errors
Invalid transfer.
### State impact
May mutate archive state.
""")
    return project


def test_state5_handoff_has_stable_public_operation_key(tmp_path: Path) -> None:
    payload = design_stage5.handoff(_project(tmp_path))
    assert payload["schema_version"] == "spec_workbench_state5_handoff.v2"
    assert payload["lint_summary"]["errors"] == 0
    assert payload["operations"][0]["key"] == "public_op:archive.accept_transfer"
    assert payload["coverage"]["operations"][0]["callers"] == ["boundary:transport"]


def test_coverage_requires_state4_flow_evidence(tmp_path: Path) -> None:
    project = _project(tmp_path)
    path = project / "40_flows.md"
    path.write_text(path.read_text(encoding="utf-8").replace("capability:archive.accept_transfer", "capability:archive.missing"), encoding="utf-8")
    report = design_stage5.coverage(project)
    assert report["operations"][0]["flow_evidence_missing"] == ["flow:accept_record"]


def test_lint_requires_public_operation_sections(tmp_path: Path) -> None:
    project = _project(tmp_path)
    path = project / "50_public_apis.md"
    path.write_text(path.read_text(encoding="utf-8").replace("### Errors\nInvalid transfer.\n", ""), encoding="utf-8")
    report = design_stage5.lint(project)
    assert any(f["code"] == "missing_public_op_section" and "Errors" in f["message"] for f in report["findings"])


def test_lint_requires_owner_in_owner_section(tmp_path: Path) -> None:
    project = _project(tmp_path)
    path = project / "50_public_apis.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace("### Owner\n`module:archive`\n", "### Owner\nArchive module.\n")
    text = text.replace("### Enforces\nDurable acceptance.\n", "### Enforces\nDurable acceptance by `module:archive`.\n")
    path.write_text(text, encoding="utf-8")
    report = design_stage5.lint(project)
    assert any(f["code"] == "missing_public_op_owner" for f in report["findings"])


def test_lint_requires_documented_callers_to_match_plan(tmp_path: Path) -> None:
    project = _project(tmp_path)
    path = project / "50_public_apis.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace("`boundary:transport`", "`boundary:http`"),
        encoding="utf-8",
    )
    report = design_stage5.lint(project)
    mismatch = [f for f in report["findings"] if f["code"] == "public_op_callers_mismatch"]
    assert len(mismatch) == 1
    assert "boundary:transport" in mismatch[0]["message"]
    assert "boundary:http" in mismatch[0]["message"]


def test_lint_rejects_placeholder_markers_in_public_operation(tmp_path: Path) -> None:
    project = _project(tmp_path)
    path = project / "50_public_apis.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace("Durable acceptance.", "TODO: durable acceptance."),
        encoding="utf-8",
    )
    report = design_stage5.lint(project)
    assert any(f["code"] == "public_op_placeholder" for f in report["findings"])


def test_legacy_adapter_caller_is_rejected(tmp_path: Path) -> None:
    project = _project(tmp_path)
    path = project / "50_api_plan.json"
    path.write_text(
        path.read_text(encoding="utf-8").replace("boundary:transport", "adapter:transport"),
        encoding="utf-8",
    )
    coverage = design_stage5.coverage(project)
    assert coverage["summary"]["invalid_refs"] == 1
    assert coverage["summary"]["remaining"] == 1
    assert coverage["operations"][0]["invalid_callers"] == ["adapter:transport"]
    lint = design_stage5.lint(project)
    assert any(
        item["code"] == "invalid_plan_ref"
        and "module:<known_module> or boundary:<name>" in item["message"]
        for item in lint["findings"]
    )
    next_item = design_stage5.next_operation(project)
    assert next_item["complete"] is False
    assert next_item["next"]["invalid_callers"] == ["adapter:transport"]


def test_unknown_internal_caller_module_is_rejected(tmp_path: Path) -> None:
    project = _project(tmp_path)
    path = project / "50_api_plan.json"
    path.write_text(
        path.read_text(encoding="utf-8").replace("boundary:transport", "module:missing"),
        encoding="utf-8",
    )
    report = design_stage5.coverage(project)
    assert report["operations"][0]["invalid_callers"] == ["module:missing"]
    assert report["invalid_refs"] == [{
        "operation": "public_op:archive.accept_transfer",
        "ref": "module:missing",
        "kind": "caller_module",
    }]


def test_next_reports_complete_when_plan_is_closed(tmp_path: Path) -> None:
    payload = design_stage5.next_operation(_project(tmp_path))
    assert payload["complete"] is True
    assert payload["next"] is None
    assert payload["summary"]["remaining"] == 0


def test_state5_lineage_rejects_extra_state4_flow_usage(tmp_path: Path) -> None:
    project = _project(tmp_path)
    flow_path = project / "40_flows.md"
    flow_path.write_text(
        flow_path.read_text(encoding="utf-8")
        + """
## `flow:accept_record_again`

### Trigger
Another transfer arrives.
### Boundary
`module:archive` through `capability:archive.accept_transfer`.
### Steps
1. Accept.
### Outcomes
Accepted or rejected.
### Errors
Archive errors.
""",
        encoding="utf-8",
    )
    report = design_stage5.coverage(project)
    row = report["operations"][0]
    assert row["actual_flow_usage"] == ["flow:accept_record", "flow:accept_record_again"]
    assert row["extra_flow_evidence"] == ["flow:accept_record_again"]
    assert report["summary"]["remaining"] == 1

    lint = design_stage5.lint(project)
    assert any(f["code"] == "public_op_flow_lineage_mismatch" for f in lint["findings"])


def test_state4_capability_must_have_state5_public_operation(tmp_path: Path) -> None:
    project = _project(tmp_path)
    flow_path = project / "40_flows.md"
    flow_path.write_text(
        flow_path.read_text(encoding="utf-8").replace(
            "`capability:archive.accept_transfer`.",
            "`capability:archive.accept_transfer` and `capability:archive.get_record`.",
        ),
        encoding="utf-8",
    )
    report = design_stage5.coverage(project)
    assert report["unowned_flow_capabilities"] == ["capability:archive.get_record"]
    assert report["summary"]["unowned_flow_capabilities"] == 1

    lint = design_stage5.lint(project)
    assert any(f["code"] == "flow_capability_without_public_op" for f in lint["findings"])


def test_current_cabinet_uses_closed_caller_vocabulary() -> None:
    report = design_stage5.coverage(CABINET)
    assert report["summary"]["invalid_refs"] == 0
    assert all(not operation["invalid_callers"] for operation in report["operations"])
    callers = [
        caller
        for operation in report["operations"]
        for caller in operation["callers"]
    ]
    assert callers
    assert all(
        caller.startswith("module:") or caller.startswith("boundary:")
        for caller in callers
    )
    assert not any(caller.startswith("adapter:") for caller in callers)
