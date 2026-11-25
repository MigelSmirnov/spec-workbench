"""Witness tests for accepted decision A06 (02_rules_records.md).

Every list has one declared order, and every key ends in an identity or a
sequence number, so equal keys never occur (A06-1): projects by last-changed
instant latest first, then ``project_id``; rooms by name, then ``room_id``;
artifacts by type, version highest first, pointer id; Customers not erased by
name, then ``customer_ref``, erased ones after them by ``customer_ref``;
agent sessions by registration instant, then identity; the audit log by
sequence number. Names, types and identities compare by Unicode code point of
the stored text (rule 7). A collection inside an answer follows the list that
answers it alone (rule 8). Each tagged test carries the witness name its
Required test declares.

The Factory project supplies the ``semantic_runtime`` fixture
(``RUNTIME_SURFACE.md``); each test gets a fresh instance at
2026-01-05T09:00:00Z, and the recorded clock moves only when a test moves it.
Surface used here:

- ``owner(...)`` — ``create_project``, ``correct_project``, ``list_projects``,
  ``read_project``, ``add_room``, ``record_customer``, ``erase_customer``,
  ``list_customers``, ``publish_pointer``, ``list_pointers``,
  ``grant_project``, ``read_session``, ``list_sessions``, ``read_audit``,
  ``show_import_mapping``;
- ``owner_upload(content)`` (``upload_import``) and ``export_file(...)``;
- ``service(...)`` — ``cabinet`` ``list_projects``; ``client_portal``
  ``list_rooms``, ``read_project``; ``presupro`` ``list_artifacts``;
  ``cabinet_kernel`` ``register_agent_session``, ``read_session_access``,
  ``read_agent_projection``;
- ``clock.advance``, ``new_request_id()``.

Python compares ``str`` by code point, which is rule 7's comparison, so the
expected orders below are ``sorted`` over the stored text. Expected values:
State 5 (``50_public_apis_3_records.md``, ``50_public_apis_2_sessions.md``,
``50_public_apis_4_import_backups.md``, Conventions "Order"), State 6 answer
models (``60_model_closure_values.json``).
"""

from datetime import datetime

KERNEL = "cabinet_kernel"


def _instant(text):
    # State 6 wire format: instants are ISO 8601 text in UTC ending in `Z`.
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def _accepted(answer, answer_kind):
    assert answer["answer_kind"] == answer_kind, answer
    return answer


def _create_project(rt, name, address="Calle Mayor 1"):
    answer = rt.owner(
        "create_project",
        request_id=rt.new_request_id(),
        project={"display_name": name, "address": address},
    )
    return _accepted(answer, "project_card")["card"]


def _owner_project_ids(rt):
    items = _accepted(rt.owner("list_projects"), "project_list")["items"]
    return [item["project_id"] for item in items]


def _cabinet_project_ids(rt):
    items = _accepted(rt.service("cabinet", "list_projects"), "project_list")["items"]
    return [item["project_id"] for item in items]


def _add_room(rt, project_id, name):
    answer = rt.owner(
        "add_room", target=project_id, request_id=rt.new_request_id(), room_name=name
    )
    return _accepted(answer, "room")["room"]


def _publish(rt, project_id, uri):
    answer = rt.owner(
        "publish_pointer",
        target=project_id,
        request_id=rt.new_request_id(),
        pointer={"artifact_type": "estimate", "uri": uri},
    )
    return _accepted(answer, "pointer")["pointer"]


def _record_customer(rt, name):
    answer = rt.owner(
        "record_customer",
        request_id=rt.new_request_id(),
        customer={"name": name, "customer_kind": "person"},
    )
    return _accepted(answer, "customer")["customer"]


def _register(rt, session_id):
    answer = rt.service(KERNEL, "register_agent_session", kernel_session=session_id)
    return _accepted(answer, "session_access")["access"]


def _is_erased(item):
    # State 6 ErasedCustomer: customer_ref and erased_at, nothing else; a
    # ListedCustomer has a name and no erased instant.
    return "erased_at" in item and "name" not in item


def test_same_instant_projects_list_by_id(semantic_runtime):
    """RT1: two projects changed at the same instant list by id."""
    rt = semantic_runtime
    # Five projects made at one instant (the clock is not moved): their
    # last-changed instants are equal, so `project_id` alone orders them.
    # Five, not two: an implementation that lists in insertion or store order
    # matches the id order for five random UUIDs once in 120 runs.
    same_instant = [_create_project(rt, f"A06 same instant {n}") for n in range(5)]
    assert len({card["last_changed_at"] for card in same_instant}) == 1
    by_id = sorted(card["project_id"] for card in same_instant)

    # A06 rule 1: last-changed latest first, then `project_id` ascending
    # (rule 7: identities by code point).
    assert _owner_project_ids(rt) == by_id
    assert _cabinet_project_ids(rt) == by_id

    # A project changed later lists first (latest first).
    rt.clock.advance(minutes=1)
    later = _create_project(rt, "A06 later")
    assert _owner_project_ids(rt) == [later["project_id"]] + by_id

    # The key is the last-changed instant, not creation: correcting one of the
    # five (A03; it moves last_changed_at, A04-3) brings it to the top, and the
    # rest keep their id order.
    rt.clock.advance(minutes=1)
    corrected_id = by_id[2]
    corrected = _accepted(
        rt.owner(
            "correct_project",
            target=corrected_id,
            stated_version=1,
            project={"display_name": "A06 corrected", "address": "Calle Mayor 1"},
        ),
        "project_card",
    )
    assert corrected["changed"] is True
    rest = [pid for pid in by_id if pid != corrected_id]
    expected = [corrected_id, later["project_id"]] + rest
    assert _owner_project_ids(rt) == expected
    assert _cabinet_project_ids(rt) == expected


def test_erased_customers_list_last(semantic_runtime):
    """RT2: an erased Customer lists after every Customer that is not erased."""
    rt = semantic_runtime
    # Names chosen so that code-point order differs from a case-folding or
    # accent-folding collation (rule 7): "Zoe" < "beatriz" < "Álvaro".
    names = ["Carla", "beatriz", "Ana", "Boris", "Álvaro", "Boris", "Zoe"]
    made = [_record_customer(rt, name) for name in names]

    def listed():
        return _accepted(rt.owner("list_customers"), "customer_list")["items"]

    # Control, before any erasure: by name, then customer_ref (rule 4).
    expected = sorted(made, key=lambda c: (c["name"], c["customer_ref"]))
    assert [(i["name"], i["customer_ref"]) for i in listed()] == [
        (c["name"], c["customer_ref"]) for c in expected
    ]

    # Erase "Ana" (first by name), "Zoe" and "Carla", in descending
    # customer_ref order and at moving instants, so an order by erasure
    # instant or by erasure order is told apart from rule 4's by ref.
    erased_refs = sorted(
        (c["customer_ref"] for c in made if c["name"] in ("Ana", "Zoe", "Carla")),
        reverse=True,
    )
    for ref in erased_refs:
        rt.clock.advance(minutes=1)
        _accepted(rt.owner("erase_customer", target=ref, stated_version=1), "customer")

    items = listed()
    kept = sorted(
        (c for c in made if c["customer_ref"] not in erased_refs),
        key=lambda c: (c["name"], c["customer_ref"]),
    )
    # A06 rule 4: not erased by name then ref; erased ones after them by ref.
    assert [i["customer_ref"] for i in items] == (
        [c["customer_ref"] for c in kept] + sorted(erased_refs)
    )
    assert [_is_erased(i) for i in items] == [False] * len(kept) + [True] * len(erased_refs)


def test_artifact_versions_list_highest_first(semantic_runtime):
    """RT3: artifacts of one type list version 3, 2, 1."""
    rt = semantic_runtime
    project_id = _create_project(rt, "A06 artifacts")["project_id"]
    published = [
        _publish(rt, project_id, f"https://presupro.example/estimates/{n}") for n in (1, 2, 3)
    ]
    assert [p["version"] for p in published] == [1, 2, 3]

    # A06 rule 3: by type, then version highest first, then pointer id —
    # for the owner and for a service alike (State 5 list_pointers).
    owner_list = _accepted(rt.owner("list_pointers", target=project_id), "pointers")["pointers"]
    service_list = _accepted(
        rt.service("presupro", "list_artifacts", {"project_id": project_id}), "pointers"
    )["pointers"]
    for pointers in (owner_list, service_list):
        assert [p["version"] for p in pointers] == [3, 2, 1]
        assert [p["pointer_id"] for p in pointers] == [
            published[2]["pointer_id"],
            published[1]["pointer_id"],
            published[0]["pointer_id"],
        ]
        assert [p["status"] for p in pointers] == ["published", "superseded", "superseded"]


def test_project_card_rooms_follow_list_rooms(semantic_runtime):
    """RT4: a project card lists its rooms in the order of 'list rooms'."""
    rt = semantic_runtime
    project_id = _create_project(rt, "A06 rooms")["project_id"]
    # Added out of order; four rooms share a name (R0-10), so the tie is
    # broken by room_id (an insertion-order tie-break matches it once in 24);
    # "Bath" < "Zona" < "bath" < "hall" < "kitchen" < "Ärea" by code point.
    names = ["kitchen", "hall", "Ärea", "hall", "bath", "Bath", "hall", "Zona", "hall"]
    rooms = [_add_room(rt, project_id, name) for name in names]
    expected = [
        room["room_id"] for room in sorted(rooms, key=lambda r: (r["name"], r["room_id"]))
    ]

    # A06 rule 2: 'list rooms' by name, then room_id.
    listed = _accepted(
        rt.service("client_portal", "list_rooms", {"project_id": project_id}), "rooms"
    )["rooms"]["rooms"]
    assert [room["room_id"] for room in listed] == expected

    # A06 rule 8: the card's rooms as 'list rooms' gives them, field for field
    # (State 5 read_project_card: "each as 'list rooms' gives it").
    owner_card = _accepted(rt.owner("read_project", target=project_id), "project_card")["card"]
    portal_card = _accepted(
        rt.service("client_portal", "read_project", {"project_id": project_id}), "project_card"
    )["card"]
    assert owner_card["rooms"] == listed
    assert portal_card["rooms"] == listed


def test_nested_collections_follow_declared_order(semantic_runtime):
    """RT5: sessions, the audit log, the projection's pointers, granted ids and
    the import mapping follow their declared orders."""
    rt = semantic_runtime

    # -- Agent sessions (A06 rule 5): registration instant, then identity.
    # One registered earlier, three at one later instant, named so that code
    # point order ("S-B" < "S-a" < "S-b") differs from case folding.
    _register(rt, "S-z")
    rt.clock.advance(minutes=1)
    for session in ("S-b", "S-B", "S-a"):
        _register(rt, session)
    sessions = _accepted(rt.owner("list_sessions"), "session_list")["items"]
    assert [s["access"]["session_id"] for s in sessions] == ["S-z", "S-B", "S-a", "S-b"]
    assert _instant(sessions[0]["registered_at"]) < _instant(sessions[1]["registered_at"])
    assert len({s["registered_at"] for s in sessions[1:]}) == 1

    # -- A session's granted ids by project_id (A06 rule 8), granted in the
    # reverse of that order.
    projects = [_create_project(rt, f"A06 granted {n}") for n in range(4)]
    ids = sorted(p["project_id"] for p in projects)
    version = 1
    for project_id in reversed(ids):
        answer = _accepted(
            rt.owner(
                "grant_project",
                target="S-a",
                stated_version=version,
                project_id=project_id,
                make_active=False,
            ),
            "session_access",
        )
        version = answer["access"]["access_version"]
    owner_access = _accepted(rt.owner("read_session", target="S-a"), "session_access")["access"]
    kernel_access = _accepted(
        rt.service(KERNEL, "read_session_access", kernel_session="S-a"), "session_access"
    )["access"]
    assert owner_access["granted_project_ids"] == ids
    assert kernel_access["granted_project_ids"] == ids
    sessions = _accepted(rt.owner("list_sessions"), "session_list")["items"]
    [listed_a] = [s for s in sessions if s["access"]["session_id"] == "S-a"]
    assert listed_a["access"]["granted_project_ids"] == ids

    # -- The agent projection's pointers follow 'list artifacts' (rule 8):
    # the projection carries the published ones only (State 1, A22 rule 4).
    target = ids[0]
    for n in (1, 2, 3):
        _accepted(
            rt.service(
                KERNEL,
                "publish_artifact_pointer",
                {
                    "project_id": target,
                    "request_id": rt.new_request_id(),
                    "pointer": {"artifact_type": "estimate", "uri": f"https://p.example/{n}"},
                },
                kernel_session="S-a",
            ),
            "pointer",
        )
    full = _accepted(
        rt.service(KERNEL, "list_artifacts", {"project_id": target}, kernel_session="S-a"),
        "pointers",
    )["pointers"]
    projection = _accepted(
        rt.service(KERNEL, "read_agent_projection", {"project_id": target}, kernel_session="S-a"),
        "agent_projection",
    )
    assert projection["pointers"] == [p for p in full if p["status"] == "published"]
    assert [p["version"] for p in projection["pointers"]] == [3]

    # -- The audit log by sequence number, ascending (A06 rule 6, M09): the
    # entries written above are the four creates, then the four grants.
    entries = _accepted(rt.owner("read_audit"), "audit_view")["entries"]
    numbers = [e["sequence_number"] for e in entries]
    assert numbers == sorted(numbers)
    assert len(set(numbers)) == len(numbers)
    assert [e["action"] for e in entries] == (
        ["project_created"] * 4 + ["session_project_granted"] * 4
    )
    # The grants' entries come in the order they were made (reverse id order).
    assert [e["subject"]["project_id"] for e in entries[4:]] == list(reversed(ids))

    # -- The import mapping (A06 rule 8): projects by project_id, each one's
    # rooms and pointers as their lists, the Customers it makes by v1 value.
    # The file holds them in other orders.
    p1 = "00000000-0000-4000-8000-000000000001"
    p2 = "00000000-0000-4000-8000-000000000002"
    p3 = "00000000-0000-4000-8000-000000000003"
    created = "2025-03-01T10:00:00+00:00"

    def v1_project(project_id, customer_ref):
        return {
            "project_id": project_id,
            "name": f"Obra {project_id[-1]}",
            "address": "Calle Real 5",
            "status": "active",
            "customer_ref": customer_ref,
            "created_at": created,
            "updated_at": created,
            "archived_at": None,
        }

    def v1_room(room_id, name):
        return {"room_id": room_id, "project_id": p1, "name": name, "created_at": created}

    def v1_pointer(pointer_id, version, status, superseded_at):
        return {
            "pointer_id": pointer_id,
            "project_id": p1,
            "artifact_type": "estimate",
            "owner_service": "presupro",
            # State 6 "The import file": versions as text of decimal digits.
            "version": str(version),
            "status": status,
            "uri": f"https://v1.example/{version}",
            "payload_ref": None,
            "content_digest": None,
            "created_at": created,
            "superseded_at": superseded_at,
        }

    later = "2025-03-02T10:00:00+00:00"
    content = rt.export_file(
        projects=[
            v1_project(p3, "mid-customer"),
            v1_project(p1, "zeta-customer"),
            v1_project(p2, "alpha-customer"),
        ],
        rooms=[
            v1_room("10000000-0000-4000-8000-000000000003", "kitchen"),
            v1_room("10000000-0000-4000-8000-000000000002", "hall"),
            v1_room("10000000-0000-4000-8000-000000000004", "Bath"),
            v1_room("10000000-0000-4000-8000-000000000001", "hall"),
        ],
        pointers=[
            v1_pointer("20000000-0000-4000-8000-000000000002", 2, "superseded", later),
            v1_pointer("20000000-0000-4000-8000-000000000003", 3, "published", None),
            v1_pointer("20000000-0000-4000-8000-000000000001", 1, "superseded", later),
        ],
    )
    _accepted(rt.owner_upload(content), "import_upload")
    picks = [
        {"project_id": p3, "display_name": "Obra 3", "alias": None},
        {"project_id": p1, "display_name": "Obra 1", "alias": None},
        {"project_id": p2, "display_name": "Obra 2", "alias": None},
    ]
    mapping = _accepted(
        rt.owner("show_import_mapping", import_choices={"picks": picks, "customers": []}),
        "import_mapping",
    )["mapping"]
    assert [p["project_id"] for p in mapping["projects"]] == [p1, p2, p3]
    mapped_p1 = mapping["projects"][0]
    # Rooms as 'list rooms': by name, then room_id ("Bath" < "hall" < "kitchen").
    assert [r["room_id"] for r in mapped_p1["rooms"]] == [
        "10000000-0000-4000-8000-000000000004",
        "10000000-0000-4000-8000-000000000001",
        "10000000-0000-4000-8000-000000000002",
        "10000000-0000-4000-8000-000000000003",
    ]
    # Pointers as 'list artifacts': type, version highest first, pointer id.
    assert [p["version"] for p in mapped_p1["pointers"]] == [3, 2, 1]
    # The Customers it makes by their v1 value.
    assert [c["v1_value"] for c in mapping["customers"]] == [
        "alpha-customer",
        "mid-customer",
        "zeta-customer",
    ]
