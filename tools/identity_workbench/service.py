from __future__ import annotations

from pathlib import Path
from typing import Any

from identity_workbench.model import Finding, IdentityWorkbenchError, INSPECTION_SCHEMA, INVENTORY_SCHEMA, VERIFICATION_SCHEMA
from identity_workbench.sources import load_assembled, load_closure, load_state1

def _load(project: Path):
    state1, state1_findings = load_state1(project)
    closure, closure_findings = load_closure(project)
    assembled, assembled_findings = load_assembled(project)
    return state1, closure, assembled, [*state1_findings, *closure_findings, *assembled_findings]

def inventory(project: Path) -> dict[str, Any]:
    state1, closure, assembled, findings = _load(project)
    names = sorted(set(state1) | set(closure) | set(assembled))
    return {
        "schema_version": INVENTORY_SCHEMA,
        "project_root": project.resolve().name,
        "models": [{
            "name": name,
            "state1": state1.get(name).identity if name in state1 else None,
            "closure": closure.get(name).identity if name in closure else None,
            "assembled": assembled.get(name).identity if name in assembled else None,
        } for name in names],
        "summary": {
            "models": len(names), "state1_models": len(state1),
            "closure_models": len(closure), "assembled_runtime_models": len(assembled),
            "source_errors": len(findings),
        },
        "findings": [finding.to_dict() for finding in findings],
    }

def inspect_model(project: Path, name: str) -> dict[str, Any]:
    state1, closure, assembled, findings = _load(project)
    if name not in set(state1) | set(closure) | set(assembled):
        raise IdentityWorkbenchError(f"Unknown model: {name}")
    sources = {
        "state1": state1.get(name).to_dict() if name in state1 else None,
        "closure": closure.get(name).to_dict() if name in closure else None,
        "assembled": assembled.get(name).to_dict() if name in assembled else None,
    }
    present = [source["identity"] for source in sources.values() if source]
    return {
        "schema_version": INSPECTION_SCHEMA,
        "project_root": project.resolve().name,
        "model": name,
        "consistent": len(present) == 3 and len(set(present)) == 1,
        "sources": sources,
        "findings": [finding.to_dict() for finding in findings if finding.model == name],
    }

def verify(project: Path) -> dict[str, Any]:
    state1, closure, assembled, findings = _load(project)
    findings = list(findings)
    for name, record in sorted(assembled.items()):
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
            "closure_models": len(closure), "errors": len(findings),
        },
        "findings": [finding.to_dict() for finding in findings],
    }
