"""Witness tests for accepted decision A01 (02_rules_functions.md).

Identity is computed by the kernel: a content record's identity is the SHA-256
of the RFC 8785 canonical JSON of its facts, order-free lists sorted; a caller
never supplies one; an equal submission returns the existing record and records
nothing; activations are identified by their store position; the purpose of a
slot or a flow is fixed when it is created. Each test carries the witness name
its Required test declares.

The Factory project supplies the ``semantic_runtime`` pytest fixture. It binds
these scenarios to the generated public operations of State 5 — named here by
their operation names, with arguments shaped as the State 6 models — without
changing the assertions below. Each test gets a fresh, empty kernel store.

Fixture surface used here:

- ``issue_contract_version(slot_id, purpose, inputs, outputs,
  resource_bounds=None)`` -> contract_version_id; ports are dicts with the
  fields of Port (M01); without ``resource_bounds`` the fixture supplies bounds
  within the installation's ceilings; acts as agent ``author``;
- ``read_contract_version(contract_version_id)`` -> ContractVersion (M03);
- ``read_slot(slot_id)`` -> SlotHistory;
- ``add_trial_case(contract_version_id, inputs, expected_outputs=None)`` ->
  ShownAddedTrialCase; values are RequestJsonValue dicts;
- ``submit_implementation(contract_version_id, code, actor=...)`` ->
  ShownSubmission; ``read_implementation(implementation_id)`` ->
  ShownImplementationRead (owner);
- ``roll_back_slot(slot_id, implementation_id)`` -> Activation (M09), as the
  owner;
- ``compose_flow_version(flow_id, purpose, inputs, outputs, nodes, edges,
  constants)`` -> ComposedFlowVersion; ``active_flow_version(flow_id)`` ->
  FlowAnswer;
- ``page_records(record_type, record_filter)`` -> RecordPageAnswer;
- capabilities: ``installation.set_agent_tokens`` and
  ``installation.agent_token`` (a second author agent), ``clock.set`` and
  ``clock.advance`` (the kernel clock), ``mcp_request`` (a request with a field
  no operation schema has).
"""

import hashlib
import json

import pytest

NUMBER = '{"type":"integer"}'
TEXT = '{"type":"string"}'

OWNER = {"kind": "owner", "agent_name": None}
AUTHOR = {"kind": "agent", "agent_name": "author"}
SECOND_AUTHOR = {"kind": "agent", "agent_name": "second_author"}

T1 = 1_900_000_000_000_000  # epoch_us
MINUTE_MS = 60_000

BOUNDS = {
    "wall_time_ms": 1000,
    "memory_bytes": 67108864,
    "output_bytes": 1048576,
    "process_count": 1,
}

DOUBLE = 'def run(inputs):\n    return {"y": inputs["x"] * 2}\n'
PLUS_TWO = 'def run(inputs):\n    return {"y": inputs["x"] + 2}\n'


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


def _function(semantic_runtime, slot_id, purpose=None, schema=NUMBER):
    """A function of one input `x` and one output `y`, both of `schema`."""
    return semantic_runtime.issue_contract_version(
        slot_id,
        purpose=purpose or f"A01 witness: {slot_id}",
        inputs=[_port("x", "input", schema, "open")],
        outputs=[_port("y", "output", schema)],
    )


def _json(port, json_text):
    return {"payload_kind": "json", "port": port, "json_text": json_text}


def _node(node_id, contract_version_id):
    return {
        "node_id": node_id,
        "kind": "function",
        "contract_version_id": contract_version_id,
        "binding_id": None,
        "map_over": None,
    }


def _equals(field, value):
    return {"filter_kind": "equals", "field": field, "value": value}


def _contract_versions_of(semantic_runtime, slot_id):
    page = semantic_runtime.page_records(
        "contract_version", _equals("slot_id", slot_id), page_size=200
    )
    return page.records.contract_versions


def _flow_versions_of(semantic_runtime, flow_id):
    page = semantic_runtime.page_records(
        "flow_version", _equals("flow_id", flow_id), page_size=200
    )
    return page.records.flow_versions


def _value(x):
    return getattr(x, "value", x)


def _actor(actor):
    return (_value(actor.kind), actor.agent_name)


def _jcs_sha256(facts):
    """SHA-256 hex of the RFC 8785 canonical JSON of `facts`.

    Every key and string of the facts below is ASCII and every number a small
    integer, so sorted keys, no whitespace and JSON string escaping give exactly
    the JCS bytes.
    """
    text = json.dumps(facts, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _contract_version_identity(slot_id, inputs, outputs, resource_bounds):
    # State 6 decision 14 and content_identity: the ContractVersionContent
    # object, every field keyed by name, subject_kind included, value_schema as
    # its canonical text; ports sorted by (direction, name) by code point.
    def by_direction_and_name(port):
        return (port["direction"], port["name"])

    return _jcs_sha256(
        {
            "subject_kind": "contract_version",
            "slot_id": slot_id,
            "inputs": sorted(inputs, key=by_direction_and_name),
            "outputs": sorted(outputs, key=by_direction_and_name),
            "resource_bounds": resource_bounds,
        }
    )


def test_equal_submission_returns_existing(semantic_runtime):
    """[witness: verification:kernel_a01_equal_submission_returns_existing]

    A01 Required test 1: the same implementation code submitted by two agents
    at different times is one implementation with the first submitter
    recorded.
    """
    installation = semantic_runtime.installation
    installation.set_agent_tokens(
        [
            {
                "agent_name": "author",
                "token": installation.agent_token("author"),
                "may_author": True,
            },
            {
                "agent_name": "helper",
                "token": installation.agent_token("helper"),
                "may_author": False,
            },
            {
                "agent_name": "second_author",
                # A16 rule 2: every token at least 43 characters.
                "token": "a01-second-author-token-" + "s" * 32,
                "may_author": True,
            },
        ]
    )
    contract = _function(semantic_runtime, "a01_equal_submission")

    semantic_runtime.clock.set(T1)
    first = semantic_runtime.submit_implementation(contract, DOUBLE, actor=AUTHOR)
    semantic_runtime.clock.advance(ms=MINUTE_MS)
    second = semantic_runtime.submit_implementation(
        contract, DOUBLE, actor=SECOND_AUTHOR
    )

    # A01 rule 4: the existing record is returned unchanged; its first author
    # and time stay.
    implementation_id = first.implementation.implementation_id
    assert second.implementation.implementation_id == implementation_id
    assert _actor(second.implementation.submitted_by) == ("agent", "author")
    assert second.implementation.submitted_at.epoch_us == T1

    stored = semantic_runtime.read_implementation(implementation_id, actor=OWNER)
    assert _actor(stored.implementation.submitted_by) == ("agent", "author")
    assert stored.implementation.submitted_at.epoch_us == T1

    # A01 rule 4: nothing new is recorded for it.
    page = semantic_runtime.page_records(
        "implementation", _equals("contract_version_id", contract), page_size=200
    )
    assert [i.implementation_id for i in page.records.implementations] == [
        implementation_id
    ]

    # Control: other code from the second agent at that later time is a new
    # implementation with that agent and time, so the result above comes from
    # the equal identity, not from by-fields or times the kernel never records.
    other = semantic_runtime.submit_implementation(
        contract, PLUS_TWO, actor=SECOND_AUTHOR
    )
    assert other.implementation.implementation_id != implementation_id
    assert _actor(other.implementation.submitted_by) == ("agent", "second_author")
    assert other.implementation.submitted_at.epoch_us == T1 + MINUTE_MS * 1000


def test_caller_supplied_identity_refused(semantic_runtime):
    """[witness: verification:kernel_a01_caller_supplied_identity_refused]

    A01 Required test 2: a request carrying its own `contract_version_id` is
    refused.
    """
    slot_id = "a01_supplied_identity"
    inputs = [_port("x", "input", NUMBER, "open")]
    outputs = [_port("y", "output", NUMBER)]
    request = {
        "slot_id": slot_id,
        "purpose": "A01 witness: supplied identity",
        "inputs": inputs,
        "outputs": outputs,
        "resource_bounds": dict(BOUNDS),
    }
    author_token = semantic_runtime.installation.agent_token("author")

    # The identity the kernel would compute itself: even the right one is not
    # accepted from the caller.
    supplied = dict(request)
    supplied["contract_version_id"] = _contract_version_identity(
        slot_id, inputs, outputs, BOUNDS
    )
    with pytest.raises(Exception) as exc:
        semantic_runtime.mcp_request(
            "issue_contract_version", supplied, token=author_token
        )
    # A01 rule 1: a request that supplies one of these identities is refused;
    # IssueContractVersionRequest has no such field, so it is an unknown field
    # (A16 rule 4), `invalid_request` in State 5's closed set.
    assert exc.value.code == "invalid_request"

    # Nothing was recorded: no contract version and no slot.
    assert list(_contract_versions_of(semantic_runtime, slot_id)) == []
    page = semantic_runtime.page_records("slot", None, page_size=200)
    assert [s.slot_id for s in page.records.slots] == []

    # Control: the same request without the identity is accepted, and the
    # kernel computes that same identity itself.
    answer = semantic_runtime.mcp_request(
        "issue_contract_version", request, token=author_token
    )
    assert answer.contract_version.contract_version_id == supplied[
        "contract_version_id"
    ]
    assert [
        c.contract_version_id for c in _contract_versions_of(semantic_runtime, slot_id)
    ] == [supplied["contract_version_id"]]


def test_equal_contract_not_made_current(semantic_runtime):
    """[witness: verification:kernel_a01_equal_contract_not_made_current]

    A01 Required test 3: re-issuing an older, equal contract version returns it
    and leaves the slot's current contract version unchanged.
    """
    slot_id = "a01_equal_contract"
    purpose = "A01 witness: equal contract"

    semantic_runtime.clock.set(T1)
    older = _function(semantic_runtime, slot_id, purpose, NUMBER)
    semantic_runtime.clock.advance(ms=MINUTE_MS)
    newer = _function(semantic_runtime, slot_id, purpose, TEXT)
    assert newer != older

    # Control: a new contract version does become the slot's current one, so
    # the check below is not passed by a slot that never moves.
    assert semantic_runtime.read_slot(slot_id).current_contract_version_id == newer

    semantic_runtime.clock.advance(ms=MINUTE_MS)
    again = _function(semantic_runtime, slot_id, purpose, NUMBER)

    # A01 rule 4: the existing record is returned; it does not become the
    # slot's current contract version again.
    assert again == older
    history = semantic_runtime.read_slot(slot_id)
    assert history.current_contract_version_id == newer
    assert [c.contract_version.contract_version_id for c in history.contract_versions] == [
        older,
        newer,
    ]

    # A01 rule 4: its first time stays, nothing new is recorded for it.
    assert semantic_runtime.read_contract_version(older).issued_at.epoch_us == T1
    assert [
        c.contract_version_id for c in _contract_versions_of(semantic_runtime, slot_id)
    ] == [newer, older]  # newest first (A16 rule 6)


def test_identity_covers_resource_bounds(semantic_runtime):
    """[witness: verification:kernel_a01_identity_covers_resource_bounds]

    A01 Required test 4: two contract versions differing only in one resource
    bound have different identities.
    """
    slot_id = "a01_bounds_identity"
    purpose = "A01 witness: bounds in identity"
    inputs = [_port("x", "input", NUMBER, "open")]
    outputs = [_port("y", "output", NUMBER)]

    first = semantic_runtime.issue_contract_version(
        slot_id, purpose, inputs, outputs, resource_bounds=dict(BOUNDS)
    )
    assert semantic_runtime.read_contract_version(first).resource_bounds.memory_bytes == (
        BOUNDS["memory_bytes"]
    )

    # A01 rule 1 with State 1 M03: every resource bound is a fact of the
    # identity, so each field is changed alone (doubled, still within the
    # release ceilings of A20 rule 1) — an identity that leaves out any one
    # bound makes that pair equal.
    identities = [first]
    for field in BOUNDS:
        changed = dict(BOUNDS)
        changed[field] = BOUNDS[field] * 2
        other = semantic_runtime.issue_contract_version(
            slot_id, purpose, inputs, outputs, resource_bounds=changed
        )
        assert other != first
        assert getattr(
            semantic_runtime.read_contract_version(other).resource_bounds, field
        ) == changed[field]
        identities.append(other)
    assert len(set(identities)) == len(BOUNDS) + 1

    # Control: the same content with the same bounds has the same identity, so
    # the difference above comes from the bound, not from a time or a random
    # part in the identity.
    repeated = semantic_runtime.issue_contract_version(
        slot_id, purpose, inputs, outputs, resource_bounds=dict(BOUNDS)
    )
    assert repeated == first


def test_slot_purpose_fixed_at_creation(semantic_runtime):
    """[witness: verification:kernel_a01_slot_purpose_fixed_at_creation]

    A01 Required test 5: a request naming an existing slot with a different
    purpose is refused.
    """
    slot_id = "a01_slot_purpose"
    purpose = "A01 witness: slot purpose"
    first = _function(semantic_runtime, slot_id, purpose, NUMBER)

    # New content, so only the purpose can refuse it.
    with pytest.raises(Exception) as exc:
        _function(semantic_runtime, slot_id, "A01 witness: another purpose", TEXT)
    # A01 rule 5: a different purpose for an existing slot is refused.
    assert exc.value.code == "refused"

    # Equal content with a different purpose is refused as well: the purpose
    # rule comes first among the operation's own checks (A01 rule 5), before
    # an equal contract version is returned (A01 rule 4).
    with pytest.raises(Exception) as exc:
        _function(semantic_runtime, slot_id, "A01 witness: another purpose", NUMBER)
    assert exc.value.code == "refused"

    # Nothing was recorded: the slot keeps its purpose and its one version.
    history = semantic_runtime.read_slot(slot_id)
    assert history.slot.purpose == purpose
    assert history.current_contract_version_id == first
    assert [
        c.contract_version_id for c in _contract_versions_of(semantic_runtime, slot_id)
    ] == [first]

    # Control (A01 rule 5): the same new content with the same purpose is
    # accepted, so the refusal above came from the purpose.
    same_purpose = _function(semantic_runtime, slot_id, purpose, TEXT)
    assert same_purpose != first
    assert semantic_runtime.read_slot(slot_id).slot.purpose == purpose


def test_identity_is_sha256_of_jcs_sorted(semantic_runtime):
    """[witness: verification:kernel_a01_identity_is_sha256_of_jcs_sorted]

    A01 Required test 6: the same contract version submitted with its ports in
    another order has the same `contract_version_id`, and that identity equals
    the SHA-256 of the RFC 8785 canonical JSON of its facts.
    """
    slot_id = "a01_sorted_identity"
    purpose = "A01 witness: sorted identity"
    inputs = [
        _port("b", "input", NUMBER, "open"),
        _port("a", "input", TEXT, "business_confidential"),
    ]
    outputs = [
        _port("z", "output", TEXT),
        _port("y", "output", NUMBER),
    ]

    first = semantic_runtime.issue_contract_version(
        slot_id, purpose, inputs, outputs, resource_bounds=dict(BOUNDS)
    )
    reordered = semantic_runtime.issue_contract_version(
        slot_id,
        purpose,
        list(reversed(inputs)),
        list(reversed(outputs)),
        resource_bounds=dict(BOUNDS),
    )

    # A01 rule 1: order-free lists are sorted before hashing — ports by
    # (direction, name) — so the same content in another order is one identity.
    assert reordered == first
    # A01 rule 1, State 6 decision 14: SHA-256 of the canonical JSON of the
    # ContractVersionContent facts.
    assert first == _contract_version_identity(slot_id, inputs, outputs, BOUNDS)

    # Control (A01 rule 1: list values themselves keep their order): two
    # schemas whose enum lists differ only in order are different contracts,
    # so the equality above is not the result of sorting every list.
    enum_ab = '{"enum":["a","b"],"type":"string"}'
    enum_ba = '{"enum":["b","a"],"type":"string"}'
    with_ab = semantic_runtime.issue_contract_version(
        slot_id,
        purpose,
        [_port("x", "input", enum_ab, "open")],
        [_port("y", "output", NUMBER)],
        resource_bounds=dict(BOUNDS),
    )
    with_ba = semantic_runtime.issue_contract_version(
        slot_id,
        purpose,
        [_port("x", "input", enum_ba, "open")],
        [_port("y", "output", NUMBER)],
        resource_bounds=dict(BOUNDS),
    )
    assert with_ab != with_ba
    assert with_ab == _contract_version_identity(
        slot_id,
        [_port("x", "input", enum_ab, "open")],
        [_port("y", "output", NUMBER)],
        BOUNDS,
    )


def test_flow_purpose_fixed_at_creation(semantic_runtime):
    """[witness: verification:kernel_a01_flow_purpose_fixed_at_creation]

    A01 Required test 7: a request naming an existing flow with a different
    purpose is refused; one with the same purpose, or none, is accepted.
    """
    contract = _function(semantic_runtime, "a01_flow_step")
    flow_id = "a01_flow_purpose"
    purpose = "A01 witness: flow purpose"

    def compose(flow_purpose, node_ids):
        return semantic_runtime.compose_flow_version(
            flow_id,
            purpose=flow_purpose,
            inputs=[],
            outputs=[],
            nodes=[_node(node_id, contract) for node_id in node_ids],
            edges=[],
            constants=[],
        )

    first = compose(purpose, ["a"])
    first_id = first.flow_version.flow_version_id

    # New content, so only the purpose can refuse it.
    with pytest.raises(Exception) as exc:
        compose("A01 witness: another purpose", ["a", "b"])
    # A01 rule 5: a different purpose for an existing flow is refused.
    assert exc.value.code == "refused"

    # Equal content with a different purpose is refused as well: the purpose
    # rule comes first (A01 rule 5; State 5 compose_flow_version), before an
    # equal flow version is returned (A01 rule 4).
    with pytest.raises(Exception) as exc:
        compose("A01 witness: another purpose", ["a"])
    assert exc.value.code == "refused"

    # Nothing was recorded: the flow keeps its purpose and its one version.
    assert semantic_runtime.active_flow_version(flow_id).flow.purpose == purpose
    assert [
        v.flow_version_id for v in _flow_versions_of(semantic_runtime, flow_id)
    ] == [first_id]

    # A01 rule 5: the same purpose, or none, is accepted.
    same_purpose = compose(purpose, ["a", "b"])
    no_purpose = compose(None, ["a", "b", "c"])
    same_id = same_purpose.flow_version.flow_version_id
    none_id = no_purpose.flow_version.flow_version_id
    assert len({first_id, same_id, none_id}) == 3
    assert [
        v.flow_version_id for v in _flow_versions_of(semantic_runtime, flow_id)
    ] == [none_id, same_id, first_id]  # newest first (A16 rule 6)
    assert semantic_runtime.active_flow_version(flow_id).flow.purpose == purpose


def test_activation_identity_is_store_position(semantic_runtime):
    """[witness: verification:kernel_a01_activation_identity_is_store_position]

    A01 Required test 8: submitting admitted implementations i1, then i2, of
    one contract version and then rolling back to i1 records three Activation
    records in store order, the third a new record, not the first again;
    rolling back to i1 once more records nothing.
    """
    slot_id = "a01_activation_position"
    contract = _function(semantic_runtime, slot_id)
    # One case both implementations pass: 2 * 2 == 2 + 2.
    semantic_runtime.add_trial_case(
        contract, inputs=[_json("x", "2")], expected_outputs=[_json("y", "4")]
    )

    semantic_runtime.clock.set(T1)
    i1 = semantic_runtime.submit_implementation(contract, DOUBLE)
    semantic_runtime.clock.advance(ms=MINUTE_MS)
    i2 = semantic_runtime.submit_implementation(contract, PLUS_TWO)
    for submission in (i1, i2):
        assert _value(submission.verdict.verdict) == "admitted"
    i1_id = i1.implementation.implementation_id
    i2_id = i2.implementation.implementation_id
    assert i1.activation.implementation_id == i1_id
    assert i2.activation.implementation_id == i2_id

    semantic_runtime.clock.advance(ms=MINUTE_MS)
    rolled_back = semantic_runtime.roll_back_slot(slot_id, i1_id)

    # A01 rule 3: three Activation records in store order; the third is a new
    # record of i1, not the first one again.
    positions = [
        i1.activation.store_position,
        i2.activation.store_position,
        rolled_back.store_position,
    ]
    assert positions == sorted(positions)
    assert len(set(positions)) == 3
    assert rolled_back.implementation_id == i1_id
    assert rolled_back.activated_at.epoch_us == T1 + 2 * MINUTE_MS * 1000

    # A01 rule 3 (A04 rule 5): asking for the one already active records
    # nothing and returns that activation.
    semantic_runtime.clock.advance(ms=MINUTE_MS)
    again = semantic_runtime.roll_back_slot(slot_id, i1_id)
    assert again.store_position == rolled_back.store_position
    assert again.activated_at.epoch_us == rolled_back.activated_at.epoch_us

    # The slot's latest activation is still the third record.
    (history,) = semantic_runtime.read_slot(slot_id).contract_versions
    assert history.serving_activation.store_position == rolled_back.store_position
    assert history.serving_activation.implementation_id == i1_id
