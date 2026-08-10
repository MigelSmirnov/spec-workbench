#!/usr/bin/env python3
"""Deterministic State 4 flow structure, lint, and handoff.

State 4 records reviewed end-to-end flows. This tool does not infer flow order,
ownership, or contracts from prose. It exposes stable ``flow:<name>`` keys and
validates explicit ``module:*`` / ``capability:*`` references against State 3.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import design_stage3

SCHEMA_VERSION = "spec_workbench_state4.v1"
HANDOFF_SCHEMA = "spec_workbench_state4_handoff.v1"
LINT_SCHEMA = "spec_workbench_state4_lint.v1"
FLOW_RE = re.compile(r"^`flow:(?P<name>[a-z][a-z0-9_]*)`$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
STATE4_RE = re.compile(r"\bState\s+4\b", re.IGNORECASE)
MODULE_REF_RE = re.compile(r"`(module:[a-z][a-z0-9_]*)`")
CAPABILITY_REF_RE = re.compile(r"`(capability:[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*)`")
REQUIRED_SECTIONS = ("Trigger", "Boundary", "Steps", "Outcomes", "Errors")


@dataclass(frozen=True)
class SourceRange:
    path: str
    start_line: int
    end_line: int


@dataclass(frozen=True)
class FlowItem:
    key: str
    name: str
    source: SourceRange
    sections: tuple[str, ...]
    module_refs: tuple[str, ...]
    capability_refs: tuple[str, ...]


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    flow_key: str
    message: str
    source: SourceRange


def _iter_state4_files(project: Path) -> Iterable[Path]:
    for path in sorted(project.rglob("*.md")):
        if not path.is_file():
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        if any(STATE4_RE.search(line) for line in lines[:40]):
            yield path


def _headings(lines: list[str]) -> list[tuple[int, int, str]]:
    result = []
    for number, line in enumerate(lines, start=1):
        match = HEADING_RE.match(line)
        if match:
            result.append((number, len(match.group(1)), match.group(2).strip()))
    return result


def parse_flows(project: Path) -> list[FlowItem]:
    project = project.resolve()
    result: list[FlowItem] = []
    for path in _iter_state4_files(project):
        lines = path.read_text(encoding="utf-8").splitlines()
        headings = _headings(lines)
        for index, (start, level, title) in enumerate(headings):
            if level != 2:
                continue
            match = FLOW_RE.fullmatch(title)
            if match is None:
                continue
            end = len(lines)
            for next_start, next_level, _ in headings[index + 1:]:
                if next_level <= level:
                    end = next_start - 1
                    break
            body = "\n".join(lines[start - 1:end])
            child_titles = tuple(
                child_title
                for child_start, child_level, child_title in headings[index + 1:]
                if start < child_start <= end and child_level > level
            )
            name = match.group("name")
            result.append(FlowItem(
                key=f"flow:{name}",
                name=name,
                source=SourceRange(path.relative_to(project).as_posix(), start, end),
                sections=child_titles,
                module_refs=tuple(sorted(set(MODULE_REF_RE.findall(body)))),
                capability_refs=tuple(sorted(set(CAPABILITY_REF_RE.findall(body)))),
            ))
    return result


def _payload(flow: FlowItem) -> dict[str, object]:
    return asdict(flow)


def manifest(project: Path) -> dict[str, object]:
    flows = parse_flows(project)
    counts: dict[str, int] = {}
    for flow in flows:
        counts[flow.key] = counts.get(flow.key, 0) + 1
    return {
        "schema_version": SCHEMA_VERSION,
        "project_root": project.resolve().name,
        "flows": [_payload(flow) for flow in flows],
        "diagnostics": {"duplicate_flow_keys": sorted(k for k, v in counts.items() if v > 1)},
    }


def get_flow(project: Path, key: str) -> dict[str, object] | None:
    normalized = key if key.startswith("flow:") else f"flow:{key}"
    for flow in parse_flows(project):
        if flow.key == normalized:
            return _payload(flow)
    return None


def lint(project: Path) -> dict[str, object]:
    flows = parse_flows(project)
    stage3 = design_stage3.handoff(project)
    modules = {entry["key"] for entry in stage3["modules"]}
    capabilities = {entry["key"] for entry in stage3["capabilities"]}
    findings: list[Finding] = []
    counts: dict[str, int] = {}
    for flow in flows:
        counts[flow.key] = counts.get(flow.key, 0) + 1
    for flow in flows:
        sections = {title.casefold() for title in flow.sections}
        if counts[flow.key] > 1:
            findings.append(Finding("error", "duplicate_flow_key", flow.key, "Flow key is not unique.", flow.source))
        for required in REQUIRED_SECTIONS:
            if required.casefold() not in sections:
                findings.append(Finding("error", "missing_flow_section", flow.key, f"Required State 4 section {required!r} is absent.", flow.source))
        if not flow.module_refs:
            findings.append(Finding("error", "missing_module_refs", flow.key, "Flow must name at least one explicit State 3 module reference.", flow.source))
        for ref in flow.module_refs:
            if ref not in modules:
                findings.append(Finding("error", "unknown_module_ref", flow.key, f"Unknown State 3 module reference {ref!r}.", flow.source))
        for ref in flow.capability_refs:
            if ref not in capabilities:
                findings.append(Finding("error", "unknown_capability_ref", flow.key, f"Unknown State 3 capability reference {ref!r}.", flow.source))
    return {
        "schema_version": LINT_SCHEMA,
        "summary": {
            "flows": len(flows),
            "errors": sum(f.severity == "error" for f in findings),
            "warnings": sum(f.severity == "warning" for f in findings),
        },
        "findings": [asdict(f) for f in findings],
    }


def handoff(project: Path) -> dict[str, object]:
    report = lint(project)
    return {
        "schema_version": HANDOFF_SCHEMA,
        "project_root": project.resolve().name,
        "flows": [_payload(flow) for flow in parse_flows(project)],
        "lint_summary": report["summary"],
    }


def _render_human(report: dict[str, object]) -> str:
    summary = report["summary"]
    lines = [f"State 4: {summary['flows']} flows; {summary['errors']} errors; {summary['warnings']} warnings"]
    for finding in report["findings"]:
        lines.append(f"{finding['severity'].upper()} {finding['code']} {finding['flow_key']} - {finding['message']}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--list", action="store_true")
    action.add_argument("--get", metavar="FLOW_KEY")
    action.add_argument("--lint", action="store_true")
    action.add_argument("--handoff", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.project.is_dir():
        print(f"design_stage4: error: project directory not found: {args.project}", file=sys.stderr)
        return 2
    if args.get:
        payload = get_flow(args.project, args.get)
        if payload is None:
            print(f"design_stage4: error: unknown flow: {args.get}", file=sys.stderr)
            return 1
    elif args.lint:
        payload = lint(args.project)
    elif args.handoff:
        payload = handoff(args.project)
    elif args.list:
        payload = [_payload(flow) for flow in parse_flows(args.project)]
    else:
        payload = manifest(args.project)
    if args.lint and not args.json:
        print(_render_human(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    if args.lint and payload["summary"]["errors"]:
        return 1
    if args.handoff and payload["lint_summary"]["errors"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
