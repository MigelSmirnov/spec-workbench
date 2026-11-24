"""Witness tests for accepted decision A01 (02_rules_records.md).

A create carries a request id; its repeat changes nothing. 'Create a
project', 'record a customer', 'add a room' and 'publish an artifact pointer'
each carry a request id the caller makes (rule 1); Registry keeps it with the
record, written once (rule 2). A repeat passes stages (1) to (4) of A04 rule 6
and, for a room or a publish, the archive check of its project (rule 3); it is
looked up among the records of its model — of its project for a room or a
pointer (rule 4); equal current facts answer the record as it stands and change
nothing (rule 4), other facts are refused as a conflict (rule 5); facts compare
as A02 reads them, a publish's project and publisher among them (rule 6); a
create without one is refused and creates of one request id are applied one at
a time (rule 7); anonymisation or erasure takes the request id away, and a later
create with it is a new create (rule 8). Each witness test carries the name its
Required test declares; the untagged Required tests 3, 5 and 6 have a test
named by what they show.

The Factory project `registry` supplies the ``semantic_runtime`` fixture
(``RUNTIME_SURFACE.md``). Each test gets a fresh, empty instance. Expected
values come from State 2 (A01, A02, A04 rule 6, A10), State 5 (the operations
of ``50_public_apis_3_records.md`` and ``50_public_apis_2_sessions.md``, and
"Closed set of refusal codes" in ``50_public_apis_0_conventions.md``), State 6
(the answer models of ``60_model_closure_values.json``) and the data provider's
constants (``70_data_provider_closure.json``).

Surface used here:

- ``owner(action, target=None, stated_version=None, **values)`` with the
  actions ``create_project``, ``correct_project``, ``archive_project``,
  ``erase_project`` (confirmation steps confirmed by the fixture),
  ``read_project``, ``list_projects``, ``record_customer``, ``read_customer``,
  ``list_customers``, ``add_room``, ``publish_pointer``, ``list_pointers``,
  ``list_sessions``, ``grant_project``, ``revoke_project``;
- ``service(name, operation, inputs=None, kernel_session=None, token=...)``
  with ``register_agent_session``, ``add_room``, ``publish_artifact_pointer``
  for ``cabinet_kernel``, and ``add_room`` for ``presupro``;
- ``new_request_id()``, ``clock.advance``, ``store_rows(table)``;
- ``stop()``, ``start()``, ``sign_in()`` and
  ``configure_release(**constants)``: after ``stop()`` and before
  ``start()``, the instance runs over the same store on a test release whose
  named data-provider constants hold the values given; here
  ``ARTIFACT_TYPE_OWNERS=[]``, a release that removed `estimate` (A22 rules
  2-5);
- two surface calls made from two threads at once (Required test 12).
"""

import json
import threading
from concurrent.futures import ThreadPoolExecutor

# State 5, "Closed set of refusal codes"; stages are the data provider's
# REFUSAL_STAGE_* constants (70_data_provider_closure.json).
STAGE_AUTHENTICATION = 1  # REFUSAL_STAGE_AUTHENTICATION
STAGE_AGENT_SESSION = 2  # REFUSAL_STAGE_AGENT_SESSION
STAGE_EXISTENCE = 3  # REFUSAL_STAGE_EXISTENCE
STAGE_VALUES = 4  # REFUSAL_STAGE_VALUES
STAGE_LIFECYCLE = 6  # REFUSAL_STAGE_LIFECYCLE

KERNEL = "cabinet_kernel"  # State 6 ServiceName
PRESUPRO = "presupro"

# A22 rule 1 / ARTIFACT_TYPE_OWNERS: the first release declares `estimate`,
# owner service PresuPro.
ESTIMATE = "estimate"

# Every table a create or its repeat could write (60_data_closure.json,
# config.persistence); a repeat or a refusal leaves all of them as they were.
TABLES = (
    "project_rows",
    "room_rows",
    "customer_rows",
    "pointer_rows",
    "agent_session_rows",
    "audit_entry_rows",
    "audit_sequence_rows",
)


# --- helpers -------------------------------------------------------------


def _project_facts(display_name="Casa Norte", address="Calle Mayor 1, Valencia", **more):
    """State 6 GivenProjectFacts: every field present, unnamed ones None."""
    facts = {
        "display_name": display_name,
        "alias": None,
        "customer_ref": None,
        "address": address,
        "object_kind": None,
        "floor_area": None,
        "rooms_count": None,
        "floor": None,
    }
    facts.update(more)
    return facts


def _customer_facts(name="Ana Ruiz", customer_kind="person", **more):
    """State 6 GivenCustomerFacts."""
    facts = {
        "name": name,
        "customer_kind": customer_kind,
        "phone": None,
        "email": None,
        "language": None,
        "tax_id": None,
        "legal_name": None,
    }
    facts.update(more)
    return facts


def _pointer(uri="https://presupro.example/estimates/1", artifact_type=ESTIMATE):
    """State 6 GivenPointer."""
    return {
        "artifact_type": artifact_type,
        "uri": uri,
        "payload_ref": None,
        "content_digest": None,
    }


def _inputs(**given):
    """State 6 ServiceInputs: every field present, unnamed ones None."""
    inputs = {
        "project_id": None,
        "customer_ref": None,
        "artifact_type": None,
        "pointer_id": None,
        "list_choice": None,
        "room_name": None,
        "request_id": None,
        "pointer": None,
        "request_text": None,
    }
    inputs.update(given)
    return inputs


def _store(rt):
    return {table: rt.store_rows(table) for table in TABLES}


def _refused(answer, code, stage, kinds):
    """State 5 'Closed set of refusal codes': code, stage, the failing kinds."""
    assert answer["answer_kind"] == "refused", answer
    assert answer["code"] == code, answer
    assert answer["stage"] == stage, answer
    assert [failure["kind"] for failure in answer["failures"]] == kinds, answer


def _card(answer):
    """State 6 ProjectCardAnswer -> its card (ProjectCard or AnonymisedProject)."""
    assert answer["answer_kind"] == "project_card", answer
    return answer["card"]


def _create_project(rt, request_id, **facts):
    return rt.owner("create_project", request_id=request_id, project=_project_facts(**facts))


def _read_card(rt, project_id):
    return _card(rt.owner("read_project", target=project_id))


def _listed_ids(rt, list_choice="with_archived"):
    # State 6 ProjectListChoice: `active` or `with_archived`.
    answer = rt.owner("list_projects", list_choice=list_choice)
    assert answer["answer_kind"] == "project_list", answer
    return [item["project_id"] for item in answer["items"]]


def _new_project(rt, **facts):
    answer = _create_project(rt, rt.new_request_id(), **facts)
    return _card(answer)["project_id"]


def _owner_rooms(rt, project_id):
    return _read_card(rt, project_id)["rooms"]


def _owner_pointers(rt, project_id):
    answer = rt.owner("list_pointers", target=project_id)
    assert answer["answer_kind"] == "pointers", answer
    return answer["pointers"]


def _kernel(rt, session_id, operation, **given):
    return rt.service(KERNEL, operation, inputs=_inputs(**given), kernel_session=session_id)


def _register(rt, session_id):
    answer = rt.service(KERNEL, "register_agent_session", inputs=None, kernel_session=session_id)
    assert answer["answer_kind"] != "refused", answer


def _session_item(rt, session_id):
    answer = rt.owner("list_sessions")
    assert answer["answer_kind"] == "session_list", answer
    [item] = [i for i in answer["items"] if i["access"]["session_id"] == session_id]
    return item


def _grant(rt, session_id, project_id):
    # State 6 OwnerValues: a grant acts on the session and names the project as
    # `project_id`; it states the access version (A12, 60_contracts.md).
    version = _session_item(rt, session_id)["access"]["access_version"]
    rt.owner(
        "grant_project",
        target=session_id,
        stated_version=version,
        project_id=project_id,
        make_active=False,
    )
    assert project_id in _session_item(rt, session_id)["access"]["granted_project_ids"]


def _revoke(rt, session_id, project_id):
    version = _session_item(rt, session_id)["access"]["access_version"]
    rt.owner("revoke_project", target=session_id, stated_version=version, project_id=project_id)
    assert project_id not in _session_item(rt, session_id)["access"]["granted_project_ids"]


def _kernel_project(rt, session_id):
    """A registered Kernel session with one active-status project in its set."""
    _register(rt, session_id)
    project_id = _new_project(rt)
    _grant(rt, session_id, project_id)
    return project_id


def _archive(rt, project_id):
    revision = _read_card(rt, project_id)["revision"]
    card = _card(rt.owner("archive_project", target=project_id, stated_version=revision))
    assert card["status"] == "archived", card
    return card


def _remove_estimate(rt):
    """A22 rule 4: restart on a release whose ARTIFACT_TYPE_OWNERS no longer
    declares `estimate`, the first release's only type."""
    rt.stop()
    rt.configure_release(ARTIFACT_TYPE_OWNERS=[])
    assert rt.start() is None
    rt.sign_in()


def _at_once(*calls):
    """Run the calls from separate threads released together; answers in call order."""
    barrier = threading.Barrier(len(calls))

    def run(call):
        barrier.wait()
        return call()

    with ThreadPoolExecutor(max_workers=len(calls)) as pool:
        futures = [pool.submit(run, call) for call in calls]
        return [future.result() for future in futures]


# --- Required test 1 -----------------------------------------------------


def test_equal_repeat_answers_existing_project(semantic_runtime):
    """[witness: verification:registry_a01_equal_repeat_answers_existing_project]

    A01 Required test 1: two 'create a project' calls with the same request id
    and equal facts make one project; the second answers it. Shows A01-1,
    A01-3.
    """
    rt = semantic_runtime
    request_id = rt.new_request_id()

    first = _create_project(rt, request_id)
    # State 5 'Repeats': a create answers `changed`; a new record is a change.
    assert first["changed"] is True, first
    card = _card(first)
    project_id = card["project_id"]
    # State 5 create_project: a new Project is active at revision 1
    # (REVISION_FIRST = 1).
    assert card["status"] == "active"
    assert card["revision"] == 1

    rt.clock.advance(minutes=5)
    before = _store(rt)
    second = _create_project(rt, request_id)

    # A01 rule 4 / A01-3: the record as it stands now, unchanged; nothing moved,
    # its last-changed instant included although the clock moved.
    assert second["changed"] is False, second
    assert _card(second) == card
    assert _store(rt) == before
    assert _read_card(rt, project_id) == card
    # A01-1: one project carries the request id.
    assert _listed_ids(rt) == [project_id]
    # A01 rule 9, State 5 "What answers never carry": the stored request id is
    # in neither answer.
    assert request_id not in json.dumps(first)
    assert request_id not in json.dumps(second)

    # Control: equal facts under another request id are a second project —
    # Registry never merges look-alike records (A01 Consequence, R0-34).
    other = _create_project(rt, rt.new_request_id())
    assert other["changed"] is True, other
    assert _card(other)["project_id"] != project_id
    assert sorted(_listed_ids(rt)) == sorted([project_id, _card(other)["project_id"]])


# --- Required test 2 -----------------------------------------------------


def test_same_request_id_other_name_refused(semantic_runtime):
    """[witness: verification:registry_a01_same_request_id_other_name_refused]

    A01 Required test 2: the same request id with a different display name is
    refused and nothing changes. Shows A01-4.
    """
    rt = semantic_runtime
    request_id = rt.new_request_id()
    card = _card(_create_project(rt, request_id, display_name="Casa Norte"))
    project_id = card["project_id"]

    before = _store(rt)
    answer = _create_project(rt, request_id, display_name="Casa Sur")

    # A01 rule 5; State 5 create_project Errors `refused` (`conflict`), stage (6).
    _refused(answer, "refused", STAGE_LIFECYCLE, ["conflict"])
    assert _store(rt) == before
    assert _read_card(rt, project_id) == card
    assert _listed_ids(rt) == [project_id]

    # Control: the equal repeat is still answered (A01 rule 4).
    again = _create_project(rt, request_id, display_name="Casa Norte")
    assert again["changed"] is False, again
    assert _card(again) == card


# --- Required test 3 (untagged) -------------------------------------------


def test_rooms_with_other_request_ids_and_one_name_are_two(semantic_runtime):
    """A01 Required test 3: two 'add a room' calls with different request ids
    and the same name make two rooms (R0-10)."""
    rt = semantic_runtime
    project_id = _new_project(rt)

    first = rt.owner("add_room", target=project_id, room_name="Cocina", request_id=rt.new_request_id())
    second = rt.owner("add_room", target=project_id, room_name="Cocina", request_id=rt.new_request_id())

    # State 6 RoomAnswer; State 5 add_room: "A room of the same name is a
    # second room".
    for answer in (first, second):
        assert answer["answer_kind"] == "room", answer
        assert answer["changed"] is True, answer
        assert answer["room"]["name"] == "Cocina"
    assert first["room"]["room_id"] != second["room"]["room_id"]

    rooms = _owner_rooms(rt, project_id)
    assert sorted(room["room_id"] for room in rooms) == sorted(
        [first["room"]["room_id"], second["room"]["room_id"]]
    )
    assert [room["name"] for room in rooms] == ["Cocina", "Cocina"]


# --- Required test 4 -----------------------------------------------------


def test_repeat_after_archive_not_reactivated(semantic_runtime):
    """[witness: verification:registry_a01_repeat_after_archive_not_reactivated]

    A01 Required test 4: a repeat of a project's create after the project was
    archived answers the archived project and does not reactivate it. Shows
    A01-3.
    """
    rt = semantic_runtime
    request_id = rt.new_request_id()
    project_id = _card(_create_project(rt, request_id))["project_id"]
    rt.clock.advance(minutes=1)
    archived = _archive(rt, project_id)
    # A04-3: archiving moved the revision once.
    assert archived["revision"] == 2

    rt.clock.advance(minutes=1)
    before = _store(rt)
    repeat = _create_project(rt, request_id)

    # A01 rule 4: answered as it stands now — archived, revision 2 — and
    # nothing changes (State 5 create_project: "archived included").
    assert repeat["changed"] is False, repeat
    card = _card(repeat)
    assert card["project_id"] == project_id
    assert card["status"] == "archived"
    assert card["revision"] == 2
    assert card == _read_card(rt, project_id)
    assert card["last_changed_at"] == archived["last_changed_at"]
    assert _store(rt) == before
    # Not reactivated: absent from the active list, archived in the full one.
    assert project_id not in _listed_ids(rt, "active")
    assert _listed_ids(rt, "with_archived") == [project_id]


# --- Required test 5 (untagged) -------------------------------------------


def test_create_without_request_id_refused(semantic_runtime):
    """A01 Required test 5: a create without a request id is refused (A01 rule
    7), for each of the four creates; a blank one is missing (A01 rule 1)."""
    rt = semantic_runtime
    project_id = _new_project(rt)

    creates = {
        "create_project": lambda request_id: rt.owner(
            "create_project", request_id=request_id, project=_project_facts(display_name="Otra")
        ),
        "record_customer": lambda request_id: rt.owner(
            "record_customer", request_id=request_id, customer=_customer_facts()
        ),
        "add_room": lambda request_id: rt.owner(
            "add_room", target=project_id, room_name="Baño", request_id=request_id
        ),
        "publish_pointer": lambda request_id: rt.owner(
            "publish_pointer", target=project_id, pointer=_pointer(), request_id=request_id
        ),
    }

    before = _store(rt)
    for action, create in creates.items():
        for missing in (None, "", "   "):
            # State 5: `invalid_request` (`missing_value`) at stage (4); A02
            # rule 1: blank is missing.
            answer = create(missing)
            _refused(answer, "invalid_request", STAGE_VALUES, ["missing_value"])
            assert any(
                element.get("name") == "request_id" for element in answer["failures"][0]["path"]
            ), (action, answer)
    assert _store(rt) == before

    # Control: the same creates with a request id are accepted.
    for action, create in creates.items():
        answer = create(rt.new_request_id())
        assert answer["answer_kind"] != "refused", (action, answer)
        assert answer["changed"] is True, (action, answer)


# --- Required test 6 (untagged) -------------------------------------------


def test_former_request_id_after_anonymisation_makes_new_project(semantic_runtime):
    """A01 Required test 6: after anonymising a project, a create with that
    project's former request id makes a new project with a new id (A01 rule
    8)."""
    rt = semantic_runtime
    request_id = rt.new_request_id()
    project_id = _card(_create_project(rt, request_id))["project_id"]
    archived = _archive(rt, project_id)
    erased = rt.owner(
        "erase_project",
        target=project_id,
        stated_version=archived["revision"],
        erasure="anonymise",
    )
    # State 6 ProjectErasedAnswer.
    assert erased["answer_kind"] == "project_erased", erased
    assert erased["changed"] is True

    answer = _create_project(rt, request_id)

    # A01 rule 8: a new create, answered with the new record it made — so not
    # silent (`changed` true), a new id, active at revision 1.
    assert answer["changed"] is True, answer
    card = _card(answer)
    assert card["project_id"] != project_id
    assert card["status"] == "active"
    assert card["revision"] == 1
    # The anonymised project stays its erased form (State 5 conventions,
    # "Erased records answer").
    # The wire carries no `view_kind`: the form is told by its fields.
    old = _read_card(rt, project_id)
    assert set(old) == {"project_id", "status"}, old
    assert old["status"] == "archived"
    assert card["project_id"] in _listed_ids(rt)


# --- Required test 7 -----------------------------------------------------


def test_publish_retry_returns_same_pointer(semantic_runtime):
    """[witness: verification:registry_a01_publish_retry_returns_same_pointer]

    A01 Required test 7: Kernel retrying a publish with the same request id
    gets the same pointer and version; the pointer it made is not superseded.
    Shows A01-1, A01-3.
    """
    rt = semantic_runtime
    session_id = "kernel-session-a01-publish"
    project_id = _kernel_project(rt, session_id)
    request_id = rt.new_request_id()

    first = _kernel(rt, session_id, "publish_artifact_pointer",
                    project_id=project_id, pointer=_pointer(), request_id=request_id)
    assert first["answer_kind"] == "pointer", first
    assert first["changed"] is True
    pointer = first["pointer"]
    # A07 rule 1: the first pointer of its type, version 1, published.
    assert pointer["version"] == 1
    assert pointer["status"] == "published"

    rt.clock.advance(minutes=2)
    before = _store(rt)
    retry = _kernel(rt, session_id, "publish_artifact_pointer",
                    project_id=project_id, pointer=_pointer(), request_id=request_id)

    # A01 rule 4: the same pointer, as it stands, nothing changed; it neither
    # supersedes nor makes a version.
    assert retry["answer_kind"] == "pointer", retry
    assert retry["changed"] is False
    assert retry["pointer"] == pointer
    assert _store(rt) == before
    listed = _owner_pointers(rt, project_id)
    assert listed == [pointer]
    assert listed[0]["status"] == "published"
    assert listed[0]["superseded_at"] is None

    # Control: a publish under a new request id is a new version and
    # supersedes the first (A07 rule 1) — so the retry above would have shown
    # it, had it been taken as new.
    newer = _kernel(rt, session_id, "publish_artifact_pointer",
                    project_id=project_id,
                    pointer=_pointer(uri="https://presupro.example/estimates/2"),
                    request_id=rt.new_request_id())
    assert newer["changed"] is True
    assert newer["pointer"]["version"] == 2

    # A01 rule 4: a repeat answers its pointer whatever its status now —
    # superseded — and makes no version.
    before = _store(rt)
    late = _kernel(rt, session_id, "publish_artifact_pointer",
                   project_id=project_id, pointer=_pointer(), request_id=request_id)
    assert late["changed"] is False, late
    assert late["pointer"]["pointer_id"] == pointer["pointer_id"]
    assert late["pointer"]["version"] == 1
    assert late["pointer"]["status"] == "superseded"
    assert _store(rt) == before
    statuses = {p["pointer_id"]: (p["version"], p["status"]) for p in _owner_pointers(rt, project_id)}
    assert statuses == {
        pointer["pointer_id"]: (1, "superseded"),
        newer["pointer"]["pointer_id"]: (2, "published"),
    }


# --- Required test 8 -----------------------------------------------------


def test_repeat_after_correction_refused(semantic_runtime):
    """[witness: verification:registry_a01_repeat_after_correction_refused]

    A01 Required test 8: a repeat of a project's create after the project was
    corrected is refused. Shows A01-4.
    """
    rt = semantic_runtime
    request_id = rt.new_request_id()
    project_id = _card(_create_project(rt, request_id, display_name="Casa Norte"))["project_id"]

    # Control: before the correction the repeat is answered (A01 rule 4).
    assert _create_project(rt, request_id, display_name="Casa Norte")["changed"] is False

    corrected = _card(rt.owner(
        "correct_project", target=project_id, stated_version=1,
        project=_project_facts(display_name="Casa Sur"),
    ))
    assert corrected["display_name"] == "Casa Sur"
    assert corrected["revision"] == 2

    before = _store(rt)
    answer = _create_project(rt, request_id, display_name="Casa Norte")

    # A01 rule 5: the record corrected since — its current facts differ —
    # is refused as a conflict at stage (6); nothing changes.
    _refused(answer, "refused", STAGE_LIFECYCLE, ["conflict"])
    assert _store(rt) == before
    assert _read_card(rt, project_id) == corrected


# --- Required test 9 -----------------------------------------------------


def test_blank_optional_equals_absent_on_repeat(semantic_runtime):
    """[witness: verification:registry_a01_blank_optional_equals_absent_on_repeat]

    A01 Required test 9: a repeat of 'record a customer' giving an empty
    e-mail equals one that gave none. Shows A01-3.
    """
    rt = semantic_runtime

    def record(request_id, **facts):
        return rt.owner("record_customer", request_id=request_id, customer=_customer_facts(**facts))

    def customers():
        answer = rt.owner("list_customers")
        assert answer["answer_kind"] == "customer_list", answer
        return [item["customer_ref"] for item in answer["items"]]

    # Given none, repeated blank.
    request_id = rt.new_request_id()
    first = record(request_id)
    assert first["answer_kind"] == "customer", first
    assert first["changed"] is True
    customer = first["customer"]
    assert customer["email"] is None

    before = _store(rt)
    # A01 rule 6 + A02 rule 3: an optional value given blank is the same as
    # one not given, so these are repeats.
    for blank in ("", "   "):
        repeat = record(request_id, email=blank)
        assert repeat["answer_kind"] == "customer", repeat
        assert repeat["changed"] is False, repeat
        assert repeat["customer"] == customer
    assert _store(rt) == before
    assert customers() == [customer["customer_ref"]]

    # Control: an e-mail actually given is another fact — a conflict (A01
    # rule 5), so equality is not "ignore the e-mail".
    _refused(record(request_id, email="ana@example.es"), "refused", STAGE_LIFECYCLE, ["conflict"])
    assert _store(rt) == before

    # Given blank, repeated with none.
    other_id = rt.new_request_id()
    blank_first = record(other_id, name="Luis Gómez", email="")
    assert blank_first["changed"] is True
    assert blank_first["customer"]["email"] is None  # A02 rule 3: absent
    before = _store(rt)
    repeat = record(other_id, name="Luis Gómez")
    assert repeat["changed"] is False, repeat
    assert repeat["customer"] == blank_first["customer"]
    assert _store(rt) == before


# --- Required test 10 ----------------------------------------------------


def test_repeat_outside_session_set_not_found(semantic_runtime):
    """[witness: verification:registry_a01_repeat_outside_session_set_not_found]

    A01 Required test 10: Kernel repeating 'add a room' after the project left
    its session's set is answered as not found (A10). Shows A01-2.
    """
    rt = semantic_runtime
    session_id = "kernel-session-a01-outside"
    project_id = _kernel_project(rt, session_id)
    request_id = rt.new_request_id()

    def add():
        return _kernel(rt, session_id, "add_room",
                       project_id=project_id, room_name="Salón", request_id=request_id)

    first = add()
    assert first["answer_kind"] == "room", first
    assert first["changed"] is True
    # Control: inside the set the repeat answers the room (A01 rule 4).
    inside = add()
    assert inside["changed"] is False, inside
    assert inside["room"] == first["room"]

    _revoke(rt, session_id, project_id)
    before = _store(rt)
    outside = add()

    # A01 rule 3 + A10 rules 1, 3: stage (2) refuses before the repeat is
    # recognised; State 5: `not_found` (`agent_call_refused`), stage (2).
    _refused(outside, "not_found", STAGE_AGENT_SESSION, ["agent_call_refused"])
    assert _store(rt) == before
    assert [room["room_id"] for room in _owner_rooms(rt, project_id)] == [first["room"]["room_id"]]

    # A10 rule 3 / A10-2: the same answer as for a project that does not exist.
    unknown = _kernel(rt, session_id, "add_room",
                      project_id="no-such-project-a01", room_name="Salón", request_id=request_id)
    assert outside == unknown


# --- Required test 11 ----------------------------------------------------


def test_repeat_publish_removed_type_refused(semantic_runtime):
    """[witness: verification:registry_a01_repeat_publish_removed_type_refused]

    A01 Required test 11: repeating a publish after its type was removed is
    refused as an unknown type (A22). Shows A01-2.
    """
    rt = semantic_runtime
    session_id = "kernel-session-a01-removed"
    project_id = _kernel_project(rt, session_id)
    request_id = rt.new_request_id()

    def publish():
        return _kernel(rt, session_id, "publish_artifact_pointer",
                       project_id=project_id, pointer=_pointer(), request_id=request_id)

    first = publish()
    assert first["changed"] is True, first
    # Control: in the release that declares `estimate`, the repeat answers.
    assert publish()["changed"] is False

    # A22 rule 4: a release without `estimate` (the only declared type).
    _remove_estimate(rt)
    before = _store(rt)
    answer = publish()

    # A01 rule 3: the publish's type is checked at stage (4) for a repeat too;
    # A22 rule 5 / State 5: `invalid_request` (`unknown_artifact_type`).
    _refused(answer, "invalid_request", STAGE_VALUES, ["unknown_artifact_type"])
    assert _store(rt) == before
    # A22 rule 4: the pointer is kept as it was.
    assert _owner_pointers(rt, project_id) == [first["pointer"]]


# --- Required test 12 ----------------------------------------------------


def test_concurrent_creates_make_one_record(semantic_runtime):
    """[witness: verification:registry_a01_concurrent_creates_make_one_record]

    A01 Required test 12: two concurrent creates with one request id and equal
    facts — of a project, a Customer, a room of one project, a pointer of one
    project by one publisher (Kernel naming one session) — make one record; the
    other answers it. With different facts, or another publisher, the second
    is refused as a conflict. The same request id for rooms of two different
    projects makes two rooms. Shows A01-1, A01-3, A01-4.
    """
    rt = semantic_runtime
    session_id = "kernel-session-a01-concurrent"
    project_id = _kernel_project(rt, session_id)
    second_project = _new_project(rt, display_name="Casa Este")
    _grant(rt, session_id, second_project)
    rt.owner("list_projects")  # the owner session is open before the threads

    def one_record(answers):
        # A01 rule 7: applied one at a time — one made it, the other is its
        # repeat (A01 rule 4).
        for answer in answers:
            assert answer["answer_kind"] != "refused", answers
        assert sorted(answer["changed"] for answer in answers) == [False, True], answers

    def race(calls, table, records, entries):
        """Two calls at once, and the store read before and after them.

        A01-3, A01-4 under concurrency: the store afterwards is the store
        before plus what the one accepted create writes — `records` new rows
        of its own table and `entries` audit entries (M09, "the actions that
        write an entry": creating a project and recording a customer write
        one; adding a room and publishing a pointer none) — every row held
        before unchanged and no other table touched. The repeat answered, or
        the conflict refused, wrote nothing of its own.
        """
        before = _store(rt)
        answers = _at_once(*calls)
        after = _store(rt)
        for name in TABLES:
            old, new = before[name], after[name]
            for row in old:
                if name != "audit_sequence_rows":
                    assert row in new, (name, row)
            if name == "audit_sequence_rows":
                # M12: the one sequence row moves only with a written entry.
                assert len(new) == len(old) or not old, (name, new)
                if not entries:
                    assert new == old, (name, old, new)
                continue
            grown = {table: records, "audit_entry_rows": entries}.get(name, 0)
            assert len(new) == len(old) + grown, (name, old, new)
        return answers

    def one_made_one_conflict(answers):
        # A01 rule 5: the second is refused as a conflict, stage (6).
        accepted = [a for a in answers if a["answer_kind"] != "refused"]
        refused = [a for a in answers if a["answer_kind"] == "refused"]
        assert len(accepted) == 1 and len(refused) == 1, answers
        assert accepted[0]["changed"] is True
        _refused(refused[0], "refused", STAGE_LIFECYCLE, ["conflict"])
        return accepted[0]

    # Projects, equal facts.
    k = rt.new_request_id()
    answers = race(
        (lambda: _create_project(rt, k), lambda: _create_project(rt, k)),
        "project_rows", 1, 1,
    )
    one_record(answers)
    assert _card(answers[0]) == _card(answers[1])
    made_project = _card(answers[0])["project_id"]

    # Projects, different facts.
    k = rt.new_request_id()
    answers = race(
        (
            lambda: _create_project(rt, k, display_name="Casa Oeste"),
            lambda: _create_project(rt, k, display_name="Casa Sur"),
        ),
        "project_rows", 1, 1,
    )
    other_project = _card(one_made_one_conflict(answers))["project_id"]
    assert sorted(_listed_ids(rt)) == sorted([project_id, second_project, made_project, other_project])

    # Customers, equal facts, then different facts.
    k = rt.new_request_id()
    record = lambda **facts: rt.owner("record_customer", request_id=k, customer=_customer_facts(**facts))  # noqa: E731
    answers = race((record, record), "customer_rows", 1, 1)
    one_record(answers)
    assert answers[0]["customer"] == answers[1]["customer"]
    k = rt.new_request_id()
    answers = race(
        (lambda: record(name="Eva Martín"), lambda: record(name="Eva Martin")),
        "customer_rows", 1, 1,
    )
    one_made_one_conflict(answers)
    listed = rt.owner("list_customers")["items"]
    assert len(listed) == 2

    # Rooms of one project by Kernel, equal facts, then different facts.
    k = rt.new_request_id()
    add = lambda name, project=project_id: _kernel(  # noqa: E731
        rt, session_id, "add_room", project_id=project, room_name=name, request_id=k
    )
    answers = race((lambda: add("Cocina"), lambda: add("Cocina")), "room_rows", 1, 0)
    one_record(answers)
    assert answers[0]["room"] == answers[1]["room"]
    k = rt.new_request_id()
    answers = race((lambda: add("Baño"), lambda: add("Aseo")), "room_rows", 1, 0)
    one_made_one_conflict(answers)
    assert len(_owner_rooms(rt, project_id)) == 2

    # One request id for rooms of two different projects: two rooms — the
    # lookup is among the rooms of the call's project (A01 rule 4, A01-1).
    k = rt.new_request_id()
    answers = race(
        (lambda: add("Terraza", project_id), lambda: add("Terraza", second_project)),
        "room_rows", 2, 0,
    )
    for answer in answers:
        assert answer["answer_kind"] == "room", answers
        assert answer["changed"] is True, answers
    assert answers[0]["room"]["room_id"] != answers[1]["room"]["room_id"]
    assert "Terraza" in [r["name"] for r in _owner_rooms(rt, project_id)]
    assert [r["name"] for r in _owner_rooms(rt, second_project)] == ["Terraza"]

    # Pointers of one project by one publisher (Kernel, one session).
    k = rt.new_request_id()
    by_kernel = lambda: _kernel(  # noqa: E731
        rt, session_id, "publish_artifact_pointer",
        project_id=second_project, pointer=_pointer(), request_id=k,
    )
    answers = race((by_kernel, by_kernel), "pointer_rows", 1, 0)
    one_record(answers)
    assert answers[0]["pointer"] == answers[1]["pointer"]
    assert answers[0]["pointer"]["version"] == 1
    assert len(_owner_pointers(rt, second_project)) == 1

    # Pointers of one project by one publisher, different facts (another
    # uri): one made, the other refused as a conflict (A01 rule 5). On a
    # project of its own, granted to the session, so that the pointer made is
    # the type's first and supersedes none: the store changes by that row.
    third_project = _new_project(rt, display_name="Casa Norte")
    _grant(rt, session_id, third_project)
    k = rt.new_request_id()
    by_kernel_uri = lambda uri: _kernel(  # noqa: E731
        rt, session_id, "publish_artifact_pointer",
        project_id=third_project, pointer=_pointer(uri=uri), request_id=k,
    )
    made_pointer = one_made_one_conflict(race(
        (
            lambda: by_kernel_uri("https://presupro.example/estimates/2"),
            lambda: by_kernel_uri("https://presupro.example/estimates/3"),
        ),
        "pointer_rows", 1, 0,
    ))
    assert made_pointer["pointer"]["version"] == 1
    assert len(_owner_pointers(rt, third_project)) == 1

    # Another publisher with the same request id and pointer: the owner beside
    # Kernel — the publisher is one of the facts (A01 rule 6).
    k = rt.new_request_id()
    by_kernel = lambda: _kernel(  # noqa: E731
        rt, session_id, "publish_artifact_pointer",
        project_id=project_id, pointer=_pointer(), request_id=k,
    )
    by_owner = lambda: rt.owner(  # noqa: E731
        "publish_pointer", target=project_id, pointer=_pointer(), request_id=k
    )
    one_made_one_conflict(race((by_kernel, by_owner), "pointer_rows", 1, 0))
    assert len(_owner_pointers(rt, project_id)) == 1

    # Another Kernel session as publisher: refused too (A01 rule 6).
    other_session = "kernel-session-a01-concurrent-2"
    _register(rt, other_session)
    _grant(rt, other_session, project_id)
    before = _store(rt)
    _refused(
        _kernel(rt, other_session, "publish_artifact_pointer",
                project_id=project_id, pointer=_pointer(), request_id=k),
        "refused", STAGE_LIFECYCLE, ["conflict"],
    )
    assert _store(rt) == before


# --- Required test 13 ----------------------------------------------------


def test_repeat_on_archived_project_refused(semantic_runtime):
    """[witness: verification:registry_a01_repeat_on_archived_project_refused]

    A01 Required test 13: a repeat with equal facts of 'add a room' or of a
    publish, after its project was archived, is refused and nothing changes.
    Shows A01-2.
    """
    rt = semantic_runtime
    session_id = "kernel-session-a01-archived"
    project_id = _kernel_project(rt, session_id)
    kernel_room, kernel_pointer = rt.new_request_id(), rt.new_request_id()
    owner_room, owner_pointer = rt.new_request_id(), rt.new_request_id()

    repeats = {
        "kernel add_room": lambda: _kernel(
            rt, session_id, "add_room", project_id=project_id, room_name="Cocina", request_id=kernel_room
        ),
        "kernel publish": lambda: _kernel(
            rt, session_id, "publish_artifact_pointer",
            project_id=project_id, pointer=_pointer(), request_id=kernel_pointer,
        ),
        "owner add_room": lambda: rt.owner(
            "add_room", target=project_id, room_name="Baño", request_id=owner_room
        ),
        "owner publish": lambda: rt.owner(
            "publish_pointer", target=project_id,
            pointer=_pointer(uri="https://presupro.example/estimates/owner"),
            request_id=owner_pointer,
        ),
    }
    made = {}
    for name, call in repeats.items():
        answer = call()
        assert answer["answer_kind"] != "refused", (name, answer)
        assert answer["changed"] is True, (name, answer)
        made[name] = answer
    # Control: before the archive each repeat is answered unchanged.
    for name, call in repeats.items():
        assert call()["changed"] is False, name

    _archive(rt, project_id)
    # R0-70: archiving keeps the project in the session's set.
    assert project_id in _session_item(rt, session_id)["access"]["granted_project_ids"]
    before = _store(rt)
    card = _read_card(rt, project_id)
    pointers = _owner_pointers(rt, project_id)

    for name, call in repeats.items():
        # A01 rule 3: a repeat passes the archive check of its project; State
        # 5 add_room / publish_pointer: `refused` (`archived`), stage (6).
        _refused(call(), "refused", STAGE_LIFECYCLE, ["archived"])

    assert _store(rt) == before
    assert _read_card(rt, project_id) == card
    assert _owner_pointers(rt, project_id) == pointers


# --- Required test 14 ----------------------------------------------------


def test_repeat_failing_early_stage_refused(semantic_runtime):
    """[witness: verification:registry_a01_repeat_failing_early_stage_refused]

    A01 Required test 14: a repeat failing any check of stages (1) to (4) of
    A04 rule 6 is refused, is never answered as a repeat, and nothing changes:
    one from a service without the right (1); Kernel's after the project left
    its session's set (2); a room's on a project deleted whole since (3); one
    whose required value is now given blank, or a publish of a removed type
    (4). Shows A01-2.
    """
    rt = semantic_runtime
    session_id = "kernel-session-a01-early"
    project_id = _kernel_project(rt, session_id)
    room_id = rt.new_request_id()
    pointer_id = rt.new_request_id()
    project_request = rt.new_request_id()

    def kernel_room(name="Cocina", service=KERNEL, **token):
        # `token=None` sends no token (RUNTIME_SURFACE.md, `service`); a
        # service other than Kernel names no agent session.
        return rt.service(
            service, "add_room",
            inputs=_inputs(project_id=project_id, room_name=name, request_id=room_id),
            kernel_session=session_id if service == KERNEL else None,
            **token,
        )

    def kernel_publish():
        return _kernel(rt, session_id, "publish_artifact_pointer",
                       project_id=project_id, pointer=_pointer(), request_id=pointer_id)

    room = kernel_room()
    assert room["changed"] is True, room
    pointer = kernel_publish()
    assert pointer["changed"] is True, pointer
    project_card = _card(_create_project(rt, project_request))

    # Controls: each repeat is answered before its check fails.
    assert kernel_room()["changed"] is False
    assert kernel_publish()["changed"] is False
    assert _create_project(rt, project_request)["changed"] is False

    before = _store(rt)

    # (1) No token, then a service without the right: A09; State 5
    # `unauthenticated` (`no_valid_token`) and `not_permitted`
    # (`outside_service_rights`), stage (1). PresuPro has no `add_room` in the
    # imported SERVICE_RIGHTS.
    _refused(kernel_room(token=None), "unauthenticated", STAGE_AUTHENTICATION, ["no_valid_token"])
    _refused(kernel_room(service=PRESUPRO), "not_permitted", STAGE_AUTHENTICATION,
             ["outside_service_rights"])

    # (4) A required value now given blank: `missing_value`, never a repeat
    # and never a conflict (A02 rule 1).
    _refused(kernel_room(name="   "), "invalid_request", STAGE_VALUES, ["missing_value"])
    _refused(_create_project(rt, project_request, display_name="  "),
             "invalid_request", STAGE_VALUES, ["missing_value"])
    assert _store(rt) == before

    # (4) A publish of a removed type (A22 rule 5).
    _remove_estimate(rt)
    before = _store(rt)
    _refused(kernel_publish(), "invalid_request", STAGE_VALUES, ["unknown_artifact_type"])
    assert _store(rt) == before
    # Control: the room's repeat is still answered after the restart.
    assert kernel_room()["changed"] is False

    # (2) Kernel's after the project left its session's set (A10 rule 3).
    _revoke(rt, session_id, project_id)
    before = _store(rt)
    _refused(kernel_room(), "not_found", STAGE_AGENT_SESSION, ["agent_call_refused"])
    assert _store(rt) == before

    # (3) A room's repeat on a project deleted whole since: the owner's (the
    # deletion also drops it from every session, A11). State 5 add_room:
    # `not_found` (`unknown_project`), stage (3).
    doomed = _new_project(rt, display_name="Casa Derribo")
    owner_room_id = rt.new_request_id()
    made = rt.owner("add_room", target=doomed, room_name="Patio", request_id=owner_room_id)
    assert made["changed"] is True
    again = rt.owner("add_room", target=doomed, room_name="Patio", request_id=owner_room_id)
    assert again["changed"] is False  # control
    archived = _archive(rt, doomed)
    deleted = rt.owner("erase_project", target=doomed, stated_version=archived["revision"],
                       erasure="delete_whole")
    assert deleted["answer_kind"] == "project_erased", deleted
    before = _store(rt)
    _refused(
        rt.owner("add_room", target=doomed, room_name="Patio", request_id=owner_room_id),
        "not_found", STAGE_EXISTENCE, ["unknown_project"],
    )
    assert _store(rt) == before

    # The records the repeats named are as they were.
    assert _read_card(rt, project_card["project_id"]) == project_card
    assert [r["room_id"] for r in _owner_rooms(rt, project_id)] == [room["room"]["room_id"]]
    assert _owner_pointers(rt, project_id) == [pointer["pointer"]]
