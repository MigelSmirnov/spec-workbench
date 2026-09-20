#!/usr/bin/env python3
"""Deterministic cross-state trace validation for spec-workbench.

The first supported transition is State 2 -> State 3. The tool deliberately does
not infer ownership from prose. A project supplies an explicit ``30_trace.json``
manifest that maps each State 2 decision to exactly one primary State 3 owner or
to an explicit non-runtime disposition. Optional consumers record secondary
module dependencies without confusing them with ownership.

The resulting handoff uses stable ``module:*`` and ``capability:*`` keys from
``design_stage3`` and is intended for later design states and future MCP use.
"""
from __future__ import annotations

import fence

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import design_index
import design_stage3

TRACE_SCHEMA = "spec_workbench_trace_2_3.v1"
REPORT_SCHEMA = "spec_workbench_trace_report_2_3.v1"
HANDOFF_SCHEMA = "spec_workbench_trace_handoff_2_3.v1"
DEFAULT_TRACE_FILE = "30_trace.json"
ALLOWED_DISPOSITIONS = {
    "cross_cutting",
    "deployment_process",
    "evidence_record",
    "external_owner",
}


class DesignTraceError(Exception):
    """Trace input could not be loaded or validated structurally."""


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    subject: str
    message: str


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise DesignTraceError(f"trace manifest could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise DesignTraceError(f"trace manifest is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise DesignTraceError("trace manifest root must be an object")
    return payload


def load_manifest(project: Path, trace_file: Path | None = None) -> dict[str, Any]:
    path = trace_file or (project / DEFAULT_TRACE_FILE)
    payload = _load_json(path)
    if payload.get("schema_version") != TRACE_SCHEMA:
        raise DesignTraceError(
            f"unsupported trace schema {payload.get('schema_version')!r}; expected {TRACE_SCHEMA!r}"
        )
    decisions = payload.get("decisions")
    if not isinstance(decisions, dict):
        raise DesignTraceError("trace manifest must contain an object named 'decisions'")
    return payload


def _state2_decisions(project: Path) -> dict[str, dict[str, Any]]:
    index = design_index.build_index(project)
    return {
        item["key"]: item
        for item in index["items"]
        if item["state"] == 2 and item["kind"] == "decision"
    }


def _module_keys(project: Path) -> set[str]:
    return {module["key"] for module in design_stage3.handoff(project)["modules"]}


def analyze(project: Path, trace_file: Path | None = None) -> dict[str, Any]:
    project = project.resolve()
    manifest = load_manifest(project, trace_file)
    actual = _state2_decisions(project)
    modules = _module_keys(project)
    findings: list[Finding] = []
    normalized: dict[str, dict[str, Any]] = {}

    for key, definition in manifest["decisions"].items():
        if key not in actual:
            findings.append(Finding("error", "unknown_state2_decision", key, "Trace entry does not resolve to a State 2 decision."))
        if not isinstance(definition, dict):
            findings.append(Finding("error", "invalid_trace_entry", key, "Trace entry must be an object."))
            continue

        owner = definition.get("primary_owner")
        disposition = definition.get("disposition")
        reason = definition.get("reason")
        consumers = definition.get("consumers", [])
        if not isinstance(consumers, list) or not all(isinstance(value, str) for value in consumers):
            findings.append(Finding("error", "invalid_consumers", key, "consumers must be a list of module keys."))
            consumers = []

        if (owner is None) == (disposition is None):
            findings.append(Finding("error", "owner_disposition_exclusive", key, "Exactly one of primary_owner or disposition is required."))
        if owner is not None:
            if not isinstance(owner, str) or owner not in modules:
                findings.append(Finding("error", "unknown_primary_owner", key, f"Primary owner {owner!r} is not a State 3 module."))
        if disposition is not None:
            if disposition not in ALLOWED_DISPOSITIONS:
                findings.append(Finding("error", "invalid_disposition", key, f"Disposition {disposition!r} is not allowed."))
            if not isinstance(reason, str) or not reason.strip():
                findings.append(Finding("error", "missing_disposition_reason", key, "A non-runtime disposition requires a non-empty reason."))

        bad_consumers = sorted({consumer for consumer in consumers if consumer not in modules})
        for consumer in bad_consumers:
            findings.append(Finding("error", "unknown_consumer", key, f"Consumer {consumer!r} is not a State 3 module."))
        if owner is not None and owner in consumers:
            findings.append(Finding("warning", "owner_repeated_as_consumer", key, "Primary owner is also listed as a consumer; remove the duplicate role."))

        normalized[key] = {
            "primary_owner": owner,
            "disposition": disposition,
            "reason": reason if disposition is not None else None,
            "consumers": sorted(set(consumers)),
        }

    unclaimed = sorted(set(actual) - set(manifest["decisions"]))
    for key in unclaimed:
        findings.append(Finding("error", "unclaimed_state2_decision", key, "State 2 decision has no primary owner or explicit disposition."))

    findings.sort(key=lambda finding: (finding.severity, finding.code, finding.subject, finding.message))
    fenced_findings = fence.enforce([asdict(finding) for finding in findings])
    return {
        "schema_version": REPORT_SCHEMA,
        "project_root": project.name,
        "summary": {
            "state2_decisions": len(actual),
            "trace_entries": len(manifest["decisions"]),
            "owned": sum(1 for value in normalized.values() if value["primary_owner"] is not None),
            "dispositioned": sum(1 for value in normalized.values() if value["disposition"] is not None),
            "unclaimed": len(unclaimed),
            "errors": fence.stops(fenced_findings),
            "warnings": 0,
        },
        "decisions": normalized,
        "unclaimed_state2_decisions": unclaimed,
        "findings": fenced_findings,
    }


def handoff(project: Path, trace_file: Path | None = None) -> dict[str, Any]:
    report = analyze(project, trace_file)
    stage3 = design_stage3.handoff(project)
    return {
        "schema_version": HANDOFF_SCHEMA,
        "project_root": project.resolve().name,
        "modules": stage3["modules"],
        "capabilities": stage3["capabilities"],
        "state2_trace": report["decisions"],
        "trace_summary": report["summary"],
    }


def _render_human(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "Trace 2->3: "
        f"{summary['state2_decisions']} decisions; {summary['owned']} owned; "
        f"{summary['dispositioned']} dispositioned; {summary['unclaimed']} unclaimed; "
        f"{summary['errors']} errors; {summary['warnings']} warnings"
    ]
    for finding in report["findings"]:
        lines.append(
            f"{finding['severity'].upper()} {finding['code']} {finding['subject']} - {finding['message']}"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--trace-file", type=Path)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--check", action="store_true", help="Validate State 2 -> State 3 trace coverage")
    action.add_argument("--handoff", action="store_true", help="Emit State 3 handoff enriched with backward trace")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if not args.project.is_dir():
        print(f"design_trace: error: project directory not found: {args.project}", file=sys.stderr)
        return 2
    try:
        if args.handoff:
            payload = handoff(args.project, args.trace_file)
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
            return 0 if payload["trace_summary"]["errors"] == 0 else 1
        report = analyze(args.project, args.trace_file)
    except DesignTraceError as exc:
        print(f"design_trace: error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(_render_human(report), end="")
    return 0 if report["summary"]["errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
