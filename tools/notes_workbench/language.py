"""Report State 7 notes that the Factory will not accept as generation evidence.

The Workbench notes gate proves that every callable *has* a note. The Factory's
own pre-generation gate additionally requires that at least one of those notes
*states a requirement*: it must be scoped to the bare callable name, carry a
note class that establishes implementation semantics, and contain a positive
modal (MUST / SHOULD / MAY). A note written in the imperative mood — "Return the
observed state." — satisfies the Workbench and is rejected by the Factory.

That divergence is invisible until Route B stops before its first provider call,
after a specification has already been exported and accepted. This module makes
it visible in the Workbench, against the same assembled specification the
Factory consumes, and points at the Markdown line where each note is authored.

It also cross-checks a defect the coverage rules cannot see. A note that names a
runtime dependency — "obtain the exact X bound to request.app.state.y and pass it
to z" — encodes a binding that the assembled contracts already own. When the
named type disagrees with the parameter type z actually requires, the note is
counted as coverage and still directs generation to read the wrong attribute.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from notes_workbench.note_standard import NOTE_CLASSES


SCHEMA_VERSION = "spec_workbench_notes_language.v1"

# Mirrors tools/spec_underspec_gate.py in the Factory. A note class carries
# implementation semantics unless it only records evidence about, or a fallback
# from, behavior established elsewhere.
NON_SEMANTIC_CLASSES = frozenset({"TEST_EVIDENCE", "FALLBACK"})

# Replicated verbatim from the Factory gate: a scope is one identifier with at
# most one dot, and coverage requires the scope to equal the callable name, so a
# class-qualified note never covers the bare function.
SCOPE_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*:")
MARKER_RE = re.compile(r"\[([A-Z_]+)\]")
POSITIVE_MODAL_RE = re.compile(r"\b(?:MUST|SHOULD|MAY)\b(?!\s+NOT\b)", re.IGNORECASE)

# The two authored note shapes. `80_notes.md` writes one note per line; the
# modular `80_notes_*.md` files write list items whose prose wraps.
INLINE_NOTE_RE = re.compile(r"^(?P<scope>[A-Za-z_][A-Za-z0-9_.]*):\s*\[(?P<class>[A-Z_]+)\]\s*(?P<text>.+?)\s*$")
LIST_NOTE_RE = re.compile(r"^-\s*(?P<scope>[A-Za-z_][A-Za-z0-9_.]*)\s*\[(?P<class>[A-Z_]+)\]:\s*(?P<text>.*?)\s*$")

APP_STATE_RE = re.compile(r"request\.app\.state\.([A-Za-z_][A-Za-z0-9_]*)")
IDENTIFIER_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\b")

_OPENERS = "([{"
_CLOSERS = ")]}"


def semantic_classes() -> tuple[frozenset[str], list[str]]:
    """Return the classes that establish semantics, plus any table drift."""
    unknown = sorted(NON_SEMANTIC_CLASSES - set(NOTE_CLASSES))
    return frozenset(NOTE_CLASSES) - NON_SEMANTIC_CLASSES, unknown


def _finding(severity: str, code: str, message: str, **fields: Any) -> dict[str, Any]:
    return {"severity": severity, "code": code, "message": message, **fields}


def note_scope(note: str) -> str | None:
    match = SCOPE_RE.match(note)
    return match.group(1) if match else None


def note_markers(note: str) -> set[str]:
    return {match.group(1) for match in MARKER_RE.finditer(note)}


def is_positive(note: str) -> bool:
    """A note states a requirement only through an affirmative modal clause."""
    return POSITIVE_MODAL_RE.search(note) is not None


def split_top_level(text: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for char in text:
        if char in _OPENERS:
            depth += 1
        elif char in _CLOSERS:
            depth -= 1
        if char == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    tail = "".join(current).strip()
    if tail:
        parts.append(tail)
    return [part for part in parts if part]


def signature_parameters(signature: str) -> list[tuple[str, str]]:
    """Return ordered ``(name, annotation)`` pairs of a contract signature."""
    text = signature.strip()
    if not text.startswith("("):
        return []
    depth = 0
    close = -1
    for index, char in enumerate(text):
        if char in _OPENERS:
            depth += 1
        elif char in _CLOSERS:
            depth -= 1
            if depth == 0:
                close = index
                break
    if close == -1:
        return []
    result: list[tuple[str, str]] = []
    for raw in split_top_level(text[1:close]):
        head, _, _default = raw.partition("=")
        name, _, annotation = head.partition(":")
        result.append((name.strip(), annotation.strip()))
    return result


def is_function_contract(name: str, signature: object) -> bool:
    if not isinstance(name, str) or not isinstance(signature, str):
        return False
    return "." not in name and not name.isupper() and signature.strip().startswith("(")


def load_assembled_spec(project: Path) -> dict[str, Any]:
    path = project / "global_spec.json"
    if not path.is_file():
        raise FileNotFoundError(f"assembled specification not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"assembled specification must be an object: {path}")
    return payload


def factory_coverage(spec: dict[str, Any]) -> list[dict[str, Any]]:
    """Findings for callables the Factory will refuse to generate."""
    required, _drift = semantic_classes()
    module_functions = spec.get("module_functions")
    contracts = spec.get("contracts")
    notes = [note for note in spec.get("notes") or [] if isinstance(note, str)]
    if not isinstance(module_functions, dict) or not isinstance(contracts, dict):
        return [_finding(
            "block",
            "assembled_spec_incomplete",
            "Assembled specification has no module_functions/contracts to evaluate.",
        )]

    findings: list[dict[str, Any]] = []
    for module in sorted(module_functions):
        owned = module_functions[module]
        if not isinstance(owned, list):
            continue
        for name in sorted(item for item in owned if isinstance(item, str)):
            signature = contracts.get(name)
            if not is_function_contract(name, signature):
                continue
            scoped = [note for note in notes if note_scope(note) == name]
            covering = [
                note for note in scoped
                if note_markers(note) & required and is_positive(note)
            ]
            if covering:
                continue
            marked = [note for note in scoped if note_markers(note) & required]
            if not scoped:
                reason = "no note is scoped to this callable"
            elif not marked:
                reason = "scoped notes carry no semantic note class"
            else:
                reason = "scoped semantic notes state no positive modal requirement"
            findings.append(_finding(
                "block",
                "contract_without_positive_note",
                f"{module}.{name} has a contract the Factory will not generate: {reason}.",
                module=module,
                scope=name,
                contract=signature,
                scoped_notes=len(scoped),
                semantic_notes=len(marked),
                reason=reason,
            ))
    return findings


def _iter_authored_notes(project: Path):
    """Yield authored notes from every State 7 file, in both authored shapes."""
    for path in sorted(project.glob("80_notes*.md")):
        lines = path.read_text(encoding="utf-8").splitlines()
        pending: dict[str, Any] | None = None
        for number, raw in enumerate(lines, start=1):
            stripped = raw.strip()
            list_match = LIST_NOTE_RE.match(stripped)
            if list_match:
                if pending is not None:
                    yield pending
                pending = {
                    "path": path.name,
                    "line": number,
                    "scope": list_match.group("scope"),
                    "class": list_match.group("class"),
                    "text": list_match.group("text"),
                }
                continue
            if pending is not None:
                # Wrapped prose continues the previous list item; a modal may
                # only appear on the continuation line.
                if stripped and not stripped.startswith(("-", "#")) and raw.startswith((" ", "\t")):
                    pending["text"] = f"{pending['text']} {stripped}".strip()
                    continue
                yield pending
                pending = None
            inline_match = INLINE_NOTE_RE.match(stripped)
            if inline_match:
                yield {
                    "path": path.name,
                    "line": number,
                    "scope": inline_match.group("scope"),
                    "class": inline_match.group("class"),
                    "text": inline_match.group("text"),
                }
        if pending is not None:
            yield pending


def authored_repair_sites(project: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Findings at the Markdown line where a note must be reworded."""
    required, _drift = semantic_classes()
    findings: list[dict[str, Any]] = []
    files: set[str] = set()
    for note in _iter_authored_notes(project):
        files.add(note["path"])
        if note["class"] not in required:
            continue
        if is_positive(note["text"]):
            continue
        findings.append(_finding(
            "warn",
            "note_without_positive_modal",
            f"{note['path']}:{note['line']} states {note['scope']} in the imperative mood; "
            "the Factory counts a note as evidence only with MUST, SHOULD, or MAY.",
            path=note["path"],
            line=note["line"],
            scope=note["scope"],
            note_class=note["class"],
            text=note["text"],
        ))
    return findings, sorted(files)


def dependency_bindings(spec: dict[str, Any]) -> list[dict[str, Any]]:
    """Findings where a note's named runtime dependency contradicts contracts."""
    contracts = spec.get("contracts")
    notes = [note for note in spec.get("notes") or [] if isinstance(note, str)]
    if not isinstance(contracts, dict):
        return []
    composition = contracts.get("create_app")
    if not isinstance(composition, str):
        return []

    bound_types = {
        name: annotation
        for name, annotation in signature_parameters(composition)
        if name and annotation
    }
    if not bound_types:
        return []
    service_types = set(bound_types.values())

    findings: list[dict[str, Any]] = []
    for note in notes:
        scope = note_scope(note)
        attributes = sorted(set(APP_STATE_RE.findall(note)))
        if not attributes:
            continue
        if len(attributes) > 1:
            findings.append(_finding(
                "warn",
                "ambiguous_dependency_binding",
                f"{scope} names several request.app.state attributes in one note; "
                "the required binding cannot be checked against contracts.",
                scope=scope,
                attributes=attributes,
                text=note,
            ))
            continue
        attribute = attributes[0]
        if attribute not in bound_types:
            findings.append(_finding(
                "block",
                "unknown_app_state_attribute",
                f"{scope} reads request.app.state.{attribute}, which create_app never binds.",
                scope=scope,
                attribute=attribute,
                bound_attributes=sorted(bound_types),
                text=note,
            ))
            continue
        bound_type = bound_types[attribute]

        for identifier in sorted(set(IDENTIFIER_RE.findall(note))):
            if identifier == scope:
                continue
            signature = contracts.get(identifier)
            if not is_function_contract(identifier, signature):
                continue
            parameters = signature_parameters(signature)
            if not parameters:
                continue
            required_type = parameters[0][1]
            if required_type not in service_types or required_type == bound_type:
                continue
            findings.append(_finding(
                "block",
                "dependency_binding_mismatch",
                f"{scope} is told to pass {bound_type} from request.app.state.{attribute} "
                f"to {identifier}, whose contract requires {required_type}.",
                scope=scope,
                attribute=attribute,
                bound_type=bound_type,
                delegate=identifier,
                required_type=required_type,
                text=note,
            ))
    return findings


def report(project: Path) -> dict[str, Any]:
    """Full notes-language report for one design case."""
    spec = load_assembled_spec(project)
    _required, drift = semantic_classes()

    findings = factory_coverage(spec)
    repair_sites, note_files = authored_repair_sites(project)
    findings.extend(repair_sites)
    findings.extend(dependency_bindings(spec))
    if drift:
        findings.append(_finding(
            "warn",
            "note_class_table_drift",
            "Note classes excluded from semantics are absent from the canonical table: "
            + ", ".join(drift),
            classes=drift,
        ))

    blocking = [item for item in findings if item["severity"] == "block"]
    counts: dict[str, int] = {}
    for item in findings:
        counts[item["code"]] = counts.get(item["code"], 0) + 1

    return {
        "schema_version": SCHEMA_VERSION,
        "project": project.name,
        "status": "block" if blocking else "pass",
        "summary": {
            "findings": len(findings),
            "blocking": len(blocking),
            "by_code": counts,
            "note_files_scanned": note_files,
            # The Workbench coverage gate reads 80_notes.md alone, so notes
            # authored in the modular files are otherwise never gated here.
            "note_files_ungated_by_coverage": [
                name for name in note_files if name != "80_notes.md"
            ],
        },
        "findings": findings,
    }
