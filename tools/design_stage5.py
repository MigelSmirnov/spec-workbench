#!/usr/bin/env python3
"""Deterministic State 5 public-module-operation workbench.

State 5 freezes only cross-boundary public operations proven by reviewed State 4
flows. ``public_op:<module>.<name>`` denotes an operation owned by a project
module. Caller references are closed: ``module:<name>`` denotes an internal
project caller and ``boundary:<name>`` denotes an external/runtime boundary.
Deterministic HTTP exposure is designed later from accepted operations and
contracts; see ROUTER_IR_GUIDE.
"""
from __future__ import annotations

import fence

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import design_stage3
import design_stage4

SCHEMA_VERSION = "spec_workbench_state5.v2"
PLAN_SCHEMA = "spec_workbench_state5_plan.v1"
LINT_SCHEMA = "spec_workbench_state5_lint.v2"
COVERAGE_SCHEMA = "spec_workbench_state5_coverage.v2"
HANDOFF_SCHEMA = "spec_workbench_state5_handoff.v2"
DEFAULT_PLAN_FILE = "50_api_plan.json"
PUBLIC_OP_RE = re.compile(
    r"^`(?P<key>public_op:(?P<module>[a-z][a-z0-9_]*)\.(?P<name>[a-z][a-z0-9_]*))`$"
)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
STATE5_RE = re.compile(r"\bState\s+5\b", re.IGNORECASE)
MODULE_REF_RE = re.compile(r"`(module:[a-z][a-z0-9_]*)`")
BOUNDARY_REF_RE = re.compile(r"^boundary:[a-z][a-z0-9_]*$")
REQUIRED_SECTIONS = (
    "Owner", "Callers", "Inputs", "Outputs", "Observable effect",
    "Enforces", "Errors", "State impact",
)


class DesignStage5Error(Exception):
    pass


@dataclass(frozen=True)
class SourceRange:
    path: str
    start_line: int
    end_line: int


@dataclass(frozen=True)
class PublicOpItem:
    key: str
    module: str
    name: str
    source: SourceRange
    sections: tuple[str, ...]
    module_refs: tuple[str, ...]


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    operation_key: str
    message: str
    source: SourceRange


def _iter_state5_files(project: Path) -> Iterable[Path]:
    for path in sorted(project.rglob("*.md")):
        if not path.is_file():
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        if any(STATE5_RE.search(line) for line in lines[:40]):
            yield path


def _headings(lines: list[str]) -> list[tuple[int, int, str]]:
    result = []
    for number, line in enumerate(lines, start=1):
        match = HEADING_RE.match(line)
        if match:
            result.append((number, len(match.group(1)), match.group(2).strip()))
    return result


def parse_operations(project: Path) -> list[PublicOpItem]:
    project = project.resolve()
    result: list[PublicOpItem] = []
    for path in _iter_state5_files(project):
        lines = path.read_text(encoding="utf-8").splitlines()
        headings = _headings(lines)
        for index, (start, level, title) in enumerate(headings):
            if level != 2:
                continue
            match = PUBLIC_OP_RE.fullmatch(title)
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
            result.append(PublicOpItem(
                key=match.group("key"),
                module=match.group("module"),
                name=match.group("name"),
                source=SourceRange(path.relative_to(project).as_posix(), start, end),
                sections=child_titles,
                module_refs=tuple(sorted(set(MODULE_REF_RE.findall(body)))),
            ))
    return result


def parse_apis(project: Path) -> list[PublicOpItem]:
    """Backward-compatible Python helper name; payload keys use public operations."""
    return parse_operations(project)


def _payload(item: PublicOpItem) -> dict[str, object]:
    return asdict(item)


def _load_plan(project: Path, *, required: bool = False) -> dict[str, Any] | None:
    path = project / DEFAULT_PLAN_FILE
    if not path.is_file():
        if required:
            raise DesignStage5Error(f"State 5 public-operation plan not found: {path}")
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DesignStage5Error(f"State 5 public-operation plan could not be read: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != PLAN_SCHEMA:
        raise DesignStage5Error(f"unsupported State 5 plan schema; expected {PLAN_SCHEMA!r}")
    operations = payload.get("operations")
    if not isinstance(operations, list):
        raise DesignStage5Error("State 5 plan must contain a list named 'operations'")
    seen: set[str] = set()
    for index, entry in enumerate(operations):
        if not isinstance(entry, dict):
            raise DesignStage5Error(f"plan entry {index} must be an object")
        key = entry.get("key")
        capability = entry.get("capability")
        if not isinstance(key, str) or PUBLIC_OP_RE.fullmatch(f"`{key}`") is None:
            raise DesignStage5Error(f"plan entry {index} has invalid public operation key {key!r}")
        if key in seen:
            raise DesignStage5Error(f"duplicate planned public operation key: {key}")
        seen.add(key)
        expected_capability = "capability:" + key.removeprefix("public_op:")
        if capability != expected_capability:
            raise DesignStage5Error(
                f"planned operation {key} must map to matching State 3 capability {expected_capability!r}"
            )
        for field in ("flows", "callers"):
            value = entry.get(field)
            if not isinstance(value, list) or not value or not all(isinstance(v, str) for v in value):
                raise DesignStage5Error(f"planned operation {key} field {field!r} must be a non-empty string list")
        purpose = entry.get("purpose")
        if not isinstance(purpose, str) or not purpose.strip():
            raise DesignStage5Error(f"planned operation {key} requires a non-empty purpose")
    return payload


def manifest(project: Path) -> dict[str, object]:
    items = parse_operations(project)
    counts: dict[str, int] = {}
    for item in items:
        counts[item.key] = counts.get(item.key, 0) + 1
    return {
        "schema_version": SCHEMA_VERSION,
        "project_root": project.resolve().name,
        "operations": [_payload(item) for item in items],
        "diagnostics": {"duplicate_operation_keys": sorted(k for k, v in counts.items() if v > 1)},
    }


def get_operation(project: Path, key: str) -> dict[str, object] | None:
    normalized = key if key.startswith("public_op:") else f"public_op:{key}"
    for item in parse_operations(project):
        if item.key == normalized:
            return _payload(item)
    return None


def get_api(project: Path, key: str) -> dict[str, object] | None:
    return get_operation(project, key)


def coverage(project: Path) -> dict[str, object]:
    plan = _load_plan(project, required=True)
    actual = {item.key: item for item in parse_operations(project)}
    stage3 = design_stage3.handoff(project)
    stage4 = design_stage4.handoff(project)
    known_modules = {entry["key"] for entry in stage3["modules"]}
    known_capabilities = {entry["key"] for entry in stage3["capabilities"]}
    flows = {entry["key"]: entry for entry in stage4["flows"]}
    rows: list[dict[str, object]] = []
    invalid_refs: list[dict[str, str]] = []

    for entry in plan["operations"]:
        key = entry["key"]
        capability = entry["capability"]
        declared_flows = list(entry["flows"])
        callers = list(entry["callers"])
        invalid_callers: list[str] = []
        if capability not in known_capabilities:
            invalid_refs.append({"operation": key, "ref": capability, "kind": "capability"})
        for caller in callers:
            if caller.startswith("module:"):
                if caller not in known_modules:
                    invalid_refs.append({"operation": key, "ref": caller, "kind": "caller_module"})
                    invalid_callers.append(caller)
            elif BOUNDARY_REF_RE.fullmatch(caller) is None:
                invalid_refs.append({"operation": key, "ref": caller, "kind": "caller"})
                invalid_callers.append(caller)
        missing_flow_evidence: list[str] = []
        for flow_key in declared_flows:
            flow = flows.get(flow_key)
            if flow is None:
                invalid_refs.append({"operation": key, "ref": flow_key, "kind": "flow"})
                continue
            if capability not in set(flow["capability_refs"]):
                missing_flow_evidence.append(flow_key)
        item = actual.get(key)
        expected_owner = "module:" + key.removeprefix("public_op:").split(".", 1)[0]
        owner_missing = bool(item is not None and expected_owner not in set(item.module_refs))
        rows.append({
            "key": key,
            "capability": capability,
            "flows": declared_flows,
            "callers": callers,
            "invalid_callers": invalid_callers,
            "implemented": item is not None,
            "expected_owner": expected_owner,
            "owner_missing": owner_missing,
            "flow_evidence_missing": missing_flow_evidence,
        })

    planned = {entry["key"] for entry in plan["operations"]}
    unplanned = sorted(set(actual) - planned)
    complete = sum(
        1 for row in rows
        if row["implemented"]
        and not row["owner_missing"]
        and not row["flow_evidence_missing"]
        and not row["invalid_callers"]
    )
    return {
        "schema_version": COVERAGE_SCHEMA,
        "project_root": project.resolve().name,
        "summary": {
            "planned": len(rows),
            "implemented": sum(bool(row["implemented"]) for row in rows),
            "complete": complete,
            "remaining": len(rows) - complete,
            "invalid_refs": len(invalid_refs),
            "unplanned_operations": len(unplanned),
        },
        "operations": rows,
        "invalid_refs": invalid_refs,
        "unplanned_operations": unplanned,
    }


def next_operation(project: Path) -> dict[str, object]:
    report = coverage(project)
    for row in report["operations"]:
        if (
            not row["implemented"]
            or row["owner_missing"]
            or row["flow_evidence_missing"]
            or row["invalid_callers"]
        ):
            return {"schema_version": COVERAGE_SCHEMA, "project_root": project.resolve().name,
                    "complete": False, "next": row, "summary": report["summary"]}
    return {"schema_version": COVERAGE_SCHEMA, "project_root": project.resolve().name,
            "complete": True, "next": None, "summary": report["summary"]}


def next_api(project: Path) -> dict[str, object]:
    return next_operation(project)


def lint(project: Path) -> dict[str, object]:
    items = parse_operations(project)
    findings: list[Finding] = []
    counts: dict[str, int] = {}
    for item in items:
        counts[item.key] = counts.get(item.key, 0) + 1
    for item in items:
        if counts[item.key] > 1:
            findings.append(Finding("error", "duplicate_public_op_key", item.key, "Public operation key is not unique.", item.source))
        sections = {section.casefold() for section in item.sections}
        for required in REQUIRED_SECTIONS:
            if required.casefold() not in sections:
                findings.append(Finding("error", "missing_public_op_section", item.key,
                                        f"Required State 5 section {required!r} is absent.", item.source))
        expected_owner = "module:" + item.module
        if expected_owner not in set(item.module_refs):
            findings.append(Finding("error", "missing_public_op_owner", item.key,
                                    f"Owner section must explicitly reference {expected_owner!r}.", item.source))

    if _load_plan(project, required=False) is not None:
        report = coverage(project)
        for invalid in report["invalid_refs"]:
            if invalid["kind"] == "caller":
                message = (
                    f"Planned caller reference {invalid['ref']!r} is invalid; callers must use "
                    "module:<known_module> or boundary:<name>."
                )
            elif invalid["kind"] == "caller_module":
                message = f"Planned caller module reference {invalid['ref']!r} is not a known State 3 module."
            else:
                message = f"Planned {invalid['kind']} reference {invalid['ref']!r} is not valid State 3/4 evidence."
            findings.append(Finding(
                "error", "invalid_plan_ref", invalid["operation"], message,
                SourceRange(DEFAULT_PLAN_FILE, 1, 1),
            ))
        for row in report["operations"]:
            if row["flow_evidence_missing"]:
                findings.append(Finding("error", "missing_flow_evidence", row["key"],
                                        "Planned public operation capability is not explicitly used by every declared State 4 flow: "
                                        + ", ".join(row["flow_evidence_missing"]),
                                        SourceRange(DEFAULT_PLAN_FILE, 1, 1)))
        for key in report["unplanned_operations"]:
            item = next((candidate for candidate in items if candidate.key == key), None)
            if item is not None:
                findings.append(Finding("warning", "unplanned_public_op", key,
                                        "Public operation exists but is not declared in the explicit State 5 plan.", item.source))

    fenced_findings = fence.enforce([asdict(f) for f in findings])
    return {
        "schema_version": LINT_SCHEMA,
        "summary": {
            "operations": len(items),
            "errors": fence.stops(fenced_findings),
            "warnings": 0,
        },
        "findings": fenced_findings,
    }


def handoff(project: Path) -> dict[str, object]:
    report = lint(project)
    return {
        "schema_version": HANDOFF_SCHEMA,
        "project_root": project.resolve().name,
        "operations": [_payload(item) for item in parse_operations(project)],
        "coverage": coverage(project) if _load_plan(project, required=False) is not None else None,
        "lint_summary": report["summary"],
    }


def _render_human(report: dict[str, object]) -> str:
    summary = report["summary"]
    lines = [f"State 5: {summary['operations']} public operations; {summary['errors']} errors; {summary['warnings']} warnings"]
    for finding in report["findings"]:
        lines.append(f"{finding['severity'].upper()} {finding['code']} {finding['operation_key']} - {finding['message']}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--list", action="store_true")
    action.add_argument("--get", metavar="PUBLIC_OP_KEY")
    action.add_argument("--lint", action="store_true")
    action.add_argument("--coverage", action="store_true")
    action.add_argument("--next", action="store_true")
    action.add_argument("--handoff", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.project.is_dir():
        print(f"design_stage5: error: project directory not found: {args.project}", file=sys.stderr)
        return 2
    try:
        if args.get:
            payload = get_operation(args.project, args.get)
            if payload is None:
                print(f"design_stage5: error: unknown public operation: {args.get}", file=sys.stderr)
                return 1
        elif args.lint:
            payload = lint(args.project)
        elif args.coverage:
            payload = coverage(args.project)
        elif args.next:
            payload = next_operation(args.project)
        elif args.handoff:
            payload = handoff(args.project)
        elif args.list:
            payload = [_payload(item) for item in parse_operations(args.project)]
        else:
            payload = manifest(args.project)
    except DesignStage5Error as exc:
        print(f"design_stage5: error: {exc}", file=sys.stderr)
        return 2
    if args.lint and not args.json:
        print(_render_human(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    if args.lint and payload["summary"]["errors"]:
        return 1
    if args.coverage and (payload["summary"]["invalid_refs"] or payload["summary"]["remaining"]):
        return 1
    if args.handoff and payload["lint_summary"]["errors"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
