from __future__ import annotations

import json
from pathlib import Path

import pytest

import design_lint


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _decision(
    key: str = "A1",
    *,
    formal_title: str = "Formal invariants",
    extra_sections: str = "",
) -> str:
    return f"""# State 2

## Accepted decision {key} — Canonical

### Normative rules

1. Preserve evidence.

{extra_sections}### {formal_title}

```text
evidence_is_preserved = true
```

### Required tests

1. Evidence remains available.

### Consequence

The decision is reviewable.
"""


def _codes(report: design_lint.LintReport) -> list[str]:
    return [finding.code for finding in report.findings]


def test_clean_canonical_decision_has_no_findings(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    _write(project / "02_rules.md", _decision())

    report = design_lint.lint_project(project)

    assert report.findings == ()
    assert report.state == 2
    assert report.summary.decisions == 1
    assert report.summary.open_questions == 0
    assert report.summary.errors == 0
    assert report.summary.warnings == 0
    assert design_lint.report_exit_code(report) == 0
    assert "OK: no authoring findings." in design_lint.render_human(report)


def test_missing_canonical_sections_are_review_warnings(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    _write(
        project / "02_rules.md",
        "# State 2\n\n## Accepted decision A1 — Minimal\n\nDecision body.\n",
    )

    report = design_lint.lint_project(project)

    assert _codes(report) == ["missing_canonical_section"] * 4 + [
        "section_not_nested"
    ]
    assert report.summary.warnings == 5
    assert report.summary.errors == 0
    assert design_lint.report_exit_code(report) == 0


@pytest.mark.parametrize("formal_title", ["Formal invariant", "Formal invariants"])
def test_singular_and_plural_formal_invariant_are_canonical(
    tmp_path: Path,
    formal_title: str,
) -> None:
    project = tmp_path / "demo"
    _write(project / "02_rules.md", _decision(formal_title=formal_title))

    report = design_lint.lint_project(project)

    assert report.findings == ()


def test_unusual_additional_sections_are_allowed(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    _write(
        project / "02_rules.md",
        _decision(
            extra_sections=(
                "### Payload rules\n\nPayload stays explicit.\n\n"
                "### Retry safety\n\nRetries are reviewed.\n\n"
                "### Supplier behavior\n\nSupplier evidence is retained.\n\n"
            )
        ),
    )

    report = design_lint.lint_project(project)

    assert report.findings == ()


def test_canonical_title_matching_normalizes_internal_whitespace(
    tmp_path: Path,
) -> None:
    project = tmp_path / "demo"
    _write(
        project / "02_rules.md",
        _decision().replace("### Normative rules", "### Normative   rules"),
    )

    report = design_lint.lint_project(project)

    assert report.findings == ()


def test_unusual_canonical_section_order_is_one_warning(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    _write(
        project / "02_rules.md",
        """# State 2

## Accepted decision A1 — Reordered

### Consequence
Outcome.

### Normative rules
1. Rule.

### Formal invariants
Invariant.

### Required tests
1. Test.
""",
    )

    report = design_lint.lint_project(project)

    assert _codes(report) == ["canonical_section_order"]
    assert report.findings[0].severity == "warning"


def test_exact_duplicate_section_is_ambiguity_error(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    document = _decision().replace(
        "### Normative rules\n",
        "### Normative rules\nFirst.\n\n### Normative rules\n",
        1,
    )
    _write(project / "02_rules.md", document)

    report = design_lint.lint_project(project)

    assert _codes(report) == ["ambiguous_section"]
    assert report.findings[0].severity == "error"
    assert design_lint.report_exit_code(report) == 1


def test_case_only_duplicate_section_is_warning_not_error(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    document = _decision().replace(
        "### Normative rules\n",
        "### Normative rules\nFirst.\n\n### NORMATIVE RULES\n",
        1,
    )
    _write(project / "02_rules.md", document)

    report = design_lint.lint_project(project)

    assert _codes(report) == [
        "duplicate_canonical_section",
        "duplicate_section_name",
    ]
    assert {finding.severity for finding in report.findings} == {"warning"}


def test_supporting_decision_source_key_is_info(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    document = _decision().replace(
        "## Accepted decision A1 — Canonical",
        "## Accepted decision",
    )
    _write(project / "02_rules_supporting.md", document)

    report = design_lint.lint_project(project)

    assert _codes(report) == ["supporting_decision"]
    finding = report.findings[0]
    assert finding.severity == "info"
    assert finding.item_key == "source:02_rules_supporting.md#accepted-decision"
    assert report.summary.supporting_decisions == 1


def test_flat_supporting_sections_report_not_nested(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    _write(
        project / "02_rules.md",
        """# State 2

## Accepted decision

Supporting body.

## Normative rules

1. This same-level section is outside the item.
""",
    )

    report = design_lint.lint_project(project)

    assert "section_not_nested" in _codes(report)
    finding = next(
        finding
        for finding in report.findings
        if finding.code == "section_not_nested"
    )
    assert finding.item_key == "source:02_rules.md#accepted-decision"
    assert finding.severity == "warning"


def test_unresolved_references_warn_and_statistics_distinguish_resolution(
    tmp_path: Path,
) -> None:
    project = tmp_path / "demo"
    _write(
        project / "02_a.md",
        _decision("A1").replace(
            "The decision is reviewable.",
            "A1 depends on A2 and OQ-404.",
        ),
    )
    _write(project / "02_b.md", _decision("A2"))

    report = design_lint.lint_project(project)

    assert _codes(report) == ["unresolved_reference"]
    assert report.findings[0].item_key == "A1"
    assert report.findings[0].severity == "warning"
    assert "OQ-404" in report.findings[0].message
    assert report.summary.explicit_references == 2
    assert report.summary.resolved_references == 1
    assert report.summary.unresolved_references == 1


def test_multiple_files_and_open_questions_are_counted(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    _write(project / "02_a.md", _decision("A1"))
    _write(
        project / "02_b.md",
        "# State 2\n\n## Open question OQ-1 — Retention\n\nHow long?\n",
    )

    report = design_lint.lint_project(project)

    assert report.summary.files == 2
    assert report.summary.decisions == 1
    assert report.summary.open_questions == 1
    assert report.findings == ()


def test_items_from_other_states_are_filtered_but_can_resolve_refs(
    tmp_path: Path,
) -> None:
    project = tmp_path / "demo"
    _write(
        project / "02_rules.md",
        _decision("A1").replace(
            "The decision is reviewable.",
            "A1 explicitly references A30.",
        ),
    )
    _write(
        project / "03_modules.md",
        "# State 3\n\n## Accepted decision A30 — Other state\n",
    )

    report = design_lint.lint_project(project, state=2)

    assert report.summary.decisions == 1
    assert report.summary.files == 1
    assert report.summary.explicit_references == 1
    assert report.summary.resolved_references == 1
    assert report.findings == ()


def test_duplicate_explicit_ids_are_errors_with_stable_location_order(
    tmp_path: Path,
) -> None:
    project = tmp_path / "demo"
    _write(project / "02_b.md", _decision("A1"))
    _write(project / "02_a.md", _decision("A1"))

    report = design_lint.lint_project(project)

    assert _codes(report) == ["duplicate_explicit_id"]
    finding = report.findings[0]
    assert finding.severity == "error"
    assert finding.path == "02_a.md"
    assert "02_a.md:3, 02_b.md:3" in finding.message


def test_json_and_finding_order_are_stable_across_files(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    _write(
        project / "02_b.md",
        "# State 2\n\n## Accepted decision A2 — Missing\n\nReferences OQ-9.\n",
    )
    _write(
        project / "02_a.md",
        "# State 2\n\n## Accepted decision A1 — Missing\n\nReferences OQ-8.\n",
    )

    report = design_lint.lint_project(project)
    rendered = design_lint.render_json(report)

    assert rendered == design_lint.render_json(design_lint.lint_project(project))
    payload = json.loads(rendered)
    assert list(payload) == [
        "findings",
        "project_root",
        "schema_version",
        "state",
        "summary",
    ]
    assert payload["schema_version"] == "spec_workbench_design_lint.v1"
    assert [finding["path"] for finding in payload["findings"]] == (
        ["02_a.md"] * 6 + ["02_b.md"] * 6
    )
    assert rendered.endswith("\n")


def test_cli_exit_codes_distinguish_lint_error_and_analysis_failure(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project = tmp_path / "demo"
    _write(project / "a.md", _decision("A1"))
    _write(project / "b.md", _decision("A1"))

    assert design_lint.main([str(project), "--state", "2", "--json"]) == 1
    lint_output = capsys.readouterr()
    assert json.loads(lint_output.out)["summary"]["errors"] == 1
    assert lint_output.err == ""

    assert design_lint.main([str(project), "--state", "3"]) == 2
    analysis_output = capsys.readouterr()
    assert analysis_output.out == ""
    assert "supports only State 2" in analysis_output.err


def test_missing_project_is_analysis_failure(tmp_path: Path) -> None:
    missing = tmp_path / "missing"

    with pytest.raises(design_lint.DesignLintError, match="directory not found"):
        design_lint.lint_project(missing)
