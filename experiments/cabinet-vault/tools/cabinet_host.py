#!/usr/bin/env python3
"""Experimental trusted host for CABINET_V0 capability execution."""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any


class CabinetHostError(RuntimeError):
    pass


@dataclass(frozen=True)
class Grant:
    principal_id: str
    principal_status: str
    capabilities: frozenset[str]
    project_ids: frozenset[str]
    grant_id: str = "demo-grant"
    policy_version: str = "cabinet-v0"


def _digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(payload).hexdigest()


def load_definition(path: Path) -> dict[str, Any]:
    """Load the experimental YAML definition when PyYAML is available."""
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise CabinetHostError(
            "PyYAML is required only for loading CABINET_V0 YAML; core host execution uses stdlib only"
        ) from exc
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise CabinetHostError("cabinet definition must be a mapping")
    return data


class CabinetHost:
    """Small trusted kernel: authorize declared capability, then execute fixed lowering."""

    def __init__(self, definition: dict[str, Any], connection: sqlite3.Connection):
        self.definition = definition
        self.connection = connection
        self.audit_log: list[dict[str, Any]] = []

    def manifest_for(self, grant: Grant) -> dict[str, Any]:
        if grant.principal_status != "active":
            raise CabinetHostError("inactive_or_revoked_principal")
        declared = self.definition.get("capabilities", {})
        visible = {
            name: value
            for name, value in declared.items()
            if name in grant.capabilities
        }
        return {
            "cabinet": self.definition.get("cabinet", {}),
            "schemas": self.definition.get("schemas", {}),
            "capabilities": visible,
        }

    def execute(self, grant: Grant, request: dict[str, Any]) -> dict[str, Any]:
        if grant.principal_status != "active":
            raise CabinetHostError("inactive_or_revoked_principal")

        invoke = request.get("invoke", request)
        capability = invoke.get("capability")
        args = invoke.get("args", {})

        declared = self.definition.get("capabilities", {})
        if capability not in declared:
            raise CabinetHostError("unknown_capability")
        if capability not in grant.capabilities:
            raise CabinetHostError("capability_not_granted")
        if declared[capability].get("effects") not in (None, []):
            raise CabinetHostError("undeclared_effect")

        if capability == "invoice.summary":
            result = self._invoice_summary(grant, args)
        else:
            raise CabinetHostError("no_trusted_lowering")

        evidence = {
            "grant_id": grant.grant_id,
            "principal_id": grant.principal_id,
            "capability": capability,
            "resource_scope": sorted(grant.project_ids),
            "policy_version": grant.policy_version,
            "input_digest": _digest(args),
            "result_digest": _digest(result),
            "occurred_at": datetime.now(timezone.utc).isoformat(),
        }
        self.audit_log.append(evidence)
        return {**result, "evidence": evidence}

    def _invoice_summary(self, grant: Grant, args: dict[str, Any]) -> dict[str, Any]:
        project_id = args.get("project_id")
        if not isinstance(project_id, str) or not project_id:
            raise CabinetHostError("invalid_project_id")
        if project_id not in grant.project_ids:
            raise CabinetHostError("resource_scope_expansion")

        date_from = args.get("date_from")
        date_to = args.get("date_to")
        query = [
            "SELECT COUNT(*), COALESCE(SUM(confirmed_total), 0),",
            "       COUNT(DISTINCT currency), MIN(currency)",
            "FROM invoices",
            "WHERE project_id = ? AND confirmed = 1",
        ]
        params: list[Any] = [project_id]
        if date_from:
            query.append("AND invoice_date >= ?")
            params.append(date_from)
        if date_to:
            query.append("AND invoice_date <= ?")
            params.append(date_to)

        row = self.connection.execute("\n".join(query), params).fetchone()
        if row is None:
            raise CabinetHostError("execution_failed")
        count, total, currency_count, currency = row
        if currency_count > 1:
            raise CabinetHostError("mixed_currency_aggregate")

        return {
            "project_id": project_id,
            "invoice_count": int(count),
            "confirmed_total": str(Decimal(str(total))),
            "currency": currency if count else None,
        }


def build_demo_db() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute(
        """
        CREATE TABLE invoices (
            invoice_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            invoice_date TEXT NOT NULL,
            confirmed INTEGER NOT NULL,
            confirmed_total TEXT NOT NULL,
            currency TEXT NOT NULL,
            raw_source_path TEXT NOT NULL
        )
        """
    )
    connection.executemany(
        "INSERT INTO invoices VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            ("inv-1", "project-1", "2026-07-03", 1, "120.50", "EUR", "/secret/a.pdf"),
            ("inv-2", "project-1", "2026-07-11", 1, "79.50", "EUR", "/secret/b.pdf"),
            ("inv-3", "project-1", "2026-07-19", 0, "999.00", "EUR", "/secret/unconfirmed.pdf"),
            ("inv-4", "project-2", "2026-07-05", 1, "500.00", "EUR", "/secret/c.pdf"),
        ],
    )
    return connection


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "definition",
        type=Path,
        nargs="?",
        default=Path("experiments/cabinet-vault/cabinet_backend_invoice_summary.yaml"),
    )
    parser.add_argument("--project", default="project-1")
    parser.add_argument("--date-from")
    parser.add_argument("--date-to")
    args = parser.parse_args(argv)

    definition = load_definition(args.definition)
    host = CabinetHost(definition, build_demo_db())
    grant = Grant(
        principal_id="agent:local-example",
        principal_status="active",
        capabilities=frozenset({"invoice.summary"}),
        project_ids=frozenset({args.project}),
    )
    request = {
        "invoke": {
            "capability": "invoice.summary",
            "args": {
                "project_id": args.project,
                "date_from": args.date_from,
                "date_to": args.date_to,
            },
        }
    }
    print(json.dumps(host.execute(grant, request), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
