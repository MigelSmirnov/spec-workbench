"""Witness tests for accepted decision A03 (02_rules_records.md).

A correction replaces the editable facts as a whole: 'correct a project'
gives display name, alias, customer link and the object; 'correct a customer'
gives kind, contact data and fiscal data. An optional fact a correction does
not give is cleared; the facts it does not edit — identity, status, marks, the
created instant, the request id — stay; a correction giving exactly the stored
facts changes nothing (revision, last-changed instant, no audit entry); a
customer newly named is checked for eligibility, the one already named is not.
Each witness test carries the name its Required test declares; Required test
3, untagged, has a test named by what it shows.

The Factory project `registry` supplies the ``semantic_runtime`` fixture
(``tests/semantic/RUNTIME_SURFACE.md``): a fresh instance per test, driven
over its two real listeners. Expected values come from State 2 (A01, A02, A03,
A04, A05), State 5 (`50_public_apis_3_records.md`: `projects.create_project`,
`projects.correct_project`, `projects.read_project_card`,
`customers.record_customer`, `customers.correct_customer`,
`customers.mark_customer`, `customers.read_customer`,
`customers.list_customers`, `audit_log.read_audit_entries`; "Closed set of
refusal codes" in `50_public_apis_0_conventions.md`) and State 6 (answer
models `ProjectCardAnswer`, `CustomerAnswer`, `CustomerListAnswer`,
`AuditViewAnswer`, `RefusedAnswer`; `GivenProjectFacts`,
`GivenCustomerFacts`, `ProjectCard`, `CustomerDetail`; constants of
`70_data_provider_closure.json`).

Fixture surface used here:

- ``owner(action, target=None, stated_version=None, **values)`` -> answer,
  for `create_project`, `correct_project`, `read_project`,
  `record_customer`, `correct_customer`, `mark_customer`, `read_customer`,
  `list_customers`, `read_audit`; ``values`` are `OwnerValues` fields:
  ``request_id``, ``project`` (a `GivenProjectFacts` dict), ``customer`` (a
  `GivenCustomerFacts` dict), ``transition``;
- ``new_request_id()``; ``clock.advance(hours=…)``, each followed by
  ``sign_in()``: an hour leaves the held owner session past its 30 idle
  minutes (A13 rule 2; RUNTIME_SURFACE.md "The owner's session");
- ``store_rows(table)`` for the audit table where a refusal must write none.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

# Default start instant of the fixture (RUNTIME_SURFACE.md, "Time").
START = datetime(2026, 1, 5, 9, 0, tzinfo=timezone.utc)

# Stage numbers of A04 rule 6, as 70_data_provider_closure.json gives them:
# REFUSAL_STAGE_LIFECYCLE = 6.
STAGE_LIFECYCLE = 6
# REVISION_FIRST = 1 (70_data_provider_closure.json; State 1 "Revisions and
# times": an ordinal starting at 1).
REVISION_FIRST = 1

ADDRESS = "Calle Mayor 1, Valencia"


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


def _project_facts(
    display_name="Casa Lopez",
    alias=None,
    customer_ref=None,
    address=ADDRESS,
    object_kind=None,
    floor_area=None,
    rooms_count=None,
    floor=None,
):
    # State 6 GivenProjectFacts: every field a text or absent.
    return {
        "display_name": display_name,
        "alias": alias,
        "customer_ref": customer_ref,
        "address": address,
        "object_kind": object_kind,
        "floor_area": floor_area,
        "rooms_count": rooms_count,
        "floor": floor,
    }


def _customer_facts(
    name="Ana Lopez",
    customer_kind="person",
    phone=None,
    email=None,
    language=None,
    tax_id=None,
    legal_name=None,
):
    # State 6 GivenCustomerFacts.
    return {
        "name": name,
        "customer_kind": customer_kind,
        "phone": phone,
        "email": email,
        "language": language,
        "tax_id": tax_id,
        "legal_name": legal_name,
    }


def _create_project(rt, request_id=None, **facts):
    answer = rt.owner(
        "create_project",
        request_id=request_id or rt.new_request_id(),
        project=_project_facts(**facts),
    )
    assert answer["answer_kind"] == "project_card", answer
    return answer["card"]


def _correct_project(rt, project_id, revision, **facts):
    return rt.owner(
        "correct_project",
        target=project_id,
        stated_version=revision,
        project=_project_facts(**facts),
    )


def _card(rt, project_id):
    answer = rt.owner("read_project", target=project_id)
    assert answer["answer_kind"] == "project_card", answer
    return answer["card"]


def _record_customer(rt, request_id=None, **facts):
    answer = rt.owner(
        "record_customer",
        request_id=request_id or rt.new_request_id(),
        customer=_customer_facts(**facts),
    )
    assert answer["answer_kind"] == "customer", answer
    return answer["customer"]


def _customer(rt, customer_ref):
    answer = rt.owner("read_customer", target=customer_ref)
    assert answer["answer_kind"] == "customer", answer
    return answer["customer"]


def _restrict(rt, customer_ref):
    current = _customer(rt, customer_ref)
    answer = rt.owner(
        "mark_customer",
        target=customer_ref,
        stated_version=current["revision"],
        transition="restrict",
    )
    assert answer["answer_kind"] == "customer", answer
    assert answer["customer"]["restricted_at"] is not None
    return answer["customer"]


def _audit_actions(rt, action):
    """Audit entries of one AuditAction, in sequence order (A06 rule 6)."""
    answer = rt.owner("read_audit")
    assert answer["answer_kind"] == "audit_view", answer
    return [e for e in answer["entries"] if e["action"] == action]


def test_correction_without_alias_clears_it(semantic_runtime):
    """[witness: verification:registry_a03_correction_without_alias_clears_it]

    A03 Required test 1: a project correction without an alias clears the
    alias. Shows A03-1.
    """
    rt = semantic_runtime
    # A03 rule 1: the customer link is an editable fact of the project; the
    # correction below links this Customer, newly named, so editable(p) = f is
    # shown on the link too, not only on the alias.
    named = _record_customer(rt, name="Ana Lopez")
    created = _create_project(
        rt,
        display_name="Casa Lopez",
        alias="LOPEZ-1",
        object_kind="apartment",
        floor_area="85.5",
        rooms_count="3",
        floor="2",
    )
    pid = created["project_id"]
    assert created["alias"] == "LOPEZ-1"
    assert created["revision"] == REVISION_FIRST

    # Control: a correction that gives the alias keeps it, while the display
    # name it gives is applied — so the clearing below is the alias not being
    # given, not every correction losing the alias.
    kept = _correct_project(
        rt,
        pid,
        REVISION_FIRST,
        display_name="Casa Lopez Garcia",
        alias="LOPEZ-1",
        object_kind="apartment",
        floor_area="85.5",
        rooms_count="3",
        floor="2",
    )
    assert kept["answer_kind"] == "project_card", kept
    assert kept["changed"] is True
    assert kept["card"]["alias"] == "LOPEZ-1"
    assert kept["card"]["display_name"] == "Casa Lopez Garcia"
    assert kept["card"]["customer_ref"] is None  # not given, so none

    rt.clock.advance(hours=1)
    rt.sign_in()  # past the 30 idle minutes: a new owner session (A13 rule 2)
    # A03 rule 1: the correction gives every editable fact; rule 2: the alias
    # and the object's kind and floor it does not give are cleared.
    cleared = _correct_project(
        rt,
        pid,
        REVISION_FIRST + 1,
        display_name="Casa Lopez Garcia",
        alias=None,
        customer_ref=named["customer_ref"],
        object_kind=None,
        floor_area="85.5",
        rooms_count="3",
        floor=None,
    )
    assert cleared["answer_kind"] == "project_card", cleared
    assert cleared["changed"] is True

    card = _card(rt, pid)  # read back, not only the answer
    for shown in (cleared["card"], card):
        # A03-1: editable(p) = f — alias cleared, the facts given kept.
        assert shown["alias"] is None
        assert shown["display_name"] == "Casa Lopez Garcia"
        assert shown["customer_ref"] == named["customer_ref"]
        obj = shown["object_facts"]
        assert obj["address"] == ADDRESS
        assert obj["object_kind"] is None
        assert obj["floor"] is None
        assert Decimal(obj["floor_area_m2"]) == Decimal("85.5")
        assert obj["rooms_count"] == 3
        # A03 rule 3 / A03-2: identity, status and created instant stay.
        assert shown["project_id"] == pid
        assert shown["status"] == "active"
        assert _instant(shown["created_at"]) == START
        # A03 rule 3 → A04-3: the change moved the revision once, at now.
        assert shown["revision"] == REVISION_FIRST + 2
        assert _instant(shown["last_changed_at"]) == START + timedelta(hours=1)


def test_equal_correction_keeps_revision(semantic_runtime):
    """[witness: verification:registry_a03_equal_correction_keeps_revision]

    A03 Required test 2: a correction equal to the stored card leaves the
    revision where it was. Shows A03-3.
    """
    rt = semantic_runtime
    facts = dict(
        display_name="Casa Ruiz",
        alias="RUIZ",
        object_kind="house",
        floor_area="120",
        rooms_count="5",
        floor="0",
    )
    created = _create_project(rt, **facts)
    pid = created["project_id"]
    before = _card(rt, pid)
    corrected_entries = len(_audit_actions(rt, "project_corrected"))

    rt.clock.advance(hours=2)
    rt.sign_in()  # past the 30 idle minutes: a new owner session (A13 rule 2)
    # A03 rule 4: exactly the stored facts — accepted, nothing changes.
    equal = _correct_project(rt, pid, REVISION_FIRST, **facts)
    assert equal["answer_kind"] == "project_card", equal
    # State 5 Conventions "Repeats": an accepted correction without a change
    # answers changed false.
    assert equal["changed"] is False
    after = _card(rt, pid)
    for shown in (equal["card"], after):
        # A03-3: f = editable(p before) => p = p before.
        assert shown == before
        assert shown["revision"] == REVISION_FIRST
        assert _instant(shown["last_changed_at"]) == START
    # A03 rule 4 / A05 rule 2: no audit entry is written.
    assert len(_audit_actions(rt, "project_corrected")) == corrected_entries

    # Control: a correction that differs in one fact is a change, so the
    # result above comes from the equality, not from corrections never
    # moving the revision.
    changed = _correct_project(rt, pid, REVISION_FIRST, **dict(facts, floor="1"))
    assert changed["answer_kind"] == "project_card", changed
    assert changed["changed"] is True
    assert changed["card"]["revision"] == REVISION_FIRST + 1
    assert _instant(changed["card"]["last_changed_at"]) == START + timedelta(hours=2)
    assert len(_audit_actions(rt, "project_corrected")) == corrected_entries + 1


def test_keeping_restricted_customer_accepted_newly_naming_refused(semantic_runtime):
    """A03 Required test 3 (untagged): a correction keeping a customer that has
    since been restricted is accepted; one newly naming a restricted customer
    is refused.
    """
    rt = semantic_runtime
    named = _record_customer(rt, name="Ana Lopez")
    other = _record_customer(rt, name="Luis Perez")
    created = _create_project(rt, customer_ref=named["customer_ref"])
    pid = created["project_id"]
    assert created["customer_ref"] == named["customer_ref"]

    _restrict(rt, named["customer_ref"])
    _restrict(rt, other["customer_ref"])

    # A03 rule 5: keeping the customer already named is not newly naming it —
    # accepted although that customer is now restricted.
    kept = _correct_project(
        rt,
        pid,
        REVISION_FIRST,
        display_name="Casa Lopez II",
        customer_ref=named["customer_ref"],
    )
    assert kept["answer_kind"] == "project_card", kept
    assert kept["changed"] is True
    assert kept["card"]["customer_ref"] == named["customer_ref"]
    assert kept["card"]["display_name"] == "Casa Lopez II"

    before = _card(rt, pid)
    audit_before = rt.store_rows("audit_entry_rows")
    # A03 rule 5: newly naming a restricted customer is refused — State 5
    # correct_project Errors and the closed set: `refused`, stage (6),
    # `customer_restricted`.
    refused = _correct_project(
        rt,
        pid,
        REVISION_FIRST + 1,
        display_name="Casa Lopez II",
        customer_ref=other["customer_ref"],
    )
    assert _refusal(refused) == ("refused", STAGE_LIFECYCLE, ["customer_restricted"])
    # A04 rule 2 / State 5 "Stages": a refusal changes nothing, writes no entry.
    assert _card(rt, pid) == before
    assert rt.store_rows("audit_entry_rows") == audit_before

    # Control: newly naming an eligible customer is accepted, so the refusal
    # above is the restriction, not every change of the customer link.
    eligible = _record_customer(rt, name="Marta Gil")
    moved = _correct_project(
        rt,
        pid,
        REVISION_FIRST + 1,
        display_name="Casa Lopez II",
        customer_ref=eligible["customer_ref"],
    )
    assert moved["answer_kind"] == "project_card", moved
    assert moved["card"]["customer_ref"] == eligible["customer_ref"]


def test_customer_correction_replaces_editable_facts(semantic_runtime):
    """[witness: verification:registry_a03_customer_correction_replaces_editable_facts]

    A03 Required test 4: a Customer correction replaces every editable fact,
    clearing an optional one it does not give; its identity, created
    instant, request id and marks stay; one giving exactly the stored facts
    leaves the revision. Shows A03-1, A03-2, A03-3.
    """
    rt = semantic_runtime
    request_id = rt.new_request_id()
    recorded = _record_customer(
        rt,
        request_id=request_id,
        name="Obras Levante",
        customer_kind="company",
        phone="+34 600 000 001",
        email="obras@example.test",
        language="es",
        tax_id="B12345678",
        legal_name="Obras Levante S.L.",
    )
    ref = recorded["customer_ref"]
    assert recorded["revision"] == REVISION_FIRST

    # A mark the correction must keep (A03 rule 3: marks).
    rt.clock.advance(hours=1)
    rt.sign_in()  # past the 30 idle minutes: a new owner session (A13 rule 2)
    restricted = _restrict(rt, ref)
    restricted_at = _instant(restricted["restricted_at"])
    assert restricted_at == START + timedelta(hours=1)
    revision = restricted["revision"]

    rt.clock.advance(hours=1)
    rt.sign_in()  # past the 30 idle minutes: a new owner session (A13 rule 2)
    corrected_facts = dict(
        name="Pedro Levante",
        customer_kind="person",
        phone="+34 600 000 002",
        email=None,
        language="ru",
        tax_id="12345678Z",
        legal_name=None,
    )
    corrected = rt.owner(
        "correct_customer",
        target=ref,
        stated_version=revision,
        customer=_customer_facts(**corrected_facts),
    )
    assert corrected["answer_kind"] == "customer", corrected
    assert corrected["changed"] is True

    after = _customer(rt, ref)
    for shown in (corrected["customer"], after):
        # A03-1: every editable fact replaced; e-mail and legal name, not
        # given, cleared (A03 rule 2).
        assert shown["name"] == "Pedro Levante"
        assert shown["customer_kind"] == "person"
        assert shown["phone"] == "+34 600 000 002"
        assert shown["email"] is None
        assert shown["language"] == "ru"
        assert shown["tax_id"] == "12345678Z"
        assert shown["legal_name"] is None
        # A03-2: identity, created instant and marks stay.
        assert shown["customer_ref"] == ref
        assert _instant(shown["created_at"]) == START
        assert _instant(shown["restricted_at"]) == restricted_at
        assert shown["relationship_ended_on"] is None
        # A03 rule 3 → A04-3: one move of the pair, at now.
        assert shown["revision"] == revision + 1
        assert _instant(shown["last_changed_at"]) == START + timedelta(hours=2)

    # A03-2, the request id stays: it is never answered (A01 rule 9), so it
    # is shown by its effect. A01 rule 4: a create carrying the request id
    # with facts equal to the record's current ones is a repeat answering
    # that record; had the correction removed the request id, the same create
    # would make a second Customer (A01 rule 8).
    repeat = rt.owner(
        "record_customer",
        request_id=request_id,
        customer=_customer_facts(**corrected_facts),
    )
    assert repeat["answer_kind"] == "customer", repeat
    assert repeat["changed"] is False
    assert repeat["customer"]["customer_ref"] == ref
    listed = rt.owner("list_customers")
    assert listed["answer_kind"] == "customer_list", listed
    assert [c["customer_ref"] for c in listed["items"]] == [ref]

    # A03-3: exactly the stored facts change nothing — revision and
    # last-changed instant stay, `changed` false (A03 rule 4).
    rt.clock.advance(hours=1)
    rt.sign_in()  # past the 30 idle minutes: a new owner session (A13 rule 2)
    equal = rt.owner(
        "correct_customer",
        target=ref,
        stated_version=revision + 1,
        customer=_customer_facts(**corrected_facts),
    )
    assert equal["answer_kind"] == "customer", equal
    assert equal["changed"] is False
    assert equal["customer"] == after
    assert _customer(rt, ref) == after

    # Control for A03-3: a correction differing from the stored facts in one
    # optional fact only (the e-mail, cleared before) is a change — the
    # equality above is over every editable fact, not over the name alone.
    one_more = rt.owner(
        "correct_customer",
        target=ref,
        stated_version=revision + 1,
        customer=_customer_facts(**dict(corrected_facts, email="p@example.test")),
    )
    assert one_more["answer_kind"] == "customer", one_more
    assert one_more["changed"] is True
    assert one_more["customer"]["email"] == "p@example.test"
    assert one_more["customer"]["revision"] == revision + 2
    assert _instant(one_more["customer"]["last_changed_at"]) == START + timedelta(
        hours=3
    )
