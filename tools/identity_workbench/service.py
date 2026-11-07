from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from identity_workbench.model import Finding, IdentityWorkbenchError, INSPECTION_SCHEMA, INVENTORY_SCHEMA, VERIFICATION_SCHEMA
from identity_workbench.sources import load_assembled, load_closure, load_contract_closure, load_state1

def _load(project: Path):
    state1, state1_findings = load_state1(project)
    closure, closure_findings = load_closure(project)
    contract_closure, contract_closure_findings = load_contract_closure(project)
    assembled, assembled_findings = load_assembled(project)
    return state1, closure, contract_closure, assembled, [*state1_findings, *closure_findings, *contract_closure_findings, *assembled_findings]

def inventory(project: Path) -> dict[str, Any]:
    state1, closure, contract_closure, assembled, findings = _load(project)
    names = sorted(set(state1) | set(closure) | set(contract_closure) | set(assembled))
    return {
        "schema_version": INVENTORY_SCHEMA,
        "project_root": project.resolve().name,
        "models": [{
            "name": name,
            "state1": state1.get(name).identity if name in state1 else None,
            "closure": closure.get(name).identity if name in closure else None,
            "contract_closure": contract_closure.get(name).identity if name in contract_closure else None,
            "assembled": assembled.get(name).identity if name in assembled else None,
        } for name in names],
        "summary": {
            "models": len(names), "state1_models": len(state1),
            "closure_models": len(closure), "contract_models": len(contract_closure), "assembled_runtime_models": len(assembled),
            "source_errors": len(findings),
        },
        "findings": [finding.to_dict() for finding in findings],
    }

def inspect_model(project: Path, name: str) -> dict[str, Any]:
    state1, closure, contract_closure, assembled, findings = _load(project)
    if name not in set(state1) | set(closure) | set(contract_closure) | set(assembled):
        raise IdentityWorkbenchError(f"Unknown model: {name}")
    sources = {
        "state1": state1.get(name).to_dict() if name in state1 else None,
        "closure": closure.get(name).to_dict() if name in closure else None,
        "contract_closure": contract_closure.get(name).to_dict() if name in contract_closure else None,
        "assembled": assembled.get(name).to_dict() if name in assembled else None,
    }
    present = [source["identity"] for source in sources.values() if source]
    return {
        "schema_version": INSPECTION_SCHEMA,
        "project_root": project.resolve().name,
        "model": name,
        "consistent": len(set(present)) == 1 and (
            len(present) == 3 or (name in contract_closure and len(present) == 2)
        ),
        "sources": sources,
        "findings": [finding.to_dict() for finding in findings if finding.model == name],
    }

def verify(project: Path) -> dict[str, Any]:
    state1, closure, contract_closure, assembled, findings = _load(project)
    findings = list(findings)
    for name, record in sorted(assembled.items()):
        if name in contract_closure:
            if contract_closure[name].identity != record.identity:
                findings.append(Finding("contract_closure_identity_mismatch", f"{name}: assembled={record.identity}, contract closure={contract_closure[name].identity}.", name, contract_closure[name].location))
            continue
        if name not in state1:
            findings.append(Finding("missing_state1_model", f"Assembled runtime model {name} has no canonical State 1 model record.", name, record.location))
        elif state1[name].identity != record.identity:
            findings.append(Finding("state1_identity_mismatch", f"{name}: assembled={record.identity}, State 1={state1[name].identity}.", name, state1[name].location))
        if name not in closure:
            findings.append(Finding("missing_model_closure", f"Assembled runtime model {name} is absent from model closure.", name, record.location))
        elif closure[name].identity != record.identity:
            findings.append(Finding("closure_identity_mismatch", f"{name}: assembled={record.identity}, model closure={closure[name].identity}.", name, closure[name].location))
    return {
        "schema_version": VERIFICATION_SCHEMA,
        "project_root": project.resolve().name,
        "summary": {
            "assembled_runtime_models": len(assembled), "state1_models": len(state1),
            "closure_models": len(closure), "contract_models": len(contract_closure), "errors": len(findings),
        },
        "findings": [finding.to_dict() for finding in findings],
    }


TYPE_NAME = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
CLOSURE_GLOB = "60_model_closure_*.json"


def _closure_models(project: Path) -> dict[str, dict[str, Any]]:
    models: dict[str, dict[str, Any]] = {}
    for path in sorted(project.glob(CLOSURE_GLOB)):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(payload, dict) and isinstance(payload.get("models"), dict):
            models.update({k: v for k, v in payload["models"].items() if isinstance(v, dict)})
    return models


def _introduced(contracts: dict[str, Any], models: dict[str, dict[str, Any]]) -> set[str]:
    """Closure models a contract introduces: named in a signature, or a field type of one that is."""
    frontier = [name for signature in contracts.values() for name in TYPE_NAME.findall(str(signature))
                if name in models]
    found: set[str] = set()
    while frontier:
        name = frontier.pop()
        if name in found:
            continue
        found.add(name)
        for field_type in (models[name].get("fields") or {}).values():
            frontier += [n for n in TYPE_NAME.findall(str(field_type)) if n in models and n not in found]
    # an interface model is introduced by its own method contracts too
    found |= {key.split(".", 1)[0] for key in contracts if "." in key and key.split(".", 1)[0] in models}
    return found


def state6_closure(project: Path) -> dict[str, Any]:
    """The identity obligation State 1 carries to State 6, before anything is assembled.

    State 1 decides what a model means and who mints it; the model closure
    (60_model_closure_*.json) is the one typed field list, written with the
    State 6 contracts. At the State 6 handoff: every State 1 model a contract
    introduces has a closure record of the same identity, and every ``contract_only`` record is justified —
    introduced by a contract (named in a signature, or carried by a field of a
    model that is) and not a State 1 concept. A case with no closure file is not
    checked, which is not a pass: identity, field carriers and the time source
    all read the closure.
    """
    state1, findings = load_state1(project)
    if not list(project.glob(CLOSURE_GLOB)):
        return {"schema_version": VERIFICATION_SCHEMA, "project_root": project.resolve().name,
                "outcome": "not_checked",
                "summary": {"state1_models": len(state1), "closure_models": 0, "contract_models": 0, "errors": 1},
                "findings": [{"code": "model_closure_absent", "outcome": "not_checked", "severity": "error",
                              "message": (f"no {CLOSURE_GLOB}: the {len(state1)} State 1 model(s) and the models "
                                          "the contracts introduce have no typed closure, so identity closure, "
                                          "field carriers and the time source of State 6 are not checked — "
                                          "not checked is not a pass")}]}
    closure, closure_findings = load_closure(project)
    contract_closure, contract_findings = load_contract_closure(project)
    findings = [*findings, *closure_findings, *contract_findings]
    try:
        contracts = json.loads((project / "60_contracts.json").read_text(encoding="utf-8")).get("contracts") or {}
    except (OSError, ValueError, AttributeError):
        contracts = {}
    contracts = contracts if isinstance(contracts, dict) else {}
    universe = {name: {} for name in state1}
    universe.update(_closure_models(project))
    introduced = _introduced(contracts, universe)
    for name, record in sorted(state1.items()):
        if name not in introduced:
            continue  # a concept no contract introduces is not in the specification (identity: assembled models only)
        if name in contract_closure:
            findings.append(Finding("state1_model_marked_contract_only",
                                    f"{name} is a State 1 concept; a contract_only record would drop its identity "
                                    "evidence. Move it to a closure file without identity_scope contract_only.",
                                    name, contract_closure[name].location))
        elif name not in closure:
            findings.append(Finding("missing_model_closure",
                                    f"State 1 model {name} has no model-closure record.", name, record.location))
        elif closure[name].identity != record.identity:
            findings.append(Finding("closure_identity_mismatch",
                                    f"{name}: State 1={record.identity}, model closure={closure[name].identity}.",
                                    name, closure[name].location))
    for name, record in sorted(contract_closure.items()):
        if name not in state1 and name not in introduced:
            findings.append(Finding("contract_only_model_unintroduced",
                                    f"contract_only model {name} is introduced by no contract (no signature and "
                                    "no field of an introduced model names it): nothing justifies it.",
                                    name, record.location))
    items = [{**finding.to_dict(), "severity": "error"} for finding in findings]
    return {"schema_version": VERIFICATION_SCHEMA, "project_root": project.resolve().name,
            "outcome": "closed" if not items else "open",
            "summary": {"state1_models": len(state1), "closure_models": len(closure),
                        "contract_models": len(contract_closure), "errors": len(items)},
            "findings": items}
