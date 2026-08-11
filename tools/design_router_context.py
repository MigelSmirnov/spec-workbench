#!/usr/bin/env python3
"""Deterministic global http_router_backend context-closure workbench.

This phase follows per-route Router Closure and freezes global backend/wiring,
principal/auth-policy, projection and error-policy declarations. It is
fail-closed: unresolved canonical exception taxonomy prevents Router IR handoff.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import design_stage6_contracts
from router_workbench import authoring as route_authoring
from router_workbench.refs import validate_argument_refs

SCHEMA = "spec_workbench_router_context.v1"
REPORT_SCHEMA = "spec_workbench_router_context_coverage.v1"
FILE = "70_router_context.json"


class RouterContextError(ValueError):
    pass


def load(project: Path) -> dict[str, Any]:
    path = project / FILE
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RouterContextError(f"missing {FILE}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise RouterContextError(f"invalid {FILE}: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA:
        raise RouterContextError(f"unsupported Router context schema; expected {SCHEMA!r}")
    return payload


def coverage(project: Path) -> dict[str, Any]:
    payload = load(project)
    findings: list[dict[str, str]] = []
    contracts = design_stage6_contracts.handoff(project)
    if not contracts["ready"]:
        findings.append({"severity":"error","code":"state6_not_ready","message":"State 6 canonical contract handoff must be ready."})
    routes = route_authoring.coverage(project)
    if not routes["summary"]["handoff_ready"]:
        findings.append({"severity":"error","code":"route_catalog_not_ready","message":"Contract-aware per-route closure must be ready before global Router context closure."})

    backend = payload.get("backend")
    if backend != {"framework": "fastapi", "emitter": "fastapi_sync_v1"}:
        findings.append({"severity":"error","code":"invalid_backend","message":"backend must select the accepted fastapi_sync_v1 deterministic emitter."})
    wiring = payload.get("wiring")
    if not isinstance(wiring, dict):
        findings.append({"severity":"error","code":"invalid_wiring","message":"wiring must be an object."})
        wiring = {}
    contract_map = contracts.get("contracts", {})
    app_factory = wiring.get("app_factory")
    if app_factory not in contract_map:
        findings.append({"severity":"error","code":"unknown_app_factory","message":str(app_factory)})
    request_parameter = wiring.get("request_parameter")
    if request_parameter != "request":
        findings.append({"severity":"error","code":"invalid_request_parameter","message":"v1 Cabinet handlers use canonical request parameter 'request'."})
    state_bindings = wiring.get("state_bindings")
    if not isinstance(state_bindings, dict) or not state_bindings:
        findings.append({"severity":"error","code":"missing_state_bindings","message":"state_bindings must be a non-empty object."})
    extractors = wiring.get("credential_extractors")
    if not isinstance(extractors, dict) or not extractors:
        findings.append({"severity":"error","code":"missing_credential_extractors","message":"credential_extractors must be a non-empty object."})
        extractors = {}
    for name, extractor in sorted(extractors.items()):
        if not isinstance(extractor, dict) or extractor.get("kind") != "header_scheme":
            findings.append({"severity":"error","code":"invalid_credential_extractor","message":name})
            continue
        if extractor.get("function") not in contract_map:
            findings.append({"severity":"error","code":"unknown_extractor_function","message":name})
        if extractor.get("exception") in {None, "", "unresolved"}:
            findings.append({"severity":"error","code":"unresolved_extractor_exception","message":name})

    principals = payload.get("principals")
    if not isinstance(principals, dict):
        findings.append({"severity":"error","code":"invalid_principals","message":"principals must be an object."})
        principals = {}
    for name, principal in sorted(principals.items()):
        if not isinstance(principal, dict) or principal.get("resolver") not in contract_map:
            findings.append({"severity":"error","code":"unknown_principal_resolver","message":name})
            continue
        refs = validate_argument_refs({"args": principal.get("args")}, operation=None, location=f"principals.{name}")
        findings.extend({"severity":f.severity,"code":f.code,"message":f.message} for f in refs)

    policies = payload.get("auth_policies")
    if not isinstance(policies, dict):
        findings.append({"severity":"error","code":"invalid_auth_policies","message":"auth_policies must be an object."})
        policies = {}
    for name, policy in sorted(policies.items()):
        principal = policy.get("principal") if isinstance(policy, dict) else None
        if principal is not None and principal not in principals:
            findings.append({"severity":"error","code":"unknown_auth_policy_principal","message":name})

    route_payload = json.loads((project / "70_router_closure.json").read_text(encoding="utf-8"))
    for item in route_payload.get("items", []):
        if isinstance(item, dict) and item.get("emission") != "unresolved" and item.get("auth") not in policies:
            findings.append({"severity":"error","code":"unknown_route_auth_policy","message":str(item.get("operation"))})

    error_policy = payload.get("error_policy")
    if not isinstance(error_policy, dict):
        findings.append({"severity":"error","code":"invalid_error_policy","message":"error_policy must be an object."})
        error_policy = {}
    if error_policy.get("body") != "empty":
        findings.append({"severity":"error","code":"invalid_error_body","message":"http_router_backend/v1 uses body='empty'."})
    mapping = error_policy.get("mapping")
    if not isinstance(mapping, list) or not mapping:
        findings.append({"severity":"error","code":"missing_error_mapping","message":"error_policy.mapping must be non-empty before Router IR handoff."})

    unresolved = payload.get("unresolved")
    if not isinstance(unresolved, list):
        findings.append({"severity":"error","code":"invalid_unresolved","message":"unresolved must be a list."})
        unresolved = []
    topics = sorted(str(item.get("topic")) for item in unresolved if isinstance(item, dict) and item.get("topic"))
    errors = sum(item["severity"] == "error" for item in findings)
    ready = payload.get("status") == "closed" and not topics and errors == 0
    return {
        "schema_version": REPORT_SCHEMA,
        "project_root": project.resolve().name,
        "summary": {"errors": errors, "unresolved": len(topics), "handoff_ready": ready},
        "unresolved_topics": topics,
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--coverage", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.project.is_dir():
        print(f"design_router_context: error: project directory not found: {args.project}", file=sys.stderr)
        return 2
    try:
        report = coverage(args.project)
    except (RouterContextError, ValueError) as exc:
        print(f"design_router_context: error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        s = report["summary"]
        print(f"Router context: {s['errors']} errors; {s['unresolved']} unresolved; handoff_ready={str(s['handoff_ready']).lower()}")
    return 0 if report["summary"]["handoff_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
