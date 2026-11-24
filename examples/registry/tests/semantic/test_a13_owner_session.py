"""Witness tests for accepted decision A13 (02_rules_access.md).

The owner signs in with the owner credential and receives an owner session of
bounded life: it ends at the first of 8 hours after sign-in, 30 minutes
without an owner request, the owner's sign-out and the instance's restart;
every duration is measured by the process's monotonic clock, which a change
of the wall clock does not move and which counts a suspension of the host;
a session past a limit serves no request from that moment and the pass ends
it, with its pending confirmation and its upload. Five refused sign-ins less
than 15 minutes old start a 15-minute lockout of the whole instance, during
which every sign-in is refused, the right credential included, uncounted and
without extending it. Every change carries its session's CSRF value; an
action asking for confirmation carries a one-time value of the session that
is used up by the first submission carrying it and expires after 10 minutes.
Each tagged test carries the witness name its Required test declares.

The Factory project `registry` supplies the ``semantic_runtime`` fixture
(``tests/semantic/RUNTIME_SURFACE.md``): a fresh instance per test, driven
over its two real listeners. Expected values come from State 2 (A13, A04
rule 6), State 5 (`50_public_apis_2_sessions.md`:
`owner_sessions.sign_in_owner`, `admit_owner_request`, `sign_out_owner`,
`show_confirmation_step`, `take_confirmation`, `end_expired_sessions`;
`50_public_apis_5_surfaces.md`: `operations.perform_owner_operation`,
`owner_interface.serve_owner_request`, `instance_lifecycle.start_instance`;
"Closed set of refusal codes" in `50_public_apis_0_conventions.md`), State 6
(`SignedInAnswer`, `SignedOutAnswer`, `ConfirmationStepAnswer`,
`ProjectListAnswer`, `ProjectCardAnswer`, `RefusedAnswer`; "The owner
interface's requests and pages" in `60_contracts.md`) and the constants of
`70_data_provider_closure.json`.

Fixture surface used here:

- ``sign_in(credential=…)`` / ``sign_out()`` -> answer; ``owner_session()``
  and ``use_owner_session(s)`` for tests with two sessions (``s.cookie``,
  ``s.csrf``);
- ``owner(action, target=None, stated_version=None, confirm=True,
  **values)`` -> answer, for `list_projects`, `create_project`,
  `read_project`, `correct_project` and `archive_project` (``confirm=False``
  returns the confirmation step); ``owner_confirm(step, value=None)``;
- ``owner(..., csrf=…)``: the CSRF value sent instead of the session's
  (``None`` sends none);
- ``stop()``, ``configure(owner_credential=…)``, ``start()`` and
  ``diagnostics()`` (Required tests 10 and 11);
- ``owner_http(method, path, query=None, form=None, cookie=…)`` -> (status,
  html, headers), for the sign-in page, a raw change without CSRF, the
  session cookie a sign-in sets and the pages a session is shown;
- ``restart()``; ``run_session_pass()`` -> int, how many sessions
  `end_expired_sessions` ended (its State 5 output);
- ``clock.advance``; ``clock.suspend(seconds)``: a host suspension, both
  clocks moved (the monotonic one counts it); ``clock.shift_wall(hours=…)``:
  the recorded (wall) clock alone moved, the monotonic reading unchanged;
- ``new_request_id()``; ``store_rows(table)``, `project_rows` and, in
  Required test 11, every table.

The tests rely on ``owner()`` sending the session the fixture holds (the
last ``sign_in()`` or ``use_owner_session``) as it is, and returning its
refusal when that session is no longer valid; a new session comes only from
``sign_in()`` (RUNTIME_SURFACE.md, "The owner's session").
"""

import json
from html.parser import HTMLParser

# 70_data_provider_closure.json
STAGE_AUTHENTICATION = 1  # REFUSAL_STAGE_AUTHENTICATION
STAGE_VERSION = 5  # REFUSAL_STAGE_VERSION
OWNER_SESSION_MAX_HOURS = 8
OWNER_SESSION_IDLE_MINUTES = 30
SIGN_IN_WINDOW_MINUTES = 15
SIGN_IN_LOCKOUT_MINUTES = 15
SIGN_IN_REFUSAL_LIMIT = 5
CONFIRMATION_VALID_MINUTES = 10
SECRET_MIN_BYTES = 32
# REFUSAL_HTTP_STATUSES: unauthenticated and not_permitted 422;
# SERVICE_ANSWER_STATUS 200.
STATUS_ANSWER = 200
STATUS_UNAUTHENTICATED = 422
STATUS_NOT_PERMITTED = 422
# OWNER_ACTIONS: the sign-in form posts to the sign_in row's path.
SIGN_IN_PATH = "/sign_in"
LIST_PROJECTS_PATH = "/"
CREATE_PROJECT_PATH = "/create_project"
# OWNER_CSRF_FIELD
CSRF_FIELD = "csrf"
# OWNER_SESSION_COOKIE_NAME, OWNER_SESSION_COOKIE_ATTRIBUTES
SESSION_COOKIE_NAME = "__Host-registry_session"
SESSION_COOKIE_ATTRIBUTES = "Secure; HttpOnly; SameSite=Strict; Path=/"
# OwnerRequest.presented_credential: a form field is named by its field's
# name (60_contracts.md, "The owner interface's requests and pages").
CREDENTIAL_FIELD = "presented_credential"
READ_PROJECT_PATH = "/read_project"
# OWNER_TARGET_PARAMETER
TARGET_PARAMETER = "target"

# global_spec.json "persistence": every table of the store.
TABLES = (
    "project_rows",
    "room_rows",
    "customer_rows",
    "pointer_rows",
    "agent_session_rows",
    "audit_entry_rows",
    "migration_closure_rows",
    "audit_sequence_rows",
)

ONE_MICROSECOND = 0.000001  # seconds

# Wrong credentials: not the configured one (the fixture's secrets are
# distinct random values of at least SECRET_MIN_BYTES bytes).
WRONG = "wrong-owner-credential-" + "x" * SECRET_MIN_BYTES
OTHER_WRONG = "another-wrong-credential-" + "y" * SECRET_MIN_BYTES

ADDRESS = "Calle Mayor 1, Valencia"


def _refusal(answer):
    """(code, stage, kinds) of a refused answer (State 5 closed set)."""
    assert answer["answer_kind"] == "refused", answer
    return (
        answer["code"],
        answer["stage"],
        [f["kind"] for f in answer["failures"]],
    )


NO_SESSION = ("unauthenticated", STAGE_AUTHENTICATION, ["no_owner_session"])
SIGN_IN_REFUSED = ("unauthenticated", STAGE_AUTHENTICATION, ["sign_in_refused"])
CSRF_REFUSED = ("not_permitted", STAGE_AUTHENTICATION, ["csrf_refused"])


def _confirmation_refused(kind):
    return ("confirmation_refused", STAGE_AUTHENTICATION, [kind])


def _served(rt):
    """One owner read in the held session; it must be served."""
    answer = rt.owner("list_projects")
    assert answer["answer_kind"] == "project_list", answer
    return answer


def _refused_no_session(rt):
    """One owner read in the held session; refused at the session check."""
    answer = rt.owner("list_projects")
    assert _refusal(answer) == NO_SESSION
    return answer


def _signed_in(answer):
    assert answer["answer_kind"] == "signed_in", answer
    return answer


def _project_facts(display_name):
    # State 6 GivenProjectFacts; display name and address required (A02).
    return {
        "display_name": display_name,
        "alias": None,
        "customer_ref": None,
        "address": ADDRESS,
        "object_kind": None,
        "floor_area": None,
        "rooms_count": None,
        "floor": None,
    }


def _create_project(rt, display_name):
    answer = rt.owner(
        "create_project",
        request_id=rt.new_request_id(),
        project=_project_facts(display_name),
    )
    assert answer["answer_kind"] == "project_card", answer
    return answer["card"]


def _project(rt, project_id):
    answer = rt.owner("read_project", target=project_id)
    assert answer["answer_kind"] == "project_card", answer
    return answer["card"]


def _project_ids(rt):
    return sorted(item["project_id"] for item in _served(rt)["items"])


# --- Required test 1 -------------------------------------------------------


def test_idle_31_minutes_refused(semantic_runtime):
    """A13 rule 2, A13-3: 31 minutes without an owner request ends the
    session; its next request is refused at the session check and the
    interface answers it with the sign-in page; signing in again serves."""
    rt = semantic_runtime
    _signed_in(rt.sign_in())

    # Control: a request after 29 minutes is served and restarts the 30.
    rt.clock.advance(minutes=29)
    _served(rt)
    status, _html, _headers = rt.owner_http("GET", LIST_PROJECTS_PATH)
    assert status == STATUS_ANSWER

    # 31 minutes after the last request (the raw GET above was one).
    rt.clock.advance(minutes=31)
    _refused_no_session(rt)

    # The refusal of stage (1) without a valid session is rendered as the
    # sign-in page (State 5 "Closed set of refusal codes", last paragraph;
    # owner_interface Outputs), its form addressed by OWNER_ACTIONS' sign_in
    # row, with the unauthenticated status of REFUSAL_HTTP_STATUSES.
    status, html, _headers = rt.owner_http("GET", LIST_PROJECTS_PATH)
    assert status == STATUS_UNAUTHENTICATED
    assert SIGN_IN_PATH in html

    # Signing in again gives a session that is served.
    _signed_in(rt.sign_in())
    _served(rt)


# --- Required test 2 -------------------------------------------------------


def test_lockout_refuses_right_credential(semantic_runtime):
    """A13 rule 3, A13-2: five refusals less than 15 minutes old start a
    lockout in which the right credential is refused too, with the same
    answer as a wrong one (rule 4); 15 minutes after the fifth refusal the
    right credential is accepted."""
    rt = semantic_runtime

    # Control 1: refusals that left the 15-minute window are not counted.
    for _ in range(SIGN_IN_REFUSAL_LIMIT - 1):
        assert _refusal(rt.sign_in(credential=WRONG)) == SIGN_IN_REFUSED
    rt.clock.advance(minutes=SIGN_IN_WINDOW_MINUTES)
    assert _refusal(rt.sign_in(credential=WRONG)) == SIGN_IN_REFUSED
    # One refusal in the window: not a lockout.
    _signed_in(rt.sign_in())

    # Control 2: four refusals do not lock (the fifth starts the lockout);
    # the accepted sign-in clears the count, so four more do not lock either.
    for _ in range(2):
        for _ in range(SIGN_IN_REFUSAL_LIMIT - 1):
            assert _refusal(rt.sign_in(credential=WRONG)) == SIGN_IN_REFUSED
        _signed_in(rt.sign_in())

    # Five refusals a minute apart: the fifth starts the lockout, which runs
    # from that refusal, not from the first of the five.
    wrong_answers = []
    for i in range(SIGN_IN_REFUSAL_LIMIT):
        if i:
            rt.clock.advance(minutes=1)
        wrong_answers.append(rt.sign_in(credential=WRONG))
    for answer in wrong_answers:
        assert _refusal(answer) == SIGN_IN_REFUSED

    locked = rt.sign_in()
    assert _refusal(locked) == SIGN_IN_REFUSED
    # Rule 4: one answer whatever was wrong — a lockout tells nothing.
    assert locked == wrong_answers[-1]

    # Still locked a microsecond before 15 minutes after the fifth refusal
    # ("while now is less than 15 minutes after that refusal").
    rt.clock.advance(seconds=SIGN_IN_LOCKOUT_MINUTES * 60 - ONE_MICROSECOND)
    assert _refusal(rt.sign_in()) == SIGN_IN_REFUSED
    # 15 minutes after the fifth refusal: accepted.
    rt.clock.advance(seconds=ONE_MICROSECOND)
    _signed_in(rt.sign_in())
    _served(rt)


# --- Required test 3 (untagged) --------------------------------------------


def test_change_without_session_csrf_refused(semantic_runtime):
    """A13 rule 5: a change carrying no CSRF value, or another session's, is
    refused (`not_permitted`, `csrf_refused`) and creates nothing; the same
    change with its session's value is accepted."""
    rt = semantic_runtime
    _signed_in(rt.sign_in())
    first = rt.owner_session()
    _signed_in(rt.sign_in())
    second = rt.owner_session()
    rt.use_owner_session(first)

    none_sent = rt.owner(
        "create_project",
        request_id=rt.new_request_id(),
        project=_project_facts("Sin CSRF"),
        csrf=None,
    )
    assert _refusal(none_sent) == CSRF_REFUSED

    other_sent = rt.owner(
        "create_project",
        request_id=rt.new_request_id(),
        project=_project_facts("CSRF ajeno"),
        csrf=second.csrf,
    )
    assert _refusal(other_sent) == CSRF_REFUSED

    # The raw form without the CSRF field: refused with not_permitted's
    # status (REFUSAL_HTTP_STATUSES), nothing created.
    raw_form = {
        "request_id": rt.new_request_id(),
        "project.display_name": "Formulario crudo",
        "project.address": ADDRESS,
    }
    status, _html, _headers = rt.owner_http(
        "POST", CREATE_PROJECT_PATH, form=raw_form, cookie=first.cookie
    )
    assert status == STATUS_NOT_PERMITTED

    # Nothing changed: no project, read back and in the store.
    assert _project_ids(rt) == []
    assert rt.store_rows("project_rows") == []

    # Control: the raw form with the session's own CSRF value is accepted.
    status, _html, _headers = rt.owner_http(
        "POST",
        CREATE_PROJECT_PATH,
        form={**raw_form, CSRF_FIELD: first.csrf},
        cookie=first.cookie,
    )
    assert status == STATUS_ANSWER
    # Control: the same change through owner() with the session's value.
    created = _create_project(rt, "Con CSRF")
    assert len(_project_ids(rt)) == 2
    assert created["project_id"] in _project_ids(rt)


# --- Required test 4 -------------------------------------------------------


def test_restart_ends_owner_sessions(semantic_runtime):
    """A13 rule 2, A13-5 ("a restart since s.began"): an owner session is
    never durable; a restart ends every one, a new sign-in serves."""
    rt = semantic_runtime
    _signed_in(rt.sign_in())
    first = rt.owner_session()
    _signed_in(rt.sign_in())
    second = rt.owner_session()

    # Control: both sessions are served before the restart (signing in ends
    # none of the others, rule 2).
    rt.use_owner_session(first)
    _served(rt)
    rt.use_owner_session(second)
    _served(rt)

    rt.restart()

    rt.use_owner_session(first)
    _refused_no_session(rt)
    rt.use_owner_session(second)
    _refused_no_session(rt)

    _signed_in(rt.sign_in())
    _served(rt)


# --- Required test 5 -------------------------------------------------------


def test_lockout_sign_in_not_extending(semantic_runtime):
    """A13 rule 3, A13-2: sign-ins during a lockout are refused, are not
    counted and do not extend it: 15 minutes after the fifth refusal the
    right credential is accepted although sign-ins were refused at 10 and 14
    minutes."""
    rt = semantic_runtime
    for _ in range(SIGN_IN_REFUSAL_LIMIT):
        assert _refusal(rt.sign_in(credential=WRONG)) == SIGN_IN_REFUSED

    rt.clock.advance(minutes=10)
    assert _refusal(rt.sign_in()) == SIGN_IN_REFUSED
    rt.clock.advance(minutes=4)
    # Wrong ones during the lockout: had they been counted, five refusals
    # would lie in the window at minute 15 (minutes 10 to 14) and start a
    # new lockout; had they extended it, it would last to minute 29.
    for _ in range(SIGN_IN_REFUSAL_LIMIT):
        assert _refusal(rt.sign_in(credential=OTHER_WRONG)) == SIGN_IN_REFUSED

    rt.clock.advance(minutes=1)  # 15 minutes after the fifth refusal
    _signed_in(rt.sign_in())
    _served(rt)


# --- Required test 6 (untagged) --------------------------------------------


def test_confirmation_value_used_once_and_expires(semantic_runtime):
    """A13 rule 6: a confirmation value is used up by the first submission
    carrying it, accepted or refused; another value leaves the pending one;
    one shown 10 minutes ago is expired and cleared."""
    rt = semantic_runtime
    _signed_in(rt.sign_in())

    # Used by an accepted submission, refused the second time.
    project = _create_project(rt, "Archivo uno")
    step = rt.owner(
        "archive_project",
        target=project["project_id"],
        stated_version=project["revision"],
        confirm=False,
    )
    assert step["answer_kind"] == "confirmation_step", step
    assert step["action"] == "archive_project"
    # Another value while the pending one is valid: refused, pending kept.
    other = rt.owner_confirm(step, value="z" * (2 * SECRET_MIN_BYTES))
    assert _refusal(other) == _confirmation_refused("confirmation_other_value")
    accepted = rt.owner_confirm(step)
    assert accepted["answer_kind"] == "project_card", accepted
    assert accepted["card"]["status"] == "archived"
    again = rt.owner_confirm(step)
    assert _refusal(again) == _confirmation_refused("confirmation_not_pending")
    assert _project(rt, project["project_id"])["revision"] == (
        project["revision"] + 1
    )

    # Used by a refused submission: the step showed revision 1, a correction
    # moved it to 2, so the confirmed archive is refused stale (stage 5,
    # after the confirmation was taken at stage 1) — and the value is gone.
    project = _create_project(rt, "Archivo dos")
    step = rt.owner(
        "archive_project",
        target=project["project_id"],
        stated_version=project["revision"],
        confirm=False,
    )
    corrected = rt.owner(
        "correct_project",
        target=project["project_id"],
        stated_version=project["revision"],
        project=_project_facts("Archivo dos, corregido"),
    )
    assert corrected["answer_kind"] == "project_card", corrected
    stale = rt.owner_confirm(step)
    assert _refusal(stale) == ("stale", STAGE_VERSION, ["stale_revision"])
    again = rt.owner_confirm(step)
    assert _refusal(again) == _confirmation_refused("confirmation_not_pending")
    assert _project(rt, project["project_id"])["status"] == "active"
    # Control: a step shown again at the current revision is accepted.
    current = _project(rt, project["project_id"])
    archived = rt.owner(
        "archive_project",
        target=project["project_id"],
        stated_version=current["revision"],
    )
    assert archived["card"]["status"] == "archived"

    # Expiry: valid less than 10 minutes after it was shown.
    project = _create_project(rt, "Archivo tres")
    step = rt.owner(
        "archive_project",
        target=project["project_id"],
        stated_version=project["revision"],
        confirm=False,
    )
    rt.clock.advance(minutes=CONFIRMATION_VALID_MINUTES)
    expired = rt.owner_confirm(step)
    assert _refusal(expired) == _confirmation_refused("confirmation_expired")
    # Cleared: the same value is now not pending.
    again = rt.owner_confirm(step)
    assert _refusal(again) == _confirmation_refused("confirmation_not_pending")
    assert _project(rt, project["project_id"])["status"] == "active"

    # Control: a microsecond before 10 minutes it is accepted.
    step = rt.owner(
        "archive_project",
        target=project["project_id"],
        stated_version=project["revision"],
        confirm=False,
    )
    rt.clock.advance(seconds=CONFIRMATION_VALID_MINUTES * 60 - ONE_MICROSECOND)
    accepted = rt.owner_confirm(step)
    assert accepted["answer_kind"] == "project_card", accepted
    assert accepted["card"]["status"] == "archived"


# --- Required test 7 -------------------------------------------------------


def test_eight_hours_and_sign_out_refused(semantic_runtime):
    """A13 rule 2, A13-1, A13-4: a session kept busy every 10 minutes is served
    until a microsecond before 8 hours after its sign-in and refused at 8
    hours; a signed-out session is refused at its next request within its 30
    minutes, while another open session goes on."""
    rt = semantic_runtime
    _signed_in(rt.sign_in())

    elapsed = 0
    while elapsed + 10 < OWNER_SESSION_MAX_HOURS * 60:
        rt.clock.advance(minutes=10)
        elapsed += 10
        _served(rt)
    assert elapsed == 470
    rt.clock.advance(seconds=10 * 60 - ONE_MICROSECOND)
    _served(rt)  # 7 h 59 min 59.999999 s after sign-in
    rt.clock.advance(seconds=ONE_MICROSECOND)
    _refused_no_session(rt)  # exactly 8 hours: A13-1, "t >= began + 8h"

    # Sign-out.
    _signed_in(rt.sign_in())
    leaving = rt.owner_session()
    _signed_in(rt.sign_in())
    staying = rt.owner_session()
    rt.use_owner_session(leaving)
    rt.clock.advance(minutes=5)
    _served(rt)
    signed_out = rt.sign_out()
    assert signed_out["answer_kind"] == "signed_out", signed_out
    rt.clock.advance(minutes=1)  # well within its 30 minutes
    _refused_no_session(rt)
    # A second sign-out of the ended session is refused too (State 5
    # admit_owner_request: it finds the session marked signed out).
    assert _refusal(rt.sign_out()) == NO_SESSION
    # Control: the other session is untouched by the sign-out.
    rt.use_owner_session(staying)
    _served(rt)


# --- Required test 8 -------------------------------------------------------


def test_idle_limit_boundary_exclusive(semantic_runtime):
    """A13-3 ("t >= s.last_request + 30min"), A13-6: a request a microsecond before
    30 minutes after the last one is served and restarts the 30; one exactly
    30 minutes after the last is refused."""
    rt = semantic_runtime
    _signed_in(rt.sign_in())
    _served(rt)

    rt.clock.advance(seconds=OWNER_SESSION_IDLE_MINUTES * 60 - ONE_MICROSECOND)
    _served(rt)  # restarts the 30 minutes from here

    # Had the served request not restarted the 30, this would be refused.
    rt.clock.advance(minutes=OWNER_SESSION_IDLE_MINUTES - 1)
    _served(rt)

    rt.clock.advance(minutes=OWNER_SESSION_IDLE_MINUTES)
    _refused_no_session(rt)


# --- Required test 9 -------------------------------------------------------


def test_monotonic_clock_decides_validity(semantic_runtime):
    """A13 rule 2, A13-3, A13-6: the limits are measured by the monotonic
    reading alone. Moving the wall clock back or forward by hours changes no
    session's validity; 31 minutes counted by the monotonic reading — a host
    suspension, which that reading counts — make the next request refused, a
    submission of its pending confirmation included; the next pass ends that
    session and no other. (What the pass drops with the ended session — its
    confirmation and upload — no request can ask about: Required test 9 no
    longer claims it.)"""
    rt = semantic_runtime
    _signed_in(rt.sign_in())
    project = _create_project(rt, "Reloj")

    # Wall clock back by 5 hours: an implementation timing the idle limit
    # by the wall clock would see the next 31 monotonic minutes as 4 h 29
    # min in the past and serve the session.
    rt.clock.shift_wall(hours=-5)
    rt.clock.advance(minutes=1)
    _served(rt)

    # Wall clock forward by 12 hours: by the wall, 7 hours past the
    # sign-in's 8 hour limit and far past the idle one; by the monotonic
    # reading 2 minutes since sign-in.
    rt.clock.shift_wall(hours=12)
    rt.clock.advance(minutes=1)
    _served(rt)

    # The session holds a pending confirmation.
    step = rt.owner(
        "archive_project",
        target=project["project_id"],
        stated_version=project["revision"],
        confirm=False,
    )
    assert step["answer_kind"] == "confirmation_step", step
    suspended = rt.owner_session()

    # A suspension of 31 minutes: the monotonic reading counts it, so from
    # the process's side both clocks move by 31 minutes (A13 rule 2: "counts
    # the time the host or its VM was suspended"; RUNTIME_SURFACE.md
    # `clock.suspend`). Then the wall clock back by 3 hours: a wall-clock
    # implementation would see -2 h 29 min.
    rt.clock.suspend(31 * 60)
    rt.clock.shift_wall(hours=-3)
    _refused_no_session(rt)
    refused_confirmation = rt.owner_confirm(step)
    assert _refusal(refused_confirmation) == NO_SESSION

    # Control: a session signed in now is valid; the pass leaves it.
    _signed_in(rt.sign_in())
    fresh = rt.owner_session()
    ended = rt.run_session_pass()
    # end_expired_sessions answers how many sessions it ended (State 5): the
    # suspended one alone.
    assert ended == 1
    assert rt.run_session_pass() == 0
    _served(rt)

    rt.use_owner_session(suspended)
    _refused_no_session(rt)
    rt.use_owner_session(fresh)
    # The confirmation the ended session held changed nothing.
    assert _project(rt, project["project_id"])["status"] == "active"


def test_refused_change_restarts_idle(semantic_runtime):
    """A13 rule 2: every request carrying the valid session restarts its 30
    minutes, whatever its answer — a change refused for its CSRF value
    included (State 5 admit_owner_request)."""
    rt = semantic_runtime
    _signed_in(rt.sign_in())
    rt.clock.advance(minutes=20)
    refused = rt.owner(
        "create_project",
        request_id=rt.new_request_id(),
        project=_project_facts("Sin CSRF"),
        csrf=None,
    )
    assert _refusal(refused) == CSRF_REFUSED
    rt.clock.advance(minutes=20)  # 40 since sign-in, 20 since the refusal
    _served(rt)
    rt.clock.advance(minutes=OWNER_SESSION_IDLE_MINUTES)
    _refused_no_session(rt)


# --- Required test 10 (untagged) -------------------------------------------


def _header_items(headers):
    return headers.items() if hasattr(headers, "items") else headers


def _set_cookies(headers):
    return [v for k, v in _header_items(headers) if k.lower() == "set-cookie"]


def _cookie_parts(set_cookie):
    """(name, value, attributes) of one Set-Cookie value; attribute names are
    case-insensitive (RFC 6265), so they are compared in lower case."""
    first, *attributes = [part.strip() for part in set_cookie.split(";")]
    name, _, value = first.partition("=")
    return name, value, sorted(a.lower() for a in attributes if a)


def test_sign_in_sets_session_cookie_attributes(semantic_runtime):
    """A13 Required test 10: signing in sets the session cookie
    OWNER_SESSION_COOKIE_NAME with the attributes
    OWNER_SESSION_COOKIE_ATTRIBUTES and no other — Secure, HttpOnly,
    SameSite=Strict, Path=/, no Domain — and a refused sign-in sets none
    (A13 rules 1, 4; 60_contracts.md "The owner's pages"). That a browser
    then sends it only over HTTPS from another machine is the cookie's
    `Secure` and the deployment's, carried (A13 rule 7)."""
    rt = semantic_runtime
    credential = "a13-owner-credential-" + "c" * SECRET_MIN_BYTES
    rt.stop()
    rt.configure(owner_credential=credential)
    assert rt.start() is None

    # A refused sign-in sets no cookie.
    status, html, headers = rt.owner_http(
        "POST", SIGN_IN_PATH, form={CREDENTIAL_FIELD: WRONG}, cookie=None
    )
    assert status == STATUS_UNAUTHENTICATED
    assert _set_cookies(headers) == []
    assert WRONG not in html  # never echoes the credential (rule 4)

    status, html, headers = rt.owner_http(
        "POST", SIGN_IN_PATH, form={CREDENTIAL_FIELD: credential}, cookie=None
    )
    assert status == STATUS_ANSWER
    (set_cookie,) = _set_cookies(headers)
    name, value, attributes = _cookie_parts(set_cookie)
    assert name == SESSION_COOKIE_NAME
    assert value
    assert attributes == sorted(
        a.strip().lower() for a in SESSION_COOKIE_ATTRIBUTES.split(";")
    ), set_cookie
    assert not any(a.startswith("domain") for a in attributes)
    # The identity travels only in the cookie: not in the page (rule 7).
    assert value not in html
    assert credential not in html


# --- Required test 11 (untagged) -------------------------------------------


class _Page(HTMLParser):
    """Where a value stands in a page: its text, its URLs (href, action,
    src) and its form inputs' values."""

    def __init__(self, html):
        super().__init__()
        self.texts, self.urls, self.input_values, self.other_attributes = [], [], [], []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if value is None:
                continue
            if name in ("href", "action", "src", "formaction"):
                self.urls.append(value)
            elif tag == "input" and name == "value":
                self.input_values.append(value)
            else:
                self.other_attributes.append(value)

    handle_startendtag = handle_starttag

    def handle_data(self, data):
        self.texts.append(data)


def _identity(cookie):
    """The session identity the held cookie carries (a bare value, or
    `name=value`)."""
    text = str(cookie)
    prefix = SESSION_COOKIE_NAME + "="
    return text[len(prefix):].split(";")[0] if text.startswith(prefix) else text


def test_session_values_never_in_url_log_or_record(semantic_runtime):
    """A13 Required test 11: the session's identity, its CSRF value and a
    shown confirmation value appear in no URL of a page the interface serves,
    in no diagnostic and in no stored row, the audit entries among them; the
    identity is not in a page, and the CSRF and confirmation values only in
    its forms (A13 rule 7). Constant-time comparison and the random source
    are not observable here and are carried (A13 rule 7)."""
    rt = semantic_runtime
    _signed_in(rt.sign_in())
    session = rt.owner_session()
    identity = _identity(session.cookie)
    csrf = session.csrf
    assert identity and csrf and identity != csrf

    card = _create_project(rt, "Valores")
    step = rt.owner(
        "archive_project",
        target=card["project_id"],
        stated_version=card["revision"],
        confirm=False,
    )
    assert step["answer_kind"] == "confirmation_step", step
    confirmation = step["confirmation_value"]
    assert confirmation not in (identity, csrf)
    values = {"identity": identity, "csrf": csrf, "confirmation": confirmation}

    pages = [(LIST_PROJECTS_PATH, None), (READ_PROJECT_PATH, {TARGET_PARAMETER: card["project_id"]})]
    for path, query in pages:
        status, html, headers = rt.owner_http("GET", path, query=query)
        assert status == STATUS_ANSWER, path
        page = _Page(html)
        for label, value in values.items():
            assert not any(value in url for url in page.urls), (path, label)
            assert not any(value in text for text in page.texts), (path, label)
            assert not any(value in a for a in page.other_attributes), (path, label)
            for _, header in _header_items(headers):
                if label != "identity":
                    assert value not in header, (path, label)
        assert identity not in html, path
        # Only in a form's input, when the page carries it at all.
        assert all(csrf not in v or v == csrf for v in page.input_values), path

    archived = rt.owner_confirm(step)
    assert archived["answer_kind"] == "project_card", archived
    assert archived["card"]["status"] == "archived"

    lines = rt.diagnostics()
    rows = json.dumps({table: rt.store_rows(table) for table in TABLES}, default=str)
    for label, value in values.items():
        assert not any(value in line for line in lines), label
        assert value not in rows, label
