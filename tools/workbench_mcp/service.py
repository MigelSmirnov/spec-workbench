"""Read-only service behind the Spec Workbench MCP gateway.

One named mechanism: answer "where did this specification line come from, and
what does the workbench already know about it" for one logical project.

The factory MCP diagnoses an accepted spec and computes which ops instrument
may patch it. This service answers the question underneath: which accepted
design decision owns the touched name, whether a reported gap is an instance
of a known closure class, and whether a finding was already waived with a
reason. An agent that sees an accepted decision behind a spec address stops
patching design intent as if it were a bug.

Every project-scoped answer is computed on a temporary read-only worktree of
the project's canonical ref (authoring_pipeline.materialized_project), never
on someone's working checkout. Pure case-level functions take a materialized
``case_root`` so they stay testable against the checked-in example cases.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import authoring_pipeline
import design_closure_gaps
import design_index
import design_stage6_contracts
import project_navigation
from notes_workbench import language

SCHEMA_PREFIX = "spec_workbench_mcp"
FACTORY_TARGET_FILE = "90_factory_target.json"
CONTRACT_PLAN_FILE = "60_contract_plan.json"
CONTRACT_CATALOG_FILE = "60_contracts.json"
TRACE_FILE = "30_trace.json"
WAIVERS_FILE = "closure_gap_waivers.json"
ASSEMBLED_SPEC_FILE = "global_spec.json"

MAX_MENTIONED_ITEMS = 12
MAX_SECTION_LINES = 40
MAX_NOTES = 20


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _read_at_ref(repo_root: Path, ref: str, relpath: str) -> dict[str, Any] | None:
    """Read one JSON blob from a git ref without materializing a worktree."""
    try:
        raw = authoring_pipeline._git(repo_root, "show", f"{ref}:{relpath}")
    except authoring_pipeline.AuthoringPipelineError:
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


# ---------------------------------------------------------------- projects

def list_cases(repo_root: Path) -> dict[str, Any]:
    """Curated logical projects with their factory targets, from canonical refs."""
    rows = []
    for view in project_navigation.list_projects(repo_root):
        target = _read_at_ref(repo_root, view.resolved_ref, f"{view.path}/{FACTORY_TARGET_FILE}")
        rows.append({
            **project_navigation.as_jsonable(view),
            "factory_project": (target or {}).get("factory_project"),
        })
    return {"schema_version": f"{SCHEMA_PREFIX}_cases.v1", "cases": rows}


def resolve_case_for_factory_project(repo_root: Path, factory_project: str) -> str | None:
    """The workbench case id whose 90_factory_target names this factory project."""
    for row in list_cases(repo_root)["cases"]:
        if row.get("factory_project") == factory_project:
            return row.get("id")
    return None


# ---------------------------------------------------------------- provenance

def _surface_entry(case_root: Path, name: str) -> dict[str, Any] | None:
    plan = _load_json(case_root / CONTRACT_PLAN_FILE) or {}
    catalog = _load_json(case_root / CONTRACT_CATALOG_FILE) or {}
    for entry in plan.get("functions") or []:
        if isinstance(entry, dict) and entry.get("function") == name:
            return {
                "function": name,
                "module": entry.get("module"),
                "visibility": entry.get("visibility"),
                "public_operation": entry.get("public_operation"),
                "purpose": entry.get("purpose"),
                "signature": (catalog.get("contracts") or {}).get(name),
            }
    return None


def _module_of_name(case_root: Path, name: str, surface: dict[str, Any] | None) -> str | None:
    if surface and isinstance(surface.get("module"), str):
        return surface["module"].removeprefix("module:")
    plan = _load_json(case_root / CONTRACT_PLAN_FILE) or {}
    modules = {str(e.get("module") or "").removeprefix("module:")
               for e in plan.get("functions") or [] if isinstance(e, dict)}
    return name if name in modules else None


def _trace_ownership(case_root: Path, module: str | None) -> list[dict[str, Any]]:
    if not module:
        return []
    trace = _load_json(case_root / TRACE_FILE) or {}
    rows = []
    for decision_id, entry in sorted((trace.get("decisions") or {}).items()):
        if not isinstance(entry, dict):
            continue
        owner = entry.get("primary_owner") == f"module:{module}"
        consumer = f"module:{module}" in (entry.get("consumers") or [])
        if owner or consumer:
            rows.append({"decision": decision_id, "role": "owner" if owner else "consumer"})
    return rows


def _section_text(case_root: Path, item: dict[str, Any]) -> list[str]:
    source = item.get("source") or {}
    path = case_root / str(source.get("path") or "")
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    start = max(1, int(source.get("start_line") or 1))
    end = min(len(lines), int(source.get("end_line") or start))
    body = lines[start - 1:end]
    if len(body) > MAX_SECTION_LINES:
        body = body[:MAX_SECTION_LINES] + [f"... ({end - start + 1 - MAX_SECTION_LINES} more lines; "
                                           f"design_context {source.get('path')}:{start})"]
    return body


def _waivers_for(case_root: Path, name: str, module: str | None) -> list[dict[str, Any]]:
    payload = _load_json(case_root / WAIVERS_FILE) or {}
    hits = []
    for waiver in payload.get("waivers") or []:
        if not isinstance(waiver, dict):
            continue
        rendered = json.dumps(waiver, ensure_ascii=False)
        if name in rendered or (module and module in rendered):
            hits.append(waiver)
    return hits


def _scoped_notes(case_root: Path, name: str) -> list[str]:
    spec = _load_json(case_root / ASSEMBLED_SPEC_FILE) or {}
    scoped = []
    for note in spec.get("notes") or []:
        text = str(note)
        scope = language.note_scope(text)
        if scope == name or (scope or "").split(".", 1)[0] == name:
            scoped.append(text)
    return scoped[:MAX_NOTES]


def provenance(case_root: Path, name: str) -> dict[str, Any]:
    """Everything the design corpus states about one name, decisions first.

    Decisions come back with their authored body so the caller sees the
    rationale and consequence, not just a pointer. A non-empty ``decisions``
    list means the name is design intent with an owner: changing its meaning
    requires engaging those decisions, not only the spec address.
    """
    surface = _surface_entry(case_root, name)
    module = _module_of_name(case_root, name, surface)

    mentions = design_index.find_mentions_in_items(case_root, name)
    items: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for mention in mentions:
        key = mention.item_key
        if key is None:
            continue
        if key not in items:
            item = design_index.get_item(case_root, key) or {}
            items[key] = {
                "key": key,
                "kind": item.get("kind"),
                "state": item.get("state"),
                "title": mention.item_title,
                "location": f"{mention.path}:{mention.line}",
                "mentions": 0,
            }
            order.append(key)
        items[key]["mentions"] += 1

    decisions = []
    referenced = []
    for key in order[:MAX_MENTIONED_ITEMS]:
        row = items[key]
        if row["kind"] == "decision":
            item = design_index.get_item(case_root, key) or {}
            decisions.append({**row, "body": _section_text(case_root, item)})
        else:
            referenced.append(row)

    for trace_row in _trace_ownership(case_root, module):
        if trace_row["decision"] not in items:
            item = design_index.get_item(case_root, trace_row["decision"]) or {}
            if item:
                decisions.append({
                    "key": trace_row["decision"],
                    "kind": "decision",
                    "state": item.get("state"),
                    "title": item.get("title"),
                    "location": f"{(item.get('source') or {}).get('path')}:{(item.get('source') or {}).get('start_line')}",
                    "mentions": 0,
                    "trace_role": trace_row["role"],
                    "body": _section_text(case_root, item) if trace_row["role"] == "owner" else [],
                })

    return {
        "schema_version": f"{SCHEMA_PREFIX}_provenance.v1",
        "name": name,
        "surface": surface,
        "module": module,
        "decisions": decisions,
        "referenced_in": referenced,
        "waivers": _waivers_for(case_root, name, module),
        "notes": _scoped_notes(case_root, name),
        "deliberate_design_signals": bool(decisions) or bool(_waivers_for(case_root, name, module)),
    }


# ---------------------------------------------------------------- diagnostics

def _waived(finding: dict[str, Any], waivers: list[dict[str, Any]]) -> str | None:
    for waiver in waivers:
        keys = {k: v for k, v in waiver.items() if k not in {"reason", "decided"}}
        if keys and all(finding.get(k) == v for k, v in keys.items()) and waiver.get("reason"):
            return str(waiver["reason"])
    return None


def closure(case_root: Path) -> dict[str, Any]:
    """Closure-gap fuses with waiver status, plus State 6 contract warnings.

    A waived finding is a deliberate decision with a recorded reason — treat it
    as design intent, not as a gap to close in passing.
    """
    report = design_closure_gaps.run(case_root)
    payload = _load_json(case_root / WAIVERS_FILE) or {}
    waivers = [w for w in payload.get("waivers") or [] if isinstance(w, dict)]
    findings = []
    for finding in report["findings"]:
        reason = _waived(finding, waivers)
        findings.append({**finding, "waived": reason is not None,
                         **({"waiver_reason": reason} if reason else {})})

    stage6: dict[str, Any] = {}
    try:
        lint = design_stage6_contracts.lint(case_root)
        stage6 = {"summary": lint["summary"],
                  "warnings": [f for f in lint["findings"] if f.get("severity") == "warning"]}
    except design_stage6_contracts.DesignStage6ContractsError as exc:
        stage6 = {"skipped": str(exc)}

    return {
        "schema_version": f"{SCHEMA_PREFIX}_closure.v1",
        "summary": report["summary"],
        "open_findings": [f for f in findings if not f["waived"]],
        "waived_findings": [f for f in findings if f["waived"]],
        "stage6_contracts": stage6,
    }


def notes_language(case_root: Path, scope: str | None = None) -> dict[str, Any]:
    """The notes-language report the factory gate will apply, optionally scoped."""
    report = language.report(case_root)
    if scope:
        report = {
            **report,
            "findings": [f for f in report["findings"]
                         if scope in json.dumps(f, ensure_ascii=False)],
            "filtered_to_scope": scope,
        }
    return report


def design_context(case_root: Path, location: str, radius: int = 6) -> dict[str, Any]:
    """Authored design text around PATH:LINE, with the owning indexed item."""
    context = design_index.context_at(case_root, location, radius=radius)
    return {
        "schema_version": f"{SCHEMA_PREFIX}_context.v1",
        "path": context.path,
        "line": context.line,
        "item_key": context.item_key,
        "item_title": context.item_title,
        "heading_path": list(context.heading_path),
        "lines": list(context.lines),
    }
