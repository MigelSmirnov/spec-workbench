from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from dataclasses import replace
from pathlib import Path
from typing import Any

from .model import EvidenceGraph, EvidenceRef, NodeState, Obligation, stable_obligation_id
from .ownership import find_ownership_conflicts
from .registry import RULES, ObligationRule, classify, is_defining
from .reports import finding_addresses, finding_evidence


NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


class ObligationAccumulator:
    def __init__(self) -> None:
        self._items: dict[tuple[str, str], dict[str, Any]] = {}

    def add(
        self,
        rule: ObligationRule,
        *,
        caused_by: str,
        addressed_to: tuple[str, ...] = (),
        evidence: tuple[EvidenceRef, ...] = (),
        required_from: tuple[str, ...] = (),
        originating_nodes: tuple[str, ...] = (),
        semantic_owner: str | None = None,
        implementation_mode: str | None = None,
        irregular_reason: str | None = None,
        ownership_status: str | None = None,
        detail: str = "",
    ) -> None:
        key = (rule.kind, caused_by)
        current = self._items.setdefault(key, {
            "addressed_to": set(),
            "evidence": set(),
            "required_from": set(),
            "originating_nodes": set(),
            "semantic_owner": None,
            "implementation_mode": None,
            "irregular_reason": None,
            "ownership_status": None,
            "detail": [],
        })
        current["addressed_to"].update(addressed_to)
        current["evidence"].update(evidence)
        current["required_from"].update(required_from)
        current["originating_nodes"].update(originating_nodes)
        for field, value in (
            ("semantic_owner", semantic_owner),
            ("implementation_mode", implementation_mode),
            ("irregular_reason", irregular_reason),
            ("ownership_status", ownership_status),
        ):
            if value is None:
                continue
            if current[field] not in {None, value}:
                raise ValueError(
                    f"{kind}/{caused_by}: conflicting {field}: {current[field]!r}, {value!r}"
                )
            current[field] = value
        if detail and detail not in current["detail"]:
            current["detail"].append(detail)

    def build(self) -> list[Obligation]:
        result: list[Obligation] = []
        for (kind, caused_by), item in sorted(self._items.items()):
            rule = RULES[kind]
            result.append(Obligation(
                id=stable_obligation_id(kind, caused_by),
                kind=kind,
                addressed_to=tuple(sorted(item["addressed_to"])),
                caused_by=caused_by,
                evidence=tuple(sorted(item["evidence"])),
                precedence_class=rule.precedence_class,
                resolution_owner=rule.resolution_owner,
                required_from=tuple(sorted(item["required_from"])),
                originating_nodes=tuple(sorted(item["originating_nodes"])),
                semantic_owner=item["semantic_owner"],
                implementation_mode=item["implementation_mode"],
                irregular_reason=item["irregular_reason"],
                ownership_status=item["ownership_status"],
                detail=" | ".join(item["detail"]),
                category=rule.category,
            ))
        return result


def _finding_cause(
    report: str,
    finding: dict[str, Any],
    addresses: tuple[str, ...],
    rule: ObligationRule,
) -> str:
    joined = ",".join(addresses)
    grouped = {
        "module_cut_undecided": f"state3:{joined}:architectural_cut",
        "model_identity_unresolved": f"state1:{joined}:identity_closure",
        "interface_without_provider": f"state6:{joined}:provider_closure",
        "boundary_auth_principal_unresolved": "router_context:auth_principal_closure",
        "boundary_error_contract_missing": "router_context:error_contract_closure",
    }
    if rule.kind == "boundary_input_contract_missing":
        grouped[rule.kind] = f"state6:{joined}:boundary_input_contract"
    if rule.kind in grouped:
        return grouped[rule.kind]
    discriminator = finding.get("location") or finding.get("contract") or finding.get("scope")
    if not discriminator:
        discriminator = ",".join(addresses)
    if not discriminator:
        discriminator = hashlib.sha256(str(finding.get("message") or "").encode("utf-8")).hexdigest()[:12]
    return f"report:{report}:{finding.get('code')}:{discriminator}"


def _boundaries_for_operation(graph: EvidenceGraph, operation: str) -> tuple[str, ...]:
    return tuple(sorted(
        edge.target
        for edge in graph.edges
        if edge.source == operation
        and edge.kind == "called_by"
        and graph.nodes[edge.target].kind == "boundary"
    ))


def _all_routed_boundaries(graph: EvidenceGraph) -> tuple[str, ...]:
    return tuple(sorted({
        edge.source
        for edge in graph.edges
        if edge.kind == "ingress_route" and graph.nodes[edge.source].kind == "boundary"
    }))


def _report_obligations(
    graph: EvidenceGraph,
    report_findings: list[dict[str, Any]],
    accumulator: ObligationAccumulator,
    diagnostics: list[dict[str, Any]],
) -> None:
    for item in report_findings:
        report = item["report"]
        finding = item["finding"]
        code = finding["code"]
        if code == "missing_state1_model":
            # The projection below owns this one cause and retains the exact State 1/projection evidence.
            continue
        rule = classify(report, code)
        addresses = finding_addresses(finding, graph)
        required_from: tuple[str, ...] = ()
        if rule.kind.startswith("boundary_"):
            operation = next((address for address in addresses if address.startswith("public_op:")), None)
            if operation:
                boundaries = _boundaries_for_operation(graph, operation)
                if boundaries:
                    addresses = boundaries
                    required_from = (operation,)
            elif code in {"invalid_error_policy", "invalid_error_body", "missing_error_mapping", "missing_credential_extractors", "invalid_principals", "invalid_auth_policies"}:
                addresses = _all_routed_boundaries(graph)
        if rule.category == "tool":
            addresses = ()
        if not addresses and rule.category != "tool":
            diagnostics.append({
                "kind": "unaddressed_finding",
                "report": report,
                "code": code,
                "message": finding.get("message"),
                "structured_fields": sorted(key for key in finding if key not in {"message", "severity", "code"}),
            })
            continue
        cause = _finding_cause(report, finding, addresses, rule)
        accumulator.add(
            rule,
            caused_by=cause,
            addressed_to=addresses,
            evidence=(finding_evidence(report, finding),),
            required_from=required_from,
            originating_nodes=required_from,
            detail=str(finding.get("hint") or finding.get("message") or ""),
        )


def _capability_reachability(graph: EvidenceGraph) -> tuple[set[str], dict[str, str]]:
    spec = graph.metadata["spec"]
    owners = {
        str(row.get("function")): str(row.get("module") or "").removeprefix("module:")
        for row in graph.metadata["functions"]
        if isinstance(row.get("function"), str)
    }
    route_roots: set[str] = set()
    backend = ((spec.get("rules") or {}).get("http_router_backend") or {})
    for route in backend.get("routes") or []:
        if not isinstance(route, dict):
            continue
        delegate = route.get("delegate") or {}
        if isinstance(delegate, dict) and isinstance(delegate.get("function"), str):
            route_roots.add(delegate["function"])
        if route.get("emission") == "irregular" and isinstance(route.get("handler"), str):
            route_roots.add(route["handler"])
        for step in route.get("authorize") or []:
            if isinstance(step, dict) and isinstance(step.get("function"), str):
                route_roots.add(step["function"])
    for principal in (backend.get("principals") or {}).values():
        if isinstance(principal, dict) and isinstance(principal.get("resolver"), str):
            route_roots.add(principal["resolver"])

    for row in graph.metadata["operations"]:
        if graph.metadata["exposure"].get(row["key"]) == "internal-only" and row.get("callers") and all(str(value).startswith("boundary:") for value in row["callers"]):
            route_roots.add(row["key"].split(".", 1)[1])

    note_calls: dict[str, set[str]] = defaultdict(set)
    notes_path = graph.project / "80_notes.md"
    if notes_path.is_file():
        for line in notes_path.read_text(encoding="utf-8").splitlines():
            if ":" not in line or "[ORCHESTRATION]" not in line:
                continue
            scope, body = line.split(":", 1)
            scope = scope.strip()
            if scope not in owners:
                continue
            for name in set(NAME_RE.findall(body)):
                if name in owners and name != scope:
                    note_calls[scope].add(name)

    reached = set(route_roots)
    frontier = list(route_roots)
    while frontier:
        current = frontier.pop()
        for target in note_calls.get(current, set()):
            if target not in reached:
                reached.add(target)
                frontier.append(target)
    return reached, owners


def _derived_obligations(
    graph: EvidenceGraph,
    factory_parity: dict[str, Any],
    accumulator: ObligationAccumulator,
) -> None:
    for conflict in find_ownership_conflicts(tuple(graph.metadata.get("semantic_claims", ()))):
        owner_label = conflict.canonical_owner or "unresolved"
        ownership_status = "wrong_owner" if conflict.canonical_owner is not None else "ambiguous_owner"
        if conflict.canonical_owner is not None:
            detail = (
                f"{conflict.semantic_key} is canonically owned by {conflict.canonical_owner}; "
                f"downstream owners are {', '.join(conflict.conflicting_owners)}. "
                f"Return the decision to {conflict.canonical_owner}; "
                "this does not prescribe deleting the downstream expression."
            )
        else:
            detail = (
                f"{conflict.semantic_key} has conflicting canonical owners: "
                f"{', '.join(conflict.conflicting_owners)}. Canonical evidence does not identify "
                "one owner; resolve that ambiguity before downstream repair."
            )
        accumulator.add(
            RULES["duplicate_semantic_ownership"],
            caused_by=f"semantic:{conflict.semantic_key}:owned_by:{owner_label}",
            addressed_to=conflict.conflicting_expressions,
            evidence=conflict.evidence,
            required_from=(conflict.canonical_owner,) if conflict.canonical_owner is not None else (),
            originating_nodes=conflict.conflicting_expressions,
            semantic_owner=conflict.canonical_owner,
            implementation_mode=conflict.implementation_mode,
            irregular_reason=conflict.irregular_reason,
            ownership_status=ownership_status,
            detail=detail,
        )

    for key, row in graph.metadata["decisions"].items():
        if not row.get("primary_owner") and not row.get("disposition"):
            accumulator.add(
                RULES["decision_without_owner"],
                caused_by=f"decision:{key}:accepted_without_owner",
                addressed_to=(f"decision:{key}",),
                evidence=(EvidenceRef("trace", "30_trace.json"),),
                originating_nodes=(f"decision:{key}",),
                detail="Accepted State 2 decision has neither a primary owner nor an explicit disposition.",
            )

    for name, declaration in graph.metadata["spec"].get("models", {}).items():
        if not isinstance(declaration, dict) or name in graph.metadata["state1_model_sources"]:
            continue
        kind = "interface" if declaration.get("kind") in {"interface", "protocol"} else "model"
        node = f"{kind}:{name}"
        accumulator.add(
            RULES["model_without_design_source"],
            caused_by=f"projection:{node}:without_state1_source",
            addressed_to=(node,),
            evidence=(EvidenceRef("projection", f"global_spec.json:models.{name}"),),
            originating_nodes=(node,),
            detail="Projection contains the type, but no canonical State 1 model item owns it.",
        )

    implementation = graph.metadata["spec"].get("implementation_obligations") or {}
    interfaces_in_use = {
        edge.target
        for edge in graph.edges
        if edge.kind == "uses_type" and graph.nodes[edge.target].kind == "interface"
    }
    contracts = graph.metadata["spec"].get("contracts") or {}
    for interface_node in sorted(interfaces_in_use):
        name = interface_node.removeprefix("interface:")
        row = implementation.get(name)
        missing = not isinstance(row, dict)
        if isinstance(row, dict) and row.get("disposition") in {"local", "policy"}:
            implementations = row.get("implementations")
            missing = not isinstance(implementations, list) or not implementations
            interface_methods = {key.split(".", 1)[1]: value for key, value in contracts.items() if key.startswith(name + ".")}
            for concrete in implementations or []:
                for method, signature in interface_methods.items():
                    if contracts.get(f"{concrete}.{method}") != signature:
                        missing = True
        if missing:
            users = tuple(sorted(edge.source for edge in graph.edges if edge.kind == "uses_type" and edge.target == interface_node))
            accumulator.add(
                RULES["interface_without_provider"],
                caused_by=f"interface:{name}:provider_closure",
                addressed_to=(interface_node,),
                evidence=(EvidenceRef("projection", f"global_spec.json:implementation_obligations.{name}"),),
                required_from=users,
                originating_nodes=(interface_node,),
                detail="The used interface has no complete local/policy/external implementation disposition and surface closure.",
            )

    routes = graph.metadata["routes"]
    for row in graph.metadata["operations"]:
        boundaries = tuple(sorted(value for value in row.get("callers", []) if str(value).startswith("boundary:")))
        if not boundaries:
            continue
        if row["key"] not in routes and graph.metadata["exposure"].get(row["key"]) != "internal-only":
            accumulator.add(
                RULES["boundary_without_ingress"],
                caused_by=f"public_op:{row['key']}:boundary_ingress",
                addressed_to=boundaries,
                evidence=(EvidenceRef("state5", "50_api_plan.json"), EvidenceRef("router_closure", "70_router_closure.json")),
                required_from=(row["key"], row["capability"]),
                originating_nodes=(row["key"],),
                detail=f"No accepted route carries {row['key']} for its designed boundary caller(s).",
            )
    for operation in routes:
        if not _boundaries_for_operation(graph, operation):
            accumulator.add(
                RULES["route_without_designed_boundary"],
                caused_by=f"router:{operation}:without_state5_boundary",
                addressed_to=(operation,) if operation in graph.nodes else (),
                evidence=(EvidenceRef("router_closure", "70_router_closure.json"),),
                originating_nodes=(operation,) if operation in graph.nodes else (),
                detail="A route exists without an explicit State 5 boundary caller.",
            )

    outcome_nodes = {node_id for node_id, node in graph.nodes.items() if node.kind == "outcome"}
    mapped = set(graph.metadata["explicit_outcome_edges"])
    if mapped:
        for outcome in sorted(outcome_nodes - mapped):
            accumulator.add(
                RULES["outcome_without_flow"],
                caused_by=f"state0:{outcome}:without_reviewed_flow",
                addressed_to=(outcome,),
                evidence=graph.nodes[outcome].evidence,
                originating_nodes=(outcome,),
                detail="Other outcomes use explicit outcome:* flow mapping, but this accepted outcome has no implementing reviewed flow.",
            )
    else:
        for outcome in sorted(outcome_nodes):
            accumulator.add(
                RULES["outcome_flow_mapping_unresolved"],
                caused_by=f"state0:{outcome}:flow_mapping_unresolved",
                addressed_to=(outcome,),
                evidence=graph.nodes[outcome].evidence,
                originating_nodes=(outcome,),
                detail="Current artifacts contain no explicit outcome:* → flow correspondence; the projection refuses lexical matching.",
            )

    reached, owners = _capability_reachability(graph)
    for row in graph.metadata["flow_coverage"]:
        flow = row["key"]
        for capability in row.get("candidate_capabilities", []):
            if capability in graph.nodes:
                continue
            accumulator.add(
                RULES["flow_capability_missing"],
                caused_by=f"{flow}:{capability}:missing_surface",
                addressed_to=(flow,),
                evidence=(EvidenceRef("state4_plan", "40_flow_plan.json"),),
                required_from=(capability,),
                originating_nodes=(flow,),
                detail=f"{capability} is not declared by any State 3 module.",
            )

    for edge in [item for item in graph.edges if item.kind == "requires_capability" and graph.nodes[item.source].kind == "flow"]:
        module, operation = edge.target.removeprefix("capability:").split(".", 1)
        if owners.get(operation) != module:
            accumulator.add(
                RULES["flow_capability_missing"],
                caused_by=f"{edge.source}:{edge.target}:missing_surface",
                addressed_to=(edge.source,),
                evidence=edge.evidence,
                required_from=(edge.target,),
                originating_nodes=(edge.source,),
                detail=f"{edge.target} is not planned and contracted under module:{module}.",
            )
        elif operation not in reached:
            callers = tuple(sorted(
                item.source
                for item in graph.edges
                if item.kind == "requires_capability"
                and item.target == edge.target
                and graph.nodes[item.source].kind in {"module", "boundary"}
            ))
            accumulator.add(
                RULES["capability_unreachable"],
                caused_by=f"{edge.target}:reachability_unresolved",
                addressed_to=callers or (edge.source,),
                evidence=edge.evidence,
                required_from=(edge.target,),
                originating_nodes=(edge.source,),
                detail=f"No accepted route/non-HTTP ingress and explicit orchestration chain reaches {edge.target}.",
            )

    if factory_parity.get("available"):
        for consumer, provider in factory_parity.get("dependency_not_designed", []):
            consumer_node = f"module:{consumer}"
            provider_node = f"module:{provider}"
            if consumer_node not in graph.nodes:
                graph.add_node(consumer_node, "module", evidence=[EvidenceRef("factory", f"{consumer}:merged_dependency_graph")])
            if provider_node not in graph.nodes:
                graph.add_node(provider_node, "module", evidence=[EvidenceRef("factory", f"{provider}:merged_dependency_graph")])
            accumulator.add(
                RULES["dependency_not_designed"],
                caused_by=f"factory_dependency:{consumer}->{provider}",
                addressed_to=(consumer_node,),
                evidence=(EvidenceRef("factory", f"merged_dependency_graph:{consumer}->{provider}"),),
                required_from=(provider_node,),
                originating_nodes=(consumer_node,),
                detail="Factory merged dependency exists without an explicit Workbench module_internal edge; architectural explanation is required.",
            )


def derive(
    graph: EvidenceGraph,
    report_findings: list[dict[str, Any]],
    factory_parity: dict[str, Any],
    diagnostics: list[dict[str, Any]],
) -> tuple[tuple[Obligation, ...], dict[str, NodeState]]:
    accumulator = ObligationAccumulator()
    _report_obligations(graph, report_findings, accumulator, diagnostics)
    _derived_obligations(graph, factory_parity, accumulator)
    obligations = accumulator.build()

    defining_by_node: dict[str, set[str]] = defaultdict(set)
    for obligation in obligations:
        if is_defining(obligation.kind):
            for address in obligation.addressed_to:
                defining_by_node[address].add(obligation.id)

    def blockers(node: str, seen: set[str]) -> set[str]:
        result: set[str] = set()
        for target in graph.definitional_targets(node):
            if target in seen:
                continue
            seen.add(target)
            result.update(defining_by_node.get(target, set()))
            result.update(blockers(target, seen))
        return result

    scheduled: list[Obligation] = []
    for obligation in obligations:
        blocked_by: set[str] = set()
        for address in obligation.addressed_to:
            blocked_by.update(blockers(address, {address}))
        blocked_by.discard(obligation.id)
        scheduled.append(replace(
            obligation,
            status="BLOCKED" if blocked_by else "READY",
            blocked_by=tuple(sorted(blocked_by)),
        ))

    obligation_by_node: dict[str, list[str]] = defaultdict(list)
    incoming_by_node: dict[str, list[str]] = defaultdict(list)
    for obligation in scheduled:
        for address in obligation.addressed_to:
            obligation_by_node[address].append(obligation.id)
        for required in obligation.required_from:
            if required in graph.nodes and required not in obligation.addressed_to:
                incoming_by_node[required].append(obligation.id)
    states: dict[str, NodeState] = {}
    for node_id, node in graph.nodes.items():
        external_blockers = blockers(node_id, {node_id})
        local_ids = tuple(sorted(obligation_by_node.get(node_id, [])))
        incoming_ids = tuple(sorted(incoming_by_node.get(node_id, [])))
        locally_complete = not local_ids
        globally_settled = not external_blockers and not local_ids and not incoming_ids
        status = "BLOCKED" if external_blockers else ("SETTLED" if globally_settled else "READY")
        states[node_id] = NodeState(
            node=node_id,
            kind=node.kind,
            locally_complete=locally_complete,
            globally_settled=globally_settled,
            status=status,
            obligation_ids=local_ids,
            blocked_by=tuple(sorted(external_blockers)),
        )
    return tuple(scheduled), states
