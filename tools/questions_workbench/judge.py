"""Judge the repeated topics of a round, and check the judge mechanically.

Repetition says that reviews agree a question exists, not that it matters.
The judge sorts each repeated topic into a kind; only a contradiction or a gap
with an observable consequence keeps a state open. Every non-blocking kind
carries evidence the tool can check without trusting the judge: a quote must
appear verbatim in the texts (for `answered_later`, in the later states'
texts the judge searched), a later state must come after this one, a
precedent must be a prior non-blocking judgement whose quotes still stand. A
judgement whose evidence fails counts as blocking.
"""
from __future__ import annotations

from typing import Any

BLOCKING = {"contradiction", "consequential_gap"}
KINDS = BLOCKING | {"answered", "answered_later", "later_state", "indifferent", "preexisting", "judged_before"}


def _norm(text: str) -> str:
    return " ".join(str(text).split())


def _found(quote: str, corpus: str) -> bool:
    quote = _norm(quote)
    return len(quote) >= 12 and quote in corpus


def check(judgement: dict[str, Any] | None, state: int, texts: str, old_texts: str | None,
          later_texts: str | None = None, precedents: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    """The judgement as kept in the round, with `verified` and `blocking`."""
    if not isinstance(judgement, dict):
        return {"kind": None, "verified": False, "blocking": True, "failure": "the judge gave no judgement"}
    kind = judgement.get("kind")
    quotes = [q for q in judgement.get("quotes") or [] if isinstance(q, str) and q.strip()]
    kept = {
        "kind": kind,
        "quotes": quotes,
        "later_state": judgement.get("later_state"),
        "divergence": str(judgement.get("divergence") or ""),
        "why": str(judgement.get("why") or ""),
    }
    corpus = _norm(texts)
    failure = None
    if kind not in KINDS:
        failure = f"unknown kind {kind!r}"
    elif kind == "contradiction":
        if len(quotes) < 2 or not all(_found(q, corpus) for q in quotes):
            failure = "a contradiction needs two quotes found verbatim in the texts"
    elif kind == "consequential_gap":
        if not kept["divergence"].strip():
            failure = "a consequential gap needs the two behaviours and who notices"
    elif kind == "answered":
        if not quotes or not all(_found(q, corpus) for q in quotes):
            failure = "the answering quote is not found verbatim in the texts"
    elif kind == "answered_later":
        if later_texts is None:
            failure = "answered_later is allowed only when the judge was given the later states' texts"
        elif not quotes or not all(_found(q, _norm(later_texts)) for q in quotes):
            failure = "the deciding quote is not found verbatim in the later states' texts"
    elif kind == "judged_before":
        precedent = (precedents or {}).get(str(judgement.get("precedent")))
        if precedent is None:
            failure = "judged_before must name one of the prior judgements offered"
        else:
            kept["precedent"] = precedent
            where = _norm(later_texts) if precedent["kind"] == "answered_later" and later_texts else corpus
            if precedent["kind"] == "answered_later" and later_texts is None:
                failure = "the precedent quotes later states the judge was not given"
            elif not all(_found(q, where) for q in precedent["quotes"]):
                failure = "a passage the precedent quotes is no longer found verbatim"
    elif kind == "later_state":
        later = kept["later_state"]
        if not isinstance(later, int) or isinstance(later, bool) or later <= state:
            failure = f"later_state must be a state after {state}"
    elif kind == "indifferent":
        if not kept["why"].strip():
            failure = "an indifferent topic needs the reason no one acts on the difference"
    elif kind == "preexisting":
        if old_texts is None:
            failure = "preexisting is allowed only for a reopened state (--since)"
        elif not quotes or not all(_found(q, corpus) and _found(q, _norm(old_texts)) for q in quotes):
            failure = "the quoted passage is not found verbatim in both versions"
    kept["verified"] = failure is None
    kept["blocking"] = kind in BLOCKING or failure is not None
    if failure:
        kept["failure"] = failure
    return kept
