from __future__ import annotations

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
    # State 3 canonical module headings contain `module:<name>`.
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
    return result


def _address_resolves(address: str, known: set[str]) -> bool:
    if address in known:
        return True
    # A placement may represent a structured parent used as a whole. A deeper
    # address is valid only when the known placement itself is that parent.
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

    by_scope: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for note in notes:
        by_scope[note["scope"]].append(note)

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

    blocks = sum(item["severity"] == "block" for item in findings)
    reviews = sum(item["severity"] == "review" for item in findings)
    return {
        "schema_version": "spec_workbench_state7_notes_gate.v1",
        "project_root": project.resolve().name,
        "summary": {
            "notes": len(notes),
            "blocks": blocks,
            "reviews": reviews,
            "handoff_ready": blocks == 0 and reviews == 0,
        },
        "notes": notes,
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
