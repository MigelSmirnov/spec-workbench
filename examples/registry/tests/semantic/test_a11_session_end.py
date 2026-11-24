"""Witness tests for accepted decision A11 (02_rules_access.md).

Cabinet Kernel registers a session when its agent session starts and ends it
when it ends; the owner may end any session. Ending is a session's one end and
removes its record — set, active project, pending request, access version —
while the audit entries that name it stay (A11 rules 2, 3). After its end the
session is unregistered, a call naming it refused as for an unregistered
session (rule 4); a registration of the ended identity makes a new, empty
session (rule 4). Each witness test carries the name its Required test
declares.

The Factory project `registry` supplies the ``semantic_runtime`` fixture
(``tests/semantic/RUNTIME_SURFACE.md``): a fresh instance per test, driven
over its two real listeners. Expected values come from State 2 (A10, A11,
A12, M09 by A14), State 5 (`50_public_apis_2_sessions.md`:
`agent_sessions.register_session`, `agent_sessions.check_agent_call`,
`agent_sessions.read_session_access`, `agent_sessions.request_project_access`,
`agent_sessions.list_sessions`, `agent_sessions.grant_project`,
`agent_sessions.end_session`; `50_public_apis_1_foundation.md`:
`audit_log.read_audit_entries`; "Closed set of refusal codes" in
`50_public_apis_0_conventions.md`) and State 6 (`SessionAccessAnswer`/
`SessionAccess`, `SessionEndedAnswer`, `RequestPendingAnswer`,
`SessionListAnswer`, `AuditViewAnswer`/`AuditEntry`/`SessionProjectSubject`,
`RefusedAnswer`; the store table `agent_session_rows` of
`70_persistence_closure.json`; the constants `ACCESS_VERSION_FIRST`,
`REFUSAL_STAGE_*` of `70_data_provider_closure.json`).

Fixture surface used here:

- ``service(name, operation, inputs=None, kernel_session=None)`` -> answer;
- ``owner(action, target=None, stated_version=None, **values)`` -> answer,
  for `create_project`, `read_session`, `list_sessions`, `grant_project`,
  `end_session`, `read_audit`; ``values``: ``request_id``, ``project``,
  ``project_id``, ``make_active``;
- ``new_request_id()``; ``store_rows(table)`` for `agent_session_rows`.
"""

import json
import uuid

# Stage numbers of A04 rule 6 (70_data_provider_closure.json):
# REFUSAL_STAGE_AGENT_SESSION = 2, REFUSAL_STAGE_EXISTENCE = 3.
STAGE_AGENT_SESSION = 2
STAGE_EXISTENCE = 3
# ACCESS_VERSION_FIRST = 1 (70_data_provider_closure.json; A12 rule 1).
ACCESS_VERSION_FIRST = 1

KERNEL = "cabinet_kernel"

# 70_persistence_closure.json: the table of M06 AgentSession rows
# (config.persistence.agent_session_table_name).
SESSION_TABLE = "agent_session_rows"


# --- helpers -----------------------------------------------------------------


def _answered(answer, kind):
    assert answer["answer_kind"] == kind, answer
    return answer


def _refused(answer, code, stage, kinds):
    """A refusal of the closed set (State 5): code, stage, the failing kinds."""
    assert answer["answer_kind"] == "refused", answer
    assert answer["code"] == code, answer
    assert answer["stage"] == stage, answer
    assert sorted(f["kind"] for f in answer["failures"]) == sorted(kinds), answer
    return answer


def _agent_call_refused(answer):
    """The one answer of A10 rule 3: not_found / agent_call_refused, stage
    (2) (State 5 closed set)."""
    return _refused(answer, "not_found", STAGE_AGENT_SESSION, ["agent_call_refused"])


def _create_project(rt, name):
    answer = rt.owner(
        "create_project",
        request_id=rt.new_request_id(),
        project={"display_name": name, "address": f"{name}, Calle Mayor 5"},
    )
    return _answered(answer, "project_card")["card"]["project_id"]


def _session_id(tag):
    return f"a11-{tag}-{uuid.uuid4().hex}"


def _register(rt, session_id):
    return _answered(
        rt.service(KERNEL, "register_agent_session", kernel_session=session_id),
        "session_access",
    )


def _kernel(rt, session_id, operation, **inputs):
    return rt.service(KERNEL, operation, inputs, kernel_session=session_id)


def _owner_access(rt, session_id):
    return _answered(
        rt.owner("read_session", target=session_id), "session_access"
    )["access"]


def _grant(rt, session_id, project_id, make_active=False):
    return _answered(
        rt.owner(
            "grant_project",
            target=session_id,
            stated_version=_owner_access(rt, session_id)["access_version"],
            project_id=project_id,
            make_active=make_active,
        ),
        "session_access",
    )["access"]


def _full_session(rt, session_id, project_id):
    """A registered session with a granted, active project and a pending
    request: every part of the record A11 rule 3 names."""
    _register(rt, session_id)
    _grant(rt, session_id, project_id, make_active=True)
    _answered(
        _kernel(rt, session_id, "request_project_access", request_text="Casa del vecino"),
        "request_pending",
    )
    access = _owner_access(rt, session_id)
    assert access["granted_project_ids"] == [project_id]
    assert access["active_project_id"] == project_id
    assert access["request_pending"] is True
    assert access["access_version"] > ACCESS_VERSION_FIRST
    return access


def _rows_naming(rt, session_id):
    """The session table's rows that name `session_id` in any column."""
    return [
        row
        for row in rt.store_rows(SESSION_TABLE)
        if session_id in json.dumps(row, default=str)
    ]


def _listed_ids(rt):
    listed = _answered(rt.owner("list_sessions"), "session_list")
    return [item["access"]["session_id"] for item in listed["items"]]


# --- Required test 1 ----------------------------------------------------------


def test_ended_session_access_read_refused(semantic_runtime):
    """After Kernel ends a session, reading its access is refused (A11-1)."""
    rt = semantic_runtime
    project_id = _create_project(rt, "Casa Fin")
    session_id = _session_id("ended")
    _full_session(rt, session_id, project_id)

    # Control: while registered, reading its access is answered, and the
    # session table holds its one row.
    _answered(_kernel(rt, session_id, "read_session_access"), "session_access")
    assert len(_rows_naming(rt, session_id)) == 1

    # Kernel ends it, stating no version (A12 rule 3).
    _answered(_kernel(rt, session_id, "end_agent_session"), "session_ended")
    # A11-1 "no record of x remains": no row of the session table names it.
    assert _rows_naming(rt, session_id) == []

    # Now unregistered: the one answer of A10 rule 3, field for field the
    # answer for an identity never registered (A11 rule 4).
    ended = _agent_call_refused(_kernel(rt, session_id, "read_session_access"))
    never = _agent_call_refused(
        _kernel(rt, _session_id("never"), "read_session_access")
    )
    assert ended == never

    # The owner, too, finds no such session: not_found / unknown_session at
    # stage (3) (agent_sessions.read_session_access Errors), and the list
    # holds none.
    _refused(
        rt.owner("read_session", target=session_id),
        "not_found",
        STAGE_EXISTENCE,
        ["unknown_session"],
    )
    assert session_id not in _listed_ids(rt)

    # Ending it again is refused as for an unregistered session (A11 rule 5).
    _agent_call_refused(_kernel(rt, session_id, "end_agent_session"))


# --- Required test 2 ----------------------------------------------------------


def test_reregistered_ended_identity_empty(semantic_runtime):
    """Registering the ended identity again answers a session with no project
    (A11-2)."""
    rt = semantic_runtime
    project_id = _create_project(rt, "Casa Vuelta")
    session_id = _session_id("again")
    before = _full_session(rt, session_id, project_id)

    # Control: registering the living session again answers it unchanged
    # (A11 rule 1, A05) — the emptiness below is the end's, not the
    # registration's.
    repeat = _register(rt, session_id)
    assert repeat["access"] == before
    assert repeat["changed"] is False

    _answered(_kernel(rt, session_id, "end_agent_session"), "session_ended")

    # Kernel's defect: the ended identity registered again makes a new session
    # with an empty set (A11 rule 4; register_session Observable effect): no
    # project, none active, no request, the first access version.
    again = _register(rt, session_id)
    access = again["access"]
    assert access["session_id"] == session_id
    assert access["granted_project_ids"] == []
    assert access["active_project_id"] is None
    assert access["request_pending"] is False
    assert access["access_version"] == ACCESS_VERSION_FIRST
    # A new record was written, not an existing one answered (A05).
    assert again["changed"] is True
    assert _owner_access(rt, session_id) == access

    # The old grant is gone with the old session: its project is outside the
    # new set (A10 rule 3), named or as the active one.
    _agent_call_refused(
        _kernel(rt, session_id, "read_agent_projection", project_id=project_id)
    )
    _agent_call_refused(_kernel(rt, session_id, "read_agent_projection"))


# --- Required test 3 ----------------------------------------------------------


def test_owner_ended_session_call_refused(semantic_runtime):
    """The owner ends a session; its next agent-authority call is refused
    (A11-1)."""
    rt = semantic_runtime
    project_id = _create_project(rt, "Casa Dueno")
    session_id = _session_id("owner-ended")
    other_id = _session_id("other")
    access = _full_session(rt, session_id, project_id)
    _register(rt, other_id)
    _grant(rt, other_id, project_id)

    # Control: the session's call on its project is answered before the end.
    _answered(
        _kernel(rt, session_id, "read_agent_projection", project_id=project_id),
        "agent_projection",
    )

    # Control on the reading: each session has its row before the end.
    assert len(_rows_naming(rt, session_id)) == 1
    assert len(_rows_naming(rt, other_id)) == 1

    # The owner ends it, stating the access version seen (A12 rule 3).
    _answered(
        rt.owner(
            "end_session", target=session_id, stated_version=access["access_version"]
        ),
        "session_ended",
    )
    # A11-1 "no record of x remains": no row of the session table names the
    # ended session; the other keeps its row.
    assert _rows_naming(rt, session_id) == []
    assert len(_rows_naming(rt, other_id)) == 1

    # Every next agent-authority call naming it is refused with the one answer
    # of A10 rule 3: a project call, a write, a session operation.
    _agent_call_refused(
        _kernel(rt, session_id, "read_agent_projection", project_id=project_id)
    )
    _agent_call_refused(
        _kernel(
            rt,
            session_id,
            "add_room",
            project_id=project_id,
            room_name="Cocina",
            request_id=rt.new_request_id(),
        )
    )
    _agent_call_refused(_kernel(rt, session_id, "read_session_access"))
    _agent_call_refused(
        _kernel(rt, session_id, "request_project_access", request_text="otra vez")
    )
    assert session_id not in _listed_ids(rt)

    # The other session holding the same project is untouched.
    _answered(
        _kernel(rt, other_id, "read_agent_projection", project_id=project_id),
        "agent_projection",
    )
    assert other_id in _listed_ids(rt)


# --- Required test 4 ----------------------------------------------------------


def test_ended_session_leaves_no_record(semantic_runtime):
    """After a session ends the store holds no record of it: neither its set,
    its active project, its pending request nor its access version (A11-1)."""
    rt = semantic_runtime
    project_id = _create_project(rt, "Casa Borrada")
    by_kernel = _session_id("by-kernel")
    by_owner = _session_id("by-owner")
    living = _session_id("living")
    _full_session(rt, by_kernel, project_id)
    owner_access = _full_session(rt, by_owner, project_id)
    _full_session(rt, living, project_id)

    # Control on the reading: each session has its row.
    for session_id in (by_kernel, by_owner, living):
        assert len(_rows_naming(rt, session_id)) == 1

    entries_before = _answered(rt.owner("read_audit"), "audit_view")["entries"]

    _answered(_kernel(rt, by_kernel, "end_agent_session"), "session_ended")
    _answered(
        rt.owner(
            "end_session",
            target=by_owner,
            stated_version=owner_access["access_version"],
        ),
        "session_ended",
    )

    # Ending removes the record, by either principal (A11 rules 2, 3): no row
    # of the session table names either ended session — not a row with its
    # set, active project, request or version cleared.
    assert _rows_naming(rt, by_kernel) == []
    assert _rows_naming(rt, by_owner) == []
    # The living session keeps its whole record.
    assert len(_rows_naming(rt, living)) == 1
    living_access = _owner_access(rt, living)
    assert living_access["granted_project_ids"] == [project_id]
    assert living_access["active_project_id"] == project_id
    assert living_access["request_pending"] is True
    assert len(rt.store_rows(SESSION_TABLE)) == 1

    # A11-1 "not registered(x)": a call naming either ended session gets the
    # one answer of A10 rule 3, field for field the answer for an identity
    # never registered (A11 rule 4); the owner finds neither and lists
    # neither. Control: the living session's same call is answered.
    never = _agent_call_refused(
        _kernel(rt, _session_id("never"), "read_session_access")
    )
    for ended_id in (by_kernel, by_owner):
        assert _agent_call_refused(
            _kernel(rt, ended_id, "read_session_access")
        ) == never
        _refused(
            rt.owner("read_session", target=ended_id),
            "not_found",
            STAGE_EXISTENCE,
            ["unknown_session"],
        )
    _answered(_kernel(rt, living, "read_session_access"), "session_access")
    listed = _listed_ids(rt)
    assert by_kernel not in listed and by_owner not in listed
    assert living in listed
    # Reading changed nothing: still only the living session's row.
    assert len(rt.store_rows(SESSION_TABLE)) == 1

    # The audit entries that name an ended session stay (A11 rule 3, M09): the
    # grant of its project is still recorded.
    # Ending writes no entry (A11 rule 6) and removes none: the log is the
    # log read before the two ends.
    entries = _answered(rt.owner("read_audit"), "audit_view")["entries"]
    assert entries == entries_before
    granted_to = {
        entry["subject"].get("session_id")
        for entry in entries
        if entry["action"] == "session_project_granted"
    }
    assert {by_kernel, by_owner, living} <= granted_to
