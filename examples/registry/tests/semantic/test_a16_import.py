"""Witness tests for accepted decision A16 (02_rules_installation.md).

The import shows its mapping, then applies it in one transaction: an upload
changes nothing and is kept only in its owner session; the mapping checks
what the picks bring in and nothing else; the confirmation step is shown only
for a clean mapping; an accepted import writes every picked project with its
rooms and pointers, the Customers it makes, the migration closure and one
audit entry in one transaction; a failed transaction leaves none of them;
once the closure exists every further upload and confirmation is refused.
Each witness test carries the name its Required test declares; the untagged
Required tests (1, 3, 6–11) are here too, named by what they show.

Expected values come from the design: A16's rules, State 5
(`50_public_apis_4_import_backups.md` — `read_import_mapping`,
`confirm_import`, `record_migration_closure`; `50_public_apis_0_conventions.md`
"Closed set of refusal codes"), State 6 (`60_contracts.md` "The import file";
the models `ImportUploadAnswer`, `ImportMappingAnswer`, `ImportAcceptedAnswer`,
`ConfirmationStepAnswer`, `ImportMapping`, `MalformedRecord`,
`ConflictingRecord`, `MissingMappingValue`, `MigrationClosure`, `AuditEntry`,
`ImportPublisher`, `ImportSubject` of `60_model_closure_*.json`), the table
names of `global_spec.json` `persistence`, and State 7 (`80_notes.md`,
`migration_import`) where it fixes an answer's exact shape.

The Factory project supplies the ``semantic_runtime`` pytest fixture
(`RUNTIME_SURFACE.md`); each test gets a fresh instance with an empty store.

Fixture surface used here:

- ``owner(action, target=None, confirm=True, **values)`` -> answer, with
  ``owner_confirm(step_answer)`` for a step shown with ``confirm=False``;
- ``owner_upload(content)`` -> answer of ``upload_import``;
- ``sign_in()``, ``sign_out()``, ``owner_session()``,
  ``use_owner_session(s)`` for the tests with two sessions or an ended one;
- ``new_request_id()``; ``clock.set(iso)`` (before the first owner request,
  so the session that holds the upload is not past its 30 idle minutes);
- capabilities: ``export_file(projects=…, rooms=…, pointers=…)``,
  ``store_rows(table)``, and ``faults.fail_store_call(method)`` with
  ``insert_migration_closure_row`` or ``insert_audit_entry_row``
  (`StoreRepository`, ``70_persistence_closure.json``): that call raises
  once, ``store.run_in_transaction`` rolls back and the operation answers
  ``internal_error`` (``transaction_failed``). Failing a write the import
  makes late shows that an import split over several transactions would
  leave the earlier ones committed.
"""

import hashlib
import json
from datetime import datetime

# State 5, "Closed set of refusal codes": the stages by A04 rule 6, named by
# the data closure's REFUSAL_STAGE_* constants (70_data_provider_closure.json).
STAGE_AUTHENTICATION = 1  # REFUSAL_STAGE_AUTHENTICATION
STAGE_EXISTENCE = 3  # REFUSAL_STAGE_EXISTENCE
STAGE_LIFECYCLE = 6  # REFUSAL_STAGE_LIFECYCLE

# global_spec.json "persistence": one table per durable model.
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
IMPORTED_TABLES = (
    "project_rows",
    "room_rows",
    "customer_rows",
    "pointer_rows",
    "audit_entry_rows",
    "migration_closure_rows",
)

# ARTIFACT_TYPE_OWNERS (data closure): the one declared type and its owner.
ESTIMATE = "estimate"
ESTIMATE_OWNER = "presupro"


# --- the import file (60_contracts.md "The import file"; State 6 Export*) ---
# Every member value is JSON text or null (80_notes.md `_parse_export`: any
# other JSON value makes the file unreadable), so a version is "1", not 1.


def _project(
    project_id,
    name,
    *,
    status="active",
    customer_ref=None,
    created_at="2024-03-01T10:00:00+00:00",
    updated_at="2024-03-05T10:00:00+00:00",
    archived_at=None,
    address=None,
):
    return {
        "project_id": project_id,
        "name": name,
        "address": address or f"{name}, Valencia",
        "status": status,
        "customer_ref": customer_ref,
        "created_at": created_at,
        "updated_at": updated_at,
        "archived_at": archived_at,
    }


def _room(room_id, project_id, name, created_at="2024-03-01T11:00:00+00:00"):
    return {
        "room_id": room_id,
        "project_id": project_id,
        "name": name,
        "created_at": created_at,
    }


def _pointer(
    pointer_id,
    project_id,
    *,
    version="1",
    status="published",
    created_at="2024-03-02T10:00:00+00:00",
    superseded_at=None,
    artifact_type=ESTIMATE,
    owner_service=ESTIMATE_OWNER,
):
    return {
        "pointer_id": pointer_id,
        "project_id": project_id,
        "artifact_type": artifact_type,
        "owner_service": owner_service,
        "version": version,
        "status": status,
        "uri": f"https://presupro.example/estimates/{pointer_id}",
        "payload_ref": None,
        "content_digest": None,
        "created_at": created_at,
        "superseded_at": superseded_at,
    }


def _file(rt, projects, rooms=(), pointers=()):
    return rt.export_file(
        projects=list(projects), rooms=list(rooms), pointers=list(pointers)
    )


def _digest(content):
    # 80_notes.md `_file_digest`: lowercase hex SHA-256 of the bytes.
    return hashlib.sha256(content).hexdigest()


# --- the owner's choices (State 6 ImportChoices / ImportPick / ImportCustomerValue)


def _pick(project_id, display_name=None, alias=None):
    return {"project_id": project_id, "display_name": display_name, "alias": alias}


def _customer(v1_value, name, kind, is_tax_id=False):
    return {
        "v1_value": v1_value,
        "name": name,
        "customer_kind": kind,
        "is_tax_id": is_tax_id,
    }


def _choices(picks, customers=()):
    return {"picks": list(picks), "customers": list(customers)}


# --- reading answers and the store ---


def _assert_kind(answer, kind):
    assert answer["answer_kind"] == kind, answer


def _assert_refused(answer, code, stage, kinds):
    """A refusal of the closed set (State 5), its kinds in answer order."""
    assert answer["answer_kind"] == "refused", answer
    assert answer["code"] == code, answer
    assert answer["stage"] == stage, answer
    assert [f["kind"] for f in answer["failures"]] == kinds, answer


def _assert_alone(answer, kind):
    """`import_closed` and `file_not_kept` are answered alone with an empty
    path (Conventions, "Stages"; 80_notes.md `read_import_mapping`,
    `confirm_import`): code `refused`, stage (6)."""
    _assert_refused(answer, "refused", STAGE_LIFECYCLE, [kind])
    assert answer["failures"][0]["path"] == [], answer


def _record(row):
    """A row's `record` column: the model as JSON (`json_model` storage)."""
    record = row["record"]
    return json.loads(record) if isinstance(record, (str, bytes)) else record


def _snapshot(rt):
    return {table: rt.store_rows(table) for table in TABLES}


def _assert_nothing_imported(rt):
    for table in IMPORTED_TABLES:
        assert rt.store_rows(table) == [], table


def _instant(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def _upload(rt, content):
    answer = rt.owner_upload(content)
    _assert_kind(answer, "import_upload")
    assert answer["file_digest"] == _digest(content)
    return answer


def _mapping(rt, choices):
    answer = rt.owner("show_import_mapping", import_choices=choices)
    _assert_kind(answer, "import_mapping")
    return answer["mapping"]


def _step(rt, choices):
    """Ask for the import's confirmation step without submitting it."""
    return rt.owner("confirm_import", confirm=False, import_choices=choices)


def _confirm(rt, choices):
    """Ask for the step and submit its value (A13 rule 6)."""
    return rt.owner("confirm_import", import_choices=choices)


def _production_project(rt, name="Obra de producción"):
    answer = rt.owner(
        "create_project",
        request_id=rt.new_request_id(),
        project={
            "display_name": name,
            "alias": None,
            "customer_ref": None,
            "address": "Calle Real 1, Valencia",
            "object_kind": None,
            "floor_area": None,
            "rooms_count": None,
            "floor": None,
        },
    )
    _assert_kind(answer, "project_card")
    return answer["card"]["project_id"]


def _production_pointer(rt, project_id):
    answer = rt.owner(
        "publish_pointer",
        target=project_id,
        request_id=rt.new_request_id(),
        pointer={
            "artifact_type": ESTIMATE,
            "uri": "https://presupro.example/estimates/production",
            "payload_ref": None,
            "content_digest": None,
        },
    )
    _assert_kind(answer, "pointer")
    return answer["pointer"]["pointer_id"]


def _not_imported(rt, project_id):
    # A project Registry does not hold answers `not_found` (`unknown_project`)
    # at stage (3) (State 5, "Closed set of refusal codes").
    _assert_refused(
        rt.owner("read_project", target=project_id),
        "not_found",
        STAGE_EXISTENCE,
        ["unknown_project"],
    )


# --- one file most tests import: two projects of one v1 customer, rooms,
# a superseded and a published pointer, and a project nobody picks.

V1_CUSTOMER = "B12345678"
V1_CUSTOMER_OTHER = "C-0042"


def _full_file(rt):
    projects = [
        _project("v1-p1", "Reforma cocina Mayor", customer_ref=V1_CUSTOMER),
        _project(
            "v1-p2",
            "Baño Ruzafa",
            status="archived",
            customer_ref=V1_CUSTOMER,
            created_at="2023-05-01T08:00:00+00:00",
            updated_at="2023-06-10T08:00:00+00:00",
            # rule 4: an archived project's last-changed instant may differ
            # from its archived instant (L05).
            archived_at="2023-06-01T08:00:00+00:00",
        ),
        _project("v1-p3", "Terraza Benimaclet", customer_ref=V1_CUSTOMER_OTHER),
    ]
    rooms = [
        _room("v1-r1", "v1-p1", "Cocina"),
        _room("v1-r2", "v1-p1", "Despensa"),
        _room("v1-r3", "v1-p2", "Baño", created_at="2023-05-02T08:00:00+00:00"),
        _room("v1-r4", "v1-p3", "Terraza"),
    ]
    pointers = [
        _pointer(
            "v1-e1",
            "v1-p1",
            version="1",
            status="superseded",
            superseded_at="2024-03-04T10:00:00+00:00",
        ),
        _pointer(
            "v1-e2", "v1-p1", version="2", created_at="2024-03-04T10:00:00+00:00"
        ),
        _pointer("v1-e3", "v1-p3"),
    ]
    return _file(rt, projects, rooms, pointers)


FULL_CHOICES = _choices(
    [_pick("v1-p1", alias="MAYOR"), _pick("v1-p2", display_name="Baño Ruzafa 2023")],
    [_customer(V1_CUSTOMER, "Talleres Norte SL", "company", is_tax_id=True)],
)


def _fail_and_show_nothing_remains(rt, choices, method):
    """A failure inside the import's transaction leaves no project, room,
    pointer, Customer, closure or entry (A16 rule 7, A16-1; State 5
    `record_migration_closure` "a failed transaction leaves none").

    The failure is placed at the `StoreRepository` call `method`
    (`70_persistence_closure.json`): the closure's insertion
    `insert_migration_closure_row` (written after the records) or the audit
    entry's `insert_audit_entry_row` (written last, State 4
    `flow:import_from_vps` step 5) — so every record written before it must
    be rolled back with it."""
    before = _snapshot(rt)
    rt.faults.fail_store_call(method)
    failed = _confirm(rt, choices)
    # State 5: `internal_error` carries no stage; its kind `transaction_failed`.
    _assert_refused(failed, "internal_error", None, ["transaction_failed"])
    assert _snapshot(rt) == before
    _assert_nothing_imported(rt)
    for pick in choices["picks"]:
        _not_imported(rt, pick["project_id"])
    customers = rt.owner("list_customers")
    _assert_kind(customers, "customer_list")
    assert customers["items"] == []


# --------------------------------------------------------------------------


def test_upload_answers_projects_and_changes_nothing(semantic_runtime):
    """Required test 1: uploading answers the file's projects and changes
    nothing; showing the mapping changes nothing either (rule 1, State 5
    `read_import_mapping` "Observable effect: None")."""
    rt = semantic_runtime
    content = _full_file(rt)
    before = _snapshot(rt)

    uploaded = _upload(rt, content)
    # State 5 Outputs at `upload`: each project with its id and status, as the
    # file gives them; 80_notes.md: ordered by project_id.
    assert uploaded["projects"] == [
        {"project_id": "v1-p1", "status": "active"},
        {"project_id": "v1-p2", "status": "archived"},
        {"project_id": "v1-p3", "status": "active"},
    ]
    assert _snapshot(rt) == before

    mapping = _mapping(rt, FULL_CHOICES)
    assert mapping["clean"] is True
    assert _snapshot(rt) == before
    _assert_nothing_imported(rt)
    listed = rt.owner("list_projects", list_choice="with_archived")
    _assert_kind(listed, "project_list")
    assert listed["items"] == []


def test_held_pointer_id_refuses_whole_import(semantic_runtime):
    """Required test 2 (A16-3): a file whose one pointer id production holds
    refuses the whole import — no project of the picks arrives."""
    rt = semantic_runtime
    production = _production_project(rt)
    held = _production_pointer(rt, production)

    content = _file(
        rt,
        [_project("v1-a", "Reforma Mayor"), _project("v1-b", "Baño Ruzafa")],
        [_room("v1-ra", "v1-a", "Cocina"), _room("v1-rb", "v1-b", "Baño")],
        # the second pointer of the file carries the id production holds
        [_pointer("v1-ea", "v1-a"), _pointer(held, "v1-b")],
    )
    _upload(rt, content)
    before = _snapshot(rt)
    both = _choices([_pick("v1-a"), _pick("v1-b")])

    # Rule 5 / State 5 Outputs: the conflict names the record's kind, its id
    # as the file gives it and its position among the file's pointers.
    mapping = _mapping(rt, both)
    assert mapping["conflicts"] == [
        {"record_kind": "pointer", "record_id": held, "position": 1}
    ]
    assert mapping["malformed"] == []
    assert mapping["clean"] is False

    # Rule 1: no confirmation step while the mapping shows a conflict; the
    # step request answers the mapping (80_notes.md OwnerActionStep.run).
    step = _step(rt, both)
    assert step["answer_kind"] != "confirmation_step", step
    assert "confirmation_value" not in step
    _assert_kind(step, "import_mapping")
    assert step["mapping"]["clean"] is False

    # Whole import refused, nothing changed: not even the clean pick arrived.
    assert _snapshot(rt) == before
    _not_imported(rt, "v1-a")
    _not_imported(rt, "v1-b")
    assert rt.store_rows("migration_closure_rows") == []
    pointers = rt.owner("list_pointers", target=production)
    _assert_kind(pointers, "pointers")
    assert [p["pointer_id"] for p in pointers["pointers"]] == [held]
    assert pointers["pointers"][0]["project_id"] == production

    # Control: the same file without the conflicting pick is accepted.
    accepted = _confirm(rt, _choices([_pick("v1-a")]))
    _assert_kind(accepted, "import_accepted")
    assert [p["project_id"] for p in accepted["projects"]] == ["v1-a"]
    _not_imported(rt, "v1-b")
    pointers = rt.owner("list_pointers", target=production)
    assert [p["pointer_id"] for p in pointers["pointers"]] == [held]


def test_confirmation_after_new_upload_refused_file_not_kept(semantic_runtime):
    """Required test 3: a step shown before another upload of the session is
    refused at confirmation, `file_not_kept` — also when the new file has the
    same bytes (rule 2; State 5 `confirm_import`: "that session's upload of
    that number, not merely bytes of that digest")."""
    rt = semantic_runtime
    choices = _choices([_pick("v1-a")])
    first = _file(rt, [_project("v1-a", "Reforma Mayor")])
    other = _file(
        rt, [_project("v1-a", "Reforma Mayor")], [_room("v1-ra", "v1-a", "Cocina")]
    )
    assert first != other

    first_upload = _upload(rt, first)
    stale_step = _step(rt, choices)
    _assert_kind(stale_step, "confirmation_step")
    _upload(rt, other)
    before = _snapshot(rt)
    _assert_alone(rt.owner_confirm(stale_step), "file_not_kept")
    assert _snapshot(rt) == before

    # Same bytes again: a new upload number, so the step bound to the earlier
    # number is refused although the digest is equal.
    step_on_other = _step(rt, choices)
    _assert_kind(step_on_other, "confirmation_step")
    again = _upload(rt, other)
    assert again["file_digest"] == _digest(other)
    assert again["upload_number"] != first_upload["upload_number"]
    _assert_alone(rt.owner_confirm(step_on_other), "file_not_kept")
    assert _snapshot(rt) == before
    _assert_nothing_imported(rt)

    # Control: a step shown on the file now kept is accepted, and it applies
    # that file (its room), not the first.
    accepted = _confirm(rt, choices)
    _assert_kind(accepted, "import_accepted")
    assert accepted["file_digest"] == _digest(other)
    card = rt.owner("read_project", target="v1-a")["card"]
    assert [r["room_id"] for r in card["rooms"]] == ["v1-ra"]


def test_second_import_after_success_refused(semantic_runtime):
    """Required test 4 (A16-2): once the closure exists, uploading, mapping
    and confirming — a step of another session shown before the import was
    accepted included — are refused `import_closed`, answered alone and
    before every other check, and change nothing (rules 2, 7, 8)."""
    rt = semantic_runtime
    content = _file(rt, [_project("v1-a", "Reforma Mayor")])
    choices = _choices([_pick("v1-a")])

    _upload(rt, content)
    first_session = rt.owner_session()
    rt.sign_in()
    second_session = rt.owner_session()
    assert second_session != first_session
    _upload(rt, content)
    other_step = _step(rt, choices)
    _assert_kind(other_step, "confirmation_step")

    # Control: the first import is accepted.
    rt.use_owner_session(first_session)
    accepted = _confirm(rt, choices)
    _assert_kind(accepted, "import_accepted")
    assert len(rt.store_rows("migration_closure_rows")) == 1
    after_import = _snapshot(rt)

    second_file = _file(rt, [_project("v1-z", "Otra obra")])
    _assert_alone(rt.owner_upload(second_file), "import_closed")
    _assert_alone(
        rt.owner("show_import_mapping", import_choices=choices), "import_closed"
    )
    _assert_alone(_step(rt, choices), "import_closed")

    # The other session's step: its value is valid (stage (1) passes) and its
    # upload was dropped by the accepted import — the closure is answered
    # alone, before `file_not_kept`.
    rt.use_owner_session(second_session)
    _assert_alone(rt.owner_confirm(other_step), "import_closed")
    _assert_alone(rt.owner_upload(second_file), "import_closed")

    assert _snapshot(rt) == after_import
    assert len(rt.store_rows("migration_closure_rows")) == 1
    _not_imported(rt, "v1-z")


def test_failed_transaction_leaves_no_import(semantic_runtime):
    """Required test 5 (A16-1): a failure during the import's transaction
    leaves no project, no Customer and no closure; the import may then be
    retried, nothing of the refused attempt remaining (rule 9)."""
    rt = semantic_runtime
    _upload(rt, _full_file(rt))
    _fail_and_show_nothing_remains(rt, FULL_CHOICES, "insert_migration_closure_row")
    assert rt.store_rows("migration_closure_rows") == []

    # Control and rule 9: the upload is still kept (it is dropped only after a
    # commit, rule 2) and a retry is accepted — no leftover id conflicts.
    retried = _confirm(rt, FULL_CHOICES)
    _assert_kind(retried, "import_accepted")
    assert [p["project_id"] for p in retried["projects"]] == ["v1-p1", "v1-p2"]
    assert len(rt.store_rows("migration_closure_rows")) == 1


def test_conflict_of_unpicked_project_does_not_refuse(semantic_runtime):
    """Required test 6: an id production holds that belongs only to a project
    the owner did not pick is neither shown nor refuses (rule 3)."""
    rt = semantic_runtime
    production = _production_project(rt)
    content = _file(
        rt,
        [_project("v1-a", "Reforma Mayor"), _project(production, "Obra repetida")],
        [_room("v1-ra", "v1-a", "Cocina"), _room("v1-rx", production, "Salón")],
    )
    _upload(rt, content)

    # Contrast: picked, the same record is a conflict (rule 5).
    with_it = _mapping(rt, _choices([_pick("v1-a"), _pick(production)]))
    assert with_it["conflicts"] == [
        {"record_kind": "project", "record_id": production, "position": 1}
    ]
    assert with_it["clean"] is False

    only_a = _choices([_pick("v1-a")])
    mapping = _mapping(rt, only_a)
    assert mapping["conflicts"] == []
    assert mapping["malformed"] == []
    assert mapping["clean"] is True
    accepted = _confirm(rt, only_a)
    _assert_kind(accepted, "import_accepted")
    assert [p["project_id"] for p in accepted["projects"]] == ["v1-a"]
    # The production project is untouched: still its own name, no new room.
    card = rt.owner("read_project", target=production)["card"]
    assert card["display_name"] == "Obra de producción"
    assert card["rooms"] == []


def test_room_of_absent_project_neither_imported_nor_refusing(semantic_runtime):
    """Required test 7: a room naming a project the file does not hold belongs
    to no pick — not imported, not shown, not refusing (rule 3; 80_notes.md
    `_build_mapping`)."""
    rt = semantic_runtime
    content = _file(
        rt,
        [_project("v1-a", "Reforma Mayor")],
        [_room("v1-ra", "v1-a", "Cocina"), _room("v1-orphan", "v1-ghost", "Sótano")],
    )
    _upload(rt, content)
    choices = _choices([_pick("v1-a")])
    mapping = _mapping(rt, choices)
    assert mapping["malformed"] == []
    assert mapping["clean"] is True
    assert [r["room_id"] for r in mapping["projects"][0]["rooms"]] == ["v1-ra"]

    accepted = _confirm(rt, choices)
    _assert_kind(accepted, "import_accepted")
    assert [r["room_id"] for r in rt.store_rows("room_rows")] == ["v1-ra"]
    card = rt.owner("read_project", target="v1-a")["card"]
    assert [r["room_id"] for r in card["rooms"]] == ["v1-ra"]
    _not_imported(rt, "v1-ghost")


def test_customer_without_kind_refuses_confirmation(semantic_runtime):
    """Required test 8: confirming without a kind for a Customer the import
    makes is refused — the mapping shows the missing value and no step is
    shown (rule 1, A02; State 5 `read_import_mapping`: "named by its subject
    … and by its field")."""
    rt = semantic_runtime
    content = _file(rt, [_project("v1-a", "Reforma Mayor", customer_ref=V1_CUSTOMER)])
    _upload(rt, content)
    before = _snapshot(rt)

    no_kind = _choices(
        [_pick("v1-a")], [_customer(V1_CUSTOMER, "Talleres Norte SL", None, True)]
    )
    mapping = _mapping(rt, no_kind)
    assert mapping["missing"] == [
        {"subject_kind": "customer", "subject": V1_CUSTOMER, "field": "customer_kind"}
    ]
    assert mapping["clean"] is False
    step = _step(rt, no_kind)
    _assert_kind(step, "import_mapping")
    assert step["mapping"]["clean"] is False
    assert _snapshot(rt) == before
    _assert_nothing_imported(rt)

    # Control: with the kind given, the import is accepted and the Customer
    # carries it, the v1 value as its tax id (R0-80).
    with_kind = _choices(
        [_pick("v1-a")],
        [_customer(V1_CUSTOMER, "Talleres Norte SL", "company", True)],
    )
    accepted = _confirm(rt, with_kind)
    _assert_kind(accepted, "import_accepted")
    (made,) = accepted["customers"]
    customer = rt.owner("read_customer", target=made["customer_ref"])["customer"]
    assert customer["customer_kind"] == "company"
    assert customer["tax_id"] == V1_CUSTOMER


def test_withdrawn_pointer_of_pick_is_malformed(semantic_runtime):
    """Required test 9: a picked project holding a `withdrawn` pointer refuses
    the import as malformed (rule 4: "a pointer is `withdrawn` (v1 never
    withdrew one, M05)")."""
    rt = semantic_runtime
    choices = _choices([_pick("v1-a")])
    bad = _file(
        rt,
        [_project("v1-a", "Reforma Mayor")],
        pointers=[_pointer("v1-ea", "v1-a", status="withdrawn")],
    )
    _upload(rt, bad)
    before = _snapshot(rt)
    mapping = _mapping(rt, choices)
    (record,) = mapping["malformed"]
    assert (record["record_kind"], record["record_id"], record["position"]) == (
        "pointer",
        "v1-ea",
        0,
    )
    assert "withdrawn_pointer" in record["defects"]
    assert mapping["clean"] is False
    _assert_kind(_step(rt, choices), "import_mapping")
    assert _snapshot(rt) == before
    _assert_nothing_imported(rt)

    # Control: the same pointer `published` is well formed and imported.
    good = _file(
        rt,
        [_project("v1-a", "Reforma Mayor")],
        pointers=[_pointer("v1-ea", "v1-a", status="published")],
    )
    _upload(rt, good)
    assert _mapping(rt, choices)["malformed"] == []
    _assert_kind(_confirm(rt, choices), "import_accepted")
    assert [r["pointer_id"] for r in rt.store_rows("pointer_rows")] == ["v1-ea"]


def test_confirmation_after_session_ended_refused(semantic_runtime):
    """Required test 10: confirming after the owner session that uploaded the
    file has ended is refused, and its upload went with the session (rule 2,
    M11; State 5: `no_owner_session` at stage (1))."""
    rt = semantic_runtime
    content = _file(rt, [_project("v1-a", "Reforma Mayor")])
    choices = _choices([_pick("v1-a")])
    _upload(rt, content)
    step = _step(rt, choices)
    _assert_kind(step, "confirmation_step")
    ended = rt.owner_session()
    _assert_kind(rt.sign_out(), "signed_out")
    before = _snapshot(rt)

    rt.use_owner_session(ended)
    _assert_refused(
        rt.owner_confirm(step),
        "unauthenticated",
        STAGE_AUTHENTICATION,
        ["no_owner_session"],
    )
    rt.sign_in()
    # The new session keeps no file: its mapping is `file_not_kept`.
    _assert_alone(
        rt.owner("show_import_mapping", import_choices=choices), "file_not_kept"
    )
    assert _snapshot(rt) == before
    _assert_nothing_imported(rt)

    # Control: uploaded again in the open session, the import is accepted.
    _upload(rt, content)
    _assert_kind(_confirm(rt, choices), "import_accepted")


def test_step_for_conflicting_mapping_refused_makes_no_value(semantic_runtime):
    """Required test 11: asking for the import's confirmation step while the
    mapping shows a conflicting id is refused, and no confirmation value is
    made (rule 1; A13 rule 6: a shown step replaces the session's pending
    value, so a value made here would replace the earlier one)."""
    rt = semantic_runtime
    production = _production_project(rt)
    content = _file(
        rt, [_project("v1-a", "Reforma Mayor"), _project(production, "Repetida")]
    )
    _upload(rt, content)

    clean = _choices([_pick("v1-a")])
    clean_step = _step(rt, clean)
    _assert_kind(clean_step, "confirmation_step")

    conflicting = _choices([_pick("v1-a"), _pick(production)])
    refused_step = _step(rt, conflicting)
    assert refused_step["answer_kind"] != "confirmation_step", refused_step
    assert "confirmation_value" not in refused_step
    _assert_kind(refused_step, "import_mapping")
    assert refused_step["mapping"]["conflicts"] == [
        {"record_kind": "project", "record_id": production, "position": 1}
    ]

    # No value was made: the earlier pending value is still the session's and
    # is accepted (a replaced one would be `confirmation_other_value`).
    accepted = rt.owner_confirm(clean_step)
    _assert_kind(accepted, "import_accepted")
    assert [p["project_id"] for p in accepted["projects"]] == ["v1-a"]


def test_accepted_import_stores_all_in_one_transaction(semantic_runtime):
    """Required test 12 (A16-1): an accepted import stores every picked
    project with its rooms and pointers, the Customers it made, one closure
    holding the file's digest and exactly one audit entry; a failure inside
    its transaction leaves none of them."""
    rt = semantic_runtime
    # The clock is set before the first owner request: the upload belongs to
    # the owner session (M11), so the confirmation must come in that session,
    # not past its 30 idle minutes (A13 rule 2).
    accepted_at = "2026-02-10T12:00:00Z"
    rt.clock.set(accepted_at)
    content = _full_file(rt)
    digest = _digest(content)
    _upload(rt, content)

    # The failing half first: nothing of the attempt remains.
    _fail_and_show_nothing_remains(rt, FULL_CHOICES, "insert_audit_entry_row")

    accepted = _confirm(rt, FULL_CHOICES)
    _assert_kind(accepted, "import_accepted")
    assert accepted["file_digest"] == digest

    # State 6 ImportedProjectResult: the name and alias each arrived under —
    # the v1 name unless the owner gave another (rule 1, R0-85).
    assert accepted["projects"] == [
        {
            "project_id": "v1-p1",
            "display_name": "Reforma cocina Mayor",
            "alias": "MAYOR",
            "status": "active",
        },
        {
            "project_id": "v1-p2",
            "display_name": "Baño Ruzafa 2023",
            "alias": None,
            "status": "archived",
        },
    ]
    # One Customer for the one distinct v1 value the picks name (rule 1).
    (made,) = accepted["customers"]
    assert made["v1_value"] == V1_CUSTOMER
    customer_ref = made["customer_ref"]
    assert customer_ref and customer_ref != V1_CUSTOMER

    # Projects with their own ids, instants and rooms (State 5
    # `write_imported_project`: revision 1, source instants; 80_notes.md
    # `confirm_import`: updated_at as last_changed_at, a room's created_at as
    # added_at), linked to the Customer made (R0-80).
    p1 = rt.owner("read_project", target="v1-p1")["card"]
    assert p1["status"] == "active" and p1["revision"] == 1
    assert p1["customer_ref"] == customer_ref
    assert _instant(p1["created_at"]) == _instant("2024-03-01T10:00:00+00:00")
    assert _instant(p1["last_changed_at"]) == _instant("2024-03-05T10:00:00+00:00")
    assert p1["object_facts"]["address"] == "Reforma cocina Mayor, Valencia"
    assert [(r["room_id"], r["name"]) for r in p1["rooms"]] == [
        ("v1-r1", "Cocina"),
        ("v1-r2", "Despensa"),
    ]
    assert _instant(p1["rooms"][0]["added_at"]) == _instant(
        "2024-03-01T11:00:00+00:00"
    )
    p2 = rt.owner("read_project", target="v1-p2")["card"]
    assert p2["status"] == "archived" and p2["customer_ref"] == customer_ref
    assert p2["archived_on"] == "2023-06-01"
    assert [r["room_id"] for r in p2["rooms"]] == ["v1-r3"]

    # Pointers under their ids and instants, the import their publisher
    # (State 6 ImportPublisher; M05). Order of 'list artifacts' (A06): by
    # version, highest first.
    pointers = rt.owner("list_pointers", target="v1-p1")["pointers"]
    assert [(p["pointer_id"], p["version"], p["status"]) for p in pointers] == [
        ("v1-e2", 2, "published"),
        ("v1-e1", 1, "superseded"),
    ]
    for p in pointers:
        assert p["publisher"] == {"publisher_kind": "import", "file_digest": digest}
        assert p["owner_service"] == ESTIMATE_OWNER
    assert _instant(pointers[1]["superseded_at"]) == _instant(
        "2024-03-04T10:00:00+00:00"
    )

    # The Customer made at the action's instant, revision 1, the v1 value its
    # tax id as the owner said (State 5 `make_imported_customer`).
    customer = rt.owner("read_customer", target=customer_ref)["customer"]
    assert customer["name"] == "Talleres Norte SL"
    assert customer["customer_kind"] == "company"
    assert customer["tax_id"] == V1_CUSTOMER
    assert customer["revision"] == 1
    assert _instant(customer["created_at"]) == _instant(accepted_at)

    # Nothing of the unpicked project or its v1 customer (rule 3).
    _not_imported(rt, "v1-p3")
    assert sorted(r["project_id"] for r in rt.store_rows("project_rows")) == [
        "v1-p1",
        "v1-p2",
    ]
    assert sorted(r["room_id"] for r in rt.store_rows("room_rows")) == [
        "v1-r1",
        "v1-r2",
        "v1-r3",
    ]
    assert sorted(r["pointer_id"] for r in rt.store_rows("pointer_rows")) == [
        "v1-e1",
        "v1-e2",
    ]
    assert [r["customer_ref"] for r in rt.store_rows("customer_rows")] == [
        customer_ref
    ]

    # One closure holding the file's digest (M10; State 5
    # `record_migration_closure`: principal the owner).
    (closure_row,) = rt.store_rows("migration_closure_rows")
    closure = _record(closure_row)
    assert closure["file_digest"] == digest
    assert _instant(closure["accepted_at"]) == _instant(accepted_at)
    assert closure["principal"]["principal_kind"] == "owner"
    assert closure["confirmation_id"]

    # Exactly one audit entry, naming the closure by the file's digest and
    # carrying its confirmation id (M09; A14 rule 5; State 6 ImportSubject).
    (entry_row,) = rt.store_rows("audit_entry_rows")
    entry = _record(entry_row)
    assert entry["action"] == "import_accepted"
    assert entry["subject"] == {"subject_kind": "import", "file_digest": digest}
    assert entry["confirmation_id"] == closure["confirmation_id"]
    assert entry["principal"]["principal_kind"] == "owner"
    assert _instant(entry["recorded_at"]) == _instant(accepted_at)
