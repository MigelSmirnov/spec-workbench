#!/usr/bin/env python3
"""Deterministic State 2 authoring lint over ``design_index`` output.

The linter owns methodology checks and report rendering.  It deliberately does
not parse Markdown, infer semantics, compare design states, or assign owners.
Warnings are review prompts rather than claims that a specification is wrong.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal, Sequence

import design_index


SUPPORTED_STATE = 2
SCHEMA_VERSION = "spec_workbench_design_lint.v1"
Severity = Literal["error", "warning", "info"]
SEVERITY_ORDER: dict[Severity, int] = {"error": 0, "warning": 1, "info": 2}


@dataclass(frozen=True)
class CanonicalSection:
    key: str
    label: str
    aliases: frozenset[str]


CANONICAL_SECTIONS = (
    CanonicalSection("normative_rules", "Normative rules", frozenset({"normative rules"})),
    CanonicalSection(
        "formal_invariants",
        "Formal invariant(s)",
        frozenset({"formal invariant", "formal invariants"}),
    ),
    CanonicalSection("required_tests", "Required tests", frozenset({"required tests"})),
    CanonicalSection("consequence", "Consequence", frozenset({"consequence"})),
)


class DesignLintError(Exception):
    """The analysis could not be performed."""


@dataclass(frozen=True)
class Finding:
    severity: Severity
    code: str
    item_key: str
    path: str
    line: int
    message: str


@dataclass(frozen=True)
class LintSummary:
    files: int
    decisions: int
    open_questions: int
    supporting_decisions: int
    explicit_references: int
    resolved_references: int
    unresolved_references: int
    errors: int
    warnings: int
    info: int


@dataclass(frozen=True)
class LintReport:
    schema_version: str
    project_root: str
    state: int
    summary: LintSummary
    findings: tuple[Finding, ...]


def _normalized_title(title: str) -> str:
    return " ".join(title.casefold().split())


def _finding(
    severity: Severity,
    code: str,
    item: dict[str, object],
    message: str,
    *,
    line: int | None = None,
) -> Finding:
    return Finding(
        severity=severity,
        code=code,
        item_key=item["key"],
        path=item["source"]["path"],
        line=line if line is not None else item["source"]["start_line"],
        message=message,
    )


def _finding_sort_key(finding: Finding) -> tuple[object, ...]:
    return (
        finding.path,
        finding.line,
        finding.item_key,
        SEVERITY_ORDER[finding.severity],
        finding.code,
        finding.message,
    )


def _duplicate_section_findings(item: dict[str, object]) -> list[Finding]:
    findings: list[Finding] = []
    by_exact: dict[str, list[dict[str, object]]] = defaultdict(list)
    by_normalized: dict[str, list[dict[str, object]]] = defaultdict(list)
    for section in item["sections"]:
        by_exact[section["title"]].append(section)
        by_normalized[_normalized_title(section["title"])].append(section)

    exact_ambiguous: set[str] = set()
    for title, sections in sorted(by_exact.items()):
        if len(sections) <= 1:
            continue
        exact_ambiguous.add(_normalized_title(title))
        findings.append(
            _finding(
                "error",
                "ambiguous_section",
                item,
                f"Section title {title!r} occurs {len(sections)} times and is not uniquely addressable.",
                line=sections[0]["start_line"],
            )
        )

    for normalized, sections in sorted(by_normalized.items()):
        if len(sections) <= 1 or normalized in exact_ambiguous:
            continue
        rendered = ", ".join(repr(section["title"]) for section in sections)
        findings.append(
            _finding(
                "warning",
                "duplicate_section_name",
                item,
                f"Section titles differ only by case or whitespace: {rendered}.",
                line=sections[0]["start_line"],
            )
        )
    return findings


def _canonical_section_findings(item: dict[str, object]) -> list[Finding]:
    findings: list[Finding] = []
    sections = item["sections"]
    positions: dict[str, list[int]] = {}

    for canonical in CANONICAL_SECTIONS:
        matches = [
            index
            for index, section in enumerate(sections)
            if _normalized_title(section["title"]) in canonical.aliases
        ]
        positions[canonical.key] = matches
        if not matches:
            findings.append(
                _finding(
                    "warning",
                    "missing_canonical_section",
                    item,
                    f"Review decision: canonical section {canonical.label!r} is absent.",
                )
            )
        elif len(matches) > 1:
            exact_titles = [sections[index]["title"] for index in matches]
            if len(set(exact_titles)) == len(exact_titles):
                findings.append(
                    _finding(
                        "warning",
                        "duplicate_canonical_section",
                        item,
                        f"Canonical role {canonical.label!r} appears under multiple aliases.",
                        line=sections[matches[0]]["start_line"],
                    )
                )

    expected = [
        canonical.key
        for canonical in CANONICAL_SECTIONS
        if positions[canonical.key]
    ]
    observed = [
        key
        for _, key in sorted(
            (positions[canonical.key][0], canonical.key)
            for canonical in CANONICAL_SECTIONS
            if positions[canonical.key]
        )
    ]
    if observed != expected:
        labels = {canonical.key: canonical.label for canonical in CANONICAL_SECTIONS}
        rendered = " -> ".join(labels[key] for key in observed)
        findings.append(
            _finding(
                "warning",
                "canonical_section_order",
                item,
                f"Canonical sections appear in an unusual order: {rendered}.",
            )
        )
    return findings


def _duplicate_item_findings(
    index: dict[str, object],
    selected_items: list[dict[str, object]],
) -> list[Finding]:
    selected_keys = {item["key"] for item in selected_items}
    duplicates = [
        key
        for key in index["diagnostics"]["duplicate_keys"]
        if key in selected_keys
    ]
    findings: list[Finding] = []
    for key in sorted(duplicates):
        occurrences = [item for item in index["items"] if item["key"] == key]
        selected_occurrences = [
            item for item in occurrences if item["state"] == SUPPORTED_STATE
        ]
        anchor = min(
            selected_occurrences,
            key=lambda item: (item["source"]["path"], item["source"]["start_line"]),
        )
        locations = ", ".join(
            f"{item['source']['path']}:{item['source']['start_line']}"
            for item in sorted(
                occurrences,
                key=lambda item: (item["source"]["path"], item["source"]["start_line"]),
            )
        )
        code = "duplicate_explicit_id" if anchor["explicit_id"] else "duplicate_item_key"
        findings.append(
            _finding(
                "error",
                code,
                anchor,
                f"Design item key {key!r} is duplicated at {locations}.",
            )
        )
    return findings


def lint_project(project: Path, *, state: int = SUPPORTED_STATE) -> LintReport:
    """Analyze one design state using only the structural design index."""
    if state != SUPPORTED_STATE:
        raise DesignLintError(
            f"design_lint v1 supports only State {SUPPORTED_STATE}, got State {state}"
        )
    project = project.resolve()
    if not project.is_dir():
        raise DesignLintError(f"project directory not found: {project}")
    try:
        index = design_index.build_index(project)
    except Exception as exc:
        raise DesignLintError(f"design index could not be built: {exc}") from exc

    selected_items = [item for item in index["items"] if item["state"] == state]
    decisions = [item for item in selected_items if item["kind"] == "decision"]
    open_questions = [
        item for item in selected_items if item["kind"] == "open_question"
    ]
    known_keys = {item["key"] for item in index["items"]}
    findings = _duplicate_item_findings(index, selected_items)

    for item in decisions:
        findings.extend(_duplicate_section_findings(item))
        findings.extend(_canonical_section_findings(item))
        if not item["sections"]:
            findings.append(
                _finding(
                    "warning",
                    "section_not_nested",
                    item,
                    "Decision has no indexed child sections; nest owned headings deeper than the decision heading.",
                )
            )
        if item["explicit_id"] is None:
            findings.append(
                _finding(
                    "info",
                    "supporting_decision",
                    item,
                    f"Supporting decision uses source key {item['key']!r}; explicit ID is optional.",
                )
            )

    unresolved_count = 0
    for item in selected_items:
        for reference in item["explicit_refs"]:
            if reference in known_keys:
                continue
            unresolved_count += 1
            findings.append(
                _finding(
                    "warning",
                    "unresolved_reference",
                    item,
                    f"Explicit reference {reference!r} does not resolve to an indexed item.",
                )
            )

    ordered_findings = tuple(sorted(findings, key=_finding_sort_key))
    severities = Counter(finding.severity for finding in ordered_findings)
    reference_count = sum(len(item["explicit_refs"]) for item in selected_items)
    summary = LintSummary(
        files=len({item["source"]["path"] for item in selected_items}),
        decisions=len(decisions),
        open_questions=len(open_questions),
        supporting_decisions=sum(item["explicit_id"] is None for item in decisions),
        explicit_references=reference_count,
        resolved_references=reference_count - unresolved_count,
        unresolved_references=unresolved_count,
        errors=severities["error"],
        warnings=severities["warning"],
        info=severities["info"],
    )
    return LintReport(
        schema_version=SCHEMA_VERSION,
        project_root=project.name,
        state=state,
        summary=summary,
        findings=ordered_findings,
    )


def render_json(report: LintReport) -> str:
    """Render a stable machine-readable report."""
    return json.dumps(asdict(report), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_human(report: LintReport) -> str:
    """Render a concise deterministic report for authoring review."""
    summary = report.summary
    lines = [
        f"Design lint: {report.project_root} (State {report.state})",
        (
            "Summary: "
            f"{summary.decisions} decisions, "
            f"{summary.open_questions} open questions, "
            f"{summary.explicit_references} references "
            f"({summary.unresolved_references} unresolved), "
            f"{summary.files} files"
        ),
        (
            "Findings: "
            f"{summary.errors} errors, "
            f"{summary.warnings} warnings, "
            f"{summary.info} info"
        ),
    ]
    for finding in report.findings:
        lines.append(
            f"{finding.severity.upper()} {finding.code} "
            f"{finding.item_key} {finding.path}:{finding.line} - {finding.message}"
        )
    if not report.findings:
        lines.append("OK: no authoring findings.")
    return "\n".join(lines) + "\n"


def report_exit_code(report: LintReport) -> int:
    return 1 if report.summary.errors else 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path, help="Directory containing design Markdown")
    parser.add_argument(
        "--state",
        type=int,
        default=SUPPORTED_STATE,
        help=f"Design state to lint (v1: only {SUPPORTED_STATE})",
    )
    parser.add_argument("--json", action="store_true", help="Emit stable JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        report = lint_project(args.project, state=args.state)
    except DesignLintError as exc:
        print(f"design_lint: error: {exc}", file=sys.stderr)
        return 2
    output = render_json(report) if args.json else render_human(report)
    print(output, end="")
    return report_exit_code(report)


if __name__ == "__main__":
    raise SystemExit(main())
