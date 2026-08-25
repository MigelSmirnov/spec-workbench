#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "examples" / "cabinet-web-backend"
STAGE = ROOT / ".stage" / "cabinet-web-persistence"
SERVICE = ROOT / "tools" / "spec_projection_workbench" / "service.py"
NOTES = PROJECT / "80_notes.md"

CANDIDATE_FILES = (
    "60_model_closure_domain.json",
    "60_contract_plan.json",
    "60_contracts.json",
    "60_data_closure.json",
    "70_persistence_closure.json",
)

MODEL_BLOCK = '''    model_paths = sorted(project.glob("60_model_closure_*.json"))
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

'''


def materialize_candidate() -> None:
    for name in CANDIDATE_FILES:
        source = STAGE / f"{name}.gz"
        if not source.is_file():
            raise SystemExit(f"missing staged candidate: {source}")
        with gzip.open(source, "rt", encoding="utf-8") as handle:
            content = handle.read()
        (PROJECT / name).write_text(content, encoding="utf-8")


def patch_projector() -> None:
    text = SERVICE.read_text(encoding="utf-8")
    if 'model_paths = sorted(project.glob("60_model_closure_*.json"))' not in text:
        anchor = '''    findings: list[dict[str, Any]] = []\n    source_checks: list[dict[str, Any]] = []\n\n    data_report = design_stage6_data.lint(project)\n'''
        replacement = '''    findings: list[dict[str, Any]] = []\n    source_checks: list[dict[str, Any]] = []\n\n''' + MODEL_BLOCK + '''    data_report = design_stage6_data.lint(project)\n'''
        if anchor not in text:
            raise SystemExit("projector model-source anchor changed")
        text = text.replace(anchor, replacement, 1)
    if '        "models",\n        "persistence",' not in text:
        anchor = '        "module_paths",\n        "persistence",'
        replacement = '        "module_paths",\n        "models",\n        "persistence",'
        if anchor not in text:
            raise SystemExit("projector plan-address anchor changed")
        text = text.replace(anchor, replacement, 1)
    SERVICE.write_text(text, encoding="utf-8")


def method_rows() -> dict[str, dict]:
    closure = json.loads((PROJECT / "70_persistence_closure.json").read_text(encoding="utf-8"))
    result: dict[str, dict] = {}
    for repository in closure["backend_ir"]["repositories"]:
        if repository.get("repository") != "PostgresCabinetUnitOfWork":
            continue
        for row in repository.get("methods", []):
            result[row["method"]] = row
    return result


def table_models() -> dict[str, str]:
    closure = json.loads((PROJECT / "70_persistence_closure.json").read_text(encoding="utf-8"))
    return {row["table"]: row["model"] for row in closure["backend_ir"]["tables"]}


def uow_note(scope: str, row: dict, models: dict[str, str]) -> str:
    query = row["query"]
    method = scope.rsplit(".", 1)[-1]
    if query == "lock":
        keys = ", ".join(row["keys"])
        return (
            f"{scope}: [DEPENDENCY_BOUNDARY] MUST acquire only the transaction-scoped "
            f"{row['scope']} lock for typed key(s) {keys} inside the already active operation UoW before dependent reads or writes; "
            "MUST NOT open, commit, retry, or apply domain policy on its own."
        )
    table = row["table"]
    model = models[table]
    if query in {"get_by_key", "get_unique"}:
        return (
            f"{scope}: [PROVENANCE] MUST read only the exact persisted {model} row selected by the declared typed filter from {table} inside the active operation UoW; "
            "MUST return stored facts without substituting another identity/version or applying lifecycle policy."
        )
    if query in {"list_by", "list_all"}:
        return (
            f"{scope}: [DETERMINISM_OR_ORDERING] MUST return only persisted {model} rows selected from {table} by the declared bounded filter and IR ordering inside the active operation UoW; "
            "MUST NOT infer additional membership or mutate storage."
        )
    if query in {"insert", "insert_many"}:
        return (
            f"{scope}: [PROVENANCE] MUST insert the exact supplied {model} projection into {table} inside the active operation UoW and let uniqueness/constraint conflicts remain visible to the caller; "
            "MUST NOT upsert, replace prior evidence, or commit independently."
        )
    if query in {"update_fields", "update_many"}:
        updates = ", ".join(row["updates"])
        return (
            f"{scope}: [PROVENANCE] MUST update only the declared mutable field(s) {updates} on the existing {model} row selected by the IR filter in {table} inside the active operation UoW; "
            "MUST NOT insert a missing row, change immutable binding fields, or commit independently."
        )
    if query in {"upsert", "upsert_many"}:
        conflict = ", ".join(row["conflict"])
        updates = ", ".join(row["updates"])
        return (
            f"{scope}: [PROVENANCE] MUST perform only the IR-declared {query} for {model} in {table}, using conflict key(s) {conflict} and changing only {updates} on conflict inside the active operation UoW; "
            "MUST NOT broaden the conflict identity or apply business policy."
        )
    raise SystemExit(f"unsupported deterministic UoW query for note generation: {method} -> {query}")


def append_notes() -> None:
    contracts = json.loads((PROJECT / "60_contracts.json").read_text(encoding="utf-8"))["contracts"]
    rows = method_rows()
    models = table_models()
    current = NOTES.read_text(encoding="utf-8")
    existing = {
        line.split(":", 1)[0].strip()
        for line in current.splitlines()
        if ": [" in line
    }
    additions: list[str] = []
    for scope in contracts:
        if not scope.startswith("CabinetUnitOfWork.") or scope in existing:
            continue
        method = scope.rsplit(".", 1)[-1]
        row = rows.get(method)
        if row is None:
            raise SystemExit(f"no deterministic persistence row for {scope}")
        additions.append(uow_note(scope, row, models))

    specials = {
        "PostgresCabinetUnitOfWorkFactory.__init__": (
            "PostgresCabinetUnitOfWorkFactory.__init__: [CONFIG_REFERENCE] MUST bind only the protected PostgreSQL connection setting required by = config.runtime_storage.database_url_required; MUST NOT open a transaction, read domain state, or provide a fallback database."
        ),
        "PostgresCabinetUnitOfWorkFactory.open": (
            "PostgresCabinetUnitOfWorkFactory.open: [DEPENDENCY_BOUNDARY] MUST construct and return one fresh PostgresCabinetUnitOfWork for one application operation so singleton services never share an active transaction; connection/UoW construction MUST remain outside domain services."
        ),
        "create_cabinet_web_app": (
            "create_cabinet_web_app: [ORCHESTRATION] MUST be the sole Cabinet Web composition root: resolve protected deployment configuration, run PostgreSQL migration/connectivity checks and source-publication recovery before traffic, construct the PostgreSQL UoW factory and protected filesystem byte store, wire every accepted service/gateway dependency, then delegate the completed graph to create_app; MUST fail closed instead of inventing adapters, defaults, or local-backend reachability."
        ),
    }
    for scope, note in specials.items():
        if scope in contracts and scope not in existing:
            additions.append(note)

    expected = [
        scope for scope in contracts
        if scope.startswith("CabinetUnitOfWork.") and scope not in existing
    ]
    expected += [scope for scope in specials if scope in contracts and scope not in existing]
    if len(additions) != len(expected):
        raise SystemExit(f"note generation mismatch: expected {len(expected)}, got {len(additions)}")
    if additions:
        current = current.rstrip() + "\n\n## Deterministic PostgreSQL UoW and composition closure\n\n" + "\n".join(additions) + "\n"
        NOTES.write_text(current, encoding="utf-8")
    print(json.dumps({"materialized_files": len(CANDIDATE_FILES), "generated_notes": len(additions)}, sort_keys=True))


def main() -> None:
    materialize_candidate()
    patch_projector()
    append_notes()


if __name__ == "__main__":
    main()
