#!/usr/bin/env python3
"""Deterministic State 4 flow workbench, lint, coverage, and handoff.

State 4 records reviewed end-to-end flows. The workbench does not invent flow
order, ownership, contracts, modules, or capabilities from prose. Projects may
supply an explicit ``40_flow_plan.json`` that lists operator-accepted flow needs.
The tool then reports coverage and the next missing flow without authoring it.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import design_stage3

SCHEMA_VERSION = "spec_workbench_state4.v2"
HANDOFF_SCHEMA = "spec_workbench_state4_handoff.v2"
LINT_SCHEMA = "spec_workbench_state4_lint.v2"
PLAN_SCHEMA = "spec_workbench_state4_plan.v1"
COVERAGE_SCHEMA = "spec_workbench_state4_coverage.v1"
DEFAULT_PLAN_FILE = "40_flow_plan.json"
FLOW_RE = re.compile(r"^`flow:(?P<name>[a-z][a-z0-9_]*)`$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
STATE4_RE = re.compile(r"\bState\s+4\b", re.IGNORECASE)
MODULE_REF_RE = re.compile(r"`(module:[a-z][a-z0-9_]*)`")
CAPABILITY_REF_RE = re.compile(r"`(capability:[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*)`")
REQUIRED_SECTIONS = ("Trigger", "Boundary", "Steps", "Outcomes", "Errors")


class DesignStage4Error(Exception):
    """State 4 project input is structurally invalid."""


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


def _load_plan(project: Path, *, required: bool = False) -> dict[str, Any] | None:
    path = project / DEFAULT_PLAN_FILE
    if not path.is_file():
        if required:
            raise DesignStage4Error(f"State 4 flow plan not found: {path}")
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DesignStage4Error(f"State 4 flow plan could not be read: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != PLAN_SCHEMA:
        raise DesignStage4Error(f"unsupported State 4 flow plan schema; expected {PLAN_SCHEMA!r}")
    flows = payload.get("flows")
    if not isinstance(flows, list):
        raise DesignStage4Error("State 4 flow plan must contain a list named 'flows'")
    seen: set[str] = set()
    for index, entry in enumerate(flows):
        if not isinstance(entry, dict):
            raise DesignStage4Error(f"flow plan entry {index} must be an object")
        key = entry.get("key")
        if not isinstance(key, str) or FLOW_RE.fullmatch(f"`{key}`") is None:
            raise DesignStage4Error(f"flow plan entry {index} has invalid key {key!r}")
        if key in seen:
            raise DesignStage4Error(f"duplicate planned flow key: {key}")
        seen.add(key)
        purpose = entry.get("purpose")
        if not isinstance(purpose, str) or not purpose.strip():
            raise DesignStage4Error(f"planned flow {key} requires a non-empty purpose")
        for field in ("required_modules", "candidate_capabilities"):
            value = entry.get(field, [])
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                raise DesignStage4Error(f"planned flow {key} field {field!r} must be a string list")
    return payload


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


def coverage(project: Path) -> dict[str, object]:
    plan = _load_plan(project, required=True)
    actual = {flow.key: flow for flow in parse_flows(project)}
    stage3 = design_stage3.handoff(project)
    known_modules = {entry["key"] for entry in stage3["modules"]}
    known_capabilities = {entry["key"] for entry in stage3["capabilities"]}
    rows: list[dict[str, object]] = []
    invalid_plan_refs: list[dict[str, str]] = []
    for entry in plan["flows"]:
        key = entry["key"]
        required_modules = list(entry.get("required_modules", []))
        candidate_capabilities = list(entry.get("candidate_capabilities", []))
        for ref in required_modules:
            if ref not in known_modules:
                invalid_plan_refs.append({"flow": key, "ref": ref, "kind": "module"})
        for ref in candidate_capabilities:
            if ref not in known_capabilities:
                invalid_plan_refs.append({"flow": key, "ref": ref, "kind": "capability"})
        flow = actual.get(key)
        rows.append({
            "key": key,
            "purpose": entry["purpose"],
            "implemented": flow is not None,
            "required_modules": required_modules,
            "candidate_capabilities": candidate_capabilities,
            "missing_required_modules": sorted(set(required_modules) - set(flow.module_refs if flow else ())),
            "missing_candidate_capabilities": sorted(set(candidate_capabilities) - set(flow.capability_refs if flow else ())),
        })
    planned_keys = {entry["key"] for entry in plan["flows"]}
    unplanned = sorted(set(actual) - planned_keys)
    complete = sum(1 for row in rows if row["implemented"] and not row["missing_required_modules"] and not row["missing_candidate_capabilities"])
    return {
        "schema_version": COVERAGE_SCHEMA,
        "project_root": project.resolve().name,
        "summary": {
            "planned": len(rows),
            "implemented": sum(bool(row["implemented"]) for row in rows),
            "complete": complete,
            "remaining": len(rows) - complete,
            "invalid_plan_refs": len(invalid_plan_refs),
            "unplanned_flows": len(unplanned),
        },
        "flows": rows,
        "invalid_plan_refs": invalid_plan_refs,
        "unplanned_flows": unplanned,
    }


def next_flow(project: Path) -> dict[str, object]:
    report = coverage(project)
    for row in report["flows"]:
        if not row["implemented"] or row["missing_required_modules"] or row["missing_candidate_capabilities"]:
            return {
                "schema_version": COVERAGE_SCHEMA,
                "project_root": project.resolve().name,
                "complete": False,
                "next": row,
                "summary": report["summary"],
            }
    return {
        "schema_version": COVERAGE_SCHEMA,
        "project_root": project.resolve().name,
        "complete": True,
        "next": None,
        "summary": report["summary"],
    }


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
    plan = _load_plan(project, required=False)
    if plan is not None:
        coverage_report = coverage(project)
        for invalid in coverage_report["invalid_plan_refs"]:
            source = SourceRange(DEFAULT_PLAN_FILE, 1, 1)
            findings.append(Finding("error", "invalid_plan_ref", invalid["flow"], f"Planned {invalid['kind']} reference {invalid['ref']!r} does not exist in State 3.", source))
        for key in coverage_report["unplanned_flows"]:
            flow = next((item for item in flows if item.key == key), None)
            if flow is not None:
                findings.append(Finding("warning", "unplanned_flow", key, "Flow exists but is not declared in the explicit State 4 flow plan.", flow.source))
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
    plan = _load_plan(project, required=False)
    return {
        "schema_version": HANDOFF_SCHEMA,
        "project_root": project.resolve().name,
        "flows": [_payload(flow) for flow in parse_flows(project)],
        "coverage": coverage(project) if plan is not None else None,
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
    action.add_argument("--coverage", action="store_true")
    action.add_argument("--next", action="store_true")
    action.add_argument("--handoff", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.project.is_dir():
        print(f"design_stage4: error: project directory not found: {args.project}", file=sys.stderr)
        return 2
    try:
        if args.get:
            payload = get_flow(args.project, args.get)
            if payload is None:
                print(f"design_stage4: error: unknown flow: {args.get}", file=sys.stderr)
                return 1
        elif args.lint:
            payload = lint(args.project)
        elif args.coverage:
            payload = coverage(args.project)
        elif args.next:
            payload = next_flow(args.project)
        elif args.handoff:
            payload = handoff(args.project)
        elif args.list:
            payload = [_payload(flow) for flow in parse_flows(args.project)]
        else:
            payload = manifest(args.project)
    except DesignStage4Error as exc:
        print(f"design_stage4: error: {exc}", file=sys.stderr)
        return 2
    if args.lint and not args.json:
        print(_render_human(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    if args.lint and payload["summary"]["errors"]:
        return 1
    if args.coverage and (payload["summary"]["invalid_plan_refs"] or payload["summary"]["remaining"]):
        return 1
    if args.handoff and payload["lint_summary"]["errors"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
