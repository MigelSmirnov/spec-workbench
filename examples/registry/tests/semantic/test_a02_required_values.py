"""Witness tests for accepted decision A02 (02_rules_records.md).

A required value is present and not blank. A required value given empty or
as white space only is missing and the action is refused as for a missing
value (rule 1); a present value is kept exactly as written (rule 2); an
optional value given blank is absent (rule 3); a present value outside the form
State 1 declares is refused at stage (4) of A04 rule 6, every such value named
— an alias over ``ALIAS_MAX_CHARACTERS`` (40) code points, an object kind
outside the vocabulary, a floor area not greater than
``OBJECT_FLOOR_AREA_MIN_EXCLUSIVE`` (0), a number of rooms that is not a whole
number of at least ``OBJECT_ROOMS_MIN`` (1), a floor that is not a whole number
(rule 4). Each test carries the witness name its Required test declares.

The Factory project `registry` supplies the ``semantic_runtime`` fixture
(``RUNTIME_SURFACE.md``). Each test gets a fresh, empty instance. Expected
values come from State 2 (A02, A04 rule 6), State 5 (``create_project``,
``correct_project``, ``record_customer``, ``correct_customer``, ``add_room``,
``request_project_access``, ``list_sessions``, and "Closed set of refusal
codes" in ``50_public_apis_0_conventions.md``), State 6 (the models of
``60_model_closure_*.json``) and the data provider's constants
(``70_data_provider_closure.json``).

Surface used here:

- ``owner(action, target=None, stated_version=None, **values)`` with
  ``create_project``, ``correct_project``, ``read_project``,
  ``list_projects``, ``record_customer``, ``correct_customer``,
  ``read_customer``, ``list_customers``, ``add_room``, ``list_sessions``;
- ``service("cabinet_kernel", ...)`` with ``register_agent_session`` and
  ``request_project_access``;
- ``new_request_id()``, ``store_rows(table)``.
"""

STAGE_VALUES = 4  # REFUSAL_STAGE_VALUES; State 5 `invalid_request` is stage (4)

ALIAS_MAX_CHARACTERS = 40  # data provider constant ALIAS_MAX_CHARACTERS

KERNEL = "cabinet_kernel"

TABLES = (
    "project_rows",
    "room_rows",
    "customer_rows",
    "pointer_rows",
    "agent_session_rows",
    "audit_entry_rows",
    "audit_sequence_rows",
)

BLANKS = ("", "   ", " \t ")  # A02 rule 1: empty, or white space only


# --- helpers -------------------------------------------------------------


def _project_facts(display_name="Casa Norte", address="Calle Mayor 1, Valencia", **more):
    """State 6 GivenProjectFacts; characteristics are given as text."""
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


def _inputs(**given):
    """State 6 ServiceInputs."""
    inputs = dict.fromkeys(
        ("project_id", "customer_ref", "artifact_type", "pointer_id", "list_choice",
         "room_name", "request_id", "pointer", "request_text")
    )
    inputs.update(given)
    return inputs


def _store(rt):
    return {table: rt.store_rows(table) for table in TABLES}


def _names(failure):
    """The names along a failure's path (State 6 PathElement.name)."""
    return [element.get("name") for element in failure["path"]]


def _invalid(answer, *expected):
    """`invalid_request` at stage (4) naming exactly `expected`, each a pair
    (kind, field), in the answer's order (State 5 'Stages')."""
    assert answer["answer_kind"] == "refused", answer
    assert answer["code"] == "invalid_request", answer
    assert answer["stage"] == STAGE_VALUES, answer
    failures = answer["failures"]
    assert len(failures) == len(expected), answer
    for failure, (kind, field) in zip(failures, expected):
        assert failure["kind"] == kind, answer
        assert field in _names(failure), answer


def _card(answer):
    assert answer["answer_kind"] == "project_card", answer
    return answer["card"]


def _create(rt, **facts):
    return rt.owner("create_project", request_id=rt.new_request_id(), project=_project_facts(**facts))


def _read_card(rt, project_id):
    return _card(rt.owner("read_project", target=project_id))


def _project_ids(rt):
    answer = rt.owner("list_projects", list_choice="with_archived")
    assert answer["answer_kind"] == "project_list", answer
    return [item["project_id"] for item in answer["items"]]


def _customer(answer):
    assert answer["answer_kind"] == "customer", answer
    return answer["customer"]


def _session(rt, session_id):
    answer = rt.owner("list_sessions")
    assert answer["answer_kind"] == "session_list", answer
    [item] = [i for i in answer["items"] if i["access"]["session_id"] == session_id]
    return item


# --- Required test 1 -----------------------------------------------------


def test_blank_display_name_refused(semantic_runtime):
    """[witness: verification:registry_a02_blank_display_name_refused]

    A02 Required test 1: a project with a display name of three spaces is
    refused. Shows A02-1, A02-2.
    """
    rt = semantic_runtime
    before = _store(rt)

    # A02 rule 1; State 5 create_project: display name required,
    # `invalid_request` (`missing_value`) at stage (4).
    _invalid(_create(rt, display_name="   "), ("missing_value", "display_name"))
    for blank in BLANKS:
        _invalid(_create(rt, display_name=blank), ("missing_value", "display_name"))
    # Every failing value of the stage is named (A04 rule 6): the address,
    # also required (R0-45), blank beside it.
    answer = _create(rt, display_name="   ", address=" ")
    assert answer["answer_kind"] == "refused", answer
    assert answer["code"] == "invalid_request" and answer["stage"] == STAGE_VALUES, answer
    named = sorted(
        field
        for failure in answer["failures"]
        for field in ("display_name", "address")
        if failure["kind"] == "missing_value" and field in _names(failure)
    )
    assert named == ["address", "display_name"], answer
    assert len(answer["failures"]) == 2, answer

    # A02-2: nothing blank reached the store.
    assert _store(rt) == before
    assert _project_ids(rt) == []

    # Control: a display name present is accepted.
    card = _card(_create(rt, display_name="Casa Norte"))
    assert card["display_name"] == "Casa Norte"

    # The same holds for a correction (A02 rule 4: "every action that gives
    # the value"): blank refused, the card unchanged.
    before = _store(rt)
    _invalid(
        rt.owner("correct_project", target=card["project_id"], stated_version=1,
                 project=_project_facts(display_name="   ")),
        ("missing_value", "display_name"),
    )
    assert _store(rt) == before
    assert _read_card(rt, card["project_id"]) == card


# --- Required test 2 -----------------------------------------------------


def test_room_name_spaces_kept_as_written(semantic_runtime):
    """[witness: verification:registry_a02_room_name_spaces_kept_as_written]

    A02 Required test 2: a room name ``"  Cocina "`` is stored with its
    spaces. Shows A02-3.
    """
    rt = semantic_runtime
    project_id = _card(_create(rt))["project_id"]

    padded = rt.owner("add_room", target=project_id, room_name="  Cocina ", request_id=rt.new_request_id())
    assert padded["answer_kind"] == "room", padded
    # A02 rule 2: kept exactly as written; Registry trims nothing (R0-68).
    assert padded["room"]["name"] == "  Cocina "

    plain = rt.owner("add_room", target=project_id, room_name="Cocina", request_id=rt.new_request_id())
    assert plain["room"]["name"] == "Cocina"

    # Read back: two rooms with their names as given, by name (A06 rule 2;
    # " " sorts before "C" by code point).
    rooms = _read_card(rt, project_id)["rooms"]
    assert [room["name"] for room in rooms] == ["  Cocina ", "Cocina"]
    assert rooms[0]["room_id"] == padded["room"]["room_id"]


# --- Required test 3 -----------------------------------------------------


def test_empty_optional_email_clears_it(semantic_runtime):
    """[witness: verification:registry_a02_empty_optional_email_clears_it]

    A02 Required test 3: a Customer correction giving an e-mail of ``""``
    clears the e-mail. Shows A02-1.
    """
    rt = semantic_runtime
    recorded = _customer(rt.owner(
        "record_customer", request_id=rt.new_request_id(),
        customer=_customer_facts(email="ana@example.es"),
    ))
    ref = recorded["customer_ref"]
    assert recorded["email"] == "ana@example.es"
    revision = recorded["revision"]

    def correct(email):
        nonlocal revision
        answer = rt.owner("correct_customer", target=ref, stated_version=revision,
                          customer=_customer_facts(email=email))
        customer = _customer(answer)
        revision = customer["revision"]
        return answer, customer

    # A02 rule 3: an optional value given blank is absent, so the correction
    # (A03: replaces the editable facts as a whole) clears it.
    answer, customer = correct("")
    assert answer["changed"] is True, answer
    assert customer["email"] is None
    assert _customer(rt.owner("read_customer", target=ref))["email"] is None

    # Control: an e-mail given is stored as given.
    _, customer = correct("eva@example.es")
    assert customer["email"] == "eva@example.es"

    # White space only is blank too (A02 rule 3).
    _, customer = correct("  \t ")
    assert customer["email"] is None
    read = _customer(rt.owner("read_customer", target=ref))
    assert read["email"] is None
    assert read["name"] == "Ana Ruiz"


# --- Required test 4 -----------------------------------------------------


def test_alias_over_forty_code_points_refused(semantic_runtime):
    """[witness: verification:registry_a02_alias_over_forty_code_points_refused]

    A02 Required test 4: an alias of 40 characters is stored; one of 41 is
    refused and nothing changes. Shows A02-5.
    """
    rt = semantic_runtime
    # A02 rule 4: counted as Unicode code points (ALIAS_MAX_CHARACTERS = 40).
    # 40 astral code points: 80 UTF-16 units, 160 UTF-8 bytes.
    astral_40 = "\U0001F3E0" * ALIAS_MAX_CHARACTERS
    # 40 code points that are 20 user-perceived characters, not in NFC.
    combining_40 = "é" * (ALIAS_MAX_CHARACTERS // 2)
    # 41 code points that are only 21 user-perceived characters (and 21 after
    # NFC): a grapheme or normalising count would let it through.
    combining_41 = "é" * (ALIAS_MAX_CHARACTERS // 2) + "x"
    plain_41 = "a" * (ALIAS_MAX_CHARACTERS + 1)
    assert len(astral_40) == len(combining_40) == 40
    assert len(combining_41) == len(plain_41) == 41

    stored = {}
    for alias in (astral_40, combining_40, "a" * ALIAS_MAX_CHARACTERS):
        card = _card(_create(rt, display_name=f"Casa {len(stored)}", alias=alias))
        # A02 rule 2 / A02-3: stored exactly as written (no normalisation).
        assert card["alias"] == alias
        assert _read_card(rt, card["project_id"])["alias"] == alias
        stored[card["project_id"]] = card

    before = _store(rt)
    for alias in (plain_41, combining_41):
        # State 5: `invalid_request` (`outside_form`) at stage (4), naming the
        # alias.
        _invalid(_create(rt, display_name="Casa larga", alias=alias), ("outside_form", "alias"))
    assert _store(rt) == before
    assert sorted(_project_ids(rt)) == sorted(stored)

    # The same check holds for a correction (A02 rule 4): 41 refused and the
    # card unchanged; 40 accepted.
    project_id, card = next(iter(stored.items()))
    before = _store(rt)
    _invalid(
        rt.owner("correct_project", target=project_id, stated_version=card["revision"],
                 project=_project_facts(display_name=card["display_name"], alias=combining_41)),
        ("outside_form", "alias"),
    )
    assert _store(rt) == before
    assert _read_card(rt, project_id) == card
    corrected = _card(rt.owner(
        "correct_project", target=project_id, stated_version=card["revision"],
        project=_project_facts(display_name=card["display_name"], alias="b" * ALIAS_MAX_CHARACTERS),
    ))
    assert corrected["alias"] == "b" * ALIAS_MAX_CHARACTERS


# --- Required test 5 -----------------------------------------------------


def test_out_of_form_values_all_named(semantic_runtime):
    """[witness: verification:registry_a02_out_of_form_values_all_named]

    A02 Required test 5: a project created with kind ``villa``, or with a
    floor area of 0, is refused naming both values; one created with no kind
    and no characteristic is accepted. Shows A02-4.
    """
    rt = semantic_runtime
    before = _store(rt)

    # Each alone.
    _invalid(_create(rt, object_kind="villa"), ("outside_closed_list", "object_kind"))
    _invalid(_create(rt, floor_area="0"), ("outside_form", "floor_area"))
    # Both at once: every failure of stage (4) named (A02 rule 4, A04 rule 6),
    # ordered by kind in the order create_project's Errors list them —
    # `outside_closed_list` before `outside_form` (State 5 'Stages').
    _invalid(
        _create(rt, object_kind="villa", floor_area="0"),
        ("outside_closed_list", "object_kind"),
        ("outside_form", "floor_area"),
    )
    assert _store(rt) == before
    assert _project_ids(rt) == []

    # Control: no kind and no characteristic is accepted (A02 rule 4: an
    # absent object kind or characteristic is never refused).
    card = _card(_create(rt))
    assert card["object_facts"] == {
        "address": "Calle Mayor 1, Valencia",
        "object_kind": None,
        "floor_area_m2": None,
        "rooms_count": None,
        "floor": None,
    }
    # Control: a declared kind and a positive area are accepted (State 6
    # ObjectKind; a Decimal answered as its text).
    house = _card(_create(rt, display_name="Casa Sur", object_kind="house", floor_area="85.5"))
    assert house["object_facts"]["object_kind"] == "house"
    assert house["object_facts"]["floor_area_m2"] == "85.5"


# --- Required test 6 -----------------------------------------------------


def test_object_characteristic_bounds_checked(semantic_runtime):
    """[witness: verification:registry_a02_object_characteristic_bounds_checked]

    A02 Required test 6: a number of rooms of 0 and one of 2.5 are each
    refused as out of form; 1 and 7 are stored. A floor of -1 is stored; 1.5
    is refused. A floor area of 0.01 is stored as given; one of 0 or -3 is
    refused; a project with no characteristic at all is stored without one.
    Shows A02-3, A02-4.
    """
    rt = semantic_runtime
    before = _store(rt)
    # A02 rule 4; State 5: `outside_form` — rooms not a whole number of at
    # least OBJECT_ROOMS_MIN (1), a floor not a whole number, an area not
    # greater than OBJECT_FLOOR_AREA_MIN_EXCLUSIVE (0).
    for rooms in ("0", "2.5"):
        _invalid(_create(rt, rooms_count=rooms), ("outside_form", "rooms_count"))
    _invalid(_create(rt, floor="1.5"), ("outside_form", "floor"))
    for area in ("0", "-3"):
        _invalid(_create(rt, floor_area=area), ("outside_form", "floor_area"))
    assert _store(rt) == before
    assert _project_ids(rt) == []

    def stored(**facts):
        card = _card(_create(rt, display_name=f"Casa {facts}", **facts))
        assert _read_card(rt, card["project_id"])["object_facts"] == card["object_facts"]
        return card["object_facts"]

    # Wire form (RUNTIME_SURFACE.md): an int as a number, a Decimal as its
    # text. A02 rule 2: stored as given.
    assert stored(rooms_count="1")["rooms_count"] == 1
    assert stored(rooms_count="7")["rooms_count"] == 7
    assert stored(floor="-1")["floor"] == -1
    assert stored(floor_area="0.01")["floor_area_m2"] == "0.01"
    # As given, its trailing zero included: a float or a normalised Decimal
    # would answer "12.5" (A02 rule 2; State 6 Object.floor_area_m2: Decimal).
    assert stored(floor_area="12.50")["floor_area_m2"] == "12.50"
    bare = stored()
    assert (bare["object_kind"], bare["floor_area_m2"], bare["rooms_count"], bare["floor"]) == (
        None, None, None, None,
    )
    # Six accepted, none refused.
    assert len(_project_ids(rt)) == 6


# --- Required test 7 -----------------------------------------------------


def test_required_texts_blank_refused_padded_kept(semantic_runtime):
    """[witness: verification:registry_a02_required_texts_blank_refused_padded_kept]

    A02 Required test 7: a Customer's name and an access request text with
    spaces around them are stored as written; a room name, a Customer's name
    and an access request text of spaces only are each refused and nothing
    changes. Shows A02-1, A02-2, A02-3.
    """
    rt = semantic_runtime
    session_id = "kernel-session-a02-texts"
    registered = rt.service(KERNEL, "register_agent_session", inputs=None, kernel_session=session_id)
    assert registered["answer_kind"] != "refused", registered
    project_id = _card(_create(rt))["project_id"]

    def request_access(text):
        return rt.service(KERNEL, "request_project_access",
                          inputs=_inputs(request_text=text), kernel_session=session_id)

    def record(name):
        return rt.owner("record_customer", request_id=rt.new_request_id(),
                        customer=_customer_facts(name=name))

    # Blank refused first, on an empty set of customers and no pending request.
    before = _store(rt)
    session_before = _session(rt, session_id)
    for blank in BLANKS:
        _invalid(
            rt.owner("add_room", target=project_id, room_name=blank, request_id=rt.new_request_id()),
            ("missing_value", "room_name"),
        )
        _invalid(record(blank), ("missing_value", "name"))
        # State 5 request_project_access: the text is required (A02),
        # `invalid_request` (`missing_value`).
        _invalid(request_access(blank), ("missing_value", "request_text"))
    assert _store(rt) == before
    assert _read_card(rt, project_id)["rooms"] == []
    assert rt.owner("list_customers")["items"] == []
    assert _session(rt, session_id) == session_before
    assert session_before["request_text"] is None
    assert session_before["access"]["request_pending"] is False

    # Padded values are kept exactly as written (A02 rule 2).
    customer = _customer(record("  Ana Ruiz "))
    assert customer["name"] == "  Ana Ruiz "
    assert _customer(rt.owner("read_customer", target=customer["customer_ref"]))["name"] == "  Ana Ruiz "

    pending = request_access("  necesito Casa Norte  ")
    assert pending["answer_kind"] == "request_pending", pending
    item = _session(rt, session_id)
    assert item["request_text"] == "  necesito Casa Norte  "
    assert item["access"]["request_pending"] is True
    # State 5 request_project_access: the access version moves by one.
    assert item["access"]["access_version"] == session_before["access"]["access_version"] + 1

    # A blank request after it is refused and leaves the pending one as it is.
    before = _store(rt)
    _invalid(request_access("  "), ("missing_value", "request_text"))
    _invalid(record("   "), ("missing_value", "name"))
    assert _store(rt) == before
    assert _session(rt, session_id) == item
