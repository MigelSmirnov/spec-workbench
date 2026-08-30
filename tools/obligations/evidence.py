"""Evidence layer: nodes and edges read from the existing artifacts.

Only facts the artifacts already state become edges.  Nothing is inferred
here; inference (an obligation) happens in ``projection``.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import design_stage3
import design_stage4
import design_stage5
import design_stage6_contracts
import design_trace

NODE_KINDS = ("decision", "model", "interface", "boundary", "actor", "outcome",
              "module", "capability", "flow", "public_op", "function", "contract")

# Edges that define a node in terms of another: an open *defining* obligation on
# the target blocks the source.
DEFINITIONAL_EDGES = ("capability→module", "public_op→capability", "public_op→flow",
                      "function→public_op", "contract→function", "contract→model")

_TYPE_SKIP = {"None", "Optional", "Sequence", "Mapping", "Iterable", "Iterator", "Callable",
              "Protocol", "Any", "Self", "AsyncIterator", "Awaitable", "Union", "Literal"}


@dataclass
class Graph:
    project: Path
    nodes: dict[str, str] = field(default_factory=dict)
    edges: dict[str, set[tuple[str, str]]] = field(default_factory=lambda: defaultdict(set))
    decisions: dict[str, dict[str, Any]] = field(default_factory=dict)
    operations: list[dict[str, Any]] = field(default_factory=list)
    functions: list[dict[str, Any]] = field(default_factory=list)
    routes: dict[str, dict[str, Any]] = field(default_factory=dict)
    closure_models: dict[str, dict[str, Any]] = field(default_factory=dict)
    spec_models: dict[str, dict[str, Any]] = field(default_factory=dict)
    flow_outcomes_text: dict[str, str] = field(default_factory=dict)
    unresolved_types: set[tuple[str, str]] = field(default_factory=set)  # (contract, type name)

    def node(self, key: str, kind: str) -> str:
        self.nodes.setdefault(key, kind)
        return key

    def edge(self, kind: str, src: str, dst: str) -> None:
        self.edges[kind].add((src, dst))

    def owner_module(self, key: str) -> str | None:
        kind, _, rest = key.partition(":")
        if kind == "module":
            return key
        if kind in {"capability", "public_op", "function", "contract"}:
            return f"module:{rest.split('.', 1)[0]}"
        if kind == "decision":
            return self.decisions.get(rest, {}).get("primary_owner")
        return None

    def owned_by(self, module_key: str) -> list[str]:
        return [n for n in self.nodes if n != module_key and self.owner_module(n) == module_key]

    def definitional_targets(self, key: str) -> set[str]:
        out: set[str] = set()
        for kind in DEFINITIONAL_EDGES:
            out.update(dst for src, dst in self.edges[kind] if src == key)
        return out


def _capability_key(ref: Any) -> str | None:
    if isinstance(ref, str):
        return ref
    if isinstance(ref, dict):
        return ref.get("key") or ref.get("ref") or ref.get("capability")
    return None


def _section_text(lines: list[str], heading: str) -> str:
    out: list[str] = []
    active = False
    for line in lines:
        if re.match(r"^#{2,4}\s", line):
            active = line.strip("# \n").lower() == heading.lower()
            continue
        if active:
            out.append(line)
    return "\n".join(out)


def _state0_roots(graph: Graph) -> None:
    path = graph.project / "00_product.md"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    for section, kind in (("Actors", "actor"), ("Observable outcomes", "outcome")):
        match = re.search(rf"^## {re.escape(section)}\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
        if not match:
            continue
        for heading in re.findall(r"^### (.+)$", match.group(1), re.M):
            graph.node(f"{kind}:{heading.strip().strip('`')}", kind)


def build(project: Path) -> Graph:
    graph = Graph(project=project)
    # State 3: modules and their capability names
    for module in design_stage3.handoff(project).get("modules", []):
        graph.node(module["key"], "module")
        for ref in module.get("capability_refs", []):
            key = _capability_key(ref)
            if key:
                graph.node(key, "capability")
                graph.edge("module→capability", module["key"], key)
                graph.edge("capability→module", key, module["key"])
    # State 2 → trace: decisions and owners
    trace = design_trace.analyze(project)
    graph.decisions = dict(trace.get("decisions", {}))
    unclaimed = trace.get("unclaimed_state2_decisions", [])
    for item in (unclaimed if isinstance(unclaimed, list) else list(unclaimed)):
        key = item if isinstance(item, str) else (item.get("key") or item.get("decision") or item.get("id"))
        if key and key not in graph.decisions:
            graph.decisions[key] = {"primary_owner": None, "consumers": [], "unclaimed": True}
    for decision_key, row in graph.decisions.items():
        graph.node(f"decision:{decision_key}", "decision")
        if row.get("primary_owner"):
            graph.edge("decision→owner", f"decision:{decision_key}", row["primary_owner"])
    # State 4: flows
    flow_lines = (project / "40_flows.md").read_text(encoding="utf-8").splitlines() if (project / "40_flows.md").exists() else []
    for item in design_stage4.parse_flows(project):
        graph.node(item.key, "flow")
        block = flow_lines[item.source.start_line - 1: item.source.end_line]
        graph.flow_outcomes_text[item.key] = _section_text(block, "Outcomes")
    for row in design_stage4.coverage(project).get("flows", []):
        graph.node(row["key"], "flow")
        for module_key in row.get("required_modules", []):
            graph.edge("flow→module", row["key"], module_key)
        for capability in row.get("candidate_capabilities", []):
            graph.edge("flow→capability", row["key"], capability)
    # State 5: public operations, callers (modules or boundaries)
    graph.operations = design_stage5.coverage(project).get("operations", [])
    for row in graph.operations:
        graph.node(row["key"], "public_op")
        graph.edge("public_op→capability", row["key"], row["capability"])
        for flow_key in row.get("flows", []):
            graph.edge("public_op→flow", row["key"], flow_key)
        for caller in row.get("callers", []):
            graph.node(caller, "boundary" if caller.startswith("boundary:") else "module")
            graph.edge("public_op→caller", row["key"], caller)
    # models: closure files are the design source; global_spec.json is the projection
    for path in sorted(project.glob("60_model_closure_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        graph.closure_models.update(payload.get("models", {}))
    spec_path = project / "global_spec.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8")) if spec_path.exists() else {}
    graph.spec_models = {n: d for n, d in (spec.get("models") or {}).items() if isinstance(d, dict)}
    for name, declaration in {**graph.closure_models, **graph.spec_models}.items():
        if not isinstance(declaration, dict):
            continue
        kind = "interface" if declaration.get("kind") in {"interface", "protocol"} else "model"
        graph.node(f"{kind}:{name}", kind)
    for consumer, providers in (spec.get("imports") or {}).get("module_internal", {}).items():
        for provider in providers:
            graph.edge("module→module", f"module:{consumer}", f"module:{provider}")
    # State 6: functions, contracts, the types their signatures name
    type_nodes = {key.split(":", 1)[1]: key for key, kind in graph.nodes.items() if kind in {"model", "interface"}}
    imported_names: set[str] = set()
    for line in [*(spec.get("imports") or {}).get("stdlib", []), *(spec.get("imports") or {}).get("third_party", [])]:
        if isinstance(line, str) and " import " in line:
            imported_names.update(part.strip().split(" as ")[-1] for part in line.split(" import ", 1)[1].split(","))
    graph.functions = design_stage6_contracts.coverage(project).get("functions", [])
    provider_classes = {row["function"].split(".", 1)[0] for row in graph.functions if "." in row["function"]}
    # a class that owns contracts in the assembled spec is a decided module surface, not a missing model
    provider_classes |= {key.split(".", 1)[0] for key in (spec.get("contracts") or {}) if "." in key}
    for row in graph.functions:
        module_name = row["module"].split(":", 1)[1]
        function_key = graph.node(f"function:{module_name}.{row['function']}", "function")
        graph.edge("function→module", function_key, row["module"])
        if row.get("public_operation"):
            graph.edge("function→public_op", function_key, row["public_operation"])
        signature = row.get("signature") or ""
        if not signature:
            continue
        contract_key = graph.node(f"contract:{module_name}.{row['function']}", "contract")
        graph.edge("contract→function", contract_key, function_key)
        for name in set(re.findall(r"\b[A-Z][A-Za-z0-9_]+\b", signature)):
            if name in type_nodes:
                graph.edge("contract→model", contract_key, type_nodes[name])
            elif name not in _TYPE_SKIP and name not in provider_classes and name not in imported_names:
                graph.unresolved_types.add((contract_key, name))
    # router closure: ingress per public operation
    router_path = project / "70_router_closure.json"
    if router_path.exists():
        for item in json.loads(router_path.read_text(encoding="utf-8")).get("items", []):
            if item.get("operation"):
                graph.routes[item["operation"]] = item
    _state0_roots(graph)
    return graph
