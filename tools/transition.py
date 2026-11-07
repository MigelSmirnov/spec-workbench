#!/usr/bin/env python3
"""The transition protocol: what a layer closes, carries and receives.

skills/spec-authoring/TRANSITION_PROTOCOL.md is the method. A phase of
authoring_sequence.json may declare a ``layer`` block:

    "layer": {
      "owns":    ["<decision this layer makes>", ...],
      "checks":  ["<check run at this layer's own handoff>", ...],
      "carries": [{"id": ..., "obligation": ..., "to": "<receiving phase>",
                   "check": "<check that confirms it there>"}]
    }

Nothing here re-decides anything. A check is a rule of the standard already
implemented by its owner (identity, closure gaps, witness, flow closure); this
module only runs it at the handoff of the layer that receives the obligation,
and reports one of four outcomes:

    closed         the decision is recorded and confirmed at the available level
    carried        a determined obligation with a receiving layer and a criterion
    not_checked    an input the check needs does not exist — never a pass; when
                   the input is required at this layer, the transition stops
    workbench_gap  the decision cannot be expressed in the standard, or the tool
                   cannot check the evidence there is (KNOWN_GAPS.md); it stops
                   too, but it is routed to the Workbench, not to the author

    python tools/transition.py examples/<case> --phase state6_exact_contracts [--json]
    python tools/transition.py examples/<case> --state 7 [--json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
SEQUENCE_FILE = ROOT / "skills" / "spec-authoring" / "authoring_sequence.json"
KNOWN_GAPS_FILE = ROOT / "skills" / "spec-authoring" / "KNOWN_GAPS.md"
SCHEMA = "spec_workbench_transition.v1"
OUTCOMES = ("closed", "carried", "not_checked", "workbench_gap", "open")
CLOSURE_GLOB = "60_model_closure_*.json"
NOTES_FILE = "80_notes.md"
KNOWN_GAP_TAG = re.compile(r"\[known_gap:\s*(KG-\d{3})\]")
GAP_HEADING = re.compile(r"^##\s+(KG-\d{3})\b")
GAP_CODES = re.compile(r"^Finding codes:\s*(.+)$")


def load_sequence(path: Path = SEQUENCE_FILE) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _phases(sequence: dict[str, Any]) -> list[dict[str, Any]]:
    return list(sequence.get("phases") or [])


def obligations(sequence: dict[str, Any]) -> list[dict[str, Any]]:
    """Every obligation a layer carries, with the phase that gives it."""
    found = []
    for phase in _phases(sequence):
        for item in (phase.get("layer") or {}).get("carries") or []:
            found.append({**item, "from": phase["id"]})
    return found


def received(sequence: dict[str, Any], phase_id: str) -> list[dict[str, Any]]:
    """The obligations that close at `phase_id`: carried there by an earlier layer."""
    return [item for item in obligations(sequence) if item.get("to") == phase_id]


def own_checks(sequence: dict[str, Any], phase_id: str) -> list[str]:
    for phase in _phases(sequence):
        if phase["id"] == phase_id:
            return list((phase.get("layer") or {}).get("checks") or [])
    return []


def layer(sequence: dict[str, Any], phase_id: str) -> dict[str, Any]:
    """The static protocol of one phase: what it owns, checks, carries and receives."""
    phase = next((p for p in _phases(sequence) if p["id"] == phase_id), {})
    block = phase.get("layer") or {}
    return {
        "owns": list(block.get("owns") or []),
        "checks": list(block.get("checks") or []),
        "carries": [dict(item) for item in block.get("carries") or []],
        "receives": [{k: v for k, v in item.items()} for item in received(sequence, phase_id)],
    }


# ---------------------------------------------------------------- the checks

def _report(outcome: str, findings: list[dict[str, Any]], **summary: Any) -> dict[str, Any]:
    return {"outcome": outcome, "findings": findings, "summary": summary}


def _closure_models(project: Path) -> dict[str, Any] | None:
    paths = sorted(project.glob(CLOSURE_GLOB))
    if not paths:
        return None
    models: dict[str, Any] = {}
    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(payload, dict) and isinstance(payload.get("models"), dict):
            models.update(payload["models"])
    return models


def _not_checked(code: str, message: str) -> dict[str, Any]:
    return _report("not_checked", [{"severity": "error", "code": code, "outcome": "not_checked",
                                    "message": f"{message} — not checked is not a pass"}])


def _contract_rows(project: Path) -> tuple[dict[str, Any], dict[str, str]]:
    import design_stage6_contracts

    try:
        catalog = design_stage6_contracts.load_catalog(project)["contracts"]
        plan = design_stage6_contracts.load_plan(project)["functions"]
    except (design_stage6_contracts.DesignStage6ContractsError, OSError, ValueError, KeyError):
        return {}, {}
    contracts = {k: v for k, v in catalog.items() if isinstance(v, str) and v != "unresolved"}
    func_module = {e["function"]: str(e.get("module") or "").removeprefix("module:")
                   for e in plan if isinstance(e, dict) and isinstance(e.get("function"), str)}
    return contracts, func_module


def _spec_or_none(project: Path) -> dict[str, Any] | None:
    import design_closure_gaps

    try:
        return design_closure_gaps.load_spec(project)
    except (OSError, ValueError):
        return None


def _time_authorities(project: Path) -> set[str]:
    """Modules with a declared source: policy authorities and module-level clock consumers."""
    import design_closure_gaps

    return design_closure_gaps.time_sources(project, _spec_or_none(project))


def check_model_closure(project: Path) -> dict[str, Any]:
    from identity_workbench.service import state6_closure

    report = state6_closure(project)
    return _report(report["outcome"], report["findings"], **report["summary"])


def check_time_source(project: Path) -> dict[str, Any]:
    """State 2 decided where time comes from; State 6 contracts must say how each consumer gets it."""
    import design_closure_gaps

    impacts = design_closure_gaps.parse_state_impacts(project)
    mutating = [name for name, row in impacts.items() if not row["read_only"]]
    models = _closure_models(project)
    if models is None:
        if not mutating:
            return _report("closed", [], mutating_operations=0)
        return _not_checked("time_source_not_checked",
                            f"{len(mutating)} mutating public operation(s): whether their returned timestamps have a "
                            f"source needs the model closure ({CLOSURE_GLOB}), and there is none")
    contracts, func_module = _contract_rows(project)
    sources = _time_authorities(project)
    through = design_closure_gaps.calls_supplying_time(project, _spec_or_none(project), models, contracts,
                                                       func_module, sources)
    findings = [{**f, "severity": "error"} for f in design_closure_gaps.fresh_timestamp_findings(
        models, contracts, func_module, impacts, sources, through)]
    return _report("open" if findings else "closed", findings, mutating_operations=len(mutating))


def check_ambient_time(project: Path) -> dict[str, Any]:
    """A note that needs the current time names its source (State 2 decided which)."""
    import design_closure_gaps

    notes_path = project / NOTES_FILE
    if not notes_path.is_file():
        return _not_checked("ambient_time_not_checked", f"no {NOTES_FILE}: the notes this check reads are not written")
    models = _closure_models(project)
    if models is None:
        return _not_checked("ambient_time_not_checked",
                            f"whether a note's clock is handed to its module needs the model closure ({CLOSURE_GLOB})")
    contracts, func_module = _contract_rows(project)
    notes = [line for line in notes_path.read_text(encoding="utf-8").splitlines()
             if line.strip() and not line.startswith("#")]
    sources = _time_authorities(project)
    through = design_closure_gaps.calls_supplying_time(project, _spec_or_none(project), models, contracts,
                                                       func_module, sources, notes)
    findings = [{**f, "severity": "error"} for f in design_closure_gaps.ambient_time_findings(
        models, contracts, func_module, notes, sources, through)]
    return _report("open" if findings else "closed", findings)


def check_flow_steps(project: Path) -> dict[str, Any]:
    import flow_closure

    report = flow_closure.coverage(project, reachability=False)
    return _report("open" if report["findings"] else "closed", report["findings"], **report["summary"])


def check_flow_reachability(project: Path) -> dict[str, Any]:
    import flow_closure

    report = flow_closure.coverage(project)
    outcome = ("not_checked" if report["summary"]["reachability"] == "not_checked"
               else "open" if report["findings"] else "closed")
    return _report(outcome, report["findings"], **report["summary"])


def check_invariant_tests(project: Path) -> dict[str, Any]:
    import design_decision_witness

    report = design_decision_witness.required_tests(project)
    carried = report["summary"]["binding_carried"]
    outcome = "open" if report["findings"] else ("carried" if carried else "closed")
    return _report(outcome, report["findings"], **report["summary"])


def check_decision_witness(project: Path, factory: Path | None = None) -> dict[str, Any]:
    import design_decision_witness

    report = design_decision_witness.coverage(project, factory)
    outcome = ("not_checked" if report["findings"] and all(f.get("outcome") == "not_checked" for f in report["findings"])
               else "open" if report["findings"] else "closed")
    return _report(outcome, report["findings"], **report["summary"])


def check_witness_material(project: Path, factory: Path | None = None) -> dict[str, Any]:
    """A binding made at State 2 is judged there: its check's content must be readable whole."""
    import design_decision_witness

    materials = design_decision_witness.binding_material(project, factory)
    missing = [m for m in materials if m["status"] != "available"]
    findings = [{"severity": "error", "code": "witness_material_not_checked", "outcome": "not_checked",
                 "decision": m["decision"], "witness": m["witness"],
                 "message": (f"{m['decision']}: whether {m['witness']} asserts {', '.join(m['invariants']) or 'its invariant'} "
                             f"cannot be judged: {m.get('reason')} — not checked is not a pass")} for m in missing]
    return _report("not_checked" if findings else "closed", findings, bindings=len(materials),
                   available=len(materials) - len(missing))


CHECKS: dict[str, Callable[[Path], dict[str, Any]]] = {
    "witness_material": check_witness_material,
    "model_closure": check_model_closure,
    "time_source": check_time_source,
    "ambient_time": check_ambient_time,
    "flow_steps": check_flow_steps,
    "flow_reachability": check_flow_reachability,
    "invariant_tests": check_invariant_tests,
    "decision_witness": check_decision_witness,
}


# ---------------------------------------------------------------- known gaps

def known_gaps(path: Path = KNOWN_GAPS_FILE) -> dict[str, set[str]]:
    """KG id -> the finding codes the gap makes uncloseable by the author."""
    gaps: dict[str, set[str]] = {}
    current = None
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return gaps
    for line in lines:
        heading = GAP_HEADING.match(line)
        if heading:
            current = heading.group(1)
            gaps[current] = set()
            continue
        codes = GAP_CODES.match(line.strip())
        if current and codes:
            gaps[current] |= {c.strip(" `") for c in codes.group(1).split(",") if c.strip(" `")}
    return gaps


def cited_gaps(project: Path) -> set[str]:
    """The known gaps a case's design documents cite as ``[known_gap: KG-nnn]``."""
    cited: set[str] = set()
    for path in sorted(project.glob("*.md")):
        try:
            cited |= set(KNOWN_GAP_TAG.findall(path.read_text(encoding="utf-8")))
        except OSError:
            continue
    return cited


def classify(project: Path, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Mark the findings a cited known gap explains as ``workbench_gap``. They still stop."""
    gaps = known_gaps()
    codes = {code: gap for gap in cited_gaps(project) for code in gaps.get(gap, ())}
    result = []
    for finding in findings:
        gap = codes.get(str(finding.get("code")))
        if gap and isinstance(finding, dict):
            finding = {**finding, "outcome": "workbench_gap", "known_gap": gap,
                       "hint": (f"Workbench gap {gap} (skills/spec-authoring/KNOWN_GAPS.md): the standard has no form "
                                "for this decision. Do not change the service's behaviour to satisfy the check; "
                                "the gap is closed by a decision of the standard's owner.")}
        result.append(finding)
    return result


# ---------------------------------------------------------------- running

# The checks that read a Factory checkout; run_check hands them the one the caller chose.
FACTORY_CHECKS = frozenset({"decision_witness", "witness_material"})


def run_check(project: Path, name: str, factory: Path | None = None) -> dict[str, Any]:
    """Run one check. `factory` is the Factory checkout the witness checks read;
    None keeps their own discovery (SPEC_WORKBENCH_FACTORY_ROOT or the sibling)."""
    function = CHECKS.get(name)
    if function is None:
        return _report("workbench_gap", [{"severity": "error", "code": "transition_check_unknown",
                                          "outcome": "workbench_gap",
                                          "message": f"the sequence names check {name!r}, which the Workbench does not have"}])
    try:
        report = function(project, factory) if name in FACTORY_CHECKS and factory is not None else function(project)
    except Exception as exc:  # an input that cannot be read is an input that does not exist
        return _not_checked("transition_check_failed", f"check {name} could not read its inputs ({exc})")
    findings = classify(project, report["findings"])
    outcome = report["outcome"]
    if findings and all(f.get("outcome") == "workbench_gap" for f in findings):
        outcome = "workbench_gap"
    return {**report, "findings": findings, "outcome": outcome}


def blocking(result: dict[str, Any]) -> bool:
    return result["outcome"] not in {"closed", "carried"}


def run_phase(project: Path, phase_id: str, sequence: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run what closes at `phase_id`: its own checks, and every obligation carried to it."""
    sequence = sequence or load_sequence()
    results = []
    for name in own_checks(sequence, phase_id):
        results.append({"check": name, "from": phase_id, "obligation": "owned by this layer", **run_check(project, name)})
    for item in received(sequence, phase_id):
        results.append({"id": item.get("id"), "check": item["check"], "from": item["from"],
                        "obligation": item.get("obligation", ""), **run_check(project, item["check"])})
    stops = [r for r in results if blocking(r)]
    findings = [{**f, "carried_from": r["from"], "check": r["check"]} for r in stops for f in r["findings"]]
    return {"schema_version": SCHEMA, "phase": phase_id, "ready": not stops, "results": results,
            "findings": findings,
            "summary": {"checks": len(results), "blocking": len(stops),
                        **{o: sum(r["outcome"] == o for r in results) for o in OUTCOMES}}}


def state_phases(sequence: dict[str, Any], state: int) -> list[str]:
    return [p["id"] for p in _phases(sequence) if p.get("semantic_state") == state]


def run_state(project: Path, state: int, sequence: dict[str, Any] | None = None) -> dict[str, Any]:
    """Everything that closes at a semantic state's phases."""
    sequence = sequence or load_sequence()
    reports = [run_phase(project, phase, sequence) for phase in state_phases(sequence, state)]
    results = [r for report in reports for r in report["results"]]
    findings = [f for report in reports for f in report["findings"]]
    return {"schema_version": SCHEMA, "state": state, "ready": all(r["ready"] for r in reports),
            "results": results, "findings": findings,
            "summary": {"checks": len(results), "blocking": sum(blocking(r) for r in results),
                        **{o: sum(r["outcome"] == o for r in results) for o in OUTCOMES}}}


def _gate_findings(project: Path, state: int) -> list[dict[str, Any]]:
    """The deterministic findings of a state's own gate, as a round is shown them."""
    from dataclasses import asdict

    if state in (1, 2):
        import design_lint
        return [{"code": f["code"], "severity": f["severity"], "message": f["message"],
                 "item": f.get("item_key")} for f in map(asdict, design_lint.lint_project(project, state=state).findings)]
    gates = {3: ("design_stage3", "lint"), 4: ("design_stage4", "lint"), 5: ("design_stage5", "lint")}
    if state in gates:
        import importlib
        module, name = gates[state]
        return list(getattr(importlib.import_module(module), name)(project).get("findings") or [])
    if state == 7:
        from notes_workbench import gate as notes_gate
        return list(notes_gate.coverage(project).get("findings") or [])
    return []


def round_context(project: Path, state: int, sequence: dict[str, Any] | None = None) -> dict[str, Any]:
    """What a question round of `state` is given besides the texts: the layer it
    asks about, the results of what closes there, and its gate's findings.

    None of it is design text: it is not cut into units and changes no digest,
    so a finding that changes reopens nothing (QUESTIONS.md, units).
    """
    sequence = sequence or load_sequence()
    phases = state_phases(sequence, state)
    owns = [o for phase in phases for o in layer(sequence, phase)["owns"]]
    carries = [c for phase in phases for c in layer(sequence, phase)["carries"]]
    report = run_state(project, state, sequence)
    try:
        gate = [{k: f.get(k) for k in ("code", "severity", "message") if f.get(k) is not None}
                for f in _gate_findings(project, state) if isinstance(f, dict)]
    except Exception as exc:  # the gate cannot read the case: say so, never report it clean
        gate = [{"code": "state_gate_not_checked", "severity": "error",
                 "message": f"the State {state} gate could not read the case ({exc}) — not checked is not a pass"}]
    materials: list[dict[str, Any]] = []
    if "witness_material" in [c for phase in phases for c in own_checks(sequence, phase)]:
        import design_decision_witness
        materials = design_decision_witness.binding_material(project)
    return {"state": state, "owns": owns, "carries": carries, "results": report["results"],
            "ready": report["ready"] and not any(f.get("severity") in {"error", "block"} for f in gate),
            "gate_findings": gate, "materials": materials}


def module_obligations(project: Path, context: dict[str, Any], module: str) -> list[str]:
    """The received obligations one generated module's code takes part in (State 7).

    A State 7 round reads one module's Factory prompt; this is what it is asked
    against besides: a flow step nothing calls in a flow the module takes part
    in (the module may be the caller whose note must name it), a note of the
    module that needs the current time without its source, and every result
    that could not be checked at all. The Factory prompt itself is unchanged.
    """
    import design_stage4

    try:
        spec = json.loads((project / "global_spec.json").read_text(encoding="utf-8"))
        owners = {f: m for m, fs in (spec.get("module_functions") or {}).items() for f in fs or []}
    except (OSError, ValueError, AttributeError):
        owners = {}
    try:
        flows = {flow.key: {ref.removeprefix("capability:").split(".", 1)[0] for ref in flow.capability_refs}
                 for flow in design_stage4.parse_flows(project)}
    except Exception:  # the State 4 gate reports an unreadable flow document
        flows = {}
    lines: list[str] = []
    for result in context.get("results") or []:
        if result["outcome"] in ("closed", "carried"):
            continue
        if result["outcome"] == "not_checked":
            lines += [f"- [not_checked] {f.get('code')}: {f.get('message', '')}" for f in result.get("findings") or []]
            continue
        for finding in result.get("findings") or []:
            code = finding.get("code")
            if code == "flow_capability_unreached" and module in flows.get(str(finding.get("flow")), set()):
                lines.append(f"- [{result['outcome']}] {finding['flow']} needs {finding['capability']}, and nothing a "
                             "route reaches calls it: if this module's code calls it in that flow, a note of the "
                             "calling function must name it")
            elif code == "ambient_time_note" and owners.get(str(finding.get("contract"))) == module:
                lines.append(f"- [{result['outcome']}] {finding.get('message', '')}")
    return lines


def _human(report: dict[str, Any]) -> str:
    where = report.get("phase") or f"State {report.get('state')}"
    lines = [f"transition {where}: ready={str(report['ready']).lower()} {report['summary']}"]
    for result in report["results"]:
        lines.append(f"  [{result['outcome']}] {result['check']} (from {result['from']}): {result['obligation']}")
        for finding in result["findings"][:20]:
            lines.append(f"      {finding.get('code')}: {finding.get('message', '')[:200]}")
        if len(result["findings"]) > 20:
            lines.append(f"      … {len(result['findings']) - 20} more")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("project", type=Path)
    where = parser.add_mutually_exclusive_group(required=True)
    where.add_argument("--phase")
    where.add_argument("--state", type=int)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.project.is_dir():
        print(f"transition: error: project directory not found: {args.project}", file=sys.stderr)
        return 2
    report = run_phase(args.project, args.phase) if args.phase else run_state(args.project, args.state)
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else _human(report))
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
