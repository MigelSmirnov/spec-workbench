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
with formal invariants and no witness at all stops the case (the fence raises
its warning). A tag binds the invariant identifiers its own line names, so
one check cannot stand for a decision's other invariants; whether the check
really asserts the invariant stays a judgement of the State 2 question round.

Two things are kept apart (TRANSITION_PROTOCOL.md, "Invariant evidence"): the
Required tests item that describes what must be shown — a State 2 decision,
checked at the State 2 handoff by ``required_tests`` — and the binding of that
description to an existing check, confirmed here. Neither is the reviewer's
defect witness of a question round, which shows a history in which the texts
give two outcomes.

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
except ImportError:  # the MCP venv once lacked it and every check read "unavailable"
    yaml = None

SCHEMA_VERSION = "spec_workbench_decision_witness.v1"
FACTORY_ROOT_ENV = "SPEC_WORKBENCH_FACTORY_ROOT"
FACTORY_TARGET_FILE = "90_factory_target.json"
ASSEMBLED_SPEC_FILE = "global_spec.json"
# Authoring-sequence phases that block on deterministic design_lint findings
# (design_authoring_next): State 1 models, State 2 decisions and the State 2
# security review. A decision whose invariant is one of these gates is
# witnessed by the gate itself.
LINT_GATES = ("state1_models", "state2_rules_decisions")
WITNESS_RE = re.compile(r"\[witness:\s*(verification|note|workbench):([A-Za-z0-9_.\-]+)\]")
NOTE_SCOPE_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*:")


def factory_root(workbench_root: Path) -> Path:
    override = os.environ.get(FACTORY_ROOT_ENV)
    if override:
        return Path(override)
    # the canonical checkout sits beside the workbench; a worktree sits one level deeper
    for candidate in (workbench_root.parent / "code_factory", workbench_root.parent.parent / "code_factory"):
        if (candidate / "verification").is_dir():
            return candidate
    return workbench_root.parent / "code_factory"


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _verification_check_names(case: Path, factory: Path) -> tuple[set[str] | None, str]:
    """Focused command-check names of the target factory project, or None and why they are unverifiable."""
    if yaml is None:
        return None, f"PyYAML is not installed for {sys.executable}"
    target = _load_json(case / FACTORY_TARGET_FILE)
    project = target.get("factory_project")
    if not isinstance(project, str) or not project:
        return None, f"{FACTORY_TARGET_FILE} names no factory_project"
    config_path = factory / "verification" / "configs" / f"{project}.yaml"
    try:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except OSError:
        return None, f"{config_path} is not readable (set {FACTORY_ROOT_ENV} to the factory checkout)"
    except yaml.YAMLError:
        return None, f"{config_path} is not valid YAML"
    commands = ((config or {}).get("checks") or {}).get("commands") or []
    return {str(item.get("name")) for item in commands if isinstance(item, dict) and item.get("name")}, ""


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


INVARIANT_ID_RE = re.compile(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d{1,4}\b")


def invariant_ids(text: str) -> list[str]:
    """The identifiers formal invariants are written under (INV-031, PLAT-REG-003), in order."""
    return list(dict.fromkeys(INVARIANT_ID_RE.findall(text)))


def _workbench_checks() -> set[str]:
    try:
        from assembly_workbench.model import CHECK_ORDER
        checks = set(CHECK_ORDER)
    except ImportError:  # pragma: no cover
        checks = set()
    return checks | set(LINT_GATES)


def _resolve(kind: str, name: str, key: Any, location: str, check_names: set[str] | None, unavailable: str,
             evidence_scopes: set[str] | None) -> tuple[bool, dict[str, Any] | None]:
    """Whether one tag binds to an existing check, and the finding when it does not or cannot be told."""
    if kind == "workbench":
        # a decision the workbench itself enforces: on every assembly (identity, flows …)
        # or as a design_lint gate of the authoring sequence (State 1/2, security review)
        if name in _workbench_checks():
            return True, None
        return False, {"severity": "error", "code": "witness_unresolved", "decision": key,
                       "witness": f"{kind}:{name}", "location": location,
                       "message": (f"{key}: claims workbench check {name!r} that the assembly nor the authoring "
                                   "sequence runs — a claimed witness that is absent is worse than no claim")}
    if kind == "verification":
        if check_names is None:
            return True, {"severity": "warning", "code": "witness_unverifiable", "outcome": "not_checked",
                          "decision": key, "witness": f"{kind}:{name}", "location": location,
                          "message": f"{key}: factory verification config unavailable ({unavailable}); "
                                     f"witness {name} is not checked — not checked is not a pass"}
        if name in check_names:
            return True, None
        return False, {"severity": "error", "code": "witness_unresolved", "decision": key,
                       "witness": f"{kind}:{name}", "location": location,
                       "message": (f"{key}: claims verification check {name!r} that the factory config does not "
                                   "define — a claimed witness that is absent is worse than no claim")}
    if evidence_scopes is None:
        return True, {"severity": "warning", "code": "witness_unverifiable", "outcome": "not_checked",
                      "decision": key, "witness": f"{kind}:{name}", "location": location,
                      "message": f"{key}: no assembled specification yet; note witness {name} is not checked "
                                 "before assembly"}
    if name in evidence_scopes:
        return True, None
    return False, {"severity": "error", "code": "witness_unresolved", "decision": key,
                   "witness": f"{kind}:{name}", "location": location,
                   "message": (f"{key}: claims a [TEST_EVIDENCE] note at scope {name!r} that the assembled "
                               "specification does not carry")}


def _decisions(case: Path):
    """(key, invariants (location, text), tests (location, text) | None) per decision with formal invariants."""
    for item in design_index.list_items(case, kind="decision"):
        invariants = _section_lines(case, item, "Formal invariant(s)") or _section_lines(case, item, "Formal invariants")
        if invariants is None or not invariants[1].strip():
            continue
        yield item.get("key"), invariants, _section_lines(case, item, "Required tests")


def required_tests(case: Path) -> dict[str, Any]:
    """The State 2 half: every formal invariant has a described required test.

    What the test must show is a State 2 decision; which existing check proves
    it is a binding, confirmed by ``coverage`` at decision_witness_resolution
    (TRANSITION_PROTOCOL.md, "Invariant evidence"). A described test without a
    binding is carried there, not a pass and not a stop here.
    """
    case = case.resolve()
    findings: list[dict[str, Any]] = []
    decisions = carried = 0
    for key, invariants, tests in _decisions(case):
        decisions += 1
        body = tests[1] if tests else ""
        described = [line for line in body.splitlines()[1:] if line.strip()]
        if not described:
            findings.append({"severity": "error", "code": "invariant_without_required_test", "decision": key,
                             "location": invariants[0],
                             "message": f"{key}: formal invariants declared and no Required tests describe what "
                                        "must be shown — the decision has not said how it would be known to hold"})
            continue
        untested = [i for i in invariant_ids(invariants[1]) if i not in set(invariant_ids(body))]
        for ident in untested:
            findings.append({"severity": "error", "code": "invariant_without_required_test", "decision": key,
                             "invariant": ident, "location": tests[0],
                             "message": f"{key}: invariant {ident} is named by no Required tests item"})
        if not WITNESS_RE.search(body):
            carried += 1
    findings = fence.enforce(findings)
    return {"schema_version": SCHEMA_VERSION, "project_root": case.name,
            "summary": {"decisions_with_invariants": decisions, "binding_carried": carried,
                        "errors": fence.stops(findings)},
            "findings": findings}


def coverage(case: Path, factory: Path | None = None) -> dict[str, Any]:
    """Every invariant-bearing decision binds to an existing check that asserts it.

    A tag binds the invariant identifiers named on its own Required tests line;
    when the invariants carry identifiers, each one needs a binding line, so one
    tag cannot stand for invariants it does not name. A tag on a line naming no
    identifier binds the whole decision. Whether the bound check really asserts
    the invariant stays a judgement of the State 2 question round.
    """
    case = case.resolve()
    if factory is None:
        factory = factory_root(Path(__file__).resolve().parents[1])
    check_names, unavailable = _verification_check_names(case, factory)
    evidence_scopes = _test_evidence_scopes(case)

    findings: list[dict[str, Any]] = []
    decisions = 0
    witnessed = 0
    for key, invariants, tests in _decisions(case):
        decisions += 1
        lines = tests[1].splitlines() if tests else []
        location = (tests or invariants)[0]
        if not any(WITNESS_RE.search(line) for line in lines):
            findings.append({
                "severity": "warning", "code": "decision_without_witness",
                "decision": key, "location": location,
                "message": (f"{key}: formal invariants declared, no witness tag in "
                            "Required tests — nothing mechanical enforces this decision"),
            })
            continue
        ids = invariant_ids(invariants[1])
        bound: set[str] = set()
        whole = False
        for line in lines:
            resolved_line = False
            for kind, name in WITNESS_RE.findall(line):
                resolved, finding = _resolve(kind, name, key, location, check_names, unavailable, evidence_scopes)
                resolved_line = resolved_line or resolved
                if finding:
                    findings.append(finding)
            if resolved_line:
                named = [i for i in invariant_ids(line) if i in ids]
                bound.update(named)
                whole = whole or not named
        unbound = [] if whole else [i for i in ids if i not in bound]
        for ident in unbound:
            findings.append({
                "severity": "warning", "code": "invariant_without_witness", "decision": key,
                "invariant": ident, "location": location,
                "message": f"{key}: invariant {ident} is bound to no existing check; a tag binds only the "
                           "invariants its own line names",
            })
        if (whole or bound) and not unbound:
            witnessed += 1

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
