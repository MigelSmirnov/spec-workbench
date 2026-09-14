from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import design_router_context
import design_stage4
from assembly_workbench.checks import CHECKS

from .model import EvidenceGraph, EvidenceRef


ADDRESS_FIELDS = (
    "module_key",
    "module",
    "decision",
    "capability",
    "flow",
    "flow_key",
    "operation",
    "operation_key",
    "contract",
    "function",
    "scope",
    "model",
    "interface",
    "key",
)


def _walk(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        if isinstance(value.get("code"), str) and isinstance(value.get("message"), str):
            yield value
            return
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def collect_reports(project: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    findings: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    reports = {**CHECKS, "flows": design_stage4.lint}
    if (project / design_router_context.FILE).is_file():
        reports["router_context"] = design_router_context.coverage
    for name, callable_ in reports.items():
        try:
            report = callable_(project)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            diagnostics.append({
                "kind": "report_unavailable",
                "report": name,
                "detail": str(exc),
            })
            continue
        for finding in _walk(report):
            findings.append({"report": name, "finding": finding})
    return findings, diagnostics


def finding_addresses(finding: dict[str, Any], graph: EvidenceGraph) -> tuple[str, ...]:
    addresses: list[str] = []
    for field in ADDRESS_FIELDS:
        value = finding.get(field)
        if not isinstance(value, str) or not value:
            continue
        candidates: list[str] = []
        if field in {"module", "module_key"}:
            candidates.append(value if value.startswith("module:") else f"module:{value}")
        elif field == "decision":
            candidates.append(value if value.startswith("decision:") else f"decision:{value}")
        elif field == "model":
            candidates.extend((f"model:{value}", f"interface:{value}"))
        elif field == "interface":
            candidates.append(value if value.startswith("interface:") else f"interface:{value}")
        elif field in {"contract", "function", "scope"} and ":" not in value:
            suffix = f".{value}"
            candidates.extend(node_id for node_id in graph.nodes if node_id.startswith(("contract:", "function:")) and node_id.endswith(suffix))
        else:
            candidates.append(value)
        for candidate in candidates:
            if candidate in graph.nodes and candidate not in addresses:
                addresses.append(candidate)
    return tuple(addresses)


def finding_evidence(report: str, finding: dict[str, Any]) -> EvidenceRef:
    location = finding.get("location") or finding.get("source") or finding.get("scope") or finding.get("contract")
    ref = f"{finding.get('code')}:{location}" if location else str(finding.get("code"))
    return EvidenceRef(f"report:{report}", ref)
