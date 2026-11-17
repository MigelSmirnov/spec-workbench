"""Two candidate designs of an owner request's arrival (State 5 round-38 T7).

A — arrival after the head (an A13 clarification): owner_interface reads the
    bounded head first; the session is checked, at the clock's reading then,
    when the request is admitted. One step, no state between.
B — two-phase admission (A13 unchanged): the session is checked when the
    request's headers arrive and the request takes a ticket; the CSRF value is
    checked later, at admission. While a ticket is pending, neither the pass
    nor a sign-out may remove the session.

Only the arrival/limit/sign-out logic is modelled; locks are omitted.
"""
from __future__ import annotations

from dataclasses import dataclass, field

IDLE = 30 * 60
MAX_AGE = 8 * 3600


class Refused(Exception):
    pass


@dataclass
class Session:
    began: float
    last_request: float
    csrf: str
    signed_out: bool = False
    pending: int = 0           # design B only
    ended: bool = False

    def valid_at(self, reading: float) -> bool:
        return (not self.signed_out and not self.ended
                and reading < self.began + MAX_AGE
                and reading < self.last_request + IDLE)


@dataclass
class SessionsA:
    sessions: dict[str, Session] = field(default_factory=dict)

    def admit(self, session_id: str, csrf: str | None, now: float) -> None:
        session = self.sessions.get(session_id)
        if session is None or not session.valid_at(now):
            raise Refused("session")
        session.last_request = max(session.last_request, now)
        if csrf != session.csrf:
            raise Refused("csrf")

    def run_pass(self, now: float) -> None:
        for key, session in list(self.sessions.items()):
            if not session.valid_at(now):
                del self.sessions[key]

    def sign_out(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)


@dataclass
class Ticket:
    session_id: str


@dataclass
class SessionsB:
    sessions: dict[str, Session] = field(default_factory=dict)

    def arrive(self, session_id: str, now: float) -> Ticket:
        session = self.sessions.get(session_id)
        if session is None or not session.valid_at(now):
            raise Refused("session")
        session.last_request = max(session.last_request, now)
        session.pending += 1
        return Ticket(session_id)

    def admit(self, ticket: Ticket, csrf: str | None) -> None:
        session = self.sessions[ticket.session_id]   # pinned: still there
        try:
            if csrf != session.csrf:
                raise Refused("csrf")
        finally:
            session.pending -= 1
            self._drop_if_ended(ticket.session_id)

    def run_pass(self, now: float) -> None:
        for key, session in list(self.sessions.items()):
            if not session.valid_at(now):
                session.ended = True
                self._drop_if_ended(key)

    def sign_out(self, session_id: str) -> None:
        session = self.sessions.get(session_id)
        if session is not None:
            session.signed_out = True
            self._drop_if_ended(session_id)

    def _drop_if_ended(self, key: str) -> None:
        session = self.sessions[key]
        if (session.ended or session.signed_out) and session.pending == 0:
            del self.sessions[key]
