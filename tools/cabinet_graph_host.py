#!/usr/bin/env python3
"""Experimental CABINET_V0 host for bounded execution graphs."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from cabinet_host import CabinetHostError, Grant, _digest, build_demo_db, load_definition


@dataclass(frozen=True)
class InvoiceRefSet:
    """Opaque cabinet-local working set. Never serialize this object to an agent."""

    project_id: str
    invoice_ids: tuple[str, ...]


class CabinetGraphHost:
    def __init__(self, definition: dict[str, Any], connection):
        self.definition = definition
        self.connection = connection
        self.audit_log: list[dict[str, Any]] = []

    def manifest_for(self, grant: Grant) -> dict[str, Any]:
        if grant.principal_status != "active":
            raise CabinetHostError("inactive_or_revoked_principal")
        declared = self.definition.get("capabilities", {})
        return {
            "cabinet": self.definition.get("cabinet", {}),
            "schemas": self.definition.get("schemas", {}),
            "capabilities": {
                name: spec for name, spec in declared.items() if name in grant.capabilities
            },
        }

    def execute_graph(self, grant: Grant, graph: dict[str, Any]) -> dict[str, Any]:
        if grant.principal_status != "active":
            raise CabinetHostError("inactive_or_revoked_principal")

        nodes = graph.get("nodes")
        output_spec = graph.get("output")
        if not isinstance(nodes, list) or not isinstance(output_spec, dict):
            raise CabinetHostError("invalid_execution_graph")

        values: dict[str, Any] = {}
        trace: list[dict[str, Any]] = []
        seen: set[str] = set()
        for node in nodes:
            if not isinstance(node, dict):
                raise CabinetHostError("invalid_execution_node")
            node_id = node.get("id")
            capability = node.get("capability")
            raw_args = node.get("args", {})
            if not isinstance(node_id, str) or not node_id:
                raise CabinetHostError("invalid_node_id")
            if node_id in seen:
                raise CabinetHostError("duplicate_node_id")
            seen.add(node_id)

            self._authorize_capability(grant, capability)
            args = self._resolve_args(raw_args, values)
            value = self._execute_node(grant, capability, args)
            values[node_id] = value
            trace.append({"node": node_id, "capability": capability, "input_digest": _digest(raw_args)})

        output_id = output_spec.get("from")
        if output_id not in values:
            raise CabinetHostError("invalid_graph_output")
        result = values[output_id]
        if isinstance(result, InvoiceRefSet):
            raise CabinetHostError("non_opaque_intermediate_escape")
        if not isinstance(result, dict):
            raise CabinetHostError("invalid_graph_output")

        evidence = {
            "grant_id": grant.grant_id,
            "principal_id": grant.principal_id,
            "graph_digest": _digest(graph),
            "policy_version": grant.policy_version,
            "trace": trace,
            "result_digest": _digest(result),
            "occurred_at": datetime.now(timezone.utc).isoformat(),
        }
        self.audit_log.append(evidence)
        return {**result, "evidence": evidence}

    def _authorize_capability(self, grant: Grant, capability: Any) -> None:
        declared = self.definition.get("capabilities", {})
        if capability not in declared:
            raise CabinetHostError("unknown_capability")
        if capability not in grant.capabilities:
            raise CabinetHostError("capability_not_granted")
        if declared[capability].get("effects") not in (None, []):
            raise CabinetHostError("undeclared_effect")

    def _resolve_args(self, value: Any, values: dict[str, Any]) -> Any:
        if isinstance(value, dict):
            if set(value) == {"from"}:
                ref = value["from"]
                if ref not in values:
                    raise CabinetHostError("unknown_node_reference")
                return values[ref]
            return {key: self._resolve_args(item, values) for key, item in value.items()}
        if isinstance(value, list):
            return [self._resolve_args(item, values) for item in value]
        return value

    def _execute_node(self, grant: Grant, capability: str, args: dict[str, Any]) -> Any:
        if capability == "invoice.select":
            return self._select(grant, args)
        if capability == "invoice.filter_confirmed":
            return self._filter_confirmed(args)
        if capability == "invoice.filter_date":
            return self._filter_date(args)
        if capability == "invoice.aggregate_total":
            return self._aggregate_total(args)
        raise CabinetHostError("no_trusted_lowering")

    def _require_refset(self, args: dict[str, Any]) -> InvoiceRefSet:
        source = args.get("source")
        if not isinstance(source, InvoiceRefSet):
            raise CabinetHostError("invalid_opaque_handle")
        return source

    def _select(self, grant: Grant, args: dict[str, Any]) -> InvoiceRefSet:
        project_id = args.get("project_id")
        if not isinstance(project_id, str) or not project_id:
            raise CabinetHostError("invalid_project_id")
        if project_id not in grant.project_ids:
            raise CabinetHostError("resource_scope_expansion")
        rows = self.connection.execute(
            "SELECT invoice_id FROM invoices WHERE project_id = ? ORDER BY invoice_id",
            (project_id,),
        ).fetchall()
        return InvoiceRefSet(project_id, tuple(row[0] for row in rows))

    def _filter_confirmed(self, args: dict[str, Any]) -> InvoiceRefSet:
        source = self._require_refset(args)
        if not source.invoice_ids:
            return source
        marks = ",".join("?" for _ in source.invoice_ids)
        rows = self.connection.execute(
            f"SELECT invoice_id FROM invoices WHERE confirmed = 1 AND invoice_id IN ({marks}) ORDER BY invoice_id",
            source.invoice_ids,
        ).fetchall()
        return InvoiceRefSet(source.project_id, tuple(row[0] for row in rows))

    def _filter_date(self, args: dict[str, Any]) -> InvoiceRefSet:
        source = self._require_refset(args)
        if not source.invoice_ids:
            return source
        marks = ",".join("?" for _ in source.invoice_ids)
        query = [f"SELECT invoice_id FROM invoices WHERE invoice_id IN ({marks})"]
        params: list[Any] = list(source.invoice_ids)
        date_from = args.get("date_from")
        date_to = args.get("date_to")
        if date_from:
            query.append("AND invoice_date >= ?")
            params.append(str(date_from))
        if date_to:
            query.append("AND invoice_date <= ?")
            params.append(str(date_to))
        query.append("ORDER BY invoice_id")
        rows = self.connection.execute("\n".join(query), params).fetchall()
        return InvoiceRefSet(source.project_id, tuple(row[0] for row in rows))

    def _aggregate_total(self, args: dict[str, Any]) -> dict[str, Any]:
        source = self._require_refset(args)
        if not source.invoice_ids:
            return {
                "project_id": source.project_id,
                "invoice_count": 0,
                "confirmed_total": "0",
                "currency": None,
            }
        marks = ",".join("?" for _ in source.invoice_ids)
        row = self.connection.execute(
            f"""
            SELECT COUNT(*), COALESCE(SUM(confirmed_total), 0),
                   COUNT(DISTINCT currency), MIN(currency)
            FROM invoices
            WHERE invoice_id IN ({marks})
            """,
            source.invoice_ids,
        ).fetchone()
        if row is None:
            raise CabinetHostError("execution_failed")
        count, total, currency_count, currency = row
        if currency_count > 1:
            raise CabinetHostError("mixed_currency_aggregate")
        return {
            "project_id": source.project_id,
            "invoice_count": int(count),
            "confirmed_total": str(Decimal(str(total))),
            "currency": currency,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "definition",
        type=Path,
        nargs="?",
        default=Path("experiments/cabinet-vault/cabinet_backend_execution_graph.yaml"),
    )
    args = parser.parse_args(argv)
    definition = load_definition(args.definition)
    host = CabinetGraphHost(definition, build_demo_db())
    grant = Grant(
        principal_id="agent:local-example",
        principal_status="active",
        capabilities=frozenset(definition["grant"]["capabilities"]),
        project_ids=frozenset(definition["grant"]["resource_scope"]["project_ids"]),
        grant_id="graph-demo-grant",
    )
    result = host.execute_graph(grant, definition["execution_graph"])
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
