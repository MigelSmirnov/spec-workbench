#!/usr/bin/env python3
"""Every rule check of the standard on any revision, layered by owning state.

The second direction of issue #147. ``authoring next`` stops a case at the
first transition that does not hold; this lens shows everything at once, for a
case at any git ref or for a Factory accepted specification before a migration
starts, grouped by the state that owns each rule:

    python tools/design_diagnose.py --case examples/<case> [--ref <git ref>]
    python tools/design_diagnose.py --spec <global_spec.json> [--ref <git ref>]
    ... [--factory-root <code_factory>] [--code-root <project root>] [--json]

A rule whose inputs do not exist in the revision reports ``not_checkable``,
never silence or a pass. Wall-clock and elapsed-time obligations are shown
apart: a wall-clock backend says nothing about a monotonic source.

Three kinds of result are kept apart, each with what it read:

- the Workbench's checks of the design and the specification (always);
- the Factory's canonical validator on the specification (``--factory-root``);
- the Factory's time-source conformance gate on an implementation
  (``--code-root`` and ``--factory-root``), with the Factory commit and the
  digest of every file scanned. Without code it is ``not_checked``: no code
  is not a passed code check, and it hides none of the specification's results.

Nothing is written into the case, the Factory or the code; a ref is read from a
temporary worktree.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterator

import design_closure_gaps

SCHEMA = "spec_workbench_revision_diagnosis.v1"
ROOT = Path(__file__).resolve().parents[1]
SPEC_FILE = "global_spec.json"
NOT_CHECKABLE = "not_checkable"

# closure_gaps codes and the state that owns the rule they check
CLOSURE_OWNERS = {
    "model_without_fields": 1,
    "prose_closure_leak": 1,
    "orphan_read_entity": 5,
    "external_interface_returned": 6,
    "table_without_writer": 6,
    "fresh_timestamp_without_source": 2,
    "ambient_time_note": 2,
}
# Elapsed-time language in a note: a measured duration, not an instant.
ELAPSED_RE = re.compile(
    r"\b(?:monotonic(?:_ns)?|elapsed(?: time)?|duration|perf_counter(?:_ns)?|time\.monotonic(?:_ns)?)\b",
    re.IGNORECASE,
)
NOTE_SCOPE_RE = re.compile(r"^-?\s*([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*:")
TIME_SUBCATEGORIES = {"time_source_policy_invalid", "time_source_policy_required"}
CLOCK_CAPABILITIES = ("wall_clock_authority", "elapsed_clock_authority", "host_clock_authority")


# ---------------------------------------------------------------- inputs

def _git(repo: Path, *args: str) -> str:
    done = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if done.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {done.stderr.strip()}")
    return done.stdout.strip()


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@contextlib.contextmanager
def materialize(path: Path, ref: str | None, kind: str) -> Iterator[tuple[Path, dict[str, Any]]]:
    """(case directory to read, description of the input). A ref is read from a
    temporary detached worktree; a raw specification is placed alone in a
    temporary directory, so every check sees exactly what the revision holds."""
    path = path.resolve()
    with tempfile.TemporaryDirectory(prefix="design-diagnose-") as temp:
        described: dict[str, Any] = {"kind": kind, "path": str(path), "ref": ref}
        source = path
        worktree = None
        if ref is not None:
            repo = Path(_git(path if path.is_dir() else path.parent, "rev-parse", "--show-toplevel"))
            described["commit"] = _git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}")
            worktree = Path(temp) / "worktree"
            _git(repo, "worktree", "add", "--detach", "--quiet", str(worktree), described["commit"])
            source = worktree / path.relative_to(repo)
        try:
            if kind == "spec":
                case = Path(temp) / "spec"
                case.mkdir()
                data = source.read_bytes()
                (case / SPEC_FILE).write_bytes(data)
                described["spec_sha256"] = _sha(data)
            else:
                case = source
                spec = case / SPEC_FILE
                described["spec_sha256"] = _sha(spec.read_bytes()) if spec.is_file() else None
            yield case, described
        finally:
            if worktree is not None:
                repo = Path(_git(path if path.is_dir() else path.parent, "rev-parse", "--show-toplevel"))
                subprocess.run(["git", "-C", str(repo), "worktree", "remove", "--force", str(worktree)],
                               capture_output=True)


def _load_spec(case: Path) -> dict[str, Any] | None:
    try:
        spec = json.loads((case / SPEC_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return spec if isinstance(spec, dict) else None


def _has_state(case: Path, state: int) -> bool:
    from questions_workbench import documents
    return any(found == state for found, _ in documents.design_documents(case, state))


# ---------------------------------------------------------------- rule checks

def _result(rule: str, state: int, outcome: str, findings: list[dict[str, Any]] | None = None,
            reads: list[str] | None = None, reason: str | None = None) -> dict[str, Any]:
    findings = findings or []
    counts: dict[str, int] = {}
    for finding in findings:
        counts[str(finding.get("code"))] = counts.get(str(finding.get("code")), 0) + 1
    result = {"rule": rule, "state": state, "outcome": outcome, "findings": findings,
              "counts": dict(sorted(counts.items())), "reads": reads or []}
    if reason:
        result["reason"] = reason
    return result


def check_identity(case: Path, spec: dict[str, Any] | None) -> dict[str, Any]:
    rule = "every model has one identity and one closure"
    if not list(case.glob("01_models*.md")):
        return _result(rule, 1, NOT_CHECKABLE, reason="no State 1 model documents (01_models*.md) in the revision")
    if spec is not None and isinstance(spec.get("models"), dict):
        from identity_workbench import verify
        report = verify(case)
        return _result(rule, 1, "open" if report["findings"] else "closed", report["findings"],
                       ["01_models*.md", "60_model_closure_*.json", SPEC_FILE])
    from identity_workbench.service import state6_closure
    report = state6_closure(case)
    outcome = report["outcome"] if report["outcome"] != "not_checked" else NOT_CHECKABLE
    return _result(rule, 1, outcome, report["findings"], ["01_models*.md", "60_model_closure_*.json", "60_contracts.json"])


def check_time_sources(case: Path, spec: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Fresh timestamps (contracts and State 5) and notes that need the current time."""
    fresh_rule, notes_rule = "every fresh timestamp has a source", "a note that needs the time names its source"
    if spec is None:
        return [_result(fresh_rule, 2, NOT_CHECKABLE, reason=f"no assembled {SPEC_FILE} in the revision"),
                _result(notes_rule, 2, NOT_CHECKABLE, reason=f"no assembled {SPEC_FILE} in the revision")]
    models = spec.get("models") or {}
    contracts = spec.get("contracts") or {}
    owners = {f: m for m, fs in (spec.get("module_functions") or {}).items() for f in fs or []}
    sources = design_closure_gaps.time_sources(case, spec)
    notes = design_closure_gaps.ambient_time_findings(models, contracts, owners, spec.get("notes") or [], sources)
    results = [_result(notes_rule, 2, "open" if notes else "closed", notes, [f"{SPEC_FILE} notes, contracts, models"])]
    impacts = design_closure_gaps.parse_state_impacts(case)
    if not impacts:
        results.insert(0, _result(fresh_rule, 2, NOT_CHECKABLE,
                                  reason="no State 5 documents: which operations write is not stated in the revision"))
    else:
        fresh = design_closure_gaps.fresh_timestamp_findings(models, contracts, owners, impacts, sources)
        results.insert(0, _result(fresh_rule, 2, "open" if fresh else "closed", fresh,
                                  [f"{SPEC_FILE} contracts and models", "State 5 State impact"]))
    return results


def check_witness(case: Path, factory: Path | None) -> dict[str, Any]:
    rule = "every formal invariant is witnessed"
    import design_decision_witness
    if not _has_state(case, 2):
        return _result(rule, 2, NOT_CHECKABLE, reason="no State 2 documents in the revision")
    report = design_decision_witness.coverage(case, factory)
    findings = report["findings"]
    if findings and all(f.get("outcome") == "not_checked" for f in findings):
        return _result(rule, 2, NOT_CHECKABLE, findings, ["State 2 Required tests"],
                       reason="the bound checks cannot be read (no Factory verification config)")
    return _result(rule, 2, "open" if findings else "closed", findings,
                   ["State 2 Required tests", "Factory verification config", SPEC_FILE])


def check_flows(case: Path) -> dict[str, Any]:
    rule = "every flow step is executed"
    import flow_closure
    if not _has_state(case, 4):
        return _result(rule, 4, NOT_CHECKABLE, reason="no State 4 flow documents in the revision")
    try:
        report = flow_closure.coverage(case)
    except Exception as exc:  # the State 6 plan or catalog is missing or unreadable
        return _result(rule, 4, NOT_CHECKABLE, reason=f"the flows' operations cannot be read ({exc})")
    outcome = NOT_CHECKABLE if report["summary"]["reachability"] == "not_checked" else (
        "open" if report["findings"] else "closed")
    return _result(rule, 4, outcome, report["findings"], ["State 4 flows", "60_contract_plan.json", "80_notes.md",
                                                          "router and backend closures"])


def check_closure(spec: dict[str, Any] | None, case: Path) -> list[dict[str, Any]]:
    """The other closure-completeness rules of the specification, each with its owner."""
    if spec is None:
        return [_result("the specification's closure is complete", 6, NOT_CHECKABLE,
                        reason=f"no assembled {SPEC_FILE} in the revision")]
    findings = (design_closure_gaps.check_models(spec) + design_closure_gaps.check_orphan_reads(spec)
                + design_closure_gaps.check_external_returns(spec) + design_closure_gaps.check_tables(spec)
                + design_closure_gaps.check_prose(case, spec))
    by_state: dict[int, list[dict[str, Any]]] = {}
    for finding in findings:
        by_state.setdefault(CLOSURE_OWNERS.get(finding["code"], 6), []).append(finding)
    rules = {1: "every model states its content", 5: "everything read is produced", 6: "every return and table has a producer"}
    return [_result(rules[state], state, "open" if by_state.get(state) else "closed", by_state.get(state, []),
                    [SPEC_FILE]) for state in sorted(rules)]


# ---------------------------------------------------------------- time coverage

def _scoped_notes(spec: dict[str, Any]) -> list[tuple[str, str]]:
    found = []
    for note in spec.get("notes") or []:
        match = NOTE_SCOPE_RE.match(str(note))
        found.append((match.group(1) if match else "", str(note)))
    return found


def _clock_backend(case: Path, spec: dict[str, Any] | None) -> dict[str, Any] | None:
    backend = ((spec or {}).get("rules") or {}).get("system_clock_backend")
    if isinstance(backend, dict):
        return backend
    try:
        closure = json.loads((case / design_closure_gaps.CLOCK_CLOSURE_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return closure.get("backend_ir") if isinstance(closure, dict) and closure.get("status") == "closed" else None


def time_coverage(case: Path, spec: dict[str, Any] | None) -> dict[str, Any]:
    """Wall-clock and elapsed-time obligations, each against its own declared sources."""
    bounds = [
        "wall-clock requirements: notes in ambient current-time language (design_closure_gaps.AMBIENT_TIME_RE) "
        "and mutating State 5 operations that return datetime fields",
        f"elapsed-time requirements: notes naming monotonic, elapsed time, duration or perf_counter ({ELAPSED_RE.pattern})",
        "not analysed: design prose outside the notes, contracts' parameter meaning, and code — a requirement not "
        "detected here is not proof that none exists",
    ]
    if spec is None:
        return {"wall": {"outcome": NOT_CHECKABLE}, "elapsed": {"outcome": NOT_CHECKABLE},
                "analysis_bounds": bounds, "reason": f"no assembled {SPEC_FILE} in the revision"}

    owners = {f: m for m, fs in (spec.get("module_functions") or {}).items() for f in fs or []}

    def module_of(scope: str) -> str | None:
        return owners.get(scope) or owners.get(scope.split(".", 1)[0])

    policy = (spec.get("rules") or {}).get("time_source_policy") or {}
    wall_policy = policy.get("wall_clock") if isinstance(policy, dict) else None
    elapsed_policy = policy.get("elapsed_time") if isinstance(policy, dict) else None
    backend = _clock_backend(case, spec)
    wiring = (backend or {}).get("wiring") or {}

    # wall clock
    models, contracts = spec.get("models") or {}, spec.get("contracts") or {}
    wall_sources = design_closure_gaps.time_sources(case, spec)
    impacts = design_closure_gaps.parse_state_impacts(case)
    required = (design_closure_gaps.ambient_time_findings(models, contracts, owners, spec.get("notes") or [])
                + design_closure_gaps.fresh_timestamp_findings(models, contracts, owners, impacts))
    uncovered = (design_closure_gaps.ambient_time_findings(models, contracts, owners, spec.get("notes") or [], wall_sources)
                 + design_closure_gaps.fresh_timestamp_findings(models, contracts, owners, impacts, wall_sources))
    wall = {
        "outcome": "open" if uncovered else "closed",
        "requirements": [{"scope": f["contract"], "module": module_of(f["contract"]), "evidence": f["code"]}
                         for f in required],
        "declared": {
            "policy_authorities": list((wall_policy or {}).get("authority_modules") or []),
            "backend": ({"schema_version": backend.get("schema_version"), "module": wiring.get("module"),
                         "operation": wiring.get("function") or wiring.get("wall_clock_function")
                         or wiring.get("concrete_class")} if backend else None),
            "consumers": sorted(design_closure_gaps.clock_consumers(case, spec)),
        },
        "findings": uncovered,
        "state_impacts_read": bool(impacts),
    }

    # elapsed time
    authorities = list((elapsed_policy or {}).get("authority_modules") or [])
    accessor = wiring.get("elapsed_clock_function") if isinstance(wiring.get("elapsed_clock_function"), str) else None
    clock_module = wiring.get("module")
    imports = design_closure_gaps.decided_imports(case, spec)
    consumers = sorted(consumer for consumer, providers in (imports or {}).items()
                       if accessor and isinstance(providers, dict) and accessor in (providers.get(clock_module) or []))
    requirements, findings = [], []
    for scope, note in _scoped_notes(spec):
        phrase = ELAPSED_RE.search(note)
        if not phrase:
            continue
        module = module_of(scope)
        requirements.append({"scope": scope, "module": module, "evidence": phrase.group(0)})
        if module not in authorities and module not in consumers:
            findings.append({"code": "elapsed_requirement_without_source", "contract": scope, "module": module,
                             "phrase": phrase.group(0),
                             "message": (f"{scope}: the note needs elapsed time ('{phrase.group(0)}') and module "
                                         f"{module} holds no elapsed-time authority and imports no elapsed "
                                         "operation of a clock backend")})
    for module in authorities:
        if not (accessor and module == clock_module):
            findings.append({"code": "elapsed_authority_without_backend", "module": module,
                             "message": (f"rules.time_source_policy grants {module} elapsed-time authority and no "
                                         "clock backend emits an elapsed operation in it: a clock adapter left to "
                                         "generation (the Factory refuses it as elapsed_clock_authority)")})
    elapsed = {
        "outcome": "open" if findings else "closed",
        "requirements": requirements,
        "declared": {"policy_authorities": authorities,
                     "backend_operation": f"{clock_module}.{accessor}" if accessor else None,
                     "consumers": consumers, "imports_decided": imports is not None},
        "findings": findings,
    }
    return {"wall": wall, "elapsed": elapsed, "analysis_bounds": bounds}


# ---------------------------------------------------------------- the Factory

def factory_root(explicit: Path | None) -> Path | None:
    if explicit is not None:
        return explicit
    override = os.environ.get("SPEC_WORKBENCH_FACTORY_ROOT")
    if override:
        return Path(override)
    for candidate in (ROOT.parent / "code_factory", ROOT.parent.parent / "code_factory"):
        if (candidate / "tools" / "validate_spec.py").is_file():
            return candidate
    return None


def _factory_identity(factory: Path) -> dict[str, Any]:
    identity: dict[str, Any] = {"root": str(factory)}
    try:
        identity["commit"] = _git(factory, "rev-parse", "HEAD")
        identity["dirty"] = bool(_git(factory, "status", "--porcelain", "--", "tools", "SPEC_STANDARD.md"))
    except RuntimeError:
        identity["commit"] = None
    tools = {name: factory / "tools" / name for name in ("validate_spec.py", "python_time_source_gate.py",
                                                          "time_source_policy.py")}
    identity["tool_sha256"] = {name: _sha(path.read_bytes()) for name, path in tools.items() if path.is_file()}
    return identity


def _time_related(finding: dict[str, Any]) -> bool:
    if finding.get("subcategory") in TIME_SUBCATEGORIES:
        return True
    text = json.dumps(finding)
    return (finding.get("subcategory") == "local_implementation_requires_deterministic_backend"
            and any(capability in text for capability in CLOCK_CAPABILITIES)) or "clock" in str(finding.get("subcategory"))


def factory_spec_check(case: Path, factory: Path | None) -> dict[str, Any]:
    """The Factory's canonical validator on the specification; time findings apart."""
    spec_path = case / SPEC_FILE
    if not spec_path.is_file():
        return {"outcome": NOT_CHECKABLE, "reason": f"no {SPEC_FILE} in the revision"}
    validator = factory / "tools" / "validate_spec.py" if factory else None
    if validator is None or not validator.is_file():
        return {"outcome": "not_checked", "reason": "no Factory checkout (--factory-root or SPEC_WORKBENCH_FACTORY_ROOT)"}
    with tempfile.TemporaryDirectory(prefix="design-diagnose-validate-") as temp:
        out = Path(temp) / "report.json"
        done = subprocess.run([sys.executable, str(validator), str(spec_path), "--out", str(out), "--quiet"],
                              capture_output=True, text=True, cwd=str(factory))
        if not out.is_file():
            return {"outcome": "not_checked", "factory": _factory_identity(factory),
                    "reason": f"the validator wrote no report (exit {done.returncode})"}
        report = json.loads(out.read_text(encoding="utf-8"))
    errors = [f for f in report.get("findings") or [] if str(f.get("severity")).lower() in {"error", "block"}]
    time_errors = [f for f in errors if _time_related(f)]
    return {"outcome": "open" if time_errors else "closed", "factory": _factory_identity(factory),
            "status": report.get("status"), "errors": len(errors), "time_findings": time_errors}


def factory_code_check(case: Path, factory: Path | None, code_root: Path | None) -> dict[str, Any]:
    """The Factory's time-source conformance gate on an implementation, with what it read."""
    if code_root is None:
        return {"outcome": "not_checked", "reason": "no implementation given (--code-root): the code is not "
                                                     "checked, which is not a passed check"}
    spec_path = case / SPEC_FILE
    gate = factory / "tools" / "python_time_source_gate.py" if factory else None
    if not spec_path.is_file():
        return {"outcome": NOT_CHECKABLE, "reason": f"no {SPEC_FILE}: the gate reads the policy from it"}
    if gate is None or not gate.is_file():
        return {"outcome": "not_checked", "reason": "no Factory checkout with tools/python_time_source_gate.py"}
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    scanned = {}
    for module, target in (spec.get("module_paths") or {}).items():
        path = code_root / f"{target}.py"
        if path.is_file():
            scanned[module] = {"path": f"{target}.py", "sha256": _sha(path.read_bytes())}
    code: dict[str, Any] = {"root": str(code_root), "files": scanned}
    try:
        code["commit"] = _git(code_root, "rev-parse", "HEAD")
    except RuntimeError:
        code["commit"] = None
    done = subprocess.run([sys.executable, str(gate), "--spec", str(spec_path), "--project-root", str(code_root)],
                          capture_output=True, text=True, cwd=str(factory))
    try:
        report = json.loads(done.stdout)
    except ValueError:
        return {"outcome": "not_checked", "factory": _factory_identity(factory), "code": code,
                "reason": f"the gate gave no report (exit {done.returncode}): {done.stderr.strip()[-200:]}"}
    outcome = {"PASS": "closed", "BLOCK": "open"}.get(report.get("verdict"), NOT_CHECKABLE)
    return {"outcome": outcome, "verdict": report.get("verdict"), "factory": _factory_identity(factory),
            "code": code, "findings": report.get("findings") or [], "reason": report.get("reason")}


# ---------------------------------------------------------------- the report

def diagnose(path: Path, kind: str, ref: str | None = None, factory: Path | None = None,
             code_root: Path | None = None) -> dict[str, Any]:
    factory = factory_root(factory)
    with materialize(path, ref, kind) as (case, described):
        spec = _load_spec(case)
        results = [check_identity(case, spec), *check_time_sources(case, spec), check_witness(case, factory),
                   check_flows(case), *check_closure(spec, case)]
        time = time_coverage(case, spec)
        factory_results = {"spec": factory_spec_check(case, factory),
                           "code": factory_code_check(case, factory, code_root.resolve() if code_root else None)}
    by_state: dict[str, list[dict[str, Any]]] = {}
    for result in sorted(results, key=lambda r: r["state"]):
        by_state.setdefault(f"State {result['state']}", []).append(result)
    summary = {state: {"open": sum(len(r["findings"]) for r in rows if r["outcome"] == "open"),
                       "not_checkable": [r["rule"] for r in rows if r["outcome"] == NOT_CHECKABLE]}
               for state, rows in by_state.items()}
    return {"schema_version": SCHEMA, "input": described, "by_state": by_state, "summary": summary,
            "time": time, "factory": factory_results}


def _line(result: dict[str, Any]) -> str:
    if result["outcome"] == NOT_CHECKABLE:
        return f"    {result['rule']}: not checkable — {result.get('reason', '')}"
    counts = ", ".join(f"{count} {code}" for code, count in result["counts"].items())
    return f"    {result['rule']}: {result['outcome']}" + (f" ({counts})" if counts else "")


def human(report: dict[str, Any]) -> str:
    source = report["input"]
    lines = [f"diagnosis of {source['kind']} {source['path']}" + (f" at {source.get('commit')}" if source.get("ref") else "")]
    lines.append("  " + " · ".join(
        f"{state}: {row['open']} open" + (f", {len(row['not_checkable'])} not checkable" if row["not_checkable"] else "")
        for state, row in report["summary"].items()))
    for state, rows in report["by_state"].items():
        lines.append(f"  {state}")
        lines += [_line(row) for row in rows]
    time = report["time"]
    for kind in ("wall", "elapsed"):
        part = time[kind]
        lines.append(f"  time · {kind}: {part['outcome']}"
                     + (f", {len(part.get('requirements', []))} requirement(s), {len(part.get('findings', []))} without a source"
                        if part["outcome"] != NOT_CHECKABLE else ""))
        lines += [f"    {f['code']}: {f['message'][:160]}" for f in part.get("findings", [])[:10]]
    for kind in ("spec", "code"):
        part = report["factory"][kind]
        detail = part.get("reason") or (f"{len(part.get('time_findings', part.get('findings', [])))} time finding(s)")
        lines.append(f"  Factory {kind} check: {part['outcome']} — {detail}")
        for finding in part.get("time_findings", part.get("findings", []))[:10]:
            lines.append(f"    {finding.get('subcategory') or finding.get('code')}: "
                         f"{str(finding.get('message') or finding.get('reason'))[:160]}")
    lines.append("  bounds: " + " | ".join(time["analysis_bounds"]))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--case", type=Path, help="a case directory")
    target.add_argument("--spec", type=Path, help="an accepted global_spec.json (e.g. a Factory project's)")
    parser.add_argument("--ref", help="read the case or the specification as it was at this git ref")
    parser.add_argument("--factory-root", type=Path)
    parser.add_argument("--code-root", type=Path, help="an implementation the specification's module_paths resolve in")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    path, kind = (args.case, "case") if args.case else (args.spec, "spec")
    try:
        report = diagnose(path, kind, args.ref, args.factory_root, args.code_root)
    except (RuntimeError, OSError, ValueError) as exc:
        print(f"design_diagnose: error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str) if args.json else human(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
