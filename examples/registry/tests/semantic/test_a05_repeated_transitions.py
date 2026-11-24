"""Witness tests for accepted decision A05 (02_rules_records.md).

A transition to the state a record is already in, that passes every check of
A04 rule 6, is accepted and changes nothing: it answers the record as it
stands, its revision, last-changed instant and a session's access version
stay, no audit entry is written and no confirmation id is minted (rules 1, 2).
Ending an ended relationship with another date does not move the date (rule
3). The refusals State 0 states stay refusals and come first (rule 4). Each
tagged test carries the witness name its Required test declares.

The Factory project supplies the ``semantic_runtime`` fixture
(``RUNTIME_SURFACE.md``); each test gets a fresh instance at
2026-01-05T09:00:00Z. Surface used here:

- ``owner(action, target, stated_version, confirm, **values)`` — the owner
  actions of the imported ``OWNER_ACTIONS``: ``create_project``,
  ``read_project``, ``archive_project``, ``erase_project``,
  ``record_customer``, ``read_customer``, ``mark_customer``,
  ``erase_customer``, ``read_session``, ``list_sessions``, ``grant_project``,
  ``set_active_project``, ``list_pointers``, ``publish_pointer``,
  ``withdraw_pointer``, ``read_audit``;
- ``service("cabinet_kernel", ...)`` — ``register_agent_session``,
  ``read_session_access``;
- ``clock.advance``, ``new_request_id()``, ``store_rows(table)``.

Expected values: State 5 (``50_public_apis_0_conventions.md``, "Repeats",
"Closed set of refusal codes"; ``50_public_apis_2_sessions.md``,
``50_public_apis_3_records.md``), State 6 answer models
(``60_model_closure_values.json``), the data provider's constants
(``70_data_provider_closure.json``).
"""

from datetime import datetime

# 70_data_provider_closure.json: REFUSAL_STAGE_LIFECYCLE = 6.
STAGE_LIFECYCLE = 6

# 70_persistence_closure.json: the store's eight tables.
TABLES = (
    "project_rows",
    "room_rows",
    "customer_rows",
    "pointer_rows",
    "agent_session_rows",
    "audit_entry_rows",
    "audit_sequence_rows",
    "migration_closure_rows",
)

KERNEL = "cabinet_kernel"


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


def _store(rt):
    return {table: rt.store_rows(table) for table in TABLES}


def _audit(rt):
    return _accepted(rt.owner("read_audit"), "audit_view")["entries"]


def _create_project(rt, name="A05 project", address="Calle Mayor 1"):
    answer = rt.owner(
        "create_project",
        request_id=rt.new_request_id(),
        project={"display_name": name, "address": address},
    )
    return _accepted(answer, "project_card")["card"]


def _read_project(rt, project_id):
    return _accepted(rt.owner("read_project", target=project_id), "project_card")["card"]


def _record_customer(rt, name="Ana Gómez"):
    answer = rt.owner(
        "record_customer",
        request_id=rt.new_request_id(),
        customer={"name": name, "customer_kind": "person"},
    )
    return _accepted(answer, "customer")["customer"]


def _read_customer(rt, customer_ref):
    return _accepted(rt.owner("read_customer", target=customer_ref), "customer")["customer"]


def _mark(rt, customer_ref, revision, transition, end_date=None):
    values = {"transition": transition}
    if end_date is not None:
        values["end_date"] = end_date
    return rt.owner("mark_customer", target=customer_ref, stated_version=revision, **values)


def _register(rt, session_id):
    answer = rt.service(KERNEL, "register_agent_session", kernel_session=session_id)
    return _accepted(answer, "session_access")


def _read_session(rt, session_id):
    return _accepted(rt.owner("read_session", target=session_id), "session_access")["access"]


def _registered_at(rt, session_id):
    items = _accepted(rt.owner("list_sessions"), "session_list")["items"]
    [item] = [item for item in items if item["access"]["session_id"] == session_id]
    return item["registered_at"]


def _grant(rt, session_id, version, project_id, make_active=False):
    return rt.owner(
        "grant_project",
        target=session_id,
        stated_version=version,
        project_id=project_id,
        make_active=make_active,
    )


def _set_active(rt, session_id, version, project_id):
    # State 5 set_active_project: "the project, or none to clear".
    if project_id is None:
        return rt.owner("set_active_project", target=session_id, stated_version=version)
    return rt.owner(
        "set_active_project",
        target=session_id,
        stated_version=version,
        project_id=project_id,
    )


def _pointers(rt, project_id):
    return _accepted(rt.owner("list_pointers", target=project_id), "pointers")["pointers"]


def _publish(rt, project_id, uri):
    answer = rt.owner(
        "publish_pointer",
        target=project_id,
        request_id=rt.new_request_id(),
        pointer={"artifact_type": "estimate", "uri": uri},
    )
    return _accepted(answer, "pointer")["pointer"]


def test_restrict_restricted_customer_unchanged(semantic_runtime):
    """RT1: restricting a restricted Customer answers it, same revision, no entry."""
    rt = semantic_runtime
    customer = _record_customer(rt)
    ref = customer["customer_ref"]
    # REVISION_FIRST = 1 (70_data_provider_closure.json).
    assert customer["revision"] == 1

    # Control: the first restriction is a change (A04-3): the revision moves,
    # the mark is set at the action's instant and one entry is written (A14
    # rule 1, OWNER_AUDIT_ACTIONS mark_customer/restrict -> customer_restricted).
    entries_before = _audit(rt)
    rt.clock.advance(minutes=1)
    first = _accepted(_mark(rt, ref, 1, "restrict"), "customer")
    assert first["changed"] is True
    restricted = first["customer"]
    assert restricted["revision"] == 2
    assert restricted["restricted_at"] is not None
    assert _instant(restricted["last_changed_at"]) > _instant(customer["last_changed_at"])
    entries_after_first = _audit(rt)
    assert len(entries_after_first) == len(entries_before) + 1
    assert entries_after_first[-1]["action"] == "customer_restricted"
    assert entries_after_first[-1]["subject"]["customer_ref"] == ref

    # The repeat states the current revision (A04 rule 3) at a later instant:
    # accepted, `changed: false` (State 5 "Repeats"), the record as it stands.
    store_before = _store(rt)
    rt.clock.advance(minutes=5)
    again = _accepted(_mark(rt, ref, 2, "restrict"), "customer")
    assert again["changed"] is False
    assert again["customer"] == restricted  # A05 rule 2: answered as it stands
    assert _read_customer(rt, ref) == restricted

    # A05 rule 2: no audit entry; nothing else in the store moved either.
    assert _audit(rt) == entries_after_first
    assert _store(rt) == store_before


def test_end_ended_relationship_keeps_date(semantic_runtime):
    """RT2: ending an ended relationship with a new date keeps the old date."""
    rt = semantic_runtime
    ref = _record_customer(rt)["customer_ref"]

    # Control: a real end is dated as given (State 5 mark_customer: "an end
    # dated as given or today"); today is 2026-01-05, so 2026-01-02 is allowed.
    ended = _accepted(_mark(rt, ref, 1, "end", end_date="2026-01-02"), "customer")
    assert ended["changed"] is True
    assert ended["customer"]["relationship_ended_on"] == "2026-01-02"
    assert ended["customer"]["revision"] == 2
    entries = _audit(rt)
    store_before = _store(rt)

    # A05 rule 3: another date does not move it; nothing changes (rule 2).
    rt.clock.advance(minutes=3)
    other_date = _accepted(_mark(rt, ref, 2, "end", end_date="2026-01-04"), "customer")
    assert other_date["changed"] is False
    assert other_date["customer"] == ended["customer"]
    # Ending again with no date (which would date it today) keeps it too.
    no_date = _accepted(_mark(rt, ref, 2, "end"), "customer")
    assert no_date["changed"] is False
    assert no_date["customer"]["relationship_ended_on"] == "2026-01-02"
    assert _read_customer(rt, ref) == ended["customer"]
    assert _audit(rt) == entries
    assert _store(rt) == store_before

    # Control (A05 rule 3, "the owner resumes and ends again to change it"):
    # after a resume the new date is taken, so the date is not simply frozen.
    resumed = _accepted(_mark(rt, ref, 2, "resume"), "customer")
    assert resumed["customer"]["relationship_ended_on"] is None
    re_ended = _accepted(_mark(rt, ref, 3, "end", end_date="2026-01-04"), "customer")
    assert re_ended["customer"]["relationship_ended_on"] == "2026-01-04"


def test_regrant_keeps_access_version(semantic_runtime):
    """RT3: granting a project already granted leaves the access version."""
    rt = semantic_runtime
    project_id = _create_project(rt)["project_id"]
    session = "a05-session-regrant"
    registered = _register(rt, session)
    # ACCESS_VERSION_FIRST = 1 (70_data_provider_closure.json).
    assert registered["access"]["access_version"] == 1

    # Control: the first grant joins the project and moves the version once
    # (State 5 grant_project), with its entry session_project_granted.
    first = _accepted(_grant(rt, session, 1, project_id), "session_access")
    assert first["changed"] is True
    assert first["project_joined"] is True
    assert first["access"]["granted_project_ids"] == [project_id]
    assert first["access"]["access_version"] == 2
    entries = _audit(rt)
    assert entries[-1]["action"] == "session_project_granted"
    store_before = _store(rt)

    # The repeat states the current access version (A12 rule 3, A04 rule 3).
    rt.clock.advance(minutes=2)
    again = _accepted(_grant(rt, session, 2, project_id), "session_access")
    assert again["changed"] is False
    assert again["project_joined"] is False
    assert again["access"] == first["access"]  # version 2, same set, no active
    assert _read_session(rt, session) == first["access"]
    # Kernel reads the same access version (A12 rule 5).
    kernel_view = _accepted(
        rt.service(KERNEL, "read_session_access", kernel_session=session),
        "session_access",
    )
    assert kernel_view["access"]["access_version"] == 2
    assert _audit(rt) == entries
    assert _store(rt) == store_before


def test_withdrawing_withdrawn_or_superseded_pointer_refused(semantic_runtime):
    """RT4 (untagged): withdrawing a withdrawn pointer is refused (A05 rule 4).

    Rule 4 names a superseded pointer beside it; both are shown.
    """
    rt = semantic_runtime
    project_id = _create_project(rt)["project_id"]
    first = _publish(rt, project_id, "https://presupro.example/estimates/1")
    second = _publish(rt, project_id, "https://presupro.example/estimates/2")

    # Control: withdrawing the published pointer is accepted.
    withdrawn = _accepted(rt.owner("withdraw_pointer", target=second["pointer_id"]), "pointer")
    assert withdrawn["pointer"]["status"] == "withdrawn"
    listed = _pointers(rt, project_id)
    store_before = _store(rt)

    # State 5 withdraw_pointer: (6) a withdrawn or superseded pointer refused,
    # `refused` with kinds `withdrawn` / `superseded` (closed set, stage 6).
    rt.clock.advance(minutes=1)
    _assert_refused(
        rt.owner("withdraw_pointer", target=second["pointer_id"]),
        "refused",
        STAGE_LIFECYCLE,
        ["withdrawn"],
    )
    _assert_refused(
        rt.owner("withdraw_pointer", target=first["pointer_id"]),
        "refused",
        STAGE_LIFECYCLE,
        ["superseded"],
    )
    # Nothing changed: the withdrawal's instant and principal stay.
    assert _pointers(rt, project_id) == listed
    assert _store(rt) == store_before


def test_regrant_of_archived_project_refused_and_kept(semantic_runtime):
    """RT5 (untagged): granting again a granted, since archived project is refused.

    The project stays in the set (R0-46, R0-70) and nothing changes.
    """
    rt = semantic_runtime
    archived = _create_project(rt, name="A05 archived")
    open_project = _create_project(rt, name="A05 open")
    session = "a05-session-archived"
    _register(rt, session)
    granted = _accepted(_grant(rt, session, 1, archived["project_id"]), "session_access")
    version = granted["access"]["access_version"]

    # Archiving keeps every session's set (State 5 archive_project, R0-70).
    _accepted(
        rt.owner("archive_project", target=archived["project_id"], stated_version=1),
        "project_card",
    )
    access = _read_session(rt, session)
    assert access["granted_project_ids"] == [archived["project_id"]]
    assert access["access_version"] == version
    store_before = _store(rt)

    # A05 rule 4: granting an archived project, already granted included,
    # is refused (State 5 grant_project: `refused` (`archived`), stage 6).
    _assert_refused(
        _grant(rt, session, version, archived["project_id"]),
        "refused",
        STAGE_LIFECYCLE,
        ["archived"],
    )
    assert _read_session(rt, session) == access
    assert _store(rt) == store_before

    # Control: the same session, at the same version, is granted an active
    # project — so the refusal is the archived project's, not the session's.
    other = _accepted(_grant(rt, session, version, open_project["project_id"]), "session_access")
    assert other["changed"] is True
    assert sorted(other["access"]["granted_project_ids"]) == sorted(
        [archived["project_id"], open_project["project_id"]]
    )


def test_every_repeated_transition_answers_unchanged(semantic_runtime):
    """RT6: every repeated transition of A05 rule 1 answers the record unchanged.

    For each: a control transition that changes state first, then the repeat
    at a later instant: same revision, last-changed instant and access
    version, `changed: false`, no audit entry (and so no confirmation id),
    the store unchanged.
    """
    rt = semantic_runtime

    def repeat(call, answer_kind):
        entries = _audit(rt)
        store_before = _store(rt)
        rt.clock.advance(minutes=7)
        answer = _accepted(call(), answer_kind)
        assert answer["changed"] is False, answer
        # A05 rule 2; A14 rules 3, 5: no entry, so no confirmation id.
        assert _audit(rt) == entries
        assert _store(rt) == store_before
        return answer

    # -- Archiving an archived project (R0-12); archive is a confirmed action.
    project = _create_project(rt, name="A05 to archive")
    pid = project["project_id"]
    rt.clock.advance(minutes=1)
    archived = _accepted(rt.owner("archive_project", target=pid, stated_version=1), "project_card")
    assert archived["changed"] is True
    assert archived["card"]["status"] == "archived"
    assert archived["card"]["revision"] == 2
    entry = _audit(rt)[-1]
    assert entry["action"] == "project_archived"
    assert entry["confirmation_id"] is not None  # control: a real one mints one
    again = repeat(
        lambda: rt.owner("archive_project", target=pid, stated_version=2),
        "project_card",
    )
    assert again["card"] == archived["card"]
    assert _read_project(rt, pid) == archived["card"]

    # -- Anonymising an anonymised project (R0-71). The erased form has no
    # revision, so the repeat states none (A04 rule 3).
    rt.clock.advance(minutes=1)
    anonymised = _accepted(
        rt.owner("erase_project", target=pid, stated_version=2, erasure="anonymise"),
        "project_erased",
    )
    assert anonymised["changed"] is True
    assert _audit(rt)[-1]["action"] == "project_anonymised"
    erased_form = _read_project(rt, pid)
    again = repeat(
        lambda: rt.owner("erase_project", target=pid, stated_version=None, erasure="anonymise"),
        "project_erased",
    )
    assert again["project_id"] == pid
    assert again["erasure"] == "anonymise"
    assert _read_project(rt, pid) == erased_form

    # -- Erasing an erased Customer (Primary actions).
    customer = _record_customer(rt, name="Erased Customer")
    ref = customer["customer_ref"]
    rt.clock.advance(minutes=1)
    erased = _accepted(rt.owner("erase_customer", target=ref, stated_version=1), "customer")
    assert erased["changed"] is True
    assert _audit(rt)[-1]["action"] == "customer_erased"
    again = repeat(
        lambda: rt.owner("erase_customer", target=ref, stated_version=None),
        "customer",
    )
    assert again["customer"] == erased["customer"]  # erased_at stays
    assert _read_customer(rt, ref) == erased["customer"]

    # -- Lifting an unrestricted Customer, resuming one that is not ended.
    marked = _record_customer(rt, name="Marked Customer")
    mref = marked["customer_ref"]
    again = repeat(lambda: _mark(rt, mref, 1, "lift"), "customer")
    assert again["customer"] == marked
    again = repeat(lambda: _mark(rt, mref, 1, "resume"), "customer")
    assert again["customer"] == marked
    # Control: after a restriction and an end, lift and resume are changes.
    restricted = _accepted(_mark(rt, mref, 1, "restrict"), "customer")["customer"]
    ended = _accepted(_mark(rt, mref, 2, "end"), "customer")["customer"]
    assert ended["revision"] == 3
    lifted = _accepted(_mark(rt, mref, 3, "lift"), "customer")
    assert lifted["changed"] is True
    assert lifted["customer"]["restricted_at"] is None
    resumed = _accepted(_mark(rt, mref, 4, "resume"), "customer")
    assert resumed["changed"] is True
    assert resumed["customer"]["relationship_ended_on"] is None
    assert restricted["revision"] == 2
    # And repeated again after those changes, still unchanged at revision 5.
    again = repeat(lambda: _mark(rt, mref, 5, "lift"), "customer")
    assert again["customer"] == resumed["customer"]

    # -- Registering a registered session (R0-53): its registration instant,
    # its granted set, active project and access version stay. The session is
    # given a project first, so a re-registration that resets the session to
    # an empty one is told apart from a repeat.
    session = "a05-session-every"
    registered = _register(rt, session)
    assert registered["changed"] is True  # control: a new session is a change
    registered_at = _registered_at(rt, session)
    active = _create_project(rt, name="A05 active")
    aid = active["project_id"]
    granted = _accepted(_grant(rt, session, 1, aid, make_active=True), "session_access")
    assert granted["access"]["granted_project_ids"] == [aid]
    assert granted["access"]["active_project_id"] == aid
    version = granted["access"]["access_version"]
    again = repeat(
        lambda: rt.service(KERNEL, "register_agent_session", kernel_session=session),
        "session_access",
    )
    assert again["access"] == granted["access"]
    assert _registered_at(rt, session) == registered_at

    # -- Making the active project active again; clearing an active project
    # that is already clear.
    again = repeat(lambda: _set_active(rt, session, version, aid), "session_access")
    assert again["access"] == granted["access"]
    # Control: clearing it is a change and moves the version by one.
    cleared = _accepted(_set_active(rt, session, version, None), "session_access")
    assert cleared["changed"] is True
    assert cleared["access"]["active_project_id"] is None
    assert cleared["access"]["granted_project_ids"] == [aid]  # clearing revokes nothing
    assert cleared["access"]["access_version"] == version + 1
    again = repeat(
        lambda: _set_active(rt, session, version + 1, None),
        "session_access",
    )
    assert again["access"] == cleared["access"]
    assert _read_session(rt, session) == cleared["access"]
