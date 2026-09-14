from __future__ import annotations

import copy
import difflib
import json
import os
import stat
import tempfile
from pathlib import Path
from typing import Any

import design_router_ir
import design_stage6_contracts
import design_stage6_data
from persistence_workbench import authoring as persistence_authoring

from spec_projection_workbench.model import (
    PLAN_SCHEMA,
    VERIFY_SCHEMA,
    SpecProjectionError,
)


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SpecProjectionError(f"missing {label}: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise SpecProjectionError(f"invalid {label}: {exc}") from exc
    if not isinstance(payload, dict):
        raise SpecProjectionError(f"{label} must be a JSON object")
    return payload


def _repo_root(project: Path) -> Path:
    project = project.resolve()
    for candidate in (project, *project.parents):
        sequence = candidate / "skills" / "spec-authoring" / "authoring_sequence.json"
        if sequence.is_file():
            return candidate
    raise SpecProjectionError(
        "could not locate skills/spec-authoring/authoring_sequence.json above project"
    )


def _load_sequence(project: Path) -> dict[str, Any]:
    sequence = _read_json(
        _repo_root(project) / "skills" / "spec-authoring" / "authoring_sequence.json",
        "authoring sequence",
    )
    if sequence.get("schema_version") != "spec_workbench_authoring_sequence.v2":
        raise SpecProjectionError("unsupported authoring_sequence.json schema")
    invariants = sequence.get("invariants")
    if not isinstance(invariants, dict):
        raise SpecProjectionError("authoring_sequence.json lacks invariants")
    if invariants.get("persistence_final_ir_is_deterministic_projection") is not True:
        raise SpecProjectionError(
            "authoring sequence does not authorize deterministic persistence projection"
        )
    if invariants.get("router_final_ir_is_deterministic_projection") is not True:
        raise SpecProjectionError(
            "authoring sequence does not authorize deterministic router projection"
        )
    return sequence


def _phase_artifacts(sequence: dict[str, Any], phase_id: str) -> tuple[str, ...]:
    phases = sequence.get("phases")
    if not isinstance(phases, list):
        raise SpecProjectionError("authoring_sequence.json lacks phases")
    for row in phases:
        if isinstance(row, dict) and row.get("id") == phase_id:
            values = row.get("compatibility_artifacts", [])
            if not isinstance(values, list) or not all(isinstance(v, str) and v for v in values):
                raise SpecProjectionError(
                    f"authoring phase {phase_id!r} has invalid compatibility_artifacts"
                )
            return tuple(values)
    raise SpecProjectionError(f"authoring phase not declared: {phase_id}")


def _source_present(project: Path, artifacts: tuple[str, ...]) -> bool:
    return any((project / artifact).is_file() for artifact in artifacts)


def _contract_symbol(contract_name: str) -> str:
    return contract_name.split(".", 1)[0]


def _handoff_modules(handoff_contracts: dict[str, Any]) -> list[str]:
    modules: list[str] = []
    seen: set[str] = set()
    for name, entry in handoff_contracts.items():
        if not isinstance(name, str) or not name:
            raise SpecProjectionError("State 6 handoff contains an invalid contract name")
        if not isinstance(entry, dict):
            raise SpecProjectionError(f"State 6 handoff contract {name!r} is invalid")
        raw_module = entry.get("module")
        if not isinstance(raw_module, str) or not raw_module.startswith("module:"):
            raise SpecProjectionError(
                f"State 6 handoff contract {name!r} has invalid module ownership"
            )
        module = raw_module.removeprefix("module:")
        if not module:
            raise SpecProjectionError(
                f"State 6 handoff contract {name!r} has empty module ownership"
            )
        if module not in seen:
            seen.add(module)
            modules.append(module)
    return modules


def _sync_module_topology(
    current_order: Any,
    current_paths: Any,
    handoff_contracts: dict[str, Any],
) -> tuple[list[str] | None, dict[str, str] | None]:
    order_present = current_order is not None
    paths_present = current_paths is not None
    if not order_present and not paths_present:
        return None, None
    if order_present != paths_present:
        raise SpecProjectionError(
            "global_spec.module_order and global_spec.module_paths must either both exist or both be absent"
        )
    if not isinstance(current_order, list) or not current_order or not all(
        isinstance(module, str) and module for module in current_order
    ):
        raise SpecProjectionError(
            "global_spec.module_order must be a non-empty string list"
        )
    if len(set(current_order)) != len(current_order):
        raise SpecProjectionError("global_spec.module_order contains duplicate modules")
    if not isinstance(current_paths, dict):
        raise SpecProjectionError("global_spec.module_paths must be an object")
    if set(current_paths) != set(current_order):
        raise SpecProjectionError(
            "global_spec.module_paths keys must match global_spec.module_order exactly"
        )

    parents: set[str] = set()
    result_paths: dict[str, str] = {}
    for module in current_order:
        path = current_paths.get(module)
        if not isinstance(path, str) or not path:
            raise SpecProjectionError(
                f"global_spec.module_paths[{module!r}] must be a non-empty string"
            )
        parent, separator, leaf = path.rpartition("/")
        if not separator or not parent or leaf != module:
            raise SpecProjectionError(
                f"global_spec.module_paths[{module!r}] must end with '/{module}'"
            )
        parents.add(parent)
        result_paths[module] = path
    if len(parents) != 1:
        raise SpecProjectionError(
            "global_spec.module_paths must share one deterministic module root before new modules can be projected"
        )
    module_root = next(iter(parents))

    result_order = list(current_order)
    for module in _handoff_modules(handoff_contracts):
        if module not in result_paths:
            result_order.append(module)
            result_paths[module] = f"{module_root}/{module}"
    return result_order, result_paths


def _sync_module_functions(
    current: Any,
    current_contracts: dict[str, Any],
    handoff_contracts: dict[str, Any],
) -> dict[str, list[str]]:
    if not isinstance(current, dict):
        raise SpecProjectionError("global_spec.module_functions must be an object")
    result: dict[str, list[str]] = {}
    for module, symbols in current.items():
        if not isinstance(module, str) or not isinstance(symbols, list) or not all(
            isinstance(symbol, str) for symbol in symbols
        ):
            raise SpecProjectionError(
                "global_spec.module_functions must map module names to string lists"
            )
        result[module] = list(symbols)

    old_symbols = {
        _contract_symbol(name)
        for name in current_contracts
        if isinstance(name, str) and name
    }
    target_owner: dict[str, str] = {}
    target_order: list[str] = []
    for name, entry in handoff_contracts.items():
        if not isinstance(name, str) or not name:
            raise SpecProjectionError("State 6 handoff contains an invalid contract name")
        if not isinstance(entry, dict):
            raise SpecProjectionError(f"State 6 handoff contract {name!r} is invalid")
        raw_module = entry.get("module")
        if not isinstance(raw_module, str) or not raw_module.startswith("module:"):
            raise SpecProjectionError(
                f"State 6 handoff contract {name!r} has invalid module ownership"
            )
        module = raw_module.removeprefix("module:")
        symbol = _contract_symbol(name)
        previous = target_owner.get(symbol)
        if previous is not None and previous != module:
            raise SpecProjectionError(
                f"State 6 assigns symbol {symbol!r} to both {previous!r} and {module!r}"
            )
        if previous is None:
            target_owner[symbol] = module
            target_order.append(symbol)

    contract_symbols = old_symbols | set(target_owner)
    for module, symbols in result.items():
        result[module] = [
            symbol
            for symbol in symbols
            if symbol not in contract_symbols or target_owner.get(symbol) == module
        ]

    for symbol in target_order:
        module = target_owner[symbol]
        if module not in result:
            result[module] = []
        if symbol not in result[module]:
            result[module].append(symbol)
    return result


def _sync_model_ownership(
    module_functions: dict[str, list[str]], models: Any
) -> dict[str, list[str]]:
    if not isinstance(models, dict):
        raise SpecProjectionError("global_spec.models must be an object")
    result = copy.deepcopy(module_functions)
    owned = result.setdefault("models", [])
    for name in models:
        if not isinstance(name, str) or not name:
            raise SpecProjectionError("global_spec.models contains an invalid model name")
        if name not in owned:
            owned.append(name)
    return result


def _sync_model_exports(imports: Any, models: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(imports, dict):
        raise SpecProjectionError("global_spec.imports must be an object")
    result = copy.deepcopy(imports)
    internal = result.get("internal")
    if not isinstance(internal, dict):
        raise SpecProjectionError("global_spec.imports.internal must be an object")
    exports = internal.setdefault("models", [])
    if not isinstance(exports, list) or not all(
        isinstance(symbol, str) for symbol in exports
    ):
        raise SpecProjectionError(
            "global_spec.imports.internal.models must be a string list"
        )
    for name in models:
        if name not in exports:
            exports.append(name)
    return result


def _finding(
    severity: str,
    code: str,
    message: str,
    *,
    source: str | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "severity": severity,
        "code": code,
        "message": message,
    }
    if source is not None:
        row["source"] = source
    return row


def _change(address: str, before: Any, after: Any) -> dict[str, Any] | None:
    if before == after:
        return None
    if before is None:
        action = "add"
    elif after is None:
        action = "remove"
    else:
        action = "replace"
    return {"address": address, "action": action}


def _set(projected: dict[str, Any], address: str, value: Any) -> None:
    parts = address.split(".")
    current: dict[str, Any] = projected
    for part in parts[:-1]:
        child = current.get(part)
        if not isinstance(child, dict):
            child = {}
            current[part] = child
        current = child
    current[parts[-1]] = copy.deepcopy(value)


def _get(root: dict[str, Any], address: str) -> Any:
    current: Any = root
    for part in address.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _source_check(
    source: str,
    *,
    enabled: bool,
    ready: bool,
    status: str | None = None,
    errors: int = 0,
) -> dict[str, Any]:
    return {
        "source": source,
        "enabled": enabled,
        "ready": ready,
        "status": status,
        "errors": errors,
    }


def _project(project: Path) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    project = project.resolve()
    if not project.is_dir():
        raise SpecProjectionError(f"project directory not found: {project}")
    sequence = _load_sequence(project)
    current = _read_json(project / "global_spec.json", "global_spec.json")
    projected = copy.deepcopy(current)
    findings: list[dict[str, Any]] = []
    source_checks: list[dict[str, Any]] = []

    model_paths = sorted(project.glob("60_model_closure_*.json"))
    if model_paths:
        model_overlay: dict[str, Any] = {}
        model_errors = 0
        for path in model_paths:
            payload = _read_json(path, path.name)
            if payload.get("schema_version") != "spec_workbench_model_closure.v1":
                model_errors += 1
                findings.append(
                    _finding(
                        "block",
                        "model_handoff_not_ready",
                        f"{path.name} has an unsupported model-closure schema",
                        source=path.name,
                    )
                )
                continue
            if payload.get("status") != "closed":
                model_errors += 1
                findings.append(
                    _finding(
                        "block",
                        "model_handoff_not_ready",
                        f"{path.name} must be closed before model projection",
                        source=path.name,
                    )
                )
                continue
            models = payload.get("models")
            if not isinstance(models, dict):
                model_errors += 1
                findings.append(
                    _finding(
                        "block",
                        "model_handoff_not_ready",
                        f"{path.name}.models must be an object",
                        source=path.name,
                    )
                )
                continue
            for name, declaration in models.items():
                if not isinstance(name, str) or not name or not isinstance(declaration, dict):
                    raise SpecProjectionError(
                        f"{path.name} contains an invalid model declaration"
                    )
                previous = model_overlay.get(name)
                if previous is not None and previous != declaration:
                    raise SpecProjectionError(
                        f"model {name!r} has conflicting closed declarations across model closures"
                    )
                model_overlay[name] = declaration
        model_ready = model_errors == 0
        source_checks.append(
            _source_check(
                " + ".join(path.name for path in model_paths),
                enabled=True,
                ready=model_ready,
                status="closed" if model_ready else "open",
                errors=model_errors,
            )
        )
        if model_ready:
            current_models = current.get("models")
            if not isinstance(current_models, dict):
                raise SpecProjectionError("global_spec.models must be an object")
            projected_models = copy.deepcopy(current_models)
            for name, declaration in model_overlay.items():
                projected_models[name] = copy.deepcopy(declaration)
            _set(projected, "models", projected_models)

    data_report = design_stage6_data.lint(project)
    data_errors = int(data_report.get("summary", {}).get("errors", 0))
    data_payload = design_stage6_data.load(project)
    data_status = data_payload.get("status")
    data_ready = data_errors == 0 and data_status == "accepted"
    source_checks.append(
        _source_check(
            design_stage6_data.DEFAULT_FILE,
            enabled=True,
            ready=data_ready,
            status=data_status if isinstance(data_status, str) else None,
            errors=data_errors,
        )
    )
    if not data_ready:
        findings.append(
            _finding(
                "block",
                "structured_data_handoff_not_ready",
                "pre-contract structured data must be accepted and lint-clean before projection",
                source=design_stage6_data.DEFAULT_FILE,
            )
        )
    else:
        sections = data_payload.get("sections")
        if not isinstance(sections, dict):
            raise SpecProjectionError("60_data_closure.json sections must be an object")
        for section in ("config", "persistence", "properties", "determinism"):
            value = sections.get(section)
            if not isinstance(value, dict):
                raise SpecProjectionError(
                    f"60_data_closure.json sections.{section} must be an object"
                )
            _set(projected, section, value)
        rules = sections.get("rules")
        if not isinstance(rules, dict):
            raise SpecProjectionError("60_data_closure.json sections.rules must be an object")
        for namespace, value in rules.items():
            if not isinstance(namespace, str) or not namespace:
                raise SpecProjectionError("structured rules namespace must be a non-empty string")
            _set(projected, f"rules.{namespace}", value)

    state6 = design_stage6_contracts.handoff(project)
    state6_ready = state6.get("ready") is True
    state6_summary = state6.get("summary") if isinstance(state6.get("summary"), dict) else {}
    state6_errors = int(state6_summary.get("errors", 0))
    source_checks.append(
        _source_check(
            design_stage6_contracts.DEFAULT_CATALOG_FILE,
            enabled=True,
            ready=state6_ready,
            status="closed" if state6_summary.get("plan_closed") is True else "open",
            errors=state6_errors,
        )
    )
    if not state6_ready:
        findings.append(
            _finding(
                "block",
                "state6_handoff_not_ready",
                "exact State 6 contract handoff must be ready before projection",
                source=design_stage6_contracts.DEFAULT_CATALOG_FILE,
            )
        )
    else:
        handoff_contracts = state6.get("contracts")
        if not isinstance(handoff_contracts, dict):
            raise SpecProjectionError("State 6 handoff contracts must be an object")
        signatures: dict[str, str] = {}
        for name, entry in handoff_contracts.items():
            signature = entry.get("signature") if isinstance(entry, dict) else None
            if not isinstance(signature, str) or not signature:
                raise SpecProjectionError(f"State 6 contract {name!r} lacks exact signature")
            signatures[name] = signature
        current_contracts = current.get("contracts")
        if not isinstance(current_contracts, dict):
            raise SpecProjectionError("global_spec.contracts must be an object")
        _set(projected, "contracts", signatures)
        _set(projected, "function_order", list(handoff_contracts))
        module_order, module_paths = _sync_module_topology(
            current.get("module_order"),
            current.get("module_paths"),
            handoff_contracts,
        )
        if module_order is not None and module_paths is not None:
            _set(projected, "module_order", module_order)
            _set(projected, "module_paths", module_paths)
        projected["module_functions"] = _sync_module_functions(
            current.get("module_functions"),
            current_contracts,
            handoff_contracts,
        )
        projected_models = projected.get("models")
        if projected_models is not None:
            projected["module_functions"] = _sync_model_ownership(
                projected["module_functions"], projected_models
            )
            projected["imports"] = _sync_model_exports(
                current.get("imports"), projected_models
            )

    persistence_artifacts = _phase_artifacts(
        sequence, "deterministic_persistence_closure"
    )
    persistence_report = persistence_authoring.handoff(project)
    persistence_enabled = persistence_report.get("enabled") is True
    persistence_ready = persistence_report.get("ready") is True
    persistence_summary = (
        persistence_report.get("summary")
        if isinstance(persistence_report.get("summary"), dict)
        else {}
    )
    persistence_errors = int(persistence_summary.get("errors", 0))
    source_checks.append(
        _source_check(
            persistence_artifacts[0] if persistence_artifacts else "persistence closure",
            enabled=persistence_enabled,
            ready=persistence_ready,
            status=(
                "closed"
                if persistence_summary.get("closed") is True
                else "open" if persistence_enabled else None
            ),
            errors=persistence_errors,
        )
    )
    if persistence_enabled:
        if not persistence_ready:
            findings.append(
                _finding(
                    "block",
                    "persistence_handoff_not_ready",
                    "enabled persistence closure is open or invalid; "
                    "rules.persistence_backend cannot be projected",
                    source=persistence_artifacts[0] if persistence_artifacts else None,
                )
            )
        else:
            backend_ir = persistence_report.get("backend_ir")
            if not isinstance(backend_ir, dict):
                raise SpecProjectionError(
                    "ready persistence handoff did not provide backend_ir"
                )
            _set(projected, "rules.persistence_backend", backend_ir)
    elif _get(current, "rules.persistence_backend") is not None:
        findings.append(
            _finding(
                "block",
                "unowned_persistence_backend",
                "global_spec contains rules.persistence_backend but no enabled "
                "persistence authoring closure owns it",
            )
        )

    router_artifacts = (
        _phase_artifacts(sequence, "deterministic_http_router_closure")
        + _phase_artifacts(sequence, "deterministic_http_router_context_closure")
    )
    router_enabled = _source_present(project, router_artifacts)
    router_ready = not router_enabled
    router_errors = 0
    router_handoff: dict[str, Any] | None = None
    if router_enabled:
        try:
            router_handoff = design_router_ir.assemble(project)
            router_ready = router_handoff.get("ready") is True
        except (design_router_ir.RouterIRAssemblyError, ValueError) as exc:
            router_ready = False
            router_errors = 1
            findings.append(
                _finding(
                    "block",
                    "router_handoff_not_ready",
                    str(exc),
                    source=" + ".join(router_artifacts),
                )
            )
    source_checks.append(
        _source_check(
            " + ".join(router_artifacts) if router_artifacts else "router closure",
            enabled=router_enabled,
            ready=router_ready,
            status="closed" if router_ready and router_enabled else "open" if router_enabled else None,
            errors=router_errors,
        )
    )
    if router_enabled and router_ready:
        rules = router_handoff.get("rules") if isinstance(router_handoff, dict) else None
        backend = rules.get("http_router_backend") if isinstance(rules, dict) else None
        if not isinstance(backend, dict):
            raise SpecProjectionError(
                "ready Router IR handoff did not provide rules.http_router_backend"
            )
        _set(projected, "rules.http_router_backend", backend)
    elif not router_enabled and _get(current, "rules.http_router_backend") is not None:
        findings.append(
            _finding(
                "block",
                "unowned_http_router_backend",
                "global_spec contains rules.http_router_backend but no Router authoring "
                "artifacts own it",
            )
        )

    return current, projected, findings, source_checks


def build_plan(project: Path) -> dict[str, Any]:
    current, projected, findings, source_checks = _project(project)
    changes: list[dict[str, Any]] = []
    addresses = [
        "config",
        "contracts",
        "function_order",
        "imports.internal",
        "module_functions",
        "module_order",
        "module_paths",
        "models",
        "persistence",
        "properties",
        "determinism",
    ]
    current_rules = current.get("rules") if isinstance(current.get("rules"), dict) else {}
    projected_rules = (
        projected.get("rules") if isinstance(projected.get("rules"), dict) else {}
    )
    for namespace in sorted(set(current_rules) | set(projected_rules)):
        if current_rules.get(namespace) != projected_rules.get(namespace):
            addresses.append(f"rules.{namespace}")
    for address in addresses:
        row = _change(address, _get(current, address), _get(projected, address))
        if row is not None:
            changes.append(row)
    blocks = sum(row.get("severity") == "block" for row in findings)
    return {
        "schema_version": PLAN_SCHEMA,
        "project_root": project.resolve().name,
        "ready_to_apply": blocks == 0,
        "in_sync": blocks == 0 and not changes,
        "summary": {
            "changes": len(changes),
            "blocks": blocks,
            "sources": len(source_checks),
            "ready_sources": sum(row["ready"] for row in source_checks),
        },
        "source_checks": source_checks,
        "changes": changes,
        "findings": findings,
    }


def _canonical_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def render_diff(project: Path) -> str:
    project = project.resolve()
    _, projected, _, _ = _project(project)
    before = (project / "global_spec.json").read_text(encoding="utf-8").splitlines(
        keepends=True
    )
    after = _canonical_text(projected).splitlines(keepends=True)
    return "".join(
        difflib.unified_diff(
            before,
            after,
            fromfile="a/global_spec.json",
            tofile="b/global_spec.json",
            lineterm="\n",
        )
    )


def _atomic_replace(path: Path, content: str, mode: int) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            os.fchmod(handle.fileno(), mode)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        try:
            directory_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except OSError:
            pass
    finally:
        temporary.unlink(missing_ok=True)


def apply(project: Path) -> dict[str, Any]:
    project = project.resolve()
    plan = build_plan(project)
    if not plan["ready_to_apply"]:
        codes = ", ".join(row["code"] for row in plan["findings"] if row["severity"] == "block")
        raise SpecProjectionError(f"projection is blocked: {codes}")
    _, projected, _, _ = _project(project)
    path = project / "global_spec.json"
    before = path.read_text(encoding="utf-8")
    mode = stat.S_IMODE(path.stat().st_mode)
    _atomic_replace(path, _canonical_text(projected), mode)
    try:
        verification = verify(project)
        if not verification["ready"] or not verification["in_sync"]:
            raise SpecProjectionError("post-apply projection verification failed")
    except Exception:
        _atomic_replace(path, before, mode)
        raise
    return {
        "schema_version": "spec_workbench_projection_apply.v1",
        "project_root": project.name,
        "applied_changes": plan["summary"]["changes"],
        "in_sync": True,
    }


def verify(project: Path) -> dict[str, Any]:
    plan = build_plan(project)
    return {
        "schema_version": VERIFY_SCHEMA,
        "project_root": plan["project_root"],
        "ready": plan["ready_to_apply"],
        "in_sync": plan["in_sync"],
        "summary": plan["summary"],
        "source_checks": plan["source_checks"],
        "changes": plan["changes"],
        "findings": plan["findings"],
    }
