"""Candidates: project symbols a scope may use (IMPORTS_WORKBENCH.md §5).

No candidate enters the table without the author's decision and none is
dropped: a symbol named only in a negative clause is still a candidate, marked
``negative``. The weak sources (a field name, a union variant) are the noisy
ones of the §2 measurement; the gate accepts them only on a cited note or on
the code.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable

from imports_workbench.case import IDENTIFIER, Case, Scope
from imports_workbench.model import CANDIDATE_STRENGTH, EVIDENCE, STRONG, STRUCTURAL, WEAK

# Words that make a clause negative. A symbol is an identifier token, so the
# WITHOUT inside SANDBOX_TRAPPED_WITHOUT_ARGUMENT is never one of them.
NEGATIVE_WORDS = frozenset({"never", "without", "not", "no", "nor", "cannot", "none", "nothing", "neither"})
_CLAUSE_END = re.compile(r";|\.(?=\s|$)")
_FIELD_DEPTH = 3
_RANK = {STRUCTURAL: 0, STRONG: 1, EVIDENCE: 2, WEAK: 3}


@dataclass
class Candidate:
    symbol: str
    provider: str
    sources: set[str] = field(default_factory=set)
    evidence: list[str] = field(default_factory=list)
    negative: bool = False

    @property
    def key(self) -> tuple[str, str]:
        return self.symbol, self.provider

    @property
    def strength(self) -> str:
        return min((CANDIDATE_STRENGTH[s] for s in self.sources), key=_RANK.__getitem__)

    @property
    def weak_only(self) -> bool:
        return all(CANDIDATE_STRENGTH[s] == WEAK for s in self.sources)

    def as_json(self) -> dict[str, Any]:
        row: dict[str, Any] = {"symbol": self.symbol, "provider": self.provider,
                               "candidates": sorted(self.sources), "strength": self.strength,
                               "evidence": list(dict.fromkeys(self.evidence))}
        if self.negative:
            row["negative"] = True
        return row


class _Collector:
    def __init__(self, case: Case, scope: Scope) -> None:
        self.case, self.scope = case, scope
        own = set(case.exports.get(scope.module, ())) | set(case.module_functions.get(scope.module, ()))
        self.catalog = {symbol: [p for p in providers if p != scope.module]
                        for symbol, providers in case.catalog().items() if symbol not in own}
        self.found: dict[tuple[str, str], Candidate] = {}

    def add(self, symbol: str, source: str, evidence: str, negative: bool = False) -> None:
        for provider in self.catalog.get(symbol, ()):
            candidate = self.found.setdefault((symbol, provider), Candidate(symbol, provider))
            candidate.sources.add(source)
            candidate.evidence.append(evidence)
            # a candidate is negative only while every mention of it is
            candidate.negative = negative if len(candidate.evidence) == 1 else candidate.negative and negative


def _identifiers(text: str) -> list[str]:
    return IDENTIFIER.findall(text or "")


def _clauses(text: str) -> Iterable[str]:
    return (part for part in _CLAUSE_END.split(text) if part.strip())


# A negation governs a symbol only inside its own part of the clause: commas and
# subordinators start a new part ("MUST raise X when the ref does not exist").
_PART_BREAK = re.compile(r",|\b(?:when|if|unless|where|whose|that|which|while|because|after|before|until)\b",
                         re.IGNORECASE)
_NEGATED_AFTER = re.compile(r"^\s*(?:(?:is|are|was|were|must|may|shall|does|do|can|will)\s+)?(?:not|never)\b",
                            re.IGNORECASE)


def _negative(clause: str, start: int, end: int) -> bool:
    """The symbol at clause[start:end] is negated: a negative word before it in its own
    part of the clause ("never calls X", "MUST NOT read X", "without X"), or right after
    it ("X is not called")."""
    before = _PART_BREAK.split(clause[:start])[-1]
    if any(token.lower() in NEGATIVE_WORDS for token in _identifiers(before)):
        return True
    return bool(_NEGATED_AFTER.match(_PART_BREAK.split(clause[end:])[0]))


def _model_types(case: Case, annotation: str) -> list[str]:
    return [name for name in dict.fromkeys(_identifiers(annotation)) if name in case.models]


def _reachable_fields(case: Case, roots: Iterable[str]) -> list[tuple[str, str, str]]:
    """(model, field, model type of the field) reachable from the roots, up to three levels."""
    found: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    frontier = [(root, 0) for root in roots]
    while frontier:
        name, level = frontier.pop(0)
        if name in seen or level >= _FIELD_DEPTH:
            continue
        seen.add(name)
        fields = (case.models.get(name) or {}).get("fields")
        for field_name, annotation in (fields.items() if isinstance(fields, dict) else ()):
            for target in _model_types(case, str(annotation)):
                found.append((name, str(field_name), target))
                frontier.append((target, level + 1))
    return found


def scope_candidates(case: Case, scope: Scope, accepted: Iterable[dict[str, Any]] = ()) -> dict[tuple[str, str], Candidate]:
    """Every candidate of one scope; ``accepted`` are its decided uses (they extend the reach)."""
    collector = _Collector(case, scope)
    accepted = [row for row in accepted if isinstance(row, dict) and isinstance(row.get("symbol"), str)]

    for symbol in _identifiers(scope.signature):
        collector.add(symbol, "contract", "contract")
    # a callee's signature types are imported structurally with it (SPEC_STANDARD §7)
    for row in accepted:
        callee = case.contracts.get(row["symbol"])
        if callee is not None:
            for symbol in _identifiers(callee):
                collector.add(symbol, "contract", f"contract:{row['symbol']}")

    for address, note in scope.notes:
        for clause in _clauses(note.text):
            for match in IDENTIFIER.finditer(clause):
                symbol = match.group(0)
                if symbol not in collector.catalog:
                    continue
                called = clause[match.end():].lstrip().startswith("(")
                collector.add(symbol, "note_call" if called else "note_mention", address,
                              _negative(clause, match.start(), match.end()))

    words = set(_identifiers(scope.text)) | set(_identifiers(scope.signature))
    roots = list(dict.fromkeys(
        _model_types(case, scope.signature)
        + [row["symbol"] for row in accepted if row["symbol"] in case.models]))
    for model, field_name, target in _reachable_fields(case, roots):
        if field_name in words:
            collector.add(target, "field_name", f"field:{model}.{field_name}")
    for root in roots:
        declaration = case.models.get(root) or {}
        if declaration.get("kind") == "discriminated_union":
            for variant in declaration.get("variants") or ():
                if isinstance(variant, str):
                    collector.add(variant, "variant", f"variant:{root}")
    return collector.found


def code_candidates(case: Case, module: str, code_imports: dict[str, list[str]]) -> dict[tuple[str, str], Candidate]:
    """Project symbols the module's accepted code names, as module-level evidence."""
    found: dict[tuple[str, str], Candidate] = {}
    for provider, symbols in sorted((code_imports or {}).items()):
        for symbol in symbols:
            candidate = found.setdefault((symbol, provider), Candidate(symbol, provider))
            candidate.sources.add("code_used")
            candidate.evidence.append("code")
    return found
