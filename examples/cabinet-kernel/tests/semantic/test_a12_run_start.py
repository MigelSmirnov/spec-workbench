"""Witness tests for accepted decision A12 (02_rules_runs.md).

A run starts from its flow's active version only after the start checks of
rule 1 pass, in their order, and otherwise is refused without a run; once
started, it pins the flow version and the implementation of every function
node, and nothing recorded later changes what it executes. Each test carries
the witness name its Required test declares.

The Factory project supplies the ``semantic_runtime`` pytest fixture. It binds
these scenarios to the generated public operations of State 5 — named here by
their operation names, with arguments shaped as the State 6 models — without
changing the assertions below. Each test gets a fresh, empty kernel store; the
installation starts with the owner, agent ``author`` and agent ``helper``, no
service selected and no credential.

Fixture surface used here:

- ``issue_contract_version(slot_id, purpose, inputs, outputs)`` ->
  contract_version_id; ``add_trial_case(contract_version_id, inputs)`` ->
  ShownAddedTrialCase; ``submit_implementation(contract_version_id, code)`` ->
  ShownSubmission, all as agent ``author`` — an admitted submission activates
  its implementation (A04 rule 4), which is how a function node gets a current
  activation;
- ``propose_binding(service_id, operation_name, inputs, outputs)`` ->
  OperationBinding, as agent ``author``; ``accept_binding(binding_id)``, as the
  owner;
- ``compose_flow_version(flow_id, purpose, inputs, outputs, nodes, edges,
  constants)`` -> ComposedFlowVersion, as agent ``author``;
  ``activate_flow_version(flow_version_id)`` -> FlowActivation, as the owner;
- ``start_run(flow_id, inputs)`` -> ShownRun and
  ``continue_after_approval(approval_id, decision)`` -> ShownRun, as the owner;
  inputs are RequestJsonValue dicts;
- ``page_records(record_type, record_filter, page_size)`` -> RecordPageAnswer:
  ``run`` (no run exists) and ``node_execution`` (the trace, newest first);
- capabilities: ``manifest.write_record``, ``installation.select_instance``,
  ``installation.set_credential``, ``stub_service`` and ``clock.advance``.
"""

import pytest

NUMBER = '{"type":"integer"}'
NUMBERS = '{"type":"array","items":{"type":"number"}}'

# A20 rule 1, release v1
STORED_VALUE_BYTES_MAX = 1048576

SERVICE = "ledger"
INSTANCE = "rig"
CREDENTIAL_HEADER = "X-Api-Key"
CREDENTIAL = "a12-canary-credential-31d0"

# Python implementations, as A03 rule 3 shapes them.
COPY_N = "def run(inputs):\n    return {'y': inputs['n']}\n"
COPY_X = "def run(inputs):\n    return {'y': inputs['x']}\n"
ADD_ONE = "def run(inputs):\n    return {'y': inputs['x'] + 1}\n"
ADD_HUNDRED = "def run(inputs):\n    return {'y': inputs['x'] + 100}\n"


def _port(name, direction, schema, disclosure_class=None, cardinality="one"):
    return {
        "name": name,
        "direction": direction,
        "value_schema": schema,
        "carriage": "value",
        "media_type": None,
        "cardinality": cardinality,
        "disclosure_class": disclosure_class,
    }


def _value(port, json_text):
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
    """A flow input or output endpoint has the empty node id (A05 rule 2)."""
    return {
        "from_node": from_node,
        "from_port": from_port,
        "to_node": to_node,
        "to_port": to_port,
        "guard": None,
    }


def _enum(value):
    return getattr(value, "value", value)


def _contract(semantic_runtime, slot_id, inputs, outputs, case_inputs):
    """A contract version with one authored trial case (A04 rule 3: an empty
    corpus admits nothing)."""
    contract_version_id = semantic_runtime.issue_contract_version(
        slot_id,
        purpose=f"A12 witness: {slot_id}",
        inputs=inputs,
        outputs=outputs,
    )
    semantic_runtime.add_trial_case(contract_version_id, inputs=case_inputs)
    return contract_version_id


def _admit(semantic_runtime, contract_version_id, code):
    """Submit code; admitted, it becomes the current activation (A04 rule 4)."""
    submission = semantic_runtime.submit_implementation(contract_version_id, code)
    assert _enum(submission.verdict.verdict) == "admitted"
    assert submission.activation is not None
    return submission.implementation.implementation_id


def _x_to_y(semantic_runtime, slot_id):
    """A contract version of one integer input `x` and one integer output `y`."""
    return _contract(
        semantic_runtime,
        slot_id,
        inputs=[_port("x", "input", NUMBER, "open")],
        outputs=[_port("y", "output", NUMBER)],
        case_inputs=[_value("x", "1")],
    )


def _runs_of(semantic_runtime, flow_version_id):
    page = semantic_runtime.page_records(
        "run",
        {"filter_kind": "equals", "field": "flow_version_id", "value": flow_version_id},
        page_size=200,
    )
    return page.records.runs


def _trace(semantic_runtime, run_id):
    """The run's NodeExecutions in store order (pages come newest first)."""
    page = semantic_runtime.page_records(
        "node_execution",
        {"filter_kind": "equals", "field": "run_id", "value": run_id},
        page_size=200,
    )
    return list(reversed(page.records.node_executions))


def _only_record(trace, node_id):
    records = [record for record in trace if record.node_id == node_id]
    assert len(records) == 1
    return records[0]


def _output(run, port):
    (output,) = [output for output in run.outputs if output.port == port]
    return output


def test_start_refused_without_run(semantic_runtime):
    """[witness: verification:kernel_a12_start_refused_without_run]

    A12 Required test 1: a run whose flow has no active version, or whose input
    misses a port, or whose function node has no current activation, is
    refused and no run exists.
    """
    copy = _x_to_y(semantic_runtime, "a12_copy")
    _admit(semantic_runtime, copy, COPY_X)

    # Two flow inputs `p` and `q`, each copied to a flow output.
    def compose(flow_id, contract_version_id):
        return semantic_runtime.compose_flow_version(
            flow_id,
            purpose=f"A12 witness: {flow_id}",
            inputs=[
                _port("p", "input", NUMBER, "open"),
                _port("q", "input", NUMBER, "open"),
            ],
            outputs=[_port("out_p", "output", NUMBER), _port("out_q", "output", NUMBER)],
            nodes=[
                _function_node("a", contract_version_id),
                _function_node("b", contract_version_id),
            ],
            edges=[
                _edge("", "p", "a", "x"),
                _edge("", "q", "b", "x"),
                _edge("a", "y", "", "out_p"),
                _edge("b", "y", "", "out_q"),
            ],
            constants=[],
        )

    both = [_value("p", "1"), _value("q", "2")]

    # No active version: composed and proven, never activated.
    inactive = compose("a12_inactive", copy)
    assert inactive.proof.proven is True
    with pytest.raises(Exception) as exc:
        semantic_runtime.start_run("a12_inactive", inputs=both)
    # State 5 runs.start_run: `refused` naming the first failing start check.
    assert exc.value.code == "refused"
    assert len(_runs_of(semantic_runtime, inactive.flow_version.flow_version_id)) == 0

    # An input that misses a port.
    active = compose("a12_active", copy)
    semantic_runtime.activate_flow_version(active.flow_version.flow_version_id)
    with pytest.raises(Exception) as exc:
        semantic_runtime.start_run("a12_active", inputs=[_value("p", "1")])
    assert exc.value.code == "refused"
    assert len(_runs_of(semantic_runtime, active.flow_version.flow_version_id)) == 0

    # A function node whose contract version has no current activation: the
    # proof only asks that the contract version exists (A05 rule 1 phase 1),
    # so the version is proven and active, and only the start check refuses.
    unserved = _x_to_y(semantic_runtime, "a12_unserved")
    unserved_flow = compose("a12_unserved_flow", unserved)
    assert unserved_flow.proof.proven is True
    semantic_runtime.activate_flow_version(unserved_flow.flow_version.flow_version_id)
    with pytest.raises(Exception) as exc:
        semantic_runtime.start_run("a12_unserved_flow", inputs=both)
    assert exc.value.code == "refused"
    assert len(_runs_of(semantic_runtime, unserved_flow.flow_version.flow_version_id)) == 0

    # Control: the same requests start a run once the missing piece exists, so
    # each refusal above came from its own start check.
    run = semantic_runtime.start_run("a12_active", inputs=both)
    assert _enum(run.status) == "succeeded"
    (listed,) = _runs_of(semantic_runtime, active.flow_version.flow_version_id)
    assert listed.run_id == run.run_id

    _admit(semantic_runtime, unserved, COPY_X)
    served = semantic_runtime.start_run("a12_unserved_flow", inputs=both)
    assert _enum(served.status) == "succeeded"
    (listed,) = _runs_of(semantic_runtime, unserved_flow.flow_version.flow_version_id)
    assert listed.run_id == served.run_id


def test_pins_survive_later_records(semantic_runtime):
    """[witness: verification:kernel_a12_pins_survive_later_records]

    A12 Required test 2: a run started before a new activation, a new flow
    activation or a new binding executes, to the end, the flow version and
    implementations it pinned at start, including after a long wait for
    approval.
    """
    stub = semantic_runtime.stub_service()
    stub.on("POST", "/entries", json={"y": 7})
    semantic_runtime.manifest.write_record(
        SERVICE,
        {
            "service": SERVICE,
            "capabilities": [
                {
                    "name": "post_entry",
                    "exposed_as": {"http_api": ["POST /entries"]},
                    "effect_class": "state-transition",
                    "idempotency_key": None,
                }
            ],
            "instances": [
                {
                    "instance_name": INSTANCE,
                    "api_base_url": stub.base_url,
                    "required_headers": None,
                    "instance_class": "disposable_rig",
                }
            ],
        },
    )
    semantic_runtime.installation.select_instance(SERVICE, INSTANCE)
    semantic_runtime.installation.set_credential(SERVICE, CREDENTIAL_HEADER, CREDENTIAL)

    prepare = _x_to_y(semantic_runtime, "a12_prepare")
    _admit(semantic_runtime, prepare, COPY_X)
    finish = _x_to_y(semantic_runtime, "a12_finish")
    finish_before = _admit(semantic_runtime, finish, ADD_ONE)

    def accepted_binding(input_class):
        proposed = semantic_runtime.propose_binding(
            SERVICE,
            "post_entry",
            inputs=[_port("x", "input", NUMBER, input_class)],
            outputs=[_port("y", "output", NUMBER, "open")],
        )
        return semantic_runtime.accept_binding(proposed.binding_id).binding_id

    def compose(binding_id):
        # x -> a (function) -> b (operation, state-transition) -> c (function)
        # -> out; `c` executes only after the owner approves `b`.
        composed = semantic_runtime.compose_flow_version(
            "a12_pinned",
            purpose="A12 witness: pins",
            inputs=[_port("x", "input", NUMBER, "open")],
            outputs=[_port("out", "output", NUMBER)],
            nodes=[
                _function_node("a", prepare),
                _operation_node("b", binding_id),
                _function_node("c", finish),
            ],
            edges=[
                _edge("", "x", "a", "x"),
                _edge("a", "y", "b", "x"),
                _edge("b", "y", "c", "x"),
                _edge("c", "y", "", "out"),
            ],
            constants=[],
        )
        assert composed.proof.proven is True
        semantic_runtime.activate_flow_version(composed.flow_version.flow_version_id)
        return composed.flow_version.flow_version_id

    binding_before = accepted_binding("open")
    version_before = compose(binding_before)

    run = semantic_runtime.start_run("a12_pinned", inputs=[_value("x", "1")])
    assert _enum(run.status) == "awaiting_approval"
    assert run.flow_version_id == version_before
    (wait,) = run.waiting
    assert wait.node_id == "b"
    assert _enum(wait.reason) == "owner_approval"

    # While the run waits: a new activation of `c`'s contract version, a new
    # accepted binding for the same operation, and a new flow version pinning
    # it, activated by the owner; then a long wait.
    finish_after = _admit(semantic_runtime, finish, ADD_HUNDRED)
    assert finish_after != finish_before
    binding_after = accepted_binding("business_confidential")
    assert binding_after != binding_before
    version_after = compose(binding_after)
    assert version_after != version_before
    semantic_runtime.clock.advance(days=30)

    # A12 rule 2: the run executes, to the end, what it pinned at start.
    ended = semantic_runtime.continue_after_approval(wait.approval_id, "approve")
    assert _enum(ended.status) == "succeeded"
    assert ended.flow_version_id == version_before
    produced = _output(ended, "out")
    assert produced.output_kind == "produced"
    assert produced.value.json_text == "8"  # the service's 7, plus 1 by `c`

    trace = _trace(semantic_runtime, run.run_id)
    sent = _only_record(trace, "b")
    assert _enum(sent.status) == "succeeded"
    assert sent.executed.binding_id == binding_before
    finished = _only_record(trace, "c")
    assert _enum(finished.status) == "succeeded"
    assert finished.executed.implementation_id == finish_before

    # Control: a run started after those records executes the new version, the
    # new binding and the new implementation, so the result above is the pin,
    # not a later record left unread.
    later = semantic_runtime.start_run("a12_pinned", inputs=[_value("x", "1")])
    assert later.flow_version_id == version_after
    (later_wait,) = later.waiting
    later_ended = semantic_runtime.continue_after_approval(later_wait.approval_id, "approve")
    assert _enum(later_ended.status) == "succeeded"
    assert _output(later_ended, "out").value.json_text == "107"
    later_trace = _trace(semantic_runtime, later.run_id)
    assert _only_record(later_trace, "b").executed.binding_id == binding_after
    assert _only_record(later_trace, "c").executed.implementation_id == finish_after


def test_start_inputs_exact_and_valid(semantic_runtime):
    """[witness: verification:kernel_a12_start_inputs_exact_and_valid]

    A12 Required test 4: a start whose request supplies a port the flow does
    not declare, or a value that misfits its port's schema, or a `many` value
    that is not a JSON array of fitting elements, or a value above
    `stored_value_bytes_max`, is refused and no run exists.
    """
    take = _contract(
        semantic_runtime,
        "a12_take",
        inputs=[
            _port("big", "input", NUMBERS, "open"),
            _port("n", "input", NUMBER, "open"),
            _port("ns", "input", NUMBER, "open", cardinality="many"),
        ],
        outputs=[_port("y", "output", NUMBER)],
        case_inputs=[_value("big", "[]"), _value("n", "1"), _value("ns", "[1]")],
    )
    _admit(semantic_runtime, take, COPY_N)
    composed = semantic_runtime.compose_flow_version(
        "a12_inputs",
        purpose="A12 witness: inputs",
        inputs=[
            _port("big", "input", NUMBERS, "open"),
            _port("n", "input", NUMBER, "open"),
            _port("ns", "input", NUMBER, "open", cardinality="many"),
        ],
        outputs=[_port("out", "output", NUMBER)],
        nodes=[_function_node("t", take)],
        edges=[
            _edge("", "big", "t", "big"),
            _edge("", "n", "t", "n"),
            _edge("", "ns", "t", "ns"),
            _edge("t", "y", "", "out"),
        ],
        constants=[],
    )
    flow_version_id = composed.flow_version.flow_version_id
    semantic_runtime.activate_flow_version(flow_version_id)

    valid = {"big": "[1.5]", "n": "3", "ns": "[1,2]"}

    def inputs(**changed):
        values = dict(valid, **changed)
        return [_value(port, text) for port, text in sorted(values.items())]

    # The text is 5 bytes per element, within the request bound of A16 rule 4;
    # its canonical form writes 1e20 as 100000000000000000000 (RFC 8785), 22
    # bytes per element, so the value itself is above the ceiling.
    expanding = "[" + ",".join(["1e20"] * 200000) + "]"
    assert len(expanding.encode("utf-8")) <= STORED_VALUE_BYTES_MAX
    assert 22 * 200000 > STORED_VALUE_BYTES_MAX

    refused_starts = [
        # A12 rule 1: the request supplies exactly the flow's input ports.
        inputs(extra="1"),
        # each value fits its port's schema ...
        inputs(n='"three"'),
        # ... for a `many` port, a JSON array ...
        inputs(ns="2"),
        # ... whose every element fits it ...
        inputs(ns='[1,"two"]'),
        # ... and then is within `stored_value_bytes_max`.
        inputs(big=expanding),
    ]
    for request in refused_starts:
        with pytest.raises(Exception) as exc:
            semantic_runtime.start_run("a12_inputs", inputs=request)
        assert exc.value.code == "refused"
        assert len(_runs_of(semantic_runtime, flow_version_id)) == 0

    # A value whose text is itself above the ceiling is refused by the
    # surface's request bound, before any start check (A16 rules 1 and 4:
    # a field over its bound is `invalid_request`); no run exists either.
    oversized = "[" + ",".join(["1"] * (STORED_VALUE_BYTES_MAX // 2)) + "]"
    assert len(oversized.encode("utf-8")) > STORED_VALUE_BYTES_MAX
    with pytest.raises(Exception) as exc:
        semantic_runtime.start_run("a12_inputs", inputs=inputs(big=oversized))
    assert exc.value.code == "invalid_request"
    assert len(_runs_of(semantic_runtime, flow_version_id)) == 0

    # Control: the valid inputs start a run, so the refusals came from the
    # checks, not from a flow that cannot start.
    run = semantic_runtime.start_run("a12_inputs", inputs=inputs())
    assert _enum(run.status) == "succeeded"
    assert _output(run, "out").value.json_text == "3"
    (listed,) = _runs_of(semantic_runtime, flow_version_id)
    assert listed.run_id == run.run_id
