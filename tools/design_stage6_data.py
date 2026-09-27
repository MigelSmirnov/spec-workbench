#!/usr/bin/env python3
"""Deterministic pre-contract structured-data closure workbench.

This compatibility tool predates the frozen authoring sequence and therefore
retains ``state6`` in its schema names and the ``60_data_closure.json`` filename.
It is not semantic State 6. Semantic State 6 is exact contracts and internal
functions; see skills/spec-authoring/AUTHORING_SEQUENCE.md.

The workbench places already accepted semantic facts into structured
specification homes before exact contracts and notes. It does not invent values.
Contract-dependent deterministic backend IR is post-State-6 authoring and is
forbidden here. Empty sections are valid when no accepted value belongs there yet.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from identity_workbench.sources import load_state1

# Compatibility identifiers: do not infer semantic state numbering from them.
SCHEMA = "spec_workbench_state6_data_closure.v1"
REPORT_SCHEMA = "spec_workbench_state6_data_lint.v2"
DEFAULT_FILE = "60_data_closure.json"
ALLOWED_SECTIONS = {"config", "rules", "persistence", "properties", "determinism"}
PERSISTENCE_CLASSES = {"master", "derived", "issued", "mirrored"}
DATA_CLOSURE_STATUSES = {"in_progress", "accepted", "closed"}
FINAL_DATA_CLOSURE_STATUSES = {"closed"}
CONTRACT_DEPENDENT_RULE_NAMESPACES = {"persistence_backend"}


def load(project: Path) -> dict[str, Any]:
    path = project / DEFAULT_FILE
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing {DEFAULT_FILE}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {DEFAULT_FILE}: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA:
        raise ValueError(f"unsupported compatibility data-closure schema; expected {SCHEMA!r}")
    return payload


def _lookup(root: Any, dotted: str) -> tuple[bool, Any]:
    cur = root
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return False, None
        cur = cur[part]
    return True, cur


DATA_PROVIDER_CLOSURE = "70_data_provider_closure.json"
# A scalar this long is a file name, an identifier or a profile, not a coincidence.
DISTINCTIVE_SCALAR_LENGTH = 12


def _data_nodes(prefix: str, value: Any):
    yield prefix, value
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(key, str):
                yield from _data_nodes(f"{prefix}.{key}", item)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _data_nodes(f"{prefix}[{index}]", item)


def _distinctive(value: Any) -> bool:
    if isinstance(value, (list, dict)):
        return len(value) >= 2
    return isinstance(value, str) and len(value) >= DISTINCTIVE_SCALAR_LENGTH


def _two_home_findings(project: Path, sections: Any) -> list[dict[str, Any]]:
    """SPEC_STANDARD 15.4: a leaf has one home.

    A value that generated code reads lives in a data-provider constant
    (SPEC_STANDARD 6.10). The same value left at a `rules` or `config` address is a
    second home: the two drift apart, and the address has no module consumer
    (SPEC_STANDARD 15.3), which stops Route B once that address changes. Only a
    distinctive value is judged - a structure of two or more entries or a long
    string - because short scalars do coincide.
    """
    path = project / DATA_PROVIDER_CLOSURE
    if not path.is_file() or not isinstance(sections, dict):
        return []
    try:
        closure = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    backend = closure.get("backend_ir") if isinstance(closure, dict) else None
    constants = backend.get("constants") if isinstance(backend, dict) else None
    if not isinstance(constants, dict):
        return []
    homes: dict[str, list[str]] = {}
    for root in ("rules", "config"):
        for address, value in _data_nodes(root, sections.get(root)):
            if address != root and _distinctive(value):
                homes.setdefault(json.dumps(value, sort_keys=True, ensure_ascii=False), []).append(address)
    findings: list[dict[str, Any]] = []
    for symbol, row in constants.items():
        value = row.get("value") if isinstance(row, dict) else None
        if not _distinctive(value):
            continue
        for address in homes.get(json.dumps(value, sort_keys=True, ensure_ascii=False), []):
            findings.append({
                "severity": "error",
                "code": "value_in_two_homes",
                "message": (
                    f"{address} holds the same value as data-provider constant {symbol}. SPEC_STANDARD 15.4: a leaf "
                    "has one home. Keep the constant and remove the value from the data closure, or remove the constant."
                ),
                "address": address,
                "symbol": symbol,
            })
    return findings


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

    rules = sections.get("rules", {})
    if isinstance(rules, dict):
        for namespace in sorted(CONTRACT_DEPENDENT_RULE_NAMESPACES & set(rules)):
            findings.append({
                "severity": "error",
                "code": "contract_dependent_backend_in_precontract_data",
                "message": (
                    f"rules.{namespace} depends on canonical State 6 contracts and must be authored "
                    "through the post-contract deterministic backend closure, not 60_data_closure.json"
                ),
            })

    persistence = sections.get("persistence", {})
    persistence_counts = {name: 0 for name in sorted(PERSISTENCE_CLASSES)}
    state1_identities, _ = load_state1(project)
    if isinstance(persistence, dict):
        for model_name, declaration in sorted(persistence.items()):
            if not isinstance(model_name, str) or not model_name:
                findings.append({"severity":"error","code":"invalid_persistence_model","message":"persistence model names must be non-empty strings"})
                continue
            if not isinstance(declaration, dict):
                findings.append({"severity":"error","code":"invalid_persistence_declaration","message":f"persistence.{model_name} must be an object"})
                continue
            persistence_class = declaration.get("class")
            if persistence_class not in PERSISTENCE_CLASSES:
                findings.append({"severity":"error","code":"invalid_persistence_class","message":f"persistence.{model_name}.class must be one of {sorted(PERSISTENCE_CLASSES)}"})
                continue
            persistence_counts[persistence_class] += 1
            identity_record = state1_identities.get(model_name)
            if identity_record is None:
                findings.append({
                    "severity": "error",
                    "code": "persistence_model_missing_identity",
                    "message": f"persistence.{model_name} refers to a model without canonical State 1 identity",
                })
            elif persistence_class in {"master", "mirrored"} and identity_record.identity != "entity":
                findings.append({
                    "severity": "error",
                    "code": "persistence_identity_incompatible",
                    "message": (
                        f"persistence.{model_name} class={persistence_class} requires identity entity; "
                        f"State 1 declares {identity_record.identity}"
                    ),
                })
            if persistence_class == "mirrored":
                remote = declaration.get("remote")
                if not isinstance(remote, str) or not remote.strip():
                    findings.append({"severity":"error","code":"missing_mirrored_remote","message":f"persistence.{model_name} class=mirrored requires non-empty remote"})

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
            findings.append({"severity":"error","code":"invalid_address_root","message":f"{address} is outside pre-contract structured sections"})
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

    findings.extend(_two_home_findings(project, sections))

    unresolved = payload.get("unresolved", [])
    if not isinstance(unresolved, list):
        findings.append({"severity":"error","code":"invalid_unresolved","message":"unresolved must be a list"})
        unresolved = []
    unresolved_topics = sorted({str(x.get("topic")) for x in unresolved if isinstance(x, dict) and x.get("topic")})

    status = payload.get("status")
    if status is not None and status not in DATA_CLOSURE_STATUSES:
        findings.append({
            "severity": "error",
            "code": "invalid_data_closure_status",
            "message": f"status must be one of {sorted(DATA_CLOSURE_STATUSES)} when present",
        })
    if status in FINAL_DATA_CLOSURE_STATUSES and unresolved:
        findings.append({
            "severity": "error",
            "code": "final_data_closure_has_unresolved",
            "message": (
                f"status={status!r} declares final structured-data closure but unresolved still contains "
                f"{len(unresolved)} item(s)"
            ),
        })

    return {
        "schema_version": REPORT_SCHEMA,
        "summary": {
            "status": status,
            "placements": len(placements),
            "structured_values": len(leaves),
            "persistence_models": len(persistence) if isinstance(persistence, dict) else 0,
            "persistence_classes": persistence_counts,
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
        print(f"Pre-contract data closure: {s['placements']} placements; {s['structured_values']} values; {s['persistence_models']} persistence models; {s['errors']} errors; {s['unresolved_topics']} unresolved topics")
        for finding in report["findings"]:
            print(f"{finding['severity'].upper()} {finding['code']} - {finding['message']}")
    return 1 if report["summary"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
