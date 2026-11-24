"""Witness tests for accepted decision A04 (02_rules_records.md).

Every action that moves a Project's or a Customer's revision states the
revision it was made against; a stated revision that is not the current one,
or none for a record that has one, is refused as stale and nothing changes;
an erased Customer and an anonymised project have no revision, so a revision
stated for one is stale; an accepted change moves the revision by one and the
last-changed instant to now, one that changes nothing moves neither; every
operation checks in one order — (1) authentication and rights, the owner's
session, CSRF value and confirmation; (2) agent authority; (3) existence;
(4) values; (5) the stated revision; (6) lifecycle — and the first failing
stage is its answer. Each test carries the witness name its Required test
declares.

The Factory project `registry` supplies the ``semantic_runtime`` fixture
(``tests/semantic/RUNTIME_SURFACE.md``): a fresh instance per test, driven
over its two real listeners. Expected values come from State 2 (A02, A03,
A04, A05, A10, A13), State 5 (`50_public_apis_3_records.md`:
`projects.correct_project`, `projects.archive_project`,
`projects.erase_project`, `projects.read_project_card`, `projects.add_room`,
`customers.mark_customer`, `customers.erase_customer_contact`,
`customers.read_customer`; `50_public_apis_2_sessions.md`:
`agent_sessions.register_session`, `agent_sessions.check_agent_call`,
`agent_sessions.grant_project`; `50_public_apis_5_surfaces.md`:
`operations.perform_service_operation`; "Closed set of refusal codes" in
`50_public_apis_0_conventions.md`) and State 6 (answer models
`ProjectCardAnswer`, `ProjectErasedAnswer`, `CustomerAnswer`, `RoomAnswer`,
`RefusedAnswer`; `ProjectCard`, `AnonymisedProject`, `CustomerDetail`,
`ErasedCustomer`; constants of `70_data_provider_closure.json`).

Fixture surface used here:

- ``owner(action, target=None, stated_version=None, confirm=True,
  **values)`` -> answer, for `create_project`, `correct_project`,
  `archive_project` and `erase_project` (each confirmed by the fixture,
  A13 rule 6), `read_project`, `record_customer`, `mark_customer`,
  `erase_customer`, `read_customer`, `grant_project`; ``values`` are
  `OwnerValues` fields: ``request_id``, ``project``, ``customer``,
  ``transition``, ``erasure``, ``project_id``;
- ``owner(..., csrf=None)``: the owner request sent without the session's
  CSRF value, for `test_csrf_refusal_before_stale`;
- ``service("cabinet_kernel", operation, inputs, kernel_session=…)`` ->
  answer, for `register_agent_session` and `add_room`;
- ``new_request_id()``; ``clock.advance(hours=…)`` / ``(days=…)``, each
  followed by ``sign_in()``: the held owner session is past its 30 idle
  minutes (A13 rule 2; RUNTIME_SURFACE.md "The owner's session");
- ``store_rows(table)`` for `project_rows`, `customer_rows`,
  `audit_entry_rows` (70_persistence_closure.json), where "nothing changed"
  needs more than a surface read.
"""

from datetime import datetime, timedelta, timezone

# Default start instant of the fixture (RUNTIME_SURFACE.md, "Time").
START = datetime(2026, 1, 5, 9, 0, tzinfo=timezone.utc)

# Stage numbers of A04 rule 6, 70_data_provider_closure.json:
STAGE_AUTHENTICATION = 1  # REFUSAL_STAGE_AUTHENTICATION
STAGE_AGENT_SESSION = 2  # REFUSAL_STAGE_AGENT_SESSION
STAGE_EXISTENCE = 3  # REFUSAL_STAGE_EXISTENCE
STAGE_VALUES = 4  # REFUSAL_STAGE_VALUES
STAGE_VERSION = 5  # REFUSAL_STAGE_VERSION
STAGE_LIFECYCLE = 6  # REFUSAL_STAGE_LIFECYCLE
# REVISION_FIRST = 1, ACCESS_VERSION_FIRST = 1 (70_data_provider_closure.json).
REVISION_FIRST = 1
ACCESS_VERSION_FIRST = 1

STALE = ("stale", STAGE_VERSION, ["stale_revision"])

ADDRESS = "Calle Mayor 1, Valencia"
KERNEL = "cabinet_kernel"  # ServiceName (State 6)


def _instant(text):
    """An answer's instant: ISO text in UTC ending in `Z` (RUNTIME_SURFACE)."""
    assert text.endswith("Z"), text
    return datetime.fromisoformat(text[:-1] + "+00:00")


def _refusal(answer):
    """(code, stage, kinds) of a refused answer (State 5 closed set)."""
    assert answer["answer_kind"] == "refused", answer
    return (
        answer["code"],
        answer["stage"],
        sorted(f["kind"] for f in answer["failures"]),
    )


def _project_facts(display_name="Casa Lopez", alias=None, address=ADDRESS):
    # State 6 GivenProjectFacts; the object's kind and characteristics absent.
    return {
        "display_name": display_name,
        "alias": alias,
        "customer_ref": None,
        "address": address,
        "object_kind": None,
        "floor_area": None,
        "rooms_count": None,
        "floor": None,
    }


def _customer_facts(name="Ana Lopez"):
    # State 6 GivenCustomerFacts.
    return {
        "name": name,
        "customer_kind": "person",
        "phone": "+34 600 000 001",
        "email": "ana@example.test",
        "language": "es",
        "tax_id": None,
        "legal_name": None,
    }


def _create_project(rt, display_name="Casa Lopez"):
    answer = rt.owner(
        "create_project",
        request_id=rt.new_request_id(),
        project=_project_facts(display_name),
    )
    assert answer["answer_kind"] == "project_card", answer
    assert answer["card"]["revision"] == REVISION_FIRST
    return answer["card"]["project_id"]


def _correct(rt, project_id, revision, display_name, **owner_kw):
    return rt.owner(
        "correct_project",
        target=project_id,
        stated_version=revision,
        project=_project_facts(display_name),
        **owner_kw,
    )


def _card(rt, project_id):
    answer = rt.owner("read_project", target=project_id)
    assert answer["answer_kind"] == "project_card", answer
    return answer["card"]


def _archive_raw(rt, project_id, revision):
    return rt.owner("archive_project", target=project_id, stated_version=revision)


def _archive(rt, project_id, revision):
    answer = _archive_raw(rt, project_id, revision)
    assert answer["answer_kind"] == "project_card", answer
    return answer


def _erase_project(rt, project_id, revision, erasure):
    return rt.owner(
        "erase_project", target=project_id, stated_version=revision, erasure=erasure
    )


def _is_anonymised_form(card, project_id):
    """State 5 Conventions "Erased records answer": an anonymised project
    answers its `project_id`, status `archived` and the anonymised mark,
    nothing else (State 6 AnonymisedProject). The wire carries no `view_kind`
    (RUNTIME_SURFACE.md "Answers are the wire answers"): the form is told by
    its fields alone."""
    assert set(card) == {"project_id", "status"}, card
    assert card["project_id"] == project_id
    assert card["status"] == "archived"
    return True


def _record_customer(rt, name="Ana Lopez"):
    answer = rt.owner(
        "record_customer",
        request_id=rt.new_request_id(),
        customer=_customer_facts(name),
    )
    assert answer["answer_kind"] == "customer", answer
    assert answer["customer"]["revision"] == REVISION_FIRST
    return answer["customer"]["customer_ref"]


def _customer(rt, customer_ref):
    answer = rt.owner("read_customer", target=customer_ref)
    assert answer["answer_kind"] == "customer", answer
    return answer["customer"]


def _mark(rt, customer_ref, revision, transition="restrict"):
    return rt.owner(
        "mark_customer",
        target=customer_ref,
        stated_version=revision,
        transition=transition,
    )


def _erase_customer(rt, customer_ref, revision):
    return rt.owner("erase_customer", target=customer_ref, stated_version=revision)


def _is_erased_form(customer, customer_ref):
    """State 5 Conventions: an erased Customer answers its `customer_ref`, the
    erased mark and its instant, nothing else (State 6 ErasedCustomer). The
    wire carries no `view_kind`: the form is told by its fields alone."""
    assert set(customer) == {"customer_ref", "erased_at"}, customer
    assert customer["customer_ref"] == customer_ref
    return True


def _rows(rt, *tables):
    return {t: rt.store_rows(t) for t in tables}


def test_second_tab_stale_revision_refused(semantic_runtime):
    """[witness: verification:registry_a04_second_tab_stale_revision_refused]

    A04 Required test 1: two owner tabs correct one project from revision 3;
    the first is accepted, the second is refused as stale. Shows A04-2,
    A04-3.
    """
    rt = semantic_runtime
    pid = _create_project(rt, "Casa v1")
    assert _correct(rt, pid, 1, "Casa v2")["card"]["revision"] == 2
    assert _correct(rt, pid, 2, "Casa v3")["card"]["revision"] == 3
    shown_in_both_tabs = _card(rt, pid)
    assert shown_in_both_tabs["revision"] == 3

    rt.clock.advance(hours=1)
    rt.sign_in()  # past the 30 idle minutes: a new owner session (A13 rule 2)
    first = _correct(rt, pid, 3, "Casa tab one")
    # A04-3: accepted and changed → revision + 1, last-changed = now.
    assert first["answer_kind"] == "project_card", first
    assert first["changed"] is True
    assert first["card"]["display_name"] == "Casa tab one"
    assert first["card"]["revision"] == 4
    assert _instant(first["card"]["last_changed_at"]) == START + timedelta(hours=1)
    after_first = _card(rt, pid)
    rows = _rows(rt, "project_rows", "audit_entry_rows")

    rt.clock.advance(hours=1)
    rt.sign_in()  # past the 30 idle minutes: a new owner session (A13 rule 2)
    # A04-2: the second tab states 3, no longer current → `stale`, stage (5),
    # `stale_revision` (State 5 closed set; correct_project Errors).
    second = _correct(rt, pid, 3, "Casa tab two")
    assert _refusal(second) == STALE
    # A04-2: r unchanged — read back and the store (no write, no entry).
    assert _card(rt, pid) == after_first
    assert _rows(rt, "project_rows", "audit_entry_rows") == rows

    # Control: the second tab, read again (revision 4), is accepted — the
    # refusal is the stated revision, not a second correction as such.
    again = _correct(rt, pid, 4, "Casa tab two")
    assert again["changed"] is True
    assert again["card"]["display_name"] == "Casa tab two"
    assert again["card"]["revision"] == 5


def test_restrict_with_old_revision_refused(semantic_runtime):
    """[witness: verification:registry_a04_restrict_with_old_revision_refused]

    A04 Required test 2: restricting a customer with an old revision is
    refused. Shows A04-2.
    """
    rt = semantic_runtime
    ref = _record_customer(rt)
    corrected = rt.owner(
        "correct_customer",
        target=ref,
        stated_version=REVISION_FIRST,
        customer=_customer_facts("Ana Lopez Garcia"),
    )
    assert corrected["customer"]["revision"] == REVISION_FIRST + 1
    before = _customer(rt, ref)
    rows = _rows(rt, "customer_rows", "audit_entry_rows")

    rt.clock.advance(hours=1)
    rt.sign_in()  # past the 30 idle minutes: a new owner session (A13 rule 2)
    # A04 rule 1: restricting states the revision; rule 2: an old one is
    # stale (State 5 mark_customer Errors).
    old = _mark(rt, ref, REVISION_FIRST)
    assert _refusal(old) == STALE
    after = _customer(rt, ref)
    assert after == before
    assert after["restricted_at"] is None
    assert _rows(rt, "customer_rows", "audit_entry_rows") == rows

    # Control: the current revision restricts, moving the revision once.
    current = _mark(rt, ref, REVISION_FIRST + 1)
    assert current["answer_kind"] == "customer", current
    assert current["changed"] is True
    assert _instant(current["customer"]["restricted_at"]) == START + timedelta(hours=1)
    assert current["customer"]["revision"] == REVISION_FIRST + 2


def test_archive_moves_revision_once(semantic_runtime):
    """[witness: verification:registry_a04_archive_moves_revision_once]

    A04 Required test 3: archiving moves the revision once; archiving again
    with the new revision answers the project unchanged. Shows A04-3, A04-6.
    """
    rt = semantic_runtime
    pid = _create_project(rt)

    rt.clock.advance(hours=1)
    rt.sign_in()  # past the 30 idle minutes: a new owner session (A13 rule 2)
    archived = _archive(rt, pid, REVISION_FIRST)
    # A04-3: accepted and changed → revision + 1 and last-changed = now;
    # State 5 archive_project: "its revision and last-changed instant move
    # once"; the card's archived date is the UTC date of that instant.
    assert archived["changed"] is True
    card = archived["card"]
    assert card["status"] == "archived"
    assert card["revision"] == REVISION_FIRST + 1
    assert _instant(card["last_changed_at"]) == START + timedelta(hours=1)
    assert card["archived_on"] == "2026-01-05"
    assert _card(rt, pid) == card
    rows = _rows(rt, "project_rows", "audit_entry_rows")

    # A day later, so a re-stamped archived instant would show in the
    # archived date as well as in the last-changed instant.
    rt.clock.advance(days=1)
    rt.sign_in()  # past the 30 idle minutes: a new owner session (A13 rule 2)
    # A04-6 / A05 rules 1–2: archiving again with the new revision is
    # accepted, changes nothing: revision, last-changed instant and the
    # written-once archived instant (State 1 M01) stay, no entry.
    again = _archive(rt, pid, REVISION_FIRST + 1)
    assert again["changed"] is False
    assert again["card"] == card
    assert _card(rt, pid) == card
    assert _rows(rt, "project_rows", "audit_entry_rows") == rows

    # A04 rule 3: a no-change action still states the revision; the old one
    # is stale.
    assert _refusal(_archive_raw(rt, pid, REVISION_FIRST)) == STALE
    assert _card(rt, pid) == card


def test_stale_before_archived_refusal(semantic_runtime):
    """[witness: verification:registry_a04_stale_before_archived_refusal]

    A04 Required test 4: correcting an archived project with a stale revision
    is refused as stale, not as archived. Shows A04-1, A04-2.
    """
    rt = semantic_runtime
    pid = _create_project(rt)
    archived = _archive(rt, pid, REVISION_FIRST)["card"]
    assert archived["revision"] == REVISION_FIRST + 1
    rows = _rows(rt, "project_rows", "audit_entry_rows")

    # A04-1: stage (5), the stated revision, comes before stage (6), the
    # archive check — the answer is `stale` alone.
    stale = _correct(rt, pid, REVISION_FIRST, "Casa renamed")
    assert _refusal(stale) == STALE

    # Control: the current revision passes stage (5) and is refused at
    # stage (6) as archived (State 5 correct_project Errors), so the
    # archived refusal exists and the order is what separates the two.
    current = _correct(rt, pid, REVISION_FIRST + 1, "Casa renamed")
    assert _refusal(current) == ("refused", STAGE_LIFECYCLE, ["archived"])

    assert _card(rt, pid) == archived
    assert _rows(rt, "project_rows", "audit_entry_rows") == rows


def test_session_set_hides_missing_name(semantic_runtime):
    """[witness: verification:registry_a04_session_set_hides_missing_name]

    A04 Required test 5: Kernel naming a project outside its set with a blank
    room name receives the not-found answer, not the missing-name refusal.
    Shows A04-1.
    """
    rt = semantic_runtime
    session = "a04-kernel-session-1"
    registered = rt.service(KERNEL, "register_agent_session", kernel_session=session)
    assert registered["answer_kind"] != "refused", registered

    outside = _create_project(rt, "Outside the set")
    inside = _create_project(rt, "Inside the set")
    # A new session has an empty set and access version 1 (State 5
    # register_session; ACCESS_VERSION_FIRST); the owner grants `inside`.
    granted = rt.owner(
        "grant_project",
        target=session,
        stated_version=ACCESS_VERSION_FIRST,
        project_id=inside,
    )
    assert granted["answer_kind"] == "session_access", granted
    assert inside in granted["access"]["granted_project_ids"]
    assert outside not in granted["access"]["granted_project_ids"]

    def add_room(project_id, name):
        return rt.service(
            KERNEL,
            "add_room",
            inputs={
                "project_id": project_id,
                "room_name": name,
                "request_id": rt.new_request_id(),
            },
            kernel_session=session,
        )

    rows = _rows(rt, "room_rows", "project_rows")
    # A04 rule 6 (2): the set check's refusal hides every later failure; State
    # 5 closed set: `not_found`, always stage (2), `agent_call_refused` alone
    # — no `missing_value` beside it (A10 rule 3).
    hidden = add_room(outside, "   ")
    assert _refusal(hidden) == ("not_found", STAGE_AGENT_SESSION, ["agent_call_refused"])
    assert _rows(rt, "room_rows", "project_rows") == rows
    assert _card(rt, outside)["rooms"] == []

    # Control 1: the same blank name on a project in the set reaches stage
    # (4): `invalid_request`, `missing_value` (A02 rule 1, add_room Errors).
    blank = add_room(inside, "   ")
    assert _refusal(blank) == ("invalid_request", STAGE_VALUES, ["missing_value"])
    assert _card(rt, inside)["rooms"] == []

    # Control 2: a named room on a project in the set is added — Kernel's
    # add_room is reachable at all.
    added = add_room(inside, "Cocina")
    assert added["answer_kind"] == "room", added
    assert added["room"]["name"] == "Cocina"
    assert [r["name"] for r in _card(rt, inside)["rooms"]] == ["Cocina"]
    assert _card(rt, outside)["rooms"] == []


def test_erasure_resubmit_with_revision_stale(semantic_runtime):
    """[witness: verification:registry_a04_erasure_resubmit_with_revision_stale]

    A04 Required test 6: erasing a Customer's contact data again from the
    form that erased it, stating that revision, is refused as stale and
    changes nothing; erasing it stating no revision answers it unchanged.
    Shows A04-4, A04-5.
    """
    rt = semantic_runtime
    ref = _record_customer(rt)

    rt.clock.advance(hours=1)
    rt.sign_in()  # past the 30 idle minutes: a new owner session (A13 rule 2)
    erased = _erase_customer(rt, ref, REVISION_FIRST)
    assert erased["answer_kind"] == "customer", erased
    assert erased["changed"] is True
    # A04-4: an accepted erasure leaves no revision — the erased form only
    # (M04, State 5 erase_customer_contact).
    assert _is_erased_form(erased["customer"], ref)
    erased_at = _instant(erased["customer"]["erased_at"])
    assert erased_at == START + timedelta(hours=1)
    after_erasure = _customer(rt, ref)
    assert after_erasure == erased["customer"]
    rows = _rows(rt, "customer_rows", "audit_entry_rows")

    rt.clock.advance(hours=1)
    rt.sign_in()  # past the 30 idle minutes: a new owner session (A13 rule 2)
    # A04-5: the form that erased it resubmitted, stating revision 1 for a
    # record that has none → `stale` (A04 rule 3).
    resubmitted = _erase_customer(rt, ref, REVISION_FIRST)
    assert _refusal(resubmitted) == STALE
    assert _customer(rt, ref) == after_erasure
    assert _rows(rt, "customer_rows", "audit_entry_rows") == rows

    # Control, A04 rule 3 / A05 rule 1: stating none, the erasure of an
    # erased Customer is accepted and changes nothing — its erased instant
    # stays, no entry.
    unchanged = _erase_customer(rt, ref, None)
    assert unchanged["answer_kind"] == "customer", unchanged
    assert unchanged["changed"] is False
    assert unchanged["customer"] == after_erasure
    assert _instant(unchanged["customer"]["erased_at"]) == erased_at
    assert _rows(rt, "customer_rows", "audit_entry_rows") == rows


def test_erased_customer_stale_before_erased(semantic_runtime):
    """[witness: verification:registry_a04_erased_customer_stale_before_erased]

    A04 Required test 7: restricting an erased Customer from a card read
    before its erasure is refused as stale, not as erased. Shows A04-1,
    A04-5.
    """
    rt = semantic_runtime
    ref = _record_customer(rt)
    card_before_erasure = _customer(rt, ref)
    assert card_before_erasure["revision"] == REVISION_FIRST

    erased = _erase_customer(rt, ref, REVISION_FIRST)
    assert erased["changed"] is True
    after_erasure = _customer(rt, ref)
    assert _is_erased_form(after_erasure, ref)
    rows = _rows(rt, "customer_rows", "audit_entry_rows")

    # A04-5 and A04-1: the old card's revision is stale (stage 5), answered
    # before the erased Customer's lifecycle refusal (stage 6).
    stale = _mark(rt, ref, card_before_erasure["revision"])
    assert _refusal(stale) == STALE

    # Control: stating none — what a card of the erased Customer carries —
    # passes stage (5) and is refused at stage (6) `customer_erased` (State 5
    # mark_customer Errors), so the erased refusal exists and only the order
    # separates them.
    none_stated = _mark(rt, ref, None)
    assert _refusal(none_stated) == ("refused", STAGE_LIFECYCLE, ["customer_erased"])

    assert _customer(rt, ref) == after_erasure
    assert _rows(rt, "customer_rows", "audit_entry_rows") == rows


def test_missing_revision_refused_as_stale(semantic_runtime):
    """[witness: verification:registry_a04_missing_revision_refused_as_stale]

    A04 Required test 8: restricting a Customer that has a revision, stating
    none, is refused as stale, not as a missing value. Shows A04-2.
    """
    rt = semantic_runtime
    ref = _record_customer(rt)
    before = _customer(rt, ref)
    rows = _rows(rt, "customer_rows", "audit_entry_rows")

    # A04 rule 2: "so is an action that states none for a record that has
    # one" — `stale`, stage (5), not `invalid_request` `missing_value`.
    none_stated = _mark(rt, ref, None)
    assert _refusal(none_stated) == STALE
    assert _customer(rt, ref) == before
    assert _customer(rt, ref)["restricted_at"] is None
    assert _rows(rt, "customer_rows", "audit_entry_rows") == rows

    # Control: stating the current revision restricts.
    stated = _mark(rt, ref, REVISION_FIRST)
    assert stated["changed"] is True
    assert stated["customer"]["restricted_at"] is not None
    assert stated["customer"]["revision"] == REVISION_FIRST + 1


def test_csrf_refusal_before_stale(semantic_runtime):
    """[witness: verification:registry_a04_csrf_refusal_before_stale]

    A04 Required test 9: an owner correction without the session's CSRF value
    and stating a stale revision is refused for the CSRF value, not as stale.
    Shows A04-1.

    Uses ``owner(..., csrf=None)`` (RUNTIME_SURFACE.md, `owner`):
    the page status alone cannot tell the two refusals apart, both being 422
    (REFUSAL_HTTP_STATUSES).
    """
    rt = semantic_runtime
    pid = _create_project(rt, "Casa v1")
    assert _correct(rt, pid, REVISION_FIRST, "Casa v2")["card"]["revision"] == 2
    before = _card(rt, pid)
    rows = _rows(rt, "project_rows", "audit_entry_rows")

    # A04 rule 6 (1): for the owner, a valid session, then for a change its
    # CSRF value (A13 rule 5) — stage (1), `not_permitted`, `csrf_refused`
    # (State 5 closed set), before stage (5)'s stale revision.
    no_csrf = _correct(rt, pid, REVISION_FIRST, "Casa v3", csrf=None)
    assert _refusal(no_csrf) == ("not_permitted", STAGE_AUTHENTICATION, ["csrf_refused"])
    assert _card(rt, pid) == before
    assert _rows(rt, "project_rows", "audit_entry_rows") == rows

    # Control 1: the same stale request with the CSRF value is refused at
    # stage (5) — so the answer above is the CSRF check coming first.
    with_csrf = _correct(rt, pid, REVISION_FIRST, "Casa v3")
    assert _refusal(with_csrf) == STALE
    assert _card(rt, pid) == before

    # Control 2: no CSRF value with the current revision is still refused —
    # the CSRF check does not depend on the revision.
    no_csrf_current = _correct(rt, pid, 2, "Casa v3", csrf=None)
    assert _refusal(no_csrf_current) == (
        "not_permitted",
        STAGE_AUTHENTICATION,
        ["csrf_refused"],
    )
    assert _card(rt, pid) == before

    # Control 3: CSRF value and current revision → accepted.
    accepted = _correct(rt, pid, 2, "Casa v3")
    assert accepted["changed"] is True
    assert accepted["card"]["revision"] == 3


def test_anonymised_project_former_revision_stale(semantic_runtime):
    """[witness: verification:registry_a04_anonymised_project_former_revision_stale]

    A04 Required test 10: after anonymising a project it has no revision:
    correcting or erasing it stating its former revision is refused as stale
    and changes nothing; a project deleted whole is not found. Shows A04-4,
    A04-5.
    """
    rt = semantic_runtime
    pid = _create_project(rt, "Casa anonimizada")
    former = _archive(rt, pid, REVISION_FIRST)["card"]["revision"]
    assert former == REVISION_FIRST + 1

    anonymised = _erase_project(rt, pid, former, "anonymise")
    assert anonymised["answer_kind"] == "project_erased", anonymised
    assert anonymised["erasure"] == "anonymise"
    assert anonymised["changed"] is True
    # A04-4: no revision after — only the erased form is read back.
    card = _card(rt, pid)
    assert _is_anonymised_form(card, pid)
    rows = _rows(rt, "project_rows", "room_rows", "audit_entry_rows")

    # A04-5: stating the former revision for a record without one → stale,
    # for a correction (stage 5 before 6's archived/anonymised) ...
    corrected = _correct(rt, pid, former, "Casa otra vez")
    assert _refusal(corrected) == STALE
    # ... and for an erasure, the confirmation step passed by the fixture.
    re_erased = _erase_project(rt, pid, former, "anonymise")
    assert _refusal(re_erased) == STALE
    # Deleting whole with the former revision is stale too: stage (5) comes
    # before A05 rule 4's `anonymised` refusal (A04 rule 3).
    deleted_stale = _erase_project(rt, pid, former, "delete_whole")
    assert _refusal(deleted_stale) == STALE

    assert _card(rt, pid) == card
    assert _rows(rt, "project_rows", "room_rows", "audit_entry_rows") == rows

    # Control: stating none, anonymising again is accepted and changes
    # nothing (A05 rule 1; State 5 erase_project); deleting it whole is
    # refused at stage (6) `anonymised` (A05 rule 4).
    again = _erase_project(rt, pid, None, "anonymise")
    assert again["answer_kind"] == "project_erased", again
    assert again["changed"] is False
    assert _refusal(_erase_project(rt, pid, None, "delete_whole")) == (
        "refused",
        STAGE_LIFECYCLE,
        ["anonymised"],
    )
    assert _card(rt, pid) == card
    assert _rows(rt, "project_rows", "room_rows", "audit_entry_rows") == rows

    # A project deleted whole is not found: `not_found`, stage (3),
    # `unknown_project` (correct_project, read_project_card Errors).
    gone = _create_project(rt, "Casa borrada")
    gone_revision = _archive(rt, gone, REVISION_FIRST)["card"]["revision"]
    deleted = _erase_project(rt, gone, gone_revision, "delete_whole")
    assert deleted["answer_kind"] == "project_erased", deleted
    assert deleted["erasure"] == "delete_whole"
    assert deleted["changed"] is True
    not_found = ("not_found", STAGE_EXISTENCE, ["unknown_project"])
    assert _refusal(_correct(rt, gone, gone_revision, "Casa")) == not_found
    assert _refusal(rt.owner("read_project", target=gone)) == not_found


def test_change_moves_revision_and_last_changed(semantic_runtime):
    """[witness: verification:registry_a04_change_moves_revision_and_last_changed]

    A04 Required test 11: a correction that changes a project moves its
    revision by exactly one and sets its last-changed instant to the current
    instant; one that changes nothing leaves both. Shows A04-3, A04-6.
    """
    rt = semantic_runtime
    pid = _create_project(rt, "Casa v1")
    created = _card(rt, pid)
    # State 1 "Revisions and times": created at revision 1, last-changed at
    # the created instant.
    assert created["revision"] == REVISION_FIRST
    assert _instant(created["created_at"]) == START
    assert _instant(created["last_changed_at"]) == START

    rt.clock.advance(hours=3)
    rt.sign_in()  # past the 30 idle minutes: a new owner session (A13 rule 2)
    changed = _correct(rt, pid, REVISION_FIRST, "Casa v2")
    # A04-3: exactly one more, last-changed = now; created instant stays.
    assert changed["changed"] is True
    for shown in (changed["card"], _card(rt, pid)):
        assert shown["revision"] == REVISION_FIRST + 1
        assert _instant(shown["last_changed_at"]) == START + timedelta(hours=3)
        assert _instant(shown["created_at"]) == START

    rt.clock.advance(hours=2)
    rt.sign_in()  # past the 30 idle minutes: a new owner session (A13 rule 2)
    second = _correct(rt, pid, REVISION_FIRST + 1, "Casa v3")
    # A second change moves it by one again, to the new now — the step is
    # one, not a jump, and the instant follows the clock.
    assert second["card"]["revision"] == REVISION_FIRST + 2
    assert _instant(second["card"]["last_changed_at"]) == START + timedelta(hours=5)
    settled = _card(rt, pid)

    rt.clock.advance(hours=1)
    rt.sign_in()  # past the 30 idle minutes: a new owner session (A13 rule 2)
    # A04-6: accepted, no change → revision and last-changed stay.
    equal = _correct(rt, pid, REVISION_FIRST + 2, "Casa v3")
    assert equal["changed"] is False
    assert equal["card"] == settled
    after = _card(rt, pid)
    assert after == settled
    assert after["revision"] == REVISION_FIRST + 2
    assert _instant(after["last_changed_at"]) == START + timedelta(hours=5)
