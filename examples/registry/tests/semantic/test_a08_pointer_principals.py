"""Witness tests for accepted decision A08 (02_rules_artifacts.md).

A pointer is published and withdrawn by Cabinet Kernel for the agent, on a
project of its session's set, or by the owner (rule 1); no other service has
the right, whatever type it names (rule 2). The pointer names the owner
service the declared vocabulary fixes for its type; the caller does not
choose it (rule 3). The pointer records its publisher, and a withdrawal its
principal: Kernel for the agent naming the session, or the owner (rule 4). A
withdrawal names the pointer only; for Kernel its project is checked against
the session's set, and a pointer that does not exist or lies outside the set
is answered as not found (rule 7). Formal invariants A08-1, A08-2. Each tagged
test carries the witness name its Required test declares.

The Factory project supplies the ``semantic_runtime`` fixture
(``RUNTIME_SURFACE.md``); each test gets a fresh instance at
2026-01-05T09:00:00Z. Surface used here:

- ``owner(...)`` — ``create_project``, ``grant_project``, ``revoke_project``,
  ``read_session``, ``publish_pointer``, ``withdraw_pointer``,
  ``list_pointers``;
- ``service(name, operation, inputs, kernel_session=...)`` — for
  ``cabinet_kernel``: ``register_agent_session``,
  ``publish_artifact_pointer``, ``withdraw_artifact_pointer``; for
  ``presupro``, ``client_portal``, ``cabinet``: ``publish_artifact_pointer``
  and ``withdraw_artifact_pointer`` (which they have no right to);
  ``presupro`` ``list_artifacts``;
- ``store_rows("pointer_rows")``, ``new_request_id()``, ``clock.advance``.

Expected values: State 5 (``50_public_apis_0_conventions.md``, "Closed set of
refusal codes" and its note on stage (2); ``50_public_apis_5_surfaces.md``
perform_service_operation and serve_service_request;
``50_public_apis_3_records.md`` publish_pointer, withdraw_pointer), State 6
(``PointerView``, ``PointerPublisher``, ``ActingPrincipal``), the data
provider's ``SERVICE_RIGHTS`` and ``ARTIFACT_TYPE_OWNERS``
(``70_data_provider_closure.json``).
"""

from datetime import datetime

KERNEL = "cabinet_kernel"

# 70_data_provider_closure.json: REFUSAL_STAGE_AUTHENTICATION = 1,
# REFUSAL_STAGE_AGENT_SESSION = 2, REFUSAL_STAGE_VALUES = 4.
STAGE_AUTHENTICATION = 1
STAGE_AGENT_SESSION = 2
STAGE_VALUES = 4

# 70_data_provider_closure.json ARTIFACT_TYPE_OWNERS:
# [{"artifact_type": "estimate", "owner_service": "presupro"}].
ESTIMATE_OWNER = "presupro"


def _instant(text):
    # State 6 wire format: instants are ISO 8601 text in UTC ending in `Z`.
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def _accepted(answer, answer_kind):
    assert answer["answer_kind"] == answer_kind, answer
    return answer


def _assert_refused(answer, code, stage, kinds):
    # RUNTIME_SURFACE.md "Refusals are answers"; State 5 closed set.
    assert answer["answer_kind"] == "refused", answer
    assert answer["code"] == code, answer
    assert answer["stage"] == stage, answer
    assert [failure["kind"] for failure in answer["failures"]] == kinds, answer


def _create_project(rt, name="A08 project"):
    answer = rt.owner(
        "create_project",
        request_id=rt.new_request_id(),
        project={"display_name": name, "address": "Calle Mayor 1"},
    )
    return _accepted(answer, "project_card")["card"]["project_id"]


def _register(rt, session):
    answer = rt.service(KERNEL, "register_agent_session", kernel_session=session)
    return _accepted(answer, "session_access")["access"]["access_version"]


def _grant(rt, session, *project_ids):
    version = _accepted(rt.owner("read_session", target=session), "session_access")["access"][
        "access_version"
    ]
    for project_id in project_ids:
        answer = rt.owner(
            "grant_project",
            target=session,
            stated_version=version,
            project_id=project_id,
            make_active=False,
        )
        version = _accepted(answer, "session_access")["access"]["access_version"]
    return version


def _publish_inputs(rt, project_id, uri, artifact_type="estimate"):
    return {
        "project_id": project_id,
        "request_id": rt.new_request_id(),
        "pointer": {"artifact_type": artifact_type, "uri": uri},
    }


def _kernel_publish(rt, session, project_id, uri):
    return rt.service(
        KERNEL,
        "publish_artifact_pointer",
        _publish_inputs(rt, project_id, uri),
        kernel_session=session,
    )


def _kernel_withdraw(rt, session, pointer_id):
    return rt.service(
        KERNEL, "withdraw_artifact_pointer", {"pointer_id": pointer_id}, kernel_session=session
    )


def _owner_publish(rt, project_id, uri):
    return rt.owner(
        "publish_pointer",
        target=project_id,
        request_id=rt.new_request_id(),
        pointer={"artifact_type": "estimate", "uri": uri},
    )


def _list(rt, project_id):
    return _accepted(rt.owner("list_pointers", target=project_id), "pointers")["pointers"]


def _principal_of(publisher):
    # State 6 PointerPublisher: discriminated by publisher_kind; a pointer
    # published in Registry carries PrincipalPublisher (M05).
    assert publisher["publisher_kind"] == "principal", publisher
    return publisher["principal"]


def _assert_kernel_principal(principal, session):
    # M07 / State 6 ActingPrincipal: agent_via_kernel naming the session.
    assert principal["principal_kind"] == "agent_via_kernel", principal
    assert principal["session_id"] == session, principal


def _assert_owner_principal(principal):
    assert principal["principal_kind"] == "owner", principal
    assert principal["session_id"] is None, principal


def test_presupro_publish_refused(semantic_runtime):
    """RT1: PresuPro calling 'publish an artifact pointer' is refused."""
    rt = semantic_runtime
    project_id = _create_project(rt)
    _register(rt, "a08-s")
    _grant(rt, "a08-s", project_id)
    rows = rt.store_rows("pointer_rows")

    # SERVICE_RIGHTS lists publish_artifact_pointer and
    # withdraw_artifact_pointer for cabinet_kernel alone; any other service is
    # refused at stage (1): `not_permitted` (`outside_service_rights`), A09
    # rule 3. "Whatever type it names" (A08 rule 2): the declared `estimate`,
    # whose owner service PresuPro is, and an undeclared one alike — stage (1)
    # comes before the type's check at stage (4) (A04 rule 6).
    for service in ("presupro", "client_portal", "cabinet"):
        for artifact_type in ("estimate", "wall_plan"):
            answer = rt.service(
                service,
                "publish_artifact_pointer",
                _publish_inputs(rt, project_id, "https://presupro.example/e/x", artifact_type),
            )
            _assert_refused(answer, "not_permitted", STAGE_AUTHENTICATION, ["outside_service_rights"])
    assert _list(rt, project_id) == []
    assert rt.store_rows("pointer_rows") == rows

    # Control: Kernel, for a session holding the project, publishes it.
    published = _accepted(
        _kernel_publish(rt, "a08-s", project_id, "https://presupro.example/e/1"), "pointer"
    )["pointer"]
    assert [p["pointer_id"] for p in _list(rt, project_id)] == [published["pointer_id"]]

    # Nor may PresuPro withdraw it (A08 rule 2, "or withdraw").
    _assert_refused(
        rt.service("presupro", "withdraw_artifact_pointer", {"pointer_id": published["pointer_id"]}),
        "not_permitted",
        STAGE_AUTHENTICATION,
        ["outside_service_rights"],
    )
    assert _list(rt, project_id) == [published]


def test_kernel_publish_names_owner_and_publisher(semantic_runtime):
    """RT2: Kernel publishes an `estimate` for session S; the pointer names
    PresuPro as its owner service and Kernel for S as its publisher."""
    rt = semantic_runtime
    project_id = _create_project(rt)
    # Two sessions hold the project, so a publisher taken from any session
    # but the one the request names is told apart.
    for session in ("a08-S", "a08-T"):
        _register(rt, session)
        _grant(rt, session, project_id)

    rt.clock.advance(minutes=1)
    answer = _accepted(
        _kernel_publish(rt, "a08-S", project_id, "https://presupro.example/e/1"), "pointer"
    )
    pointer = answer["pointer"]
    # A08-2: owner_service = owner_service(type), from ARTIFACT_TYPE_OWNERS.
    assert pointer["owner_service"] == ESTIMATE_OWNER
    # A08 rule 4: Kernel for the agent naming the session.
    _assert_kernel_principal(_principal_of(pointer["publisher"]), "a08-S")
    assert _instant(pointer["published_at"]) == _instant("2026-01-05T09:01:00Z")

    second = _accepted(
        _kernel_publish(rt, "a08-T", project_id, "https://presupro.example/e/2"), "pointer"
    )["pointer"]
    _assert_kernel_principal(_principal_of(second["publisher"]), "a08-T")
    # The owner's publish records the owner (rule 4), the same owner service.
    third = _accepted(
        _owner_publish(rt, project_id, "https://presupro.example/e/3"), "pointer"
    )["pointer"]
    _assert_owner_principal(_principal_of(third["publisher"]))
    assert third["owner_service"] == ESTIMATE_OWNER

    # Read back: the history keeps each publisher as written (written once).
    by_id = {p["pointer_id"]: p for p in _list(rt, project_id)}
    _assert_kernel_principal(_principal_of(by_id[pointer["pointer_id"]]["publisher"]), "a08-S")
    _assert_kernel_principal(_principal_of(by_id[second["pointer_id"]]["publisher"]), "a08-T")
    _assert_owner_principal(_principal_of(by_id[third["pointer_id"]]["publisher"]))
    assert {p["owner_service"] for p in by_id.values()} == {ESTIMATE_OWNER}

    # A08 rule 3, "the caller does not choose it": GivenPointer declares no
    # owner service, so a request carrying one is not of the wire format —
    # stage (4) `invalid_request` (`outside_closed_list`), State 5
    # serve_service_request Errors — and nothing is published.
    rows = rt.store_rows("pointer_rows")
    inputs = _publish_inputs(rt, project_id, "https://presupro.example/e/4")
    inputs["pointer"]["owner_service"] = "cabinet"
    _assert_refused(
        rt.service(KERNEL, "publish_artifact_pointer", inputs, kernel_session="a08-S"),
        "invalid_request",
        STAGE_VALUES,
        ["outside_closed_list"],
    )
    assert rt.store_rows("pointer_rows") == rows


def test_withdraw_outside_set_not_found(semantic_runtime):
    """RT3: Kernel withdrawing a pointer on a project outside its session's set
    is answered as not found: the whole answer equal to that for a pointer
    that does not exist (A10 rule 3)."""
    rt = semantic_runtime
    inside = _create_project(rt, "A08 inside")
    outside = _create_project(rt, "A08 outside")
    revoked = _create_project(rt, "A08 revoked")
    session = "a08-W"
    _register(rt, session)
    _grant(rt, session, inside, revoked)

    # A pointer on a project never granted (published by the owner), and one
    # Kernel published itself on a project revoked since.
    never_granted = _accepted(
        _owner_publish(rt, outside, "https://presupro.example/o/1"), "pointer"
    )["pointer"]
    on_revoked = _accepted(
        _kernel_publish(rt, session, revoked, "https://presupro.example/r/1"), "pointer"
    )["pointer"]
    version = _accepted(rt.owner("read_session", target=session), "session_access")["access"][
        "access_version"
    ]
    _accepted(
        rt.owner("revoke_project", target=session, stated_version=version, project_id=revoked),
        "session_access",
    )
    rows = rt.store_rows("pointer_rows")

    # A08 rule 7, A10 rule 3: `not_found` (`agent_call_refused`), always of
    # stage (2) (State 5 closed set, the note on stage (2)).
    refused_outside = _kernel_withdraw(rt, session, never_granted["pointer_id"])
    _assert_refused(refused_outside, "not_found", STAGE_AGENT_SESSION, ["agent_call_refused"])
    refused_revoked = _kernel_withdraw(rt, session, on_revoked["pointer_id"])
    _assert_refused(refused_revoked, "not_found", STAGE_AGENT_SESSION, ["agent_call_refused"])
    # The same answer as a pointer that does not exist (A08 rule 7, A10-2):
    # the whole answer, field for field. A10 rule 3: the failure's path is
    # built from the request alone — the name of the input naming the
    # pointer, never its id — so the three requests, which differ only in
    # the pointer id they give, are answered equal.
    unknown = _kernel_withdraw(rt, session, "00000000-0000-4000-8000-00000000dead")
    _assert_refused(unknown, "not_found", STAGE_AGENT_SESSION, ["agent_call_refused"])
    assert refused_outside == unknown
    assert refused_revoked == unknown
    for answer in (refused_outside, refused_revoked):
        text = repr(answer)
        assert never_granted["pointer_id"] not in text
        assert on_revoked["pointer_id"] not in text

    # Nothing changed: both pointers stay published.
    assert _list(rt, outside) == [never_granted]
    assert _list(rt, revoked) == [on_revoked]
    assert rt.store_rows("pointer_rows") == rows

    # Control: the same session withdraws a pointer of a project in its set.
    in_set = _accepted(
        _kernel_publish(rt, session, inside, "https://presupro.example/i/1"), "pointer"
    )["pointer"]
    withdrawn = _accepted(_kernel_withdraw(rt, session, in_set["pointer_id"]), "pointer")
    assert withdrawn["pointer"]["status"] == "withdrawn"
    _assert_kernel_principal(withdrawn["pointer"]["withdrawn_by"], session)


def test_owner_withdraws_kernel_pointer_records_owner(semantic_runtime):
    """RT4 (untagged): the owner withdraws a pointer Kernel published; the
    withdrawal records the owner."""
    rt = semantic_runtime
    project_id = _create_project(rt)
    session = "a08-K"
    _register(rt, session)
    _grant(rt, session, project_id)
    kernels = _accepted(
        _kernel_publish(rt, session, project_id, "https://presupro.example/e/1"), "pointer"
    )["pointer"]

    rt.clock.advance(minutes=2)
    answer = _accepted(rt.owner("withdraw_pointer", target=kernels["pointer_id"]), "pointer")
    withdrawn = answer["pointer"]
    # A07 rule 4, A08 rule 4: withdrawn, with its instant and principal.
    assert withdrawn["status"] == "withdrawn"
    _assert_owner_principal(withdrawn["withdrawn_by"])
    assert _instant(withdrawn["withdrawn_at"]) == _instant("2026-01-05T09:02:00Z")
    # The publisher is written once and stays Kernel's for the session.
    _assert_kernel_principal(_principal_of(withdrawn["publisher"]), session)
    assert _list(rt, project_id) == [withdrawn]

    # The other way round (rule 5, "either"): Kernel withdraws the owner's.
    owners = _accepted(
        _owner_publish(rt, project_id, "https://presupro.example/e/2"), "pointer"
    )["pointer"]
    by_kernel = _accepted(_kernel_withdraw(rt, session, owners["pointer_id"]), "pointer")["pointer"]
    _assert_kernel_principal(by_kernel["withdrawn_by"], session)
    _assert_owner_principal(_principal_of(by_kernel["publisher"]))
