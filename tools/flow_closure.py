"""Flow closure: every capability a State 4 flow names is declared and wired.

A flow is the design's own statement of what the system does end to end. A
flow step that names ``capability:module.operation`` is closed only when the
operation is planned and contracted (State 6) and when something outside the
owning module is obliged to call it: a route delegate in the router IR, a
note of another module that names it, or a deterministic backend that emits
the call. An operation the flows depend on but nothing calls is the assembly
quietly bypassing the design — the case stops.

The two halves belong to two layers (skills/spec-authoring/TRANSITION_PROTOCOL.md):
``steps`` — declared and contracted — needs only the State 6 plan and catalog
and is checked at the State 6 handoff; ``reachability`` needs the notes and
the router and is checked at the State 7 handoff. A call is read where the
design states it:

- a note names the callee: bare (``create_audit_schema``), dotted
  (``PortalStore.begin``), or through a parameter of the scope's own contract
  (``store.begin()`` where the contract reads ``store: PortalStore``);
- a deterministic backend emits it (SPEC_STANDARD 6.12): the unit-of-work
  store's ``begin`` creates the schema of every accessor's repository, the
  bootstrap store's operation creates the schemas of the repositories it writes
  and calls their insert methods, the bootstrap port's operation is the
  bootstrap class's, and an accessor interface's methods are its repository's.
  No note is required for a call the emitter writes.

Reachability whose roots cannot be read — a router is authored but neither an
assembled ``rules.http_router_backend`` nor a ready router closure exists — is
``not_checked``: a stop, never a pass.
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
DOTTED_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\b")
TYPE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


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


def _load_spec(project: Path) -> dict[str, Any] | None:
    path = project / SPEC_FILE
    if not path.is_file():
        return None
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return spec if isinstance(spec, dict) else None


def _router_ir(project: Path) -> tuple[dict[str, Any] | None, str | None]:
    """The router IR the roots are read from, or None and why it is unreadable.

    (None, None): the case authors no router, so it has no HTTP root.
    """
    spec = _load_spec(project)
    assembled = ((spec or {}).get("rules") or {}).get("http_router_backend")
    if isinstance(assembled, dict):
        return assembled, None
    from router_workbench.model import CATALOG_FILE as ROUTER_CLOSURE_FILE
    import design_router_context
    if not ((project / ROUTER_CLOSURE_FILE).is_file() or (project / design_router_context.FILE).is_file()):
        return None, None
    try:
        import design_router_ir
        return design_router_ir.assemble(project)["rules"]["http_router_backend"], None
    except Exception as exc:  # the router gates report their own findings
        return None, f"the router is authored but its IR is neither assembled nor assemblable ({exc})"


def _route_callees(project: Path) -> set[str]:
    return _callees_of(_router_ir(project)[0] or {})


def _callees_of(ir: dict[str, Any]) -> set[str]:
    callees: set[str] = set()
    for route in ir.get("routes") or []:
        delegate = route.get("delegate") or {}
        if isinstance(delegate.get("function"), str):
            callees.add(delegate["function"])
        # an irregular route has no lowered delegate: its companion-module handler is the entry the route reaches
        if route.get("emission") == "irregular" and isinstance(route.get("handler"), str):
            callees.add(route["handler"])
        for step in route.get("authorize") or []:
            if isinstance(step, dict) and isinstance(step.get("function"), str):
                callees.add(step["function"])
    for principal in (ir.get("principals") or {}).values():
        if isinstance(principal, dict) and isinstance(principal.get("resolver"), str):
            callees.add(principal["resolver"])
    return callees


def _parameter_types(signature: Any) -> dict[str, str]:
    """parameter -> the one class it is annotated with (``X``, ``X | None``, ``Optional[X]``)."""
    params, _, _ = str(signature or "").partition("->")
    params = params.strip()
    if params.startswith("(") and params.endswith(")"):
        params = params[1:-1]
    parts, depth, current = [], 0, ""
    for char in params:
        depth += char in "[("
        depth -= char in "])"
        if char == "," and depth == 0:
            parts.append(current)
            current = ""
        else:
            current += char
    parts.append(current)
    found: dict[str, str] = {}
    for part in parts:
        name, colon, annotation = part.partition(":")
        if not colon:
            continue
        annotation = annotation.split("=", 1)[0].strip()
        if annotation.startswith("Optional[") and annotation.endswith("]"):
            annotation = annotation[len("Optional["):-1].strip()
        names = [a.strip() for a in annotation.split("|") if a.strip() != "None"]
        if len(names) == 1 and TYPE_NAME_RE.match(names[0]):
            found[name.strip().lstrip("*")] = names[0]
    return found


def _backend_calls(project: Path, owners: dict[str, str], contracts: dict[str, Any]) -> dict[str, set[str]]:
    """Calls deterministic backends emit (SPEC_STANDARD 6.12 over 6.2/6.3): caller -> callees.

    Read from the closed closure artifacts (or, once assembled, the rules they
    project into); a backend that is not closed contributes nothing.
    """
    import standard_backends
    from persistence_workbench.model import CATALOG_FILE as PERSISTENCE_FILE

    spec_rules = (_load_spec(project) or {}).get("rules") or {}
    unit = next((b for b in standard_backends.STANDARD_BACKENDS if b.id == "sqlite_unit_of_work"), None)
    uow = (unit.authored_backend(project) if unit else None) or spec_rules.get("sqlite_unit_of_work_backend")
    persistence = spec_rules.get("persistence_backend")
    try:
        closure = json.loads((project / PERSISTENCE_FILE).read_text(encoding="utf-8"))
        if isinstance(closure, dict) and isinstance(closure.get("backend_ir"), dict):
            persistence = closure["backend_ir"]
    except (OSError, ValueError):
        pass
    if not isinstance(uow, dict) or not isinstance(persistence, dict):
        return {}
    repositories = {str(r.get("repository")): r for r in persistence.get("repositories") or [] if isinstance(r, dict)}
    calls: dict[str, set[str]] = {}

    def edge(caller: str, callee: Any) -> None:
        if isinstance(callee, str) and callee in owners:
            calls.setdefault(caller, set()).add(callee)

    wiring = uow.get("wiring") or {}
    store, transaction = wiring.get("store_class"), wiring.get("transaction_class")
    for accessor in uow.get("accessors") or []:
        repository = repositories.get(str(accessor.get("repository")))
        if not repository:
            continue
        edge(f"{store}.begin", repository.get("schema_function"))  # schema: create_on_begin_in_accessor_order
        interface = str(contracts.get(f"{transaction}.{accessor.get('accessor')}", "")).partition("->")[2].strip()
        for symbol in owners:
            if interface and symbol.startswith(interface + "."):
                method = symbol.split(".", 1)[1]
                edge(symbol, f"{repository['repository']}.{method}")
                edge(f"{transaction}.{method}", f"{repository['repository']}.{method}")
    bootstrap = uow.get("bootstrap_store")
    if isinstance(bootstrap, dict):
        operation = f"{bootstrap.get('class')}.{bootstrap.get('operation')}"
        edge(f"{bootstrap.get('port')}.{bootstrap.get('operation')}", operation)
        for write in bootstrap.get("writes") or []:
            repository = repositories.get(str(write.get("repository")))
            if repository:  # schema: create_for_written_repositories
                edge(operation, repository.get("schema_function"))
                edge(operation, f"{repository['repository']}.{write.get('method')}")
    return calls


def _note_calls(project: Path, owners: dict[str, str], contracts: dict[str, Any] | None = None) -> dict[str, set[str]]:
    """scope function -> planned operations its notes name (the calls a note obliges).

    A callee is named bare, dotted as ``Class.method``, or through a parameter
    of the scope's own contract (``store.begin()`` with ``store: PortalStore``).
    """
    path = project / NOTES_FILE
    if not path.is_file():
        return {}
    return note_call_edges(path.read_text(encoding="utf-8").split("\n"), owners, contracts)


def note_call_edges(lines: list[str], owners: dict[str, str],
                    contracts: dict[str, Any] | None = None) -> dict[str, set[str]]:
    """The calls a list of note lines (``scope: body``) obliges: scope -> callees."""
    calls: dict[str, set[str]] = {}
    contracts = contracts or {}
    for line in lines:
        line = str(line)
        if ":" not in line or line.startswith("#"):
            continue
        scope, body = line.split(":", 1)
        scope_key = scope if scope in owners else scope.split(".", 1)[0]
        if scope_key not in owners:
            continue
        named = {name for name in NAME_RE.findall(body) if name in owners}
        receivers = _parameter_types(contracts.get(scope_key) or contracts.get(scope))
        for receiver, method in DOTTED_RE.findall(body):
            for candidate in (f"{receiver}.{method}", f"{receivers.get(receiver, '')}.{method}"):
                if candidate in owners:
                    named.add(candidate)
        for name in named - {scope_key}:
            calls.setdefault(scope_key, set()).add(name)
    return calls


def _non_http_ingress_roots(project: Path) -> set[str]:
    """Public operations a boundary calls that State 5 deliberately keeps off HTTP.

    A boundary caller plus an ``internal-only`` exposure is a recorded pair of
    decisions: the boundary exists (State 5) and it is not a route (exposure).
    The only consistent reading is a non-HTTP ingress — the protected
    composition root, an operator command on the host — so these operations
    are reachability roots exactly like route delegates.
    """
    try:
        import design_stage5
        import design_stage5_exposure
    except ImportError:  # pragma: no cover
        return set()
    exposure_path = project / design_stage5_exposure.DEFAULT_FILE if hasattr(design_stage5_exposure, "DEFAULT_FILE") else project / "50_exposure_plan.json"
    internal_only: set[str] = set()
    try:
        ops = (json.loads(exposure_path.read_text(encoding="utf-8")).get("operations") or {})
        internal_only = {key for key, value in ops.items() if value == "internal-only"}
    except (OSError, ValueError):
        return set()
    roots: set[str] = set()
    try:
        rows = design_stage5.coverage(project).get("operations", [])
    except Exception:  # pragma: no cover - the State 5 lint reports its own errors
        return roots
    for row in rows:
        callers = row.get("callers") or []
        if callers and all(str(c).startswith("boundary:") for c in callers) and row["key"] in internal_only:
            roots.add(row["key"].split(".", 1)[1])
    return roots


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


def coverage(project: Path, *, reachability: bool = True) -> dict[str, Any]:
    """Flow closure. ``reachability=False`` checks only that every step is
    planned and contracted — the State 6 half, which needs no notes."""
    project = Path(project)
    flows = design_stage4.parse_flows(project)
    owners = _plan_functions(project)
    contracts = _contracts(project)
    findings: list[dict[str, Any]] = []
    reached: set[str] = set()
    roots_unreadable = None
    if reachability:
        ir, roots_unreadable = _router_ir(project)
        route_callees = _callees_of(ir or {}) | _non_http_ingress_roots(project)
        calls = _note_calls(project, owners, contracts)
        for caller, callees in _backend_calls(project, owners, contracts).items():
            calls.setdefault(caller, set()).update(callees)
        reached = _reachable(route_callees, calls)
        if roots_unreadable:
            findings.append({
                "severity": "error", "code": "flow_reachability_not_checked", "outcome": "not_checked",
                "message": f"flow reachability is not checked: {roots_unreadable}; not checked is not a pass",
            })
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
            if not reachability or roots_unreadable:
                continue
            if operation not in reached:
                findings.append({
                    "severity": "error", "code": "flow_capability_unreached", "flow": flow.key,
                    "capability": ref,
                    "message": (
                        f"{flow.key} depends on {ref}, but nothing a route reaches calls it — no note names it "
                        f"and no deterministic backend emits the call: the assembly bypasses this step"
                    ),
                })
    findings = fence.enforce(findings)
    errors = fence.stops(findings)
    return {
        "schema_version": SCHEMA,
        "project_root": project.resolve().name,
        "summary": {"flows": len(flows), "capability_references": references, "errors": errors,
                    "reachability": "checked" if reachability and not roots_unreadable
                    else ("not_checked" if reachability else "not_asked"),
                    "handoff_ready": errors == 0},
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
            print(f"  STOP {item['code']} {item.get('capability', '')} — {item['hint']}")
    return 1 if report["summary"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
