"""Closure-completeness fuses over one workbench case.

The design gates verify that what the specification states is consistent; none
of them ask whether the stated closure is complete. Four defect classes reached
generation through that blind spot on 2026-08-23 (empty package stream model,
a manifest catalogue no operation produces, catalogues closed only in prose).
This tool reports them:

  model_without_fields   a non-enum, non-interface model with no fields
  orphan_read_entity     an entity returned by operations but accepted or
                         created by none
  table_without_writer   a persistence_backend table with readers and no
                         insert/update/upsert
  prose_closure_leak     a State 1 field line enumerating closed values whose
                         field type is not an enum

A fifth class surfaced on 2026-08-29: an ambient effect. A note demands "record
UTC observation evidence" while no contract parameter, rule address, or module
dependency names a time source, so every generation run invents its own clock.
Two fuses close it from opposite sides:

  ambient_time_note              a note uses ambient current-time language and
                                 the covered contract has neither a datetime
                                 parameter nor a clock-port dependency
  fresh_timestamp_without_source a public mutating operation (State impact in
                                 50_public_apis.md) returns models carrying
                                 datetime fields while its inputs carry none
                                 and its module declares no clock port

Report-only by default; --strict exits 1 when anything is found.

    python tools/design_closure_gaps.py examples/<case> [--json] [--strict]
"""
from __future__ import annotations

import argparse
import glob
import json
import re
from pathlib import Path
from typing import Any


def load_spec(case: Path) -> dict[str, Any]:
    return json.loads((case / "global_spec.json").read_text(encoding="utf-8"))


def model_names_in(text: str, models: set[str]) -> set[str]:
    return {m for m in models if re.search(rf"\b{re.escape(m)}\b", text)}


def check_models(spec: dict[str, Any]) -> list[dict[str, Any]]:
    findings = []
    for name, decl in (spec.get("models") or {}).items():
        if not isinstance(decl, dict):
            continue
        if decl.get("kind") in {"enum", "interface", "protocol"}:
            continue
        if not decl.get("fields"):
            findings.append({
                "code": "model_without_fields", "model": name,
                "message": f"{name}: a runtime model with no fields states nothing; the generator will invent its content",
            })
    return findings


def check_orphan_reads(spec: dict[str, Any]) -> list[dict[str, Any]]:
    models = {n for n, d in (spec.get("models") or {}).items()
              if isinstance(d, dict) and d.get("kind") not in {"enum", "interface", "protocol"}}
    field_types = " ".join(
        " ".join(str(t) for t in d.get("fields", {}).values())
        for d in (spec.get("models") or {}).values() if isinstance(d, dict)
    )
    returned: set[str] = set()
    accepted: set[str] = set()
    for signature in (spec.get("contracts") or {}).values():
        params, _, ret = str(signature).partition("->")
        returned |= model_names_in(ret, models)
        accepted |= model_names_in(params, models)
    notes_text = "\n".join(spec.get("notes") or [])
    findings = []
    for name in sorted(returned - accepted):
        decl = spec["models"][name]
        if decl.get("identity") not in {"entity", None}:
            continue
        # embedded in another model's fields => produced wherever the parent is produced
        if re.search(rf"\b{re.escape(name)}\b", field_types):
            continue
        # a FIELD_ASSIGNMENT/PROVENANCE note that spells out its construction counts
        if re.search(rf"\b{re.escape(name)}\b[^.]*(?:=|carries|is built|constructed)", notes_text):
            continue
        findings.append({
            "code": "orphan_read_entity", "model": name,
            "message": f"{name} is returned by operations but no operation accepts or constructs it; nothing in the spec produces what the readers read",
        })
    return findings


def check_external_returns(spec: dict[str, Any]) -> list[dict[str, Any]]:
    obligations = spec.get("implementation_obligations") or {}
    interfaces = {n for n, d in (spec.get("models") or {}).items()
                  if isinstance(d, dict) and d.get("kind") in {"interface", "protocol"}}
    findings = []
    for symbol, signature in (spec.get("contracts") or {}).items():
        _, _, ret = str(signature).partition("->")
        for name in model_names_in(ret, interfaces):
            if (obligations.get(name) or {}).get("disposition") == "external":
                findings.append({
                    "code": "external_interface_returned", "model": name, "contract": symbol,
                    "message": f"{symbol} returns {name}, declared disposition external: the project must construct what it returns, so no producer exists by declaration",
                })
    return findings


def check_tables(spec: dict[str, Any]) -> list[dict[str, Any]]:
    backend = (spec.get("rules") or {}).get("persistence_backend")
    if not isinstance(backend, dict):
        return []
    writes: set[str] = set()
    reads: set[str] = set()
    for repo in backend.get("repositories", []):
        for method in repo.get("methods", []):
            table = method.get("table")
            if not table:
                continue
            if method.get("query") in {"insert", "insert_many", "update_fields", "upsert", "upsert_many", "append"}:
                writes.add(table)
            else:
                reads.add(table)
    return [{
        "code": "table_without_writer", "table": table,
        "message": f"table {table} has readers and no insert/update in any repository",
    } for table in sorted(reads - writes)]


FIELD_LINE = re.compile(r"^- `(?P<field>[a-z_][a-z0-9_]*)(?::\s*(?P<type>[^`]+))?`[^\n]*?—(?P<tail>.+)$")
VALUE_LIST = re.compile(r"(?:`[a-z][a-z0-9_]{2,}`\s*(?:,|or|\|)\s*)+`[a-z][a-z0-9_]{2,}`")


def check_prose(case: Path, spec: dict[str, Any]) -> list[dict[str, Any]]:
    enums = {n for n, d in (spec.get("models") or {}).items() if isinstance(d, dict) and d.get("kind") == "enum"}
    enum_vals = {v for n in enums for v in spec["models"][n].get("values", [])}
    all_fields = {f for d in (spec.get("models") or {}).values() if isinstance(d, dict) for f in (d.get("fields") or {})}
    findings = []
    for path in sorted(glob.glob(str(case / "01_*.md"))):
        in_withdrawn = False
        for lineno, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
            if line.startswith("## "):
                in_withdrawn = "withdrawn" in line.lower()
            if in_withdrawn:
                continue
            m = FIELD_LINE.match(line.strip())
            if not m or not VALUE_LIST.search(m.group("tail")):
                continue
            declared = (m.group("type") or "").split(" ")[0].strip()
            if declared in enums:
                continue
            values = re.findall(r"`([a-z][a-z0-9_]{2,})`", m.group("tail"))
            if len(values) < 2 or all(v in enum_vals for v in values) or all(v in all_fields for v in values):
                continue
            findings.append({
                "code": "prose_closure_leak", "file": Path(path).name, "line": lineno,
                "field": m.group("field"), "values": values[:8],
                "message": f"{Path(path).name}:{lineno} field {m.group('field')} enumerates closed values in prose but its type is not an enum",
            })
    return findings


NOTE_SCOPE_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*:")
# Ambient current-time language only. Bare "UTC"/"wall-clock" stays out: the
# timezone-awareness boilerplate in dependency-boundary notes constrains stored
# values and names no effect.
AMBIENT_TIME_RE = re.compile(
    r"\b(?:operation utc time|current (?:utc )?time|utc observation|observation evidence|current wall[- ]?clock)\b",
    re.IGNORECASE,
)
DATETIME_PARAM_RE = re.compile(r":\s*datetime\b")
PUBLIC_OP_HEADING_RE = re.compile(r"^## `public_op:([a-z_][a-z0-9_]*)\.([a-z_][a-z0-9_]*)`")
READ_ONLY_IMPACT_RE = re.compile(r"^\s*(?:read[- ]only|none)\b", re.IGNORECASE)


def _type_closure_has_datetime(type_str: object, models: dict[str, Any], seen: set[str] | None = None) -> bool:
    if seen is None:
        seen = set()
    names = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", str(type_str))
    if "datetime" in names:
        return True
    for name in names:
        decl = models.get(name)
        if isinstance(decl, dict) and name not in seen:
            seen.add(name)
            for field_type in (decl.get("fields") or {}).values():
                if _type_closure_has_datetime(field_type, models, seen):
                    return True
    return False


def _module_of(name: str, func_module: dict[str, str]) -> str | None:
    # "Class.__init__" is owned by the module that owns "Class"
    return func_module.get(name) or func_module.get(name.rsplit(".", 1)[0])


def clock_interfaces(models: dict[str, Any], contracts: dict[str, Any]) -> set[str]:
    """Interface models exposing an operation that returns bare datetime."""
    found: set[str] = set()
    for name, signature in contracts.items():
        owner, dot, _ = str(name).partition(".")
        if not dot:
            continue
        decl = models.get(owner)
        if not (isinstance(decl, dict) and decl.get("kind") in {"interface", "protocol"}):
            continue
        _, _, ret = str(signature).partition("->")
        if ret.strip() == "datetime":
            found.add(owner)
    return found


def modules_with_clock(models: dict[str, Any], contracts: dict[str, Any], func_module: dict[str, str]) -> set[str]:
    """Modules whose __init__ retains a clock-port interface."""
    interfaces = clock_interfaces(models, contracts)
    if not interfaces:
        return set()
    modules: set[str] = set()
    for name, signature in contracts.items():
        if not str(name).endswith(".__init__"):
            continue
        params, _, _ = str(signature).partition("->")
        if any(re.search(rf"\b{re.escape(iface)}\b", params) for iface in interfaces):
            module = _module_of(str(name), func_module)
            if module:
                modules.add(module)
    return modules


def parse_state_impacts(case: Path) -> dict[str, dict[str, Any]]:
    """Public operations and their State impact from 50_public_apis.md."""
    path = case / "50_public_apis.md"
    if not path.is_file():
        return {}
    impacts: dict[str, dict[str, Any]] = {}
    current: str | None = None
    in_impact = False
    for line in path.read_text(encoding="utf-8").splitlines():
        heading = PUBLIC_OP_HEADING_RE.match(line)
        if heading:
            current = heading.group(2)
            impacts[current] = {"module": heading.group(1), "read_only": False, "impact": ""}
            in_impact = False
            continue
        if line.startswith("### "):
            in_impact = current is not None and line[4:].strip().casefold() == "state impact"
            continue
        if in_impact and current and line.strip() and not impacts[current]["impact"]:
            impacts[current]["impact"] = line.strip()
            impacts[current]["read_only"] = bool(READ_ONLY_IMPACT_RE.match(line.strip()))
    return impacts


def ambient_time_findings(models: dict[str, Any], contracts: dict[str, Any],
                          func_module: dict[str, str], notes: list[Any]) -> list[dict[str, Any]]:
    clocked = modules_with_clock(models, contracts, func_module)
    findings = []
    for note in notes:
        text = str(note)
        phrase = AMBIENT_TIME_RE.search(text)
        if not phrase:
            continue
        scope_match = NOTE_SCOPE_RE.match(text)
        scope = scope_match.group(1) if scope_match else ""
        params, _, _ = str(contracts.get(scope, "")).partition("->")
        if DATETIME_PARAM_RE.search(params):
            continue
        if _module_of(scope, func_module) in clocked:
            continue
        findings.append({
            "code": "ambient_time_note", "contract": scope, "phrase": phrase.group(0),
            "message": (f"{scope or 'unscoped note'}: note requires '{phrase.group(0)}' but the contract has no "
                        "datetime parameter and the module retains no clock port; an unnamed time source is "
                        "reinvented by every generation run"),
        })
    return findings


def fresh_timestamp_findings(models: dict[str, Any], contracts: dict[str, Any],
                             func_module: dict[str, str],
                             impacts: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    clocked = modules_with_clock(models, contracts, func_module)
    findings = []
    for function in sorted(impacts):
        if impacts[function]["read_only"]:
            continue
        signature = contracts.get(function)
        if not isinstance(signature, str) or "->" not in signature:
            continue
        params, _, ret = signature.partition("->")
        if not _type_closure_has_datetime(ret, models):
            continue
        if _type_closure_has_datetime(params, models):
            continue
        module = impacts[function].get("module") or _module_of(function, func_module)
        if module in clocked:
            continue
        findings.append({
            "code": "fresh_timestamp_without_source", "contract": function,
            "message": (f"{function}: public mutating operation returns datetime field(s) while its inputs carry "
                        f"none and module {module} retains no clock port; name the time source — a datetime "
                        "parameter or a clock dependency in __init__"),
        })
    return findings


def check_time_sources(case: Path, spec: dict[str, Any]) -> list[dict[str, Any]]:
    models = spec.get("models") or {}
    contracts = spec.get("contracts") or {}
    func_module = {f: module for module, funcs in (spec.get("module_functions") or {}).items()
                   for f in (funcs or [])}
    return (ambient_time_findings(models, contracts, func_module, spec.get("notes") or [])
            + fresh_timestamp_findings(models, contracts, func_module, parse_state_impacts(case)))


def run(case: Path) -> dict[str, Any]:
    spec = load_spec(case)
    findings = (check_models(spec) + check_orphan_reads(spec) + check_external_returns(spec)
                + check_tables(spec) + check_prose(case, spec) + check_time_sources(case, spec))
    return {"schema_version": "design_closure_gaps.v1", "case": str(case), "findings": findings,
            "summary": {f: sum(1 for x in findings if x["code"] == f) for f in
                        ("model_without_fields", "orphan_read_entity", "external_interface_returned", "table_without_writer", "prose_closure_leak",
                         "ambient_time_note", "fresh_timestamp_without_source")}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("case", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    report = run(args.case)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"closure gaps: {report['summary']}")
        for f in report["findings"]:
            print(f"  ✗ [{f['code']}] {f['message']}")
    return 1 if (args.strict and report["findings"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
