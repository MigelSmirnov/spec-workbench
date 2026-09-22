from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import design_closure_gaps
import design_decision_witness
import design_stage3
import fence
import flow_closure
import design_stage6_contracts
import design_stage6_data
from external_contract_workbench import coverage as external_contract_coverage
from identity_workbench import verify as verify_identity
from model_surface_workbench import fields as model_fields
from notes_workbench import gate as notes_gate
from persistence_workbench import coverage as persistence_coverage
from router_workbench import service as router_service
from spec_language_workbench import verify as verify_language

from assembly_workbench.model import AssemblyWorkbenchError, CheckResult

ReportFunction = Callable[[Path], dict[str, Any]]

def _severity_count(findings: list[dict[str, Any]], values: set[str]) -> int:
    return sum(item.get("severity") in values for item in findings)

def _normalize(name: str, report: dict[str, Any]) -> CheckResult:
    summary = report.get("summary")
    findings = report.get("findings", [])
    if not isinstance(summary, dict) or not isinstance(findings, list):
        raise AssemblyWorkbenchError(f"{name} returned an invalid report shape.")
    if name == "language":
        errors = int(summary.get("errors", len(findings)))
        warnings = 0
        ready = bool(report.get("ready")) and errors == 0
    elif name == "modules":
        errors = int(summary.get("errors", 0))
        warnings = int(summary.get("warnings", 0))
        ready = errors == 0
    elif name == "identity":
        errors = int(summary.get("errors", len(findings)))
        warnings = 0
        ready = errors == 0
    elif name == "fields":
        errors = int(summary.get("errors", len(findings)))
        warnings = 0
        ready = errors == 0
    elif name == "data":
        errors = int(summary.get("errors", 0))
        warnings = _severity_count(findings, {"warning", "review"})
        ready = errors == 0
    elif name == "contracts":
        errors = int(summary.get("errors", 0))
        warnings = int(summary.get("warnings", _severity_count(findings, {"warning"})))
        ready = bool(summary.get("handoff_ready"))
    elif name == "external_contracts":
        errors = int(summary.get("errors", 0))
        warnings = 0
        ready = bool(summary.get("handoff_ready")) and errors == 0
    elif name == "notes":
        errors = int(summary.get("blocks", 0))
        warnings = int(summary.get("reviews", 0))
        ready = bool(summary.get("handoff_ready"))
    elif name == "closure_gaps":
        errors = int(summary.get("errors", len(findings)))
        warnings = 0
        ready = errors == 0
    elif name == "router":
        errors = int(summary.get("errors", 0))
        warnings = _severity_count(findings, {"warning", "review"})
        ready = bool(summary.get("handoff_ready"))
    elif name == "persistence":
        errors = int(summary.get("errors", 0))
        warnings = _severity_count(findings, {"warning", "review"})
        ready = bool(summary.get("handoff_ready"))
    elif name in {"witness", "flows", "factory"}:
        errors = int(summary.get("errors", len(findings)))
        warnings = 0
        ready = errors == 0
    else:
        raise AssemblyWorkbenchError(f"Unknown assembly check: {name}")
    # the fence: a warning is an undecided fact; it stops the assembly
    findings = fence.enforce(findings)
    if warnings:
        errors += warnings
        warnings = 0
        ready = False
    return CheckResult(
        name=name,
        ready=ready,
        schema_version=report.get("schema_version"),
        errors=errors,
        warnings=warnings,
        summary=summary,
        findings=findings,
    )

def _closure_gap_coverage(project: Path) -> dict[str, Any]:
    report = design_closure_gaps.run(project)
    findings = [
        {**item, "severity": "error"}
        for item in report.get("findings", [])
        if isinstance(item, dict)
    ]
    return {
        "schema_version": report.get("schema_version"),
        "summary": {
            **(report.get("summary") or {}),
            "errors": len(findings),
            "handoff_ready": len(findings) == 0,
        },
        "findings": findings,
    }


def _factory_storage_resolver(factory_root: Path | None = None):
    """The deterministic backend's version-bound storage registry, when the factory is reachable.

    Codec coverage is proven against the emitter that will lower the closure;
    without the factory the check reports the registry unavailable, truthfully.
    """
    import os
    import sys as _sys
    root = Path(__file__).resolve().parents[2]
    candidates = [factory_root] if factory_root is not None else []
    if os.environ.get("SPEC_WORKBENCH_FACTORY_ROOT"):
        candidates.append(Path(os.environ["SPEC_WORKBENCH_FACTORY_ROOT"]))
    candidates += [root.parent / "code_factory", root.parent.parent / "code_factory"]
    for candidate in candidates:
        emitter = candidate / "tools" / "generate_postgres_repository_draft.py"
        if emitter.is_file():
            if str(emitter.parent) not in _sys.path:
                _sys.path.append(str(emitter.parent))
            try:
                import generate_postgres_repository_draft as backend  # type: ignore
            except Exception:  # pragma: no cover - environment dependent
                return None
            return getattr(backend, "resolve_storage", None)
    return None


CHECKS: dict[str, ReportFunction] = {
    "language": verify_language,
    "modules": design_stage3.lint,
    "identity": verify_identity,
    "fields": model_fields.lint,
    "data": design_stage6_data.lint,
    "contracts": design_stage6_contracts.lint,
    "external_contracts": external_contract_coverage,
    "notes": notes_gate.coverage,
    "closure_gaps": _closure_gap_coverage,
    "router": router_service.coverage,
    "persistence": lambda project: persistence_coverage(project, storage_resolver=_factory_storage_resolver()),
    "witness": design_decision_witness.coverage,
    "flows": flow_closure.coverage,
    "factory": lambda project: factory_validation(project, factory_root=_factory_root()),
}


def _factory_root() -> Path | None:
    """The sibling Factory checkout, or the one SPEC_WORKBENCH_FACTORY_ROOT names.

    An explicit root that is not a Factory is reported as such, never replaced
    by another copy.
    """
    import os
    override = os.environ.get("SPEC_WORKBENCH_FACTORY_ROOT")
    if override:
        return Path(override)
    root = Path(__file__).resolve().parents[2]
    for candidate in (root.parent / "code_factory", root.parent.parent / "code_factory"):
        if (candidate / "tools" / "validate_spec.py").is_file():
            return candidate
    return None


def factory_validation(project: Path, *, factory_root: Path | None) -> dict[str, Any]:
    """The Factory's canonical validator, at assembly rather than at Stage 9.

    SPEC_STANDARD sections 12-14 (type origin, properties, determinism) are
    checked by no Workbench gate; before this they reached an author only at
    admission, after the whole specification was written. The verdict is the
    Factory's: no rule is implemented here. Without a Factory the check says so
    and is not ready - aggregate readiness is not available offline.
    """
    source = project / "global_spec.json"
    summary: dict[str, Any] = {"errors": 0, "factory_root": str(factory_root) if factory_root else None}
    if not source.is_file():
        return {"summary": {**summary, "errors": 1}, "findings": [{
            "severity": "error", "code": "assembled_spec_missing",
            "message": "global_spec.json is not assembled yet.",
        }]}
    validator = factory_root / "tools" / "validate_spec.py" if factory_root else None
    if validator is None or not validator.is_file():
        return {"summary": {**summary, "errors": 1}, "findings": [{
            "severity": "error", "code": "factory_unavailable",
            "message": "No Factory checkout with tools/validate_spec.py: pass SPEC_WORKBENCH_FACTORY_ROOT or place "
                       "code_factory beside this repository. Aggregate readiness is not decided without it.",
        }]}
    import hashlib, json as _json, subprocess, sys as _sys, tempfile
    with tempfile.TemporaryDirectory(prefix="spec-workbench-assembly-") as temp:
        report_path = Path(temp) / "validation.json"
        result = subprocess.run(
            [_sys.executable, str(validator), str(source), "--out", str(report_path), "--quiet"],
            text=True, capture_output=True, check=False,
        )
        if not report_path.is_file():
            return {"summary": {**summary, "errors": 1}, "findings": [{
                "severity": "error", "code": "factory_validator_failed",
                "message": f"The Factory validator produced no report (exit {result.returncode}): "
                           + (result.stderr.strip().splitlines() or [""])[-1][:300],
            }]}
        report = _json.loads(report_path.read_text(encoding="utf-8"))
    spec = _json.loads(source.read_text(encoding="utf-8"))
    canonical = "sha256:" + hashlib.sha256(
        _json.dumps(spec, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    findings = []
    if report.get("spec_sha") != canonical:
        findings.append({"severity": "error", "code": "factory_report_unbound",
                         "message": "The validator report is not bound to this global_spec.json."})
    for item in report.get("findings") or []:
        if str(item.get("severity", "")).lower() in {"error", "block"}:
            findings.append({
                "severity": "error", "code": str(item.get("id") or item.get("code") or "factory_validation"),
                "message": f"Factory validator: {item.get('message', '')}"[:500],
            })
    summary.update({
        "errors": len(findings),
        "status": report.get("status"),
        "factory_summary": report.get("summary"),
    })
    return {"summary": summary, "findings": findings}

def run(project: Path, name: str, *, factory_root: Path | None = None) -> CheckResult:
    function = CHECKS.get(name)
    if function is None:
        raise AssemblyWorkbenchError(f"Unknown assembly check: {name}")
    try:
        if name == "persistence":
            report = persistence_coverage(
                project,
                storage_resolver=_factory_storage_resolver(factory_root),
            )
        else:
            report = function(project)
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise AssemblyWorkbenchError(f"{name} check failed to load: {error}") from error
    return _normalize(name, report)
