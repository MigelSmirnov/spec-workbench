#!/usr/bin/env python3
"""Deterministically assemble final http_router_backend/v1 from closed authoring IR.

This tool performs no semantic inference. It requires contract-aware route
closure and global Router context closure to be ready, then projects their
accepted fields into the normative ``rules.http_router_backend`` shape.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import design_router_context
from router_workbench import authoring as route_authoring
from router_workbench import catalog

SCHEMA = "spec_workbench_http_router_backend_handoff.v1"


class RouterIRAssemblyError(ValueError):
    pass


def assemble(project: Path) -> dict[str, Any]:
    routes_report = route_authoring.coverage(project)
    if not routes_report["summary"]["handoff_ready"]:
        raise RouterIRAssemblyError("contract-aware per-route closure is not ready")
    context_report = design_router_context.coverage(project)
    if not context_report["summary"]["handoff_ready"]:
        raise RouterIRAssemblyError("global Router context closure is not ready")

    context = design_router_context.load(project)
    route_catalog = catalog.load(project)
    routes: list[dict[str, Any]] = []
    for item in route_catalog["items"]:
        if item["emission"] == "unresolved":
            raise RouterIRAssemblyError(f"unresolved route reached assembler: {item['operation']}")
        routes.append({key: value for key, value in item.items() if key != "operation"})

    ir = {
        "kind": "http_router_backend",
        "schema_version": 1,
        "backend": context["backend"],
        "wiring": context["wiring"],
        "principals": context["principals"],
        "auth_policies": context["auth_policies"],
        "projections": context["projections"],
        "routes": routes,
        "error_policy": context["error_policy"],
        "irregular_ownership": route_catalog["irregular_ownership"],
    }
    return {
        "schema_version": SCHEMA,
        "project_root": project.resolve().name,
        "ready": True,
        "rules": {"http_router_backend": ir},
        "source_artifacts": ["70_router_context.json", "70_router_closure.json", "60_contracts.json"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--handoff", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.project.is_dir():
        print(f"design_router_ir: error: project directory not found: {args.project}", file=sys.stderr)
        return 2
    try:
        payload = assemble(args.project)
    except (RouterIRAssemblyError, ValueError) as exc:
        print(f"design_router_ir: error: {exc}", file=sys.stderr)
        return 1
    if args.json or args.handoff:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("http_router_backend/v1 handoff_ready=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
