"""Witness tests for accepted decision A11 (02_rules_services.md).

An attempt whose outcome the kernel cannot know stays `unknown` until the owner
resolves it; the kernel never sends again on its own, and every NodeExecution
of an element takes the next attempt number. Each test carries the witness
name its Required test declares.

The Factory project supplies the ``semantic_runtime`` pytest fixture. It binds
these scenarios to the generated public operations of State 5 — named here by
their operation names, with arguments shaped as the State 6 models — without
changing the assertions below. Each test gets a fresh, empty kernel store.

Fixture surface used here:

- ``propose_binding(service_id, operation_name, inputs, outputs)`` ->
  OperationBinding (acts as agent ``author``); ``accept_binding(binding_id)``
  -> OperationBinding (the owner);
- ``compose_flow_version(flow_id, purpose, inputs, outputs, nodes, edges,
  constants)`` -> ComposedFlowVersion (agent ``author``);
  ``activate_flow_version(flow_version_id)`` -> FlowActivation (the owner);
- ``start_run(flow_id, inputs)``, ``resume_run(run_id)``,
  ``continue_after_approval(approval_id, decision)``,
  ``continue_after_resolution(attempt, resolution)``, ``read_run(run_id)`` ->
  ShownRun; inputs are RequestJsonValue dicts, ``attempt`` an AttemptKey dict;
- ``grant_standing_approval(flow_id, node_id)`` -> StandingGrant (M25);
- ``page_records(record_type, record_filter, page_size)`` -> RecordPageAnswer;
  approvals, effect attempts, node executions and runs are read from its
  ``records`` (newest first);
- every call is made by the owner unless it is an authoring operation.

Capabilities used here: ``stub_service()`` (a loopback HTTP service whose
received requests are listed in ``stub.requests``; ``action=
"drop_after_request"`` closes the connection after reading the request,
``action="kill_kernel"`` SIGKILLs the kernel once the request has arrived),
``manifest.write_record``, ``installation.select_instance``,
``installation.set_credential``, ``restart()``, ``KernelStopped`` and
``clock.advance``.
"""

import json

import pytest

TEXT = '{"type":"string"}'
NUMBER = '{"type":"integer"}'

SERVICE = "drafts"
INSTANCE = "local"
CREDENTIAL_HEADER = "X-Api-Key"
CREDENTIAL = "a11-credential-value-0001"


def _v(x):
    return getattr(x, "value", x)


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


def _capability(name, route, effect_class):
    return {
        "name": name,
        "exposed_as": {"http_api": [route]},
        "effect_class": effect_class,
        "idempotency_key": None,
    }


def _install_service(semantic_runtime, stub, capabilities):
    """Manifest record, selected instance and credential, before the first call."""
    semantic_runtime.manifest.write_record(
        SERVICE,
        {
            "service": SERVICE,
            "capabilities": capabilities,
            "instances": [
                {
                    "instance_name": INSTANCE,
                    "api_base_url": stub.base_url,
                    "required_headers": None,
                    "instance_class": "local_dev",
                }
            ],
        },
    )
    semantic_runtime.installation.select_instance(SERVICE, INSTANCE)
    semantic_runtime.installation.set_credential(
        SERVICE, CREDENTIAL_HEADER, CREDENTIAL
    )


def _binding(semantic_runtime, operation_name, inputs, outputs=()):
    proposed = semantic_runtime.propose_binding(
        SERVICE, operation_name, inputs=list(inputs), outputs=list(outputs)
    )
    return semantic_runtime.accept_binding(proposed.binding_id).binding_id


def _op_node(node_id, binding_id):
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


def _flow(semantic_runtime, flow_id, nodes, edges):
    """Flow input `title` feeding `send`; proven and activated by the owner."""
    composed = semantic_runtime.compose_flow_version(
        flow_id,
        purpose=f"A11 witness: {flow_id}",
        inputs=[_port("title", "input", TEXT, "open")],
        outputs=[],
        nodes=list(nodes),
        edges=[_edge("", "title", "send", "title")] + list(edges),
        constants=[],
    )
    assert composed.proof.proven is True
    flow_version_id = composed.flow_version.flow_version_id
    semantic_runtime.activate_flow_version(flow_version_id)
    return flow_version_id


def _send_only(semantic_runtime, flow_id):
    """One operation node `send`, binding without output ports."""
    binding_id = _binding(
        semantic_runtime, "publish", [_port("title", "input", TEXT, "open")]
    )
    _flow(semantic_runtime, flow_id, [_op_node("send", binding_id)], [])
    return binding_id


def _send_then_notify(semantic_runtime, flow_id):
    """`send` (draft-write, output `draft_id`) feeding the read node `notify`."""
    send = _binding(
        semantic_runtime,
        "create_draft",
        [_port("title", "input", TEXT, "open")],
        [_port("draft_id", "output", NUMBER, "open")],
    )
    notify = _binding(
        semantic_runtime, "notify", [_port("draft_id", "input", NUMBER, "open")]
    )
    _flow(
        semantic_runtime,
        flow_id,
        [_op_node("notify", notify), _op_node("send", send)],
        [_edge("send", "draft_id", "notify", "draft_id")],
    )
    return send, notify


def _title(text):
    return [{"payload_kind": "json", "port": "title", "json_text": json.dumps(text)}]


def _attempt_key(run_id, attempt_number, node_id="send"):
    return {
        "run_id": run_id,
        "node_id": node_id,
        "map_index": None,
        "attempt_number": attempt_number,
    }


def _by_run(run_id):
    return {"filter_kind": "equals", "field": "run_id", "value": run_id}


def _approvals(semantic_runtime, run_id):
    """The run's approvals in store order."""
    page = semantic_runtime.page_records("approval", _by_run(run_id), page_size=200)
    return list(reversed(page.records.approvals))


def _attempts(semantic_runtime, run_id):
    """The run's effect attempts in store order."""
    page = semantic_runtime.page_records(
        "effect_attempt", _by_run(run_id), page_size=200
    )
    return list(reversed(page.records.effect_attempts))


def _executions(semantic_runtime, run_id, node_id=None):
    """The run's trace in store order, optionally of one node."""
    page = semantic_runtime.page_records(
        "node_execution", _by_run(run_id), page_size=200
    )
    records = list(reversed(page.records.node_executions))
    if node_id is None:
        return records
    return [r for r in records if r.node_id == node_id]


def _waits(run):
    return [
        (w.node_id, w.map_index, _v(w.reason), w.approval_id) for w in run.waiting
    ]


def _authority(attempt):
    authority = attempt.authority
    kind = _v(authority.authority_kind)
    if kind == "approval":
        return ("approval", authority.approval_id)
    if kind == "grant":
        return ("grant", authority.grant_id)
    return (kind, authority.store_position)


def _sent(stub, method):
    return [r for r in stub.requests if r.method == method]


def test_restart_turns_in_flight_unknown(semantic_runtime):
    """[witness: verification:kernel_a11_restart_turns_in_flight_unknown]

    A11 Required test 1: killing the kernel between the in-flight record and
    the answer leaves an `unknown` attempt after restart and sends nothing.
    """
    stub = semantic_runtime.stub_service()
    _install_service(
        semantic_runtime,
        stub,
        [_capability("publish", "POST /items", "state-transition")],
    )
    binding_id = _send_only(semantic_runtime, "a11_restart")
    run = semantic_runtime.start_run("a11_restart", _title("in flight"))
    approval = _approvals(semantic_runtime, run.run_id)[0]

    # The request reaches the service; the kernel dies before the answer.
    stub.on("POST", "/items", action="kill_kernel")
    with pytest.raises(semantic_runtime.KernelStopped):
        semantic_runtime.continue_after_approval(approval.approval_id, "approve")
    assert len(stub.requests) == 1

    # From here on the service would answer any request it received.
    stub.on("POST", "/items", status=200, json={})
    semantic_runtime.clock.advance(ms=5000)
    assert semantic_runtime.restart().started is True

    # A11 rule 4: on start the `in_flight` attempt becomes `unknown`, with its
    # NodeExecution `outcome_unknown` and its approval `used`, in one call.
    attempts = _attempts(semantic_runtime, run.run_id)
    assert len(attempts) == 1
    attempt = attempts[0]
    assert _v(attempt.status) == "unknown"
    assert attempt.attempt_number == 1
    assert attempt.resolved_by is None
    assert _authority(attempt) == ("approval", approval.approval_id)
    executions = _executions(semantic_runtime, run.run_id)
    assert len(executions) == 1
    execution = executions[0]
    assert _v(execution.status) == "outcome_unknown"
    assert execution.attempt_number == 1
    assert _v(execution.executed.executed_kind) == "binding"
    assert execution.executed.binding_id == binding_id
    assert tuple(execution.outputs) == ()
    # A11 rule 4: its start time is taken from the EffectAttempt.
    assert execution.started_at == attempt.recorded_at
    # It ends when the start recovered it, five seconds later on the kernel
    # clock (A19: every timestamp from clock.kernel_now at that moment).
    assert execution.ended_at.epoch_us >= attempt.recorded_at.epoch_us + 5_000_000
    assert _v(_approvals(semantic_runtime, run.run_id)[0].status) == "used"

    # A11 rules 2 and 4: the element waits; the kernel does not ask the
    # service and does not send again.
    rested = semantic_runtime.read_run(run.run_id)
    assert _v(rested.status) == "pending"
    assert _waits(rested) == [("send", None, "outcome_unknown", None)]
    assert len(stub.requests) == 1


def test_applied_no_outputs_succeeds_one_execution(semantic_runtime):
    """[witness: verification:kernel_a11_applied_no_outputs_succeeds_one_execution]

    A11 Required test 2: resolving `applied` for a binding without outputs
    continues the run; the trace holds one NodeExecution of attempt 1,
    `outcome_unknown`, and its EffectAttempt `applied` with the owner as
    `resolved_by`.
    """
    stub = semantic_runtime.stub_service()
    stub.on("POST", "/items", action="drop_after_request")
    _install_service(
        semantic_runtime,
        stub,
        [_capability("publish", "POST /items", "draft-write")],
    )
    _send_only(semantic_runtime, "a11_applied")

    run = semantic_runtime.start_run("a11_applied", _title("applied"))

    # A09 rule 5 / A11 rule 2: a dropped connection after the request was
    # written is `outcome_unknown`; the element waits.
    assert _v(run.status) == "pending"
    assert _waits(run) == [("send", None, "outcome_unknown", None)]
    assert [_v(a.status) for a in _attempts(semantic_runtime, run.run_id)] == [
        "unknown"
    ]

    done = semantic_runtime.continue_after_resolution(
        _attempt_key(run.run_id, 1), "applied"
    )

    # A11 rule 3: `applied`, binding without output ports — the element counts
    # as succeeded and the run continues, here to its end.
    assert _v(done.status) == "succeeded"
    assert _waits(done) == []
    executions = _executions(semantic_runtime, run.run_id)
    assert [(e.node_id, e.attempt_number, _v(e.status)) for e in executions] == [
        ("send", 1, "outcome_unknown")
    ]
    attempts = _attempts(semantic_runtime, run.run_id)
    assert len(attempts) == 1
    assert attempts[0].attempt_number == 1
    assert _v(attempts[0].status) == "applied"
    assert _v(attempts[0].resolved_by.kind) == "owner"
    # A11 rule 2: nothing was sent again.
    assert len(stub.requests) == 1


def test_not_applied_fresh_approval_next_attempt(semantic_runtime):
    """[witness: verification:kernel_a11_not_applied_fresh_approval_next_attempt]

    A11 Required test 3: resolving `not_applied` under a standing grant asks
    the owner for approval; the resend is attempt 2 with its own
    EffectAttempt.
    """
    stub = semantic_runtime.stub_service()
    stub.on("POST", "/items", action="drop_after_request")
    _install_service(
        semantic_runtime,
        stub,
        [_capability("publish", "POST /items", "state-transition")],
    )
    _send_only(semantic_runtime, "a11_not_applied")
    grant = semantic_runtime.grant_standing_approval("a11_not_applied", "send")

    run = semantic_runtime.start_run("a11_not_applied", _title("not applied"))

    # Control: the first send goes under the grant without asking.
    assert _approvals(semantic_runtime, run.run_id) == []
    assert len(stub.requests) == 1
    assert _waits(run) == [("send", None, "outcome_unknown", None)]
    first = _attempts(semantic_runtime, run.run_id)[0]
    assert _authority(first) == ("grant", grant.grant_id)

    stub.on("POST", "/items", status=200, json={})
    waiting = semantic_runtime.continue_after_resolution(
        _attempt_key(run.run_id, 1), "not_applied"
    )

    # A11 rule 3: `not_applied` — the element waits again with reason
    # `owner_approval`; the next send needs a fresh approval even where a
    # grant exists, requested in the owner's same request.
    assert _v(waiting.status) == "awaiting_approval"
    approvals = _approvals(semantic_runtime, run.run_id)
    assert len(approvals) == 1
    fresh = approvals[0]
    assert _v(fresh.status) == "requested"
    assert fresh.attempt_number == 2
    assert _waits(waiting) == [("send", None, "owner_approval", fresh.approval_id)]
    assert len(stub.requests) == 1

    done = semantic_runtime.continue_after_approval(fresh.approval_id, "approve")

    assert _v(done.status) == "succeeded"
    assert len(stub.requests) == 2
    attempts = _attempts(semantic_runtime, run.run_id)
    assert [
        (a.attempt_number, _v(a.status), _authority(a)) for a in attempts
    ] == [
        (1, "not_applied", ("grant", grant.grant_id)),
        (2, "applied", ("approval", fresh.approval_id)),
    ]
    assert _v(attempts[0].resolved_by.kind) == "owner"
    executions = _executions(semantic_runtime, run.run_id)
    assert [(e.attempt_number, _v(e.status)) for e in executions] == [
        (1, "outcome_unknown"),
        (2, "succeeded"),
    ]


def test_applied_with_outputs_fails_element(semantic_runtime):
    """[witness: verification:kernel_a11_applied_with_outputs_fails_element]

    A11 Required test 5: resolving `applied` for a binding with output ports
    counts the element failed with reason `applied_outputs_unknown`; the
    attempt's one NodeExecution keeps `outcome_unknown` and the resolution
    writes none.
    """
    stub = semantic_runtime.stub_service()
    stub.on("POST", "/drafts", action="drop_after_request")
    stub.on("GET", "/notify", status=200, json={})
    _install_service(
        semantic_runtime,
        stub,
        [
            _capability("create_draft", "POST /drafts", "draft-write"),
            _capability("notify", "GET /notify", "read"),
        ],
    )
    send_binding, _ = _send_then_notify(semantic_runtime, "a11_outputs")

    run = semantic_runtime.start_run("a11_outputs", _title("with outputs"))
    assert _waits(run) == [("send", None, "outcome_unknown", None)]
    before = _executions(semantic_runtime, run.run_id)
    assert [(e.node_id, e.attempt_number, _v(e.status)) for e in before] == [
        ("send", 1, "outcome_unknown")
    ]

    done = semantic_runtime.continue_after_resolution(
        _attempt_key(run.run_id, 1), "applied"
    )

    # A11 rule 3: `applied`, binding with output ports — the element counts as
    # failed (`applied_outputs_unknown`): its dependant concludes
    # `upstream_failed` without being sent (A13 rule 5) and the run ends
    # `failed` (A13 rule 7). The reason itself is carried by no record: the
    # resolution writes no NodeExecution.
    assert _v(done.status) == "failed"
    assert _waits(done) == []
    send_records = _executions(semantic_runtime, run.run_id, "send")
    assert len(send_records) == 1
    assert send_records[0].attempt_number == 1
    assert _v(send_records[0].status) == "outcome_unknown"
    assert send_records[0].executed.binding_id == send_binding
    assert tuple(send_records[0].outputs) == ()
    assert send_records[0] == before[0]
    notify_records = _executions(semantic_runtime, run.run_id, "notify")
    assert [_v(r.status) for r in notify_records] == ["upstream_failed"]
    assert _sent(stub, "GET") == []
    attempts = _attempts(semantic_runtime, run.run_id)
    assert [(a.attempt_number, _v(a.status)) for a in attempts] == [(1, "applied")]
    assert _v(attempts[0].resolved_by.kind) == "owner"
    assert len(_sent(stub, "POST")) == 1


def test_unknown_blocks_dependants(semantic_runtime):
    """[witness: verification:kernel_a11_unknown_blocks_dependants]

    A11 Required test 6: while an element's attempt is `unknown`, the element
    waits with reason `outcome_unknown`, no node depending on it runs, and no
    request is sent again for it until the owner resolves the attempt.
    """
    stub = semantic_runtime.stub_service()
    stub.on("POST", "/drafts", action="drop_after_request")
    stub.on("GET", "/notify", status=200, json={})
    _install_service(
        semantic_runtime,
        stub,
        [
            _capability("create_draft", "POST /drafts", "draft-write"),
            _capability("notify", "GET /notify", "read"),
        ],
    )
    _send_then_notify(semantic_runtime, "a11_blocks")

    run = semantic_runtime.start_run("a11_blocks", _title("blocked"))

    # A11 rule 2: the element waits with reason `outcome_unknown`; nothing
    # depending on it runs.
    assert _v(run.status) == "pending"
    assert _waits(run) == [("send", None, "outcome_unknown", None)]
    assert _executions(semantic_runtime, run.run_id, "notify") == []
    assert len(_sent(stub, "POST")) == 1
    assert _sent(stub, "GET") == []

    # From here on the service would answer a resend.
    stub.on("POST", "/drafts", status=200, json={"draft_id": 7})

    # A resume resends only `service_unreachable` elements (A14 rule 2): with
    # none, it is refused and sends nothing.
    with pytest.raises(Exception) as exc:
        semantic_runtime.resume_run(run.run_id)
    assert exc.value.code == "refused"
    # Neither time nor a restart sends again (A11 rules 2 and 4).
    semantic_runtime.clock.advance(days=7)
    assert semantic_runtime.restart().started is True
    rested = semantic_runtime.read_run(run.run_id)
    assert _v(rested.status) == "pending"
    assert _waits(rested) == [("send", None, "outcome_unknown", None)]
    assert _executions(semantic_runtime, run.run_id, "notify") == []
    assert len(_sent(stub, "POST")) == 1
    assert _sent(stub, "GET") == []
    assert [_v(a.status) for a in _attempts(semantic_runtime, run.run_id)] == [
        "unknown"
    ]

    # Control: once the owner resolves the attempt (`not_applied`) and approves
    # the resend (A11 rule 3), the element is sent again and its dependant runs.
    waiting = semantic_runtime.continue_after_resolution(
        _attempt_key(run.run_id, 1), "not_applied"
    )
    assert len(_sent(stub, "POST")) == 1
    fresh = _approvals(semantic_runtime, run.run_id)[0]
    assert _waits(waiting) == [("send", None, "owner_approval", fresh.approval_id)]
    done = semantic_runtime.continue_after_approval(fresh.approval_id, "approve")
    assert len(_sent(stub, "POST")) == 2
    assert [r.target for r in _sent(stub, "GET")] == ["/notify?draft_id=7"]
    assert _v(done.status) == "succeeded"
    assert [
        _v(r.status) for r in _executions(semantic_runtime, run.run_id, "notify")
    ] == ["succeeded"]


def test_attempt_number_is_execution_ordinal(semantic_runtime):
    """[witness: verification:kernel_a11_attempt_number_is_execution_ordinal]

    A11 Required test 7: a `state-transition` element that waits for approval,
    is sent, ends `unknown`, is resolved `not_applied`, waits again and is
    resent with success has exactly two NodeExecutions, numbered 1 and 2; each
    EffectAttempt carries the number of the NodeExecution that concluded its
    send, and each approval the number of the attempt it was requested for;
    waiting and resolving take no number.
    """
    stub = semantic_runtime.stub_service()
    stub.on("POST", "/items", action="drop_after_request")
    _install_service(
        semantic_runtime,
        stub,
        [_capability("publish", "POST /items", "state-transition")],
    )
    _send_only(semantic_runtime, "a11_ordinal")

    # Waiting for approval takes no number (A11 rule 1).
    run = semantic_runtime.start_run("a11_ordinal", _title("ordinal"))
    first = _approvals(semantic_runtime, run.run_id)[0]
    assert first.attempt_number == 1
    assert _executions(semantic_runtime, run.run_id) == []
    assert _attempts(semantic_runtime, run.run_id) == []

    semantic_runtime.continue_after_approval(first.approval_id, "approve")
    assert [
        (e.attempt_number, _v(e.status))
        for e in _executions(semantic_runtime, run.run_id)
    ] == [(1, "outcome_unknown")]

    # Resolving takes no number and writes no NodeExecution (A11 rule 3).
    stub.on("POST", "/items", status=200, json={})
    semantic_runtime.continue_after_resolution(
        _attempt_key(run.run_id, 1), "not_applied"
    )
    assert [
        (e.attempt_number, _v(e.status))
        for e in _executions(semantic_runtime, run.run_id)
    ] == [(1, "outcome_unknown")]
    approvals = _approvals(semantic_runtime, run.run_id)
    assert len(approvals) == 2
    second = approvals[1]
    # A11 rule 1: an approval carries the next number when it is requested.
    assert second.attempt_number == 2
    assert len(_executions(semantic_runtime, run.run_id)) == 1

    done = semantic_runtime.continue_after_approval(second.approval_id, "approve")
    assert _v(done.status) == "succeeded"

    executions = _executions(semantic_runtime, run.run_id)
    assert [(e.attempt_number, _v(e.status)) for e in executions] == [
        (1, "outcome_unknown"),
        (2, "succeeded"),
    ]
    attempts = _attempts(semantic_runtime, run.run_id)
    # A11 rule 1: each EffectAttempt carries the number of the NodeExecution
    # that concluded its send.
    assert [(a.attempt_number, _v(a.status), _authority(a)) for a in attempts] == [
        (1, "not_applied", ("approval", first.approval_id)),
        (2, "applied", ("approval", second.approval_id)),
    ]
    assert [a.attempt_number for a in attempts] == [
        e.attempt_number for e in executions
    ]
    assert [
        (a.approval_id, a.attempt_number, _v(a.status))
        for a in _approvals(semantic_runtime, run.run_id)
    ] == [(first.approval_id, 1, "used"), (second.approval_id, 2, "used")]
    assert len(stub.requests) == 2
