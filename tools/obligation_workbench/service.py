from __future__ import annotations

import time
from pathlib import Path

from .derive import derive
from .evidence import build_evidence_graph
from .factory_parity import compare
from .model import Projection
from .reports import collect_reports


def build_graph(
    project: Path,
    *,
    factory_root: Path | None = None,
    factory_project: str | None = None,
) -> Projection:
    started = time.perf_counter()
    graph = build_evidence_graph(project)
    report_findings, diagnostics = collect_reports(graph.project)
    parity = compare(graph, factory_root=factory_root, factory_project=factory_project)
    obligations, states = derive(graph, report_findings, parity, diagnostics)
    return Projection(
        graph=graph,
        obligations=obligations,
        states=states,
        factory_parity=parity,
        diagnostics=tuple(diagnostics),
        elapsed_seconds=time.perf_counter() - started,
    )
