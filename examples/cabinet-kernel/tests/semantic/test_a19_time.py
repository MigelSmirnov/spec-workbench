"""Witness tests for accepted decision A19 (02_rules_installation.md).

Kernel time has one source: every timestamp the kernel records comes from its
clock module, a request never supplies the current time, a service's timestamp
is a value like any other, and a monotonic reading bounds a wait without ever
being stored. Each test carries the witness name its Required test declares.

The Factory project supplies the ``semantic_runtime`` pytest fixture. It binds
these scenarios to the generated public operations of State 5 — named here by
their operation names, with arguments shaped as the State 6 models — without
changing the assertions below. Each test gets a fresh, empty kernel store.

Fixture surface used here:

- ``issue_contract_version(slot_id, purpose, inputs, outputs)`` ->
  contract_version_id; the fixture supplies resource bounds within the
  installation's ceilings and acts as the author agent;
- ``add_trial_case(contract_version_id, inputs, expected_outputs)`` ->
  ShownAddedTrialCase; ``submit_implementation(contract_version_id, code)`` ->
  ShownSubmission;
- ``propose_binding(...)`` / ``accept_binding(binding_id)`` ->
  OperationBinding;
- ``compose_flow_version(...)`` -> ComposedFlowVersion;
  ``activate_flow_version(flow_version_id)`` -> FlowActivation;
  ``start_run(flow_id, inputs)`` -> ShownRun;
- ``read_slot(slot_id)`` -> SlotHistory; ``active_flow_version(flow_id)`` ->
  FlowAnswer; ``read_run(run_id)`` -> ShownRun; ``page_records(record_type, record_filter, page_size)`` ->
  RecordPageAnswer;
- capabilities: ``clock`` (the injected ``clock.kernel_now`` and monotonic
  source), ``manifest``, ``installation`` and ``stub_service`` (one `read`
  service on loopback), ``mcp_request`` (requests with an added field),
  ``store_dump`` (every byte the store holds).
"""

import pytest

OWNER = {"kind": "owner", "agent_name": None}
AUTHOR = {"kind": "agent", "agent_name": "author"}

TEXT = '{"type":"string"}'

ECHO_CODE = "def run(inputs):\n    return {'y': inputs['x']}\n"

# Kernel instants the tests inject, microseconds since the epoch.
T_ISSUE = 1_767_225_600_000_000  # 2026-01-01T00:00:00Z
T_CASE = T_ISSUE + 1_000_000
T_SUBMIT = T_ISSUE + 2_000_000
T_COMPOSE = T_ISSUE + 3_000_000
T_ACTIVATE = T_ISSUE + 4_000_000
T_RUN = T_ISSUE + 5_000_000

# Names of records that do not exist.
MISSING_CONTENT_ID = "0" * 64
MISSING_MINTED_ID = "a19-missing-record"


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


def _function_node(node_id, contract_version_id):
    return {
        "node_id": node_id,
        "kind": "function",
        "contract_version_id": contract_version_id,
        "binding_id": None,
        "map_over": None,
    }


def _operation_node(node_id, binding_id):
    return {
        "node_id": node_id,
        "kind": "operation",
        "contract_version_id": None,
        "binding_id": binding_id,
        "map_over": None,
    }


def _edge(from_node, from_port, to_node, to_port):
    # A05 rule 2: a flow input or output endpoint has the empty string as node.
    return {
        "from_node": from_node,
        "from_port": from_port,
        "to_node": to_node,
        "to_port": to_port,
        "guard": None,
    }


def _equals(field, value):
    return {"filter_kind": "equals", "field": field, "value": value}


def _us(instant):
    return instant.epoch_us


def _status(record):
    return getattr(record.status, "value", record.status)


def _stamp_service(semantic_runtime, service_id):
    """A manifest record of one `read` operation on a loopback stub, selected."""
    stub = semantic_runtime.stub_service()
    semantic_runtime.manifest.write_record(
        service_id,
        {
            "service": service_id,
            "capabilities": [
                {
                    "name": "get_stamp",
                    "exposed_as": {"http_api": ["GET /stamp"]},
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


def _accepted_stamp_binding(semantic_runtime, service_id):
    binding = semantic_runtime.propose_binding(
        service_id,
        "get_stamp",
        inputs=[],
        outputs=[_port("stamp", "output", TEXT, "open")],
        actor=AUTHOR,
    )
    return semantic_runtime.accept_binding(binding.binding_id, actor=OWNER).binding_id


def _authored_sequence(semantic_runtime, name):
    """Issue, add a case, submit, compose, activate and run one echo function,
    the injected clock set to its own instant before each step. Returns every
    timestamp the sequence recorded, by field."""
    clock = semantic_runtime.clock
    slot_id = f"{name}_slot"
    flow_id = f"{name}_flow"

    clock.set(T_ISSUE)
    contract_version_id = semantic_runtime.issue_contract_version(
        slot_id,
        purpose=f"A19 witness: {name}",
        inputs=[_port("x", "input", TEXT, "open")],
        outputs=[_port("y", "output", TEXT)],
    )

    clock.set(T_CASE)
    added = semantic_runtime.add_trial_case(
        contract_version_id,
        inputs=[_json("x", '"a"')],
        expected_outputs=[_json("y", '"a"')],
    )

    clock.set(T_SUBMIT)
    submission = semantic_runtime.submit_implementation(contract_version_id, ECHO_CODE)
    assert getattr(submission.verdict.verdict, "value", submission.verdict.verdict) == "admitted"
    implementation_id = submission.implementation.implementation_id
    trial_executions = semantic_runtime.page_records(
        "trial_execution", _equals("implementation_id", implementation_id), page_size=200
    ).records.trial_executions

    clock.set(T_COMPOSE)
    composed = semantic_runtime.compose_flow_version(
        flow_id,
        purpose=f"A19 witness: {name}",
        inputs=[_port("x", "input", TEXT, "open")],
        outputs=[_port("y", "output", TEXT)],
        nodes=[_function_node("f", contract_version_id)],
        edges=[_edge("", "x", "f", "x"), _edge("f", "y", "", "y")],
        constants=[],
    )
    assert composed.proof.proven is True

    clock.set(T_ACTIVATE)
    activation = semantic_runtime.activate_flow_version(
        composed.flow_version.flow_version_id, actor=OWNER
    )

    clock.set(T_RUN)
    run = semantic_runtime.start_run(flow_id, inputs=[_json("x", '"a"')], actor=OWNER)
    assert _status(run) == "succeeded"
    trace = semantic_runtime.page_records(
        "node_execution", _equals("run_id", run.run_id), page_size=200
    ).records.node_executions

    history = semantic_runtime.read_slot(slot_id)
    flow = semantic_runtime.active_flow_version(flow_id)
    return {
        "slot.created_at": _us(history.slot.created_at),
        "contract_version.issued_at": _us(history.contract_versions[0].contract_version.issued_at),
        "trial_case.added_at": _us(added.trial_case.added_at),
        "implementation.submitted_at": _us(submission.implementation.submitted_at),
        "trial_execution.executed_at": tuple(_us(t.executed_at) for t in trial_executions),
        "verdict.decided_at": _us(submission.verdict.decided_at),
        "activation.activated_at": _us(submission.activation.activated_at),
        "flow.created_at": _us(flow.flow.created_at),
        "flow_version.authored_at": _us(flow.active_version.authored_at),
        "flow_activation.activated_at": _us(activation.activated_at),
        "run.started_at": _us(run.started_at),
        "run.ended_at": _us(run.ended_at),
        "node_execution.started_at": tuple(_us(e.started_at) for e in trace),
        "node_execution.ended_at": tuple(_us(e.ended_at) for e in trace),
    }


def test_timestamps_from_injected_clock(semantic_runtime):
    """[witness: verification:kernel_a19_timestamps_from_injected_clock]

    A19 Required test 1: with an injected fixed clock, the same test sequence
    writes the same timestamps.
    """
    first = _authored_sequence(semantic_runtime, "a19_first")

    # A19 rule 1: every timestamp the kernel records comes from the clock
    # module; State 5 Conventions: taken when its store change is made (a
    # `started_at` when the execution begins), all within the step's request.
    expected = {
        "slot.created_at": T_ISSUE,
        "contract_version.issued_at": T_ISSUE,
        "trial_case.added_at": T_CASE,
        "implementation.submitted_at": T_SUBMIT,
        "trial_execution.executed_at": (T_SUBMIT,),
        "verdict.decided_at": T_SUBMIT,
        "activation.activated_at": T_SUBMIT,
        "flow.created_at": T_COMPOSE,
        "flow_version.authored_at": T_COMPOSE,
        "flow_activation.activated_at": T_ACTIVATE,
        "run.started_at": T_RUN,
        "run.ended_at": T_RUN,
        "node_execution.started_at": (T_RUN,),
        "node_execution.ended_at": (T_RUN,),
    }
    assert first == expected

    # The same sequence again, under the same injected instants, writes the
    # same timestamps.
    second = _authored_sequence(semantic_runtime, "a19_second")
    assert second == first


def test_service_timestamp_not_kernel_time(semantic_runtime):
    """[witness: verification:kernel_a19_service_timestamp_not_kernel_time]

    A19 Required test 2: a service answer with a timestamp far in the future
    changes no kernel record's time or order.
    """
    stub = _stamp_service(semantic_runtime, "a19_stamps")
    future = "2999-12-31T23:59:59Z"
    past = "1970-01-01T00:00:01Z"

    semantic_runtime.clock.set(T_COMPOSE)
    binding_id = _accepted_stamp_binding(semantic_runtime, "a19_stamps")
    composed = semantic_runtime.compose_flow_version(
        "a19_stamp_flow",
        purpose="A19 witness: service timestamps",
        inputs=[],
        outputs=[_port("stamp", "output", TEXT)],
        nodes=[_operation_node("op", binding_id)],
        edges=[_edge("op", "stamp", "", "stamp")],
        constants=[],
    )
    assert composed.proof.proven is True
    semantic_runtime.activate_flow_version(composed.flow_version.flow_version_id, actor=OWNER)

    # Run A: the service answers a time far in the future, in its body and in
    # its date headers.
    stub.on(
        "GET",
        "/stamp",
        status=200,
        json={"stamp": future},
        headers={
            "Date": "Fri, 31 Dec 2999 23:59:59 GMT",
            "Last-Modified": "Fri, 31 Dec 2999 23:59:59 GMT",
        },
    )
    semantic_runtime.clock.set(T_RUN)
    run_a = semantic_runtime.start_run("a19_stamp_flow", inputs=[], actor=OWNER)

    # Run B, later by the kernel clock: the service answers a time in the past.
    stub.on(
        "GET",
        "/stamp",
        status=200,
        json={"stamp": past},
        headers={
            "Date": "Thu, 01 Jan 1970 00:00:01 GMT",
            "Last-Modified": "Thu, 01 Jan 1970 00:00:01 GMT",
        },
    )
    t_run_b = T_RUN + 1_000_000
    semantic_runtime.clock.set(t_run_b)
    run_b = semantic_runtime.start_run("a19_stamp_flow", inputs=[], actor=OWNER)

    assert len(stub.requests) == 2

    # A19 rule 3: the service's timestamp is a value like any other — kept
    # verbatim as the output it is.
    for run, stamp in ((run_a, future), (run_b, past)):
        assert _status(run) == "succeeded"
        (output,) = run.outputs
        assert output.port == "stamp"
        assert output.value.json_text == f'"{stamp}"'

    # A19 rules 1 and 3: it never becomes a kernel timestamp — every time of
    # each run and of its trace is the injected clock's.
    for run, instant in ((run_a, T_RUN), (run_b, t_run_b)):
        shown = semantic_runtime.read_run(run.run_id)
        assert _us(shown.started_at) == instant
        assert _us(shown.ended_at) == instant
        trace = semantic_runtime.page_records(
            "node_execution", _equals("run_id", run.run_id), page_size=200
        ).records.node_executions
        assert [(e.node_id, _status(e)) for e in trace] == [("op", "succeeded")]
        assert _us(trace[0].started_at) == instant
        assert _us(trace[0].ended_at) == instant

    # A19 rule 3: the kernel orders its records only by the store's order —
    # newest first (A16 rule 6) — whatever the services said: run B, whose
    # service time is the earlier, is the newer record.
    runs = semantic_runtime.page_records("run", page_size=200).records.runs
    assert [run.run_id for run in runs] == [run_b.run_id, run_a.run_id]
    trace = semantic_runtime.page_records(
        "node_execution",
        {"filter_kind": "in_set", "field": "run_id", "values": sorted([run_a.run_id, run_b.run_id])},
        page_size=200,
    ).records.node_executions
    assert [e.run_id for e in trace] == [run_b.run_id, run_a.run_id]


def test_request_cannot_supply_time(semantic_runtime):
    """[witness: verification:kernel_a19_request_cannot_supply_time]

    A19 Required test 3: no operation schema has a field for the current time;
    a request adding one is refused as an unknown field.
    """
    owner_token = semantic_runtime.installation.owner_token
    author_token = semantic_runtime.installation.agent_token("author")
    missing_attempt = {
        "run_id": MISSING_MINTED_ID,
        "node_id": "n",
        "map_index": None,
        "attempt_number": 1,
    }

    # Every operation of the MCP surface catalogue (State 5), with a request
    # of its State 6 request model and a token of an actor the catalogue
    # lets call it, and the time field of the record it would write.
    catalogue = [
        ("issue_contract_version", author_token, {
            "slot_id": "a19_time_slot",
            "purpose": "A19 witness: request time",
            "inputs": [_port("x", "input", TEXT, "open")],
            "outputs": [_port("y", "output", TEXT)],
            "resource_bounds": _bounds(),
        }, "issued_at"),
        ("add_trial_case", author_token, {
            "contract_version_id": MISSING_CONTENT_ID,
            "inputs": [],
            "expected_outputs": None,
        }, "added_at"),
        ("submit_implementation", author_token, {
            "contract_version_id": MISSING_CONTENT_ID,
            "code": ECHO_CODE,
        }, "submitted_at"),
        ("try_implementation", author_token, {
            "implementation_id": MISSING_CONTENT_ID,
            "trial_case_ids": [],
        }, "executed_at"),
        ("capture_failed_execution", owner_token, {
            "execution": missing_attempt,
            "contract_version_id": MISSING_CONTENT_ID,
        }, "added_at"),
        ("roll_back_slot", owner_token, {
            "slot_id": "a19_missing_slot",
            "implementation_id": MISSING_CONTENT_ID,
        }, "activated_at"),
        ("propose_binding", author_token, {
            "service_id": "a19_absent",
            "operation_name": "get_stamp",
            "inputs": [],
            "outputs": [],
        }, "proposed_at"),
        ("accept_binding", owner_token, {"binding_id": MISSING_MINTED_ID}, "accepted_at"),
        ("compose_flow_version", author_token, {
            "flow_id": "a19_time_flow",
            "purpose": "A19 witness: request time",
            "inputs": [],
            "outputs": [],
            "nodes": [],
            "edges": [],
            "constants": [],
        }, "authored_at"),
        ("prove_flow_version", author_token, {"flow_version_id": MISSING_CONTENT_ID}, None),
        ("activate_flow_version", owner_token, {"flow_version_id": MISSING_CONTENT_ID}, "activated_at"),
        ("start_run", owner_token, {"flow_id": "a19_missing_flow", "inputs": []}, "started_at"),
        ("resume_run", owner_token, {"run_id": MISSING_MINTED_ID}, "resumed_at"),
        ("release_run", owner_token, {"run_id": MISSING_MINTED_ID}, "released_at"),
        ("decide_effect_approval", owner_token, {
            "approval_id": MISSING_MINTED_ID,
            "decision": "approve",
        }, "decided_at"),
        ("resolve_unknown_outcome", owner_token, {
            "attempt": missing_attempt,
            "resolution": "applied",
        }, "concluded_at"),
        ("cancel_run", owner_token, {"run_id": MISSING_MINTED_ID}, "ended_at"),
        ("grant_standing_approval", owner_token, {
            "flow_id": "a19_missing_flow",
            "node_id": "n",
        }, "granted_at"),
        ("revoke_standing_approval", owner_token, {"grant_id": MISSING_MINTED_ID}, "revoked_at"),
        ("get_slot", owner_token, {"slot_id": "a19_missing_slot"}, None),
        ("get_repair_view", owner_token, {
            "slot_id": "a19_missing_slot",
            "page_size": None,
            "continuation_token": None,
        }, None),
        ("get_contract_version", owner_token, {"contract_version_id": MISSING_CONTENT_ID}, None),
        ("get_implementation", owner_token, {"implementation_id": MISSING_CONTENT_ID}, None),
        ("get_binding", owner_token, {"binding_id": MISSING_MINTED_ID}, None),
        ("get_flow", owner_token, {"flow_id": "a19_missing_flow"}, None),
        ("get_flow_version", owner_token, {"flow_version_id": MISSING_CONTENT_ID}, None),
        ("get_run", owner_token, {"run_id": MISSING_MINTED_ID}, None),
        ("list_records", owner_token, {
            "record_type": "run",
            "record_filter": None,
            "page_size": None,
            "continuation_token": None,
        }, None),
        ("read_spooled_file", owner_token, {
            "file": {
                "run_id": MISSING_MINTED_ID,
                "producer_node_id": "n",
                "map_index": None,
                "attempt_number": 1,
                "producer_port": "y",
                "list_index": None,
            }
        }, None),
        ("read_fixture_file", owner_token, {"value_id": MISSING_CONTENT_ID}, None),
    ]
    time_value = {"epoch_us": 4_102_444_800_000_000}  # 2100-01-01T00:00:00Z

    for operation, token, request, record_time_field in catalogue:
        time_fields = ["now", "current_time", "kernel_now"]
        if record_time_field is not None:
            time_fields.append(record_time_field)
        for field in time_fields:
            # A19 rule 1: a request never supplies the current time; A16
            # rule 4: an unknown field is refused at the schema step.
            with pytest.raises(Exception) as exc:
                semantic_runtime.mcp_request(
                    operation, dict(request, **{field: time_value}), token=token
                )
            assert exc.value.code == "invalid_request", (operation, field)

    # A refusal writes nothing: the slot and the flow the creating requests
    # named do not exist.
    with pytest.raises(Exception) as exc:
        semantic_runtime.read_slot("a19_time_slot")
    assert exc.value.code == "unknown_reference"
    with pytest.raises(Exception) as exc:
        semantic_runtime.active_flow_version("a19_time_flow")
    assert exc.value.code == "unknown_reference"

    # Control: each request without the added field passes the schema step —
    # it is answered, or refused by a later check — so the refusals above are
    # the added field's.
    for operation, token, request, _ in catalogue:
        try:
            semantic_runtime.mcp_request(operation, request, token=token)
        except Exception as exc:  # a later check's refusal
            assert exc.code != "invalid_request", operation

    # And the creating requests recorded their times from the kernel clock,
    # not from anything sent.
    history = semantic_runtime.read_slot("a19_time_slot")
    assert _us(history.slot.created_at) != time_value["epoch_us"]


def test_monotonic_reading_never_stored(semantic_runtime):
    """[witness: verification:kernel_a19_monotonic_reading_never_stored]

    A19 Required test 4: with the clock module's monotonic source fixed to a
    sentinel value, a run with a sandbox execution and an HTTP request leaves
    the sentinel in no stored record.
    """
    stub = _stamp_service(semantic_runtime, "a19_mono")
    stub.on("GET", "/stamp", status=200, json={"stamp": "answered"})

    # A reading of the monotonic source in nanoseconds; distinctive in every
    # unit and encoding searched below.
    sentinel_ns = 918_273_645_546_372_819
    semantic_runtime.clock.fix_monotonic(sentinel_ns)
    semantic_runtime.clock.set(T_ISSUE)

    contract_version_id = semantic_runtime.issue_contract_version(
        "a19_mono_slot",
        purpose="A19 witness: monotonic readings",
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
    binding_id = _accepted_stamp_binding(semantic_runtime, "a19_mono")

    composed = semantic_runtime.compose_flow_version(
        "a19_mono_flow",
        purpose="A19 witness: monotonic readings",
        inputs=[_port("x", "input", TEXT, "open")],
        outputs=[_port("y", "output", TEXT), _port("stamp", "output", TEXT)],
        nodes=[
            _function_node("f", contract_version_id),
            _operation_node("op", binding_id),
        ],
        edges=[
            _edge("", "x", "f", "x"),
            _edge("f", "y", "", "y"),
            _edge("op", "stamp", "", "stamp"),
        ],
        constants=[],
    )
    assert composed.proof.proven is True
    semantic_runtime.activate_flow_version(composed.flow_version.flow_version_id, actor=OWNER)

    semantic_runtime.clock.set(T_RUN)
    run = semantic_runtime.start_run("a19_mono_flow", inputs=[_json("x", '"a"')], actor=OWNER)

    # The run made one sandbox execution and one HTTP request, both bounded by
    # deadlines of the monotonic source (A19 rule 2).
    assert _status(run) == "succeeded"
    trace = semantic_runtime.page_records(
        "node_execution", _equals("run_id", run.run_id), page_size=200
    ).records.node_executions
    assert sorted((e.node_id, _status(e)) for e in trace) == [
        ("f", "succeeded"),
        ("op", "succeeded"),
    ]
    assert len(stub.requests) == 1

    # A19 rule 1: the recorded times are the kernel clock's.
    assert _us(run.started_at) == T_RUN
    assert all(_us(e.started_at) == T_RUN and _us(e.ended_at) == T_RUN for e in trace)

    # A19 rule 2: a monotonic reading is never stored — in any unit, as text
    # or as an 8-byte integer.
    dump = semantic_runtime.store_dump()
    for reading in (sentinel_ns, sentinel_ns // 1_000, sentinel_ns // 1_000_000):
        assert str(reading).encode("ascii") not in dump, reading
        assert reading.to_bytes(8, "big") not in dump, reading
        assert reading.to_bytes(8, "little") not in dump, reading
