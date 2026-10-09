"""Witness tests for accepted decision A13 (02_rules_runs.md).

A run advances only inside the request that moves it — the start, an approval,
a resolution or a resume — one node at a time, the ready node with the
smallest `node_id` first; a guard skips what it cuts off, a failure concludes
what depends on it `upstream_failed` and wins over a skip, and the run ends
`failed` when any node failed. Each test carries the witness name its Required
test declares.

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
  its implementation (A04 rule 4), so a run can execute it (A12 rule 1);
- ``propose_binding(service_id, operation_name, inputs, outputs)`` ->
  OperationBinding, as agent ``author``; ``accept_binding(binding_id)``, as the
  owner;
- ``compose_flow_version(flow_id, purpose, inputs, outputs, nodes, edges,
  constants)`` -> ComposedFlowVersion, as agent ``author``;
  ``activate_flow_version(flow_version_id)`` -> FlowActivation, as the owner;
- ``start_run(flow_id, inputs)``, ``continue_after_approval(approval_id,
  decision)``, ``continue_after_resolution(attempt, resolution)``,
  ``resume_run(run_id)`` and ``read_run(run_id)`` -> ShownRun, as the owner;
  inputs are RequestJsonValue dicts, an attempt an AttemptKey dict;
- ``page_records(record_type, record_filter, page_size)`` -> RecordPageAnswer:
  ``node_execution`` (the trace, newest first) and ``effect_attempt``;
- capabilities: ``manifest.write_record``, ``installation.select_instance``,
  ``installation.set_credential``, ``stub_service`` (``on``, ``set_down``,
  ``requests``) and ``clock.advance``.
"""

import pytest

NUMBER = '{"type":"integer"}'
TEXT = '{"type":"string"}'
VERDICT = '{"enum":["new","duplicate"]}'

SERVICE = "ledger"
INSTANCE = "rig"
CREDENTIAL_HEADER = "X-Api-Key"
CREDENTIAL = "a13-canary-credential-58be"

# Python implementations, as A03 rule 3 shapes them.
COPY_X = "def run(inputs):\n    return {'y': inputs['x']}\n"
ADD_ONE = "def run(inputs):\n    return {'y': inputs['x'] + 1}\n"
FAIL_IF_NEGATIVE = (
    "def run(inputs):\n"
    "    if inputs['x'] < 0:\n"
    "        raise ValueError('negative')\n"
    "    return {'y': inputs['x']}\n"
)
FAIL_AT_ZERO = (
    "def run(inputs):\n"
    "    if inputs['x'] == 0:\n"
    "        raise ValueError('zero')\n"
    "    return {'y': inputs['x']}\n"
)
DIVIDE_TWELVE = "def run(inputs):\n    return {'y': 12 // inputs['x']}\n"
SUM_LIST = "def run(inputs):\n    return {'total': sum(inputs['xs'])}\n"
JOIN = "def run(inputs):\n    return {'y': inputs['p'] + inputs['q']}\n"
SCREEN_TEXT = (
    "def run(inputs):\n"
    "    item = inputs['x']\n"
    "    verdict = 'duplicate' if item.startswith('dup') else 'new'\n"
    "    return {'verdict': verdict, 'item': item}\n"
)
SCREEN_NUMBER = (
    "def run(inputs):\n"
    "    verdict = 'duplicate' if inputs['x'] < 1 else 'new'\n"
    "    return {'verdict': verdict, 'item': inputs['x']}\n"
)
BUSY_COPY = (
    "def run(inputs):\n"
    "    total = 0\n"
    "    for i in range(3000000):\n"
    "        total += i % 7\n"
    "    return {'y': inputs['x']}\n"
)


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


def _function_node(node_id, contract_version_id, map_over=None):
    return {
        "node_id": node_id,
        "kind": "function",
        "contract_version_id": contract_version_id,
        "binding_id": None,
        "map_over": map_over,
    }


def _operation_node(node_id, binding_id):
    return {
        "node_id": node_id,
        "kind": "operation",
        "contract_version_id": None,
        "binding_id": binding_id,
        "map_over": None,
    }


def _edge(from_node, from_port, to_node, to_port, guard=None):
    """A flow input or output endpoint has the empty node id (A05 rule 2)."""
    return {
        "from_node": from_node,
        "from_port": from_port,
        "to_node": to_node,
        "to_port": to_port,
        "guard": guard,
    }


def _guard(guard_port, guard_value):
    return {"guard_port": guard_port, "guard_value": guard_value}


def _enum(value):
    return getattr(value, "value", value)


def _function(semantic_runtime, slot_id, inputs, outputs, case_inputs, code):
    """A contract version with one authored trial case and `code` admitted and
    activated for it (A04 rules 3-4)."""
    contract_version_id = semantic_runtime.issue_contract_version(
        slot_id,
        purpose=f"A13 witness: {slot_id}",
        inputs=inputs,
        outputs=outputs,
    )
    semantic_runtime.add_trial_case(contract_version_id, inputs=case_inputs)
    submission = semantic_runtime.submit_implementation(contract_version_id, code)
    assert _enum(submission.verdict.verdict) == "admitted"
    assert submission.activation is not None
    return contract_version_id


def _x_to_y(semantic_runtime, slot_id, code):
    """A function of one integer input `x` and one integer output `y`."""
    return _function(
        semantic_runtime,
        slot_id,
        inputs=[_port("x", "input", NUMBER, "open")],
        outputs=[_port("y", "output", NUMBER)],
        case_inputs=[_value("x", "1")],
        code=code,
    )


def _compose_active(semantic_runtime, flow_id, inputs, outputs, nodes, edges):
    composed = semantic_runtime.compose_flow_version(
        flow_id,
        purpose=f"A13 witness: {flow_id}",
        inputs=inputs,
        outputs=outputs,
        nodes=nodes,
        edges=edges,
        constants=[],
    )
    assert composed.proof.proven is True
    semantic_runtime.activate_flow_version(composed.flow_version.flow_version_id)
    return composed.flow_version.flow_version_id


def _service(semantic_runtime, capabilities):
    """A stub service selected for SERVICE, with its credential (A17)."""
    stub = semantic_runtime.stub_service()
    semantic_runtime.manifest.write_record(
        SERVICE,
        {
            "service": SERVICE,
            "capabilities": [
                {
                    "name": name,
                    "exposed_as": {"http_api": [route]},
                    "effect_class": effect_class,
                    "idempotency_key": None,
                }
                for name, route, effect_class in capabilities
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
    return stub


def _binding(semantic_runtime, operation_name, outputs=True):
    """An accepted binding of one integer input `x` and, unless `outputs` is
    false, one integer output `y`."""
    proposed = semantic_runtime.propose_binding(
        SERVICE,
        operation_name,
        inputs=[_port("x", "input", NUMBER, "open")],
        outputs=[_port("y", "output", NUMBER, "open")] if outputs else [],
    )
    return semantic_runtime.accept_binding(proposed.binding_id).binding_id


def _trace(semantic_runtime, run_id):
    """The run's NodeExecutions in store order (pages come newest first)."""
    page = semantic_runtime.page_records(
        "node_execution",
        {"filter_kind": "equals", "field": "run_id", "value": run_id},
        page_size=200,
    )
    return list(reversed(page.records.node_executions))


def _records(trace, node_id):
    return [record for record in trace if record.node_id == node_id]


def _only_record(trace, node_id):
    records = _records(trace, node_id)
    assert len(records) == 1
    return records[0]


def _output(run, port):
    (output,) = [output for output in run.outputs if output.port == port]
    return output


def _produced(run, port):
    output = _output(run, port)
    assert output.output_kind == "produced"
    return output.value.json_text


def _missing(run, port):
    output = _output(run, port)
    assert output.output_kind == "missing"
    return _enum(output.reason)


def _snapshot(semantic_runtime, run_id):
    """What a request could change about a run: its status, its waiting
    points and its trace."""
    run = semantic_runtime.read_run(run_id)
    waiting = tuple(
        (wait.node_id, wait.map_index, _enum(wait.reason), wait.approval_id)
        for wait in run.waiting
    )
    trace = tuple(
        (record.node_id, record.map_index, record.attempt_number, _enum(record.status))
        for record in _trace(semantic_runtime, run_id)
    )
    return _enum(run.status), waiting, trace


def test_next_node_min_node_id(semantic_runtime):
    """[witness: verification:kernel_a13_next_node_min_node_id]

    A13 Required test 1: two ready nodes `b` and `a` execute `a` first, every
    time.
    """
    # Two `read` operation nodes, so the order in which they execute is also
    # the order in which their requests reach the stub service.
    stub = _service(semantic_runtime, [("look", "GET /items", "read")])
    stub.on("GET", "/items", json={})
    look = _binding(semantic_runtime, "look", outputs=False)

    def compose(flow_id, first_declared, second_declared):
        # `first_declared` receives 1, `second_declared` 2; both are ready at
        # start (A13 rule 3) and independent.
        return _compose_active(
            semantic_runtime,
            flow_id,
            inputs=[
                _port("one", "input", NUMBER, "open"),
                _port("two", "input", NUMBER, "open"),
            ],
            outputs=[],
            nodes=[
                _operation_node(first_declared, look),
                _operation_node(second_declared, look),
            ],
            edges=[
                _edge("", "one", first_declared, "x"),
                _edge("", "two", second_declared, "x"),
            ],
        )

    # `b` is declared first and receives 1; `a` receives 2.
    compose("a13_b_and_a", "b", "a")
    for _ in range(3):
        seen = len(stub.requests)
        run = semantic_runtime.start_run(
            "a13_b_and_a", inputs=[_value("one", "1"), _value("two", "2")]
        )
        assert _enum(run.status) == "succeeded"
        # A13 rule 2: the ready node with the smallest `node_id` goes first.
        targets = [request.target for request in stub.requests[seen:]]
        assert targets == ["/items?x=2", "/items?x=1"]
        trace = _trace(semantic_runtime, run.run_id)
        assert [record.node_id for record in trace] == ["a", "b"]
        a, b = trace
        assert a.ended_at.epoch_us <= b.started_at.epoch_us

    # Control: `Z` (U+005A) orders before `a` (U+0061) by code point (A05 rule
    # 2), though `a` is declared first and comes first ignoring case.
    compose("a13_a_and_Z", "a", "Z")
    seen = len(stub.requests)
    run = semantic_runtime.start_run(
        "a13_a_and_Z", inputs=[_value("one", "1"), _value("two", "2")]
    )
    assert _enum(run.status) == "succeeded"
    targets = [request.target for request in stub.requests[seen:]]
    assert targets == ["/items?x=2", "/items?x=1"]
    assert [record.node_id for record in _trace(semantic_runtime, run.run_id)] == ["Z", "a"]


def test_guard_skip_transitive_run_succeeds(semantic_runtime):
    """[witness: verification:kernel_a13_guard_skip_transitive_run_succeeds]

    A13 Required test 2: a duplicate-check guard that disables the save branch
    yields `skipped_by_guard` on the save node and on the flow output behind
    it, and a `succeeded` run.
    """
    check = _function(
        semantic_runtime,
        "a13_duplicate_check",
        inputs=[_port("x", "input", TEXT, "open")],
        outputs=[_port("item", "output", TEXT), _port("verdict", "output", VERDICT)],
        case_inputs=[_value("x", '"first"')],
        code=SCREEN_TEXT,
    )
    save = _function(
        semantic_runtime,
        "a13_save",
        inputs=[_port("x", "input", TEXT, "open")],
        outputs=[_port("y", "output", TEXT)],
        case_inputs=[_value("x", '"first"')],
        code="def run(inputs):\n    return {'y': inputs['x']}\n",
    )
    _compose_active(
        semantic_runtime,
        "a13_dedupe",
        inputs=[_port("item", "input", TEXT, "open")],
        outputs=[_port("saved", "output", TEXT), _port("verdict", "output", VERDICT)],
        nodes=[_function_node("check", check), _function_node("save", save)],
        edges=[
            _edge("", "item", "check", "x"),
            _edge("check", "item", "save", "x", guard=_guard("verdict", '"new"')),
            _edge("check", "verdict", "", "verdict"),
            _edge("save", "y", "", "saved"),
        ],
    )

    run = semantic_runtime.start_run("a13_dedupe", inputs=[_value("item", '"dup-17"')])
    trace = _trace(semantic_runtime, run.run_id)
    assert _enum(_only_record(trace, "check").status) == "succeeded"
    # A13 rule 4: the only edge into `save.x` is disabled by its guard.
    skipped = _only_record(trace, "save")
    assert _enum(skipped.status) == "skipped_by_guard"
    assert len(skipped.outputs) == 0
    # A13 rule 7: the flow output behind the skipped node is `skipped_by_guard`,
    # and a run whose nodes all succeeded or were skipped by a guard succeeded.
    assert _missing(run, "saved") == "skipped_by_guard"
    assert _produced(run, "verdict") == '"duplicate"'
    assert _enum(run.status) == "succeeded"

    # Control: an item that is not a duplicate takes the save branch, so the
    # skip above comes from the guard.
    fresh = semantic_runtime.start_run("a13_dedupe", inputs=[_value("item", '"fresh-18"')])
    assert _enum(fresh.status) == "succeeded"
    assert _produced(fresh, "saved") == '"fresh-18"'
    assert _produced(fresh, "verdict") == '"new"'
    fresh_trace = _trace(semantic_runtime, fresh.run_id)
    assert _enum(_only_record(fresh_trace, "save").status) == "succeeded"


def test_failed_input_gives_upstream_failed(semantic_runtime):
    """[witness: verification:kernel_a13_failed_input_gives_upstream_failed]

    A13 Required test 3: one failing element of three fails the mapped node,
    keeps three records, and concludes its dependants `upstream_failed`.
    """
    divide = _x_to_y(semantic_runtime, "a13_divide", DIVIDE_TWELVE)
    total = _function(
        semantic_runtime,
        "a13_total",
        inputs=[_port("xs", "input", NUMBER, "open", cardinality="many")],
        outputs=[_port("total", "output", NUMBER)],
        case_inputs=[_value("xs", "[1,2]")],
        code=SUM_LIST,
    )
    _compose_active(
        semantic_runtime,
        "a13_map",
        inputs=[_port("xs", "input", NUMBER, "open", cardinality="many")],
        outputs=[_port("total", "output", NUMBER)],
        nodes=[_function_node("m", divide, map_over="x"), _function_node("s", total)],
        edges=[
            _edge("", "xs", "m", "x"),
            _edge("m", "y", "s", "xs"),
            _edge("s", "total", "", "total"),
        ],
    )

    # The element at index 1 divides by zero and raises: `crashed` (A03 rule 5).
    run = semantic_runtime.start_run("a13_map", inputs=[_value("xs", "[1,0,2]")])
    trace = _trace(semantic_runtime, run.run_id)

    # A13 rule 2: every element runs once, and the failing one does not stop
    # the element after it; three records, none of the mapped node's own.
    elements = sorted(_records(trace, "m"), key=lambda record: record.map_index)
    assert [record.map_index for record in elements] == [0, 1, 2]
    assert [_enum(record.status) for record in elements] == [
        "succeeded",
        "crashed",
        "succeeded",
    ]
    # A13 rule 3: an element that does not succeed keeps no output.
    assert len(elements[1].outputs) == 0

    # A13 rules 5-6: one failed element fails the mapped node for its
    # dependants, which conclude `upstream_failed` without executing.
    dependant = _only_record(trace, "s")
    assert dependant.map_index is None
    assert _enum(dependant.status) == "upstream_failed"
    assert len(dependant.outputs) == 0
    assert _enum(run.status) == "failed"
    assert _missing(run, "total") == "not_produced"

    # Control: with no failing element the dependant executes on the list.
    whole = semantic_runtime.start_run("a13_map", inputs=[_value("xs", "[1,2,3]")])
    assert _enum(whole.status) == "succeeded"
    assert _produced(whole, "total") == "22"  # 12 + 6 + 4
    whole_trace = _trace(semantic_runtime, whole.run_id)
    assert _enum(_only_record(whole_trace, "s").status) == "succeeded"


def test_any_failure_ends_run_failed(semantic_runtime):
    """[witness: verification:kernel_a13_any_failure_ends_run_failed]

    A13 Required test 4: with two independent branches, a failure in one lets
    the other finish; the run ends `failed` with the other branch's output
    marked produced.
    """
    fragile = _x_to_y(semantic_runtime, "a13_fragile", FAIL_IF_NEGATIVE)
    copy = _x_to_y(semantic_runtime, "a13_copy", COPY_X)
    # `a` (fails) executes before `b` (A13 rule 2), so `b` runs after a failure.
    _compose_active(
        semantic_runtime,
        "a13_branches",
        inputs=[_port("x", "input", NUMBER, "open")],
        outputs=[_port("out_a", "output", NUMBER), _port("out_b", "output", NUMBER)],
        nodes=[_function_node("a", fragile), _function_node("b", copy)],
        edges=[
            _edge("", "x", "a", "x"),
            _edge("", "x", "b", "x"),
            _edge("a", "y", "", "out_a"),
            _edge("b", "y", "", "out_b"),
        ],
    )

    run = semantic_runtime.start_run("a13_branches", inputs=[_value("x", "-1")])
    trace = _trace(semantic_runtime, run.run_id)
    assert _enum(_only_record(trace, "a").status) == "crashed"
    assert _enum(_only_record(trace, "b").status) == "succeeded"
    # A13 rule 7: not every node succeeded, so the run ended `failed`; the
    # other branch's output is produced, the failed one's `not_produced`.
    assert _enum(run.status) == "failed"
    assert run.ended_at is not None
    assert _produced(run, "out_b") == "-1"
    assert _missing(run, "out_a") == "not_produced"

    # Control: without the failure both branches produce and the run succeeds.
    clean = semantic_runtime.start_run("a13_branches", inputs=[_value("x", "1")])
    assert _enum(clean.status) == "succeeded"
    assert _produced(clean, "out_a") == "1"
    assert _produced(clean, "out_b") == "1"


def test_advance_only_inside_request(semantic_runtime):
    """[witness: verification:kernel_a13_advance_only_inside_request]

    A13 Required test 6: between two requests a resting run gains no
    NodeExecution and no status change; the next approval, resolution or
    resume advances it inside that request, which returns only when no node
    can execute.
    """
    stub = _service(
        semantic_runtime,
        [
            ("approve_entry", "POST /approve", "state-transition"),
            ("draft_entry", "POST /draft", "draft-write"),
            ("look_entry", "GET /look", "read"),
        ],
    )
    stub.on("POST", "/approve", json={"y": 7})
    stub.on("POST", "/draft", action="drop_after_request")
    stub.on("GET", "/look", json={"y": 7})

    prepare = _x_to_y(semantic_runtime, "a13_prepare", COPY_X)
    finish = _x_to_y(semantic_runtime, "a13_finish", ADD_ONE)

    def chain(flow_id, operation_name):
        # x -> a (function) -> b (operation) -> c (function) -> out
        return _compose_active(
            semantic_runtime,
            flow_id,
            inputs=[_port("x", "input", NUMBER, "open")],
            outputs=[_port("out", "output", NUMBER)],
            nodes=[
                _function_node("a", prepare),
                _operation_node("b", _binding(semantic_runtime, operation_name)),
                _function_node("c", finish),
            ],
            edges=[
                _edge("", "x", "a", "x"),
                _edge("a", "y", "b", "x"),
                _edge("b", "y", "c", "x"),
                _edge("c", "y", "", "out"),
            ],
        )

    chain("a13_wait_approval", "approve_entry")
    chain("a13_wait_unknown", "draft_entry")
    chain("a13_wait_unreachable", "look_entry")

    def rests_unchanged(run, status, reason):
        """The run rests at `b`; time passing and reads change nothing."""
        assert _enum(run.status) == status
        (wait,) = run.waiting
        assert (wait.node_id, _enum(wait.reason)) == ("b", reason)
        before = _snapshot(semantic_runtime, run.run_id)
        assert before[0] == status
        assert [key[0] for key in before[2] if key[3] == "succeeded"] == ["a"]
        assert not [key for key in before[2] if key[0] == "c"]
        semantic_runtime.clock.advance(days=7)
        assert _snapshot(semantic_runtime, run.run_id) == before
        assert _snapshot(semantic_runtime, run.run_id) == before
        return wait

    def advanced_to_end(answer, run_id, status, c_status):
        """The request returned only once no node could execute: the answer
        is the ended run, and `c` concluded inside that request."""
        assert _enum(answer.status) == status
        assert answer.ended_at is not None
        assert len(answer.waiting) == 0
        trace = _trace(semantic_runtime, run_id)
        assert _enum(_only_record(trace, "c").status) == c_status
        assert _snapshot(semantic_runtime, run_id)[0] == status

    # An approval (A10 rule 3: the approved effect is sent in that request).
    run = semantic_runtime.start_run("a13_wait_approval", inputs=[_value("x", "1")])
    wait = rests_unchanged(run, "awaiting_approval", "owner_approval")
    answer = semantic_runtime.continue_after_approval(wait.approval_id, "approve")
    advanced_to_end(answer, run.run_id, "succeeded", "succeeded")
    assert _produced(answer, "out") == "8"

    # A resolution: the `draft-write` send dropped after the request was
    # written is `outcome_unknown` (A09 rule 5); resolved `applied` for a
    # binding with an output, `c` concludes `upstream_failed` (A11 rule 3,
    # A13 rule 5) inside the owner's request.
    run = semantic_runtime.start_run("a13_wait_unknown", inputs=[_value("x", "1")])
    rests_unchanged(run, "pending", "outcome_unknown")
    answer = semantic_runtime.continue_after_resolution(
        {"run_id": run.run_id, "node_id": "b", "map_index": None, "attempt_number": 1},
        "applied",
    )
    advanced_to_end(answer, run.run_id, "failed", "upstream_failed")

    # A resume: the `read` send finds the service down, `service_unreachable`
    # (A09 rule 5); resumed once it is up, the run finishes in that request.
    stub.set_down(True)
    run = semantic_runtime.start_run("a13_wait_unreachable", inputs=[_value("x", "1")])
    rests_unchanged(run, "pending", "service_unreachable")
    stub.set_down(False)
    answer = semantic_runtime.resume_run(run.run_id)
    advanced_to_end(answer, run.run_id, "succeeded", "succeeded")
    assert _produced(answer, "out") == "8"


def test_one_node_executes_at_a_time(semantic_runtime):
    """[witness: verification:kernel_a13_one_node_executes_at_a_time]

    A13 Required test 7: in one run of a flow with two independent function
    nodes, the second node's NodeExecution starts no earlier than the first
    one's ended.
    """
    busy = _x_to_y(semantic_runtime, "a13_busy", BUSY_COPY)
    _compose_active(
        semantic_runtime,
        "a13_two_functions",
        inputs=[_port("x", "input", NUMBER, "open")],
        outputs=[_port("out_a", "output", NUMBER), _port("out_b", "output", NUMBER)],
        nodes=[_function_node("b", busy), _function_node("a", busy)],
        edges=[
            _edge("", "x", "a", "x"),
            _edge("", "x", "b", "x"),
            _edge("a", "y", "", "out_a"),
            _edge("b", "y", "", "out_b"),
        ],
    )

    run = semantic_runtime.start_run("a13_two_functions", inputs=[_value("x", "5")])
    assert _enum(run.status) == "succeeded"
    trace = _trace(semantic_runtime, run.run_id)
    # A13 rule 2: one at a time, `a` (the smaller `node_id`) first.
    assert [record.node_id for record in trace] == ["a", "b"]
    first, second = trace
    for record in trace:
        assert record.started_at.epoch_us <= record.ended_at.epoch_us
    assert second.started_at.epoch_us >= first.ended_at.epoch_us


def test_upstream_failed_wins_over_skip(semantic_runtime):
    """[witness: verification:kernel_a13_upstream_failed_wins_over_skip]

    A13 Required test 8: a node with one input from a failed node and another
    whose only edge is disabled by its guard concludes `upstream_failed`, not
    `skipped_by_guard`.
    """
    fragile = _x_to_y(semantic_runtime, "a13_fragile", FAIL_AT_ZERO)
    screen = _function(
        semantic_runtime,
        "a13_screen",
        inputs=[_port("x", "input", NUMBER, "open")],
        outputs=[_port("item", "output", NUMBER), _port("verdict", "output", VERDICT)],
        case_inputs=[_value("x", "1")],
        code=SCREEN_NUMBER,
    )
    join = _function(
        semantic_runtime,
        "a13_join",
        inputs=[_port("p", "input", NUMBER, "open"), _port("q", "input", NUMBER, "open")],
        outputs=[_port("y", "output", NUMBER)],
        case_inputs=[_value("p", "1"), _value("q", "2")],
        code=JOIN,
    )
    # `a` fails at x = 0; `g` disables the edge into `z.q` for x < 1.
    _compose_active(
        semantic_runtime,
        "a13_fail_and_skip",
        inputs=[_port("x", "input", NUMBER, "open")],
        outputs=[_port("out", "output", NUMBER)],
        nodes=[
            _function_node("a", fragile),
            _function_node("g", screen),
            _function_node("z", join),
        ],
        edges=[
            _edge("", "x", "a", "x"),
            _edge("", "x", "g", "x"),
            _edge("a", "y", "z", "p"),
            _edge("g", "item", "z", "q", guard=_guard("verdict", '"new"')),
            _edge("z", "y", "", "out"),
        ],
    )

    run = semantic_runtime.start_run("a13_fail_and_skip", inputs=[_value("x", "0")])
    trace = _trace(semantic_runtime, run.run_id)
    assert _enum(_only_record(trace, "a").status) == "crashed"
    assert _enum(_only_record(trace, "g").status) == "succeeded"
    # A13 rule 5: when both rule 4 and this rule apply, this rule wins.
    assert _enum(_only_record(trace, "z").status) == "upstream_failed"
    assert _enum(run.status) == "failed"
    # A13 rule 7: `z` is recorded `upstream_failed`, so its output is not a skip.
    assert _missing(run, "out") == "not_produced"

    # The same with the ports exchanged — the failed input on `z.q`, the
    # disabled edge into `z.p` — so the precedence does not come from which
    # input of `z` is looked at first.
    _compose_active(
        semantic_runtime,
        "a13_skip_and_fail",
        inputs=[_port("x", "input", NUMBER, "open")],
        outputs=[_port("out", "output", NUMBER)],
        nodes=[
            _function_node("a", fragile),
            _function_node("g", screen),
            _function_node("z", join),
        ],
        edges=[
            _edge("", "x", "a", "x"),
            _edge("", "x", "g", "x"),
            _edge("a", "y", "z", "q"),
            _edge("g", "item", "z", "p", guard=_guard("verdict", '"new"')),
            _edge("z", "y", "", "out"),
        ],
    )
    mirrored = semantic_runtime.start_run("a13_skip_and_fail", inputs=[_value("x", "0")])
    mirrored_trace = _trace(semantic_runtime, mirrored.run_id)
    assert _enum(_only_record(mirrored_trace, "a").status) == "crashed"
    assert _enum(_only_record(mirrored_trace, "z").status) == "upstream_failed"
    assert _enum(mirrored.status) == "failed"
    assert _missing(mirrored, "out") == "not_produced"

    # Control: the same disabled edge with `a` succeeding skips `z`, so the
    # result above is the precedence, not a guard the kernel ignores.
    skipped = semantic_runtime.start_run("a13_fail_and_skip", inputs=[_value("x", "-1")])
    skipped_trace = _trace(semantic_runtime, skipped.run_id)
    assert _enum(_only_record(skipped_trace, "a").status) == "succeeded"
    assert _enum(_only_record(skipped_trace, "z").status) == "skipped_by_guard"
    assert _missing(skipped, "out") == "skipped_by_guard"
    assert _enum(skipped.status) == "succeeded"


def test_resolved_unknown_conclusion(semantic_runtime):
    """[witness: verification:kernel_a13_resolved_unknown_conclusion]

    A13 Required test 9: an element recorded `outcome_unknown` keeps its
    dependants waiting while its EffectAttempt is `unknown`; resolved
    `applied` for a binding without output ports, its dependants execute;
    resolved `applied` for a binding with output ports, they conclude
    `upstream_failed`; its NodeExecution keeps `outcome_unknown` throughout.
    """
    pytest.skip(
        "owner decision: which dependants can 'execute' after `applied` for a "
        "binding without output ports, when an edge starts only at an output "
        "port (M15, A05 phase 3)?"
    )
    # Both operations are `draft-write`: sent under the flow activation without
    # approval (A10 rule 1); the stub drops the connection after reading the
    # request, so each attempt is `unknown` (A09 rule 5).
    stub = _service(
        semantic_runtime,
        [
            ("push_entry", "POST /push", "draft-write"),
            ("post_entry", "POST /post", "draft-write"),
        ],
    )
    stub.on("POST", "/push", action="drop_after_request")
    stub.on("POST", "/post", action="drop_after_request")

    prepare = _x_to_y(semantic_runtime, "a13_prepare", COPY_X)
    finish = _x_to_y(semantic_runtime, "a13_finish", ADD_ONE)

    _compose_active(
        semantic_runtime,
        "a13_unknown_without_outputs",
        inputs=[_port("x", "input", NUMBER, "open")],
        outputs=[],
        nodes=[
            _function_node("a", prepare),
            _operation_node("b", _binding(semantic_runtime, "push_entry", outputs=False)),
        ],
        edges=[_edge("", "x", "a", "x"), _edge("a", "y", "b", "x")],
    )
    _compose_active(
        semantic_runtime,
        "a13_unknown_with_outputs",
        inputs=[_port("x", "input", NUMBER, "open")],
        outputs=[_port("out", "output", NUMBER)],
        nodes=[
            _function_node("a", prepare),
            _operation_node("b", _binding(semantic_runtime, "post_entry")),
            _function_node("c", finish),
        ],
        edges=[
            _edge("", "x", "a", "x"),
            _edge("a", "y", "b", "x"),
            _edge("b", "y", "c", "x"),
            _edge("c", "y", "", "out"),
        ],
    )

    def attempt_of(run_id):
        page = semantic_runtime.page_records(
            "effect_attempt",
            {"filter_kind": "equals", "field": "run_id", "value": run_id},
            page_size=200,
        )
        (attempt,) = page.records.effect_attempts
        return attempt

    def unknown_element(run_id):
        record = _only_record(_trace(semantic_runtime, run_id), "b")
        assert _enum(record.status) == "outcome_unknown"
        assert record.attempt_number == 1
        return record

    def key(run_id):
        return {"run_id": run_id, "node_id": "b", "map_index": None, "attempt_number": 1}

    # With output ports: while the attempt is `unknown`, `c` waits.
    run = semantic_runtime.start_run("a13_unknown_with_outputs", inputs=[_value("x", "1")])
    assert _enum(run.status) == "pending"  # A13 rule 8: no element waits for approval
    (wait,) = run.waiting
    assert (wait.node_id, _enum(wait.reason)) == ("b", "outcome_unknown")
    unknown_element(run.run_id)
    assert _enum(attempt_of(run.run_id).status) == "unknown"
    semantic_runtime.clock.advance(days=7)
    assert _records(_trace(semantic_runtime, run.run_id), "c") == []
    assert [request.target for request in stub.requests] == ["/post"]

    # Resolved `applied`: the element counts failed (`applied_outputs_unknown`,
    # A11 rule 3), and its dependant concludes `upstream_failed` (A13 rule 5).
    answer = semantic_runtime.continue_after_resolution(key(run.run_id), "applied")
    assert _enum(answer.status) == "failed"
    trace = _trace(semantic_runtime, run.run_id)
    assert _enum(_only_record(trace, "c").status) == "upstream_failed"
    unknown_element(run.run_id)
    attempt = attempt_of(run.run_id)
    assert _enum(attempt.status) == "applied"
    assert _enum(attempt.resolved_by.kind) == "owner"
    assert _missing(answer, "out") == "not_produced"

    # Without output ports: resolved `applied`, the element counts succeeded
    # and the run continues to its end; the record keeps `outcome_unknown`.
    plain = semantic_runtime.start_run("a13_unknown_without_outputs", inputs=[_value("x", "1")])
    assert _enum(plain.status) == "pending"
    unknown_element(plain.run_id)
    assert _enum(attempt_of(plain.run_id).status) == "unknown"
    answer = semantic_runtime.continue_after_resolution(key(plain.run_id), "applied")
    assert _enum(answer.status) == "succeeded"
    unknown_element(plain.run_id)
    assert _enum(attempt_of(plain.run_id).status) == "applied"
    assert [request.target for request in stub.requests] == ["/post", "/push"]
