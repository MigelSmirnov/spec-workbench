from __future__ import annotations

from pathlib import Path

import design_stage3


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "demo"
    _write(
        project / "01_models.md",
        """# State 1 — Models

## Model M01 — Record

### Meaning

A record.

### Identity

entity

### Identity evidence

Stable id.
""",
    )
    _write(
        project / "02_rules.md",
        """# State 2 — Rules

## Accepted decision A10 — Preserve records

### Normative rules

1. Preserve them.

### Formal invariants

record_preserved

### Required tests

1. It remains.

### Consequence

History survives.
""",
    )
    _write(
        project / "30_modules.md",
        """# State 3 — Module responsibilities

## `archive`

### Trace inputs

- A10
- M01

### Owns

- durable record preservation.

### Knows

- preservation semantics.

### Hides

- persistence sequencing.

### Must not own

- transport.

### Candidate public capabilities

```text
store_record
get_record
```

### Depth assessment

Deep archive module.
""",
    )
    return project


def test_module_keys_and_capabilities_are_stable_handoff(tmp_path: Path) -> None:
    payload = design_stage3.handoff(_project(tmp_path))

    assert payload["schema_version"] == "spec_workbench_state3_handoff.v1"
    assert payload["modules"] == [
        {
            "key": "module:archive",
            "name": "archive",
            "capabilities": ["get_record", "store_record"],
            "upstream_refs": ["A10", "M01"],
        }
    ]


def test_get_accepts_full_or_short_module_key(tmp_path: Path) -> None:
    project = _project(tmp_path)

    assert design_stage3.get_module(project, "archive")["key"] == "module:archive"
    assert design_stage3.get_module(project, "module:archive")["key"] == "module:archive"


def test_trace_maps_explicit_inputs_to_module_and_reports_coverage(tmp_path: Path) -> None:
    trace = design_stage3.trace(_project(tmp_path))

    assert trace["upstream_to_modules"]["A10"] == ["module:archive"]
    assert trace["upstream_to_modules"]["M01"] == ["module:archive"]
    assert trace["unresolved_references"] == []
    assert trace["unclaimed_state2_decisions"] == []


def test_refs_outside_trace_inputs_do_not_create_graph_edges(tmp_path: Path) -> None:
    project = _project(tmp_path)
    path = project / "30_modules.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "### Owns\n", "Text elsewhere mentions A99 but is not a trace edge.\n\n### Owns\n"
        ),
        encoding="utf-8",
    )

    module = design_stage3.get_module(project, "archive")

    assert module["upstream_refs"] == ("A10", "M01") or module["upstream_refs"] == ["A10", "M01"]


def test_lint_rejects_unresolved_trace_input(tmp_path: Path) -> None:
    project = _project(tmp_path)
    path = project / "30_modules.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace("- A10\n", "- A99\n"),
        encoding="utf-8",
    )

    report = design_stage3.lint(project)
    codes = {finding["code"] for finding in report["findings"]}

    assert report["summary"]["errors"] == 1
    assert "unresolved_upstream_reference" in codes
    assert report["summary"]["unclaimed_state2_decisions"] == 1


def test_lint_requires_module_responsibility_sections(tmp_path: Path) -> None:
    project = _project(tmp_path)
    path = project / "30_modules.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace("### Must not own\n\n- transport.\n\n", ""),
        encoding="utf-8",
    )

    report = design_stage3.lint(project)

    assert any(
        finding["code"] == "missing_module_section"
        and "Must not own" in finding["message"]
        for finding in report["findings"]
    )


def test_missing_trace_inputs_is_warning_not_inferred_from_prose(tmp_path: Path) -> None:
    project = _project(tmp_path)
    path = project / "30_modules.md"
    text = path.read_text(encoding="utf-8")
    start = text.index("### Trace inputs")
    end = text.index("### Owns")
    path.write_text(text[:start] + "A10 is mentioned in prose.\n\n" + text[end:], encoding="utf-8")

    report = design_stage3.lint(project)

    assert any(finding["code"] == "missing_trace_inputs_section" for finding in report["findings"])
    assert design_stage3.get_module(project, "archive")["upstream_refs"] == () or design_stage3.get_module(project, "archive")["upstream_refs"] == []


def test_generic_module_name_is_error(tmp_path: Path) -> None:
    project = _project(tmp_path)
    path = project / "30_modules.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace("`archive`", "`utils`"),
        encoding="utf-8",
    )

    report = design_stage3.lint(project)

    assert any(finding["code"] == "generic_module_name" for finding in report["findings"])
