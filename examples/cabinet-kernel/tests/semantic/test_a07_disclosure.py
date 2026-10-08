"""Witness tests for accepted decision A07 (02_rules_flows.md).

A disclosure class only rises along a flow — at proof time and at run time —
and an agent receives a `personal_data` value only as its digest and class.
Each test carries the witness name its Required test declares.

The Factory project supplies the ``semantic_runtime`` pytest fixture. It binds
these scenarios to the generated public operations of State 5 — named here by
their operation names, with arguments shaped as the State 6 models — without
changing the assertions below. Each test gets a fresh, empty kernel store.

Fixture surface used here:

- ``issue_contract_version(slot_id, purpose, inputs, outputs)`` ->
  contract_version_id; ports are dicts with the fields of Port (M01); the
  fixture supplies resource bounds within the installation's ceilings and acts
  as an author agent;
- ``add_trial_case(contract_version_id, inputs, expected_outputs)`` ->
  ShownAddedTrialCase and ``submit_implementation(contract_version_id,
  code)`` -> ShownSubmission, as an author agent, to admit and activate each
  function a run executes;
- ``compose_flow_version(flow_id, purpose, inputs, outputs, nodes, edges,
  constants)`` -> ComposedFlowVersion, as an author agent;
- ``propose_binding(service_id, operation_name, inputs, outputs)`` ->
  OperationBinding (M11), as an author agent; ``accept_binding(binding_id)``
  -> OperationBinding, as the owner;
- ``activate_flow_version(flow_version_id)`` -> FlowActivation and
  ``start_run(flow_id, inputs)`` -> ShownRun, as the owner; run inputs are
  RequestJsonValue dicts;
- ``read_run(run_id, actor=...)`` -> ShownRun and ``page_records(record_type,
  record_filter, page_size, actor=...)`` -> RecordPageAnswer (node executions,
  approvals); the actor is passed explicitly, since the answer is masked for an
  agent (A07 rules 4-5).

Capabilities used here (operation nodes need an accepted binding, which needs a
manifest record and a selected instance):

- ``stub_service()`` -> a loopback HTTP stub whose ``base_url`` is the
  instance's ``api_base_url``; ``stub.on(method, path, status, json)`` sets
  its answer and ``stub.requests`` lists what reached it;
- ``manifest.write_record(service_id, record)`` -> the service's record at
  the configured revision, written before the kernel starts;
- ``installation.select_instance(service_id, instance_name)``.
"""

TEXT = '{"type":"string"}'
NUMBER = '{"type":"integer"}'

OWNER = {"kind": "owner", "agent_name": None}
AUTHOR = {"kind": "agent", "agent_name": "author"}

RELAY_CODE = 'def run(inputs):\n    return {"y": inputs["x"].upper()}\n'
LENGTH_CODE = 'def run(inputs):\n    return {"n": len(inputs["x"])}\n'
SEVEN_CODE = 'def run(inputs):\n    return {"y": 7}\n'
PASS_CODE = 'def run(inputs):\n    return {"y": inputs["x"]}\n'


def _value(field):
    return getattr(field, "value", field)


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


def _contract(semantic_runtime, slot_id, inputs, outputs):
    return semantic_runtime.issue_contract_version(
        slot_id,
        purpose=f"A07 witness: {slot_id}",
        inputs=inputs,
        outputs=outputs,
    )


def _json(port, json_text):
    return {"payload_kind": "json", "port": port, "json_text": json_text}


def _admitted(semantic_runtime, contract_version_id, code, inputs, expected_outputs):
    """One trial case, then the code submitted: admitted and activated (A04)."""
    semantic_runtime.add_trial_case(
        contract_version_id, inputs=inputs, expected_outputs=expected_outputs
    )
    submission = semantic_runtime.submit_implementation(contract_version_id, code)
    assert _value(submission.verdict.verdict) == "admitted"
    assert submission.activation is not None
    return submission.implementation.implementation_id


def _node(node_id, contract_version_id):
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
    return {
        "from_node": from_node,
        "from_port": from_port,
        "to_node": to_node,
        "to_port": to_port,
        "guard": None,
    }


def _edge_key(failure):
    edge = failure.edge
    return (edge.from_node, edge.from_port, edge.to_node, edge.to_port)


def _capability(name, route, effect_class):
    return {
        "name": name,
        "exposed_as": {"http_api": [route]},
        "effect_class": effect_class,
        "idempotency_key": None,
    }


def _service(semantic_runtime, service_id, capabilities):
    """The service's manifest record with one selected loopback instance.

    Called before any operation, so it shapes the kernel's first start.
    """
    stub = semantic_runtime.stub_service()
    semantic_runtime.manifest.write_record(
        service_id,
        {
            "service": service_id,
            "capabilities": capabilities,
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


def _accepted(semantic_runtime, service_id, operation_name, inputs, outputs):
    binding = semantic_runtime.propose_binding(
        service_id, operation_name, inputs=inputs, outputs=outputs
    )
    accepted = semantic_runtime.accept_binding(binding.binding_id)
    assert _value(accepted.status) == "accepted"
    return binding.binding_id


def _of_run(run_id):
    return {"filter_kind": "equals", "field": "run_id", "value": run_id}


def _output(run, port):
    """The ShownItem a run's answer gives for one produced flow output."""
    [output] = [o for o in run.outputs if o.port == port]
    assert _value(output.output_kind) == "produced"
    return output.value


def _items(shown_ports, port):
    [shown] = [p for p in shown_ports if p.port == port]
    return list(shown.items)


def _item(shown_ports, port):
    [item] = _items(shown_ports, port)
    return item


def _trace(semantic_runtime, run_id, actor):
    page = semantic_runtime.page_records(
        "node_execution", _of_run(run_id), page_size=200, actor=actor
    )
    return {e.node_id: e for e in page.records.node_executions}


def _assert_content(item, json_text, disclosure_class):
    assert _value(item.shown_kind) == "content"
    assert item.json_text == json_text
    assert _value(item.disclosure_class) == disclosure_class
    assert item.value_id


def _assert_digest(item, disclosure_class):
    # A07 rule 4: digest and class only, no `value_id`.
    assert _value(item.shown_kind) == "value_digest"
    assert item.value_digest
    assert _value(item.disclosure_class) == disclosure_class
    assert getattr(item, "value_id", None) is None
    assert getattr(item, "json_text", None) is None


def _length_flow(semantic_runtime, flow_id, contract_version_id, input_class):
    """Flow input `name` of class `input_class` -> f -> flow output `length`."""
    composed = semantic_runtime.compose_flow_version(
        flow_id,
        purpose=f"A07 witness: {flow_id}",
        inputs=[_port("name", "input", TEXT, input_class)],
        outputs=[_port("length", "output", NUMBER)],
        nodes=[_node("f", contract_version_id)],
        edges=[_edge("", "name", "f", "x"), _edge("f", "n", "", "length")],
        constants=[],
    )
    assert composed.proof.proven is True
    semantic_runtime.activate_flow_version(composed.flow_version.flow_version_id)
    return composed


def test_function_output_takes_max_input_class(semantic_runtime):
    """[witness: verification:kernel_a07_function_output_takes_max_input_class]

    A07 Required test 1: a function that receives a `personal_data` value and
    returns an integer yields an output of class `personal_data`.
    """
    length_fn = _contract(
        semantic_runtime,
        "name_length",
        inputs=[_port("x", "input", TEXT, "personal_data")],
        outputs=[_port("n", "output", NUMBER)],
    )
    _admitted(
        semantic_runtime,
        length_fn,
        LENGTH_CODE,
        inputs=[_json("x", '"Ada"')],
        expected_outputs=[_json("n", "3")],
    )
    _length_flow(semantic_runtime, "a07_private_length", length_fn, "personal_data")

    run = semantic_runtime.start_run("a07_private_length", [_json("name", '"Ada Lovelace"')])
    assert _value(run.status) == "succeeded"
    # A07 rule 3: a function output takes the highest class its execution
    # actually received; the owner receives the content (A07 rule 4).
    owner_run = semantic_runtime.read_run(run.run_id, actor=OWNER)
    _assert_content(_output(owner_run, "length"), "12", "personal_data")
    execution = _trace(semantic_runtime, run.run_id, OWNER)["f"]
    _assert_content(_item(execution.inputs, "x"), '"Ada Lovelace"', "personal_data")
    _assert_content(_item(execution.outputs, "n"), "12", "personal_data")

    # Control: the same function fed an `open` value yields an `open` output,
    # so the class above comes from the value received, not from the class
    # the contract's input accepts.
    _length_flow(semantic_runtime, "a07_open_length", length_fn, "open")
    control = semantic_runtime.start_run("a07_open_length", [_json("name", '"Ada Lovelace"')])
    assert _value(control.status) == "succeeded"
    _assert_content(_output(control, "length"), "12", "open")


def _people_service(semantic_runtime):
    return _service(
        semantic_runtime,
        "people",
        [_capability("lookup", "GET /people", "read")],
    )


def _lookup(semantic_runtime, output_class):
    """A `read` binding of `people.lookup` declaring `output_class` on `person`."""
    return _accepted(
        semantic_runtime,
        "people",
        "lookup",
        inputs=[_port("q", "input", TEXT, "open")],
        outputs=[_port("person", "output", TEXT, output_class)],
    )


def test_proof_refuses_class_above_accepted(semantic_runtime):
    """[witness: verification:kernel_a07_proof_refuses_class_above_accepted]

    A07 Required test 2: a path from a personal-data read through two functions
    into an input accepting `business_confidential` is refused by the proof.
    """
    _people_service(semantic_runtime)
    personal_lookup = _lookup(semantic_runtime, "personal_data")
    confidential_lookup = _lookup(semantic_runtime, "business_confidential")
    relay_fn = _contract(
        semantic_runtime,
        "relay",
        inputs=[_port("x", "input", TEXT, "personal_data")],
        outputs=[_port("y", "output", TEXT)],
    )
    sink_fn = _contract(
        semantic_runtime,
        "confidential_sink",
        inputs=[_port("x", "input", TEXT, "business_confidential")],
        outputs=[_port("y", "output", TEXT)],
    )

    def compose(flow_id, lookup):
        return semantic_runtime.compose_flow_version(
            flow_id,
            purpose=f"A07 witness: {flow_id}",
            inputs=[_port("query", "input", TEXT, "open")],
            outputs=[_port("out", "output", TEXT)],
            nodes=[
                _node("f1", relay_fn),
                _node("f2", relay_fn),
                _operation_node("lookup", lookup),
                _node("sink", sink_fn),
            ],
            edges=[
                _edge("", "query", "lookup", "q"),
                _edge("lookup", "person", "f1", "x"),
                _edge("f1", "y", "f2", "x"),
                _edge("f2", "y", "sink", "x"),
                _edge("sink", "y", "", "out"),
            ],
            constants=[],
        )

    # A07 rule 2: the read's output is `personal_data` as its binding
    # declares; each function's output is the highest class reaching its
    # inputs, so `personal_data` reaches f2.y. A05 rule 1 phase 8: that exceeds
    # the `business_confidential` sink.x accepts. f1.x and f2.x accept
    # `personal_data`, so the edge into sink.x is the first that fails.
    refused = compose("a07_class_above", personal_lookup)
    assert refused.proof.proven is False
    assert _value(refused.proof.failure.phase) == "disclosure"
    assert _edge_key(refused.proof.failure) == ("f2", "y", "sink", "x")

    # Control: the same path from a read declaring `business_confidential` is
    # proven, so the refusal comes from the class carried through both
    # functions.
    control = compose("a07_class_within", confidential_lookup)
    assert control.proof.proven is True
    assert control.proof.failure is None


def test_agent_gets_personal_data_as_digest(semantic_runtime):
    """[witness: verification:kernel_a07_agent_gets_personal_data_as_digest]

    A07 Required test 3: an agent reading that run receives digests and classes
    for the personal-data values and content for the rest; the owner receives
    all content.
    """
    stub = _people_service(semantic_runtime)
    stub.on("GET", "/people", status=200, json={"person": "Ada Lovelace"})
    lookup = _lookup(semantic_runtime, "personal_data")
    relay_fn = _contract(
        semantic_runtime,
        "relay",
        inputs=[_port("x", "input", TEXT, "personal_data")],
        outputs=[_port("y", "output", TEXT)],
    )
    length_fn = _contract(
        semantic_runtime,
        "name_length",
        inputs=[_port("x", "input", TEXT, "personal_data")],
        outputs=[_port("n", "output", NUMBER)],
    )
    _admitted(
        semantic_runtime,
        relay_fn,
        RELAY_CODE,
        inputs=[_json("x", '"ab"')],
        expected_outputs=[_json("y", '"AB"')],
    )
    _admitted(
        semantic_runtime,
        length_fn,
        LENGTH_CODE,
        inputs=[_json("x", '"ab"')],
        expected_outputs=[_json("n", "2")],
    )

    # The personal-data read through two functions into a flow output, and the
    # `open` query straight to another flow output.
    composed = semantic_runtime.compose_flow_version(
        "a07_masking",
        purpose="A07 witness: masking",
        inputs=[_port("query", "input", TEXT, "open")],
        outputs=[_port("length", "output", NUMBER), _port("query_echo", "output", TEXT)],
        nodes=[
            _node("f1", relay_fn),
            _node("f2", length_fn),
            _operation_node("lookup", lookup),
        ],
        edges=[
            _edge("", "query", "lookup", "q"),
            _edge("", "query", "", "query_echo"),
            _edge("lookup", "person", "f1", "x"),
            _edge("f1", "y", "f2", "x"),
            _edge("f2", "n", "", "length"),
        ],
        constants=[],
    )
    assert composed.proof.proven is True
    semantic_runtime.activate_flow_version(composed.flow_version.flow_version_id)
    run = semantic_runtime.start_run("a07_masking", [_json("query", '"ada"')])
    assert _value(run.status) == "succeeded"

    # The agent: the run's answer.
    agent_run = semantic_runtime.read_run(run.run_id, actor=AUTHOR)
    _assert_digest(_output(agent_run, "length"), "personal_data")
    _assert_content(_output(agent_run, "query_echo"), '"ada"', "open")

    # The agent: the trace. A07 rule 3: the binding output is
    # `personal_data`, and each function output the highest class it received.
    agent_trace = _trace(semantic_runtime, run.run_id, AUTHOR)
    _assert_content(_item(agent_trace["lookup"].inputs, "q"), '"ada"', "open")
    _assert_digest(_item(agent_trace["lookup"].outputs, "person"), "personal_data")
    _assert_digest(_item(agent_trace["f1"].inputs, "x"), "personal_data")
    _assert_digest(_item(agent_trace["f1"].outputs, "y"), "personal_data")
    _assert_digest(_item(agent_trace["f2"].inputs, "x"), "personal_data")
    _assert_digest(_item(agent_trace["f2"].outputs, "n"), "personal_data")

    # The owner receives all content.
    owner_run = semantic_runtime.read_run(run.run_id, actor=OWNER)
    _assert_content(_output(owner_run, "length"), "12", "personal_data")
    _assert_content(_output(owner_run, "query_echo"), '"ada"', "open")
    owner_trace = _trace(semantic_runtime, run.run_id, OWNER)
    _assert_content(_item(owner_trace["lookup"].inputs, "q"), '"ada"', "open")
    _assert_content(
        _item(owner_trace["lookup"].outputs, "person"), '"Ada Lovelace"', "personal_data"
    )
    _assert_content(_item(owner_trace["f1"].inputs, "x"), '"Ada Lovelace"', "personal_data")
    _assert_content(_item(owner_trace["f1"].outputs, "y"), '"ADA LOVELACE"', "personal_data")
    _assert_content(_item(owner_trace["f2"].inputs, "x"), '"ADA LOVELACE"', "personal_data")
    _assert_content(_item(owner_trace["f2"].outputs, "n"), "12", "personal_data")


def test_preview_hides_personal_data_from_agent(semantic_runtime):
    """[witness: verification:kernel_a07_preview_hides_personal_data_from_agent]

    A07 Required test 4: an agent reading the approval preview of such a node
    receives no personal-data value.
    """
    stub = _service(
        semantic_runtime,
        "notices",
        [_capability("notify", "POST /notices", "state-transition")],
    )
    stub.on("POST", "/notices", status=200, json={})
    notify = _accepted(
        semantic_runtime,
        "notices",
        "notify",
        inputs=[
            _port("name", "input", TEXT, "personal_data"),
            _port("topic", "input", TEXT, "open"),
        ],
        outputs=[],
    )

    def awaiting(flow_id, name_class):
        composed = semantic_runtime.compose_flow_version(
            flow_id,
            purpose=f"A07 witness: {flow_id}",
            inputs=[
                _port("name", "input", TEXT, name_class),
                _port("topic", "input", TEXT, "open"),
            ],
            outputs=[],
            nodes=[_operation_node("notify", notify)],
            edges=[
                _edge("", "name", "notify", "name"),
                _edge("", "topic", "notify", "topic"),
            ],
            constants=[],
        )
        assert composed.proof.proven is True
        semantic_runtime.activate_flow_version(composed.flow_version.flow_version_id)
        run = semantic_runtime.start_run(
            flow_id, [_json("name", '"Ada Lovelace"'), _json("topic", '"billing"')]
        )
        assert _value(run.status) == "awaiting_approval"
        [wait] = run.waiting
        assert wait.node_id == "notify"
        return run.run_id, wait.approval_id

    def approval(run_id, approval_id, actor):
        page = semantic_runtime.page_records(
            "approval", _of_run(run_id), page_size=200, actor=actor
        )
        [shown] = page.records.approvals
        assert shown.approval_id == approval_id
        return shown

    run_id, approval_id = awaiting("a07_notice_private", "personal_data")
    assert [r for r in stub.requests if r.target == "/notices"] == []

    # A07 rule 4: one input is `personal_data`, so the agent gets no built
    # request, only the request's digest, and that input as digest and class.
    agent_view = approval(run_id, approval_id, AUTHOR)
    assert agent_view.preview.request is None
    assert agent_view.request_digest
    _assert_digest(_item(agent_view.preview.inputs, "name"), "personal_data")
    _assert_content(_item(agent_view.preview.inputs, "topic"), '"billing"', "open")

    # The owner receives every value: the built request and both inputs.
    owner_view = approval(run_id, approval_id, OWNER)
    assert owner_view.request_digest == agent_view.request_digest
    request = owner_view.preview.request
    assert request is not None
    assert _value(request.method) == "POST"
    # A09 rule 2: a JSON object body keyed by port name, canonical.
    assert _value(request.body.body_kind) == "json"
    assert request.body.json_text == '{"name":"Ada Lovelace","topic":"billing"}'
    _assert_content(_item(owner_view.preview.inputs, "name"), '"Ada Lovelace"', "personal_data")
    _assert_content(_item(owner_view.preview.inputs, "topic"), '"billing"', "open")

    # Control: the same node fed `business_confidential` instead shows the
    # agent the built request and the content, so the masking above is
    # decided by the `personal_data` class.
    run_id, approval_id = awaiting("a07_notice_confidential", "business_confidential")
    control = approval(run_id, approval_id, AUTHOR)
    assert control.preview.request is not None
    assert control.preview.request.body.json_text == '{"name":"Ada Lovelace","topic":"billing"}'
    _assert_content(
        _item(control.preview.inputs, "name"), '"Ada Lovelace"', "business_confidential"
    )


def test_inputless_function_output_open(semantic_runtime):
    """[witness: verification:kernel_a07_inputless_function_output_open]

    A07 Required test 5: a function node with no inputs yields an output of
    class `open`, at proof time and at run time.
    """
    seven_fn = _contract(
        semantic_runtime,
        "seven",
        inputs=[],
        outputs=[_port("y", "output", NUMBER)],
    )
    gate_fn = _contract(
        semantic_runtime,
        "open_gate",
        inputs=[_port("x", "input", NUMBER, "open")],
        outputs=[_port("y", "output", NUMBER)],
    )
    _admitted(semantic_runtime, seven_fn, SEVEN_CODE, inputs=[], expected_outputs=[_json("y", "7")])
    _admitted(
        semantic_runtime,
        gate_fn,
        PASS_CODE,
        inputs=[_json("x", "1")],
        expected_outputs=[_json("y", "1")],
    )

    # At proof time (A07 rule 2): `open` for a function with no inputs, so the
    # edge into gate.x, which accepts only `open`, passes phase 8.
    composed = semantic_runtime.compose_flow_version(
        "a07_inputless",
        purpose="A07 witness: inputless function",
        inputs=[],
        outputs=[_port("out", "output", NUMBER)],
        nodes=[_node("gate", gate_fn), _node("k", seven_fn)],
        edges=[_edge("k", "y", "gate", "x"), _edge("gate", "y", "", "out")],
        constants=[],
    )
    assert composed.proof.proven is True
    assert composed.proof.failure is None

    # Control: a `business_confidential` value into the same gate.x is refused
    # in phase 8, so the proof above did check the class reaching it.
    control = semantic_runtime.compose_flow_version(
        "a07_inputless_control",
        purpose="A07 witness: inputless function control",
        inputs=[_port("x", "input", NUMBER, "business_confidential")],
        outputs=[_port("out", "output", NUMBER)],
        nodes=[_node("gate", gate_fn)],
        edges=[_edge("", "x", "gate", "x"), _edge("gate", "y", "", "out")],
        constants=[],
    )
    assert control.proof.proven is False
    assert _value(control.proof.failure.phase) == "disclosure"
    assert _edge_key(control.proof.failure) == ("", "x", "gate", "x")

    # At run time (A07 rule 3, M01): the output of `k` is `open`, and so is
    # what reaches the flow output.
    semantic_runtime.activate_flow_version(composed.flow_version.flow_version_id)
    run = semantic_runtime.start_run("a07_inputless", [])
    assert _value(run.status) == "succeeded"
    _assert_content(_output(run, "out"), "7", "open")
    trace = _trace(semantic_runtime, run.run_id, OWNER)
    assert list(trace["k"].inputs) == []
    _assert_content(_item(trace["k"].outputs, "y"), "7", "open")
