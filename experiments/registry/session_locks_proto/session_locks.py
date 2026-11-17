"""Prototype of `owner_sessions`' locks (State 5 conventions, owner 2026-11-17).

The spec (50_public_apis_0_conventions.md "Locks of an owner request";
50_public_apis_2_sessions.md `admit_owner_request`, `sign_out_owner`,
`end_expired_sessions`):

- one session-table lock guards each session's entry, signed-out mark and
  last-request reading; taken last, released before any other is taken;
- the import lock, granted in the order requests asked for it; "a request
  asks for the import lock when it is admitted";
- each session's lock, granted in the order places were taken; a change
  touching no file takes its place "at once" after the check, one touching a
  file only after the import lock;
- the arrival is fixed in one hold of the table lock, which is released
  "before it waits for the import lock or a place on the session's lock".

`TURN_IN_HOLD` picks where a request asks for its turn:
  False — after the table lock is released (the text read literally);
  True  — inside the arrival's hold: it draws a ticket of the import lock, or
          its place on the session's lock, without waiting there, and waits
          for it after the release.

Not generated code: a throwaway experiment.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Callable

IDLE = 30 * 60
MAX_AGE = 8 * 3600


class Refused(Exception):
    pass


class FifoLock:
    """Granted in the order tickets were drawn. `draw` never waits."""

    def __init__(self) -> None:
        self._cond = threading.Condition()
        self._next = 0
        self._serving = 0

    def draw(self) -> int:
        with self._cond:
            ticket = self._next
            self._next += 1
            return ticket

    def wait(self, ticket: int) -> None:
        with self._cond:
            while self._serving != ticket:
                self._cond.wait()

    def release(self) -> None:
        with self._cond:
            self._serving += 1
            self._cond.notify_all()

    def acquire(self) -> None:
        self.wait(self.draw())


@dataclass
class Session:
    began: float
    last_request: float
    csrf: str
    signed_out: bool = False
    lock: FifoLock = field(default_factory=FifoLock)

    def valid_at(self, reading: float) -> bool:
        return (not self.signed_out
                and reading < self.began + MAX_AGE
                and reading < self.last_request + IDLE)


class Sessions:
    TURN_IN_HOLD = False

    def __init__(self, clock: Callable[[], float]) -> None:
        self.clock = clock
        self.table = threading.Lock()
        self.import_lock = FifoLock()
        self.sessions: dict[str, Session] = {}
        self.ended: list[str] = []
        self.log: list[tuple] = []          # what ran, in order
        self.after_release = lambda request: None   # test hook

    # ------------------------------------------------------------ sign-in
    def sign_in(self, session_id: str, csrf: str) -> None:
        with self.table:
            now = self.clock()
            self.sessions[session_id] = Session(now, now, csrf)

    # ------------------------------------------------------------ admit
    def admit(self, request: str, session_id: str, *, change: bool, file: bool,
              sign_out: bool = False, csrf: str | None = None,
              step: Callable[[Session], object] = lambda s: None):
        import_ticket = place = None
        with self.table:
            reading = self.clock()
            session = self.sessions.get(session_id)
            if session is None or not session.valid_at(reading):
                raise Refused("no_owner_session")
            session.last_request = max(session.last_request, reading)
            if change and csrf != session.csrf:
                raise Refused("csrf_refused")
            if sign_out:
                session.signed_out = True
            if self.TURN_IN_HOLD:
                if file:
                    import_ticket = self.import_lock.draw()
                elif change:
                    place = session.lock.draw()
        self.after_release(request)
        if file:
            if import_ticket is None:
                import_ticket = self.import_lock.draw()
            self.import_lock.wait(import_ticket)
            place = session.lock.draw()
        elif change and place is None:
            place = session.lock.draw()
        try:
            if place is not None:
                session.lock.wait(place)
            try:
                self.log.append(("run", request, session_id,
                                 session_id in self.ended, place is not None))
                return step(session)
            finally:
                if place is not None:
                    session.lock.release()
        finally:
            if file:
                self.import_lock.release()

    def sign_out_step(self, session_id: str) -> Callable[[Session], None]:
        def step(session: Session) -> None:
            with self.table:
                self.sessions.pop(session_id, None)
            self.ended.append(session_id)
        return step

    # ------------------------------------------------------------ the pass
    def end_expired(self) -> int:
        self.import_lock.acquire()
        try:
            with self.table:
                reading = self.clock()
                order = sorted(self.sessions.items(), key=lambda kv: kv[1].began)
            count = 0
            for session_id, session in order:
                session.lock.acquire()
                try:
                    with self.table:
                        expired = (session_id in self.sessions
                                   and not session.valid_at(reading))
                        if expired:
                            self.sessions.pop(session_id)
                    if expired:
                        self.ended.append(session_id)
                        self.log.append(("pass_ended", session_id))
                        count += 1
                finally:
                    session.lock.release()
            return count
        finally:
            self.import_lock.release()
