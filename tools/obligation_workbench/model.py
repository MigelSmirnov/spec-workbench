from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable


NODE_KINDS = frozenset({
    "actor",
    "outcome",
    "boundary",
    "decision",
    "model",
    "interface",
    "module",
    "capability",
    "flow",
    "public_op",
    "function",
    "contract",
})


@dataclass(frozen=True, order=True)
class EvidenceRef:
    source: str
    ref: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class Node:
    id: str
    kind: str
    label: str
    evidence: tuple[EvidenceRef, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "label": self.label,
            "evidence": [item.to_dict() for item in self.evidence],
        }


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    kind: str
    evidence: tuple[EvidenceRef, ...]
    defining: bool = False

    @property
    def id(self) -> str:
        return f"edge:{self.kind}:{self.source}->{self.target}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "kind": self.kind,
            "defining": self.defining,
            "evidence": [item.to_dict() for item in self.evidence],
        }


@dataclass(frozen=True)
class Obligation:
    id: str
    kind: str
    addressed_to: tuple[str, ...]
    caused_by: str
    evidence: tuple[EvidenceRef, ...]
    precedence_class: str
    resolution_owner: str
    status: str = "READY"
    blocked_by: tuple[str, ...] = ()
    required_from: tuple[str, ...] = ()
    originating_nodes: tuple[str, ...] = ()
    detail: str = ""
    category: str = "engineering"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "addressed_to": list(self.addressed_to),
            "caused_by": self.caused_by,
            "source": [item.to_dict() for item in self.evidence],
            "precedence_class": self.precedence_class,
            "resolution_owner": self.resolution_owner,
            "status": self.status,
            "blocked_by": list(self.blocked_by),
            "required_from": list(self.required_from),
            "originating_nodes": list(self.originating_nodes),
            "detail": self.detail,
            "category": self.category,
        }


@dataclass(frozen=True)
class NodeState:
    node: str
    kind: str
    locally_complete: bool
    globally_settled: bool
    status: str
    obligation_ids: tuple[str, ...] = ()
    blocked_by: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EvidenceGraph:
    project: Path
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    _edge_ids: set[str] = field(default_factory=set, repr=False)

    def add_node(
        self,
        node_id: str,
        kind: str,
        *,
        label: str | None = None,
        evidence: Iterable[EvidenceRef] = (),
    ) -> str:
        if kind not in NODE_KINDS:
            raise ValueError(f"unsupported obligation-graph node kind: {kind}")
        refs = tuple(sorted(set(evidence)))
        current = self.nodes.get(node_id)
        if current is None:
            self.nodes[node_id] = Node(node_id, kind, label or node_id.partition(":")[2], refs)
        else:
            if current.kind != kind:
                raise ValueError(f"node {node_id!r} has conflicting kinds: {current.kind!r}, {kind!r}")
            merged = tuple(sorted(set(current.evidence) | set(refs)))
            self.nodes[node_id] = Node(current.id, current.kind, current.label, merged)
        return node_id

    def add_edge(
        self,
        source: str,
        target: str,
        kind: str,
        *,
        evidence: Iterable[EvidenceRef],
        defining: bool = False,
    ) -> None:
        if source not in self.nodes or target not in self.nodes:
            raise KeyError(f"edge endpoints must exist: {source!r} -> {target!r}")
        edge = Edge(source, target, kind, tuple(sorted(set(evidence))), defining)
        if edge.id not in self._edge_ids:
            self.edges.append(edge)
            self._edge_ids.add(edge.id)

    def owner_module(self, node_id: str) -> str | None:
        node = self.nodes.get(node_id)
        if node is None:
            return None
        if node.kind == "module":
            return node_id
        if node.kind in {"capability", "public_op", "function", "contract"}:
            return f"module:{node_id.partition(':')[2].split('.', 1)[0]}"
        return None

    def owned_nodes(self, module: str) -> set[str]:
        return {node_id for node_id in self.nodes if node_id != module and self.owner_module(node_id) == module}

    def definitional_targets(self, node_id: str) -> set[str]:
        return {edge.target for edge in self.edges if edge.defining and edge.source == node_id}

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [self.nodes[key].to_dict() for key in sorted(self.nodes)],
            "edges": [edge.to_dict() for edge in sorted(self.edges, key=lambda item: item.id)],
        }


@dataclass(frozen=True)
class Projection:
    graph: EvidenceGraph
    obligations: tuple[Obligation, ...]
    states: dict[str, NodeState]
    factory_parity: dict[str, Any]
    diagnostics: tuple[dict[str, Any], ...]
    elapsed_seconds: float


def stable_obligation_id(kind: str, caused_by: str) -> str:
    digest = hashlib.sha256(f"{kind}|{caused_by}".encode("utf-8")).hexdigest()[:16]
    return f"obligation:{kind}:{digest}"
