"""Witness tests for accepted decision A10 (02_rules_access.md).

A call with agent authority is accepted only when the token is Cabinet
Kernel's, the session it names is registered and, for an operation on a
project, the project is in that session's set; 'register an agent session' is
checked for the token only (A10 rule 1). A call naming no project uses the
session's active project and is refused with none active (rule 2). Every
refusal of the set check, an unregistered session and a project that does not
exist are one answer (rule 3). A write on an archived project of the set is
refused, its reads answered (rule 4). The check is made at every call, so a
revocation holds from the next call (rules 5, 6). Each witness test carries
the name its Required test declares; Required tests 3 to 5, untagged, have
tests named by what they show.

The Factory project `registry` supplies the ``semantic_runtime`` fixture
(``tests/semantic/RUNTIME_SURFACE.md``): a fresh instance per test, driven
over its two real listeners. Expected values come from State 2 (A10, A11,
A12), State 5 (`50_public_apis_5_surfaces.md`:
`operations.perform_service_operation`; `50_public_apis_2_sessions.md`:
`agent_sessions.register_session`, `agent_sessions.check_agent_call`,
`agent_sessions.grant_project`, `agent_sessions.set_active_project`,
`agent_sessions.revoke_project`; `50_public_apis_3_records.md`:
`projects.read_agent_view`, `projects.add_room`, `projects.list_rooms`,
`projects.archive_project`; "Closed set of refusal codes" in
`50_public_apis_0_conventions.md`) and State 6 (`SessionAccessAnswer`/
`SessionAccess`, `AgentProjectionAnswer`/`AgentProject`, `RoomAnswer`,
`RoomsAnswer`, `ProjectCardAnswer`, `RefusedAnswer`; the constants
`ACCESS_VERSION_FIRST`, `REFUSAL_STAGE_*` of
`70_data_provider_closure.json`).

Fixture surface used here:

- ``service(name, operation, inputs=None, kernel_session=None)`` -> answer;
- ``owner(action, target=None, stated_version=None, confirm=True,
  **values)`` -> answer, for `create_project`, `read_project`,
  `archive_project` (confirmed), `read_session`, `grant_project`,
  `set_active_project`, `revoke_project`; ``values``: ``request_id``,
  ``project``, ``project_id``, ``make_active``;
- ``new_request_id()``; ``store_rows(table)`` for `room_rows`.
"""

import uuid

# Stage numbers of A04 rule 6 (70_data_provider_closure.json):
# REFUSAL_STAGE_AUTHENTICATION = 1, REFUSAL_STAGE_AGENT_SESSION = 2,
# REFUSAL_STAGE_LIFECYCLE = 6.
STAGE_AUTHENTICATION = 1
STAGE_AGENT_SESSION = 2
STAGE_LIFECYCLE = 6
# ACCESS_VERSION_FIRST = 1 (70_data_provider_closure.json; A12 rule 1).
ACCESS_VERSION_FIRST = 1

KERNEL = "cabinet_kernel"
CLIENT_PORTAL = "client_portal"
CABINET = "cabinet"


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
    """The one answer of A10 rule 3: not_found / agent_call_refused, always
    stage (2) (State 5 closed set)."""
    return _refused(answer, "not_found", STAGE_AGENT_SESSION, ["agent_call_refused"])


def _create_project(rt, name, alias=None):
    project = {"display_name": name, "address": f"{name}, Calle Mayor 3"}
    if alias is not None:
        project["alias"] = alias
    answer = rt.owner(
        "create_project", request_id=rt.new_request_id(), project=project
    )
    return _answered(answer, "project_card")["card"]


def _register(rt):
    session_id = f"a10-{uuid.uuid4().hex}"
    _answered(
        rt.service(KERNEL, "register_agent_session", kernel_session=session_id),
        "session_access",
    )
    return session_id


def _access(rt, session_id):
    return _answered(
        rt.owner("read_session", target=session_id), "session_access"
    )["access"]


def _grant(rt, session_id, project_id, make_active=False):
    answer = rt.owner(
        "grant_project",
        target=session_id,
        stated_version=_access(rt, session_id)["access_version"],
        project_id=project_id,
        make_active=make_active,
    )
    return _answered(answer, "session_access")["access"]


def _kernel(rt, session_id, operation, **inputs):
    return rt.service(KERNEL, operation, inputs, kernel_session=session_id)


def _room_names(rt, project_id):
    card = _answered(rt.owner("read_project", target=project_id), "project_card")["card"]
    return sorted(room["name"] for room in card["rooms"])


# --- Required test 1 ----------------------------------------------------------


def test_outside_set_answered_as_not_found(semantic_runtime):
    """Kernel reading the projection of a project outside the set receives the
    not-found answer, identical to that of a random id (A10-1, A10-2)."""
    rt = semantic_runtime
    inside = _create_project(rt, "Casa Dentro", alias="dentro")["project_id"]
    outside = _create_project(rt, "Casa Fuera", alias="fuera")["project_id"]
    session_id = _register(rt)
    _grant(rt, session_id, inside)

    # Control: the project of the set is answered (A10 rule 1).
    projection = _answered(
        _kernel(rt, session_id, "read_agent_projection", project_id=inside),
        "agent_projection",
    )
    assert projection["view"]["project_id"] == inside

    # A project that exists outside the set and an id no project has: one
    # answer, not_found / agent_call_refused at stage (2) (A10 rule 3, State
    # 5 closed set), equal field for field — stage and path included.
    outside_answer = _agent_call_refused(
        _kernel(rt, session_id, "read_agent_projection", project_id=outside)
    )
    random_answer = _agent_call_refused(
        _kernel(rt, session_id, "read_agent_projection", project_id=str(uuid.uuid4()))
    )
    assert outside_answer == random_answer
    assert "fuera" not in repr(outside_answer)

    # The project outside the set does exist (control on the setup): another
    # service may validate it.
    validation = rt.service(CABINET, "validate_project_reference", {"project_id": outside})
    _answered(validation, "validation")
    # The bare view, as the wire carries it (R0-04; RUNTIME_SURFACE.md).
    assert validation["exists"] is True

    # A10-1's other conjunct: a session that is not registered gets the same
    # answer, even for a project that is in another session's set (A10 rule
    # 3: "a call naming an unregistered session is answered as a call outside
    # the set").
    unregistered = _agent_call_refused(
        _kernel(rt, f"a10-never-{uuid.uuid4().hex}", "read_agent_projection", project_id=inside)
    )
    assert unregistered == random_answer

    # The token is part of the check (A10 rule 1): another service's token
    # naming the same session and project is refused at stage (1), its row
    # lacking the operation (A09 rule 3).
    _refused(
        rt.service(
            CLIENT_PORTAL,
            "read_agent_projection",
            {"project_id": inside},
            kernel_session=session_id,
        ),
        "not_permitted",
        STAGE_AUTHENTICATION,
        ["outside_service_rights"],
    )


# --- Required test 2 ----------------------------------------------------------


def test_revoked_project_next_call_refused(semantic_runtime):
    """After the owner revokes a project, the next 'add a room' on it is
    refused (A10-1; rules 5, 6)."""
    rt = semantic_runtime
    project_id = _create_project(rt, "Casa Revocada")["project_id"]
    kept_id = _create_project(rt, "Casa Guardada")["project_id"]
    session_id = _register(rt)
    _grant(rt, session_id, project_id)
    _grant(rt, session_id, kept_id)

    # Control: before the revocation 'add a room' is accepted.
    _answered(
        _kernel(
            rt,
            session_id,
            "add_room",
            project_id=project_id,
            room_name="Cocina",
            request_id=rt.new_request_id(),
        ),
        "room",
    )

    access = _access(rt, session_id)
    revoked = _answered(
        rt.owner(
            "revoke_project",
            target=session_id,
            stated_version=access["access_version"],
            project_id=project_id,
        ),
        "session_access",
    )["access"]
    assert project_id not in revoked["granted_project_ids"]

    # The very next call is checked against the changed set: the one answer of
    # A10 rule 3, and no room is written.
    _agent_call_refused(
        _kernel(
            rt,
            session_id,
            "add_room",
            project_id=project_id,
            room_name="Bano",
            request_id=rt.new_request_id(),
        )
    )
    assert _room_names(rt, project_id) == ["Cocina"]
    assert len(rt.store_rows("room_rows")) == 1

    # A read of the revoked project is refused the same way (rule 5: every
    # call is checked).
    _agent_call_refused(
        _kernel(rt, session_id, "read_agent_projection", project_id=project_id)
    )

    # The revocation removed that project only: the other one of the set is
    # still written to.
    _answered(
        _kernel(
            rt,
            session_id,
            "add_room",
            project_id=kept_id,
            room_name="Salon",
            request_id=rt.new_request_id(),
        ),
        "room",
    )
    assert _room_names(rt, kept_id) == ["Salon"]


# --- Required test 3 (untagged) ----------------------------------------------


def test_no_project_named_and_none_active_refused(semantic_runtime):
    """A call naming no project, with no active project, is refused (A10 rule
    2); with one active, the same call acts on it."""
    rt = semantic_runtime
    project_id = _create_project(rt, "Casa Activa", alias="activa")["project_id"]
    session_id = _register(rt)
    _grant(rt, session_id, project_id, make_active=False)

    # Granted but not active: naming no project is refused with the one answer
    # of rule 3 ("none active" is listed in agent_call_refused).
    no_active = _agent_call_refused(_kernel(rt, session_id, "read_agent_projection"))
    _agent_call_refused(
        _kernel(rt, session_id, "add_room", room_name="Cocina", request_id=rt.new_request_id())
    )
    assert rt.store_rows("room_rows") == []
    # One answer with a project outside the set (A10 rule 3).
    assert no_active == _agent_call_refused(
        _kernel(rt, session_id, "read_agent_projection", project_id=str(uuid.uuid4()))
    )

    # Control: made active, the same calls naming no project act on it.
    _answered(
        rt.owner(
            "set_active_project",
            target=session_id,
            stated_version=_access(rt, session_id)["access_version"],
            project_id=project_id,
        ),
        "session_access",
    )
    projection = _answered(
        _kernel(rt, session_id, "read_agent_projection"), "agent_projection"
    )
    assert projection["view"]["project_id"] == project_id
    _answered(
        _kernel(rt, session_id, "add_room", room_name="Cocina", request_id=rt.new_request_id()),
        "room",
    )
    assert _room_names(rt, project_id) == ["Cocina"]


# --- Required test 4 (untagged) ----------------------------------------------


def test_add_room_on_archived_project_of_set_refused(semantic_runtime):
    """'Add a room' on an archived project of the set is refused; its reads
    are answered (A10 rule 4, R0-12, R0-70)."""
    rt = semantic_runtime
    card = _create_project(rt, "Casa Archivada", alias="archivada")
    project_id = card["project_id"]
    session_id = _register(rt)
    _grant(rt, session_id, project_id)

    # Control: on the active project the write is accepted.
    _answered(
        _kernel(
            rt,
            session_id,
            "add_room",
            project_id=project_id,
            room_name="Cocina",
            request_id=rt.new_request_id(),
        ),
        "room",
    )

    archived = _answered(
        rt.owner("archive_project", target=project_id, stated_version=card["revision"]),
        "project_card",
    )["card"]
    assert archived["status"] == "archived"
    # Archiving keeps every session's set (archive_project Enforces, R0-70).
    assert _access(rt, session_id)["granted_project_ids"] == [project_id]

    # The write is refused for the archived project: stage (6), `archived`
    # (projects.add_room Errors), past the session's check it passed.
    _refused(
        _kernel(
            rt,
            session_id,
            "add_room",
            project_id=project_id,
            room_name="Bano",
            request_id=rt.new_request_id(),
        ),
        "refused",
        STAGE_LIFECYCLE,
        ["archived"],
    )
    assert _room_names(rt, project_id) == ["Cocina"]
    assert len(rt.store_rows("room_rows")) == 1

    # Reads of it are answered.
    projection = _answered(
        _kernel(rt, session_id, "read_agent_projection", project_id=project_id),
        "agent_projection",
    )
    assert projection["view"]["status"] == "archived"
    assert [room["name"] for room in projection["view"]["rooms"]] == ["Cocina"]
    _answered(_kernel(rt, session_id, "list_rooms", project_id=project_id), "rooms")


# --- Required test 5 (untagged) ----------------------------------------------


def test_kernel_registers_new_session_id(semantic_runtime):
    """Kernel registers a new session id and is accepted: the registration is
    checked for the token only (A10 rule 1, A11 rule 1)."""
    rt = semantic_runtime
    session_id = f"a10-new-{uuid.uuid4().hex}"

    # Before its registration the id is an unregistered session.
    _agent_call_refused(_kernel(rt, session_id, "read_session_access"))

    registered = _answered(
        rt.service(KERNEL, "register_agent_session", kernel_session=session_id),
        "session_access",
    )
    # A new session (agent_sessions.register_session Observable effect): the
    # id as Kernel gave it, empty set, no active project, no request, access
    # version ACCESS_VERSION_FIRST.
    access = registered["access"]
    assert access["session_id"] == session_id
    assert access["granted_project_ids"] == []
    assert access["active_project_id"] is None
    assert access["request_pending"] is False
    assert access["access_version"] == ACCESS_VERSION_FIRST
    assert registered["changed"] is True

    # It is now registered: its own operations are answered.
    read = _answered(_kernel(rt, session_id, "read_session_access"), "session_access")
    assert read["access"] == access

    # The token is checked: another service naming a new id is refused at
    # stage (1), and registers nothing.
    other_id = f"a10-other-{uuid.uuid4().hex}"
    _refused(
        rt.service(CABINET, "register_agent_session", kernel_session=other_id),
        "not_permitted",
        STAGE_AUTHENTICATION,
        ["outside_service_rights"],
    )
    _agent_call_refused(_kernel(rt, other_id, "read_session_access"))
    listed = _answered(rt.owner("list_sessions"), "session_list")
    assert [item["access"]["session_id"] for item in listed["items"]] == [session_id]
