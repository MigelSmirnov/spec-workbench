"""Note data addresses of a standard_version 3 case, judged by the Factory.

SPEC_STANDARD §15.3 asks for one resolver, and the owner placed it in the
Factory (Data Closure contract, decision Q5): `tools/spec_address.py` of the
Factory checkout decides legality, and this module only feeds it. The input
is the specification the authored sources project to, in memory, with the
notes the gate parsed from `80_notes.md` in place of its `notes`, so the answer is
about the texts being written, not about the last assembly. The Factory's
answer carries the note's position; this module maps it back to the line.

From v3 (code-factory `NOTE_ADDRESSES_CLOSED_MIN_VERSION`, held equal by
admission FA020) a note addresses data only as `= models.X` and `the imported
X constant`. A v2 case keeps the notes gate's own address checks.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from questions_workbench import documents as question_documents

# Mirrors code-factory tools/spec_version.py; admission FA020 blocks a target
# Factory that does not name the same version.
NOTE_ADDRESSES_CLOSED_MIN_VERSION = 3
# Closed from that version: no legal address is left for them (§15.3.1).
CLOSED_NOTE_CLASSES = frozenset({"CONFIG_REFERENCE", "RULE_REFERENCE"})
RESOLVER = "tools/spec_address.py"


def closes_note_addresses(project: Path) -> bool:
    """True when the case's declared standard_version closes note addresses."""
    path = project / "global_spec.json"
    try:
        version = json.loads(path.read_text(encoding="utf-8")).get("standard_version")
    except (OSError, ValueError, AttributeError):
        return False  # the language gate reports a missing or broken declaration
    return type(version) is int and version >= NOTE_ADDRESSES_CLOSED_MIN_VERSION


class ResolverUnavailable(Exception):
    """The Factory's resolver could not answer: no checkout, or no report."""


def run_resolver(spec: dict[str, Any], addresses: list[str] | None = None,
                 factory_root: Path | None = None) -> dict[str, Any]:
    """The Factory resolver's report on ``spec``: every note address, or only
    ``addresses`` (written as in a note) when given."""
    factory = factory_root or question_documents.factory_root()
    if factory is None or not (factory / RESOLVER).is_file():
        raise ResolverUnavailable(
            f"No Factory checkout with {RESOLVER} (SPEC_WORKBENCH_FACTORY_ROOT or sibling code_factory)."
        )
    args = [sys.executable, RESOLVER, "--spec", "-"]
    for address in addresses or []:
        args += ["--address", address]
    run = subprocess.run(
        args, cwd=factory, input=json.dumps(spec, ensure_ascii=False),
        text=True, capture_output=True, check=False,
    )
    try:
        report = json.loads(run.stdout)
        if not isinstance(report.get("addresses"), list):
            raise ValueError("no addresses")
    except (ValueError, AttributeError):
        tail = (run.stdout + run.stderr).strip().splitlines()
        raise ResolverUnavailable(
            f"{RESOLVER} gave no report (exit {run.returncode}): {tail[-1] if tail else 'no output'}"
        ) from None
    return report


def _finding(code: str, message: str, *, line: int | None = None, scope: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"severity": "block", "code": code, "message": message}
    if line is not None:
        result["line"] = line
    if scope is not None:
        result["scope"] = scope
    return result


def findings(project: Path, notes: list[dict[str, Any]], factory_root: Path | None = None) -> list[dict[str, Any]]:
    """Blocking findings for the data addresses of ``notes`` (the notes gate's
    parsed records: ``line``, ``scope``, ``class``, ``text``)."""
    result = [
        _finding(
            "note_class_closed",
            f"[{note['class']}] is not a note class from standard_version {NOTE_ADDRESSES_CLOSED_MIN_VERSION}: "
            "a note addresses no rules or config node. SPEC_STANDARD 15.3.1: name the symbol the backend "
            "emits, the imported data-provider constant, or the settings field.",
            line=note["line"], scope=note["scope"],
        )
        for note in notes
        if note["class"] in CLOSED_NOTE_CLASSES
    ]
    factory = factory_root or question_documents.factory_root()
    if factory is None or not (factory / RESOLVER).is_file():
        result.append(_finding(
            "note_address_resolver_unavailable",
            f"No Factory checkout with {RESOLVER} (SPEC_WORKBENCH_FACTORY_ROOT or sibling code_factory): "
            "the note addresses of a standard_version 3 case cannot be judged.",
        ))
        return result
    try:
        from spec_projection_workbench import projected_spec

        spec = projected_spec(project)
    except Exception as exc:  # noqa: BLE001 - any projection failure leaves the addresses unjudged
        result.append(_finding(
            "note_address_projection_failed",
            f"The authored sources do not project, so the note addresses cannot be judged: {exc}",
        ))
        return result
    spec["notes"] = [f"{note['scope']}: [{note['class']}] {note['text']}" for note in notes]
    try:
        addresses = run_resolver(spec, factory_root=factory)["addresses"]
    except ResolverUnavailable as exc:
        result.append(_finding("note_address_resolver_failed", str(exc)))
        return result
    for item in addresses:
        if item.get("status") == "legal":
            continue
        note = notes[item["note_index"]]
        result.append(_finding(
            str(item.get("code")),
            f"{item.get('address')}: {item.get('message')}",
            line=note["line"], scope=note["scope"],
        ))
    return result
