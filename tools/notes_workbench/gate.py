from __future__ import annotations

import fence

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from notes_workbench.note_standard import (
    NOTE_CLASSES,
    REFERENCE_CLASS_PREFIX,
    SINGLETON_CLASSES,
    SUSPICIOUS_CLASS_PAIRS,
)
from persistence_workbench import authoring as persistence_authoring
from project_extensions import deterministic_backends

NOTE_RE = re.compile(r"^(?P<scope>[A-Za-z_][A-Za-z0-9_.]*):\s*\[(?P<class>[A-Z_]+)\]\s*(?P<text>.+?)\s*$")
ADDRESS_RE = re.compile(r"=\s*(?P<address>(?:config|models|rules)(?:\.[A-Za-z_][A-Za-z0-9_]*)+)")
STUB_PATTERNS = (
    r"^todo\b",
    r"^tbd\b",
    r"^implement\b",
    r"^handle\s+(?:errors?|exceptions?)\b(?:\s+appropriately|\s+correctly)?\.?$",
    r"^validate\s+(?:input|data)\b(?:\s+appropriately|\s+correctly)?\.?$",
    r"^process\s+(?:result|response|data)\b(?:\s+appropriately|\s+correctly)?\.?$",
    r"^return\s+(?:proper|correct|appropriate)\s+response\.?$",
    r"^call\s+.+\s+appropriately\.?$",
)


def _load_contract_scopes(project: Path) -> set[str]:
    path = project / "60_contracts.json"
    if not path.is_file():
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    contracts = payload.get("contracts", {})
    return set(contracts) if isinstance(contracts, dict) else set()


def _load_module_scopes(project: Path) -> set[str]:
    path = project / "30_modules.md"
    if not path.is_file():
        return set()
    result: set[str] = set()
    for match in re.finditer(r"`module:([A-Za-z_][A-Za-z0-9_]*)`", path.read_text(encoding="utf-8")):
        result.add(match.group(1))
    return result


def _load_structured_addresses(project: Path) -> set[str]:
    path = project / "60_data_closure.json"
    if not path.is_file():
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    result: set[str] = set()
    for placement in payload.get("placements", []):
        if isinstance(placement, dict):
            address = placement.get("address")
            if isinstance(address, str) and address:
                result.add(address)
    # Model closures are the normative home of closed data form (§15.2), so a
    # note may address a model construct without copying its members into the
    # note or into 60_data_closure.json. Index roots only: the model schema is
    # still emitted deterministically by the models backend.
    for model_path in sorted(project.glob("60_model_closure*.json")):
        model_payload = json.loads(model_path.read_text(encoding="utf-8"))
        models = model_payload.get("models")
        if isinstance(models, dict):
            result.update(
                f"models.{name}"
                for name in models
                if isinstance(name, str) and name
            )
    for backend in deterministic_backends(project):
        result |= backend.structured_addresses(project)
    return result


def _load_router_deterministic_scopes(project: Path) -> set[str]:
    """Return table-emitted HTTP handler scopes from Router Closure."""
    path = project / "70_router_closure.json"
    if not path.is_file():
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    result: set[str] = set()
    for item in payload.get("items", []):
        if not isinstance(item, dict) or item.get("emission") != "table":
            continue
        handler = item.get("handler")
        if isinstance(handler, str) and handler:
            result.add(handler)
    return result


def _load_persistence_deterministic_scopes(project: Path) -> set[str]:
    """Return scopes only from a fully closed, contract-bound persistence IR.

    An open or invalid persistence closure must not suppress the State 7 note
    requirement. Its own authoring gate remains responsible for reporting why it
    cannot be handed off.
    """
    try:
        report = persistence_authoring.coverage(project)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        return set()
    if not report.get("summary", {}).get("handoff_ready"):
        return set()
    scopes = report.get("deterministic_method_scopes", [])
    return {scope for scope in scopes if isinstance(scope, str) and scope}


def _load_deterministic_callable_scopes(project: Path) -> set[str]:
    """Return callables whose implementation is fully owned by deterministic IR.

    State 7 prose is not required for table-emitted HTTP handlers or methods of
    a closed table-emitted persistence repository. Irregular handlers and
    irregular repositories remain LLM-owned and deliberately require notes.
    """
    scopes = _load_router_deterministic_scopes(project) | _load_persistence_deterministic_scopes(project)
    for backend in deterministic_backends(project):
        scopes |= backend.deterministic_method_scopes(project)
    return scopes


def _load_provider_tables(project: Path) -> dict[str, tuple[str, tuple[str, ...]]]:
    """Record tables of the declared data provider: symbol -> (row model, fields).

    The access predicate for such a table is written in its row model's field
    vocabulary (SPEC_STANDARD §15.9: the model receives the access signature —
    and a table's signature includes the match). The gate needs the declared
    fields to prescribe that vocabulary, never to copy any value.
    """
    spec_path = project / "global_spec.json"
    if not spec_path.is_file():
        return {}
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    backend = (spec.get("rules") or {}).get("data_provider_backend")
    if not isinstance(backend, dict) or backend.get("kind") != "data_provider_backend":
        return {}
    fields_by_model: dict[str, tuple[str, ...]] = {}
    for model_path in sorted(project.glob("60_model_closure*.json")):
        try:
            payload = json.loads(model_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for name, declaration in (payload.get("models") or {}).items():
            if isinstance(declaration, dict) and isinstance(declaration.get("fields"), dict):
                fields_by_model[str(name)] = tuple(declaration["fields"])
    tables: dict[str, tuple[str, tuple[str, ...]]] = {}
    for symbol, row in (backend.get("constants") or {}).items():
        if not isinstance(row, dict) or row.get("value_type") != "record_tuple":
            continue
        row_model = str(row.get("row_model") or "")
        tables[str(symbol)] = (row_model, fields_by_model.get(row_model, ()))
    return tables


def _table_access_findings(
    notes: list[dict[str, Any]],
    tables: dict[str, tuple[str, tuple[str, ...]]],
    contract_scopes: set[str],
) -> list[dict[str, Any]]:
    """§15.9 access-predicate rule: naming a record table obliges naming its
    access.

    A note that names a record-table symbol must, in that same note, either
    name at least one declared field of the table's row model (the match is
    then spelled in the row vocabulary) or name a delegate — a contract whose
    own notes spell that access (transitively, as a fixpoint over the naming
    graph, because a note naming a function is how the slicer wires calls).
    The finding prescribes the exact fill: the declared field list and the
    predicate template, per NOTE_GATE.md 'Table access must be named'.
    """
    findings: list[dict[str, Any]] = []
    scope_res = {
        scope: re.compile(r"\b" + re.escape(scope) + r"\b") for scope in contract_scopes
    }
    # the general naming graph: a note naming another contract is the same
    # wiring the slicer turns into a call edge, so delegation may pass
    # through a scope that never names the table itself
    names_scopes: dict[str, set[str]] = defaultdict(set)
    for note in notes:
        for scope, pattern in scope_res.items():
            if scope != note["scope"] and pattern.search(note["text"]):
                names_scopes[note["scope"]].add(scope)
    for symbol, (row_model, fields) in sorted(tables.items()):
        if not fields:
            continue
        symbol_re = re.compile(r"\b" + re.escape(symbol) + r"\b")
        field_res = [re.compile(r"\b" + re.escape(field) + r"\b") for field in fields]
        mentions = [note for note in notes if symbol_re.search(note["text"])]
        if not mentions:
            continue

        def names_field(note: dict[str, Any]) -> bool:
            return any(field_re.search(note["text"]) for field_re in field_res)

        defining = {note["scope"] for note in mentions if names_field(note)}
        reaches = set(defining)
        while True:
            grew = False
            for scope, named in names_scopes.items():
                if scope not in reaches and named & reaches:
                    reaches.add(scope)
                    grew = True
            if not grew:
                break
        field_list = ", ".join(fields)
        for note in mentions:
            if note["scope"] in reaches or names_field(note):
                continue
            finding = _finding(
                "block",
                "table_access_unnamed",
                (
                    f"Note names {symbol} without naming its access: no declared "
                    f"{row_model} row field appears in the note and no delegate "
                    "spells it."
                ),
                line=note["line"],
                scope=note["scope"],
            )
            finding["hint"] = (
                "not decided — decide: spell the match in the row vocabulary, e.g. "
                f"'one imported {symbol} row whose <field> equals <expression>' — "
                f"{row_model} declares fields: {field_list}; or name the contract "
                "that owns the access. SPEC_STANDARD §15.9; NOTE_GATE.md "
                "'Table access must be named'."
            )
            findings.append(finding)
    return findings


def _address_resolves(address: str, known: set[str]) -> bool:
    if address in known:
        return True
    return any(address.startswith(item + ".") for item in known)


def _finding(severity: str, code: str, message: str, *, line: int | None = None, scope: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"severity": severity, "code": code, "message": message}
    if line is not None:
        result["line"] = line
    if scope is not None:
        result["scope"] = scope
    return result


def coverage(project: Path) -> dict[str, Any]:
    path = project / "80_notes.md"
    findings: list[dict[str, Any]] = []
    notes: list[dict[str, Any]] = []
    contract_scopes = _load_contract_scopes(project)
    module_scopes = _load_module_scopes(project)
    valid_scopes = contract_scopes | module_scopes
    known_addresses = _load_structured_addresses(project)
    deterministic_scopes = _load_deterministic_callable_scopes(project)

    if not path.is_file():
        findings.append(_finding("block", "missing_notes_file", "State 7 requires 80_notes.md before handoff."))
    else:
        for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            match = NOTE_RE.fullmatch(line)
            if not match:
                findings.append(_finding("block", "invalid_note_shape", "Note must be '<scope>: [NOTE_CLASS] prose'.", line=number))
                continue
            scope = match.group("scope")
            note_class = match.group("class")
            text = match.group("text").strip()
            note = {"line": number, "scope": scope, "class": note_class, "text": text}
            notes.append(note)

            if scope not in valid_scopes:
                findings.append(_finding("block", "unknown_note_scope", f"Unknown note scope: {scope}", line=number, scope=scope))
            if note_class not in NOTE_CLASSES:
                findings.append(_finding("block", "unknown_note_class", f"Unknown note class: {note_class}", line=number, scope=scope))
                continue

            if any(re.search(pattern, text, re.IGNORECASE) for pattern in STUB_PATTERNS):
                findings.append(_finding("block", "semantic_stub", "Note is an implementation placeholder rather than a generation requirement.", line=number, scope=scope))

            addresses = [item.group("address") for item in ADDRESS_RE.finditer(text)]
            expected_prefix = REFERENCE_CLASS_PREFIX.get(note_class)
            if expected_prefix is not None:
                matching = [address for address in addresses if address.startswith(expected_prefix + ".")]
                if not matching:
                    findings.append(_finding("block", "missing_required_reference", f"[{note_class}] requires an '= {expected_prefix}.*' reference.", line=number, scope=scope))
            for address in addresses:
                if not _address_resolves(address, known_addresses):
                    findings.append(_finding("block", "unresolved_structured_reference", f"Structured reference does not resolve: {address}", line=number, scope=scope))

    findings.extend(
        _table_access_findings(notes, _load_provider_tables(project), contract_scopes)
    )

    by_scope: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for note in notes:
        by_scope[note["scope"]].append(note)

    # Every State 6 callable must be either constrained by at least one State 7
    # note or be provably owned by deterministic assembly. This prevents a new
    # callable from silently reaching the LLM with only a signature and therefore
    # admitting a trivial/placeholder implementation.
    for scope in sorted(contract_scopes - deterministic_scopes):
        if scope not in by_scope:
            findings.append(_finding(
                "block",
                "missing_callable_note",
                f"State 6 callable {scope} has no State 7 note and is not deterministically implemented.",
                scope=scope,
            ))

    for scope, scoped_notes in sorted(by_scope.items()):
        known_classes = [note["class"] for note in scoped_notes if note["class"] in NOTE_CLASSES]
        counts = Counter(known_classes)
        for singleton in SINGLETON_CLASSES:
            if counts[singleton] > 1:
                findings.append(_finding("review", "duplicate_singleton_class", f"{scope} has {counts[singleton]} [{singleton}] notes; reconcile the competing outcome descriptions.", scope=scope))
        present = set(known_classes)
        for pair, reason in SUSPICIOUS_CLASS_PAIRS.items():
            if pair <= present:
                findings.append(_finding("review", "suspicious_note_class_pair", f"{scope} combines {sorted(pair)} ({reason}); make their precedence/conditions explicit before handoff.", scope=scope))

    seen_text: dict[tuple[str, str, str], int] = {}
    for note in notes:
        key = (note["scope"], note["class"], re.sub(r"\s+", " ", note["text"].casefold()).strip())
        previous = seen_text.get(key)
        if previous is not None:
            findings.append(_finding("review", "duplicate_note", f"Duplicate note text; first occurrence is line {previous}.", line=note["line"], scope=note["scope"]))
        else:
            seen_text[key] = note["line"]

    # the fence: a note that needs review is an undecided note; it blocks
    for item in findings:
        if item.get("severity") == "review":
            item["severity"] = "block"
            item["raised_from"] = "review"
        if item.get("severity") == "block" and "hint" not in item:
            item["hint"] = fence.hint_for(item.get("code"), item.get("message"))
    blocks = sum(item["severity"] == "block" for item in findings)
    reviews = 0
    return {
        "schema_version": "spec_workbench_state7_notes_gate.v1",
        "project_root": project.resolve().name,
        "summary": {
            "notes": len(notes),
            "contract_callables": len(contract_scopes),
            "deterministic_callables": len(deterministic_scopes & contract_scopes),
            "blocks": blocks,
            "reviews": reviews,
            "handoff_ready": blocks == 0 and reviews == 0,
        },
        "notes": notes,
        "deterministic_callables": sorted(deterministic_scopes & contract_scopes),
        "findings": findings,
    }


def handoff(project: Path) -> dict[str, Any]:
    report = coverage(project)
    return {
        "schema_version": "spec_workbench_state7_notes_handoff.v1",
        "project_root": report["project_root"],
        "ready": report["summary"]["handoff_ready"],
        "summary": report["summary"],
        "findings": report["findings"],
    }
