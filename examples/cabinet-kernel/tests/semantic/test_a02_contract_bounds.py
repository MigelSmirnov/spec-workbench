"""Witness tests for accepted decision A02 (02_rules_functions.md).

A contract version is issued only when its ports are well formed and every
resource bound is a positive integer not above the release ceiling of the same
name; a bound above its ceiling or omitted is refused, never clamped or
defaulted. Each test carries the witness name its Required test declares.

The Factory project supplies the ``semantic_runtime`` pytest fixture. It binds
these scenarios to the generated public operations of State 5 — named here by
their operation names, with arguments shaped as the State 6 models — without
changing the assertions below. Each test gets a fresh, empty kernel store.

Fixture surface used here:

- ``issue_contract_version(slot_id, purpose, inputs, outputs,
  resource_bounds=None)`` -> contract_version_id; ports are dicts with the
  fields of Port (M01); ``resource_bounds`` is a ResourceBoundsRequest dict
  sent as given, a field set to None omitted from the request; without it the
  fixture supplies bounds within the installation's ceilings; acts as agent
  ``author``;
- ``read_contract_version(contract_version_id)`` -> ContractVersion (M03);
- ``page_records(record_type, record_filter)`` -> RecordPageAnswer, to show
  that a refusal recorded nothing (no contract version, no slot).

A refusal is read by its code and, where A02 rule 2 makes the reason name a
field, by its reason.
"""

import pytest

NUMBER = '{"type":"integer"}'

# A20 rule 1, release v1
CEILINGS = {
    "wall_time_ms": 30000,
    "memory_bytes": 536870912,
    "output_bytes": 67108864,
    "process_count": 8,
}

BOUND_FIELDS = ("wall_time_ms", "memory_bytes", "output_bytes", "process_count")


def _port(name, direction, schema, disclosure_class=None):
    return {
        "name": name,
        "direction": direction,
        "value_schema": schema,
        "carriage": "value",
        "media_type": None,
        "cardinality": "one",
        "disclosure_class": disclosure_class,
    }


def _input(name="x", disclosure_class="open"):
    return _port(name, "input", NUMBER, disclosure_class)


def _output(name="y", disclosure_class=None):
    return _port(name, "output", NUMBER, disclosure_class)


def _issue(semantic_runtime, slot_id, inputs=None, outputs=None, resource_bounds=None):
    return semantic_runtime.issue_contract_version(
        slot_id,
        purpose=f"A02 witness: {slot_id}",
        inputs=[_input()] if inputs is None else inputs,
        outputs=[_output()] if outputs is None else outputs,
        resource_bounds=resource_bounds,
    )


def _contract_versions_of(semantic_runtime, slot_id):
    page = semantic_runtime.page_records(
        "contract_version",
        {"filter_kind": "equals", "field": "slot_id", "value": slot_id},
        page_size=200,
    )
    return list(page.records.contract_versions)


def _slot_ids(semantic_runtime):
    page = semantic_runtime.page_records("slot", None, page_size=200)
    return [s.slot_id for s in page.records.slots]


def _assert_nothing_recorded(semantic_runtime, slot_id):
    # State 5 Conventions: a refusal is decided before the operation's first
    # store change, so it writes nothing — no contract version and, for a new
    # slot name, no slot (the `issue_contract_version` change writes both).
    assert _contract_versions_of(semantic_runtime, slot_id) == []
    assert slot_id not in _slot_ids(semantic_runtime)


def _assert_names_only(reason, field):
    # A02 rule 2 / State 5: the refusal names the failing field; the other
    # bounds, which hold, are not named.
    assert field in reason
    for other in BOUND_FIELDS:
        if other != field:
            assert other not in reason


def _bounds(contract_version):
    bounds = contract_version.resource_bounds
    return {field: getattr(bounds, field) for field in BOUND_FIELDS}


def test_bound_at_ceiling_ok_over_refused(semantic_runtime):
    """[witness: verification:kernel_a02_bound_at_ceiling_ok_over_refused]

    A02 Required test 1: every bound exactly at its ceiling is accepted; one
    unit over is refused with the field named.
    """
    at_ceiling = _issue(
        semantic_runtime, "a02_at_ceiling", resource_bounds=dict(CEILINGS)
    )
    # A02 rule 1: a bound equal to its ceiling is within it, and kept as given.
    assert _bounds(semantic_runtime.read_contract_version(at_ceiling)) == CEILINGS

    for field in BOUND_FIELDS:
        slot_id = f"a02_over_{field}"
        over = dict(CEILINGS)
        over[field] = CEILINGS[field] + 1
        with pytest.raises(Exception) as exc:
            _issue(semantic_runtime, slot_id, resource_bounds=over)
        # A02 rule 2: refused, never clamped; the refusal names the field.
        assert exc.value.code == "refused"
        _assert_names_only(exc.value.reason, field)
        # Nothing was recorded: no contract version, clamped or otherwise.
        _assert_nothing_recorded(semantic_runtime, slot_id)


def test_absent_bound_refused(semantic_runtime):
    """[witness: verification:kernel_a02_absent_bound_refused]

    A02 Required test 2: a contract without `memory_bytes` is refused.
    """
    without_memory = dict(CEILINGS, memory_bytes=None)
    with pytest.raises(Exception) as exc:
        _issue(semantic_runtime, "a02_absent_bound", resource_bounds=without_memory)
    # A02 rule 2: an omitted bound is refused; the kernel supplies no default.
    assert exc.value.code == "refused"
    _assert_names_only(exc.value.reason, "memory_bytes")
    _assert_nothing_recorded(semantic_runtime, "a02_absent_bound")

    # Control: the same contract with `memory_bytes` given is issued, so the
    # refusal above came from the omission.
    with_memory = dict(CEILINGS, memory_bytes=CEILINGS["memory_bytes"])
    issued = _issue(semantic_runtime, "a02_absent_bound", resource_bounds=with_memory)
    assert _bounds(semantic_runtime.read_contract_version(issued)) == with_memory


def test_output_disclosure_class_refused(semantic_runtime):
    """[witness: verification:kernel_a02_output_disclosure_class_refused]

    A02 Required test 3: a contract whose output port declares a disclosure
    class is refused.
    """
    slot_id = "a02_output_class"
    with pytest.raises(Exception) as exc:
        _issue(semantic_runtime, slot_id, outputs=[_output("y", "open")])
    # A02 rule 1 (M01): no output port declares a disclosure class.
    assert exc.value.code == "refused"
    _assert_nothing_recorded(semantic_runtime, slot_id)

    # Control: the same contract with an output port without a class is issued.
    issued = _issue(semantic_runtime, slot_id, outputs=[_output("y", None)])
    (output,) = semantic_runtime.read_contract_version(issued).outputs
    assert output.disclosure_class is None


def test_zero_bound_refused(semantic_runtime):
    """[witness: verification:kernel_a02_zero_bound_refused]

    A02 Required test 5: a contract with any bound set to 0 is refused.
    """
    for field in BOUND_FIELDS:
        slot_id = f"a02_zero_{field}"
        zero = dict(CEILINGS)
        zero[field] = 0
        with pytest.raises(Exception) as exc:
            _issue(semantic_runtime, slot_id, resource_bounds=zero)
        # A02 rule 1: every bound is a positive integer.
        assert exc.value.code == "refused"
        _assert_names_only(exc.value.reason, field)
        _assert_nothing_recorded(semantic_runtime, slot_id)

    # Control: the smallest positive bound, 1 for every field, is issued, so
    # the refusals above came from the zero, not from a lower limit above it.
    ones = {field: 1 for field in BOUND_FIELDS}
    issued = _issue(semantic_runtime, "a02_one_bounds", resource_bounds=ones)
    assert _bounds(semantic_runtime.read_contract_version(issued)) == ones


def test_no_output_port_refused(semantic_runtime):
    """[witness: verification:kernel_a02_no_output_port_refused]

    A02 Required test 6: a contract with no output port is refused.
    """
    slot_id = "a02_no_output"
    with pytest.raises(Exception) as exc:
        _issue(semantic_runtime, slot_id, outputs=[])
    # A02 rule 1: there is at least one output port.
    assert exc.value.code == "refused"
    _assert_nothing_recorded(semantic_runtime, slot_id)

    # Control: the same contract with one output port is issued.
    issued = _issue(semantic_runtime, slot_id, outputs=[_output()])
    assert [p.name for p in semantic_runtime.read_contract_version(issued).outputs] == [
        "y"
    ]


def test_port_names_unique_per_direction(semantic_runtime):
    """[witness: verification:kernel_a02_port_names_unique_per_direction]

    A02 Required test 7: a contract with two input ports of the same name is
    refused.
    """
    slot_id = "a02_repeated_input"
    with pytest.raises(Exception) as exc:
        _issue(semantic_runtime, slot_id, inputs=[_input("x"), _input("x")])
    # A02 rule 1: every port name is unique within its direction.
    assert exc.value.code == "refused"
    _assert_nothing_recorded(semantic_runtime, slot_id)

    # Control: one name used once per direction is issued, so the refusal
    # above came from the repetition within the inputs, not from the name.
    issued = _issue(
        semantic_runtime, slot_id, inputs=[_input("x")], outputs=[_output("x")]
    )
    contract_version = semantic_runtime.read_contract_version(issued)
    assert [p.name for p in contract_version.inputs] == ["x"]
    assert [p.name for p in contract_version.outputs] == ["x"]
