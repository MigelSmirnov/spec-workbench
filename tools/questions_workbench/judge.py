"""Judge the repeated topics of a round, and check the judge mechanically.

Repetition says that reviews agree a question exists, not that it matters.
The judge sorts each repeated topic into a kind; only a contradiction or a gap
with an observable consequence keeps a state open. Every non-blocking kind
carries evidence the tool can check without trusting the judge: a quote must
appear verbatim in the texts (for `answered_later`, in the later states'
texts the judge searched), a later state must come after this one, a
precedent must be a prior non-blocking judgement whose quotes still stand. A
judgement whose evidence fails counts as blocking.

A consequential gap that quotes no passage is about something the texts up to
this state do not speak to at all — sandbox streams, a listener binding, a
size limit. Such a gap is an implementation detail: it does not hold a design
state open, it is recorded as deferred and must be answered in the contracts
(State 6) or the notes (State 7). A gap that quotes a passage still blocks, and
its quotes are checked like any other. A gap that quotes none of this state's
own documents — only earlier states, closed by their own rounds, or the later
texts the judge searched (a note, a contract) — is a gap of those texts, not of
this state: it does not block, and is kept with the states it belongs to. A
contradiction blocks wherever its passages are.

A blocking kind needs a witness (owner, 2026-11-01, after the Registry State 2
experiments): one admissible history — an initial state, the events in order
with who acts, the two outcomes the texts allow, the observer who sees the
difference, and the passages that make the history admissible, quoted
verbatim. A contradiction or a quoted gap without a complete witness is kept
as a `hypothesis`: recorded, not blocking, and put to the next round's
reviewers, who are asked for a witness. A contradiction also names, for each
of its two passages, the earlier-state passage it rests on (verbatim, or none):
a side that rests on no State 0 or State 1 passage is usually the side to
change. State 7 asks for contradictions inside one prompt and keeps its rule.
"""
from __future__ import annotations

from typing import Any

BLOCKING = {"contradiction", "consequential_gap"}
DEFERRED_TO = "State 6 contracts or State 7 notes"
LAST_DEFERRING_STATE = 5
MODULE_STATE = 7
HYPOTHESIS = "hypothesis"
KINDS = BLOCKING | {"answered", "answered_later", "later_state", "indifferent", "preexisting", "judged_before",
                    HYPOTHESIS}
WITNESS_FIELDS = ("initial", "events", "outcomes", "observer", "basis")


def _norm(text: str) -> str:
    # Markdown code marks are not content: a judge that writes a note as
    # `handle_get_run: ...` quotes the same words the texts hold without them
    # (Cabinet Kernel State 0 round-02, 2026-10-10).
    return " ".join(str(text).replace("`", "").split())


def _found(quote: str, corpus: str) -> bool:
    quote = _norm(quote)
    return len(quote) >= 12 and quote in corpus


def precedent_holds(precedent: dict[str, Any], texts: str, later_texts: str | None = None) -> bool:
    """Whether a prior judgement can still be followed: every passage it quotes
    is found verbatim where `check` looks for it — the later states' texts for
    `answered_later`, the asked texts otherwise."""
    if precedent.get("kind") == "answered_later":
        if later_texts is None:
            return False
        where = _norm(later_texts)
    else:
        where = _norm(texts)
    return all(_found(q, where) for q in precedent.get("quotes") or [])


def witness_problem(witness: Any, corpus: str, later_corpus: str = "") -> str | None:
    """Why `witness` is not a complete witness, or None when it is. Its basis
    quotes are checked like any quote: verbatim in the texts (or the later
    states' texts the judge searched)."""
    if not isinstance(witness, dict):
        return "no witness"
    def text(name: str) -> str:
        value = witness.get(name)
        return value.strip() if isinstance(value, str) else ""
    def items(name: str) -> list[str]:
        value = witness.get(name)
        return [v.strip() for v in value if isinstance(v, str) and v.strip()] if isinstance(value, list) else []
    if not text("initial"):
        return "the witness names no initial state"
    if not items("events"):
        return "the witness names no event"
    if len(set(items("outcomes"))) < 2:
        return "the witness names fewer than two different outcomes"
    if not text("observer"):
        return "the witness names no observer"
    basis = items("basis")
    if not basis:
        return "the witness quotes no passage that makes the history admissible"
    if not all(_found(q, corpus) or (later_corpus and _found(q, later_corpus)) for q in basis):
        return "a basis passage of the witness is not found verbatim in the texts"
    return None


def _kept_witness(witness: Any) -> dict[str, Any] | None:
    if not isinstance(witness, dict):
        return None
    return {name: witness.get(name) for name in WITNESS_FIELDS if witness.get(name) not in (None, "", [])}


def _bases(judgement: dict[str, Any], earlier: str | None) -> tuple[list[dict[str, str]] | None, str | None]:
    """A contradiction's bases: for each side, the earlier-state passage it rests
    on. Returns (bases, failure)."""
    raw = judgement.get("bases")
    if not isinstance(raw, list) or not raw:
        return None, None
    bases = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        rests_on = str(entry.get("rests_on") or "").strip()
        if rests_on and earlier is not None and not _found(rests_on, _norm(earlier)):
            return None, "a basis a contradiction rests on is not found verbatim in the earlier states' texts"
        bases.append({"passage": str(entry.get("passage") or ""), "rests_on": rests_on})
    return bases, None


def check(judgement: dict[str, Any] | None, state: int, texts: str, old_texts: str | None,
          later_texts: str | None = None, precedents: dict[str, dict[str, Any]] | None = None,
          own_texts: str | None = None, witness_required: bool = False,
          earlier_texts: str | None = None) -> dict[str, Any]:
    """The judgement as kept in the round, with `verified` and `blocking`.
    `own_texts` are the asked state's own documents; without them every text
    counts as the state's own. With `witness_required`, a contradiction or a
    quoted gap without a complete witness becomes a non-blocking `hypothesis`.
    `earlier_texts` are the documents of the states before this one, where a
    contradiction's bases are looked up."""
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
        elif quotes:
            later_corpus = _norm(later_texts) if later_texts is not None else ""
            here = [_found(q, corpus) for q in quotes]
            later = [_found(q, later_corpus) for q in quotes]
            if not all(h or l for h, l in zip(here, later)):
                failure = "the quoted passage of a consequential gap is not found verbatim in the texts"
            else:
                own = _norm(own_texts) if own_texts is not None else corpus
                if not any(_found(q, own) for q in quotes):
                    kept["quoted_elsewhere"] = True
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
            if precedent.get("deferred_to"):
                kept["deferred_to"] = precedent["deferred_to"]
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
    elif kind == HYPOTHESIS:
        if not kept["why"].strip():
            failure = "a hypothesis needs the reason no witness could be built"
    elif kind == "preexisting":
        if old_texts is None:
            failure = "preexisting is allowed only for a reopened state (--since)"
        elif not quotes or not all(_found(q, corpus) and _found(q, _norm(old_texts)) for q in quotes):
            failure = "the quoted passage is not found verbatim in both versions"
    if failure is None and kind == "contradiction":
        bases, failure = _bases(judgement, earlier_texts)
        if bases is not None:
            kept["bases"] = bases
            kept["unsupported_sides"] = [b["passage"] for b in bases if not b["rests_on"]]
        elif earlier_texts is not None and witness_required:
            kept["bases_missing"] = True
    if failure is not None:
        kept.pop("deferred_to", None)  # an unverified judgement defers nothing, even after a deferred precedent
    kept["verified"] = failure is None
    deferred = (failure is None and kind == "consequential_gap"
                and (not quotes or kept.get("quoted_elsewhere"))
                and state <= LAST_DEFERRING_STATE)
    witness = _kept_witness(judgement.get("witness"))
    if witness:
        kept["witness"] = witness
    if failure is None and witness_required and kind in BLOCKING and not deferred:
        problem = witness_problem(judgement.get("witness"), corpus,
                                  _norm(later_texts) if later_texts is not None else "")
        if problem is not None:
            kept["claimed_kind"] = kind
            kept["kind"] = kind = HYPOTHESIS
            kept["witness_missing"] = problem
    if deferred:
        kept["deferred_to"] = DEFERRED_TO if not quotes else "the states whose texts it quotes"
    # State 7 asks only for contradictions inside a module's prompt: a gap the
    # judge still names there is recorded, never a reason to keep notes open
    gap_recorded = kind == "consequential_gap" and state == MODULE_STATE and failure is None
    kept["blocking"] = (kind in BLOCKING and not deferred and not gap_recorded) or failure is not None
    if failure:
        kept["failure"] = failure
    return kept
