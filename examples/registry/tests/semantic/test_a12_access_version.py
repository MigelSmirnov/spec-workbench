"""Witness tests for accepted decision A12 (02_rules_access.md).

A session's access version is ACCESS_VERSION_FIRST at registration and moves
by one with each accepted action that changes its granted set, its active
project or its pending request — a project's erasure included — once per
action however many of them it changes (A12 rule 1); a change that changes
nothing leaves it (rule 2). The owner's actions on a session state the version
the owner saw, a stale one refused with nothing changed (rule 3); Kernel's
'request access' states none and always moves it (rule 4); 'read the
session's access' answers it (rule 5). Each witness test carries the name its
Required test declares; Required test 3, untagged, has a test named by what it
shows.

The Factory project `registry` supplies the ``semantic_runtime`` fixture
(``tests/semantic/RUNTIME_SURFACE.md``): a fresh instance per test, driven
over its two real listeners. Expected values come from State 1 (M06), State 2
(A05, A11, A12, R0-61), State 5 (`50_public_apis_2_sessions.md`:
`agent_sessions.register_session`, `agent_sessions.request_project_access`,
`agent_sessions.read_session_access`, `agent_sessions.list_sessions`,
`agent_sessions.answer_access_request`, `agent_sessions.grant_project`,
`agent_sessions.set_active_project`, `agent_sessions.end_session`,
`agent_sessions.drop_project_from_sessions`; `50_public_apis_3_records.md`:
`projects.archive_project`, `projects.erase_project`; "Closed set of refusal
codes" in `50_public_apis_0_conventions.md`) and State 6
(`SessionAccessAnswer`/`SessionAccess`, `SessionListAnswer`/
`SessionListItem`, `AccessAnswer`/`GrantAnswer`, `SessionEndedAnswer`,
`ProjectErasedAnswer`, `RefusedAnswer`; the store table `agent_session_rows`
of `70_persistence_closure.json`; the constants `ACCESS_VERSION_FIRST`,
`REFUSAL_STAGE_*` of `70_data_provider_closure.json`).

Fixture surface used here:

- ``service(name, operation, inputs=None, kernel_session=None)`` -> answer;
- ``owner(action, target=None, stated_version=None, confirm=True,
  **values)`` -> answer, for `create_project`, `archive_project` and
  `erase_project` (confirmed), `read_session`, `list_sessions`,
  `answer_access_request`, `grant_project`, `set_active_project`,
  `end_session`; ``values``: ``request_id``, ``project``, ``project_id``,
  ``make_active``, ``access_answer`` (an `AccessAnswer` dict), ``erasure``;
- ``new_request_id()``; ``store_rows(table)`` for `agent_session_rows`.
"""

import json
import uuid

# Stage numbers of A04 rule 6 (70_data_provider_closure.json):
# REFUSAL_STAGE_VERSION = 5.
STAGE_VERSION = 5
# ACCESS_VERSION_FIRST = 1 (70_data_provider_closure.json; A12 rule 1).
ACCESS_VERSION_FIRST = 1

KERNEL = "cabinet_kernel"

# 70_persistence_closure.json: the table of M06 AgentSession rows.
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


def _stale(answer):
    """stale / stale_access_version, stage (5) (A12 rule 3; State 5)."""
    return _refused(answer, "stale", STAGE_VERSION, ["stale_access_version"])


def _create_project(rt, name):
    answer = rt.owner(
        "create_project",
        request_id=rt.new_request_id(),
        project={"display_name": name, "address": f"{name}, Calle Mayor 9"},
    )
    return _answered(answer, "project_card")["card"]


def _register(rt, tag):
    session_id = f"a12-{tag}-{uuid.uuid4().hex}"
    registered = _answered(
        rt.service(KERNEL, "register_agent_session", kernel_session=session_id),
        "session_access",
    )
    assert registered["access"]["access_version"] == ACCESS_VERSION_FIRST
    return session_id


def _kernel(rt, session_id, operation, **inputs):
    return rt.service(KERNEL, operation, inputs, kernel_session=session_id)


def _owner_access(rt, session_id):
    return _answered(
        rt.owner("read_session", target=session_id), "session_access"
    )["access"]


def _kernel_access(rt, session_id):
    """What Kernel reads: the current version (A12 rule 5)."""
    return _answered(
        _kernel(rt, session_id, "read_session_access"), "session_access"
    )["access"]


def _grant(rt, session_id, project_id, make_active=False, stated=None):
    if stated is None:
        stated = _owner_access(rt, session_id)["access_version"]
    return rt.owner(
        "grant_project",
        target=session_id,
        stated_version=stated,
        project_id=project_id,
        make_active=make_active,
    )


def _request_text(rt, session_id):
    listed = _answered(rt.owner("list_sessions"), "session_list")["items"]
    [item] = [i for i in listed if i["access"]["session_id"] == session_id]
    return item["request_text"]


def _session_row(rt, session_id):
    rows = [
        row
        for row in rt.store_rows(SESSION_TABLE)
        if session_id in json.dumps(row, default=str)
    ]
    assert len(rows) == 1, rows
    return rows[0]


# --- Required test 1 ----------------------------------------------------------


def test_grant_with_replaced_request_version_refused(semantic_runtime):
    """The owner opens a session while the agent replaces its request;
    granting with the old version is refused (A12-1, A12-2)."""
    rt = semantic_runtime
    project_id = _create_project(rt, "Casa Pedida")["project_id"]
    session_id = _register(rt, "request")

    # The agent asks (rule 4: no version stated; the version moves by one).
    _answered(
        _kernel(rt, session_id, "request_project_access", request_text="Casa Pedida"),
        "request_pending",
    )
    seen = _owner_access(rt, session_id)  # the owner opens the session
    assert seen["access_version"] == ACCESS_VERSION_FIRST + 1
    assert seen["request_pending"] is True

    # The agent replaces the request with an equal text: a new request is a
    # change whatever its text (M06, rule 4), one move (A12-2).
    _answered(
        _kernel(rt, session_id, "request_project_access", request_text="Casa Pedida"),
        "request_pending",
    )
    replaced = _owner_access(rt, session_id)
    assert replaced["access_version"] == seen["access_version"] + 1

    row_before = _session_row(rt, session_id)

    # The owner grants with the version seen: stale, stage (5) (A12-1).
    grant = {"answer_kind": "grant", "project_id": project_id, "make_active": False}
    _stale(
        rt.owner(
            "answer_access_request",
            target=session_id,
            stated_version=seen["access_version"],
            access_answer=grant,
        )
    )
    # ... and nothing changed: set, active project, pending request, version,
    # read back by the owner and by Kernel, and the store row itself.
    assert _session_row(rt, session_id) == row_before
    assert _owner_access(rt, session_id) == replaced
    assert _kernel_access(rt, session_id) == replaced
    assert _request_text(rt, session_id) == "Casa Pedida"

    # The same holds for a direct grant stating the old version.
    _stale(_grant(rt, session_id, project_id, stated=seen["access_version"]))
    assert _owner_access(rt, session_id) == replaced
    assert _session_row(rt, session_id) == row_before

    # Control: with the current version the same answer is accepted; the
    # request is cleared, the project joins, one move (rule 1).
    answered = _answered(
        rt.owner(
            "answer_access_request",
            target=session_id,
            stated_version=replaced["access_version"],
            access_answer=grant,
        ),
        "session_access",
    )
    access = answered["access"]
    assert access["granted_project_ids"] == [project_id]
    assert access["request_pending"] is False
    assert access["access_version"] == replaced["access_version"] + 1
    assert answered["project_joined"] is True
    assert _kernel_access(rt, session_id) == access


# --- Required test 2 ----------------------------------------------------------


def test_erasure_moves_both_session_versions(semantic_runtime):
    """Erasing a project in two sessions' sets moves both versions by one
    (A12-2; rule 1, R0-61), for either erasure (anonymise, delete whole)."""
    rt = semantic_runtime
    for erasure in ("anonymise", "delete_whole"):
        erased = _create_project(rt, f"Casa Borrar {erasure}")
        kept_id = _create_project(rt, f"Casa Queda {erasure}")["project_id"]
        erased_id = erased["project_id"]

        # Session one: the project granted and active in one action.
        one = _register(rt, f"one-{erasure}")
        _answered(_grant(rt, one, erased_id, make_active=True), "session_access")
        # Session two: another project first, then this one, at a later
        # version than session one's, so a fixed value cannot pass for "+1".
        two = _register(rt, f"two-{erasure}")
        _answered(_grant(rt, two, kept_id), "session_access")
        _answered(
            _kernel(rt, two, "request_project_access", request_text="algo"),
            "request_pending",
        )
        _answered(_grant(rt, two, erased_id), "session_access")
        # Session three: does not hold the project.
        three = _register(rt, f"three-{erasure}")
        _answered(_grant(rt, three, kept_id), "session_access")

        # Archive (an active project is never erased, erase_project Errors);
        # archiving keeps every set (R0-70).
        archived = _answered(
            rt.owner(
                "archive_project", target=erased_id, stated_version=erased["revision"]
            ),
            "project_card",
        )["card"]

        before = {s: _kernel_access(rt, s) for s in (one, two, three)}
        assert before[one]["access_version"] != before[two]["access_version"]

        _answered(
            rt.owner(
                "erase_project",
                target=erased_id,
                stated_version=archived["revision"],
                erasure=erasure,
            ),
            "project_erased",
        )

        after = {s: _kernel_access(rt, s) for s in (one, two, three)}
        # Each session holding the project: one move, however many of its
        # facts the erasure changed (set and active for session one).
        assert after[one]["access_version"] == before[one]["access_version"] + 1
        assert after[one]["granted_project_ids"] == []
        assert after[one]["active_project_id"] is None
        assert after[two]["access_version"] == before[two]["access_version"] + 1
        assert after[two]["granted_project_ids"] == [kept_id]
        assert after[two]["request_pending"] is True
        # The session that did not hold it is not changed and keeps its
        # version (rule 2).
        assert after[three] == before[three]


# --- Required test 3 (untagged) ----------------------------------------------


def test_regrant_already_granted_leaves_version(semantic_runtime):
    """Granting a project already granted leaves the version (A12 rule 2,
    A05)."""
    rt = semantic_runtime
    project_id = _create_project(rt, "Casa Dos Veces")["project_id"]
    other_id = _create_project(rt, "Casa Otra")["project_id"]
    session_id = _register(rt, "regrant")

    first = _answered(_grant(rt, session_id, project_id), "session_access")
    assert first["access"]["access_version"] == ACCESS_VERSION_FIRST + 1
    assert first["project_joined"] is True

    # The repeat: accepted, nothing changed (A05; grant_project Enforces "A
    # project already in the set is unchanged"), the version left.
    repeat = _answered(_grant(rt, session_id, project_id), "session_access")
    assert repeat["changed"] is False
    assert repeat["project_joined"] is False
    assert repeat["access"] == first["access"]
    assert _kernel_access(rt, session_id) == first["access"]

    # Control: a project not yet in the set moves it by one.
    other = _answered(_grant(rt, session_id, other_id), "session_access")
    assert other["changed"] is True
    assert other["access"]["access_version"] == first["access"]["access_version"] + 1


# --- Required test 4 ----------------------------------------------------------


def test_grant_and_activate_moves_once(semantic_runtime):
    """Granting a project and making it active in one action moves the version
    by one (A12-2, rule 1)."""
    rt = semantic_runtime
    direct_id = _create_project(rt, "Casa Directa")["project_id"]
    asked_id = _create_project(rt, "Casa Pedida")["project_id"]

    # A direct grant that also makes the project active: two facts, one move.
    session_id = _register(rt, "grant-activate")
    granted = _answered(
        _grant(rt, session_id, direct_id, make_active=True), "session_access"
    )["access"]
    assert granted["granted_project_ids"] == [direct_id]
    assert granted["active_project_id"] == direct_id
    assert granted["access_version"] == ACCESS_VERSION_FIRST + 1
    assert _kernel_access(rt, session_id) == granted

    # An answer to a request that grants and activates: three facts — the
    # request cleared, the project joined, made active — one move.
    asking = _register(rt, "answer-activate")
    _answered(
        _kernel(rt, asking, "request_project_access", request_text="Casa Pedida"),
        "request_pending",
    )
    pending = _owner_access(rt, asking)
    answered = _answered(
        rt.owner(
            "answer_access_request",
            target=asking,
            stated_version=pending["access_version"],
            access_answer={
                "answer_kind": "grant",
                "project_id": asked_id,
                "make_active": True,
            },
        ),
        "session_access",
    )["access"]
    assert answered["granted_project_ids"] == [asked_id]
    assert answered["active_project_id"] == asked_id
    assert answered["request_pending"] is False
    assert answered["access_version"] == pending["access_version"] + 1

    # Control: changing only the active project afterwards is a move of its
    # own (rule 1) — clearing it here.
    cleared = _answered(
        rt.owner(
            "set_active_project",
            target=session_id,
            stated_version=granted["access_version"],
            project_id=None,
        ),
        "session_access",
    )["access"]
    assert cleared["active_project_id"] is None
    assert cleared["granted_project_ids"] == [direct_id]
    assert cleared["access_version"] == granted["access_version"] + 1


# --- Required test 5 ----------------------------------------------------------


def test_stale_owner_end_refused_unchanged(semantic_runtime):
    """The owner ending a session stating a stale access version is refused;
    the session stays registered and unchanged (A12-1)."""
    rt = semantic_runtime
    project_id = _create_project(rt, "Casa Sigue")["project_id"]
    session_id = _register(rt, "stale-end")
    seen = _answered(_grant(rt, session_id, project_id, make_active=True), "session_access")[
        "access"
    ]
    # The agent moves the version after the owner saw it.
    _answered(
        _kernel(rt, session_id, "request_project_access", request_text="mas"),
        "request_pending",
    )
    current = _owner_access(rt, session_id)
    assert current["access_version"] == seen["access_version"] + 1
    row_before = _session_row(rt, session_id)

    # Stale: refused, stage (5) (A12 rule 3; end_session Errors).
    _stale(
        rt.owner("end_session", target=session_id, stated_version=seen["access_version"])
    )
    # A version from the future is no more current than a past one.
    _stale(
        rt.owner(
            "end_session",
            target=session_id,
            stated_version=current["access_version"] + 1,
        )
    )

    # Still registered and unchanged: the owner's and Kernel's reads, the
    # store row, and an agent call on its project answered.
    assert _owner_access(rt, session_id) == current
    assert _kernel_access(rt, session_id) == current
    assert _session_row(rt, session_id) == row_before
    _answered(
        _kernel(rt, session_id, "read_agent_projection", project_id=project_id),
        "agent_projection",
    )

    # Control: stating the current version ends it (A11 rule 2).
    _answered(
        rt.owner(
            "end_session", target=session_id, stated_version=current["access_version"]
        ),
        "session_ended",
    )
    assert [
        row
        for row in rt.store_rows(SESSION_TABLE)
        if session_id in json.dumps(row, default=str)
    ] == []
