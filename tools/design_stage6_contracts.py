#!/usr/bin/env python3
"""Deterministic State 6 exact-contract authoring workbench.

State 6 owns canonical Python signatures and the explicit inventory of public
and internal functions. The workbench never invents signatures or private
helpers. Public functions are proven by accepted State 5 operations; internal
functions must be added explicitly to the State 6 plan by the author.

For deterministic HTTP projects, State 6 also owns the operation -> canonical
handler mapping. Router Closure may choose transport semantics only after every
externally exposed operation already has exactly one handler contract here.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import design_closure_gaps
import design_stage3
import design_stage5
import design_stage5_exposure

PLAN_SCHEMA = "spec_workbench_state6_contract_plan.v1"
CATALOG_SCHEMA = "spec_workbench_state6_contracts.v1"
COVERAGE_SCHEMA = "spec_workbench_state6_contract_coverage.v1"
LINT_SCHEMA = "spec_workbench_state6_contract_lint.v1"
HANDOFF_SCHEMA = "spec_workbench_state6_contract_handoff.v1"
NEXT_SCHEMA = "spec_workbench_state6_contract_next.v1"
DEFAULT_PLAN_FILE = "60_contract_plan.json"
DEFAULT_CATALOG_FILE = "60_contracts.json"
FUNCTION_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?$")
SIGNATURE_RE = re.compile(r"^\([^\n]*\)\s*->\s*[^\n]+$")
VISIBILITIES = {"public", "internal"}
PLAN_STATUSES = {"open", "closed"}


class DesignStage6ContractsError(ValueError):
    pass


def _read_json(path: Path, schema: str, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DesignStage6ContractsError(f"missing {path.name}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise DesignStage6ContractsError(f"invalid {path.name}: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != schema:
        raise DesignStage6ContractsError(f"unsupported {label} schema; expected {schema!r}")
    return payload


def load_plan(project: Path) -> dict[str, Any]:
    payload = _read_json(project / DEFAULT_PLAN_FILE, PLAN_SCHEMA, "State 6 contract plan")
    if payload.get("status") not in PLAN_STATUSES:
        raise DesignStage6ContractsError(f"State 6 contract plan status must be one of {sorted(PLAN_STATUSES)}")
    functions = payload.get("functions")
    if not isinstance(functions, list):
        raise DesignStage6ContractsError("State 6 contract plan must contain list 'functions'")
    return payload


def load_catalog(project: Path) -> dict[str, Any]:
    payload = _read_json(project / DEFAULT_CATALOG_FILE, CATALOG_SCHEMA, "State 6 contract catalog")
    contracts = payload.get("contracts")
    if not isinstance(contracts, dict):
        raise DesignStage6ContractsError("State 6 contract catalog must contain object 'contracts'")
    return payload


def _validate_plan(project: Path, plan: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    findings: list[dict[str, str]] = []
    normalized: list[dict[str, Any]] = []
    seen_functions: set[str] = set()
    seen_public_ops: set[str] = set()
    seen_router_ops: set[str] = set()

    state5 = design_stage5.coverage(project)
    accepted_ops = {row["key"]: row for row in state5["operations"] if row["implemented"]}
    exposure = design_stage5_exposure.lint(project)
    if exposure["summary"]["errors"]:
        findings.append({
            "severity": "error",
            "code": "invalid_exposure_boundary",
            "message": "State 5 exposure boundary must be valid before State 6 handler contracts are closed.",
        })
        external_ops: set[str] = set()
    else:
        external_ops = set(exposure["external_operations"])

    for index, entry in enumerate(plan["functions"]):
        location = f"functions[{index}]"
        if not isinstance(entry, dict):
            findings.append({"severity":"error","code":"invalid_plan_entry","message":f"{location} must be an object"})
            continue
        function = entry.get("function")
        module = entry.get("module")
        visibility = entry.get("visibility")
        purpose = entry.get("purpose")
        public_op = entry.get("public_operation")
        router_op = entry.get("router_operation")
        if not isinstance(function, str) or not FUNCTION_RE.fullmatch(function):
            findings.append({"severity":"error","code":"invalid_function_name","message":f"{location}.function is invalid"})
            continue
        if function in seen_functions:
            findings.append({"severity":"error","code":"duplicate_function","message":function})
        seen_functions.add(function)
        if not isinstance(module, str) or not module.startswith("module:"):
            findings.append({"severity":"error","code":"invalid_function_module","message":function})
        if visibility not in VISIBILITIES:
            findings.append({"severity":"error","code":"invalid_visibility","message":function})
        if not isinstance(purpose, str) or not purpose.strip():
            findings.append({"severity":"error","code":"missing_function_purpose","message":function})

        if visibility == "public":
            if router_op is not None:
                findings.append({"severity":"error","code":"public_has_router_operation","message":function})
            if not isinstance(public_op, str) or public_op not in accepted_ops:
                findings.append({"severity":"error","code":"invalid_public_operation","message":function})
            else:
                if public_op in seen_public_ops:
                    findings.append({"severity":"error","code":"duplicate_public_operation_mapping","message":public_op})
                seen_public_ops.add(public_op)
                expected_module = "module:" + public_op.removeprefix("public_op:").split(".", 1)[0]
                expected_function = public_op.rsplit(".", 1)[1]
                if module != expected_module:
                    findings.append({"severity":"error","code":"public_owner_mismatch","message":f"{function}: expected {expected_module}"})
                if function != expected_function:
                    findings.append({"severity":"error","code":"public_function_name_mismatch","message":f"{public_op}: expected function {expected_function}"})
        else:
            if public_op is not None:
                findings.append({"severity":"error","code":"internal_has_public_operation","message":function})
            if router_op is not None:
                if not isinstance(router_op, str) or router_op not in external_ops:
                    findings.append({"severity":"error","code":"invalid_router_operation","message":f"{function}: {router_op!r}"})
                elif router_op in seen_router_ops:
                    findings.append({"severity":"error","code":"duplicate_router_handler","message":router_op})
                else:
                    seen_router_ops.add(router_op)

        normalized.append({
            "function": function,
            "module": module,
            "visibility": visibility,
            "public_operation": public_op,
            "router_operation": router_op,
            "purpose": purpose,
        })

    missing_public = sorted(set(accepted_ops) - seen_public_ops)
    for operation in missing_public:
        findings.append({"severity":"error","code":"missing_public_function","message":operation})
    missing_handlers = sorted(external_ops - seen_router_ops)
    for operation in missing_handlers:
        findings.append({"severity":"error","code":"missing_router_handler_contract","message":operation})
    return findings, normalized


def coverage(project: Path) -> dict[str, Any]:
    plan = load_plan(project)
    catalog = load_catalog(project)
    findings, functions = _validate_plan(project, plan)
    contracts: dict[str, Any] = catalog["contracts"]
    planned = {entry["function"] for entry in functions}
    catalog_keys = set(contracts)
    unknown = sorted(catalog_keys - planned)
    for function in unknown:
        findings.append({"severity":"error","code":"unplanned_contract","message":function})

    unresolved: list[str] = []
    rows: list[dict[str, Any]] = []
    for entry in functions:
        function = entry["function"]
        signature = contracts.get(function)
        resolved = isinstance(signature, str) and bool(signature.strip()) and signature != "unresolved"
        if resolved and not SIGNATURE_RE.fullmatch(signature.strip()):
            findings.append({"severity":"error","code":"invalid_signature_shape","message":function})
        if not resolved:
            unresolved.append(function)
        rows.append({**entry, "signature": signature, "resolved": resolved})

    module_surface = _module_surface(project, rows)
    for item in module_surface:
        if item["shallow"]:
            findings.append({
                "severity": "warning",
                "code": "module_surface_not_deep",
                "message": (
                    f"{item['module']}: {item['public']} of {item['functions']} owned functions are public "
                    f"(ratio {item['public_ratio']}); the module hides almost nothing behind its surface. "
                    "Split it along its hidden mechanisms or declare it a façade in State 3."
                ),
            })

    for item in _time_source_findings(project, rows):
        findings.append({"severity": "warning", "code": item["code"], "message": item["message"]})

    findings.extend(_interface_provider_findings(project, rows))

    plan_closed = plan["status"] == "closed"
    if not plan_closed:
        findings.append({
            "severity":"warning",
            "code":"contract_plan_open",
            "message":"State 6 function inventory remains open; review and add required internal functions before handoff.",
        })
    errors = sum(item["severity"] == "error" for item in findings)
    ready = plan_closed and not unresolved and errors == 0
    return {
        "schema_version": COVERAGE_SCHEMA,
        "project_root": project.resolve().name,
        "summary": {
            "planned_functions": len(functions),
            "public_functions": sum(row["visibility"] == "public" for row in rows),
            "internal_functions": sum(row["visibility"] == "internal" for row in rows),
            "resolved": sum(row["resolved"] for row in rows),
            "unresolved": len(unresolved),
            "errors": errors,
            "plan_closed": plan_closed,
            "handoff_ready": ready,
        },
        "functions": rows,
        "module_surface": module_surface,
        "unresolved_functions": sorted(unresolved),
        "findings": findings,
    }


SHALLOW_SURFACE_MIN_FUNCTIONS = 6
SHALLOW_SURFACE_PUBLIC_RATIO = 0.85


def _module_surface(project: Path, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Per module: how much of the owned function surface is public, against the State 3 depth declaration."""
    try:
        depth_by_module = {item.name: item.depth for item in design_stage3.parse_modules(project)}
    except OSError:
        depth_by_module = {}
    counts: dict[str, dict[str, int]] = {}
    for row in rows:
        module = str(row.get("module") or "").removeprefix("module:")
        if not module:
            continue
        bucket = counts.setdefault(module, {"public": 0, "internal": 0})
        bucket["public" if row.get("visibility") == "public" else "internal"] += 1
    result: list[dict[str, Any]] = []
    for module in sorted(counts):
        public = counts[module]["public"]
        total = public + counts[module]["internal"]
        ratio = round(public / total, 3) if total else 0.0
        kind = (depth_by_module.get(module) or {}).get("kind")
        shallow = (
            kind != "facade"
            and total >= SHALLOW_SURFACE_MIN_FUNCTIONS
            and ratio >= SHALLOW_SURFACE_PUBLIC_RATIO
        )
        result.append({
            "module": module,
            "functions": total,
            "public": public,
            "internal": counts[module]["internal"],
            "public_ratio": ratio,
            "depth_kind": kind,
            "shallow": shallow,
        })
    return result


def _time_source_findings(project: Path, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """A mutating public operation that must produce a timestamp needs a declared time source.

    Runs the same fuse the assembly-level closure gaps enforce, but at the
    moment the signature is authored — while a datetime parameter or a clock
    port in __init__ is still a State 6 decision, not a regeneration."""
    models: dict[str, Any] = {}
    for path in sorted(project.glob("60_model_closure*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict) and isinstance(payload.get("models"), dict):
            models.update(payload["models"])
    contracts = {row["function"]: row["signature"] for row in rows if row["resolved"]}
    func_module = {row["function"]: str(row["module"] or "").removeprefix("module:") for row in rows}
    impacts = design_closure_gaps.parse_state_impacts(project)
    return design_closure_gaps.fresh_timestamp_findings(models, contracts, func_module, impacts)


NOTES_FILE = "80_notes.md"
MODULE_OWNED_RE = re.compile(r"module-owned")


def _camel(module: str) -> str:
    return "".join(part.capitalize() for part in module.split("_") if part)


def _interface_provider_findings(project: Path, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """An interface a module hands out must have a declared implementation.

    A class whose methods are planned only under ``module:models`` is a port:
    it has operations and no constructor of its own. When a function returns
    such a port and no planned class outside ``models`` carries the port's
    operations, the concrete provider exists nowhere in the design — and a
    note saying "construct the module-owned concrete InvoicePackageStream"
    is an obligation without a surface. Every generation then invents a
    private class or leaves the function a stub. The finding names the
    provider the plan must declare, method by method, so the repair is a
    plan edit and not a guess."""
    classes: dict[str, dict[str, set[str]]] = {}
    for row in rows:
        function = row["function"]
        if "." not in function:
            continue
        owner, method = function.split(".", 1)
        bucket = classes.setdefault(owner, {"modules": set(), "methods": set()})
        bucket["modules"].add(str(row.get("module") or ""))
        bucket["methods"].add(method)
    interfaces = {
        name: bucket["methods"] - {"__init__"}
        for name, bucket in classes.items()
        if bucket["modules"] == {"module:models"} and bucket["methods"] - {"__init__"}
    }
    if not interfaces:
        return []

    signatures = {row["function"]: row["signature"] for row in rows if row["resolved"]}
    notes_text = ""
    notes_path = project / NOTES_FILE
    if notes_path.is_file():
        try:
            notes_text = notes_path.read_text(encoding="utf-8")
        except OSError:
            notes_text = ""

    findings: list[dict[str, Any]] = []
    for interface in sorted(interfaces):
        operations = sorted(interfaces[interface])
        providers = sorted(
            name for name, bucket in classes.items()
            if name != interface and "module:models" not in bucket["modules"]
            and set(operations) <= bucket["methods"]
        )
        if providers:
            continue
        returners: list[tuple[str, str]] = []
        for row in rows:
            function = row["function"]
            signature = signatures.get(function)
            if function.startswith(interface + ".") or not isinstance(signature, str) or "->" not in signature:
                continue
            if re.search(rf"\b{re.escape(interface)}\b", signature.rsplit("->", 1)[1]):
                returners.append((str(row.get("module") or "").removeprefix("module:"), function))
        owned_by_note = sorted({
            module for module, function in returners
            if any(
                MODULE_OWNED_RE.search(line) and re.search(rf"\b{re.escape(interface)}\b", line)
                for line in notes_text.splitlines()
                if line.startswith(function + ":")
            )
        })
        if not returners:
            continue
        modules = owned_by_note or sorted({module for module, _ in returners})
        suggested = {module: f"{_camel(module)}{interface}" for module in modules}
        plan_entries = [
            {"function": f"{suggested[module]}.{method}", "module": f"module:{module}", "visibility": "internal"}
            for module in modules
            for method in ["__init__", *operations]
        ]
        contract_entries = {
            f"{suggested[module]}.{method}": signatures.get(f"{interface}.{method}", "unresolved")
            for module in modules
            for method in operations
        }
        where = ", ".join(f"{module}.{function}" for module, function in returners)
        findings.append({
            "severity": "error",
            "code": "interface_without_provider",
            "message": (
                f"{interface} is returned by {where}"
                + (" (its note requires a module-owned concrete implementation)" if owned_by_note else "")
                + f" and no planned class outside module:models implements {', '.join(operations)}. "
                f"Declare the provider in {DEFAULT_PLAN_FILE}: internal functions "
                + ", ".join(f"{suggested[m]}.__init__ and {suggested[m]}.{{{', '.join(operations)}}}" for m in modules)
                + f" under {', '.join('module:' + m for m in modules)}; resolve them in {DEFAULT_CATALOG_FILE} "
                f"(the interface signatures: {'; '.join(f'{op}: {signatures.get(interface + '.' + op, 'unresolved')}' for op in operations)}); "
                f"then note each method in {NOTES_FILE}. Or return the interface from a provider another module declares."
            ),
            "interface": interface,
            "operations": operations,
            "returned_by": [f"{module}.{function}" for module, function in returners],
            "modules": modules,
            "prescription": {
                "plan_entries": plan_entries,
                "contract_entries": contract_entries,
                "note_scopes": sorted(contract_entries),
            },
        })
    return findings


def lint(project: Path) -> dict[str, Any]:
    report = coverage(project)
    return {
        "schema_version": LINT_SCHEMA,
        "project_root": report["project_root"],
        "summary": {**report["summary"], "warnings": sum(item["severity"] == "warning" for item in report["findings"])},
        "findings": report["findings"],
    }


def next_function(project: Path) -> dict[str, Any]:
    report = coverage(project)
    function = report["unresolved_functions"][0] if report["unresolved_functions"] else None
    row = next((item for item in report["functions"] if item["function"] == function), None)
    return {
        "schema_version": NEXT_SCHEMA,
        "project_root": report["project_root"],
        "complete": function is None and report["summary"]["handoff_ready"],
        "next": row,
        "summary": report["summary"],
    }


def handoff(project: Path) -> dict[str, Any]:
    report = coverage(project)
    return {
        "schema_version": HANDOFF_SCHEMA,
        "project_root": report["project_root"],
        "ready": report["summary"]["handoff_ready"],
        "summary": report["summary"],
        "contracts": {
            row["function"]: {
                "module": row["module"],
                "visibility": row["visibility"],
                "public_operation": row["public_operation"],
                "router_operation": row["router_operation"],
                "signature": row["signature"],
            }
            for row in report["functions"] if row["resolved"]
        },
        "unresolved_functions": report["unresolved_functions"],
        "findings": report["findings"],
    }


def _human(action: str, payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    if action == "next":
        target = payload["next"]["function"] if payload["next"] else "complete"
        return f"State 6 contracts next: {target}\n"
    return (
        f"State 6 contracts: {summary['resolved']}/{summary['planned_functions']} resolved; "
        f"{summary['unresolved']} unresolved; {summary['errors']} errors; "
        f"plan_closed={str(summary['plan_closed']).lower()}; "
        f"handoff_ready={str(summary['handoff_ready']).lower()}\n"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--coverage", action="store_true")
    action.add_argument("--lint", action="store_true")
    action.add_argument("--next", action="store_true")
    action.add_argument("--handoff", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.project.is_dir():
        print(f"design_stage6_contracts: error: project directory not found: {args.project}", file=sys.stderr)
        return 2
    selected = "coverage" if args.coverage else "lint" if args.lint else "next" if args.next else "handoff"
    try:
        payload = next_function(args.project) if selected == "next" else globals()[selected](args.project)
    except DesignStage6ContractsError as exc:
        print(f"design_stage6_contracts: error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) if args.json else _human(selected, payload))
    if selected in {"coverage", "handoff"}:
        return 0 if payload["summary"]["handoff_ready"] else 1
    if selected == "lint":
        return 1 if payload["summary"]["errors"] else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
