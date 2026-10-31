"""A small executable model of the Registry State 2 audit cluster.

Scope: A14, A15 and the parts of A01/A03/A04/A05/A13 they lean on, with the
State 0 and State 1 passages behind them (R0-37, R0-58, R0-60, R0-66, M09,
"Identity formats"), and — only to test numbering — the restore of A18/R0-89.
It is a model of the rules, not a design of Registry.

How a step is decided
---------------------
An event is first checked by the *engine*: the order of checks of A04 rule 6
and the domain effect (A01, A03, A04, A05, A15 rule 3). The engine is the same
for every text version; it is not where the versions differ.

The audit outcome of an accepted action — no entry, an entry, an entry with a
confirmation id, and the entry's sequence number — is *not* decided by the
engine. Every candidate outcome is generated and every normative passage of
the version under test (a State 0 promise, a State 1 fact, a State 2 rule or
formal invariant) is a predicate that accepts or rejects it. Then:

- no candidate passes      -> CONFLICT: the texts admit no conforming
                              implementation; the minimal sets of passages
                              that cannot hold together are reported;
- several pass, observably  -> AMBIGUITY: two careful implementations differ,
  different                    and the owner reading the log sees it;
- one passes               -> the step's outcome.

Invariants that speak about the whole log (A14's equivalence, A15's
ordering, M09's "never reused") are predicates too; they read ghost state
(every number ever written, every accepted change) that the store itself
does not have to hold. A ghost read is how a model shows that a rule asks for
knowledge Registry cannot have — the restore case.

Reductions (bounded exploration): one project slot; one request id; two
display names; days 0..MAX_DAY; erasure dates relative to today (later,
today, yesterday, before every entry); confirmation either valid or refused at
stage 1; storage failure only for a correction; at most one backup.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field, replace
from typing import Callable, Iterable, Optional

MAX_DAY = 2
DATE_RELS = ("later", "today", "yesterday", "before_all")


# --------------------------------------------------------------------------
# state
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Entry:
    seq: int
    day: int
    action: str
    conf: Optional[int]       # confirmation id, a fresh integer per mint
    date: Optional[int]       # the owner's date, for an erasure of old entries


@dataclass(frozen=True)
class Project:
    status: str               # active | archived
    revision: int
    name: str
    request_id: str


@dataclass(frozen=True)
class Store:
    project: Optional[Project]
    log: tuple[Entry, ...]
    last_seq: int             # A15 rule 5 (V1+): kept in the store apart from the entries
    # ghost, per store history: numbers this history ever wrote, and the
    # accepted changes (by the sequence number of the entry they wrote, or
    # None) — restored with the store, because R0-89 makes a restored store
    # begin its history from the backup
    hist_numbers: frozenset[int] = frozenset()
    hist_changes: tuple[Optional[int], ...] = ()


@dataclass(frozen=True)
class World:
    today: int
    store: Store
    history: int = 1
    backup: Optional[Store] = None
    marks: Optional[int] = None          # instance marks (V3a, V3b), survive a restore
    next_conf: int = 1
    all_numbers: frozenset[tuple[int, int]] = frozenset()   # ghost: (history, seq) ever written
    confs: frozenset[int] = frozenset()                     # ghost: confirmation ids ever minted


def initial() -> World:
    return World(today=0, store=Store(project=None, log=(), last_seq=0))


# --------------------------------------------------------------------------
# events
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Event:
    kind: str                  # create | correct | archive | erase | read_log | tick | backup | restore
    name: str = "A"            # create / correct: the display name given
    stale: bool = False        # correct / archive: a stated revision that is not current
    conf_ok: bool = True       # archive / erase: the confirmation value passes stage 1
    date_rel: str = "today"    # erase
    fail: bool = False         # correct: the store fails while committing

    def label(self) -> str:
        if self.kind == "create":
            return f"create(request_id=r1, name={self.name})"
        if self.kind == "correct":
            return (f"correct(name={self.name}{', stale' if self.stale else ''}"
                    f"{', store fails' if self.fail else ''})")
        if self.kind == "archive":
            return f"archive({'stale, ' if self.stale else ''}{'confirmed' if self.conf_ok else 'confirmation refused'})"
        if self.kind == "erase":
            return f"erase_before({self.date_rel}, {'confirmed' if self.conf_ok else 'confirmation refused'})"
        return self.kind


ACTOR = {"create": "owner", "correct": "owner", "archive": "owner, confirming",
         "erase": "owner, confirming", "read_log": "owner", "tick": "clock",
         "backup": "Registry (A18 daily run)", "restore": "owner on the host, outside Registry (R0-89)"}

CONFIRMED = {"archive", "erase"}
AUDITED = {"create": "create_project", "correct": "correct_project", "archive": "archive_project",
           "erase": "erase_old_entries"}   # M09 actions in the cluster


def alphabet(with_restore: bool) -> list[Event]:
    ev = [Event("create", name="A"), Event("create", name="B"),
          Event("correct", name="A"), Event("correct", name="B"),
          Event("correct", name="B", stale=True), Event("correct", name="B", fail=True),
          Event("archive"), Event("archive", stale=True), Event("archive", conf_ok=False),
          Event("read_log"), Event("tick")]
    ev += [Event("erase", date_rel=r) for r in DATE_RELS] + [Event("erase", conf_ok=False, date_rel="today")]
    if with_restore:
        ev += [Event("backup"), Event("restore")]
    return ev


# --------------------------------------------------------------------------
# engine: checks and domain effect (A01, A03, A04 rules 2-6, A05, A13, A15 rule 3)
# --------------------------------------------------------------------------

@dataclass
class Checked:
    answer: str                         # accepted | refused | failed | n/a
    reasons: tuple[str, ...] = ()
    stage: Optional[int] = None
    changed: bool = False               # domain state other than the log changes
    project_after: Optional[Project] = None
    removed: tuple[Entry, ...] = ()
    date: Optional[int] = None
    repeat_of: Optional[str] = None     # A01 / A03 r4 / A05: an accepted repeat


def erase_date(world: World, rel: str) -> int:
    return {"later": world.today + 1, "today": world.today, "yesterday": world.today - 1,
            "before_all": -1}[rel]


def check(world: World, ev: Event) -> Checked:
    p = world.store.project
    if ev.kind in ("read_log", "tick", "backup", "restore"):
        return Checked("n/a")
    # stage 1: confirmation value (A04 r6 (1), A13 r6)
    if ev.kind in CONFIRMED and not ev.conf_ok:
        return Checked("refused", ("confirmation",), 1)
    if ev.kind == "create":
        if p is None:
            return Checked("accepted", changed=True,
                           project_after=Project("active", 1, ev.name, "r1"))
        # A01 r4/r5: same request id; a repeat iff the facts equal the current ones
        if p.name == ev.name:
            return Checked("accepted", project_after=p, repeat_of="A01 r4")
        return Checked("refused", ("request_id_reused_with_other_facts",), 6)
    # stage 3: the record exists
    if ev.kind in ("correct", "archive") and p is None:
        return Checked("refused", ("not_found",), 3)
    if ev.kind == "erase":
        d = erase_date(world, ev.date_rel)
        # stage 4: values — a date later than today (A15 r3)
        if d > world.today:
            return Checked("refused", ("date_after_today",), 4)
        removed = tuple(e for e in world.store.log if e.day < d)
        return Checked("accepted", changed=bool(removed), project_after=p, removed=removed, date=d)
    # stage 5: the stated revision (A04 r2, r3: also for a would-be no-op)
    if ev.stale:
        return Checked("refused", ("stale",), 5)
    # stage 6: lifecycle
    if ev.kind == "correct":
        if p.status == "archived":
            return Checked("refused", ("archived",), 6)
        if p.name == ev.name:
            return Checked("accepted", project_after=p, repeat_of="A03 r4")
        if ev.fail:
            return Checked("failed", ("store_failure",))
        return Checked("accepted", changed=True, project_after=replace(p, name=ev.name, revision=p.revision + 1))
    if ev.kind == "archive":
        if p.status == "archived":
            return Checked("accepted", project_after=p, repeat_of="A05 r1")
        return Checked("accepted", changed=True,
                       project_after=replace(p, status="archived", revision=p.revision + 1))
    raise ValueError(ev.kind)


# --------------------------------------------------------------------------
# audit candidates
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Outcome:
    entry: bool
    conf: bool
    seq: Optional[int]

    def label(self) -> str:
        if not self.entry:
            return "no entry, no confirmation id"
        return f"entry #{self.seq}{' with confirmation id' if self.conf else ' without confirmation id'}"


def seq_candidates(world: World, numbering: str) -> list[int]:
    """Numbers a step could give its entry. Deliberately generous: which of
    them the text allows is the predicates' business, not the engine's."""
    s = world.store
    present = max((e.seq for e in s.log), default=0)
    cands = {s.last_seq + 1, present + 1}
    if world.marks is not None:
        cands.add(world.marks + 1)
    cands.add(max((n for _, n in world.all_numbers), default=0) + 1)
    return sorted(c for c in cands if c >= 1)


def outcomes(world: World, ev: Event, c: Checked, numbering: str) -> list[Outcome]:
    if c.answer != "accepted":
        return [Outcome(False, False, None)]
    res = [Outcome(False, False, None)]
    for n in seq_candidates(world, numbering):
        res.append(Outcome(True, False, n))
        if ev.kind in CONFIRMED:
            res.append(Outcome(True, True, n))
    return res


# --------------------------------------------------------------------------
# applying an outcome
# --------------------------------------------------------------------------

def _keeps_marks(numbering: str, interp: dict) -> bool:
    """A counter outside the store, which a restore does not replace: the
    instance marks of V3a/V3b, or V1's "kept durably, apart from the
    entries" read as kept outside the store (interpretation)."""
    return numbering in ("marks", "marks_skip") or (
        numbering == "durable" and interp.get("durable_counter", "in_store") == "outside_store")


def apply(world: World, ev: Event, c: Checked, o: Outcome, numbering: str, interp: dict | None = None) -> World:
    interp = interp or {}
    s = world.store
    if ev.kind == "tick":
        return replace(world, today=min(world.today + 1, MAX_DAY))
    if ev.kind == "read_log":
        return world
    if ev.kind == "backup":
        return replace(world, backup=s)
    if ev.kind == "restore":
        if world.backup is None:
            return world
        return replace(world, store=world.backup, history=world.history + 1)
    marks = world.marks
    if c.answer == "failed":
        # V3a/V3b: the number is recorded in the marks before the commit fails
        if numbering in ("marks", "marks_skip"):
            marks = max(marks or 0, s.last_seq) + 1
        return replace(world, marks=marks)
    if c.answer != "accepted":
        return world
    log = tuple(e for e in s.log if e not in c.removed)
    last = s.last_seq
    hist_numbers, all_numbers, confs, next_conf = s.hist_numbers, world.all_numbers, world.confs, world.next_conf
    conf_id = None
    if o.entry:
        if o.conf:
            conf_id = next_conf
            next_conf += 1
            confs = confs | {conf_id}
        log = log + (Entry(o.seq, world.today, AUDITED[ev.kind], conf_id, c.date),)
        last = max(last, o.seq)
        hist_numbers = hist_numbers | {o.seq}
        all_numbers = all_numbers | {(world.history, o.seq)}
        if _keeps_marks(numbering, interp):
            marks = max(marks or 0, o.seq)
    changes = s.hist_changes + ((o.seq if o.entry else None),) if (c.changed or o.entry) else s.hist_changes
    store = Store(c.project_after, log, last, hist_numbers, changes)
    return replace(world, store=store, marks=marks, next_conf=next_conf, all_numbers=all_numbers, confs=confs)


def observe(world: World, c: Optional[Checked]) -> dict:
    """What the owner sees: the answer, the project card, and the log read."""
    p = world.store.project
    return {
        "answer": None if c is None else (c.answer, list(c.reasons)),
        "project": None if p is None else {"status": p.status, "revision": p.revision, "name": p.name},
        "log": [{"seq": e.seq, "day": e.day, "action": e.action, "confirmation_id": e.conf is not None,
                 "date": e.date} for e in world.store.log],
    }


# --------------------------------------------------------------------------
# predicates: the normative passages
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Ctx:
    pre: World
    ev: Event
    c: Checked
    o: Outcome
    post: World
    interp: dict


@dataclass(frozen=True)
class Rule:
    id: str
    layer: str                 # S0 | S1 | S2 | S2-invariant
    form: str                  # transition | prohibition | condition | invariant
    keys: tuple[str, ...]      # passages in sources.Q
    pred: Callable[[Ctx], bool]
    note: str = ""


def _accepted(x: Ctx) -> bool:
    return x.c.answer == "accepted"


def _empty_erasure(x: Ctx) -> bool:
    return x.ev.kind == "erase" and _accepted(x) and not x.c.removed


def _changes_state(x: Ctx) -> bool:
    """A14's "changes state". Whether an erasure's own entry counts is a
    reading the texts do not settle before V5 (interpretation
    `own_entry_is_change`)."""
    if x.c.changed:
        return True
    return x.ev.kind == "erase" and x.interp.get("own_entry_is_change", False) and x.o.entry


def _a05_transition(x: Ctx) -> bool:
    if x.c.repeat_of == "A05 r1":
        return True
    # rejected reading, kept to be executed: an erasure that removes nothing is
    # a "transition to the state the log is already in"
    return x.interp.get("a05_covers_empty_erasure", False) and _empty_erasure(x)


def _imp(a: bool, b: bool) -> bool:
    return (not a) or b


def rules_for(version: dict) -> list[Rule]:
    v = version
    R: list[Rule] = []
    # ---- State 0 ----------------------------------------------------------
    R.append(Rule("R0-66", "S0", "transition", ("R0-66.row", "R0-66.text"),
                  lambda x: _imp(x.ev.kind == "erase" and _accepted(x), x.o.entry),
                  "an accepted erasure of old entries leaves an entry of its own naming the date"))
    R.append(Rule("R0-37/M09 conf", "S0", "condition", ("R0-37.audit", "M09.conf"),
                  lambda x: _imp(x.o.entry and x.ev.kind in CONFIRMED, x.o.conf),
                  "an entry of an action the owner confirmed carries a confirmation id"))
    R.append(Rule("R0-58 changes", "S0", "transition", ("R0-58.scope",),
                  lambda x: _imp(_accepted(x) and x.c.changed and x.ev.kind in AUDITED, x.o.entry),
                  "a significant change of state is recorded"))
    R.append(Rule("R0-58 reads", "S0", "prohibition", ("R0-58.reads", "A14.r4"),
                  lambda x: _imp(x.ev.kind == "read_log", not x.o.entry)))
    # ---- State 1 ----------------------------------------------------------
    if v["seq_scope_s1"] == "global":
        R.append(Rule("M09 never reused (global)", "S1", "invariant", ("M09.seq.global",),
                      lambda x: _imp(x.o.entry, all(n != x.o.seq for _, n in x.pre.all_numbers)),
                      "no number is ever written twice, in any history"))
    else:
        R.append(Rule("M09 never reused (per history)", "S1", "invariant", ("M09.seq.history", "R0-89.history"),
                      lambda x: _imp(x.o.entry, x.o.seq not in x.pre.store.hist_numbers)))
    # "Identity formats" read as complete: every confirmed, accepted action
    # mints an id written into its entry. State 1 round 01 T7 judged the
    # no-op case carried to State 2 (later_state), so the default reading
    # does not apply it; the strict reading is run to show what it costs.
    R.append(Rule("Identity formats (strict)", "S1", "transition", ("ID.conf_minted",),
                  lambda x: _imp(x.interp.get("id_formats_strict", False) and _accepted(x)
                                 and x.ev.kind in CONFIRMED, x.o.entry and x.o.conf)))
    # ---- State 2: A14 -----------------------------------------------------
    R.append(Rule("A14 r1", "S2", "transition", ("A14.r1",),
                  lambda x: _imp(_accepted(x) and _changes_state(x) and x.ev.kind in AUDITED, x.o.entry)))
    R.append(Rule("A14 r2", "S2", "prohibition", ("A14.r2",),
                  lambda x: _imp(not _accepted(x), not x.o.entry)))
    if v["a14_exception"]:
        R.append(Rule("A14 r3", "S2", "prohibition", ("A14.r3.new",),
                      lambda x: _imp(_accepted(x) and not _changes_state(x) and x.ev.kind != "erase",
                                     not x.o.entry)))
    else:
        R.append(Rule("A14 r3", "S2", "prohibition", ("A14.r3.old",),
                      lambda x: _imp(_accepted(x) and not _changes_state(x), not x.o.entry)))
    if v["a14_r5_exception"]:
        R.append(Rule("A14 r5", "S2", "condition", ("A14.r5.old", "A14.r5.new"),
                      lambda x: x.o.conf == (_accepted(x) and x.ev.kind in CONFIRMED
                                              and (_changes_state(x) or x.ev.kind == "erase"))))
    else:
        R.append(Rule("A14 r5", "S2", "condition", ("A14.r5.old",),
                      lambda x: x.o.conf == (_accepted(x) and x.ev.kind in CONFIRMED and _changes_state(x))))
    # A14 formal invariant
    def a14_inv(x: Ctx) -> bool:
        cond = _accepted(x) and x.ev.kind in AUDITED and (
            _changes_state(x) or (v["a14_exception"] and x.ev.kind == "erase"))
        if x.interp.get("a14_inv_reading", "at_commit") == "at_commit":
            return x.o.entry == cond
        # literal: over the log as it now stands, every accepted change of this
        # history has its entry, and every entry belongs to one
        present = {e.seq for e in x.post.store.log}
        changes = x.post.store.hist_changes
        return x.o.entry == cond and all(n is not None and n in present for n in changes)
    R.append(Rule("A14 invariant", "S2-invariant", "invariant",
                  ("A14.inv.new",) if v["a14_exception"] else ("A14.inv.old",), a14_inv))
    # ---- State 2: A05 -----------------------------------------------------
    R.append(Rule("A05 r2", "S2", "prohibition", ("A05.r1.head", "A05.r2", "A14.t2"),
                  lambda x: _imp(_a05_transition(x), not x.o.entry and not x.o.conf)))
    R.append(Rule("A03 r4 / A01 r4", "S2", "prohibition", ("A03.r4", "A01.r4"),
                  lambda x: _imp(x.c.repeat_of in ("A03 r4", "A01 r4"), not x.o.entry)))
    # ---- State 2: A15 -----------------------------------------------------
    R.append(Rule("A15 r4", "S2", "condition", ("A15.r4",),
                  lambda x: _imp(x.ev.kind == "erase" and x.o.entry,
                                 any(e.seq == x.o.seq for e in x.post.store.log))))
    numbering = v["numbering"]

    def a15_r5(x: Ctx) -> bool:
        if not x.o.entry:
            return True
        s, w = x.pre.store, x.pre
        ever_global = max((n for _, n in w.all_numbers), default=0)
        if numbering == "ever":            # "continues from the last number ever written"
            return x.o.seq == ever_global + 1
        if numbering == "durable" and x.interp.get("durable_counter", "in_store") == "outside_store":
            return x.o.seq == max(s.last_seq, w.marks or 0) + 1
        if numbering in ("durable", "history"):   # kept in the store apart from the entries
            return x.o.seq == s.last_seq + 1
        if numbering == "reissue_after_restore":
            return x.o.seq == s.last_seq + 1
        if numbering == "marks":
            # "continues from the last number ever written": a number recorded
            # in the marks before a failed commit may or may not count as written
            return x.o.seq in {max(s.last_seq, w.marks or 0) + 1, s.last_seq + 1}
        if numbering == "marks_skip":
            return x.o.seq == max(s.last_seq, w.marks or 0) + 1
        raise ValueError(numbering)
    key5 = {"ever": ("A15.r5.ever",), "durable": ("A15.r5.ever", "A15.r5.durable"),
            "reissue_after_restore": ("A15.r5.durable", "A15.r5.reissue"),
            "marks": ("A15.r5.marks",), "marks_skip": ("A15.r5.marks", "A15.r5.marks_skip"),
            "history": ("A15.r5.history",)}[numbering]
    R.append(Rule("A15 r5", "S2", "transition", key5, a15_r5))
    if v["empty_erasure"] == "nothing":
        R.append(Rule("A15 r6", "S2", "transition", ("A15.r6.old", "A15.t2.old"),
                      lambda x: _imp(_empty_erasure(x), not x.o.entry and not x.o.conf)))
    else:
        R.append(Rule("A15 r6", "S2", "transition", ("A15.r6.new", "A15.t2.new"),
                      lambda x: _imp(_empty_erasure(x), x.o.entry and x.o.conf)))
    # A15 formal invariants
    R.append(Rule("A15 invariant (order)", "S2-invariant", "invariant", ("A15.inv.seq",),
                  lambda x: all(a.seq < b.seq for a, b in zip(x.post.store.log, x.post.store.log[1:]))))
    R.append(Rule("A15 invariant (removed)", "S2-invariant", "invariant", ("A15.inv.removed",),
                  lambda x: _imp(x.ev.kind == "erase" and _accepted(x),
                                 x.c.date is None or all(e.day >= x.c.date for e in x.post.store.log))))
    mode = v["a15_inv_erasure_entry"]

    def a15_inv_entry(x: Ctx) -> bool:
        if not (x.ev.kind == "erase" and _accepted(x)):
            return True
        if mode == "if_removed" and not x.c.removed:
            return True
        if mode == "unconditional" and not x.interp.get("a15_inv_presupposes", True):
            # conditional reading of "the erasure entry e": only if there is one
            return (not x.o.entry) or x.pre.today >= x.c.date
        return x.o.entry and x.pre.today >= x.c.date
    key_inv = {"unconditional": ("A15.inv.entry.v5",) if v["empty_erasure"] != "nothing" else ("A15.inv.entry.v0",),
               "if_removed": ("A15.inv.entry.v2",)}[mode]
    R.append(Rule("A15 invariant (erasure entry)", "S2-invariant", "invariant", key_inv, a15_inv_entry))
    return R


# --------------------------------------------------------------------------
# deciding a step
# --------------------------------------------------------------------------

@dataclass
class Step:
    event: Event
    checked: Checked
    passing: list[tuple[Outcome, World]]
    violations: dict[Outcome, list[str]]
    verdict: str                          # determined | conflict | ambiguity | out_of_store | no_audit
    conflict_sets: list[tuple[str, ...]] = field(default_factory=list)
    # for a conflict: what it takes to remove it
    #   state2_edit      some outcome breaks only State 2 passages and is one
    #                    Registry can produce: editing State 2 resolves it
    #   state2_mechanism the only such outcomes need a number Registry cannot
    #                    derive from what it holds: State 2 needs a new mechanism
    #   owner            every outcome breaks a State 0 or State 1 passage:
    #                    only a change of an earlier state — a new or narrowed
    #                    promise of the owner — resolves it
    resolution: Optional[str] = None


def minimal_hitting_sets(sets: list[set[str]], limit: int = 3) -> list[tuple[str, ...]]:
    universe = sorted(set().union(*sets))
    found: list[tuple[str, ...]] = []
    for k in range(1, limit + 1):
        for combo in itertools.combinations(universe, k):
            cs = set(combo)
            if all(s & cs for s in sets) and not any(set(f) <= cs for f in found):
                found.append(combo)
    return found


def step(world: World, ev: Event, rules: list[Rule], version: dict, interp: dict) -> Step:
    c = check(world, ev)
    if c.answer == "n/a" and ev.kind != "read_log":
        return Step(ev, c, [(Outcome(False, False, None), apply(world, ev, c, Outcome(False, False, None),
                                                                  version["numbering"], interp))], {}, "no_audit")
    numbering = version["numbering"]
    passing, violations = [], {}
    for o in outcomes(world, ev, c, numbering):
        post = apply(world, ev, c, o, numbering, interp)
        x = Ctx(world, ev, c, o, post, interp)
        bad = [r.id for r in rules if not r.pred(x)]
        if bad:
            violations[o] = bad
        else:
            passing.append((o, post))
    known = knowable_numbers(world, version, interp)
    if not passing:
        sets = [set(b) for b in violations.values()]
        layer = {r.id: r.layer for r in rules}
        s2_only = [o for o, b in violations.items() if all(layer[i].startswith("S2") for i in b)]
        if any(not o.entry or o.seq in known for o in s2_only):
            resolution = "state2_edit"
        elif s2_only:
            resolution = "state2_mechanism"
        else:
            resolution = "owner"
        return Step(ev, c, [], violations, "conflict", minimal_hitting_sets(sets), resolution)
    real = [(o, post) for o, post in passing if not o.entry or o.seq in known]
    if not real:
        # the texts are satisfiable only by a number Registry cannot derive
        # from what it holds (the store, and the marks where a version has them)
        return Step(ev, c, passing, violations, "out_of_store")
    observable = {(o.entry, o.conf, o.seq) for o, _ in real}
    return Step(ev, c, real, violations, "ambiguity" if len(observable) > 1 else "determined")


def knowable_numbers(world: World, version: dict, interp: dict) -> set[int]:
    s = world.store
    known = {max((e.seq for e in s.log), default=0) + 1}
    # V0 says the next number "continues from the last number ever written"
    # but not where that number is kept; V1 onwards keep it apart from the
    # entries. Interpretation `v0_counter`: "unstated" (only the entries tell
    # it) or "kept" (read V1's mechanism into V0).
    if version["numbering"] != "ever" or interp.get("v0_counter", "unstated") == "kept":
        known.add(s.last_seq + 1)
    if world.marks is not None:
        known.add(max(world.marks, s.last_seq) + 1)
        known.add(world.marks + 1)
    return known


def run(events: Iterable[Event], version: dict, interp: dict, setup_world: Optional[World] = None,
        choose: Optional[Callable[[Step], int]] = None) -> tuple[World, list[Step]]:
    """Run a fixed history. On an ambiguity the first passing outcome is taken
    (or `choose`'s); on a conflict the run stops."""
    rules = rules_for(version)
    w = setup_world or initial()
    steps = []
    for ev in events:
        s = step(w, ev, rules, version, interp)
        steps.append(s)
        if s.verdict in ("conflict", "out_of_store"):
            break
        w = s.passing[(choose(s) if choose else 0)][1]
    return w, steps
