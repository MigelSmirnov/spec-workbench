#!/usr/bin/env python3
"""Witness resolution for accepted-decision required tests.

An accepted decision can declare formal invariants that no gate ever
enforces: A05/A07 demanded a bounded streaming download while a fully
buffering implementation passed every closure gate, because "do not buffer"
is not a name and name-closure cannot see it. The invariant lived in State 2
as prose; nothing addressable carried it.

The repair is the house move: make the declaration addressable, then close
names. A Required tests item may carry a witness tag:

    1. Large downloads stream and stay memory-bounded.
       [witness: verification:streaming_source_download_behavior]
    2. Upload without an active handoff is rejected.
       [witness: note:store_original_source]

`verification:<name>` resolves against the factory project's verification
config (the named focused command-check must exist); `note:<scope>` resolves
against the assembled specification (the scope must carry a [TEST_EVIDENCE]
note). A tag that resolves is a mechanical witness; a tag that does not is an
error — a claimed witness that is absent is worse than no claim. A decision
with formal invariants and no witness at all is reported as a warning, not a
block: the corpus adopts tags decision by decision, and adequacy of a witness
to its invariant stays a human judgement.

    python tools/design_decision_witness.py examples/<case> --coverage [--json]
"""
from __future__ import annotations

import argparse
import fence
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import design_index

try:
    import yaml
except ImportError:  # pragma: no cover - pyyaml is a workbench dependency
    yaml = None

SCHEMA_VERSION = "spec_workbench_decision_witness.v1"
FACTORY_ROOT_ENV = "SPEC_WORKBENCH_FACTORY_ROOT"
FACTORY_TARGET_FILE = "90_factory_target.json"
ASSEMBLED_SPEC_FILE = "global_spec.json"
WITNESS_RE = re.compile(r"\[witness:\s*(verification|note):([A-Za-z0-9_.\-]+)\]")
NOTE_SCOPE_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*:")


def factory_root(workbench_root: Path) -> Path:
    override = os.environ.get(FACTORY_ROOT_ENV)
    return Path(override) if override else workbench_root.parent / "code_factory"


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _verification_check_names(case: Path, factory: Path) -> set[str] | None:
    """Focused command-check names of the target factory project; None = unverifiable."""
    if yaml is None:
        return None
    target = _load_json(case / FACTORY_TARGET_FILE)
    project = target.get("factory_project")
    if not isinstance(project, str) or not project:
        return None
    config_path = factory / "verification" / "configs" / f"{project}.yaml"
    try:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    commands = ((config or {}).get("checks") or {}).get("commands") or []
    return {str(item.get("name")) for item in commands if isinstance(item, dict) and item.get("name")}


def _test_evidence_scopes(case: Path) -> set[str] | None:
    spec = _load_json(case / ASSEMBLED_SPEC_FILE)
    if not spec:
        return None
    scopes: set[str] = set()
    for note in spec.get("notes") or []:
        text = str(note)
        if "[TEST_EVIDENCE]" not in text:
            continue
        match = NOTE_SCOPE_RE.match(text)
        if match:
            scopes.add(match.group(1))
            scopes.add(match.group(1).split(".", 1)[0])
    return scopes


def _section_lines(case: Path, item: dict[str, Any], title: str) -> tuple[str, str] | None:
    """(location, text) of one canonical section of an indexed decision."""
    source = item.get("source") or {}
    path = case / str(source.get("path") or "")
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for section in item.get("sections") or []:
        if str(section.get("title", "")).casefold() == title.casefold():
            start = int(section.get("start_line") or 0)
            end = min(len(lines), int(section.get("end_line") or start))
            return f"{source.get('path')}:{start}", "\n".join(lines[start - 1:end])
    return None


def coverage(case: Path, factory: Path | None = None) -> dict[str, Any]:
    case = case.resolve()
    if factory is None:
        factory = factory_root(Path(__file__).resolve().parents[1])
    check_names = _verification_check_names(case, factory)
    evidence_scopes = _test_evidence_scopes(case)

    findings: list[dict[str, Any]] = []
    decisions = 0
    witnessed = 0
    for item in design_index.list_items(case, kind="decision"):
        invariants = _section_lines(case, item, "Formal invariant(s)") or _section_lines(case, item, "Formal invariants")
        tests = _section_lines(case, item, "Required tests")
        if invariants is None or not invariants[1].strip():
            continue
        decisions += 1
        tags = WITNESS_RE.findall(tests[1]) if tests else []
        location = (tests or invariants)[0]
        if not tags:
            findings.append({
                "severity": "warning", "code": "decision_without_witness",
                "decision": item.get("key"), "location": location,
                "message": (f"{item.get('key')}: formal invariants declared, no witness tag in "
                            "Required tests — nothing mechanical enforces this decision"),
            })
            continue
        resolved_any = False
        for kind, name in tags:
            if kind == "verification":
                if check_names is None:
                    findings.append({
                        "severity": "warning", "code": "witness_unverifiable",
                        "decision": item.get("key"), "witness": f"{kind}:{name}", "location": location,
                        "message": f"{item.get('key')}: factory verification config unavailable; "
                                   f"witness {name} will be judged at factory admission",
                    })
                    resolved_any = True
                elif name in check_names:
                    resolved_any = True
                else:
                    findings.append({
                        "severity": "error", "code": "witness_unresolved",
                        "decision": item.get("key"), "witness": f"{kind}:{name}", "location": location,
                        "message": (f"{item.get('key')}: claims verification check {name!r} that the "
                                    "factory config does not define — a claimed witness that is "
                                    "absent is worse than no claim"),
                    })
            else:
                if evidence_scopes is None:
                    findings.append({
                        "severity": "warning", "code": "witness_unverifiable",
                        "decision": item.get("key"), "witness": f"{kind}:{name}", "location": location,
                        "message": f"{item.get('key')}: no assembled specification yet; "
                                   f"note witness {name} unverifiable before assembly",
                    })
                    resolved_any = True
                elif name in evidence_scopes:
                    resolved_any = True
                else:
                    findings.append({
                        "severity": "error", "code": "witness_unresolved",
                        "decision": item.get("key"), "witness": f"{kind}:{name}", "location": location,
                        "message": (f"{item.get('key')}: claims a [TEST_EVIDENCE] note at scope "
                                    f"{name!r} that the assembled specification does not carry"),
                    })
        if resolved_any:
            witnessed += 1

    errors = sum(1 for f in findings if f["severity"] == "error")
    findings = fence.enforce(findings)
    errors = fence.stops(findings)
    return {
        "schema_version": SCHEMA_VERSION,
        "project_root": case.name,
        "summary": {
            "decisions_with_invariants": decisions,
            "witnessed": witnessed,
            "unwitnessed": decisions - witnessed,
            "errors": errors,
            "handoff_ready": errors == 0,
        },
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--coverage", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--factory-root", type=Path)
    args = parser.parse_args(argv)
    if not args.project.is_dir():
        print(f"design_decision_witness: error: project directory not found: {args.project}", file=sys.stderr)
        return 2
    report = coverage(args.project, args.factory_root)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        summary = report["summary"]
        print(f"Decision witnesses: {summary['witnessed']}/{summary['decisions_with_invariants']} witnessed; "
              f"{summary['errors']} unresolved; handoff_ready={str(summary['handoff_ready']).lower()}")
        for finding in report["findings"]:
            print(f"  {'✗' if finding['severity'] == 'error' else '!'} {finding['message']}")
    return 1 if report["summary"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
