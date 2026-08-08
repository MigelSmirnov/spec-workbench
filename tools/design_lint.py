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
SCHEMA_VERSION = "spec_workbench_design_lint.v2"
FULL_ITEM_CONTEXT_MAX_LINES = 120
LONG_ITEM_CONTEXT_RADIUS = 14
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
class SourceLocation:
    path: str
    line: int


@dataclass(frozen=True)
class LineRange:
    start_line: int
    end_line: int


@dataclass(frozen=True)
class SectionOutline:
    title: str
    level: int
    start_line: int
    end_line: int


@dataclass(frozen=True)
class Finding:
    severity: Severity
    code: str
    message: str
    item_key: str
    source: SourceLocation
    section: str | None
    heading_path: tuple[str, ...]
    item_range: LineRange
    section_outline: tuple[SectionOutline, ...]
    context_range: LineRange
    context_lines: tuple[str, ...]


@dataclass(frozen=True)
class _FindingDraft:
    severity: Severity
    code: str
    message: str
    item: dict[str, object]
    line: int
    section: str | None


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


def _draft(
    severity: Severity,
    code: str,
    item: dict[str, object],
    message: str,
    *,
    line: int | None = None,
    section: str | None = None,
) -> _FindingDraft:
    return _FindingDraft(
        severity=severity,
        code=code,
        line=line if line is not None else item["source"]["start_line"],
        message=message,
        item=item,
        section=section,
    )


def _finding_sort_key(finding: _FindingDraft) -> tuple[object, ...]:
    return (
        finding.item["source"]["path"],
        finding.line,
        finding.item["key"],
        SEVERITY_ORDER[finding.severity],
        finding.code,
        finding.message,
    )


def _duplicate_section_findings(item: dict[str, object]) -> list[_FindingDraft]:
    findings: list[_FindingDraft] = []
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
            _draft(
                "error",
                "ambiguous_section",
                item,
                f"Section title {title!r} occurs {len(sections)} times and is not uniquely addressable.",
                line=sections[0]["start_line"],
                section=title,
            )
        )

    for normalized, sections in sorted(by_normalized.items()):
        if len(sections) <= 1 or normalized in exact_ambiguous:
            continue
        rendered = ", ".join(repr(section["title"]) for section in sections)
        findings.append(
            _draft(
                "warning",
                "duplicate_section_name",
                item,
                f"Section titles differ only by case or whitespace: {rendered}.",
                line=sections[0]["start_line"],
                section=sections[0]["title"],
            )
        )
    return findings


def _missing_section_anchor(
    item: dict[str, object],
    canonical_index: int,
    positions: dict[str, list[int]],
) -> int:
    sections = item["sections"]
    for candidate in CANONICAL_SECTIONS[canonical_index + 1 :]:
        if positions.get(candidate.key):
            return sections[positions[candidate.key][0]]["start_line"]
    for candidate in reversed(CANONICAL_SECTIONS[:canonical_index]):
        if positions.get(candidate.key):
            return sections[positions[candidate.key][-1]]["end_line"]
    return item["source"]["start_line"]


def _canonical_section_findings(item: dict[str, object]) -> list[_FindingDraft]:
    findings: list[_FindingDraft] = []
    sections = item["sections"]
    positions = {
        canonical.key: [
            index
            for index, section in enumerate(sections)
            if _normalized_title(section["title"]) in canonical.aliases
        ]
        for canonical in CANONICAL_SECTIONS
    }

    for canonical_index, canonical in enumerate(CANONICAL_SECTIONS):
        matches = positions[canonical.key]
        if not matches:
            findings.append(
                _draft(
                    "warning",
                    "missing_canonical_section",
                    item,
                    f"Review decision: canonical section {canonical.label!r} is absent.",
                    line=_missing_section_anchor(item, canonical_index, positions),
                    section=canonical.label,
                )
            )
        elif len(matches) > 1:
            exact_titles = [sections[index]["title"] for index in matches]
            if len(set(exact_titles)) == len(exact_titles):
                findings.append(
                    _draft(
                        "warning",
                        "duplicate_canonical_section",
                        item,
                        f"Canonical role {canonical.label!r} appears under multiple aliases.",
                        line=sections[matches[0]]["start_line"],
                        section=canonical.label,
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
            _draft(
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
) -> list[_FindingDraft]:
    selected_keys = {item["key"] for item in selected_items}
    duplicates = [
        key
        for key in index["diagnostics"]["duplicate_keys"]
        if key in selected_keys
    ]
    findings: list[_FindingDraft] = []
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
            _draft(
                "error",
                code,
                anchor,
                f"Design item key {key!r} is duplicated at {locations}.",
            )
        )
    return findings


def _enrich_finding(project: Path, draft: _FindingDraft) -> Finding:
    item = draft.item
    item_start = item["source"]["start_line"]
    item_end = item["source"]["end_line"]
    anchor = min(max(draft.line, item_start), item_end)
    item_line_count = item_end - item_start + 1
    if item_line_count <= FULL_ITEM_CONTEXT_MAX_LINES:
        context_start = item_start
        context_end = item_end
    else:
        context_start = max(item_start, anchor - LONG_ITEM_CONTEXT_RADIUS)
        context_end = min(item_end, anchor + LONG_ITEM_CONTEXT_RADIUS)
    radius = max(anchor - context_start, context_end - anchor)
    location = f"{item['source']['path']}:{anchor}"
    try:
        context = design_index.context_at(project, location, radius=radius)
    except Exception as exc:
        raise DesignLintError(
            f"structural context could not be built for {item['key']} at {location}: {exc}"
        ) from exc
    context_lines = tuple(
        rendered
        for line_number, rendered in zip(
            range(context.start_line, context.end_line + 1),
            context.lines,
        )
        if context_start <= line_number <= context_end
    )
    return Finding(
        severity=draft.severity,
        code=draft.code,
        message=draft.message,
        item_key=item["key"],
        source=SourceLocation(item["source"]["path"], anchor),
        section=draft.section,
        heading_path=context.heading_path,
        item_range=LineRange(item_start, item_end),
        section_outline=tuple(
            SectionOutline(
                section["title"],
                section["level"],
                section["start_line"],
                section["end_line"],
            )
            for section in item["sections"]
        ),
        context_range=LineRange(context_start, context_end),
        context_lines=context_lines,
    )


def lint_project(project: Path, *, state: int = SUPPORTED_STATE) -> LintReport:
    """Analyze one design state using only the structural design index."""
    if state != SUPPORTED_STATE:
        raise DesignLintError(
            f"design_lint v2 supports only State {SUPPORTED_STATE}, got State {state}"
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
    drafts = _duplicate_item_findings(index, selected_items)

    for item in decisions:
        drafts.extend(_duplicate_section_findings(item))
        drafts.extend(_canonical_section_findings(item))
        if not item["sections"]:
            drafts.append(
                _draft(
                    "warning",
                    "section_not_nested",
                    item,
                    "Decision has no indexed child sections; nest owned headings deeper than the decision heading.",
                )
            )
        if item["explicit_id"] is None:
            drafts.append(
                _draft(
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
            drafts.append(
                _draft(
                    "warning",
                    "unresolved_reference",
                    item,
                    f"Explicit reference {reference!r} does not resolve to an indexed item.",
                )
            )

    ordered_drafts = sorted(drafts, key=_finding_sort_key)
    ordered_findings = tuple(
        _enrich_finding(project, draft) for draft in ordered_drafts
    )
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


def render_human(report: LintReport, *, compact: bool = False) -> str:
    """Render deterministic diagnostics, with structural context by default."""
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
        lines.extend(
            [
                "",
                f"{finding.severity.upper()} {finding.code} - {finding.message}",
                f"  item: {finding.item_key}",
                f"  source: {finding.source.path}:{finding.source.line}",
            ]
        )
        if finding.section is not None:
            lines.append(f"  section: {finding.section}")
        if compact:
            continue
        lines.append(
            f"  item range: {finding.item_range.start_line}-{finding.item_range.end_line}"
        )
        lines.append(
            "  heading path: " + " > ".join(finding.heading_path)
        )
        lines.append("  sections:")
        if finding.section_outline:
            for section in finding.section_outline:
                lines.append(
                    f"    {'#' * section.level} {section.title} "
                    f"{section.start_line}-{section.end_line}"
                )
        else:
            lines.append("    (none indexed)")
        lines.append(
            f"  context {finding.context_range.start_line}-{finding.context_range.end_line}:"
        )
        lines.extend(f"    {line}" for line in finding.context_lines)
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
        help=f"Design state to lint (v2: only {SUPPORTED_STATE})",
    )
    parser.add_argument("--json", action="store_true", help="Emit stable JSON")
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Hide structural outline and source context in human output",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        report = lint_project(args.project, state=args.state)
    except DesignLintError as exc:
        print(f"design_lint: error: {exc}", file=sys.stderr)
        return 2
    output = (
        render_json(report)
        if args.json
        else render_human(report, compact=args.compact)
    )
    print(output, end="")
    return report_exit_code(report)


if __name__ == "__main__":
    raise SystemExit(main())
