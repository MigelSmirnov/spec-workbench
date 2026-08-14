from __future__ import annotations

from pathlib import Path
from typing import Any

from notes_workbench import service as notes_service

from module_review_workbench.model import MODULES_SCHEMA, REVIEW_SCHEMA, SLICE_SCHEMA, ModuleReviewError
from module_review_workbench.sources import (
    assembled_notes, decisions, load_json, module_owned_persistence,
    referenced_models, rule_values, state1_models,
)

def _spec(project: Path) -> dict[str, Any]:
    return load_json(project / "global_spec.json")

def list_modules(project: Path) -> dict[str, Any]:
    spec = _spec(project)
    modules = list(spec.get("module_order", []))
    return {"schema_version": MODULES_SCHEMA, "project_root": project.resolve().name, "modules": modules}

def build_slice(project: Path, module: str) -> dict[str, Any]:
    spec = _spec(project)
    module_name = module.removeprefix("module:")
    owned = spec.get("module_functions", {}).get(module_name)
    if not isinstance(owned, list):
        raise ModuleReviewError(f"Unknown assembled module: {module_name}")
    symbols = set(owned)
    contracts = {name: value for name, value in spec.get("contracts", {}).items()
                 if name in symbols or name.split(".", 1)[0] in symbols}
    notes = assembled_notes(spec, module_name, set(contracts) | symbols)
    design_module = "domain_models" if module_name == "models" else module_name
    try:
        semantic = notes_service.module_slice(project, design_module)
    except ValueError:
        semantic = {
            "responsibility": None, "flows": [], "public_operations": [],
        }
    exports = spec.get("imports", {}).get("internal", {}).get(module_name, [])
    dependencies = spec.get("imports", {}).get("module_internal", {}).get(module_name, {})
    dependency_symbols = {
        symbol
        for provider_symbols in dependencies.values()
        if isinstance(provider_symbols, list)
        for symbol in provider_symbols
        if isinstance(symbol, str)
    }
    dependency_contracts = {
        name: value
        for name, value in spec.get("contracts", {}).items()
        if name in dependency_symbols or name.split(".", 1)[0] in dependency_symbols
    }
    persistence_catalog = spec.get("persistence", {})
    persistent_ownership = module_owned_persistence(project, module_name, set(persistence_catalog))
    models = referenced_models(
        spec,
        {**contracts, **dependency_contracts},
        symbols | dependency_symbols,
        persistent_ownership,
    )
    persistence = {name: value for name, value in spec.get("persistence", {}).items() if name in models}
    router_handoff = spec.get("rules", {}).get("http_router_backend", {})
    router = router_handoff.get("rules", {}).get("http_router_backend", router_handoff)
    routes = [route for route in router.get("routes", []) if route.get("handler") in symbols]
    deterministic_callables = sorted(
        route["handler"] for route in routes
        if route.get("emission") == "table" and route.get("handler") in contracts
    )
    return {
        "schema_version": SLICE_SCHEMA,
        "project_root": project.resolve().name,
        "module": module_name,
        "accepted_evidence": {
            "responsibility": semantic["responsibility"],
            "state1_models": state1_models(project, set(models)),
            "decisions": decisions(project, f"module:{module_name}"),
            "flows": semantic["flows"],
            "public_operations": semantic["public_operations"],
        },
        "lowered_specification": {
            "owned_symbols": owned,
            "exports": exports,
            "contracts": contracts,
            "dependency_contracts": dependency_contracts,
            "models": models,
            "persistence": persistence,
            "dependencies": dependencies,
            "routes": routes,
            "deterministic_callables": deterministic_callables,
            "rules": rule_values(spec, notes),
        },
        "generation_constraints": {
            "assembled_notes": notes,
            "note_count": len(notes),
        },
        "review_protocol": {
            "questions": [
                "Can a materially different observable behavior satisfy this complete module slice?",
                "Can any callable return a trivial result or blindly forward input without violating the slice?",
                "Can every accepted error, refusal, state effect, and invariant be located in the lowered specification?",
                "Does the lowered specification introduce behavior with no accepted business source?",
            ],
            "allowed_semantic_results": ["PASS", "PASS_INTERNAL_VARIATION", "AMBIGUITY"],
        },
    }

def review(project: Path, module: str) -> dict[str, Any]:
    packet = build_slice(project, module)
    accepted = packet["accepted_evidence"]
    lowered = packet["lowered_specification"]
    notes = packet["generation_constraints"]["assembled_notes"]
    findings: list[dict[str, Any]] = []
    contract_names = set(lowered["contracts"])
    note_scopes = {note["scope"] for note in notes}
    deterministic = set(lowered["deterministic_callables"])
    for name in sorted(contract_names - note_scopes - deterministic):
        findings.append({"severity":"block","code":"callable_without_assembled_note","scope":name,
                         "message":"Callable has no assembled generation constraint."})
    for rule in lowered["rules"]:
        if not rule["resolved"]:
            findings.append({"severity":"block","code":"unresolved_rule_reference","address":rule["address"],
                             "message":"Assembled note references an unresolved rule address."})
    final_public = set(lowered["exports"]) & contract_names
    accepted_ops = {op["key"].rsplit(".", 1)[-1] for op in accepted["public_operations"]}
    for name in sorted(accepted_ops - final_public):
        findings.append({"severity":"review","code":"accepted_operation_not_exported","scope":name,
                         "message":"Accepted State 5 operation is not a final exported callable; confirm intentional lowering or removal."})
    decision_keys = {decision["key"] for decision in accepted["decisions"]}
    missing_decisions = sorted(key for key in decision_keys if next(
        (d for d in accepted["decisions"] if d["key"] == key and d["text"]), None
    ) is None)
    for key in missing_decisions:
        findings.append({"severity":"review","code":"decision_source_not_indexed","decision":key,
                         "message":"Trace relation exists but the accepted decision source is not structurally indexed."})
    return {
        "schema_version": REVIEW_SCHEMA,
        "project_root": packet["project_root"],
        "module": packet["module"],
        "summary": {
            "contracts": len(contract_names), "assembled_notes": len(notes),
            "decisions": len(accepted["decisions"]), "flows": len(accepted["flows"]),
            "blocks": sum(f["severity"] == "block" for f in findings),
            "reviews": sum(f["severity"] == "review" for f in findings),
        },
        "findings": findings,
        "semantic_review_required": True,
    }
