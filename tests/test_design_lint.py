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
    security_review: str | None = None,
) -> str:
    review = _security_review() if security_review is None else security_review
    return f"""# State 2

## Accepted decision {key} — Canonical

### Normative rules

1. Preserve evidence.

{extra_sections}{review}### {formal_title}

```text
evidence_is_preserved = true
```

### Required tests

1. Evidence remains available.

### Consequence

The decision is reviewable.
"""


def _security_review(**overrides: str) -> str:
    records = {
        category: (
            f"- {category}: NOT_APPLICABLE; "
            f"rationale: test fixture checked {category} and has no applicable boundary"
        )
        for category in design_lint.SECURITY_CATEGORIES
    }
    records.update(overrides)
    return (
        "### Security review\n\n"
        "Security review: PERFORMED\n\n"
        + "\n".join(records[category] for category in design_lint.SECURITY_CATEGORIES)
        + "\n\n"
    )


def _codes(report: design_lint.LintReport) -> list[str]:
    return [finding.code for finding in report.findings]


def _model(
    identity: str = "entity",
    evidence: str = "Continuity matters.",
    questions: str = "None.",
) -> str:
    return f"""# State 1 — Models

## Model M12 — StoredInvoiceCard

### Meaning

Archive root.

### Identity

{identity}

### Identity evidence

{evidence}

### Source of truth

Cabinet Backend.

### Lifecycle

Active or archived.

### Persistence candidate

Durable.

### Open questions

{questions}
"""


def test_state1_model_identity_closure_passes(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    _write(project / "01_models.md", _model())

    report = design_lint.lint_project(project, state=1)

    assert report.findings == ()
    assert report.summary.models == 1
    assert design_lint.report_exit_code(report) == 0


def test_state1_requires_identity_and_evidence_sections(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    _write(
        project / "01_models.md",
        "# State 1\n\n## Model M1 — RuntimeThing\n\n### Meaning\n\nNeeded.\n",
    )

    report = design_lint.lint_project(project, state=1)

    assert _codes(report) == [
        "missing_identity_evidence",
        "missing_identity_section",
    ]
    assert report.summary.errors == 2


def test_state1_rejects_identity_hidden_in_prose(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    _write(project / "01_models.md", _model(identity="This is probably entity."))

    report = design_lint.lint_project(project, state=1)

    assert _codes(report) == ["invalid_identity"]


def test_state1_unresolved_requires_and_respects_block(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    _write(
        project / "01_models.md",
        _model(identity="UNRESOLVED", questions="BLOCK: Does continuity matter?"),
    )

    report = design_lint.lint_project(project, state=1)

    assert _codes(report) == ["invalid_identity", "blocking_open_question"]
    assert design_lint.report_exit_code(report) == 1


def test_state1_unresolved_prose_without_block_is_error(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    _write(project / "01_models.md", _model(evidence="UNRESOLVED in product requirements."))

    report = design_lint.lint_project(project, state=1)

    assert _codes(report) == ["unresolved_without_block"]


def test_state1_unresolved_marker_anywhere_in_model_requires_block(
    tmp_path: Path,
) -> None:
    project = tmp_path / "demo"
    document = _model().replace("Archive root.", "Archive root; source is UNRESOLVED.")
    _write(project / "01_models.md", document)

    report = design_lint.lint_project(project, state=1)

    assert _codes(report) == ["unresolved_without_block"]


def test_state1_legacy_runtime_heading_is_not_silently_skipped(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    _write(project / "01_models.md", "# State 1\n\n## StoredInvoiceCard\n\nArchive root.\n")

    report = design_lint.lint_project(project, state=1)

    assert _codes(report) == ["unindexed_runtime_model"]


def test_clean_canonical_decision_has_no_findings(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    _write(project / "02_rules.md", _decision())

    report = design_lint.lint_project(project)

    assert report.findings == ()
    assert report.state == 2
    assert report.summary.decisions == 1
    assert report.summary.models == 0
    assert report.summary.open_questions == 0
    assert report.summary.errors == 0
    assert report.summary.warnings == 0
    assert design_lint.report_exit_code(report) == 0
    assert "OK: no authoring findings." in design_lint.render_human(report)


def test_security_review_fully_closed_with_indexed_decision_passes(
    tmp_path: Path,
) -> None:
    project = tmp_path / "demo"
    _write(project / "02_policy.md", _decision("A1", security_review=""))
    review = _security_review(
        authorization=(
            "- authorization: APPLICABLE; references: A1; affected: M12"
        ),
    )
    _write(project / "02_review.md", _decision("A2", security_review=review))

    report = design_lint.lint_project(project, state=2)

    assert report.findings == ()
    assert report.summary.decisions == 2
    assert report.summary.resolved_references == 1
    assert design_lint.report_exit_code(report) == 0


def test_security_review_missing_category_is_error(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    review = _security_review().replace(
        next(
            line
            for line in _security_review().splitlines()
            if line.startswith("- dependencies:")
        )
        + "\n",
        "",
    )
    _write(project / "02_rules.md", _decision(security_review=review))

    report = design_lint.lint_project(project, state=2)

    assert _codes(report) == ["missing_security_category"]
    assert report.findings[0].section == "dependencies"
    assert design_lint.report_exit_code(report) == 1


def test_security_review_not_applicable_requires_rationale(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    review = _security_review(
        secrets="- secrets: NOT_APPLICABLE",
    )
    _write(project / "02_rules.md", _decision(security_review=review))

    report = design_lint.lint_project(project, state=2)

    assert _codes(report) == ["missing_not_applicable_rationale"]


def test_security_review_unresolved_is_blocking_error(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    review = _security_review(
        concurrency="- concurrency: UNRESOLVED; references: OQ-1; affected: Credit",
    )
    document = _decision(security_review=review) + (
        "\n## Open question OQ-1 — Atomicity\n\n"
        "Who owns the atomic transition?\n"
    )
    _write(project / "02_rules.md", document)

    report = design_lint.lint_project(project, state=2)

    assert _codes(report) == ["security_unresolved"]
    assert design_lint.report_exit_code(report) == 1


def test_security_review_applicable_reference_must_resolve(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    review = _security_review(
        authorization="- authorization: APPLICABLE; references: A404; affected: M12",
    )
    _write(project / "02_rules.md", _decision(security_review=review))

    report = design_lint.lint_project(project, state=2)

    assert "unresolved_security_reference" in _codes(report)
    assert design_lint.report_exit_code(report) == 1


def test_state2_without_security_review_is_blocked(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    _write(project / "02_rules.md", _decision(security_review=""))

    report = design_lint.lint_project(project, state=2)

    assert _codes(report) == ["missing_security_review"]
    assert design_lint.report_exit_code(report) == 1


def test_missing_canonical_sections_are_review_warnings(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    _write(
        project / "02_rules.md",
        "# State 2\n\n## Accepted decision A1 — Minimal\n\nDecision body.\n",
    )

    report = design_lint.lint_project(project)

    assert _codes(report) == ["missing_security_review"] + ["missing_canonical_section"] * 4 + [
        "section_not_nested"
    ]
    # the fence: every review-grade finding stops
    assert report.summary.warnings == 0
    assert report.summary.errors == 6
    assert design_lint.report_exit_code(report) == 1


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
""" + _security_review(),
    )

    report = design_lint.lint_project(project)

    assert _codes(report) == ["canonical_section_order"]
    assert report.findings[0].severity == "error"


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
    assert {finding.severity for finding in report.findings} == {"error"}


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
    assert finding.severity == "error"


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
    _write(project / "02_b.md", _decision("A2", security_review=""))

    report = design_lint.lint_project(project)

    assert _codes(report) == ["unresolved_reference"]
    assert report.findings[0].item_key == "A1"
    assert report.findings[0].severity == "error"
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
    _write(project / "02_b.md", _decision("A1", security_review=""))
    _write(project / "02_a.md", _decision("A1"))

    report = design_lint.lint_project(project)

    assert _codes(report) == ["duplicate_explicit_id"]
    finding = report.findings[0]
    assert finding.severity == "error"
    assert finding.source.path == "02_a.md"
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
    assert payload["schema_version"] == "spec_workbench_design_lint.v2"
    assert [finding["source"]["path"] for finding in payload["findings"]] == (
        ["02_a.md"] * 7 + ["02_b.md"] * 6
    )
    assert rendered.endswith("\n")


def test_cli_exit_codes_distinguish_lint_error_and_analysis_failure(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project = tmp_path / "demo"
    _write(project / "a.md", _decision("A1"))
    _write(project / "b.md", _decision("A1", security_review=""))

    assert design_lint.main([str(project), "--state", "2", "--json"]) == 1
    lint_output = capsys.readouterr()
    assert json.loads(lint_output.out)["summary"]["errors"] == 1
    assert lint_output.err == ""

    assert design_lint.main([str(project), "--state", "3"]) == 2
    analysis_output = capsys.readouterr()
    assert analysis_output.out == ""
    assert "supports States 1 and 2" in analysis_output.err


def test_missing_project_is_analysis_failure(tmp_path: Path) -> None:
    missing = tmp_path / "missing"

    with pytest.raises(design_lint.DesignLintError, match="directory not found"):
        design_lint.lint_project(missing)


def test_small_item_finding_contains_complete_structural_context(
    tmp_path: Path,
) -> None:
    project = tmp_path / "demo"
    _write(
        project / "02_rules.md",
        "# State 2\n\n## Accepted decision A1 — Minimal\n\nDecision body.\n",
    )

    report = design_lint.lint_project(project)
    finding = next(
        finding
        for finding in report.findings
        if finding.code == "section_not_nested"
    )

    assert finding.source == design_lint.SourceLocation("02_rules.md", 3)
    assert finding.section is None
    assert finding.heading_path == (
        "State 2",
        "Accepted decision A1 — Minimal",
    )
    assert finding.item_range == design_lint.LineRange(3, 5)
    assert finding.context_range == finding.item_range
    assert finding.section_outline == ()
    assert finding.context_lines == (
        "3: ## Accepted decision A1 — Minimal",
        "4: ",
        "5: Decision body.",
    )


def test_long_item_finding_uses_outline_and_local_structural_window(
    tmp_path: Path,
) -> None:
    project = tmp_path / "demo"
    normative_body = "\n".join(
        f"Rule evidence line {number}." for number in range(1, 131)
    )
    consequence_body = "\n".join(
        f"Consequence evidence line {number}." for number in range(1, 41)
    )
    _write(
        project / "02_rules.md",
        f"""# State 2

## Accepted decision A1 — Long decision

### Normative rules
{normative_body}

### Required tests
1. Verify the rule.

### Consequence
{consequence_body}
""",
    )

    report = design_lint.lint_project(project)
    finding = next(
        finding
        for finding in report.findings
        if finding.code == "missing_canonical_section"
        and finding.section == "Formal invariant(s)"
    )

    assert finding.item_range.end_line - finding.item_range.start_line + 1 > 120
    assert finding.context_range == design_lint.LineRange(
        finding.source.line - 14,
        finding.source.line + 14,
    )
    assert len(finding.context_lines) == 29
    assert finding.context_range != finding.item_range
    assert [section.title for section in finding.section_outline] == [
        "Normative rules",
        "Required tests",
        "Consequence",
    ]
    assert finding.source.line == finding.section_outline[1].start_line
    assert any("### Required tests" in line for line in finding.context_lines)


def test_item_within_full_context_threshold_is_not_reduced_to_local_window(
    tmp_path: Path,
) -> None:
    project = tmp_path / "demo"
    body = "\n".join(f"Evidence line {number}." for number in range(1, 51))
    _write(
        project / "02_rules.md",
        f"# State 2\n\n## Accepted decision A1 — Medium\n\n{body}\n",
    )

    finding = design_lint.lint_project(project).findings[0]

    assert finding.item_range.end_line - finding.item_range.start_line + 1 == 52
    assert finding.context_range == finding.item_range
    assert len(finding.context_lines) == 52


def test_human_context_is_default_and_compact_hides_blast_radius(
    tmp_path: Path,
) -> None:
    project = tmp_path / "demo"
    _write(
        project / "02_rules.md",
        "# State 2\n\n## Accepted decision A1 — Minimal\n\nDecision body.\n",
    )
    report = design_lint.lint_project(project)

    contextual = design_lint.render_human(report)
    compact = design_lint.render_human(report, compact=True)

    assert "  item range: 3-5" in contextual
    assert "  heading path: State 2 > Accepted decision A1 — Minimal" in contextual
    assert "  sections:" in contextual
    assert "  context 3-5:" in contextual
    assert "3: ## Accepted decision A1 — Minimal" in contextual
    assert "  item: A1" in compact
    assert "  source: 02_rules.md:3" in compact
    assert "  item range:" not in compact
    assert "  context " not in compact


def test_json_always_contains_structural_context(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project = tmp_path / "demo"
    _write(
        project / "02_rules.md",
        "# State 2\n\n## Accepted decision A1 — Minimal\n\nDecision body.\n",
    )

    assert design_lint.main([str(project), "--json", "--compact"]) == 1
    payload = json.loads(capsys.readouterr().out)
    finding = payload["findings"][0]

    assert finding["source"] == {"line": 3, "path": "02_rules.md"}
    assert finding["item_range"] == {"end_line": 5, "start_line": 3}
    assert finding["context_range"] == {"end_line": 5, "start_line": 3}
    assert finding["context_lines"][0].startswith("3: ## Accepted decision")
    assert "section_outline" in finding
    assert "heading_path" in finding


def test_cli_compact_flag_controls_only_human_context(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project = tmp_path / "demo"
    _write(
        project / "02_rules.md",
        "# State 2\n\n## Accepted decision A1 — Minimal\n\nDecision body.\n",
    )

    assert design_lint.main([str(project)]) == 1
    contextual = capsys.readouterr().out
    assert "  item range: 3-5" in contextual
    assert "  context 3-5:" in contextual

    assert design_lint.main([str(project), "--compact"]) == 1
    compact = capsys.readouterr().out
    assert "  item: A1" in compact
    assert "  item range:" not in compact
    assert "  context " not in compact


def test_lint_delegates_context_building_to_design_index(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / "demo"
    _write(
        project / "02_rules.md",
        "# State 2\n\n## Accepted decision A1 — Minimal\n\nDecision body.\n",
    )
    real_context_at = design_lint.design_index.context_at
    calls: list[tuple[Path, str, int]] = []

    def record_context(project_path: Path, location: str, *, radius: int = 3):
        calls.append((project_path, location, radius))
        return real_context_at(project_path, location, radius=radius)

    monkeypatch.setattr(design_lint.design_index, "context_at", record_context)

    report = design_lint.lint_project(project)

    assert len(calls) == len(report.findings)
    assert all(call[0] == project.resolve() for call in calls)
