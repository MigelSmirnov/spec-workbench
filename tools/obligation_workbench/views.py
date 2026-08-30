from __future__ import annotations

from collections import Counter
from typing import Any

from .model import Obligation, Projection
from .registry import PRECEDENCE


def _obligation_payload(obligation: Obligation, *, why_ready: bool = False) -> dict[str, Any]:
    payload = obligation.to_dict()
    if why_ready and obligation.status == "READY":
        payload["why_ready"] = "No defining obligation can change the subject of this decision."
    return payload


def list_obligations(projection: Projection) -> dict[str, Any]:
    order = {value: index for index, value in enumerate(PRECEDENCE)}
    obligations = sorted(
        projection.obligations,
        key=lambda item: (order[item.precedence_class], item.kind, item.id),
    )
    return {
        "schema_version": "spec_workbench_obligations_list.v1",
        "project_root": projection.graph.project.name,
        "obligations": [_obligation_payload(item) for item in obligations],
        "diagnostics": list(projection.diagnostics),
    }


def frontier(projection: Projection) -> dict[str, Any]:
    order = {value: index for index, value in enumerate(PRECEDENCE)}
    ready = sorted(
        (item for item in projection.obligations if item.status == "READY"),
        key=lambda item: (order[item.precedence_class], item.kind, item.id),
    )
    blocked_obligations = sorted(
        (item for item in projection.obligations if item.status == "BLOCKED"),
        key=lambda item: (item.kind, item.id),
    )
    blocked_states = sorted(
        (item for item in projection.states.values() if item.status == "BLOCKED"),
        key=lambda item: (item.kind, item.node),
    )
    states = Counter(state.status for state in projection.states.values())
    by_id = {item.id: item for item in projection.obligations}
    blocked_payload = []
    for item in blocked_obligations:
        payload = _obligation_payload(item)
        payload["defining_obligations"] = [
            {
                "id": blocker,
                "kind": by_id[blocker].kind,
                "caused_by": by_id[blocker].caused_by,
            }
            for blocker in item.blocked_by
            if blocker in by_id
        ]
        blocked_payload.append(payload)
    blocked_nodes = []
    for state in blocked_states:
        blocked_nodes.append({
            **state.to_dict(),
            "defining_obligations": [
                {
                    "id": blocker,
                    "kind": by_id[blocker].kind,
                    "caused_by": by_id[blocker].caused_by,
                }
                for blocker in state.blocked_by
                if blocker in by_id
            ],
        })
    return {
        "schema_version": "spec_workbench_obligations_frontier.v1",
        "project_root": projection.graph.project.name,
        "summary": {
            "ready": len(ready),
            "blocked": len(blocked_obligations),
            "settled_nodes": states["SETTLED"],
            "ready_nodes": states["READY"],
            "blocked_nodes": states["BLOCKED"],
        },
        "READY": [_obligation_payload(item, why_ready=True) for item in ready],
        "BLOCKED": {
            "obligations": blocked_payload,
            "nodes": blocked_nodes,
        },
        "SETTLED": {
            "count": states["SETTLED"],
            "by_kind": dict(Counter(state.kind for state in projection.states.values() if state.status == "SETTLED")),
        },
    }


def _edge_payload(projection: Projection, edge: Any) -> dict[str, Any]:
    obligation_ids = sorted({
        obligation.id
        for obligation in projection.obligations
        if edge.target in obligation.required_from
        and (edge.source in obligation.addressed_to or edge.source in obligation.originating_nodes)
    })
    return {**edge.to_dict(), "obligation_ids": obligation_ids}


def focus(projection: Projection, node: str) -> dict[str, Any]:
    if node not in projection.graph.nodes:
        raise KeyError(node)
    graph = projection.graph
    owned_nodes = graph.owned_nodes(node) if graph.nodes[node].kind == "module" else set()
    local_scope = {node, *owned_nodes}
    owned_obligations = [
        obligation
        for obligation in projection.obligations
        if local_scope.intersection(obligation.addressed_to)
    ]
    incoming_edges = [
        edge
        for edge in graph.edges
        if edge.kind in {"requires_capability", "requires_public_op"}
        and edge.target in local_scope
        and edge.source not in local_scope
    ]
    outgoing_edges = [
        edge
        for edge in graph.edges
        if edge.kind in {"requires_capability", "requires_public_op"}
        and edge.source in local_scope
        and edge.target not in local_scope
    ]
    incoming_obligations = [
        obligation
        for obligation in projection.obligations
        if local_scope.intersection(obligation.required_from)
        and not local_scope.intersection(obligation.addressed_to)
    ]
    outgoing_obligations = [
        obligation
        for obligation in projection.obligations
        if local_scope.intersection(obligation.originating_nodes)
        and not local_scope.intersection(obligation.addressed_to)
    ]
    blocker_ids = sorted({
        blocker
        for owned_node in local_scope
        for blocker in projection.states[owned_node].blocked_by
    })
    by_id = {item.id: item for item in projection.obligations}
    local_states = [projection.states[item] for item in local_scope]
    focus_locally_complete = all(item.locally_complete for item in local_states)
    focus_globally_settled = (
        all(item.globally_settled for item in local_states)
        and not incoming_obligations
        and not outgoing_obligations
    )
    focus_state = {
        **projection.states[node].to_dict(),
        "locally_complete": focus_locally_complete,
        "globally_settled": focus_globally_settled,
        "status": (
            "BLOCKED"
            if blocker_ids
            else ("SETTLED" if focus_globally_settled else "READY")
        ),
        "blocked_by": blocker_ids,
    }
    return {
        "schema_version": "spec_workbench_obligations_focus.v1",
        "project_root": graph.project.name,
        "focus": node,
        "state": focus_state,
        "OWNED": {
            "nodes": [projection.states[item].to_dict() for item in sorted(owned_nodes)],
            "obligations": [_obligation_payload(item) for item in sorted(owned_obligations, key=lambda value: value.id)],
        },
        "INCOMING": {
            "evidence_edges": [_edge_payload(projection, item) for item in sorted(incoming_edges, key=lambda value: value.id)],
            "obligations": [_obligation_payload(item) for item in sorted(incoming_obligations, key=lambda value: value.id)],
        },
        "OUTGOING": {
            "evidence_edges": [_edge_payload(projection, item) for item in sorted(outgoing_edges, key=lambda value: value.id)],
            "obligations": [_obligation_payload(item) for item in sorted(outgoing_obligations, key=lambda value: value.id)],
        },
        "BLOCKERS": [_obligation_payload(by_id[item]) for item in blocker_ids if item in by_id],
    }


def metrics(projection: Projection) -> dict[str, Any]:
    graph = projection.graph
    engineering = [item for item in projection.obligations if item.category == "engineering"]
    addressed = [item for item in engineering if item.addressed_to and all(node in graph.nodes for node in item.addressed_to)]
    states = Counter(item.status for item in projection.states.values())
    missing_sources = [item for item in projection.obligations if item.kind == "model_without_design_source"]
    outcome_gaps = [item for item in projection.obligations if item.kind in {"outcome_without_flow", "outcome_flow_mapping_unresolved"}]
    return {
        "schema_version": "spec_workbench_obligations_metrics.v1",
        "project_root": graph.project.name,
        "nodes": {
            "total": len(graph.nodes),
            "by_kind": dict(Counter(node.kind for node in graph.nodes.values())),
        },
        "evidence_edges": {
            "total": len(graph.edges),
            "by_kind": dict(Counter(edge.kind for edge in graph.edges)),
        },
        "obligations": {
            "total": len(projection.obligations),
            "by_kind": dict(Counter(item.kind for item in projection.obligations)),
            "by_status": dict(Counter(item.status for item in projection.obligations)),
            "by_precedence": dict(Counter(item.precedence_class for item in projection.obligations)),
            "with_caused_by": sum(bool(item.caused_by) for item in projection.obligations),
            "without_caused_by": sum(not item.caused_by for item in projection.obligations),
        },
        "frontier": {
            "READY": states["READY"],
            "BLOCKED": states["BLOCKED"],
            "SETTLED": states["SETTLED"],
        },
        "addressability": {
            "addressed": len(addressed),
            "total_engineering": len(engineering),
            "ratio": round(len(addressed) / len(engineering), 4) if engineering else 1.0,
            "unaddressed_obligations": [item.id for item in engineering if item not in addressed],
            "unaddressed_findings": [item for item in projection.diagnostics if item.get("kind") == "unaddressed_finding"],
            "tool_obligations": [item.id for item in projection.obligations if item.category == "tool"],
        },
        "factory_parity": projection.factory_parity,
        "models_interfaces_without_design_source": [
            {"obligation": item.id, "addressed_to": list(item.addressed_to)}
            for item in missing_sources
        ],
        "outcomes_without_flow": [
            {"obligation": item.id, "kind": item.kind, "addressed_to": list(item.addressed_to)}
            for item in outcome_gaps
        ],
        "elapsed_seconds": round(projection.elapsed_seconds, 3),
    }
