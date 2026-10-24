"""Witness tests for accepted decision A16 (02_rules_installation.md).

One owner token and named agent tokens reach one fixed set of typed
operations. A request is checked in one order — its size, its token, its
schema, its actor — before any operation looks at a record; who may do what is
State 0's table; agent text is data; list pages are bounded. Each test carries
the witness name its Required test declares.

The Factory project supplies the ``semantic_runtime`` pytest fixture. It binds
these scenarios to the generated public operations of State 5 — named here by
their operation names, with arguments shaped as the State 6 models — without
changing the assertions below. Each test gets a fresh, empty kernel store; the
installation starts with the owner, agent ``author`` (author right) and agent
``helper`` (no author right).

Fixture surface used here:

- ``issue_contract_version(slot_id, purpose, inputs, outputs)`` ->
  contract_version_id; the fixture supplies resource bounds within the
  installation's ceilings;
- ``add_trial_case(contract_version_id, inputs, expected_outputs)`` ->
  ShownAddedTrialCase; ``submit_implementation(contract_version_id, code)`` ->
  ShownSubmission;
- ``compose_flow_version(...)`` -> ComposedFlowVersion;
  ``activate_flow_version(flow_version_id)`` -> FlowActivation;
  ``start_run(flow_id, inputs)`` -> ShownRun;
- ``propose_binding(...)`` / ``accept_binding(binding_id)`` /
  ``read_binding(binding_id)`` -> OperationBinding;
- the owner-only calls ``continue_after_approval``,
  ``continue_after_resolution``, ``cancel_run``, ``grant_standing_approval``,
  ``revoke_standing_approval``, ``read_spooled_file``, ``read_fixture_file``;
- ``read_slot(slot_id)`` -> SlotHistory; ``active_flow_version(flow_id)`` ->
  FlowAnswer; ``page_records(record_type, record_filter, page_size,
  continuation_token)`` -> RecordPageAnswer;
- every call takes ``actor=`` (an Actor M27 dict);
- capabilities: ``mcp_request`` (one request over the MCP entrance with a
  given token, or raw bytes), ``surface_answers``, ``installation`` (tokens and
  configuration), ``manifest`` and ``stub_service`` (one `read` service for an
  existing binding), ``restart``, ``host_scratch_directory`` (a host
  directory outside the data directory that the kernel process could write).
"""

import secrets

import pytest

OWNER = {"kind": "owner", "agent_name": None}
AUTHOR = {"kind": "agent", "agent_name": "author"}
HELPER = {"kind": "agent", "agent_name": "helper"}

TEXT = '{"type":"string"}'

# A20 rule 1, release v1
SURFACE_REQUEST_BYTES_MAX = 134217728
# A20 rule 1, release v1
BOUNDED_TEXT_BYTES_MAX = 16384
# A20 rule 1, release v1
PAGE_SIZE_DEFAULT = 50
# A20 rule 1, release v1
PAGE_SIZE_MAX = 200

# Names of records that do not exist. A content identity is a SHA-256 (A01
# rule 1); a minted one has no shape a request could get wrong.
MISSING_CONTENT_ID = "0" * 64
MISSING_MINTED_ID = "a16-missing-record"

ECHO_CODE = "def run(inputs):\n    return {'y': inputs['x']}\n"


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


def _bounds():
    """Resource bounds within the release v1 ceilings (A20 rule 1)."""
    return {
        "wall_time_ms": 10000,
        "memory_bytes": 268435456,
        "output_bytes": 1048576,
        "process_count": 4,
    }


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


def _edge(from_node, from_port, to_node, to_port):
    return {
        "from_node": from_node,
        "from_port": from_port,
        "to_node": to_node,
        "to_port": to_port,
        "guard": None,
    }


def _equals(field, value):
    return {"filter_kind": "equals", "field": field, "value": value}


def _refusal(call, *args, **kwargs):
    with pytest.raises(Exception) as exc:
        call(*args, **kwargs)
    return exc.value


def _missing_attempt():
    return {
        "run_id": MISSING_MINTED_ID,
        "node_id": "n",
        "map_index": None,
        "attempt_number": 1,
    }


def _missing_spooled_file():
    return {
        "run_id": MISSING_MINTED_ID,
        "producer_node_id": "n",
        "map_index": None,
        "attempt_number": 1,
        "producer_port": "y",
        "list_index": None,
    }


def _echo_function(semantic_runtime, slot_id):
    """An admitted, activated function of one text input `x` and output `y`."""
    contract_version_id = semantic_runtime.issue_contract_version(
        slot_id,
        purpose=f"A16 witness: {slot_id}",
        inputs=[_port("x", "input", TEXT, "open")],
        outputs=[_port("y", "output", TEXT)],
    )
    semantic_runtime.add_trial_case(
        contract_version_id,
        inputs=[_json("x", '"a"')],
        expected_outputs=[_json("y", '"a"')],
    )
    submission = semantic_runtime.submit_implementation(contract_version_id, ECHO_CODE)
    assert getattr(submission.verdict.verdict, "value", submission.verdict.verdict) == "admitted"
    return contract_version_id


def _finished_run(semantic_runtime, name):
    """A run of a one-function flow, started by the owner."""
    contract_version_id = _echo_function(semantic_runtime, f"{name}_slot")
    composed = semantic_runtime.compose_flow_version(
        f"{name}_flow",
        purpose=f"A16 witness: {name}",
        inputs=[_port("x", "input", TEXT, "open")],
        outputs=[_port("y", "output", TEXT)],
        nodes=[_node("f", contract_version_id)],
        edges=[_edge("", "x", "f", "x"), _edge("f", "y", "", "y")],
        constants=[],
    )
    assert composed.proof.proven is True
    semantic_runtime.activate_flow_version(composed.flow_version.flow_version_id, actor=OWNER)
    return semantic_runtime.start_run(f"{name}_flow", inputs=[_json("x", '"a"')], actor=OWNER)


def _read_service(semantic_runtime, service_id):
    """A manifest record of one `read` operation on a loopback stub, selected."""
    stub = semantic_runtime.stub_service()
    stub.on("GET", "/items", status=200, json={"item": "a"})
    semantic_runtime.manifest.write_record(
        service_id,
        {
            "service": service_id,
            "capabilities": [
                {
                    "name": "get_item",
                    "exposed_as": {"http_api": ["GET /items"]},
                    "effect_class": "read",
                    "idempotency_key": None,
                }
            ],
            "instances": [
                {
                    "instance_name": "local",
                    "api_base_url": stub.base_url,
                    "required_headers": None,
                    "instance_class": "local_dev",
                }
            ],
        },
    )
    semantic_runtime.installation.select_instance(service_id, "local")
    return stub


def _list_slots(semantic_runtime, token):
    return semantic_runtime.mcp_request(
        "list_records",
        {
            "record_type": "slot",
            "record_filter": None,
            "page_size": None,
            "continuation_token": None,
        },
        token=token,
    )


def test_owner_only_actions_refuse_agents(semantic_runtime):
    """[witness: verification:kernel_a16_owner_only_actions_refuse_agents]

    A16 Required test 1: each owner-only action attempted with an authoring
    agent token is refused.
    """
    # The manifest shapes the first start, so it is written before any call.
    _read_service(semantic_runtime, "a16_items")

    binding = semantic_runtime.propose_binding(
        "a16_items",
        "get_item",
        inputs=[],
        outputs=[_port("item", "output", TEXT, "open")],
        actor=AUTHOR,
    )
    binding_id = binding.binding_id

    # A16 rule 3: accepting a binding is owner only; the actor check comes
    # before the operation's own checks (rule 1), so nothing is changed.
    refusal = _refusal(semantic_runtime.accept_binding, binding_id, actor=AUTHOR)
    assert refusal.code == "not_permitted"
    still = semantic_runtime.read_binding(binding_id)
    assert getattr(still.status, "value", still.status) == "proposed"
    assert still.accepted_by is None
    assert still.accepted_at is None

    # Every other owner-only action (A16 rule 3; reading a spooled file's or a
    # fixture's bytes, A10 rule 2), each naming a record that does not exist.
    owner_only = [
        ("continue_after_approval", (MISSING_MINTED_ID, "approve")),
        ("continue_after_approval", (MISSING_MINTED_ID, "refuse")),
        ("continue_after_resolution", (_missing_attempt(), "applied")),
        ("cancel_run", (MISSING_MINTED_ID,)),
        ("grant_standing_approval", ("a16_missing_flow", "n")),
        ("revoke_standing_approval", (MISSING_MINTED_ID,)),
        ("read_spooled_file", (_missing_spooled_file(),)),
        ("read_fixture_file", (MISSING_CONTENT_ID,)),
    ]
    for name, args in owner_only:
        call = getattr(semantic_runtime, name)
        # A16 rule 1: the actor check precedes the record lookup, so the
        # author is refused as not permitted, not as an unknown reference.
        refusal = _refusal(call, *args, actor=AUTHOR)
        assert refusal.code == "not_permitted", name

        # Control: the owner passes the actor check and reaches the lookup,
        # so the refusal above comes from the actor, not from the missing
        # record.
        control = _refusal(call, *args, actor=OWNER)
        assert control.code == "unknown_reference", name

    # Control: the owner accepts the binding the author could not.
    accepted = semantic_runtime.accept_binding(binding_id, actor=OWNER)
    assert getattr(accepted.status, "value", accepted.status) == "accepted"
    kind = accepted.accepted_by.kind
    assert getattr(kind, "value", kind) == "owner"


def test_unknown_token_uniform_refusal(semantic_runtime):
    """[witness: verification:kernel_a16_unknown_token_uniform_refusal]

    A16 Required test 2: an unknown token asking for an existing and for a
    missing run gets the same refusal.
    """
    run = _finished_run(semantic_runtime, "a16_uniform")
    unknown_token = secrets.token_urlsafe(32)
    assert unknown_token != semantic_runtime.installation.owner_token

    before = len(semantic_runtime.surface_answers())
    with pytest.raises(Exception) as existing:
        semantic_runtime.mcp_request("get_run", {"run_id": run.run_id}, token=unknown_token)
    with pytest.raises(Exception) as missing:
        semantic_runtime.mcp_request("get_run", {"run_id": MISSING_MINTED_ID}, token=unknown_token)
    answers = semantic_runtime.surface_answers()

    # A16 rule 1: one token refusal that reveals nothing about any record.
    assert existing.value.code == "unauthorized"
    assert missing.value.code == "unauthorized"
    assert existing.value.reason == missing.value.reason
    assert len(answers) == before + 2
    assert answers[-2] == answers[-1]

    # A missing token gets that same one refusal (A16 rule 1). token=None
    # sends the request without a token.
    with pytest.raises(Exception) as no_token:
        semantic_runtime.mcp_request("get_run", {"run_id": run.run_id}, token=None)
    assert no_token.value.code == "unauthorized"
    assert no_token.value.reason == existing.value.reason
    assert semantic_runtime.surface_answers()[-1] == answers[-1]

    # Control: with the owner token the two requests differ — the run is
    # answered, the missing one is an unknown reference — so the sameness
    # above comes from the token check.
    owner_token = semantic_runtime.installation.owner_token
    shown = semantic_runtime.mcp_request("get_run", {"run_id": run.run_id}, token=owner_token)
    assert shown.run_id == run.run_id
    with pytest.raises(Exception) as control:
        semantic_runtime.mcp_request("get_run", {"run_id": MISSING_MINTED_ID}, token=owner_token)
    assert control.value.code == "unknown_reference"


def test_revoked_token_refused_without_restart(semantic_runtime):
    """[witness: verification:kernel_a16_revoked_token_refused_without_restart]

    A16 Required test 3: removing an agent token from the configuration
    refuses that agent's next request without a restart.
    """
    installation = semantic_runtime.installation
    owner_token = installation.owner_token
    author_token = installation.agent_token("author")
    helper_token = installation.agent_token("helper")
    author_entry = {"agent_name": "author", "token": author_token, "may_author": True}
    helper_entry = {"agent_name": "helper", "token": helper_token, "may_author": False}

    answer = _list_slots(semantic_runtime, helper_token)
    assert getattr(answer.record_type, "value", answer.record_type) == "slot"

    # A16 rule 2: the configuration is read before each request; a changed
    # file replaces the token list. No restart is made in this test.
    installation.set_agent_tokens([author_entry])

    with pytest.raises(Exception) as exc:
        _list_slots(semantic_runtime, helper_token)
    assert exc.value.code == "unauthorized"

    # Control: the re-read passed, so the tokens still listed are served.
    assert len(_list_slots(semantic_runtime, author_token).records.slots) == 0
    assert len(_list_slots(semantic_runtime, owner_token).records.slots) == 0

    # Control: putting the token back serves it again, also without a restart,
    # so the refusal came from the re-read list.
    installation.set_agent_tokens([author_entry, helper_entry])
    answer = _list_slots(semantic_runtime, helper_token)
    assert getattr(answer.record_type, "value", answer.record_type) == "slot"


def test_schema_checked_before_record_read(semantic_runtime):
    """[witness: verification:kernel_a16_schema_checked_before_record_read]

    A16 Required test 4: a request with an unknown field is refused before any
    record is read.
    """
    semantic_runtime.issue_contract_version(
        "a16_schema_slot",
        purpose="A16 witness: schema before records",
        inputs=[_port("x", "input", TEXT, "open")],
        outputs=[_port("y", "output", TEXT)],
    )
    owner_token = semantic_runtime.installation.owner_token

    # A16 rules 1 and 4: an unknown field is refused at the schema step, before
    # the operation's own checks; whether the named record exists cannot
    # change the answer.
    for slot_id in ("a16_schema_slot", "a16_missing_slot"):
        with pytest.raises(Exception) as exc:
            semantic_runtime.mcp_request(
                "get_slot",
                {"slot_id": slot_id, "include_history": True},
                token=owner_token,
            )
        assert exc.value.code == "invalid_request", slot_id

    with pytest.raises(Exception) as exc:
        semantic_runtime.mcp_request(
            "cancel_run",
            {"run_id": MISSING_MINTED_ID, "reason": "A16 witness"},
            token=owner_token,
        )
    assert exc.value.code == "invalid_request"

    # Control: without the unknown field the same requests reach the record:
    # the existing slot is answered, the missing slot and run are unknown
    # references. So the refusals above are decided before any record is read.
    shown = semantic_runtime.mcp_request(
        "get_slot", {"slot_id": "a16_schema_slot"}, token=owner_token
    )
    assert shown.slot.slot_id == "a16_schema_slot"
    with pytest.raises(Exception) as control:
        semantic_runtime.mcp_request(
            "get_slot", {"slot_id": "a16_missing_slot"}, token=owner_token
        )
    assert control.value.code == "unknown_reference"
    with pytest.raises(Exception) as control:
        semantic_runtime.mcp_request(
            "cancel_run", {"run_id": MISSING_MINTED_ID}, token=owner_token
        )
    assert control.value.code == "unknown_reference"


def test_agent_text_stored_verbatim(semantic_runtime):
    """[witness: verification:kernel_a16_agent_text_stored_verbatim]

    A16 Required test 5: a purpose containing template or SQL syntax is stored
    and returned verbatim.
    """
    # A16 rule 5: text an agent supplies is data — never evaluated, formatted
    # or interpreted inside the kernel process.
    slot_purpose = (
        "{{ 7*7 }} {% if 1 %}x{% endif %} ${7*7} #{7*7} {0!r} {purpose} "
        "%s %(x)s %d '); DROP TABLE slot; -- \" OR '1'='1 /* */ \\x00"
    )
    flow_purpose = (
        "'; DELETE FROM flow WHERE '1'='1'; -- {{ config }} ${env:HOME} "
        "{__import__('os').system('true')} %n"
    )

    semantic_runtime.issue_contract_version(
        "a16_verbatim_slot",
        purpose=slot_purpose,
        inputs=[_port("x", "input", TEXT, "open")],
        outputs=[_port("y", "output", TEXT)],
        actor=AUTHOR,
    )
    history = semantic_runtime.read_slot("a16_verbatim_slot")
    assert history.slot.purpose == slot_purpose

    composed = semantic_runtime.compose_flow_version(
        "a16_verbatim_flow",
        purpose=flow_purpose,
        inputs=[],
        outputs=[],
        nodes=[],
        edges=[],
        constants=[],
        actor=AUTHOR,
    )
    assert composed.flow.purpose == flow_purpose
    assert semantic_runtime.active_flow_version("a16_verbatim_flow").flow.purpose == flow_purpose

    # Listed alike, and the store still holds both records: the SQL text
    # dropped and deleted nothing.
    slots = semantic_runtime.page_records("slot").records.slots
    assert [slot.purpose for slot in slots] == [slot_purpose]
    flows = semantic_runtime.page_records("flow").records.flows
    assert [flow.purpose for flow in flows] == [flow_purpose]

    # An agent reads the same text (purposes are not masked, A07).
    assert semantic_runtime.read_slot("a16_verbatim_slot", actor=HELPER).slot.purpose == slot_purpose


def test_author_actions_need_author_right(semantic_runtime):
    """[witness: verification:kernel_a16_author_actions_need_author_right]

    A16 Required test 7: an author action (author a contract or an
    implementation, add a trial case) is refused with the token of an agent
    without the author right and with the owner token.
    """
    contract_version_id = semantic_runtime.issue_contract_version(
        "a16_author_slot",
        purpose="A16 witness: author right",
        inputs=[_port("x", "input", TEXT, "open")],
        outputs=[_port("y", "output", TEXT)],
        actor=AUTHOR,
    )
    corpus_filter = _equals("contract_version_id", contract_version_id)

    # A16 rule 3: authoring a contract or an implementation and adding a
    # trial case belong to an agent with the author right only.
    for actor in (HELPER, OWNER):
        refusal = _refusal(
            semantic_runtime.issue_contract_version,
            "a16_author_new_slot",
            purpose="A16 witness: not an author",
            inputs=[_port("x", "input", TEXT, "open")],
            outputs=[_port("y", "output", TEXT)],
            actor=actor,
        )
        assert refusal.code == "not_permitted", actor

        refusal = _refusal(
            semantic_runtime.add_trial_case,
            contract_version_id,
            inputs=[_json("x", '"a"')],
            expected_outputs=[_json("y", '"a"')],
            actor=actor,
        )
        assert refusal.code == "not_permitted", actor

        refusal = _refusal(
            semantic_runtime.submit_implementation,
            contract_version_id,
            ECHO_CODE,
            actor=actor,
        )
        assert refusal.code == "not_permitted", actor

    # A refusal writes nothing (State 5, Conventions): no slot, no case, no
    # implementation.
    missing = _refusal(semantic_runtime.read_slot, "a16_author_new_slot")
    assert missing.code == "unknown_reference"
    cases = semantic_runtime.page_records("trial_case", corpus_filter)
    assert len(cases.records.trial_cases) == 0
    implementations = semantic_runtime.page_records("implementation", corpus_filter)
    assert len(implementations.records.implementations) == 0

    # Control: the same three requests by the author succeed.
    semantic_runtime.issue_contract_version(
        "a16_author_new_slot",
        purpose="A16 witness: not an author",
        inputs=[_port("x", "input", TEXT, "open")],
        outputs=[_port("y", "output", TEXT)],
        actor=AUTHOR,
    )
    added = semantic_runtime.add_trial_case(
        contract_version_id,
        inputs=[_json("x", '"a"')],
        expected_outputs=[_json("y", '"a"')],
        actor=AUTHOR,
    )
    assert added.trial_case.contract_version_id == contract_version_id
    submission = semantic_runtime.submit_implementation(
        contract_version_id, ECHO_CODE, actor=AUTHOR
    )
    assert submission.implementation.contract_version_id == contract_version_id


def test_tokens_unique(semantic_runtime):
    """[witness: verification:kernel_a16_tokens_unique]

    A16 Required test 8: the installation refuses to start, and a
    configuration re-read refuses every request, when two tokens are equal or
    two agent tokens share a name.
    """
    installation = semantic_runtime.installation
    owner_token = installation.owner_token
    author_token = installation.agent_token("author")
    helper_token = installation.agent_token("helper")
    valid = [
        {"agent_name": "author", "token": author_token, "may_author": True},
        {"agent_name": "helper", "token": helper_token, "may_author": False},
    ]
    broken_lists = {
        "two agent tokens equal": [
            {"agent_name": "author", "token": author_token, "may_author": True},
            {"agent_name": "helper", "token": author_token, "may_author": False},
        ],
        "agent token equal to the owner token": [
            {"agent_name": "author", "token": author_token, "may_author": True},
            {"agent_name": "helper", "token": owner_token, "may_author": False},
        ],
        "two agent tokens of one name": [
            {"agent_name": "author", "token": author_token, "may_author": True},
            {"agent_name": "author", "token": helper_token, "may_author": False},
        ],
    }

    # The kernel is running with a valid list.
    _list_slots(semantic_runtime, owner_token)

    for case, broken in broken_lists.items():
        # A16 rule 2: a re-read that finds two equal tokens or two agent
        # tokens of one name refuses every request, the owner's included,
        # with the one token refusal; the old list is not kept.
        installation.set_agent_tokens(broken)
        for token in (owner_token, author_token, helper_token):
            with pytest.raises(Exception) as exc:
                _list_slots(semantic_runtime, token)
            assert exc.value.code == "unauthorized", case

        # Control: a re-read that passes serves requests again, without a
        # restart, so the refusal came from the broken list.
        installation.set_agent_tokens(valid)
        _list_slots(semantic_runtime, owner_token)

        # A16 rule 1: the installation refuses to start with that list.
        installation.set_agent_tokens(broken)
        outcome = semantic_runtime.restart()
        assert outcome.started is False, case

        # Control: the same installation with a valid list starts.
        installation.set_agent_tokens(valid)
        outcome = semantic_runtime.restart()
        assert outcome.started is True, case
        _list_slots(semantic_runtime, owner_token)


def test_request_size_and_field_bounds(semantic_runtime):
    """[witness: verification:kernel_a16_request_size_and_field_bounds]

    A16 Required test 9: a request one byte over `surface_request_bytes_max`
    that carries an unknown token gets the size refusal, not the token
    refusal; a string field one byte over its bound is refused before any
    record is read.
    """
    unknown_token = secrets.token_urlsafe(32)

    # A16 rule 1: size first, counted as the bytes of the request message as
    # received; the token is checked only after it. Neither check reads the
    # message's content, so its bytes are padding.
    over = b"{" + b" " * (SURFACE_REQUEST_BYTES_MAX - 1) + b"}"
    assert len(over) == SURFACE_REQUEST_BYTES_MAX + 1
    with pytest.raises(Exception) as exc:
        semantic_runtime.mcp_request("get_slot", {}, token=unknown_token, raw=over)
    assert exc.value.code == "invalid_request"

    # Control: at exactly the ceiling the size passes and the unknown token is
    # what is refused, so the refusal above is the size's.
    at = b"{" + b" " * (SURFACE_REQUEST_BYTES_MAX - 2) + b"}"
    assert len(at) == SURFACE_REQUEST_BYTES_MAX
    with pytest.raises(Exception) as control:
        semantic_runtime.mcp_request("get_slot", {}, token=unknown_token, raw=at)
    assert control.value.code == "unauthorized"
    del over, at

    owner_token = semantic_runtime.installation.owner_token
    author_token = semantic_runtime.installation.agent_token("author")

    # A16 rule 4: every other string is at most `bounded_text_bytes_max`,
    # counted as UTF-8 bytes ("é" is two bytes), checked at the schema step.
    over_name = "é" * (BOUNDED_TEXT_BYTES_MAX // 2) + "a"
    at_name = "é" * (BOUNDED_TEXT_BYTES_MAX // 2)
    assert len(over_name.encode("utf-8")) == BOUNDED_TEXT_BYTES_MAX + 1
    assert len(at_name.encode("utf-8")) == BOUNDED_TEXT_BYTES_MAX
    with pytest.raises(Exception) as exc:
        semantic_runtime.mcp_request("get_run", {"run_id": over_name}, token=owner_token)
    assert exc.value.code == "invalid_request"
    # Control: one byte less reaches the lookup and names no run.
    with pytest.raises(Exception) as control:
        semantic_runtime.mcp_request("get_run", {"run_id": at_name}, token=owner_token)
    assert control.value.code == "unknown_reference"

    # Over its bound on a request naming an existing record: the slot exists
    # with another purpose, which A01 rule 5 would refuse after reading it.
    semantic_runtime.issue_contract_version(
        "a16_bounds_slot",
        purpose="A16 witness: field bounds",
        inputs=[_port("x", "input", TEXT, "open")],
        outputs=[_port("y", "output", TEXT)],
        actor=AUTHOR,
    )

    def _issue(purpose):
        return semantic_runtime.mcp_request(
            "issue_contract_version",
            {
                "slot_id": "a16_bounds_slot",
                "purpose": purpose,
                "inputs": [_port("x", "input", TEXT, "open")],
                "outputs": [_port("z", "output", TEXT)],
                "resource_bounds": _bounds(),
            },
            token=author_token,
        )

    with pytest.raises(Exception) as exc:
        _issue("p" * (BOUNDED_TEXT_BYTES_MAX + 1))
    assert exc.value.code == "invalid_request"
    # Control: within the bound the slot is read and its different purpose
    # refused (A01 rule 5), so the refusal above came before that read.
    with pytest.raises(Exception) as control:
        _issue("p" * BOUNDED_TEXT_BYTES_MAX)
    assert control.value.code == "refused"

    # Nothing was recorded: the slot still has its one contract version.
    history = semantic_runtime.read_slot("a16_bounds_slot")
    assert len(history.contract_versions) == 1


def test_page_size_bounded(semantic_runtime):
    """[witness: verification:kernel_a16_page_size_bounded]

    A16 Required test 10: a list request with a page size of `page_size_max`
    + 1 or of 0 is refused; one without a size returns at most
    `page_size_default` items.
    """
    slot_id = "a16_paging_slot"
    count = PAGE_SIZE_DEFAULT + 1
    for index in range(count):
        semantic_runtime.issue_contract_version(
            slot_id,
            purpose="A16 witness: page size",
            inputs=[_port(f"x{index:02d}", "input", TEXT, "open")],
            outputs=[_port("y", "output", TEXT)],
            actor=AUTHOR,
        )
    by_slot = _equals("slot_id", slot_id)

    # A16 rule 6 (State 5: invalid_request): a size above `page_size_max` or
    # below 1 is refused.
    for page_size in (PAGE_SIZE_MAX + 1, 0):
        refusal = _refusal(
            semantic_runtime.page_records,
            "contract_version",
            by_slot,
            page_size=page_size,
        )
        assert refusal.code == "invalid_request", page_size

    # A16 rule 6: without a size, `page_size_default` items; more remain.
    first = semantic_runtime.page_records("contract_version", by_slot)
    assert len(first.records.contract_versions) == PAGE_SIZE_DEFAULT
    assert first.continuation_token is not None
    rest = semantic_runtime.page_records(
        "contract_version", by_slot, continuation_token=first.continuation_token
    )
    assert len(rest.records.contract_versions) == count - PAGE_SIZE_DEFAULT
    assert rest.continuation_token is None

    # Control: the bounds themselves are accepted, so the refusals above are
    # the bound's, not a refusal of any explicit size.
    at_max = semantic_runtime.page_records("contract_version", by_slot, page_size=PAGE_SIZE_MAX)
    assert len(at_max.records.contract_versions) == count
    one = semantic_runtime.page_records("contract_version", by_slot, page_size=1)
    assert len(one.records.contract_versions) == 1


def _marker_code(marker):
    """Code that writes `marker` when imported and again when `run` is called."""
    return (
        "import pathlib\n"
        f"pathlib.Path({str(marker)!r}).write_text('imported')\n"
        "\n"
        "def run(inputs):\n"
        f"    pathlib.Path({str(marker)!r}).write_text('evaluated')\n"
        "    return {'y': inputs['x']}\n"
    )


def test_agent_code_not_run_in_kernel(semantic_runtime):
    """[witness: verification:kernel_a16_agent_code_not_run_in_kernel]

    A16 Required test 11: authoring an implementation whose code would write a
    marker file when imported or evaluated writes no marker.
    """
    marker = semantic_runtime.host_scratch_directory() / "a16_marker"
    code = _marker_code(marker)

    # Control: the code does write the marker when imported and evaluated, so
    # its absence below is the kernel's doing, not a marker that cannot appear.
    namespace = {}
    exec(compile(code, "a16_marker_code", "exec"), namespace)
    namespace["run"]({"x": "a"})
    assert marker.read_text() == "evaluated"
    marker.unlink()

    contract_version_id = semantic_runtime.issue_contract_version(
        "a16_marker_slot",
        purpose="A16 witness: agent code is data",
        inputs=[_port("x", "input", TEXT, "open")],
        outputs=[_port("y", "output", TEXT)],
        actor=AUTHOR,
    )

    # With no case nothing executes (A04 rule 3: refused `empty_corpus`), so
    # only the kernel process could have imported the code.
    empty = semantic_runtime.submit_implementation(contract_version_id, code, actor=AUTHOR)
    assert getattr(empty.verdict.verdict, "value", empty.verdict.verdict) == "refused"
    assert getattr(
        empty.verdict.reason.reason_kind, "value", empty.verdict.reason.reason_kind
    ) == "empty_corpus"
    # A16 rule 5: the kernel never evaluates or imports agent text in its own
    # process.
    assert not marker.exists()

    # The code is kept as data, verbatim (A16 rule 5; A03 Required test 4).
    implementation_id = empty.implementation.implementation_id
    stored = semantic_runtime.read_implementation(implementation_id, actor=OWNER)
    assert stored.implementation.code == code

    # With a case the code runs only in the sandbox (A03 rule 1): no host
    # directory is mounted there, and opening a path outside the exchange
    # directory is a trap (A03 rule 4), so no marker reaches the host.
    semantic_runtime.add_trial_case(
        contract_version_id,
        inputs=[_json("x", '"a"')],
        expected_outputs=[_json("y", '"a"')],
        actor=AUTHOR,
    )
    tried = semantic_runtime.submit_implementation(contract_version_id, code, actor=AUTHOR)
    assert tried.implementation.implementation_id == implementation_id
    assert getattr(tried.verdict.verdict, "value", tried.verdict.verdict) == "refused"
    assert getattr(
        tried.verdict.reason.outcome, "value", tried.verdict.reason.outcome
    ) == "sandbox_violation"
    assert not marker.exists()
