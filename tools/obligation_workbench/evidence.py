from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

import design_index
import design_stage3
import design_stage4
import design_stage5
import design_stage6_contracts
import design_trace

from .model import EvidenceGraph, EvidenceRef


HEADING_RE = re.compile(r"^(?P<marks>#{2,4})\s+(?P<title>.+?)\s*$")
EXPLICIT_OUTCOME_REF_RE = re.compile(r"\boutcome:[a-z][a-z0-9_-]*\b")


def _read_json(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.is_file():
        return {} if default is None else default
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return payload


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return slug or "unnamed"


def _state0_nodes(project: Path, graph: EvidenceGraph) -> None:
    path = project / "00_product.md"
    if not path.is_file():
        return
    section_kind: str | None = None
    section_level = 0
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        match = HEADING_RE.match(raw)
        if match is None:
            continue
        level = len(match.group("marks"))
        title = match.group("title").strip().strip("`")
        if level == 2:
            normalized = title.casefold()
            if normalized.endswith(" boundary") or normalized.endswith(" boundaries"):
                graph.add_node(
                    f"boundary:{_slug(title)}",
                    "boundary",
                    label=title,
                    evidence=[EvidenceRef("state0", f"00_product.md:{line_number}")],
                )
            section_kind = {
                "actors": "actor",
                "observable outcomes": "outcome",
                "boundaries": "boundary",
            }.get(normalized)
            if section_kind is None and (
                normalized.endswith(" boundary") or normalized.endswith(" boundaries")
            ):
                section_kind = "boundary"
            section_level = level
            continue
        if section_kind and level == section_level + 1:
            node_id = f"{section_kind}:{_slug(title)}"
            graph.add_node(
                node_id,
                section_kind,
                label=title,
                evidence=[EvidenceRef("state0", f"00_product.md:{line_number}")],
            )


def _state1_model_sources(project: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in design_index.list_items(project, state=1, kind="model"):
        title = str(item.get("title") or "")
        name = re.sub(r"^Model\s+M\d+\s*[—-]\s*", "", title, flags=re.IGNORECASE).strip().strip("`")
        source = item.get("source") or {}
        if name:
            result[name] = f"{source.get('path')}:{source.get('start_line')}"
    return result


def _annotation_names(signature: str) -> set[str]:
    try:
        tree = ast.parse(f"def __obligation_probe{signature}:\n    pass\n")
    except SyntaxError:
        return set()
    function = tree.body[0]
    if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return set()
    annotations: list[ast.expr] = []
    for argument in [*function.args.posonlyargs, *function.args.args, *function.args.kwonlyargs]:
        if argument.annotation is not None:
            annotations.append(argument.annotation)
    if function.args.vararg and function.args.vararg.annotation is not None:
        annotations.append(function.args.vararg.annotation)
    if function.args.kwarg and function.args.kwarg.annotation is not None:
        annotations.append(function.args.kwarg.annotation)
    if function.returns is not None:
        annotations.append(function.returns)
    return {node.id for annotation in annotations for node in ast.walk(annotation) if isinstance(node, ast.Name)}


def _flow_text(project: Path, item: Any) -> str:
    path = project / item.source.path
    if not path.is_file():
        return ""
    lines = path.read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[item.source.start_line - 1:item.source.end_line])


def build_evidence_graph(project: Path) -> EvidenceGraph:
    project = project.resolve()
    if not project.is_dir():
        raise ValueError(f"project directory not found: {project}")
    graph = EvidenceGraph(project)
    _state0_nodes(project, graph)

    state3_modules: set[str] = set()
    for row in design_stage3.handoff(project).get("modules", []):
        module = graph.add_node(
            row["key"],
            "module",
            label=row["name"],
            evidence=[EvidenceRef("state3", "30_modules.md")],
        )
        state3_modules.add(module)
        for capability in row.get("capability_refs", []):
            key = capability.get("key") if isinstance(capability, dict) else capability
            if not isinstance(key, str):
                continue
            graph.add_node(key, "capability", evidence=[EvidenceRef("state3", "30_modules.md")])
            graph.add_edge(module, key, "owns_capability", evidence=[EvidenceRef("state3", "30_modules.md")])
            graph.add_edge(key, module, "defined_by_module", evidence=[EvidenceRef("state3", "30_modules.md")], defining=True)

    trace = design_trace.analyze(project)
    decisions = dict(trace.get("decisions") or {})
    unclaimed = trace.get("unclaimed_state2_decisions") or []
    for item in unclaimed:
        key = item if isinstance(item, str) else item.get("key") or item.get("decision") or item.get("id")
        if key:
            decisions.setdefault(key, {"primary_owner": None, "consumers": [], "unclaimed": True})
    for key, row in decisions.items():
        node = graph.add_node(
            f"decision:{key}",
            "decision",
            label=key,
            evidence=[EvidenceRef("state2", str(row.get("source") or "02_rules.md"))],
        )
        owner = row.get("primary_owner")
        if isinstance(owner, str) and owner in graph.nodes:
            graph.add_edge(node, owner, "owned_by", evidence=[EvidenceRef("trace", "30_trace.json")])

    flows: dict[str, Any] = {}
    for item in design_stage4.parse_flows(project):
        flows[item.key] = item
        graph.add_node(
            item.key,
            "flow",
            evidence=[EvidenceRef("state4", f"{item.source.path}:{item.source.start_line}")],
        )
    flow_coverage = design_stage4.coverage(project).get("flows", [])
    for row in flow_coverage:
        flow = graph.add_node(row["key"], "flow", evidence=[EvidenceRef("state4_plan", "40_flow_plan.json")])
        for module in row.get("required_modules", []):
            if module in graph.nodes:
                graph.add_edge(flow, module, "requires_module", evidence=[EvidenceRef("state4_plan", "40_flow_plan.json")])
        for capability in row.get("candidate_capabilities", []):
            if capability in graph.nodes:
                graph.add_edge(flow, capability, "requires_capability", evidence=[EvidenceRef("state4_plan", "40_flow_plan.json")])

    explicit_outcome_edges: set[str] = set()
    for flow_id, item in flows.items():
        for outcome in sorted(set(EXPLICIT_OUTCOME_REF_RE.findall(_flow_text(project, item)))):
            if outcome in graph.nodes:
                graph.add_edge(outcome, flow_id, "implemented_by_flow", evidence=[EvidenceRef("state4", f"{item.source.path}:{item.source.start_line}")])
                explicit_outcome_edges.add(outcome)

    operations = design_stage5.coverage(project).get("operations", [])
    for row in operations:
        operation = graph.add_node(row["key"], "public_op", evidence=[EvidenceRef("state5", "50_api_plan.json")])
        capability = row.get("capability")
        if isinstance(capability, str) and capability in graph.nodes:
            graph.add_edge(operation, capability, "implements_capability", evidence=[EvidenceRef("state5", "50_api_plan.json")], defining=True)
        for flow in row.get("flows", []):
            if flow in graph.nodes:
                graph.add_edge(operation, flow, "proven_by_flow", evidence=[EvidenceRef("state5", "50_api_plan.json")], defining=True)
        for caller in row.get("callers", []):
            if not isinstance(caller, str):
                continue
            caller_kind = "boundary" if caller.startswith("boundary:") else "module"
            graph.add_node(caller, caller_kind, evidence=[EvidenceRef("state5", "50_api_plan.json")])
            graph.add_edge(operation, caller, "called_by", evidence=[EvidenceRef("state5", "50_api_plan.json")])
            graph.add_edge(caller, operation, "requires_public_op", evidence=[EvidenceRef("state5", "50_api_plan.json")])
            if isinstance(capability, str) and capability in graph.nodes:
                graph.add_edge(caller, capability, "requires_capability", evidence=[EvidenceRef("state5", "50_api_plan.json")])

    spec_path = project / "global_spec.json"
    spec = _read_json(spec_path)
    state1_sources = _state1_model_sources(project)
    spec_models = {
        name: declaration
        for name, declaration in (spec.get("models") or {}).items()
        if isinstance(name, str) and isinstance(declaration, dict)
    }
    for name, declaration in spec_models.items():
        kind = "interface" if declaration.get("kind") in {"interface", "protocol"} else "model"
        evidence = [EvidenceRef("projection", "global_spec.json:models")]
        if name in state1_sources:
            evidence.append(EvidenceRef("state1", state1_sources[name]))
        graph.add_node(f"{kind}:{name}", kind, label=name, evidence=evidence)

    for module in (spec.get("module_functions") or {}):
        graph.add_node(f"module:{module}", "module", evidence=[EvidenceRef("projection", "global_spec.json:module_functions")])
    for consumer, providers in ((spec.get("imports") or {}).get("module_internal") or {}).items():
        consumer_key = f"module:{consumer}"
        if consumer_key not in graph.nodes or not isinstance(providers, dict):
            continue
        for provider in providers:
            provider_key = f"module:{provider}"
            if provider_key in graph.nodes:
                graph.add_edge(consumer_key, provider_key, "module_dependency", evidence=[EvidenceRef("projection", f"global_spec.json:imports.module_internal.{consumer}.{provider}")])

    type_nodes = {
        node.label: node.id
        for node in graph.nodes.values()
        if node.kind in {"model", "interface"}
    }
    functions = design_stage6_contracts.coverage(project).get("functions", [])
    for row in functions:
        module_name = str(row.get("module") or "module:unknown").removeprefix("module:")
        function_name = str(row.get("function") or "unknown")
        function = graph.add_node(
            f"function:{module_name}.{function_name}",
            "function",
            label=function_name,
            evidence=[EvidenceRef("state6_plan", "60_contract_plan.json")],
        )
        module = f"module:{module_name}"
        if module in graph.nodes:
            graph.add_edge(function, module, "defined_by_module", evidence=[EvidenceRef("state6_plan", "60_contract_plan.json")], defining=True)
        public_operation = row.get("public_operation")
        if isinstance(public_operation, str) and public_operation in graph.nodes:
            graph.add_edge(function, public_operation, "implements_public_op", evidence=[EvidenceRef("state6_plan", "60_contract_plan.json")], defining=True)
        signature = row.get("signature")
        if not isinstance(signature, str) or not signature.strip() or signature == "unresolved":
            continue
        contract = graph.add_node(
            f"contract:{module_name}.{function_name}",
            "contract",
            label=function_name,
            evidence=[EvidenceRef("state6", "60_contracts.json")],
        )
        graph.add_edge(contract, function, "contract_of", evidence=[EvidenceRef("state6", "60_contracts.json")], defining=True)
        for type_name in sorted(_annotation_names(signature)):
            target = type_nodes.get(type_name)
            if target:
                graph.add_edge(contract, target, "uses_type", evidence=[EvidenceRef("state6", f"60_contracts.json:{function_name}")], defining=True)

    routes = {}
    router_path = project / "70_router_closure.json"
    if router_path.is_file():
        for row in _read_json(router_path).get("items", []):
            if isinstance(row, dict) and isinstance(row.get("operation"), str):
                routes[row["operation"]] = row
                operation = row["operation"]
                if operation in graph.nodes:
                    for edge in [edge for edge in graph.edges if edge.source == operation and edge.kind == "called_by"]:
                        if graph.nodes[edge.target].kind == "boundary":
                            graph.add_edge(edge.target, operation, "ingress_route", evidence=[EvidenceRef("router_closure", "70_router_closure.json")])

    exposure = {}
    exposure_path = project / "50_exposure_plan.json"
    if exposure_path.is_file():
        exposure = dict(_read_json(exposure_path).get("operations") or {})

    graph.metadata.update({
        "state3_modules": state3_modules,
        "decisions": decisions,
        "operations": operations,
        "functions": functions,
        "flow_coverage": flow_coverage,
        "routes": routes,
        "exposure": exposure,
        "spec": spec,
        "state1_model_sources": state1_sources,
        "explicit_outcome_edges": explicit_outcome_edges,
    })
    return graph
