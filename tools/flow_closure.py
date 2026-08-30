"""Flow closure: every capability a State 4 flow names is declared and wired.

A flow is the design's own statement of what the system does end to end. A
flow step that names ``capability:module.operation`` is closed only when the
operation is planned and contracted (State 6) and when something outside the
owning module is obliged to call it: a route delegate in the router IR, or a
note of another module that names it. An operation the flows depend on but
nothing calls is the assembly quietly bypassing the design — the case stops.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import design_stage4
import design_stage6_contracts
import fence

SCHEMA = "spec_workbench_flow_closure.v1"
NOTES_FILE = "80_notes.md"
SPEC_FILE = "global_spec.json"
NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _plan_functions(project: Path) -> dict[str, str]:
    """function name (bare or Class.method) -> owning module."""
    plan = design_stage6_contracts.load_plan(project)
    owners: dict[str, str] = {}
    for entry in plan["functions"]:
        if isinstance(entry, dict) and isinstance(entry.get("function"), str):
            owners[entry["function"]] = str(entry.get("module") or "").removeprefix("module:")
    return owners


def _contracts(project: Path) -> dict[str, Any]:
    try:
        return design_stage6_contracts.load_catalog(project)["contracts"]
    except design_stage6_contracts.DesignStage6ContractsError:
        return {}


def _route_callees(project: Path) -> set[str]:
    path = project / SPEC_FILE
    if not path.is_file():
        return set()
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    ir = ((spec.get("rules") or {}).get("http_router_backend") or {})
    callees: set[str] = set()
    for route in ir.get("routes") or []:
        delegate = route.get("delegate") or {}
        if isinstance(delegate.get("function"), str):
            callees.add(delegate["function"])
        for step in route.get("authorize") or []:
            if isinstance(step, dict) and isinstance(step.get("function"), str):
                callees.add(step["function"])
    for principal in (ir.get("principals") or {}).values():
        if isinstance(principal, dict) and isinstance(principal.get("resolver"), str):
            callees.add(principal["resolver"])
    return callees


def _note_calls(project: Path, owners: dict[str, str]) -> dict[str, set[str]]:
    """scope function -> planned operations its notes name (the calls a note obliges)."""
    path = project / NOTES_FILE
    calls: dict[str, set[str]] = {}
    if not path.is_file():
        return calls
    for line in path.read_text(encoding="utf-8").split("\n"):
        if ":" not in line or line.startswith("#"):
            continue
        scope, body = line.split(":", 1)
        scope_key = scope if scope in owners else scope.split(".", 1)[0]
        if scope_key not in owners:
            continue
        for name in set(NAME_RE.findall(body)):
            if name in owners and name != scope_key:
                calls.setdefault(scope_key, set()).add(name)
    return calls


def _reachable(route_callees: set[str], note_calls: dict[str, set[str]]) -> set[str]:
    """Everything a route reaches through the calls the notes oblige, transitively."""
    reached = set(route_callees)
    frontier = list(route_callees)
    while frontier:
        current = frontier.pop()
        for callee in note_calls.get(current, ()):
            if callee not in reached:
                reached.add(callee)
                frontier.append(callee)
    return reached


def coverage(project: Path) -> dict[str, Any]:
    project = Path(project)
    flows = design_stage4.parse_flows(project)
    owners = _plan_functions(project)
    contracts = _contracts(project)
    route_callees = _route_callees(project)
    reached = _reachable(route_callees, _note_calls(project, owners))
    findings: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    references = 0
    for flow in flows:
        for ref in flow.capability_refs:
            references += 1
            module, operation = ref.removeprefix("capability:").split(".", 1)
            key = (flow.key, ref)
            if key in seen:
                continue
            seen.add(key)
            declared = owners.get(operation) == module or any(
                symbol.startswith(operation + ".") and owners.get(symbol) == module for symbol in owners
            )
            contracted = operation in contracts or any(symbol.startswith(operation + ".") for symbol in contracts)
            if not (declared and contracted):
                findings.append({
                    "severity": "error", "code": "flow_capability_missing", "flow": flow.key,
                    "capability": ref,
                    "message": f"{flow.key} names {ref}, which is not planned and contracted under module:{module}",
                })
                continue
            obliged = operation in reached
            if not obliged:
                findings.append({
                    "severity": "error", "code": "flow_capability_unreached", "flow": flow.key,
                    "capability": ref,
                    "message": (
                        f"{flow.key} depends on {ref}, but nothing a route reaches names it in a note: "
                        f"the assembly bypasses this step"
                    ),
                })
    findings = fence.enforce(findings)
    errors = fence.stops(findings)
    return {
        "schema_version": SCHEMA,
        "project_root": project.resolve().name,
        "summary": {"flows": len(flows), "capability_references": references, "errors": errors, "handoff_ready": errors == 0},
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = coverage(args.project)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        summary = report["summary"]
        print(f"flow closure: {summary['flows']} flows, {summary['capability_references']} references, {summary['errors']} stop(s)")
        for item in report["findings"]:
            print(f"  STOP {item['code']} {item['capability']} — {item['hint']}")
    return 1 if report["summary"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
