"""Lint L2–L5 of the Data Closure contract (§6), without a model.

L1 — every address resolves and is legal — is the Factory's resolver
(`notes_workbench.factory_addresses`). The rules here check that a note
followed §15: a literal with a home is named by its address (L2), every
data signal is covered (L3), an addressed enumeration is not restated (L4),
and prose repeated across modules has not diverged (L5).

The lint gives no verdict "data / not data". A signal it cannot cover is a
reason for a structure request (contract §5), never for an explanation in
the note; a false signal is fixed by narrowing the detector in `tools/`
(decision Q16), never by an exception for a module.

Not a gate yet: the contract becomes one with the writing environment.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from notes_authoring import binding
from notes_authoring.index import SpecIndex
from notes_authoring.signals import Signal, addressed_models, detect, member_order

REPORT_SCHEMA = "spec_workbench_notes_lint.v1"
SHARED_SPAN_WORDS = 10  # M-D1
ORDER_CLAIM_RE = re.compile(r"(?:in this order of|declared order of)\s*=\s*models\.(?P<name>[A-Za-z_][A-Za-z0-9_]*)")
_WORD_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\d+")


def _finding(rule: str, code: str, severity: str, note: dict[str, Any], module: str | None,
             message: str, **evidence: Any) -> dict[str, Any]:
    return {
        "rule": rule, "code": code, "severity": severity,
        "path": note.get("path"), "line": note.get("line"), "scope": note.get("scope"),
        "module": module, "message": message, **evidence,
    }


def _covered(signal: Signal, text: str, index: SpecIndex) -> bool:
    addressed = addressed_models(text)
    if signal.kind == "quoted":
        value = signal.text.strip()
        return index.is_name(value) or any(value in index.enums.get(name, ()) for name in addressed)
    if signal.kind == "list":
        if index.fields_of_one_model(signal.items) is not None:
            return True  # field names of a declared model: shape or sort keys (M-O1)
        return any(set(signal.items) <= set(index.enums.get(name, ())) for name in addressed)
    if signal.kind == "enum_members":
        return signal.enum in addressed
    return False  # number, path, arrow, table, design_reference


def _l2_l3(note: dict[str, Any], module: str | None, index: SpecIndex) -> list[dict[str, Any]]:
    text = note["text"]
    addressed = addressed_models(text)
    out = []
    for signal in detect(text, index.enums, index.names(), index.field_names()):
        if signal.kind in ("number", "quoted"):
            value = signal.text.strip()
            own_member = any(value in index.enums.get(name, ()) for name in addressed)
            homes = [] if index.is_name(value) or own_member else index.homes(value, reaching_code=True)
            if homes:
                out.append(_finding(
                    "L2", "literal_with_home", "block", note, module,
                    f"{value!r} equals the declared value of {', '.join(homes)}: if the note means that "
                    "value, name its home; if the match is chance, the literal is data without a home (L3).",
                    signal=signal.kind, value=value, homes=homes,
                ))
                continue
        if not _covered(signal, text, index):
            out.append(_finding(
                "L3", "uncovered_data_signal", "block", note, module,
                f"{signal.kind} {signal.text!r} is not covered by an address, a declared name or an "
                "addressed enumeration.",
                signal=signal.kind, value=signal.text, items=list(signal.items), enum=signal.enum,
            ))
    return out


# Between two members of a restated list (F3) stand only separators: `open, then
# business_confidential, then personal_data`. A condition between them —
# `timeout when the deadline passed; resource_exhausted when …` — is the
# algorithm form F4, which research Q9 §2.2 classes as prose.
_PURE_GAP_RE = re.compile(r"[\s,;:()\-–—]*(?:(?:then|and|or)[\s,;:()\-–—]*)*")


def _restated_without_conditions(text: str, members: list[str]) -> bool:
    positions = []
    for member in members:
        m = re.search(rf"(?<![\w.]){re.escape(member)}(?![\w])", text)
        if m is None:
            return False
        positions.append((m.start(), m.end()))
    positions.sort()
    return all(_PURE_GAP_RE.fullmatch(text[a_end:b_start])
               for (_, a_end), (b_start, _) in zip(positions, positions[1:]))


def _l4(note: dict[str, Any], module: str | None, index: SpecIndex) -> list[dict[str, Any]]:
    text = note["text"]
    out = []
    for name in sorted(addressed_models(text)):
        members = index.enums.get(name)
        if not members or len(members) < 2:
            continue
        present = member_order(text, members)
        if len(present) == len(members) and _restated_without_conditions(text, present):
            out.append(_finding(
                "L4", "addressed_enumeration_restated", "block", note, module,
                f"every member of = models.{name} is restated next to its address with no condition "
                "between them (M-E2, form F3).",
                enum=name, members=present,
            ))
    for claim in ORDER_CLAIM_RE.finditer(text):
        name = claim.group("name")
        members = index.enums.get(name)
        if not members:
            continue
        present = member_order(text[claim.end():], members)
        declared = [member for member in members if member in present]
        if present != declared:
            out.append(_finding(
                "L4", "claimed_order_differs", "block", note, module,
                f"the note claims the declared order of = models.{name} and lists its members in "
                "another order (M-E3).",
                enum=name, listed=present, declared=declared,
            ))
    return out


def _sentences(text: str) -> list[str]:
    return re.split(r"(?<=[.;])\s+", text)


def _words(text: str) -> str:
    return " ".join(w.lower() for w in _WORD_RE.findall(text))


def _sentence_with(text: str, gram: tuple[str, ...]) -> str | None:
    words = " ".join(gram)
    return next((sentence for sentence in _sentences(text) if words in _words(sentence)), None)


def _l5(by_module: dict[str, list[dict[str, Any]]], index: SpecIndex) -> list[dict[str, Any]]:
    """M-D1: a ≥10-word span shared by notes of different modules (report,
    on both notes). M-D2: in a sentence the copies share, a list differs from
    its counterpart — the list at the same position of the other copy (block,
    on both notes)."""
    grams: dict[tuple[str, ...], list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    for module, notes in by_module.items():
        for note in notes:
            words = [w.lower() for w in _WORD_RE.findall(note["text"])]
            seen = set()
            for i in range(len(words) - SHARED_SPAN_WORDS + 1):
                gram = tuple(words[i:i + SHARED_SPAN_WORDS])
                if gram not in seen:
                    seen.add(gram)
                    grams[gram].append((module, note))
    pairs: dict[tuple[int, int], dict[str, Any]] = {}
    for gram, holders in grams.items():
        for i, (module_a, note_a) in enumerate(holders):
            for module_b, note_b in holders[i + 1:]:
                if module_a == module_b:
                    continue
                key = tuple(sorted((id(note_a), id(note_b))))
                pair = pairs.setdefault(key, {"a": (module_a, note_a), "b": (module_b, note_b), "grams": []})
                pair["grams"].append(gram)
    names = index.names()
    out = []
    for pair in pairs.values():
        (module_a, note_a), (module_b, note_b) = pair["a"], pair["b"]
        sides = (((module_a, note_a), (module_b, note_b)), ((module_b, note_b), (module_a, note_a)))
        for (module, note), (other_module, other_note) in sides:
            other = f"{other_note.get('path')}:{other_note.get('line')} ({other_module})"
            out.append(_finding(
                "L5", "shared_prose", "report", note, module,
                f"shares a {SHARED_SPAN_WORDS}-word span with {other}; name the other module's function "
                "instead of restating its rule (M-D4).",
                span=" ".join(pair["grams"][0]), other=other,
            ))
        compared = set()
        diverged: list[tuple[tuple[str, ...], tuple[str, ...]]] = []
        for gram in pair["grams"]:
            sentence_a, sentence_b = _sentence_with(note_a["text"], gram), _sentence_with(note_b["text"], gram)
            if sentence_a is None or sentence_b is None or (sentence_a, sentence_b) in compared:
                continue
            compared.add((sentence_a, sentence_b))
            lists_a = [s.items for s in detect(sentence_a, names=names) if s.kind == "list"]
            lists_b = [s.items for s in detect(sentence_b, names=names) if s.kind == "list"]
            for items_a, items_b in zip(lists_a, lists_b):
                common = set(items_a) & set(items_b)
                if items_a != items_b and len(common) * 2 >= len(set(items_a) | set(items_b)):
                    diverged.append((items_a, items_b))
        for items_a, items_b in diverged:
            for (module, note), (other_module, other_note), mine, theirs in (
                ((module_a, note_a), (module_b, note_b), items_a, items_b),
                ((module_b, note_b), (module_a, note_a), items_b, items_a),
            ):
                other = f"{other_note.get('path')}:{other_note.get('line')} ({other_module})"
                out.append(_finding(
                    "L5", "diverged_copies", "block", note, module,
                    f"a list of this note and its copy in {other} share a span and differ (M-D2).",
                    items=list(mine), other_items=list(theirs), other=other,
                ))
    return out


def lint(notes: list[dict[str, Any]], spec: dict[str, Any]) -> dict[str, Any]:
    """Lint ``notes`` (records with ``path``, ``line``, ``scope``, ``class``,
    ``text``) against the declared surface of ``spec``."""
    index = SpecIndex.build(spec)
    by_module, unbound = binding.bind(notes, spec)
    findings: list[dict[str, Any]] = []
    for note in unbound:
        findings.append(_finding("M6", "note_unbound", "block", note, None,
                                 f"scope {note['scope']!r} belongs to no module (DC-F2)."))
    for module, module_notes in sorted(by_module.items()):
        for note in module_notes:
            findings.extend(_l2_l3(note, module, index))
            findings.extend(_l4(note, module, index))
    findings.extend(_l5(by_module, index))
    modules: dict[str, dict[str, int]] = {}
    for module, module_notes in by_module.items():
        own = [f for f in findings if f["module"] == module]
        modules[module] = {
            "notes": len(module_notes),
            "blocks": sum(f["severity"] == "block" for f in own),
            "reports": sum(f["severity"] == "report" for f in own),
        }
    by_rule: dict[str, int] = defaultdict(int)
    for f in findings:
        by_rule[f"{f['rule']}:{f['code']}"] += 1
    return {
        "schema_version": REPORT_SCHEMA,
        "summary": {
            "notes": len(notes),
            "modules": len(by_module),
            "blocks": sum(f["severity"] == "block" for f in findings),
            "reports": sum(f["severity"] == "report" for f in findings),
            "by_rule": dict(sorted(by_rule.items())),
        },
        "modules": dict(sorted(modules.items())),
        "findings": findings,
    }


def lint_project(project: Path) -> dict[str, Any]:
    """Lint every `80_notes*.md` of a case (decision Q12) against the
    in-memory projection of its authored sources (decision Q1)."""
    from notes_workbench import language
    from spec_projection_workbench import projected_spec

    return lint(language.authored_notes(project), projected_spec(project))
