"""The imports closure gate, its draft and the derived imports.module_internal.

IMPORTS_WORKBENCH.md §3-§7. The table 65_imports.json is the author's: one
scope per contract and one per module, every candidate accepted into ``uses``
or rejected with a reason. ``module_internal`` is derived from ``uses`` only.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import fence

from imports_workbench import case as case_loader
from imports_workbench import factory
from imports_workbench.candidates import Candidate, code_candidates, scope_candidates
from imports_workbench.case import Case, Scope
from imports_workbench.model import (
    AVAILABLE, FINDING_MESSAGES, KNOWS, NOT_APPLICABLE, REPORT_SCHEMA, TABLE_FILE, TABLE_SCHEMA,
    UNAVAILABLE, USES_AS, ImportsError,
)

_CODE_EXEMPT_BASIS = {"contract"}
_CODE_EXEMPT_AS = {"annotates"}


def _finding(code: str, subject: str, message: str | None = None, **evidence: Any) -> dict[str, Any]:
    return {"severity": "error", "code": code, "subject": subject,
            "message": message or FINDING_MESSAGES[code], **evidence}


# -- the table ---------------------------------------------------------------

def table_path(project: Path) -> Path:
    return project / TABLE_FILE


def load_table(project: Path) -> dict[str, Any] | None:
    path = table_path(project)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as exc:
        raise ImportsError(f"{TABLE_FILE} cannot be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ImportsError(f"{TABLE_FILE} is not valid JSON: {exc}") from exc
    return payload  # any other shape is imports_table_invalid, reported by the gate


def _rows(entry: Any, key: str) -> list[dict[str, Any]]:
    rows = entry.get(key) if isinstance(entry, dict) else None
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def _key(row: dict[str, Any]) -> tuple[str | None, str | None]:
    """(symbol, provider), hashable whatever the row holds; a non-string part is None
    (the row itself is reported as imports_use_invalid)."""
    symbol, provider = row.get("symbol"), row.get("provider")
    return (symbol if isinstance(symbol, str) else None, provider if isinstance(provider, str) else None)


def derive(table: dict[str, Any] | None) -> dict[str, dict[str, list[str]]]:
    """module_internal[m][p] = the symbols of every use of every scope of m from p (§4)."""
    result: dict[str, dict[str, set[str]]] = {}
    scopes = (table or {}).get("scopes")
    for scope_id, entry in (scopes.items() if isinstance(scopes, dict) else ()):
        module = str(scope_id).split(".", 1)[0]
        for row in _rows(entry, "uses"):
            symbol, provider = _key(row)
            if isinstance(symbol, str) and isinstance(provider, str):
                result.setdefault(module, {}).setdefault(provider, set()).add(symbol)
    return {module: {provider: sorted(symbols) for provider, symbols in sorted(edges.items())}
            for module, edges in sorted(result.items())}


def drift(case: Case, table: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Where the specification's module_internal differs from the derived one (§4).

    Only modules the table judges are compared: the edges of a module the
    closure does not judge (models, emitter-written modules) are not its own.
    """
    derived = derive(table)
    scopes = (table or {}).get("scopes") if isinstance(table, dict) else None
    judged = {str(scope).split(".", 1)[0] for scope in (scopes if isinstance(scopes, dict) else ())}
    differences = []
    for module in sorted(judged & (set(derived) | set(case.module_internal) | judged)):
        current = case.module_internal.get(module) or {}
        expected = derived.get(module) or {}
        for provider in sorted(set(current) | set(expected)):
            have, want = set(current.get(provider) or ()), set(expected.get(provider) or ())
            if have != want:
                differences.append({"module": module, "provider": provider,
                                    "extra": sorted(have - want), "missing": sorted(want - have)})
    return differences


# -- the gate ----------------------------------------------------------------

def _order(case: Case) -> dict[str, int]:
    return {module: position for position, module in enumerate(case.modules)}


def _basis_problem(basis: Any, scope: Scope, case: Case, code: dict[str, list[str]] | None,
                   row: dict[str, Any]) -> str | None:
    if not isinstance(basis, str) or not basis.strip():
        return "the basis is empty"
    if basis == "contract" or basis == "code":
        if basis == "code":
            used = set((code or {}).get(row.get("provider"), ()))
            if row.get("symbol") not in used:
                return "basis `code`, but the module's code (Factory report) does not name the symbol"
        return None
    kind, _, value = basis.partition(":")
    if kind == "note":
        if basis not in {address for address, _ in scope.notes}:
            return f"{basis} is not a note of scope {scope.id}"
        return None
    if kind == "knows":
        if value not in case.knows.get(scope.module, ()):
            return f"{value} is not in State 3 Knows of {scope.module}"
        if value != row.get("provider"):
            return f"knows:{value} justifies a symbol of {value}, not of {row.get('provider')}"
        return None
    if kind == "author" and value.strip():
        return None
    return f"unknown basis form {basis!r}: contract, note:<address>, knows:<module>, code or author:<text>"


def _check_use(row: dict[str, Any], scope: Scope, case: Case, order: dict[str, int],
               code: dict[str, list[str]] | None, candidate: Candidate | None) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    symbol, provider = _key(row)
    if not isinstance(symbol, str) or not isinstance(provider, str) or row.get("as") not in USES_AS:
        return [_finding("imports_use_invalid", scope.id, row=row)]
    providers = case.providers(symbol)
    if not providers:
        found.append(_finding("imports_symbol_unknown", scope.id, symbol=symbol, provider=provider))
    elif provider not in providers:
        found.append(_finding("imports_provider_wrong", scope.id, symbol=symbol, provider=provider,
                              exported_by=providers))
    if provider == scope.module or (provider in order and order[provider] >= order.get(scope.module, -1)):
        found.append(_finding("imports_edge_forbidden", scope.id, symbol=symbol, provider=provider,
                              module_order=case.modules))
    problem = _basis_problem(row.get("basis"), scope, case, code, row)
    if problem:
        found.append(_finding("imports_basis_invalid", scope.id, f"{symbol} from {provider}: {problem}",
                              symbol=symbol, provider=provider, basis=row.get("basis")))
    if candidate is not None and candidate.weak_only and not str(row.get("basis") or "").startswith(("note:", "code")):
        found.append(_finding("imports_weak_without_basis", scope.id, symbol=symbol, provider=provider,
                              candidate=candidate.as_json(), basis=row.get("basis")))
    return found


def _code_evidence(project: Path, case: Case, factory_root: Path | None) -> dict[str, Any]:
    return factory.evidence(project, case.factory_target, factory_root)


def analyze(case: Case, table: dict[str, Any] | None, code: dict[str, Any], project: Path | None = None) -> dict[str, Any]:
    """The gate over an already loaded case, table and code evidence."""
    findings: list[dict[str, Any]] = []
    scopes = case.scopes()
    order = _order(case)
    code_status = code.get("status", NOT_APPLICABLE)
    code_modules: dict[str, Any] = code.get("modules") or {}
    table_scopes: dict[str, Any] = {}
    if table is None:
        findings.append(_finding("imports_table_missing", case.project_root))
    elif (not isinstance(table, dict) or table.get("schema_version") != TABLE_SCHEMA
          or not isinstance(table.get("scopes"), dict)):
        findings.append(_finding("imports_table_invalid", case.project_root,
                                 f"{TABLE_FILE} must have schema_version {TABLE_SCHEMA!r} and a scopes object"))
        table = None
    else:
        table_scopes = table["scopes"]

    for scope_id in sorted(set(table_scopes) - set(scopes)):
        findings.append(_finding("imports_scope_unknown", str(scope_id)))

    status: dict[str, dict[str, Any]] = {}
    pending = stale = 0
    # every use row of a module, with its scope: one key may be used by several scopes
    uses_by_module: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    rejected_by_module: dict[str, list[dict[str, Any]]] = {}
    for scope_id, scope in scopes.items():
        entry = table_scopes.get(scope_id)
        module_code = code_modules.get(scope.module) if code_status == AVAILABLE else None
        if not isinstance(entry, dict):
            candidates = scope_candidates(case, scope)
            pending += len(candidates)
            status[scope_id] = {"state": "missing", "pending": len(candidates)}
            if table is not None:
                findings.append(_finding("imports_scope_missing", scope_id, candidates=len(candidates)))
            continue
        uses, rejected = _rows(entry, "uses"), _rows(entry, "rejected")
        candidates = scope_candidates(case, scope, uses)
        is_stale = entry.get("basis_sha256") != scope.basis_sha256
        if is_stale:
            stale += 1
            findings.append(_finding("imports_scope_stale", scope_id, recorded=entry.get("basis_sha256"),
                                     current=scope.basis_sha256))
        for row in uses:
            findings += _check_use(row, scope, case, order, module_code, candidates.get(_key(row)))
            uses_by_module.setdefault(scope.module, []).append((scope_id, row))
        for row in rejected:
            if None in _key(row) and row.get("symbol") != "*":
                findings.append(_finding("imports_use_invalid", scope_id,
                                         "a rejected row needs a symbol and a provider", row=row))
            if not isinstance(row.get("reason"), str) or not row["reason"].strip():
                findings.append(_finding("imports_rejection_without_reason", scope_id, row=row))
        conflicts = {_key(row) for row in uses} & {_key(row) for row in rejected}
        for key in sorted((key for key in conflicts if None not in key), key=str):
            findings.append(_finding("imports_decision_conflict", scope_id, symbol=key[0], provider=key[1]))
        rejected_by_module.setdefault(scope.module, []).extend(rejected)
        decided = {_key(row) for row in uses} | {_key(row) for row in rejected}
        undecided = [candidate for key, candidate in candidates.items() if key not in decided]
        for candidate in undecided:
            findings.append(_finding("imports_candidate_undecided", scope_id, candidate=candidate.as_json()))
        pending += len(undecided)
        status[scope_id] = {"state": "stale" if is_stale else "decided", "pending": len(undecided),
                            "uses": len(uses), "rejected": len(rejected)}

    modules_without_code: list[str] = []
    # without a table every module-level check would only repeat imports_table_missing
    judged_modules = {scope.module for scope in scopes.values()} if table is not None else set()
    for module in sorted(judged_modules, key=lambda m: order.get(m, 0)):
        module_rows = uses_by_module.get(module, [])
        uses = {_key(row) for _, row in module_rows}
        rejected = rejected_by_module.get(module, [])
        rejected_keys = {_key(row) for row in rejected}
        for known in case.knows.get(module, ()):
            covered = any(provider == known for _, provider in uses) or any(
                row.get("provider") == known and row.get("candidate") == KNOWS for row in rejected)
            if not covered:
                findings.append(_finding("imports_knows_uncovered", module, provider=known))
                pending += 1
        if code_status != AVAILABLE:
            continue
        module_code = code_modules.get(module)
        if module_code is None:
            modules_without_code.append(module)
            continue
        named = code_candidates(case, module, module_code)
        for key, candidate in named.items():
            if key not in uses and key not in rejected_keys:
                findings.append(_finding("imports_code_undeclared", module, candidate=candidate.as_json()))
                pending += 1
        # each row is judged on its own: an exempt row of one scope does not excuse another's
        for scope_id, row in module_rows:
            key = _key(row)
            if key in named or row.get("basis") in _CODE_EXEMPT_BASIS or row.get("as") in _CODE_EXEMPT_AS:
                continue
            if isinstance(row.get("code_outdated"), str) and row["code_outdated"].strip():
                continue
            findings.append(_finding("imports_code_unused", scope_id, symbol=key[0], provider=key[1]))

    if code_status == UNAVAILABLE and case.factory_target is not None:
        findings.append(_finding("imports_factory_unavailable", case.project_root,
                                 f"{FINDING_MESSAGES['imports_factory_unavailable']}: {code.get('reason')}",
                                 factory_project=case.factory_target))

    findings.sort(key=lambda item: (item["code"], item["subject"], json.dumps(item, sort_keys=True, default=str)))
    fenced = fence.enforce(findings)
    errors = fence.stops(fenced)
    code_findings = sum(1 for item in fenced if item["code"].startswith("imports_code_"))
    handoff_ready = errors == 0
    return {
        "schema_version": REPORT_SCHEMA,
        "project_root": case.project_root,
        "table": TABLE_FILE,
        "summary": {
            "scopes": len(scopes),
            "scopes_decided": sum(1 for item in status.values() if item["state"] != "missing"),
            "pending": pending,
            "stale": stale,
            "code_evidence": code_status,
            "modules_without_code": modules_without_code,
            "errors": errors,
            "warnings": 0,
            "handoff_ready": handoff_ready,
            "strict_ready": handoff_ready and code_status == AVAILABLE and not modules_without_code
                            and code_findings == 0,
        },
        "code_evidence": {key: value for key, value in code.items() if key != "modules"},
        "out_of_scope": case.out_of_scope(),
        "scopes": status,
        "derived": {"module_internal": derive(table)},
        "findings": fenced,
    }


def coverage(project: Path, factory_root: Path | None = None) -> dict[str, Any]:
    project = Path(project).resolve()
    case = case_loader.load(project)
    return analyze(case, load_table(project), _code_evidence(project, case, factory_root), project)


def assembly_report(project: Path, factory_root: Path | None = None) -> dict[str, Any]:
    """The assembly check: the closure is closed and global_spec.json carries its projection.

    A hand edit of imports.module_internal, or an assembly older than the last
    decision, is ``imports_projection_drift`` (IMPORTS_WORKBENCH.md §9.3).
    """
    project = Path(project).resolve()
    case = case_loader.load(project)
    table = load_table(project)
    report = analyze(case, table, _code_evidence(project, case, factory_root), project)
    if table is not None and isinstance(table, dict) and isinstance(table.get("scopes"), dict):
        extra = [_finding("imports_projection_drift", item["module"],
                          f"imports.module_internal.{item['module']}.{item['provider']} in global_spec.json is not "
                          "the projection of 65_imports.json: run tools/design_spec_projection.py --apply", **item)
                 for item in drift(case, table)]
        if extra:
            report["findings"] = fence.enforce(report["findings"] + extra)
            report["summary"]["errors"] = fence.stops(report["findings"])
            report["summary"]["handoff_ready"] = False
            report["summary"]["strict_ready"] = False
        report["summary"]["drift"] = len(extra)
    return report


# -- the draft ---------------------------------------------------------------

def draft_table(case: Case, table: dict[str, Any] | None, code: dict[str, Any]) -> dict[str, Any]:
    """The table with a scope for every contract and module and every undecided candidate in ``pending``.

    Only the structural candidates of a new scope's own signature go into ``uses``;
    nothing else is accepted for the author.
    """
    table = table if isinstance(table, dict) and isinstance(table.get("scopes"), dict) else {}
    result: dict[str, Any] = {"schema_version": TABLE_SCHEMA, "scopes": dict(table.get("scopes") or {})}
    code_modules = code.get("modules") or {} if code.get("status") == AVAILABLE else {}
    scopes = case.scopes()
    order = _order(case)
    # operation scopes first: the module scope's code and Knows pending see their uses
    for scope_id, scope in sorted(scopes.items(), key=lambda item: item[1].contract is None):
        entry = result["scopes"].get(scope_id)
        if not isinstance(entry, dict):
            own = scope_candidates(case, scope)
            providers: dict[str, list[str]] = {}
            for c in own.values():
                providers.setdefault(c.symbol, []).append(c.provider)
            # a signature type is accepted only when exactly one provider may give it;
            # a choice of providers, or one the module order forbids, waits for the author
            entry = {
                "basis_sha256": scope.basis_sha256,
                "uses": [{"symbol": c.symbol, "provider": c.provider, "as": "annotates", "basis": "contract"}
                         for c in own.values()
                         if "contract" in c.evidence and len(providers[c.symbol]) == 1
                         and order.get(c.provider, len(order)) < order.get(scope.module, -1)],
                "rejected": [],
            }
        else:
            entry = dict(entry)
        uses, rejected = _rows(entry, "uses"), _rows(entry, "rejected")
        decided = {_key(row) for row in uses} | {_key(row) for row in rejected}
        pending = [c.as_json() for key, c in scope_candidates(case, scope, uses).items() if key not in decided]
        if scope.contract is None:
            # the operation scopes of the module; its own old entry is being rebuilt
            module_scopes = [e for sid, e in result["scopes"].items()
                             if str(sid).split(".", 1)[0] == scope.module and sid in scopes and sid != scope_id]
            module_uses = {_key(row) for e in module_scopes for row in _rows(e, "uses")} | {
                _key(row) for row in uses}
            module_rejected = {_key(row) for e in module_scopes for row in _rows(e, "rejected")} | {
                _key(row) for row in rejected}
            # a symbol the code names that an operation scope already has pending is
            # marked there (the author decides it once); the rest waits in the module scope
            elsewhere: dict[tuple[Any, Any], list[dict[str, Any]]] = {}
            for e in module_scopes:
                for row in e.get("pending") or ():
                    if isinstance(row, dict):
                        elsewhere.setdefault((row.get("symbol"), row.get("provider")), []).append(row)
            for key, c in code_candidates(case, scope.module, code_modules.get(scope.module) or {}).items():
                if key in module_uses or key in module_rejected:
                    continue
                if key in elsewhere:
                    for row in elsewhere[key]:
                        row["candidates"] = sorted(set(row.get("candidates") or ()) | {"code_used"})
                        row["evidence"] = list(dict.fromkeys([*(row.get("evidence") or ()), "code"]))
                    continue
                pending.append(c.as_json())
            for known in case.knows.get(scope.module, ()):
                if not any(provider == known for _, provider in module_uses) and not any(
                        row.get("provider") == known and row.get("candidate") == KNOWS
                        for e in module_scopes for row in _rows(e, "rejected")):
                    pending.append({"symbol": "*", "provider": known, "candidates": [KNOWS],
                                    "evidence": [f"knows:{known}"]})
        entry["uses"], entry["rejected"] = uses, rejected
        if pending:
            entry["pending"] = pending
        else:
            entry.pop("pending", None)
        result["scopes"][scope_id] = {key: entry[key] for key in ("basis_sha256", "uses", "rejected", "pending")
                                      if key in entry} | {k: v for k, v in entry.items()
                                                          if k not in {"basis_sha256", "uses", "rejected", "pending"}}
    result["scopes"] = dict(sorted(result["scopes"].items()))
    return result


def draft(project: Path, factory_root: Path | None = None) -> dict[str, Any]:
    project = Path(project).resolve()
    case = case_loader.load(project)
    table = draft_table(case, load_table(project), _code_evidence(project, case, factory_root))
    table_path(project).write_text(json.dumps(table, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "table": str(table_path(project)),
        "scopes": len(table["scopes"]),
        "pending": sum(len(entry.get("pending") or ()) for entry in table["scopes"].values()),
    }
