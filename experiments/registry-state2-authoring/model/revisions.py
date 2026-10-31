"""Which answer does a revision-stating owner action get, for every record state?

A small model of Registry's revision rules (A04 rules 1-3 and 6, A05, the
Primary actions rows of State 0, R0-35, R0-71), built for one question: what
happens when a request states a revision and the record has none — an erased
Customer, an anonymised project.

Nothing the texts leave open is decided here. The engine (`effect`) only
knows what each action does to a record when it is accepted. The answer is
chosen by the normative passages, written as predicates over candidate
outcomes. Where a passage can be read in more than one way, each reading is a
named parameter. A situation is decided by a set of readings (one per
parameter):

- one outcome passes every predicate -> that outcome;
- none passes                       -> CONFLICT: that set of readings is
                                       inconsistent with the texts;
- the current text admits a situation's readings with different outcomes
                                    -> the text leaves the answer open.

Reductions: one record of each kind; a record's state is one of the few that
matter here; the stated revision is one of: the current one, the one the
record had when it was erased (`last`), an older one, or none. Confirmation
(A13) is either a fresh value or a used-up one; only the first reaches the
checks this model is about.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Callable, Optional

# --------------------------------------------------------------------------
# situations
# --------------------------------------------------------------------------

CUSTOMER_STATES = ("plain", "restricted", "ended", "erased")
PROJECT_STATES = ("active", "archived", "anonymised")
CUSTOMER_ACTIONS = ("correct", "erase", "restrict", "lift", "end", "resume")
PROJECT_ACTIONS = ("correct", "archive", "anonymise", "delete_whole")
CONFIRMED = {("project", "archive"), ("project", "anonymise"), ("project", "delete_whole")}  # Identity formats
STATED = ("current", "last", "older", "none")


@dataclass(frozen=True)
class Situation:
    kind: str           # customer | project
    state: str
    action: str
    stated: str         # current | last | older | none
    conf: str = "fresh"  # fresh | used — only for confirmed actions

    @property
    def has_revision(self) -> bool:
        return self.state not in ("erased", "anonymised")

    def label(self) -> str:
        c = f", confirmation {self.conf}" if (self.kind, self.action) in CONFIRMED else ""
        return f"{self.action} {self.kind} [{self.state}] stating {self.stated}{c}"


def situations() -> list[Situation]:
    out = []
    for kind, states, actions in (("customer", CUSTOMER_STATES, CUSTOMER_ACTIONS),
                                  ("project", PROJECT_STATES, PROJECT_ACTIONS)):
        for st, act, sr in itertools.product(states, actions, STATED):
            has = st not in ("erased", "anonymised")
            if has and sr == "last":
                continue      # "last" only names the revision an erased record had
            if not has and sr == "current":
                continue      # a record without a revision has no current one
            confs = ("fresh", "used") if (kind, act) in CONFIRMED else ("fresh",)
            for cf in confs:
                out.append(Situation(kind, st, act, sr, cf))
    return out


# --------------------------------------------------------------------------
# engine: what an accepted action does (no answer is decided here)
# --------------------------------------------------------------------------

TARGET = {
    ("customer", "erase"): "erased", ("customer", "restrict"): "restricted",
    ("customer", "lift"): "plain", ("customer", "end"): "ended", ("customer", "resume"): "plain",
    ("project", "archive"): "archived", ("project", "anonymise"): "anonymised",
}


def already_there(s: Situation) -> bool:
    """The action is a transition to the state the record is in (A05 r1's
    shape). Lifting an unrestricted Customer and resuming one that is not
    ended are the repeats of A05 r1; erased and anonymised are final."""
    t = TARGET.get((s.kind, s.action))
    if t is None:
        return False
    if (s.kind, s.action) == ("customer", "lift"):
        return s.state in ("plain", "ended")
    if (s.kind, s.action) == ("customer", "resume"):
        return s.state in ("plain", "restricted")
    if (s.kind, s.action) == ("project", "archive"):
        return s.state in ("archived", "anonymised")
    return s.state == t


# outcomes, with the A04 rule 6 stage they answer at
OUTCOMES = {
    "refused: confirmation": 1,
    "refused: missing revision": 4,
    "refused: invalid revision": 4,
    "refused: stale": 5,
    "refused: lifecycle": 6,
    "accepted: unchanged": 7,
    "accepted: changed": 7,
}


# --------------------------------------------------------------------------
# readings
# --------------------------------------------------------------------------

READINGS = {
    # A04 r2 "A stated revision that is not the record's current one is refused
    # as stale": does it reach a record that has no current one?
    "a04_r2": ("all_records", "records_with_revision"),
    # A04 r3 "an action on them states none": a caller's duty Registry does not
    # check, or an input rule whose breach is an invalid value (stage 4)?
    "a04_r3_none": ("caller_duty", "invalid_value"),
    # A04 invariant "for action a … that may move r.revision": an action of a
    # kind that moves revisions, or this action on this record?
    "a04_inv": ("action_kind", "this_action"),
    # State 0's "… returns it unchanged" rows: whatever revision the request
    # states (stages 1-4 still apply), or only for a request that passes every
    # check, the revision included (as A04 r3 and test 3 already read R0-12)?
    "s0_unchanged_rows": ("over_revision", "after_checks"),
    # A04 r1 "states the revision": a request stating none on a record that has
    # one is a missing value (stage 4) or a stale revision (stage 5)?
    "absent_revision": ("missing_value", "stale"),
    # A05 r4 "The refusals State 0 states stay refusals and come first": first
    # before the repeat of A05 r1 only (they sit in stage 6), or before the
    # revision check too? Added after the hand-over check named it; the first
    # version of this model had put them in stage 6 without saying so.
    "a05_r4_first": ("before_repeat", "before_revision"),
}


# --------------------------------------------------------------------------
# predicates
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Pred:
    id: str
    layer: str
    keys: tuple[str, ...]
    fn: Callable[[Situation, str, dict], bool]
    note: str = ""


def _refused(o: str) -> bool:
    return o.startswith("refused")


def failing_stages(s: Situation, r: dict) -> dict[int, str]:
    """The checks of A04 rule 6 that fail, by stage, under readings r. Every
    condition here is a passage under a reading, never a modelling choice."""
    f: dict[int, str] = {}
    if (s.kind, s.action) in CONFIRMED and s.conf == "used":
        f[1] = "refused: confirmation"                      # A13 r6
    if s.has_revision and s.stated == "none":
        f[4 if r["absent_revision"] == "missing_value" else 5] = (
            "refused: missing revision" if r["absent_revision"] == "missing_value" else "refused: stale")
    if not s.has_revision and s.stated != "none" and r["a04_r3_none"] == "invalid_value":
        f.setdefault(4, "refused: invalid revision")
    stale = (s.stated in ("older",) and s.has_revision) or (
        not s.has_revision and s.stated != "none" and r["a04_r2"] == "all_records")
    if stale:
        f.setdefault(5, "refused: stale")
    if lifecycle_refusal(s):
        a05_r4 = s.kind == "project" and s.action == "delete_whole" and s.state == "anonymised"
        if a05_r4 and r["a05_r4_first"] == "before_revision":
            f[4.5] = "refused: lifecycle"
        else:
            f[6] = "refused: lifecycle"
    return f


def lifecycle_refusal(s: Situation) -> bool:
    """State 0's stated refusals (Primary actions rows, R0-12, R0-71), which A05
    r4 keeps first among the lifecycle checks."""
    if s.kind == "customer":
        return s.state == "erased" and s.action in ("correct", "restrict", "lift", "end", "resume")
    if s.action == "correct":
        return s.state in ("archived", "anonymised")
    if s.action == "delete_whole":
        return s.state == "anonymised" or s.state == "active"
    if s.action == "anonymise":
        return s.state == "active"
    return False


def preds() -> list[Pred]:
    P: list[Pred] = []
    # ---- State 0 ----------------------------------------------------------
    P.append(Pred("R0-35", "S0", ("R0-35",),
                  lambda s, o, r: not (o == "accepted: changed" and s.stated != "current"),
                  "a change against an older (or no) revision is refused; a no-op is not a change"))
    P.append(Pred("S0 action rows (effect)", "S0", ("S0.erase_row", "S0.correct_row"),
                  lambda s, o, r: not (o == "accepted: unchanged" and not already_there(s)),
                  "an accepted action that is not a repeat does what its row says; corrections are "
                  "modelled with facts that differ from the stored ones (A03 rule 4 is out of scope)"))
    P.append(Pred("S0 refusal rows", "S0", ("S0.correct_row", "S0.restrict_row", "S0.end_row",
                                            "S0.erase_project_row", "M04.erased_refused"),
                  lambda s, o, r: not lifecycle_refusal(s) or _refused(o)))

    def unchanged_rows(s, o, r):
        repeat_rows = {("customer", "erase"), ("project", "archive"), ("project", "anonymise")}
        if (s.kind, s.action) not in repeat_rows or not already_there(s):
            return True
        if r["s0_unchanged_rows"] == "over_revision":
            early = [k for k in failing_stages(s, r) if k < 5]
            return bool(early) or o == "accepted: unchanged"
        return o != "accepted: changed" and o != "refused: lifecycle"
    P.append(Pred("S0 'returns it unchanged' rows", "S0",
                  ("S0.erase_row", "S0.archive_row", "S0.erase_project_row", "R0-71"), unchanged_rows))
    # ---- State 2 ----------------------------------------------------------
    P.append(Pred("A04 r6 order", "S2", ("A04.r6.kind", "A04.r6.stages"),
                  lambda s, o, r: _first(s, r) == o if _first(s, r) else not _refused(o),
                  "the first failing stage answers; none failing -> accepted"))
    P.append(Pred("A05 r1-r2", "S2", ("A05.r1", "A05.r1.erased", "A05.r2"),
                  lambda s, o, r: _first(s, r) is not None or not already_there(s) or o == "accepted: unchanged"))
    P.append(Pred("accepted change only when not already there", "S2", ("A05.r1",),
                  lambda s, o, r: not (o == "accepted: changed" and already_there(s))))

    def inv(s, o, r):
        stated_differs = (s.stated in ("older", "none") and s.has_revision) or (
            not s.has_revision and s.stated != "none")
        applies = True if r["a04_inv"] == "action_kind" else s.has_revision
        return not (applies and stated_differs) or _refused(o)
    P.append(Pred("A04 invariant", "S2-invariant", ("A04.inv",), inv))
    return P


def _first(s: Situation, r: dict) -> Optional[str]:
    f = failing_stages(s, r)
    return f[min(f)] if f else None


def decide(s: Situation, r: dict, extra: list[Pred] | None = None) -> tuple[Optional[str], list[str]]:
    """The one outcome every predicate allows under readings r, or None with
    the predicates that exclude the last candidates."""
    ps = preds() + (extra or [])
    ok = [o for o in OUTCOMES if all(p.fn(s, o, r) for p in ps)]
    if len(ok) == 1:
        return ok[0], []
    if not ok:
        blame = sorted({p.id for o in OUTCOMES for p in ps if not p.fn(s, o, r)})
        return None, blame
    return "AMBIGUOUS:" + "|".join(ok), []


def reading_sets(fixed: dict | None = None):
    fixed = fixed or {}
    keys = list(READINGS)
    for vals in itertools.product(*(READINGS[k] if k not in fixed else (fixed[k],) for k in keys)):
        yield dict(zip(keys, vals))
