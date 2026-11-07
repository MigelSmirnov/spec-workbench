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

A module-level clock (system_clock_backend v2-v5, SPEC_STANDARD 6.9) is a
source for the modules that really depend on it: those importing its function
(the decided imports: 65_imports.json, else an assembled imports.module_internal,
an empty one included), or, before imports are decided, those whose State 3
Knows names the clock module (clock_consumers).

An operation may also obtain its time from a function it calls: an endpoint
returns the session whose expiry the access operation it delegates to
computes. Such an operation has a source when, through the calls the design
obliges — a note of the operation naming the callee (bare, ``Class.method``,
or ``param.method`` through its own contract) or a call a deterministic backend
emits, the same edges flow reachability reads (flow_closure) — it reaches a
function whose module has a time source and that returns a value carrying a
datetime, or the declared clock function itself. A callee the operation does
not call, a callee without a source, or one that returns no datetime is not a
source.

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

import design_stage5


def load_spec(case: Path) -> dict[str, Any]:
    return json.loads((case / "global_spec.json").read_text(encoding="utf-8"))


def model_names_in(text: str, models: set[str]) -> set[str]:
    return {m for m in models if re.search(rf"\b{re.escape(m)}\b", text)}


def check_models(spec: dict[str, Any]) -> list[dict[str, Any]]:
    findings = []
    for name, decl in (spec.get("models") or {}).items():
        if not isinstance(decl, dict):
            continue
        if decl.get("kind"):
            continue
        if not decl.get("fields"):
            findings.append({
                "code": "model_without_fields", "model": name,
                "message": f"{name}: a runtime model with no fields states nothing; the generator will invent its content",
            })
    return findings


def check_orphan_reads(spec: dict[str, Any]) -> list[dict[str, Any]]:
    models = {n for n, d in (spec.get("models") or {}).items()
              if isinstance(d, dict) and not d.get("kind")}
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
    contracts = spec.get("contracts") or {}
    owners = {f: m for m, fs in (spec.get("module_functions") or {}).items() for f in fs}

    def _provided(interface: str) -> bool:
        """A class outside models that carries every operation of the interface is its provider."""
        operations = {k.split(".", 1)[1] for k in contracts if k.startswith(interface + ".")} - {"__init__"}
        if not operations:
            return False
        classes = {k.split(".", 1)[0] for k in contracts if "." in k and k.split(".", 1)[0] != interface}
        for cls in classes:
            if owners.get(cls, "models") == "models":
                continue
            if operations <= {k.split(".", 1)[1] for k in contracts if k.startswith(cls + ".")}:
                return True
        return False

    for symbol, signature in contracts.items():
        _, _, ret = str(signature).partition("->")
        for name in model_names_in(ret, interfaces):
            if _provided(name):
                continue  # PR #31: the provider is planned and contracted; the return is produced
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
    """Public operations and their State impact from the State 5 documents."""
    impacts: dict[str, dict[str, Any]] = {}
    for path in design_stage5.public_api_documents(case):
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


def time_source_authorities(spec: dict[str, Any]) -> set[str]:
    """Modules rules.time_source_policy (SPEC_STANDARD 6.8) declares as the host wall-clock reader.

    Such a module is the named time source itself: it has no clock port to retain.
    """
    policy = (spec.get("rules") or {}).get("time_source_policy")
    wall = policy.get("wall_clock") if isinstance(policy, dict) else None
    modules = wall.get("authority_modules") if isinstance(wall, dict) else None
    return {m for m in modules if isinstance(m, str)} if isinstance(modules, list) else set()


CLOCK_CLOSURE_FILE = "70_system_clock_closure.json"
CLOCK_FUNCTION_KEYS = ("function", "wall_clock_function")


def declared_clock_function(case: Path, spec: dict[str, Any] | None = None) -> tuple[str, str] | None:
    """(module, function) of a module-level wall-clock operation the design declares.

    Read from the assembled ``rules.system_clock_backend`` when there is one,
    else from the closed ``70_system_clock_closure.json`` (SPEC_STANDARD 6.9:
    v2 ``function``, v3 ``wall_clock_function``, v4 ``function``). A class
    form (v1) hands out time through a port in ``__init__`` instead.
    """
    backend = ((spec or {}).get("rules") or {}).get("system_clock_backend")
    if not isinstance(backend, dict):
        path = Path(case) / CLOCK_CLOSURE_FILE
        try:
            closure = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            closure = None
        if not isinstance(closure, dict) or closure.get("status") != "closed":
            return None
        backend = closure.get("backend_ir")
    wiring = backend.get("wiring") if isinstance(backend, dict) else None
    if not isinstance(wiring, dict) or not isinstance(wiring.get("module"), str):
        return None
    function = next((wiring[key] for key in CLOCK_FUNCTION_KEYS if isinstance(wiring.get(key), str)), None)
    return (wiring["module"], function) if function else None


def _state3_knows(case: Path) -> dict[str, list[str]]:
    try:
        import design_stage3
        from value_flow_workbench.case import _knows
        modules = {item.name for item in design_stage3.parse_modules(Path(case))}
    except Exception:  # an unreadable State 3 declares no dependency
        return {}
    return _knows(Path(case), modules)


IMPORTS_TABLE_FILE = "65_imports.json"


def decided_imports(case: Path, spec: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """``module_internal`` once the imports are decided, or None while they are not.

    The imports closure table (65_imports.json, IMPORTS_WORKBENCH.md) is the
    authoritative decision: when it exists, its derivation is the answer, an
    empty one included. Without a table, an assembled ``imports.module_internal``
    that is present — empty or not — is a decision too (a migrated case). Only
    when neither exists are the imports undecided. Truthiness never decides:
    a decided empty table hands the clock to nobody.
    """
    path = Path(case) / IMPORTS_TABLE_FILE
    if path.is_file():
        try:
            table = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            table = None
        if isinstance(table, dict) and isinstance(table.get("scopes"), dict):
            from imports_workbench.service import derive
            return derive(table)
    imports = (spec or {}).get("imports")
    if isinstance(imports, dict) and "module_internal" in imports:
        decided = imports["module_internal"]
        return decided if isinstance(decided, dict) else {}
    return None


def clock_consumers(case: Path, spec: dict[str, Any] | None = None) -> set[str]:
    """Modules handed the declared module-level clock by a real dependency.

    Once the imports are decided (``decided_imports``), a consumer is a module
    that imports the clock function from the clock module — exactly the edge
    the Factory's conformance gate treats as a handed clock — and a decided
    table with no such edge hands it to nobody. While they are undecided
    (States 6 and 7 of a new case), it is a module whose State 3 ``Knows``
    names the clock module. A module with neither is not a consumer, however
    its notes speak of time: an arbitrary module never inherits the clock.
    """
    clock = declared_clock_function(case, spec)
    if clock is None:
        return set()
    module, function = clock
    imports = decided_imports(case, spec)
    if imports is not None:
        return {consumer for consumer, providers in imports.items()
                if isinstance(providers, dict) and function in (providers.get(module) or [])}
    return {consumer for consumer, known in _state3_knows(case).items() if module in known}


def time_sources(case: Path, spec: dict[str, Any] | None = None) -> set[str]:
    """Modules that have a declared time source without a parameter or port:
    the policy's authorities and the consumers of a module-level clock."""
    return (time_source_authorities(spec) if spec else set()) | clock_consumers(case, spec)


def ambient_time_findings(models: dict[str, Any], contracts: dict[str, Any],
                          func_module: dict[str, str], notes: list[Any],
                          sources: set[str] = frozenset(),
                          through: Any = None) -> list[dict[str, Any]]:
    clocked = modules_with_clock(models, contracts, func_module) | sources
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
        if through is not None:
            wanted, covered = through(scope, now=True)
            if wanted <= set(covered):
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
                             impacts: dict[str, dict[str, Any]],
                             sources: set[str] = frozenset(),
                             through: Any = None) -> list[dict[str, Any]]:
    clocked = modules_with_clock(models, contracts, func_module) | sources
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
        supplied: dict[str, str] = {}
        if through is not None:
            wanted, supplied = through(function)
            if wanted and wanted <= set(supplied):
                continue
        open_fields = sorted(f or "datetime" for f in (wanted - set(supplied))) if through is not None else []
        findings.append({
            "code": "fresh_timestamp_without_source", "contract": function,
            **({"unsupplied": open_fields, "supplied": {f or "datetime": s for f, s in sorted(supplied.items())}}
               if supplied else {}),
            "message": (f"{function}: public mutating operation returns datetime field(s) "
                        + (f"{', '.join(open_fields)} " if supplied else "")
                        + f"while its inputs carry none, module {module} retains no clock port, and "
                        + ("no function it calls supplies the time"
                           if not supplied else
                           "its calls supply only " + ", ".join(f"{f or 'datetime'} ({s})"
                                                              for f, s in sorted(supplied.items())))
                        + "; name the time source — a datetime parameter, a clock dependency in __init__, a "
                        "module-level clock it depends on, or the call to an operation that returns it"),
        })
    return findings


def call_edges(case: Path, spec: dict[str, Any] | None, func_module: dict[str, str],
               contracts: dict[str, Any], notes: list[Any] | None = None) -> dict[str, set[str]]:
    """caller -> callees the design obliges: note calls and deterministic backend calls (flow_closure).

    The notes are the ones given, else the assembled ones, else ``80_notes.md``.
    """
    import flow_closure

    if notes is None:
        assembled = (spec or {}).get("notes")
        notes = assembled if isinstance(assembled, list) and assembled else None
    if notes is not None:
        edges = flow_closure.note_call_edges([str(n) for n in notes], func_module, contracts)
    else:
        edges = flow_closure._note_calls(Path(case), func_module, contracts)
    try:
        backend = flow_closure._backend_calls(Path(case), func_module, contracts)
    except Exception:  # an unreadable backend obliges no call
        backend = {}
    for caller, callees in backend.items():
        edges.setdefault(caller, set()).update(callees)
    return edges


def datetime_fields(type_str: object, models: dict[str, Any], seen: set[str] | None = None) -> set[str]:
    """Names of the datetime-valued fields a type carries (``""`` for a bare datetime)."""
    seen = set() if seen is None else seen
    names = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", str(type_str))
    found = {""} if "datetime" in names else set()
    for name in names:
        decl = models.get(name)
        if isinstance(decl, dict) and name not in seen:
            seen.add(name)
            for field, field_type in (decl.get("fields") or {}).items():
                if re.search(r"\bdatetime\b", str(field_type)):
                    found.add(str(field))
                found |= {f for f in datetime_fields(field_type, models, seen) if f}
    return found


def covered_timestamps(function: str, wanted: set[str], edges: dict[str, set[str]],
                       func_module: dict[str, str], clocked: set[str], contracts: dict[str, Any],
                       models: dict[str, Any], clock: tuple[str, str] | None = None,
                       producers: set[str] = frozenset(),
                       _stack: frozenset[str] = frozenset()) -> dict[str, str]:
    """Which of the ``wanted`` datetime fields of ``function`` a call supplies: field -> source.

    A value travels back only through what a call returns. ``function``'s
    obliged calls (notes, deterministic backends; contracted functions only,
    never a class) supply a field when:

    - the call is the clock function itself: ``function`` reads the current
      time and makes every field it wants from it;
    - the callee returns a datetime field of that name and either makes time
      (``producers``: a mutating public operation or one whose note needs the
      current time) in a module with a source, or is itself supplied with that
      field by its own calls.

    A call that returns none of the wanted fields carries nothing back,
    whatever it does inside (a validation returning ``bool`` that reads the
    clock gives its caller no timestamp). A read returning stored timestamps
    makes no fresh one. Each field is judged on its own: a callee supplying
    ``expires_at`` leaves ``recorded_at`` to its own source. ``""`` stands for
    a bare datetime (a note that needs the current time wants that).
    """
    covered: dict[str, str] = {}
    if not wanted:
        return covered
    for callee in sorted(edges.get(function, ())):
        if clock is not None and callee == clock[1]:
            for field in wanted:
                covered.setdefault(field, callee)
            continue
        if callee == function or callee in _stack or callee in models or callee not in contracts:
            continue
        carried = wanted & datetime_fields(str(contracts.get(callee, "")).partition("->")[2], models)
        if not carried:
            continue
        if callee in producers and _module_of(callee, func_module) in clocked:
            for field in carried:
                covered.setdefault(field, callee)
            continue
        deeper = covered_timestamps(callee, carried, edges, func_module, clocked, contracts, models, clock,
                                    producers, _stack | {function})
        for field, source in deeper.items():
            covered.setdefault(field, source)
    return covered


def time_producers(case: Path, spec: dict[str, Any] | None, notes: list[Any] | None = None) -> set[str]:
    """Operations that make a fresh timestamp: mutating public operations, and scopes whose notes need now."""
    produced = {name for name, row in parse_state_impacts(Path(case)).items() if not row["read_only"]}
    if notes is None:
        assembled = (spec or {}).get("notes")
        if isinstance(assembled, list) and assembled:
            notes = assembled
        else:
            path = Path(case) / "80_notes.md"
            notes = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    for note in notes:
        text = str(note)
        scope = NOTE_SCOPE_RE.match(text)
        if scope and AMBIENT_TIME_RE.search(text):
            produced.add(scope.group(1))
    return produced


def calls_supplying_time(case: Path, spec: dict[str, Any] | None, models: dict[str, Any],
                         contracts: dict[str, Any], func_module: dict[str, str], sources: set[str],
                         notes: list[Any] | None = None):
    """function -> (the datetime fields it must supply, those its calls supply: field -> source).

    ``now=True`` asks for the current time itself (a note that needs it).
    """
    clocked = modules_with_clock(models, contracts, func_module) | set(sources)
    edges = call_edges(case, spec, func_module, contracts, notes)
    clock = declared_clock_function(case, spec)
    producers = time_producers(case, spec, notes)

    def through(function: str, now: bool = False) -> tuple[set[str], dict[str, str]]:
        wanted = {""} if now else datetime_fields(str(contracts.get(function, "")).partition("->")[2], models)
        return wanted, covered_timestamps(function, wanted, edges, func_module, clocked, contracts, models,
                                          clock, producers)

    return through


def check_time_sources(case: Path, spec: dict[str, Any]) -> list[dict[str, Any]]:
    models = spec.get("models") or {}
    contracts = spec.get("contracts") or {}
    func_module = {f: module for module, funcs in (spec.get("module_functions") or {}).items()
                   for f in (funcs or [])}
    sources = time_sources(case, spec)
    through = calls_supplying_time(case, spec, models, contracts, func_module, sources)
    return (ambient_time_findings(models, contracts, func_module, spec.get("notes") or [], sources, through)
            + fresh_timestamp_findings(models, contracts, func_module, parse_state_impacts(case), sources,
                                       through))


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
