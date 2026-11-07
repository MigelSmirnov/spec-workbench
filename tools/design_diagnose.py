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

Every check of the two Workbench registries — the assembly checks and the
transition checks — is in the report once, under the state or phase that owns
its rule, with the inputs it reads; a check that cannot run is an `error` row
and hides no other result. The report names the Workbench that produced it
(commit, uncommitted changes, digests of the tools it loaded, of the sequence
and of the standard), so a past result can be reproduced.

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
# Passed as the Factory when none is chosen: it holds no checkout, so a check
# that reads one reports it unavailable instead of discovering another.
NO_FACTORY = Path("/nonexistent/no-factory-chosen")
# Rows whose result depends on the Factory checkout they read.
FACTORY_READERS = frozenset({"witness", "decision_witness", "witness_material", "persistence", "imports"})

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


# ---------------------------------------------------------------- rule checks

# Every check the Workbench registers, once: the assembly registry
# (assembly_workbench.checks.CHECKS) and the transition registry
# (transition.CHECKS). Each row says which state owns the rule and which inputs
# it reads; nothing here re-implements a check. A check whose inputs the
# revision lacks is not_checkable; one that fails to run is an error; neither
# is a pass, and neither hides another check's result.
#   owner: "State N", or the phase of the authoring sequence that owns the rule
#   needs: globs that must each match at least one file of the revision
ASSEMBLY_ROWS: dict[str, dict[str, Any]] = {
    "language": {"owner": "Stage 8 assembly", "needs": [SPEC_FILE],
                 "rule": "the specification uses only the standard's language"},
    "modules": {"owner": "State 3", "needs": ["30_*.md"], "rule": "every module owns a mechanism"},
    "identity": {"owner": "State 1", "needs": ["01_models*.md", SPEC_FILE],
                 "rule": "every model has one identity and one closure"},
    "fields": {"owner": "State 6", "needs": ["01_models*.md", "60_model_closure_*.json"],
               "rule": "the model closure carries every fact State 1 names"},
    "data": {"owner": "Data closure (before State 6)", "needs": ["60_data_closure.json"],
             "rule": "every accepted value has one home"},
    "contracts": {"owner": "State 6", "needs": ["50_api_plan.json", "60_contract_plan.json", "60_contracts.json"],
                  "rule": "every planned function has an exact signature"},
    "external_contracts": {"owner": "State 6", "needs": ["60_contracts.json"],
                           "rule": "external facts rest on content-addressed evidence"},
    "notes": {"owner": "State 7", "needs": ["80_notes.md", SPEC_FILE], "rule": "notes pass the note gate"},
    "closure_gaps": {"owner": "by finding", "needs": [SPEC_FILE],
                     "rule": "the specification's closure is complete"},
    "router": {"owner": "Deterministic closures (after State 6)", "needs": ["60_contracts.json"],
               "rule": "every exposed operation has a closed route"},
    "persistence": {"owner": "Deterministic closures (after State 6)", "needs": ["60_contracts.json"],
                    "rule": "the persistence backend is closed against the contracts"},
    "witness": {"owner": "State 2", "needs": ["02_*.md"], "rule": "every formal invariant is witnessed"},
    "imports": {"owner": "Imports closure (after State 7)", "needs": ["65_imports.json", SPEC_FILE],
                "rule": "every symbol a module names is decided"},
    "flows": {"owner": "State 4", "needs": ["40_*.md", "60_contract_plan.json", "60_contracts.json"],
              "rule": "every flow step is executed"},
    # the Factory's validator is reported once, under factory.spec, with what it read
    "factory": {"owner": "Stage 9 Factory admission", "needs": [SPEC_FILE], "reported_as": "factory.spec",
                "rule": "the Factory's canonical validator accepts the specification"},
}
TRANSITION_NEEDS: dict[str, list[str]] = {
    "model_closure": ["01_models*.md", "60_contracts.json"],
    "time_source": ["50_*.md", "60_contract_plan.json", "60_contracts.json"],
    "ambient_time": ["80_notes.md", "60_contract_plan.json", "60_contracts.json"],
    "flow_steps": ["40_*.md", "60_contract_plan.json", "60_contracts.json"],
    "flow_reachability": ["40_*.md", "60_contract_plan.json", "60_contracts.json", "80_notes.md"],
    "invariant_tests": ["02_*.md"],
    "witness_material": ["02_*.md"],
    "decision_witness": ["02_*.md"],
}


def _row(registry: str, name: str, owner: str, rule: str, outcome: str, findings: list[dict[str, Any]] | None = None,
         reads: list[str] | None = None, reason: str | None = None) -> dict[str, Any]:
    findings = findings or []
    counts: dict[str, int] = {}
    for finding in findings:
        counts[str(finding.get("code") or finding.get("subcategory"))] = counts.get(
            str(finding.get("code") or finding.get("subcategory")), 0) + 1
    row = {"registry": registry, "check": name, "owner": owner, "rule": rule, "outcome": outcome,
           "findings": findings, "counts": dict(sorted(counts.items())), "reads": reads or []}
    if reason:
        row["reason"] = reason
    return row


def _missing(case: Path, needs: list[str]) -> list[str]:
    return [pattern for pattern in needs if not list(case.glob(pattern))]


def _safely(run, registry: str, name: str, owner: str, rule: str, reads: list[str]) -> list[dict[str, Any]]:
    """One check, isolated: whatever it raises becomes its own `error` row."""
    try:
        return run()
    except Exception as exc:  # noqa: BLE001 — a failing check never aborts the others
        return [_row(registry, name, owner, rule, "error", reads=reads,
                     reason=f"the check could not run: {type(exc).__name__}: {exc}")]


def assembly_rows(case: Path, factory: Path | None) -> list[dict[str, Any]]:
    from assembly_workbench import checks

    rows: list[dict[str, Any]] = []
    for name in checks.CHECKS:
        meta = ASSEMBLY_ROWS.get(name, {"owner": "unresolved", "needs": [], "rule": name})
        owner, rule, needs = meta["owner"], meta["rule"], meta["needs"]
        if meta.get("reported_as"):
            rows.append(_row("assembly", name, owner, rule, "reported_elsewhere", reads=needs,
                             reason=f"reported under {meta['reported_as']} with the Factory's identity"))
            continue
        missing = _missing(case, needs)
        if missing:
            rows.append(_row("assembly", name, owner, rule, NOT_CHECKABLE, reads=needs,
                             reason=f"the revision has no {', '.join(missing)}"))
            continue

        def run(name=name, owner=owner, rule=rule, needs=needs):
            result = checks.run(case, name, factory_root=factory)
            findings = [f for f in result.findings if isinstance(f, dict)]
            if name != "closure_gaps":
                return [_row("assembly", name, owner, rule, "closed" if result.ready else "open", findings, needs)]
            by_owner: dict[str, list[dict[str, Any]]] = {}
            for finding in findings:
                state = CLOSURE_OWNERS.get(str(finding.get("code")))
                by_owner.setdefault(f"State {state}" if state else "unresolved", []).append(finding)
            if not by_owner:
                return [_row("assembly", name, "State 6", rule, "closed", [], needs)]
            return [_row("assembly", name, holder, rule, "open", found, needs) for holder, found in sorted(by_owner.items())]

        rows += _safely(run, "assembly", name, owner, rule, needs)
    return rows


def transition_rows(case: Path, factory: Path) -> list[dict[str, Any]]:
    import transition

    sequence = transition.load_sequence()
    owners: dict[str, tuple[str, str]] = {}
    for phase in sequence["phases"]:
        state = phase.get("semantic_state")
        label = f"State {state}" if state is not None else phase["id"]
        for name in transition.own_checks(sequence, phase["id"]):
            owners[name] = (label, "owned by this layer")
    for item in transition.obligations(sequence):
        phase = next(p for p in sequence["phases"] if p["id"] == item["from"])
        state = phase.get("semantic_state")
        owners.setdefault(item["check"], (f"State {state}" if state is not None else phase["id"],
                                          item.get("obligation", "")))
    rows: list[dict[str, Any]] = []
    for name in transition.CHECKS:
        owner, rule = owners.get(name, ("unresolved", name))
        needs = TRANSITION_NEEDS.get(name, [])
        missing = _missing(case, needs)
        if missing:
            rows.append(_row("transition", name, owner, rule, NOT_CHECKABLE, reads=needs,
                             reason=f"the revision has no {', '.join(missing)}"))
            continue

        def run(name=name, owner=owner, rule=rule, needs=needs):
            result = transition.run_check(case, name, factory)
            outcome = {"not_checked": NOT_CHECKABLE}.get(result["outcome"], result["outcome"])
            row = _row("transition", name, owner, rule, outcome, result["findings"], needs)
            if outcome == NOT_CHECKABLE:
                row["reason"] = "; ".join(f.get("message", "") for f in result["findings"])[:300]
            return [row]

        rows += _safely(run, "transition", name, owner, rule, needs)
    return rows


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
            return {"outcome": "error", "factory": _factory_identity(factory),
                    "reason": f"the validator wrote no report (exit {done.returncode})"}
        try:
            report = json.loads(out.read_text(encoding="utf-8"))
        except ValueError as exc:
            return {"outcome": "error", "factory": _factory_identity(factory),
                    "reason": f"the validator's report is not JSON (exit {done.returncode}): {exc}"}
    findings = [f for f in report.get("findings") or [] if isinstance(f, dict)]
    errors = [f for f in findings if str(f.get("severity")).lower() in {"error", "block"}]
    time_errors = [f for f in errors if _time_related(f)]
    status = str(report.get("status") or "")
    # the whole result decides; the time part is shown apart, never instead
    consistent = (done.returncode == 0) == (not errors) and (status.upper() in {"PASS", "OK", ""}) == (not errors)
    outcome = "open" if errors else ("closed" if consistent else "error")
    return {"outcome": outcome, "time_outcome": "open" if time_errors else "closed",
            "factory": _factory_identity(factory), "status": report.get("status"), "exit_code": done.returncode,
            "errors": len(errors), "findings": findings, "time_findings": time_errors,
            **({} if consistent or errors else {"reason": f"the validator exited {done.returncode} with status "
                                                          f"{report.get('status')!r} and no error finding"})}


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

def workbench_identity() -> dict[str, Any]:
    """The Workbench that produced the report: commit, uncommitted changes, and
    the digest of every tool module the report imported."""
    identity: dict[str, Any] = {"root": str(ROOT)}
    try:
        identity["commit"] = _git(ROOT, "rev-parse", "HEAD")
        identity["dirty"] = bool(_git(ROOT, "status", "--porcelain", "--", "tools", "skills"))
    except RuntimeError:
        identity["commit"] = None
    tools = ROOT / "tools"
    loaded = sorted({Path(module.__file__).resolve() for module in list(sys.modules.values())
                     if getattr(module, "__file__", None) and str(module.__file__).startswith(str(tools))})
    identity["tool_sha256"] = {str(path.relative_to(ROOT)): _sha(path.read_bytes()) for path in loaded}
    sequence = ROOT / "skills" / "spec-authoring" / "authoring_sequence.json"
    standard = ROOT / "skills" / "spec-authoring" / "SPEC_STANDARD.md"
    identity["sequence_sha256"] = _sha(sequence.read_bytes()) if sequence.is_file() else None
    identity["standard_sha256"] = _sha(standard.read_bytes()) if standard.is_file() else None
    return identity


def _section(run, fallback: dict[str, Any]) -> dict[str, Any]:
    try:
        return run()
    except Exception as exc:  # noqa: BLE001 — one failing part never hides the others
        return {**fallback, "outcome": "error", "reason": f"{type(exc).__name__}: {exc}"}


def diagnose(path: Path, kind: str, ref: str | None = None, factory: Path | None = None,
             code_root: Path | None = None) -> dict[str, Any]:
    factory = factory_root(factory)
    with materialize(path, ref, kind) as (case, described):
        spec = _load_spec(case)
        # one Factory checkout for every check that reads one: the chosen root,
        # or a path that holds none, so no check falls back to another checkout
        chosen = factory or NO_FACTORY
        rows = assembly_rows(case, chosen) + transition_rows(case, chosen)
        for row in rows:
            if row["check"] in FACTORY_READERS:
                row["factory_root"] = str(chosen) if factory else None
        time = _section(lambda: time_coverage(case, spec), {
            "wall": {"outcome": "error"}, "elapsed": {"outcome": "error"}, "analysis_bounds": []})
        factory_results = {
            "spec": _section(lambda: factory_spec_check(case, factory), {}),
            "code": _section(lambda: factory_code_check(case, factory, code_root.resolve() if code_root else None), {}),
        }
    order = lambda owner: (0, int(owner.split()[1])) if owner.startswith("State ") else (1, owner)
    by_state: dict[str, list[dict[str, Any]]] = {}
    for row in sorted(rows, key=lambda r: order(r["owner"])):
        by_state.setdefault(row["owner"], []).append(row)
    # the two registries check the same rules at different moments: their counts
    # are kept apart rather than added
    summary = {owner: {"open": {registry: sum(len(r["findings"]) or 1 for r in owned
                                              if r["outcome"] == "open" and r["registry"] == registry)
                                for registry in ("assembly", "transition")},
                       "not_checkable": [r["check"] for r in owned if r["outcome"] == NOT_CHECKABLE],
                       "error": [r["check"] for r in owned if r["outcome"] == "error"]}
               for owner, owned in by_state.items()}
    coverage = {"assembly": sorted({r["check"] for r in rows if r["registry"] == "assembly"}),
                "transition": sorted({r["check"] for r in rows if r["registry"] == "transition"})}
    return {"schema_version": SCHEMA, "input": described, "workbench": workbench_identity(),
            "by_state": by_state, "summary": summary, "coverage": coverage, "time": time,
            "factory": factory_results}


def _line(row: dict[str, Any]) -> str:
    name = f"{row['check']} ({row['registry']})"
    if row["outcome"] in {NOT_CHECKABLE, "error", "reported_elsewhere"}:
        return f"    {name}: {row['outcome'].replace('_', ' ')} — {row.get('reason', '')}"
    counts = ", ".join(f"{count} {code}" for code, count in row["counts"].items())
    return f"    {name}: {row['outcome']}" + (f" ({counts})" if counts else "")


def human(report: dict[str, Any]) -> str:
    source = report["input"]
    lines = [f"diagnosis of {source['kind']} {source['path']}" + (f" at {source.get('commit')}" if source.get("ref") else "")
             + f" · workbench {str(report['workbench'].get('commit'))[:10]}"
             + (" (dirty)" if report["workbench"].get("dirty") else "")]
    lines.append("  " + " · ".join(
        f"{owner}: {row['open']['assembly']} open" + (f" ({row['open']['transition']} at its transition)"
                                                       if row['open']['transition'] else "")
        + (f", {len(row['not_checkable'])} not checkable" if row["not_checkable"] else "")
        + (f", {len(row['error'])} error" if row["error"] else "")
        for owner, row in report["summary"].items()))
    for owner, rows in report["by_state"].items():
        lines.append(f"  {owner}")
        lines += [_line(row) for row in rows]
    time = report["time"]
    for kind in ("wall", "elapsed"):
        part = time.get(kind) or {"outcome": "error"}
        lines.append(f"  time · {kind}: {part['outcome']}"
                     + (f", {len(part.get('requirements', []))} requirement(s), {len(part.get('findings', []))} without a source"
                        if part["outcome"] not in {NOT_CHECKABLE, "error"} else ""))
        lines += [f"    {f['code']}: {f['message'][:160]}" for f in part.get("findings", [])[:10]]
    spec_check = report["factory"]["spec"]
    lines.append(f"  Factory spec check: {spec_check.get('outcome')}"
                 + (f" — {spec_check['errors']} error(s), time part {spec_check.get('time_outcome')}"
                    if "errors" in spec_check else f" — {spec_check.get('reason', '')}"))
    for finding in spec_check.get("findings", [])[:15]:
        if str(finding.get("severity")).lower() in {"error", "block"}:
            lines.append(f"    {finding.get('subcategory') or finding.get('category')}: {str(finding.get('message'))[:160]}")
    code_check = report["factory"]["code"]
    lines.append(f"  Factory code check: {code_check.get('outcome')} — "
                 + (code_check.get("reason") or f"{len(code_check.get('findings', []))} finding(s)"))
    for finding in code_check.get("findings", [])[:10]:
        lines.append(f"    {finding.get('code')}: {finding.get('module')} {str(finding.get('reason'))[:120]}")
    lines.append("  bounds: " + " | ".join(time.get("analysis_bounds") or []))
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
