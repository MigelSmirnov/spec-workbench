"""Obligation projection: derived obligations, node states, frontier, focus, metrics.

An obligation is not stored anywhere.  It is what an already-decided artifact
obliges the corpus to decide next, recomputed on every run from the evidence
graph, the fenced deterministic reports and the factory's dependency report.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import fence
from assembly_workbench.checks import CHECKS

from .evidence import Graph, build
from .registry import TYPES, ObligationType, blocks, classify

FACTORY_ROOT_ENV = "SPEC_WORKBENCH_FACTORY_ROOT"


@dataclass(frozen=True)
class Obligation:
    type: str
    precedence: str
    addressed_to: str
    about: str | None
    caused_by: str
    hint: str
    source: str  # "check:<name>" | "projection" | "factory"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NodeState:
    key: str
    kind: str
    local: str      # "complete" | "open"
    system: str     # "settled" | "blocked"
    obligations: list[Obligation] = field(default_factory=list)
    blocked_by: list[str] = field(default_factory=list)

    @property
    def state(self) -> str:
        if self.system == "blocked":
            return "BLOCKED"
        return "READY" if self.local == "open" else "SETTLED"


@dataclass
class Projection:
    graph: Graph
    obligations: list[Obligation]
    states: dict[str, NodeState]
    factory: dict[str, Any]
    elapsed_seconds: float


# ----------------------------------------------------------------------------- helpers
def _walk(payload: Any, out: list[dict[str, Any]]) -> None:
    if isinstance(payload, dict):
        if "code" in payload and "message" in payload:
            out.append(payload)
        else:
            for value in payload.values():
                _walk(value, out)
    elif isinstance(payload, list):
        for value in payload:
            _walk(value, out)


def _address_from_finding(finding: dict[str, Any], graph: Graph) -> str | None:
    for key in ("module_key", "module", "decision", "capability", "flow", "flow_key",
                "operation", "operation_key", "contract", "function", "scope", "model", "key"):
        value = finding.get(key)
        if isinstance(value, str) and value:
            if key == "decision" and not value.startswith("decision:"):
                return f"decision:{value}"
            if key in {"contract", "function", "scope"} and ":" not in value:
                for node in graph.nodes:
                    if node.startswith(("contract:", "function:")) and node.endswith("." + value):
                        return node
                return f"function:?.{value}"
            if key == "model" and ":" not in value:
                return f"interface:{value}" if f"interface:{value}" in graph.nodes else f"model:{value}"
            return value
    match = re.match(r"([A-Za-z_][\w.]*):", finding.get("message", ""))
    if match:
        name = match.group(1)
        for node in graph.nodes:
            if node.startswith(("contract:", "function:")) and node.endswith("." + name):
                return node
    return None


def _factory_dependency_report(graph: Graph, factory_root: Path | None, factory_project: str | None) -> dict[str, Any]:
    """Edges the factory's local specs carry that the architecture never declared."""
    workbench_root = Path(__file__).resolve().parents[2]
    candidates = [factory_root] if factory_root else []
    if os.environ.get(FACTORY_ROOT_ENV):
        candidates.append(Path(os.environ[FACTORY_ROOT_ENV]))
    # the canonical checkout sits beside the workbench; a worktree sits one level deeper
    candidates += [workbench_root.parent / "code_factory", workbench_root.parent.parent / "code_factory"]
    root = next((c for c in candidates if (c / "tools" / "route_b_affected.py").exists()), None)
    if root is None:
        return {"available": False, "reason": f"factory tools not found; tried {[str(c) for c in candidates]}; set {FACTORY_ROOT_ENV}"}
    tools = root / "tools"
    if str(tools) not in sys.path:
        sys.path.append(str(tools))
    try:
        import route_b_affected as rba  # type: ignore
    except Exception as exc:  # pragma: no cover - environment dependent
        return {"available": False, "reason": f"route_b_affected import failed: {exc}"}
    design_modules = {k.split(":", 1)[1] for k, kind in graph.nodes.items() if kind == "module"}
    candidates: list[tuple[float, Path]] = []
    for spec_path in sorted((root / "projects").glob("*/specs/base/global_spec.json")):
        if factory_project and spec_path.parts[-4] != factory_project:
            continue
        try:
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        modules = set((spec.get("module_functions") or {}).keys())
        overlap = len(modules & design_modules) / max(1, len(design_modules | modules))
        candidates.append((overlap, spec_path))
    if not candidates:
        return {"available": False, "reason": "no factory project matched"}
    overlap, spec_path = max(candidates)
    if overlap < 0.8 and not factory_project:
        return {"available": False, "reason": f"best module overlap {overlap:.2f} < 0.8 ({spec_path.parts[-4]})"}
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    project_dir = spec_path.parents[2]
    import_map = rba.import_to_module_map(spec)
    modules = set(rba.module_paths(spec))
    declared, _, _ = rba.declared_dependency_graph(spec, import_map)
    local, _, _ = rba.dependency_graph(project_dir / "specs" / "local_specs", import_map, modules)
    declared_edges = {(c, p) for c, ps in declared.items() for p in ps if c != p}
    local_edges = {(c, p) for c, ps in local.items() for p in ps if c != p}
    designed = {(c.split(":", 1)[1], p.split(":", 1)[1]) for c, p in graph.edges["module→module"]}
    return {
        "available": True,
        "project": spec_path.parts[-4],
        "module_overlap": round(overlap, 2),
        "declared_edges": len(declared_edges),
        "local_spec_edges": len(local_edges),
        "designed_edges": len(designed),
        "undesigned": sorted((c, p) for c, p in local_edges - designed if p != "models"),
        "designed_but_absent": sorted(designed - local_edges),
    }


# ----------------------------------------------------------------------------- projection
def project(project_dir: Path, *, factory_root: Path | None = None, factory_project: str | None = None) -> Projection:
    started = time.perf_counter()
    graph = build(project_dir)
    obligations: list[Obligation] = []

    def add(kind: ObligationType, to: str, caused_by: str, hint: str | None = None, about: str | None = None, source: str = "projection") -> None:
        obligations.append(Obligation(kind.code, kind.precedence, to, about, caused_by, hint or kind.hint, source))

    caller_of = {row["capability"]: list(row.get("callers", [])) for row in graph.operations}
    # 1. fenced deterministic reports
    for name, report in CHECKS.items():
        raw: list[dict[str, Any]] = []
        _walk(report(project_dir), raw)
        for finding in fence.enforce([dict(item) for item in raw]):
            if finding.get("severity") not in {"error", "block"}:
                continue
            kind = classify(name, finding["code"])
            hint = finding.get("hint") or finding.get("message") or kind.hint
            if finding["code"] == "flow_capability_unreached":
                capability = finding["capability"]
                for caller in caller_of.get(capability) or [f"capability_owner:{capability}"]:
                    add(kind, caller, finding.get("flow") or name, f"make {capability} reachable from {caller}", about=capability, source=f"check:{name}")
                continue
            if finding["code"] == "flow_capability_missing" and finding.get("flow"):
                add(kind, finding["flow"], f"check:{name}", hint, about=finding.get("capability"), source=f"check:{name}")
                continue
            if kind.code == "unclassified_finding":
                graph.node("registry:obligations", "registry")
                add(kind, "registry:obligations", f"check:{name}", f"[{finding['code']}] {hint}", source=f"check:{name}")
                continue
            address = _address_from_finding(finding, graph)
            if address is None or address not in graph.nodes:
                # a finding with no design node: the check itself is the addressee, truthfully
                address = graph.node(f"check:{name}", "check")
            add(kind, address, f"check:{name}", hint, source=f"check:{name}")
    # 2. graph-derived obligations
    for decision_key, row in graph.decisions.items():
        if not row.get("primary_owner"):
            add(TYPES["decision_without_owner"], f"decision:{decision_key}", "State 2 acceptance")
    for name, declaration in graph.spec_models.items():
        if name not in graph.closure_models:
            kind = "interface" if declaration.get("kind") in {"interface", "protocol"} else "model"
            add(TYPES["model_without_design_source"], f"{kind}:{name}", "spec projection overlay")
    for contract_key, type_name in sorted(graph.unresolved_types):
        add(TYPES["contract_type_without_model"], contract_key, f"signature names {type_name}",
            f"{type_name} is not a closed model or interface", about=type_name)
    # boundaries and ingress
    prefix_to_boundary: dict[str, str] = {}
    for op_key, item in graph.routes.items():
        prefix = (item.get("path") or "/").split("/")[1] if "/" in (item.get("path") or "") else ""
        callers = next((r.get("callers", []) for r in graph.operations if r["key"] == op_key), [])
        boundaries = [c for c in callers if c.startswith("boundary:")]
        if len(boundaries) == 1 and prefix:
            prefix_to_boundary.setdefault(prefix, boundaries[0])
    for row in graph.operations:
        boundaries = [c for c in row.get("callers", []) if c.startswith("boundary:")]
        if boundaries and row["key"] not in graph.routes:
            for boundary in boundaries:
                add(TYPES["boundary_without_ingress"], boundary, row["key"],
                    f"no route carries {row['key']} for {boundary}", about=row["key"])
    for op_key, item in graph.routes.items():
        callers = next((r.get("callers", []) for r in graph.operations if r["key"] == op_key), [])
        prefix = (item.get("path") or "/").split("/")[1] if "/" in (item.get("path") or "") else ""
        boundary = prefix_to_boundary.get(prefix, f"boundary:{prefix or '?'}")
        if boundary not in callers:
            graph.node(boundary, "boundary")
            add(TYPES["ingress_without_designed_caller"], boundary, op_key,
                f"route {item.get('method')} {item.get('path')} serves {op_key}; State 5 callers are {callers}", about=op_key)
    # State 0 outcomes proven by flows
    outcomes_text = "\n".join(graph.flow_outcomes_text.values()).lower()
    for key, kind in list(graph.nodes.items()):
        if kind == "outcome" and key.split(":", 1)[1].lower() not in outcomes_text:
            add(TYPES["outcome_without_flow"], key, "State 0 observable outcome")
    # factory parity
    factory = _factory_dependency_report(graph, factory_root, factory_project)
    for consumer, provider in factory.get("undesigned", []):
        for name in (consumer, provider):
            if f"module:{name}" not in graph.nodes:
                graph.node(f"module:{name}", "factory_module")  # the factory has it; State 3 never declared it
        add(TYPES["dependency_not_designed"], f"module:{consumer}", f"factory local spec infers {consumer}→{provider}",
            f"declare imports.module_internal.{consumer}.{provider} by decision, or move the shared symbol", about=f"module:{provider}", source="factory")

    # 3. states with precedence by obligation class
    open_on: dict[str, list[Obligation]] = defaultdict(list)
    for obligation in obligations:
        open_on[obligation.addressed_to].append(obligation)
    defining_open = {node for node, items in open_on.items() if any(blocks(TYPES[o.type]) for o in items)}
    # derived cost: models with defining obligations → radius over contracts
    for node in sorted(defining_open):
        if graph.nodes.get(node) in {"model", "interface"}:
            modules = {src.split(":", 1)[1].split(".", 1)[0] for src, dst in graph.edges["contract→model"] if dst == node}
            if modules:
                cost = Obligation("model_closure_radius", "derived_cost", node, None, "closing this model",
                                  f"contracts in {len(modules)} module(s) reference it: {', '.join(sorted(modules))}", "projection")
                obligations.append(cost)
                open_on[node].append(cost)

    def blockers(node: str, seen: set[str]) -> list[str]:
        found: list[str] = []
        for target in sorted(graph.definitional_targets(node)):
            if target in seen:
                continue
            seen.add(target)
            if target in defining_open:
                found.append(target)
            found.extend(blockers(target, seen))
        return found

    states: dict[str, NodeState] = {}
    for key, kind in graph.nodes.items():
        mine = [o for o in open_on.get(key, []) if o.precedence != "derived_cost"]
        external = sorted(set(blockers(key, {key})))
        states[key] = NodeState(key, kind, "open" if mine else "complete", "blocked" if external else "settled",
                                open_on.get(key, []), external)
    return Projection(graph, obligations, states, factory, time.perf_counter() - started)


# ----------------------------------------------------------------------------- views
_PRECEDENCE_ORDER = {"defining": 0, "convergence": 1, "implementation": 2, "derived_cost": 3}


def _node_payload(state: NodeState) -> dict[str, Any]:
    return {
        "node": state.key, "kind": state.kind, "state": state.state, "local": state.local, "system": state.system,
        "blocked_by": state.blocked_by, "obligations": [o.as_dict() for o in state.obligations],
    }


def frontier(projection: Projection) -> dict[str, Any]:
    ready = [s for s in projection.states.values() if s.state == "READY"]
    blocked = [s for s in projection.states.values() if s.state == "BLOCKED"]
    ready.sort(key=lambda s: (min(_PRECEDENCE_ORDER[o.precedence] for o in s.obligations), -len(s.obligations), s.key))
    blocked.sort(key=lambda s: (s.kind, s.key))
    counts = Counter(s.state for s in projection.states.values())
    return {
        "schema_version": "spec_workbench_obligations_frontier.v1",
        "project_root": projection.graph.project.name,
        "summary": {"ready": counts["READY"], "blocked": counts["BLOCKED"], "settled": counts["SETTLED"],
                    "obligations": len(projection.obligations)},
        "ready": [_node_payload(s) for s in ready],
        "blocked": [_node_payload(s) for s in blocked],
    }


def listing(projection: Projection) -> dict[str, Any]:
    return {
        "schema_version": "spec_workbench_obligations_list.v1",
        "project_root": projection.graph.project.name,
        "obligations": [o.as_dict() for o in sorted(projection.obligations, key=lambda o: (_PRECEDENCE_ORDER[o.precedence], o.type, o.addressed_to))],
    }


def focus(projection: Projection, node: str) -> dict[str, Any]:
    if node not in projection.states:
        raise KeyError(node)
    graph = projection.graph
    state = projection.states[node]
    owned = graph.owned_by(node) if graph.nodes[node] == "module" else []
    owned_states = [projection.states[k] for k in owned]
    named_here = {node, *owned}
    naming = [o for o in projection.obligations if o.addressed_to not in named_here and o.about in named_here]
    return {
        "schema_version": "spec_workbench_obligations_focus.v1",
        "node": _node_payload(state),
        "owned": {"counts": dict(Counter(s.state for s in owned_states)),
                  "open": [_node_payload(s) for s in owned_states if s.state != "SETTLED"]},
        "external_blockers": state.blocked_by,
        "named_by_others": [o.as_dict() for o in naming],
    }


def metrics(projection: Projection) -> dict[str, Any]:
    nodes = projection.graph.nodes
    addressed = sum(1 for o in projection.obligations if o.addressed_to in nodes)
    counts = Counter(s.state for s in projection.states.values())
    return {
        "schema_version": "spec_workbench_obligations_metrics.v1",
        "project_root": projection.graph.project.name,
        "nodes": dict(Counter(nodes.values())),
        "edges": {kind: len(edges) for kind, edges in projection.graph.edges.items()},
        "obligations": len(projection.obligations),
        "by_type": dict(Counter(o.type for o in projection.obligations)),
        "by_precedence": dict(Counter(o.precedence for o in projection.obligations)),
        "states": {"ready": counts["READY"], "blocked": counts["BLOCKED"], "settled": counts["SETTLED"]},
        "addressability": {"addressed": addressed, "total": len(projection.obligations),
                           "unaddressed": sorted({o.addressed_to for o in projection.obligations if o.addressed_to not in nodes})},
        "unclassified": [o.hint for o in projection.obligations if o.type == "unclassified_finding"],
        "factory": projection.factory,
        "elapsed_seconds": round(projection.elapsed_seconds, 2),
    }
