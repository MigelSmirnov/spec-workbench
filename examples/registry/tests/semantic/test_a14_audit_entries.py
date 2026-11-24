"""Witness tests for accepted decision A14 (02_rules_audit.md).

Only an accepted change writes an audit entry: an accepted action that M09
lists and that changes state writes exactly one, in the transaction of the
change, so neither is stored without the other; a refused action, an action
that changes nothing (but the erasure of old entries, A15 rule 6) and every
read write none, whoever reads; a confirmation id is minted only for an
accepted, confirmed action that changes state and is written into its entry;
every entry's outcome is `accepted`. Each tagged test carries the witness
name its Required test declares.

The Factory project `registry` supplies the ``semantic_runtime`` fixture
(``tests/semantic/RUNTIME_SURFACE.md``): a fresh instance per test, driven
over its two real listeners. Expected values come from State 1 (M09), State 2
(A14, A15 rule 6, A12, A13 rule 7), State 5 (`50_public_apis_5_surfaces.md`:
`operations.perform_owner_operation`, `operations.perform_service_operation`;
`50_public_apis_1_foundation.md`: `audit_log.append_audit_entry`,
`audit_log.read_audit_entries`; `50_public_apis_3_records.md`,
`50_public_apis_2_sessions.md`, `50_public_apis_4_import_backups.md`: the
operations each action reaches; "Conventions" and "Closed set of refusal
codes" in `50_public_apis_0_conventions.md`), State 6 (`AuditEntry`,
`AuditSubject` and its variants, `ActingPrincipal`, `AuditViewAnswer`,
`OwnerValues`, `RefusedAnswer`; the tables of `70_persistence_closure.json`)
and the constants of `70_data_provider_closure.json` (`OWNER_AUDIT_ACTIONS`,
`RELEASE_VERSION`, `CONTRACT_VERSION`).

Fixture surface used here:

- ``owner(action, target=None, stated_version=None, confirm=True,
  **values)`` -> answer, for `read_audit`, `create_project`,
  `correct_project`, `archive_project`, `erase_project`, `read_project`,
  `list_projects`, `record_customer`, `correct_customer`, `mark_customer`,
  `erase_customer`, `read_customer`, `grant_project`, `revoke_project`,
  `answer_access_request`, `list_sessions`, `confirm_import`,
  `erase_audit_entries` (the confirmed ones confirmed by the fixture, A13
  rule 6); ``owner_upload(content)`` with ``export_file(projects=…,
  rooms=…, pointers=…)``; ``sign_in(credential=…)``;
- ``service(name, operation, inputs, kernel_session=…)`` -> answer;
- ``new_request_id()``;
- ``store_rows(table)`` for `audit_entry_rows`, `audit_sequence_rows`,
  `project_rows`, `customer_rows` (rows compared whole);
- ``faults.fail_store_call(method)``: the next call of that
  `StoreRepository` method (``70_persistence_closure.json``) raises,
  failing the transaction that makes it — `insert_audit_entry_row`, the
  last call of an audited action (State 7 `append_audit_entry`: the raised
  counter, then the entry, after the record's own write), and the record's
  own write, `update_project_row` or `update_customer_row`, the first.
"""

# 70_data_provider_closure.json
STAGE_AUTHENTICATION = 1  # REFUSAL_STAGE_AUTHENTICATION
STAGE_EXISTENCE = 3  # REFUSAL_STAGE_EXISTENCE
STAGE_VERSION = 5  # REFUSAL_STAGE_VERSION
RELEASE_VERSION = "registry-2.0.0"
CONTRACT_VERSION = "registry-contract-2"
ACCESS_VERSION_FIRST = 1

KERNEL = "cabinet_kernel"  # ServiceName
PORTAL = "client_portal"
CABINET = "cabinet"

# ActingPrincipal of the owner: no service, and no session — the owner
# session's identity never appears in an entry (A13 rule 7).
OWNER_PRINCIPAL = {"principal_kind": "owner", "service": None, "session_id": None}

# ConfirmedAction (State 6) and OWNER_AUDIT_ACTIONS: these actions' entries
# carry the confirmation id (A14 rule 5); the others carry none.
CONFIRMED_AUDIT_ACTIONS = {
    "project_archived",
    "project_anonymised",
    "project_deleted",
    "import_accepted",
    "audit_entries_erased",
}

ADDRESS = "Calle Mayor 1, Valencia"
MISSING_PROJECT = "00000000-0000-4000-8000-000000000000"
WRONG_CREDENTIAL = "wrong-owner-credential-" + "x" * 32


def _refusal(answer):
    """(code, stage, kinds) of a refused answer (State 5 closed set)."""
    assert answer["answer_kind"] == "refused", answer
    return (
        answer["code"],
        answer["stage"],
        [f["kind"] for f in answer["failures"]],
    )


def _log(rt):
    answer = rt.owner("read_audit")
    assert answer["answer_kind"] == "audit_view", answer
    return answer["entries"]


def _store_log(rt):
    """The log and its sequence as the store holds them."""
    return (rt.store_rows("audit_entry_rows"), rt.store_rows("audit_sequence_rows"))


def _project_facts(display_name, address=ADDRESS):
    return {
        "display_name": display_name,
        "alias": None,
        "customer_ref": None,
        "address": address,
        "object_kind": None,
        "floor_area": None,
        "rooms_count": None,
        "floor": None,
    }


def _customer_facts(name="Ana Lopez", phone="+34 600 000 001"):
    return {
        "name": name,
        "customer_kind": "person",
        "phone": phone,
        "email": None,
        "language": "es",
        "tax_id": None,
        "legal_name": None,
    }


def _ok(answer, kind):
    assert answer["answer_kind"] == kind, answer
    return answer


def _create_project(rt, display_name="Casa Lopez"):
    answer = rt.owner(
        "create_project",
        request_id=rt.new_request_id(),
        project=_project_facts(display_name),
    )
    return _ok(answer, "project_card")["card"]


def _project(rt, project_id):
    return _ok(rt.owner("read_project", target=project_id), "project_card")["card"]


def _project_subject(project_id):
    return {"subject_kind": "project", "project_id": project_id}


def _customer_subject(customer_ref):
    return {"subject_kind": "customer", "customer_ref": customer_ref}


def _session_project_subject(session_id, project_id):
    return {
        "subject_kind": "session_project",
        "session_id": session_id,
        "project_id": project_id,
    }


def _assert_entry(entry, action, subject):
    """One entry as M09 and State 6 AuditEntry declare it."""
    assert entry["action"] == action
    assert entry["subject"] == subject
    assert entry["outcome"] == "accepted"  # A14 rule 6
    assert entry["principal"] == OWNER_PRINCIPAL
    assert entry["release_version"] == RELEASE_VERSION
    assert entry["contract_version"] == CONTRACT_VERSION
    if action in CONFIRMED_AUDIT_ACTIONS:
        assert isinstance(entry["confirmation_id"], str)
        assert entry["confirmation_id"]
    else:
        assert entry["confirmation_id"] is None
    if action != "audit_entries_erased":
        assert entry["erased_before"] is None


def _one_new_entry(rt, before, action, subject):
    """The log after an accepted change: the old entries untouched and
    exactly one new entry, the change's (A14 rule 1)."""
    after = _log(rt)
    assert after[: len(before)] == before
    assert len(after) == len(before) + 1, after[len(before):]
    entry = after[-1]
    _assert_entry(entry, action, subject)
    return after


def _register(rt, session_id):
    answer = rt.service(KERNEL, "register_agent_session", kernel_session=session_id)
    return _ok(answer, "session_access")["access"]


V1_PROJECT_ID = "6f1c2a4e-8b3d-4c5e-9f70-1a2b3c4d5e6f"


def _v1_file(rt):
    # The import file of R0-72 (State 6 "The import file"): one active v1
    # project, no customer, no room, no pointer.
    return rt.export_file(
        projects=[
            {
                "project_id": V1_PROJECT_ID,
                "name": "Reforma Calle Real",
                "address": "Calle Real 2, Valencia",
                "status": "active",
                "customer_ref": None,
                "created_at": "2025-03-01T10:00:00+00:00",
                "updated_at": "2025-03-02T10:00:00+00:00",
                "archived_at": None,
            }
        ],
        rooms=[],
        pointers=[],
    )


def _every_audited_action(rt):
    """Run every action M09 lists once, accepted and changing state; after
    each, exactly one new entry of the action OWNER_AUDIT_ACTIONS names, with
    the subject M09 fixes for it. Returns the list of audit actions run."""
    run = []
    log = _log(rt)

    def check(action, subject):
        nonlocal log
        log = _one_new_entry(rt, log, action, subject)
        run.append(action)

    # Customers: record, correct, restrict, lift, end, resume.
    customer = _ok(
        rt.owner(
            "record_customer",
            request_id=rt.new_request_id(),
            customer=_customer_facts(),
        ),
        "customer",
    )["customer"]
    ref = customer["customer_ref"]
    check("customer_recorded", _customer_subject(ref))
    customer = _ok(
        rt.owner(
            "correct_customer",
            target=ref,
            stated_version=customer["revision"],
            customer=_customer_facts(phone="+34 600 000 002"),
        ),
        "customer",
    )["customer"]
    check("customer_corrected", _customer_subject(ref))
    for transition, action in (
        ("restrict", "customer_restricted"),
        ("lift", "customer_restriction_lifted"),
        ("end", "customer_relationship_ended"),
        ("resume", "customer_relationship_resumed"),
    ):
        answer = rt.owner(
            "mark_customer",
            target=ref,
            stated_version=customer["revision"],
            transition=transition,
        )
        customer = _ok(answer, "customer")["customer"]
        assert answer["changed"] is True
        check(action, _customer_subject(ref))

    # A project: create, correct.
    project = _create_project(rt, "Casa Lopez")
    pid = project["project_id"]
    check("project_created", _project_subject(pid))
    project = _ok(
        rt.owner(
            "correct_project",
            target=pid,
            stated_version=project["revision"],
            project=_project_facts("Casa Lopez, reforma"),
        ),
        "project_card",
    )["card"]
    check("project_corrected", _project_subject(pid))

    # A session: a grant, a revocation, a grant answering a request.
    sid = "a14-kernel-session-1"
    access = _register(rt, sid)
    assert _log(rt) == log  # registering writes none (A11 rule 6)
    access = _ok(
        rt.owner(
            "grant_project",
            target=sid,
            stated_version=access["access_version"],
            project_id=pid,
            make_active=False,
        ),
        "session_access",
    )["access"]
    check("session_project_granted", _session_project_subject(sid, pid))
    access = _ok(
        rt.owner(
            "revoke_project",
            target=sid,
            stated_version=access["access_version"],
            project_id=pid,
        ),
        "session_access",
    )["access"]
    check("session_project_revoked", _session_project_subject(sid, pid))
    _ok(
        rt.service(
            KERNEL,
            "request_project_access",
            {"request_text": "La obra de la calle Mayor"},
            kernel_session=sid,
        ),
        "request_pending",
    )
    assert _log(rt) == log  # an access request writes none (M09)
    access = _ok(rt.owner("read_session", target=sid), "session_access")["access"]
    _ok(
        rt.owner(
            "answer_access_request",
            target=sid,
            stated_version=access["access_version"],
            access_answer={"answer_kind": "grant", "project_id": pid, "make_active": False},
        ),
        "session_access",
    )
    check("session_project_granted", _session_project_subject(sid, pid))

    # Archive, then anonymise (both confirmed).
    project = _ok(
        rt.owner("archive_project", target=pid, stated_version=project["revision"]),
        "project_card",
    )["card"]
    check("project_archived", _project_subject(pid))
    _ok(
        rt.owner(
            "erase_project",
            target=pid,
            stated_version=project["revision"],
            erasure="anonymise",
        ),
        "project_erased",
    )
    check("project_anonymised", _project_subject(pid))

    # A second project deleted whole.
    other = _create_project(rt, "Piso Ruzafa")
    oid = other["project_id"]
    check("project_created", _project_subject(oid))
    other = _ok(
        rt.owner("archive_project", target=oid, stated_version=other["revision"]),
        "project_card",
    )["card"]
    check("project_archived", _project_subject(oid))
    _ok(
        rt.owner(
            "erase_project",
            target=oid,
            stated_version=other["revision"],
            erasure="delete_whole",
        ),
        "project_erased",
    )
    check("project_deleted", _project_subject(oid))

    # The Customer's erasure.
    _ok(
        rt.owner("erase_customer", target=ref, stated_version=customer["revision"]),
        "customer",
    )
    check("customer_erased", _customer_subject(ref))

    # The import (A16): one entry naming the file by its digest.
    upload = _ok(rt.owner_upload(_v1_file(rt)), "import_upload")
    assert _log(rt) == log  # an upload changes nothing (A16 rule 1)
    _ok(
        rt.owner(
            "confirm_import",
            upload_number=upload["upload_number"],
            file_digest=upload["file_digest"],
            import_choices={
                "picks": [{"project_id": V1_PROJECT_ID, "display_name": None, "alias": None}],
                "customers": [],
            },
        ),
        "import_accepted",
    )
    check("import_accepted", {"subject_kind": "import", "file_digest": upload["file_digest"]})

    # The erasure of old entries, before a date older than every entry: it
    # removes none and still writes its own (A15 rule 6).
    erased = _ok(
        rt.owner("erase_audit_entries", erase_before="2026-01-01"),
        "audit_erased",
    )
    assert erased["removed"] == 0
    check("audit_entries_erased", {"subject_kind": "none"})
    assert log[-1]["erased_before"] == "2026-01-01"
    return run


# --- Required test 1 -------------------------------------------------------


def test_stale_refused_correction_writes_no_entry(semantic_runtime):
    """A14 rule 2, A14-1: a correction refused as stale writes no entry and
    changes nothing; the same correction at the current revision writes
    one."""
    rt = semantic_runtime
    project = _create_project(rt, "Casa Lopez")
    pid = project["project_id"]
    current = _ok(
        rt.owner(
            "correct_project",
            target=pid,
            stated_version=project["revision"],
            project=_project_facts("Casa Lopez, segunda"),
        ),
        "project_card",
    )["card"]
    log = _log(rt)
    assert [e["action"] for e in log] == ["project_created", "project_corrected"]
    store_log = _store_log(rt)
    projects = rt.store_rows("project_rows")

    stale = rt.owner(
        "correct_project",
        target=pid,
        stated_version=project["revision"],  # the revision before the last
        project=_project_facts("Casa Lopez, tercera"),
    )
    assert _refusal(stale) == ("stale", STAGE_VERSION, ["stale_revision"])

    assert _log(rt) == log
    assert _store_log(rt) == store_log
    assert rt.store_rows("project_rows") == projects
    assert _project(rt, pid) == current

    # Control: at the current revision the correction writes its entry.
    _ok(
        rt.owner(
            "correct_project",
            target=pid,
            stated_version=current["revision"],
            project=_project_facts("Casa Lopez, tercera"),
        ),
        "project_card",
    )
    _one_new_entry(rt, log, "project_corrected", _project_subject(pid))


def test_refused_actions_write_no_entry(semantic_runtime):
    """A14 rule 2: a refused sign-in, an unknown id and a failed check of
    rights write no entry."""
    rt = semantic_runtime
    project = _create_project(rt)
    log = _log(rt)
    store_log = _store_log(rt)

    assert _refusal(rt.sign_in(credential=WRONG_CREDENTIAL)) == (
        "unauthenticated",
        STAGE_AUTHENTICATION,
        ["sign_in_refused"],
    )
    unknown = rt.owner(
        "correct_project",
        target=MISSING_PROJECT,
        stated_version=1,
        project=_project_facts("Nadie"),
    )
    assert _refusal(unknown) == ("not_found", STAGE_EXISTENCE, ["unknown_project"])
    # Listing projects is outside PresuPro's row (A09 rule 2, SERVICE_RIGHTS).
    no_right = rt.service("presupro", "list_projects", {})
    assert _refusal(no_right) == (
        "not_permitted",
        STAGE_AUTHENTICATION,
        ["outside_service_rights"],
    )
    # A new sign-in (a session's runtime state, never an entry, State 5
    # sign_in_owner) for the owner reads below.
    assert rt.sign_in()["answer_kind"] == "signed_in"

    assert _log(rt) == log
    assert _store_log(rt) == store_log
    # Control: an accepted change still writes its entry.
    _ok(
        rt.owner(
            "correct_project",
            target=project["project_id"],
            stated_version=project["revision"],
            project=_project_facts("Casa Lopez, nueva"),
        ),
        "project_card",
    )
    _one_new_entry(rt, log, "project_corrected", _project_subject(project["project_id"]))


# --- Required test 2 -------------------------------------------------------


def test_noop_archive_writes_no_entry_no_confirmation(semantic_runtime):
    """A14 rules 3, 5, A14-1: archiving an archived project is accepted with
    `changed: false`, writes no entry and so mints no confirmation id; the
    first archive wrote one entry with its confirmation id."""
    rt = semantic_runtime
    project = _create_project(rt)
    pid = project["project_id"]

    first = _ok(
        rt.owner("archive_project", target=pid, stated_version=project["revision"]),
        "project_card",
    )
    assert first["card"]["status"] == "archived"
    log = _log(rt)
    assert [e["action"] for e in log] == ["project_created", "project_archived"]
    # Control: the archive that changed state minted its confirmation id.
    assert isinstance(log[-1]["confirmation_id"], str) and log[-1]["confirmation_id"]
    assert log[0]["confirmation_id"] is None  # creating is not confirmed
    store_log = _store_log(rt)
    projects = rt.store_rows("project_rows")

    again = _ok(
        rt.owner(
            "archive_project", target=pid, stated_version=first["card"]["revision"]
        ),
        "project_card",
    )
    assert again["changed"] is False  # A05, State 5 "Repeats"
    assert again["card"] == first["card"]
    # No answer carries a confirmation id (State 6 ProjectCardAnswer); the
    # entry is its only home, and none was written.
    assert "confirmation_id" not in again
    assert _log(rt) == log
    assert _store_log(rt) == store_log
    assert rt.store_rows("project_rows") == projects


def test_noop_correction_and_regrant_write_no_entry(semantic_runtime):
    """A14 rule 3: an equal correction (A03 rule 4) and granting a project
    already granted (A05) change nothing and write no entry."""
    rt = semantic_runtime
    project = _create_project(rt, "Casa Lopez")
    pid = project["project_id"]
    access = _register(rt, "a14-noop-session")
    granted = _ok(
        rt.owner(
            "grant_project",
            target="a14-noop-session",
            stated_version=access["access_version"],
            project_id=pid,
            make_active=False,
        ),
        "session_access",
    )
    log = _log(rt)
    store_log = _store_log(rt)

    equal = _ok(
        rt.owner(
            "correct_project",
            target=pid,
            stated_version=project["revision"],
            project=_project_facts("Casa Lopez"),
        ),
        "project_card",
    )
    assert equal["changed"] is False
    regrant = _ok(
        rt.owner(
            "grant_project",
            target="a14-noop-session",
            stated_version=granted["access"]["access_version"],
            project_id=pid,
            make_active=False,
        ),
        "session_access",
    )
    assert regrant["changed"] is False
    assert _log(rt) == log
    assert _store_log(rt) == store_log


# --- Required test 3 -------------------------------------------------------


def test_failed_store_leaves_no_change_no_entry(semantic_runtime):
    """A14 rule 1, A14-1: a correction whose transaction fails — at its last
    store call, the entry's insertion, or at its first, the project's own
    write — is answered `internal_error` (`transaction_failed`) and leaves
    neither the change nor its entry; repeated, it stores both."""
    rt = semantic_runtime
    project = _create_project(rt)
    pid = project["project_id"]
    log = _log(rt)
    store_log = _store_log(rt)
    projects = rt.store_rows("project_rows")

    # The failure at the action's last store call, the entry's insertion
    # (after update_project_row and upsert_audit_sequence_row): had the
    # change been committed apart from its entry, it would stay without one.
    rt.faults.fail_store_call("insert_audit_entry_row")
    failed = rt.owner(
        "correct_project",
        target=pid,
        stated_version=project["revision"],
        project=_project_facts("Casa Lopez, fallida"),
    )
    # State 5 closed set: internal_error carries no stage.
    assert _refusal(failed) == ("internal_error", None, ["transaction_failed"])

    assert _project(rt, pid) == project
    assert rt.store_rows("project_rows") == projects
    assert _log(rt) == log
    assert _store_log(rt) == store_log

    # The failure at the change's own write, the first call: had the entry
    # been committed apart from (before) the change, it would stay alone.
    rt.faults.fail_store_call("update_project_row")
    failed = rt.owner(
        "correct_project",
        target=pid,
        stated_version=project["revision"],
        project=_project_facts("Casa Lopez, fallida"),
    )
    assert _refusal(failed) == ("internal_error", None, ["transaction_failed"])
    assert _project(rt, pid) == project
    assert rt.store_rows("project_rows") == projects
    assert _log(rt) == log
    assert _store_log(rt) == store_log

    # Control: the same correction, no failure, stores the change and entry.
    corrected = _ok(
        rt.owner(
            "correct_project",
            target=pid,
            stated_version=project["revision"],
            project=_project_facts("Casa Lopez, fallida"),
        ),
        "project_card",
    )
    assert corrected["card"]["display_name"] == "Casa Lopez, fallida"
    assert corrected["card"]["revision"] == project["revision"] + 1
    _one_new_entry(rt, log, "project_corrected", _project_subject(pid))


# --- Required test 4 -------------------------------------------------------


def test_agent_projection_read_writes_no_entry(semantic_runtime):
    """A14 rule 4, A14-1: Kernel reading the agent projection, like every
    other read — a service's, the owner's — writes no entry."""
    rt = semantic_runtime
    project = _create_project(rt)
    pid = project["project_id"]
    sid = "a14-kernel-reader"
    access = _register(rt, sid)
    assert access["access_version"] == ACCESS_VERSION_FIRST
    _ok(
        rt.owner(
            "grant_project",
            target=sid,
            stated_version=access["access_version"],
            project_id=pid,
            make_active=True,
        ),
        "session_access",
    )
    log = _log(rt)
    assert [e["action"] for e in log] == ["project_created", "session_project_granted"]
    store_log = _store_log(rt)

    # Control: each read is answered, not refused.
    view = _ok(
        rt.service(KERNEL, "read_agent_projection", {"project_id": pid}, kernel_session=sid),
        "agent_projection",
    )
    assert view["view"]["project_id"] == pid
    # The same read naming no project uses the active one (A10 rule 2).
    _ok(
        rt.service(KERNEL, "read_agent_projection", {}, kernel_session=sid),
        "agent_projection",
    )
    _ok(rt.service(KERNEL, "read_session_access", {}, kernel_session=sid), "session_access")
    assert rt.service(PORTAL, "read_project", {"project_id": pid})["answer_kind"] != "refused"
    assert rt.service(CABINET, "list_projects", {})["answer_kind"] != "refused"
    _ok(rt.owner("read_project", target=pid), "project_card")
    _ok(rt.owner("list_projects"), "project_list")
    _ok(rt.owner("list_sessions"), "session_list")
    _ok(rt.owner("read_session", target=sid), "session_access")

    assert _log(rt) == log
    assert _store_log(rt) == store_log


# --- Required test 5 -------------------------------------------------------


def test_every_entry_outcome_is_accepted(semantic_runtime):
    """A14 rule 6, A14-2: across every action that writes an entry, with
    refusals and no-change actions between them, every stored entry has the
    outcome `accepted` and there is no entry beside the accepted changes."""
    rt = semantic_runtime
    run = _every_audited_action(rt)

    # Refusals and a no-change action after the run write nothing.
    project = _create_project(rt, "Despues")
    run.append("project_created")
    stale = rt.owner(
        "correct_project",
        target=project["project_id"],
        stated_version=project["revision"] + 1,
        project=_project_facts("Despues, corregido"),
    )
    assert _refusal(stale) == ("stale", STAGE_VERSION, ["stale_revision"])
    assert rt.sign_in(credential=WRONG_CREDENTIAL)["answer_kind"] == "refused"
    rt.sign_in()
    equal = _ok(
        rt.owner(
            "correct_project",
            target=project["project_id"],
            stated_version=project["revision"],
            project=_project_facts("Despues"),
        ),
        "project_card",
    )
    assert equal["changed"] is False

    log = _log(rt)
    assert [e["action"] for e in log] == run
    assert {e["outcome"] for e in log} == {"accepted"}
    # Every AuditAction of State 6 was written once at least.
    assert set(run) == {
        "project_created",
        "project_corrected",
        "project_archived",
        "project_anonymised",
        "project_deleted",
        "customer_recorded",
        "customer_corrected",
        "customer_erased",
        "customer_restricted",
        "customer_restriction_lifted",
        "customer_relationship_ended",
        "customer_relationship_resumed",
        "session_project_granted",
        "session_project_revoked",
        "import_accepted",
        "audit_entries_erased",
    }
    # The store holds exactly these entries.
    assert len(rt.store_rows("audit_entry_rows")) == len(log)


# --- Required test 6 -------------------------------------------------------


def test_accepted_change_writes_one_entry_in_transaction(semantic_runtime):
    """A14 rule 1, A14-1: each action of M09 accepted and changing its record
    writes exactly one entry; the restriction of a Customer whose transaction
    fails leaves neither the restriction nor its entry, and repeated writes
    both."""
    rt = semantic_runtime
    _every_audited_action(rt)

    before_record = _log(rt)
    customer = _ok(
        rt.owner(
            "record_customer",
            request_id=rt.new_request_id(),
            customer=_customer_facts("Luis Garcia", "+34 600 000 003"),
        ),
        "customer",
    )["customer"]
    ref = customer["customer_ref"]
    # The Customer this test restricts is itself an accepted change of
    # M09.actions: its recording wrote exactly one entry, customer_recorded
    # (OWNER_AUDIT_ACTIONS), outcome accepted.
    _one_new_entry(rt, before_record, "customer_recorded", _customer_subject(ref))
    log = _log(rt)
    store_log = _store_log(rt)
    customers = rt.store_rows("customer_rows")

    # The failure at the restriction's last store call, the entry's
    # insertion: had the restriction been committed apart, it would stay.
    rt.faults.fail_store_call("insert_audit_entry_row")
    failed = rt.owner(
        "mark_customer", target=ref, stated_version=customer["revision"], transition="restrict"
    )
    assert _refusal(failed) == ("internal_error", None, ["transaction_failed"])
    read = _ok(rt.owner("read_customer", target=ref), "customer")["customer"]
    assert read == customer
    assert read["restricted_at"] is None
    assert rt.store_rows("customer_rows") == customers
    assert _log(rt) == log
    assert _store_log(rt) == store_log

    # The failure at the restriction's own write, the first call: an entry
    # committed apart from it would stay alone.
    rt.faults.fail_store_call("update_customer_row")
    failed = rt.owner(
        "mark_customer", target=ref, stated_version=customer["revision"], transition="restrict"
    )
    assert _refusal(failed) == ("internal_error", None, ["transaction_failed"])
    assert _ok(rt.owner("read_customer", target=ref), "customer")["customer"] == customer
    assert rt.store_rows("customer_rows") == customers
    assert _log(rt) == log
    assert _store_log(rt) == store_log

    restricted = _ok(
        rt.owner(
            "mark_customer", target=ref, stated_version=customer["revision"], transition="restrict"
        ),
        "customer",
    )["customer"]
    assert restricted["restricted_at"] is not None
    assert restricted["revision"] == customer["revision"] + 1
    _one_new_entry(rt, log, "customer_restricted", _customer_subject(ref))
