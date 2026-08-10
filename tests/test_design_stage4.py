from __future__ import annotations

from pathlib import Path

import design_stage4


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "demo"
    _write(
        project / "30_modules.md",
        """# State 3 — Module responsibilities

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
""",
    )
    _write(
        project / "40_flows.md",
        """# State 4 — Key system flows

## `flow:accept_record`

### Trigger
A transfer arrives.

### Boundary
`module:archive` owns acceptance through `capability:archive.accept_transfer`.

### Steps
1. Validate and accept.

### Outcomes
Accepted or rejected.

### Errors
Archive errors remain archive-owned.
""",
    )
    return project


def test_flow_keys_and_refs_are_stable(tmp_path: Path) -> None:
    payload = design_stage4.handoff(_project(tmp_path))
    assert payload["schema_version"] == "spec_workbench_state4_handoff.v1"
    assert payload["lint_summary"]["errors"] == 0
    assert payload["flows"][0]["key"] == "flow:accept_record"
    assert payload["flows"][0]["module_refs"] == ("module:archive",)
    assert payload["flows"][0]["capability_refs"] == ("capability:archive.accept_transfer",)


def test_get_accepts_short_or_full_flow_key(tmp_path: Path) -> None:
    project = _project(tmp_path)
    assert design_stage4.get_flow(project, "accept_record")["key"] == "flow:accept_record"
    assert design_stage4.get_flow(project, "flow:accept_record")["key"] == "flow:accept_record"


def test_lint_rejects_unknown_state3_references(tmp_path: Path) -> None:
    project = _project(tmp_path)
    path = project / "40_flows.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace("module:archive", "module:missing"),
        encoding="utf-8",
    )
    report = design_stage4.lint(project)
    assert any(f["code"] == "unknown_module_ref" for f in report["findings"])


def test_lint_requires_flow_sections(tmp_path: Path) -> None:
    project = _project(tmp_path)
    path = project / "40_flows.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace("### Errors\nArchive errors remain archive-owned.\n", "")
    path.write_text(text, encoding="utf-8")
    report = design_stage4.lint(project)
    assert any(
        f["code"] == "missing_flow_section" and "Errors" in f["message"]
        for f in report["findings"]
    )
