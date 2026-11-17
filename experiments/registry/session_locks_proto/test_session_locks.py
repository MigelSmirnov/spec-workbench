"""Run: python -I -m pytest -q -p no:cacheprovider experiments/registry/session_locks_proto"""
from __future__ import annotations

import random
import sys
import threading
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from session_locks import MAX_AGE, Refused, Sessions  # noqa: E402

CSRF = "c"


class Clock:
    def __init__(self, now=0.0):
        self.now = now
        self._lock = threading.Lock()

    def __call__(self):
        with self._lock:
            return self.now


def design(turn_in_hold: bool):
    return type("S", (Sessions,), {"TURN_IN_HOLD": turn_in_hold})


def paused(sessions, name):
    """Hold request `name` between the table lock's release and its turn."""
    reached, go = threading.Event(), threading.Event()

    def hook(request):
        if request == name:
            reached.set()
            go.wait(5)
    sessions.after_release = hook
    return reached, go


def run(target, *args, **kwargs):
    thread = threading.Thread(target=target, args=args, kwargs=kwargs, daemon=True)
    thread.start()
    return thread


def ran_on_ended(sessions, request):
    return [entry[3] for entry in sessions.log if entry[:2] == ("run", request)]


# ------------------------------------------- a sign-out overtakes a change
@pytest.mark.parametrize("file", [False, True], ids=["change", "upload"])
@pytest.mark.parametrize("turn_in_hold", [False, True], ids=["literal", "turn_in_hold"])
def test_a_change_admitted_before_a_sign_out_completes_first(turn_in_hold, file):
    clock = Clock(100.0)
    sessions = design(turn_in_hold)(clock)
    sessions.sign_in("s", CSRF)
    reached, go = paused(sessions, "C")
    change = run(sessions.admit, "C", "s", change=True, file=file, csrf=CSRF)
    assert reached.wait(5)                            # C is admitted
    out = run(sessions.admit, "SO", "s", change=True, file=True, sign_out=True,
              csrf=CSRF, step=sessions.sign_out_step("s"))
    out.join(0.5)                                     # SO admitted after C
    go.set()
    change.join(5)
    out.join(5)
    assert not change.is_alive() and not out.is_alive()
    if turn_in_hold:
        assert ran_on_ended(sessions, "C") == [False]
    else:
        # The finding: read literally, the sign-out takes its turn before the
        # change admitted ahead of it, which then runs in an ended session —
        # against sign_out_owner's "one admitted before it completes first".
        assert ran_on_ended(sessions, "C") == [True]


# ------------------------------------------- the pass overtakes a change
@pytest.mark.parametrize("turn_in_hold", [False, True], ids=["literal", "turn_in_hold"])
def test_a_change_admitted_before_the_pass_completes_first(turn_in_hold):
    clock = Clock(0.0)
    sessions = design(turn_in_hold)(clock)
    sessions.sign_in("s", CSRF)
    for minute in range(25, MAX_AGE // 60, 25):       # a read every 25 minutes
        clock.now = minute * 60.0
        sessions.admit("read", "s", change=False, file=False)
    clock.now = MAX_AGE - 1                           # C arrives 1 s short of 8 h
    reached, go = paused(sessions, "C")
    change = run(sessions.admit, "C", "s", change=True, file=False, csrf=CSRF)
    assert reached.wait(5)
    clock.now = MAX_AGE                               # the pass begins at 8 h
    sweep = run(sessions.end_expired)
    sweep.join(0.5)
    go.set()
    change.join(5)
    sweep.join(5)
    if turn_in_hold:
        assert ran_on_ended(sessions, "C") == [False]
    else:
        assert ran_on_ended(sessions, "C") == [True]


# ------------------------------------------- an upload overtaken at the import lock
@pytest.mark.parametrize("turn_in_hold", [False, True], ids=["literal", "turn_in_hold"])
def test_import_lock_is_granted_in_admission_order(turn_in_hold):
    clock = Clock(100.0)
    sessions = design(turn_in_hold)(clock)
    sessions.sign_in("a", CSRF)
    sessions.sign_in("b", CSRF)
    reached, go = paused(sessions, "first")
    first = run(sessions.admit, "first", "a", change=True, file=True, csrf=CSRF)
    assert reached.wait(5)
    second = run(sessions.admit, "second", "b", change=True, file=True, csrf=CSRF)
    second.join(0.5)
    go.set()
    first.join(5)
    second.join(5)
    order = [entry[1] for entry in sessions.log]
    assert order == (["first", "second"] if turn_in_hold else ["second", "first"])


# ------------------------------------------- stress: no deadlock, invariant holds
def test_stress_turn_in_hold_never_deadlocks_and_keeps_admission_order():
    clock = Clock(0.0)
    sessions = design(True)(clock)
    ids = [f"s{i}" for i in range(4)]
    for sid in ids:
        sessions.sign_in(sid, CSRF)
    refused = []

    def worker(n):
        local = random.Random(n)
        for k in range(60):
            sid = local.choice(ids)
            kind = local.random()
            try:
                if kind < 0.05:
                    sessions.admit(f"{n}.{k}", sid, change=True, file=True, sign_out=True,
                                   csrf=CSRF, step=sessions.sign_out_step(sid))
                elif kind < 0.10:
                    sessions.end_expired()
                elif kind < 0.40:
                    sessions.admit(f"{n}.{k}", sid, change=True, file=True, csrf=CSRF)
                elif kind < 0.75:
                    sessions.admit(f"{n}.{k}", sid, change=True, file=False, csrf=CSRF)
                else:
                    sessions.admit(f"{n}.{k}", sid, change=False, file=False)
            except Refused:
                refused.append(1)
            with clock._lock:
                clock.now += local.choice([0, 1, 60, 600])

    threads = [run(worker, n) for n in range(12)]
    for thread in threads:
        thread.join(30)
    assert not any(t.is_alive() for t in threads), "deadlock"
    # A request holding a place on the session's lock (a change, or one
    # touching a file) never runs in a session that has ended: every one
    # admitted before a sign-out or the pass ran first, every later one was
    # refused. A read holds no place and may finish after the end.
    runs = [e for e in sessions.log if e[0] == "run"]
    assert runs and refused and sessions.ended
    assert [e for e in runs if e[3] and e[4]] == []
