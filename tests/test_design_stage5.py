from __future__ import annotations

from pathlib import Path

import design_stage5


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
      "key": "api:archive.accept_transfer",
      "capability": "capability:archive.accept_transfer",
      "flows": ["flow:accept_record"],
      "callers": ["adapter:transport"],
      "purpose": "Accept one record."
    }
  ]
}
""")
    _write(project / "50_public_apis.md", """# State 5 — Public APIs

## `api:archive.accept_transfer`

### Owner
`module:archive`
### Callers
Transport adapter.
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


def test_state5_handoff_has_stable_api_key(tmp_path: Path) -> None:
    payload = design_stage5.handoff(_project(tmp_path))
    assert payload["schema_version"] == "spec_workbench_state5_handoff.v1"
    assert payload["lint_summary"]["errors"] == 0
    assert payload["apis"][0]["key"] == "api:archive.accept_transfer"


def test_coverage_requires_state4_flow_evidence(tmp_path: Path) -> None:
    project = _project(tmp_path)
    path = project / "40_flows.md"
    path.write_text(path.read_text(encoding="utf-8").replace("capability:archive.accept_transfer", "capability:archive.missing"), encoding="utf-8")
    report = design_stage5.coverage(project)
    assert report["apis"][0]["flow_evidence_missing"] == ["flow:accept_record"]


def test_lint_requires_api_sections(tmp_path: Path) -> None:
    project = _project(tmp_path)
    path = project / "50_public_apis.md"
    path.write_text(path.read_text(encoding="utf-8").replace("### Errors\nInvalid transfer.\n", ""), encoding="utf-8")
    report = design_stage5.lint(project)
    assert any(f["code"] == "missing_api_section" and "Errors" in f["message"] for f in report["findings"])


def test_next_reports_complete_when_plan_is_closed(tmp_path: Path) -> None:
    payload = design_stage5.next_api(_project(tmp_path))
    assert payload["complete"] is True
    assert payload["next"] is None
    assert payload["summary"]["remaining"] == 0
