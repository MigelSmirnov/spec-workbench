#!/usr/bin/env python3
"""Deterministic State 6 data-closure workbench.

State 6 places already accepted semantic facts into structured specification
homes before exact contracts and notes. It does not invent values. Empty
sections are valid when no accepted value belongs there yet.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCHEMA = "spec_workbench_state6_data_closure.v1"
REPORT_SCHEMA = "spec_workbench_state6_data_lint.v1"
DEFAULT_FILE = "60_data_closure.json"
ALLOWED_SECTIONS = {"config", "rules", "persistence", "properties", "determinism"}


def load(project: Path) -> dict[str, Any]:
    path = project / DEFAULT_FILE
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing {DEFAULT_FILE}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {DEFAULT_FILE}: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA:
        raise ValueError(f"unsupported State 6 schema; expected {SCHEMA!r}")
    return payload


def _lookup(root: Any, dotted: str) -> tuple[bool, Any]:
    cur = root
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return False, None
        cur = cur[part]
    return True, cur


def lint(project: Path) -> dict[str, Any]:
    payload = load(project)
    findings: list[dict[str, str]] = []
    sections = payload.get("sections")
    if not isinstance(sections, dict):
        findings.append({"severity":"error","code":"invalid_sections","message":"sections must be an object"})
        sections = {}
    unknown = sorted(set(sections) - ALLOWED_SECTIONS)
    for key in unknown:
        findings.append({"severity":"error","code":"unknown_data_section","message":f"unknown structured data section: {key}"})
    for key in ALLOWED_SECTIONS:
        if key not in sections:
            findings.append({"severity":"error","code":"missing_data_section","message":f"missing structured data section: {key}"})
        elif not isinstance(sections[key], dict):
            findings.append({"severity":"error","code":"invalid_data_section","message":f"section {key} must be an object"})

    placements = payload.get("placements")
    if not isinstance(placements, list):
        findings.append({"severity":"error","code":"invalid_placements","message":"placements must be a list"})
        placements = []
    seen: set[str] = set()
    for index, entry in enumerate(placements):
        if not isinstance(entry, dict):
            findings.append({"severity":"error","code":"invalid_placement","message":f"placement {index} must be an object"})
            continue
        address = entry.get("address")
        refs = entry.get("source_refs")
        reason = entry.get("reason")
        if not isinstance(address, str) or "." not in address:
            findings.append({"severity":"error","code":"invalid_address","message":f"placement {index} has invalid address"})
            continue
        root = address.split(".", 1)[0]
        if root not in ALLOWED_SECTIONS:
            findings.append({"severity":"error","code":"invalid_address_root","message":f"{address} is outside State 6 structured sections"})
        if address in seen:
            findings.append({"severity":"error","code":"duplicate_address","message":f"duplicate placement address: {address}"})
        seen.add(address)
        exists, _ = _lookup(sections, address)
        if not exists:
            findings.append({"severity":"error","code":"missing_placed_value","message":f"placement address has no structured value: {address}"})
        if not isinstance(refs, list) or not refs or not all(isinstance(v, str) and v.strip() for v in refs):
            findings.append({"severity":"error","code":"missing_source_evidence","message":f"{address} requires non-empty source_refs"})
        if not isinstance(reason, str) or not reason.strip():
            findings.append({"severity":"error","code":"missing_placement_reason","message":f"{address} requires a placement reason"})

    # Fail closed on structured values that have no placement evidence.
    leaves: list[str] = []
    def walk(prefix: str, value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                walk(f"{prefix}.{key}" if prefix else key, child)
        else:
            leaves.append(prefix)
    for section in sorted(ALLOWED_SECTIONS):
        if isinstance(sections.get(section), dict):
            walk(section, sections[section])
    for address in sorted(set(leaves) - seen):
        findings.append({"severity":"error","code":"untraced_structured_value","message":f"structured value lacks placement evidence: {address}"})

    unresolved = payload.get("unresolved", [])
    if not isinstance(unresolved, list):
        findings.append({"severity":"error","code":"invalid_unresolved","message":"unresolved must be a list"})
        unresolved = []
    unresolved_topics = sorted({str(x.get("topic")) for x in unresolved if isinstance(x, dict) and x.get("topic")})
    return {
        "schema_version": REPORT_SCHEMA,
        "summary": {
            "placements": len(placements),
            "structured_values": len(leaves),
            "errors": sum(f["severity"] == "error" for f in findings),
            "unresolved_topics": len(unresolved_topics),
        },
        "unresolved_topics": unresolved_topics,
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--lint", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.project.is_dir():
        print(f"design_stage6_data: error: project directory not found: {args.project}", file=sys.stderr)
        return 2
    try:
        report = lint(args.project)
    except ValueError as exc:
        print(f"design_stage6_data: error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        s = report["summary"]
        print(f"State 6 data: {s['placements']} placements; {s['structured_values']} values; {s['errors']} errors; {s['unresolved_topics']} unresolved topics")
        for finding in report["findings"]:
            print(f"{finding['severity'].upper()} {finding['code']} - {finding['message']}")
    return 1 if report["summary"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
