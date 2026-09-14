from __future__ import annotations

import time
from pathlib import Path
from typing import Iterable

from .derive import derive
from .evidence import build_evidence_graph
from .factory_parity import compare
from .model import Projection, SemanticClaim
from .reports import collect_reports


def build_graph(
    project: Path,
    *,
    factory_root: Path | None = None,
    factory_project: str | None = None,
    semantic_claims: Iterable[SemanticClaim] = (),
) -> Projection:
    started = time.perf_counter()
    graph = build_evidence_graph(project)
    claims = [*graph.metadata.get("semantic_claims", ()), *semantic_claims]
    for claim in claims:
        referenced = {claim.expressed_by, claim.semantic_owner, *claim.applies_to}
        missing = sorted(referenced - set(graph.nodes))
        if missing:
            raise ValueError(f"semantic claim {claim.id!r} references unknown nodes: {missing}")
    claim_ids = [claim.id for claim in claims]
    if len(claim_ids) != len(set(claim_ids)):
        raise ValueError("semantic claim ids must be unique")
    graph.metadata["semantic_claims"] = tuple(sorted(claims, key=lambda item: item.id))
    report_findings, diagnostics = collect_reports(graph.project)
    parity = compare(graph, factory_root=factory_root, factory_project=factory_project)
    obligations, states = derive(graph, report_findings, parity, diagnostics)
    return Projection(
        graph=graph,
        obligations=obligations,
        states=states,
        semantic_claims=graph.metadata["semantic_claims"],
        factory_parity=parity,
        diagnostics=tuple(diagnostics),
        elapsed_seconds=time.perf_counter() - started,
    )
