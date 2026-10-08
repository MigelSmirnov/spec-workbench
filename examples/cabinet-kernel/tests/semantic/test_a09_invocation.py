"""Witness tests for accepted decision A09 (02_rules_services.md).

An invocation is one HTTP request per attempt, never retried, redirected or
sent as plain `http` to a production host off the loopback, and every way it
ends has one name: for a `read` an element status, for any other operation
also an EffectAttempt status that says whether the effect may have happened.
Each test carries the witness name its Required test declares.

The Factory project supplies the ``semantic_runtime`` pytest fixture. It binds
these scenarios to the generated public operations of State 5 — named here by
their operation names, with arguments shaped as the State 6 models — without
changing the assertions below. Each test gets a fresh, empty kernel store; the
installation starts with the owner, agent ``author`` and agent ``helper``, no
service selected and no credential.

Fixture surface used here:

- ``propose_binding(service_id, operation_name, inputs, outputs)`` ->
  OperationBinding (M11), as agent ``author``; ``accept_binding(binding_id)``
  as the owner;
- ``compose_flow_version(flow_id, purpose, inputs, outputs, nodes, edges,
  constants)`` -> ComposedFlowVersion, as agent ``author``;
  ``activate_flow_version(flow_version_id)`` -> FlowActivation, as the owner;
- ``start_run(flow_id, inputs)`` and ``resume_run(run_id)`` -> ShownRun, as
  the owner; inputs are RequestJsonValue dicts;
- ``page_records(record_type, record_filter, page_size)`` -> RecordPageAnswer:
  ``node_execution`` (the trace), ``effect_attempt`` and ``approval``;
- capabilities: ``manifest.write_record``, ``installation.select_instance``,
  ``installation.set_credential``, ``stub_service`` (routes, ``action``,
  ``requests``) and ``store_dump``.
"""

import pytest

TEXT = '{"type":"string"}'
NUMBER = '{"type":"integer"}'

SERVICE = "drafts"
INSTANCE = "rig"
CREDENTIAL_HEADER = "X-Api-Key"
CREDENTIAL = "a09-canary-credential-5e1b"
WITHHELD = "error body withheld: it contained the credential"


def _port(name, direction, schema, disclosure_class="open"):
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


# create_draft: a `draft-write`, sent under the flow activation without asking
# (A10 rules 1 and 6); find_drafts: a `read`, which writes no EffectAttempt.
CAPABILITIES = [
    _capability("create_draft", "POST /drafts", "draft-write"),
    _capability("find_drafts", "GET /drafts", "read"),
]
DRAFT_INPUTS = [_port("title", "input", TEXT)]
DRAFT_OUTPUTS = [_port("draft_id", "output", TEXT)]
FIND_INPUTS = [_port("q", "input", TEXT)]
FIND_OUTPUTS = [_port("count", "output", NUMBER)]


def _install(semantic_runtime, service_id, base_url, instance_class="disposable_rig"):
    """Write the service's record, select its instance, give it a credential."""
    semantic_runtime.manifest.write_record(
        service_id,
        {
            "service": service_id,
            "capabilities": CAPABILITIES,
            "instances": [
                {
                    "instance_name": INSTANCE,
                    "api_base_url": base_url,
                    "required_headers": None,
                    "instance_class": instance_class,
                }
            ],
        },
    )
    semantic_runtime.installation.select_instance(service_id, INSTANCE)
    semantic_runtime.installation.set_credential(
        service_id, CREDENTIAL_HEADER, CREDENTIAL
    )


def _node(node_id, binding_id):
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


def _value(port, json_text):
    return {"payload_kind": "json", "port": port, "json_text": json_text}


def _enum(value):
    return getattr(value, "value", value)


def _operation_flow(semantic_runtime, flow_id, service_id, operation_name, inputs, outputs):
    """An accepted binding and an active flow of one operation node `op`, its
    ports wired to the flow's own inputs and outputs (node "", A05 rule 2)."""
    binding = semantic_runtime.propose_binding(service_id, operation_name, inputs, outputs)
    semantic_runtime.accept_binding(binding.binding_id)
    composed = semantic_runtime.compose_flow_version(
        flow_id,
        purpose=f"A09 witness: {flow_id}",
        inputs=[_port(p["name"], "input", p["value_schema"]) for p in inputs],
        outputs=[_port(p["name"], "output", p["value_schema"], None) for p in outputs],
        nodes=[_node("op", binding.binding_id)],
        edges=[_edge("", p["name"], "op", p["name"]) for p in inputs]
        + [_edge("op", p["name"], "", p["name"]) for p in outputs],
        constants=[],
    )
    assert composed.proof.proven is True
    semantic_runtime.activate_flow_version(composed.flow_version.flow_version_id)
    return binding.binding_id


def _by_run(run_id):
    return {"filter_kind": "equals", "field": "run_id", "value": run_id}


def _trace(semantic_runtime, run_id):
    page = semantic_runtime.page_records(
        "node_execution", _by_run(run_id), page_size=200
    )
    return page.records.node_executions


def _attempts(semantic_runtime, run_id):
    page = semantic_runtime.page_records(
        "effect_attempt", _by_run(run_id), page_size=200
    )
    return page.records.effect_attempts


def _approvals(semantic_runtime, run_id):
    page = semantic_runtime.page_records(
        "approval", _by_run(run_id), page_size=200
    )
    return page.records.approvals


def _waits(run):
    return [(w.node_id, _enum(w.reason)) for w in run.waiting]


def _detail_text(execution):
    detail = execution.failure_detail
    assert _enum(detail.detail_kind) == "text"
    return detail.text


def _header_values(request, name):
    return [v for (n, v) in request.headers if n.lower() == name.lower()]


def test_possibly_sent_outcome_unknown_no_retry(semantic_runtime):
    """[witness: verification:kernel_a09_possibly_sent_outcome_unknown_no_retry]

    A09 Required test 1: a `POST` whose connection drops after the request was
    written concludes `outcome_unknown` and no second request is sent.
    """
    stub = semantic_runtime.stub_service()
    stub.on("POST", "/drafts", action="drop_after_request")
    _install(semantic_runtime, SERVICE, stub.base_url)
    binding_id = _operation_flow(
        semantic_runtime, "a09_dropped", SERVICE, "create_draft", DRAFT_INPUTS, DRAFT_OUTPUTS
    )

    run = semantic_runtime.start_run("a09_dropped", [_value("title", '"Q3 report"')])

    # A09 rule 1: one request per attempt, nothing retried inside it.
    assert len(stub.requests) == 1
    assert stub.requests[0].method == "POST"
    assert stub.requests[0].target == "/drafts"

    # A09 rule 5: may have been sent, no final response -> `outcome_unknown`,
    # attempt `unknown`.
    (execution,) = _trace(semantic_runtime, run.run_id)
    assert execution.node_id == "op"
    assert execution.attempt_number == 1
    assert _enum(execution.status) == "outcome_unknown"
    assert execution.executed.binding_id == binding_id
    assert list(execution.outputs) == []
    (attempt,) = _attempts(semantic_runtime, run.run_id)
    assert attempt.attempt_number == 1
    assert attempt.binding_id == binding_id
    assert _enum(attempt.status) == "unknown"
    assert attempt.resolved_by is None
    # A10 rule 6: a `draft-write` send names the flow activation.
    assert _enum(attempt.authority.authority_kind) == "flow_activation"

    # A11 rule 2, A13 rule 8: the element waits, the run rests `pending`.
    assert _enum(run.status) == "pending"
    assert _waits(run) == [("op", "outcome_unknown")]

    # A14 rule 2: a resume resends only `service_unreachable` elements; this
    # run has none, so it is refused and still nothing is sent again.
    with pytest.raises(Exception) as exc:
        semantic_runtime.resume_run(run.run_id)
    assert exc.value.code == "refused"
    assert len(stub.requests) == 1
    again = semantic_runtime.read_run(run.run_id)
    assert _enum(again.status) == "pending"
    assert len(_trace(semantic_runtime, run.run_id)) == 1


def test_read_5xx_service_unreachable(semantic_runtime):
    """[witness: verification:kernel_a09_read_5xx_service_unreachable]

    A09 Required test 2: a `read` answered 503 rests the run `pending` with
    `service_unreachable`.
    """
    stub = semantic_runtime.stub_service()
    stub.on("GET", "/drafts", status=503, body=b"maintenance")
    _install(semantic_runtime, SERVICE, stub.base_url)
    _operation_flow(
        semantic_runtime, "a09_read_503", SERVICE, "find_drafts", FIND_INPUTS, FIND_OUTPUTS
    )

    run = semantic_runtime.start_run("a09_read_503", [_value("q", '"report"')])

    # A09 rule 5: a `read` answered 5xx is `service_unreachable`; A13 rules 5
    # and 8: a wait, not a failure, so the run rests `pending`.
    assert _enum(run.status) == "pending"
    assert run.ended_at is None
    assert _waits(run) == [("op", "service_unreachable")]
    (execution,) = _trace(semantic_runtime, run.run_id)
    assert _enum(execution.status) == "service_unreachable"
    assert list(execution.outputs) == []
    # A10 rule 6: a `read` send has no EffectAttempt.
    assert list(_attempts(semantic_runtime, run.run_id)) == []
    assert len(stub.requests) == 1

    # Control: the run really rests — once the service answers, a resume
    # sends the read again and the run completes with its output.
    stub.on("GET", "/drafts", status=200, json={"count": 3})
    resumed = semantic_runtime.resume_run(run.run_id)
    assert _enum(resumed.status) == "succeeded"
    assert len(stub.requests) == 2
    (output,) = resumed.outputs
    assert output.port == "count"
    assert output.value.json_text == "3"


def test_non_read_4xx_not_applied(semantic_runtime):
    """[witness: verification:kernel_a09_non_read_4xx_not_applied]

    A09 Required test 3: a `draft-write` answered 409 concludes
    `operation_refused` with the attempt `not_applied`.
    """
    stub = semantic_runtime.stub_service()
    stub.on(
        "POST",
        "/drafts",
        status=409,
        body=b"draft already exists",
        headers={"Content-Type": "text/plain"},
    )
    _install(semantic_runtime, SERVICE, stub.base_url)
    _operation_flow(
        semantic_runtime, "a09_conflict", SERVICE, "create_draft", DRAFT_INPUTS, DRAFT_OUTPUTS
    )

    run = semantic_runtime.start_run("a09_conflict", [_value("title", '"Q3 report"')])

    # A09 rule 5: 4xx -> `operation_refused`, attempt `not_applied`.
    (execution,) = _trace(semantic_runtime, run.run_id)
    assert _enum(execution.status) == "operation_refused"
    assert list(execution.outputs) == []
    # A09 rule 7: the unused body is kept as `failure_detail`; the class is
    # `open`, and the owner reads it as text.
    assert _detail_text(execution) == "draft already exists"
    (attempt,) = _attempts(semantic_runtime, run.run_id)
    assert _enum(attempt.status) == "not_applied"
    assert attempt.resolved_by is None

    # A13 rules 5 and 7: `operation_refused` is a failure; nothing waits, so
    # the run ends `failed`. A10 rule 1: an attempt answered 4xx is never sent
    # again.
    assert _enum(run.status) == "failed"
    assert list(run.waiting) == []
    assert len(stub.requests) == 1


def test_non_read_2xx_applied_even_if_invalid(semantic_runtime):
    """[witness: verification:kernel_a09_non_read_2xx_applied_even_if_invalid]

    A09 Required test 4: a 2xx body missing an output port's member concludes
    `contract_violation`, and for a non-read operation the attempt is
    `applied`.
    """
    stub = semantic_runtime.stub_service()
    stub.on("POST", "/drafts", status=201, json={"id": "d-1"})
    _install(semantic_runtime, SERVICE, stub.base_url)
    _operation_flow(
        semantic_runtime, "a09_invalid_2xx", SERVICE, "create_draft", DRAFT_INPUTS, DRAFT_OUTPUTS
    )

    run = semantic_runtime.start_run("a09_invalid_2xx", [_value("title", '"Q3 report"')])

    # A09 rules 3 and 5: the body has no `draft_id` member -> outputs do not
    # fit -> `contract_violation`, attempt `applied`.
    (execution,) = _trace(semantic_runtime, run.run_id)
    assert _enum(execution.status) == "contract_violation"
    assert list(execution.outputs) == []
    (attempt,) = _attempts(semantic_runtime, run.run_id)
    assert _enum(attempt.status) == "applied"
    # A13 rules 5 and 7: a failure ends the run `failed`, its output not
    # produced.
    assert _enum(run.status) == "failed"
    (missing,) = run.outputs
    assert _enum(missing.output_kind) == "missing"
    assert missing.port == "draft_id"
    assert len(stub.requests) == 1

    # Control: the same flow answered with the member succeeds, so the
    # violation above comes from the missing member, not from the status.
    stub.on("POST", "/drafts", status=201, json={"draft_id": "d-1"})
    control = semantic_runtime.start_run("a09_invalid_2xx", [_value("title", '"Q4 report"')])
    assert _enum(control.status) == "succeeded"
    (produced,) = control.outputs
    assert produced.port == "draft_id"
    assert produced.value.json_text == '"d-1"'
    (control_attempt,) = _attempts(semantic_runtime, control.run_id)
    assert _enum(control_attempt.status) == "applied"


def test_no_redirect_plain_http_restricted(semantic_runtime):
    """[witness: verification:kernel_a09_no_redirect_plain_http_restricted]

    A09 Required test 5: a redirect to another host is not followed and a
    production `http` target on a non-loopback host is refused before sending.
    """
    origin = semantic_runtime.stub_service()
    elsewhere = semantic_runtime.stub_service()
    elsewhere.on("GET", "/landing", status=200, json={"count": 1})
    port = elsewhere.authority.rsplit(":", 1)[1]
    origin.on(
        "GET",
        "/drafts",
        status=302,
        action="redirect",
        headers={"Location": f"http://localhost:{port}/landing"},
    )
    # A09 rule 4: a `production` instance on a loopback host may use `http`.
    _install(semantic_runtime, SERVICE, origin.base_url, instance_class="production")
    # A production instance on a host that is not a loopback address.
    _install(
        semantic_runtime, "remote", "http://drafts.example.test", instance_class="production"
    )
    _operation_flow(
        semantic_runtime, "a09_redirect", SERVICE, "find_drafts", FIND_INPUTS, FIND_OUTPUTS
    )
    _operation_flow(
        semantic_runtime, "a09_plain_http", "remote", "create_draft", DRAFT_INPUTS, DRAFT_OUTPUTS
    )

    redirected = semantic_runtime.start_run("a09_redirect", [_value("q", '"report"')])

    # A09 rule 1: redirects are not followed — one request, to the origin.
    assert len(origin.requests) == 1
    assert len(elsewhere.requests) == 0
    # A09 rule 5: a `read` answered 3xx is `operation_failed`
    # (`redirect_not_followed`, State 5 closed details).
    (execution,) = _trace(semantic_runtime, redirected.run_id)
    assert _enum(execution.status) == "operation_failed"
    assert _enum(execution.detail_code) == "redirect_not_followed"
    assert _enum(redirected.status) == "failed"

    plain = semantic_runtime.start_run("a09_plain_http", [_value("title", '"Q3 report"')])

    # A09 rules 4 and 6: plain `http` to a production non-loopback host is a
    # pre-send failure: `operation_failed` with `plain_http_not_allowed`, and
    # no EffectAttempt exists for it.
    (refused,) = _trace(semantic_runtime, plain.run_id)
    assert _enum(refused.status) == "operation_failed"
    assert _enum(refused.detail_code) == "plain_http_not_allowed"
    assert list(_attempts(semantic_runtime, plain.run_id)) == []
    assert list(_approvals(semantic_runtime, plain.run_id)) == []
    assert _enum(plain.status) == "failed"
    # Nothing reached either stub for that run.
    assert len(origin.requests) == 1
    assert len(elsewhere.requests) == 0


def test_credential_echo_error_body_withheld(semantic_runtime):
    """[witness: verification:kernel_a09_credential_echo_error_body_withheld]

    A09 Required test 7: a 401 whose body echoes the credential value keeps
    `failure_detail` exactly `error body withheld: it contained the
    credential`, and the credential appears in no record.
    """
    stub = semantic_runtime.stub_service()
    stub.on(
        "POST",
        "/drafts",
        status=401,
        body=f"invalid key {CREDENTIAL}".encode("utf-8"),
        headers={"Content-Type": "text/plain"},
    )
    _install(semantic_runtime, SERVICE, stub.base_url)
    _operation_flow(
        semantic_runtime, "a09_echo_401", SERVICE, "create_draft", DRAFT_INPUTS, DRAFT_OUTPUTS
    )

    run = semantic_runtime.start_run("a09_echo_401", [_value("title", '"Q3 report"')])

    # The request carried the credential the body echoes (A09 rule 1).
    (request,) = stub.requests
    assert _header_values(request, CREDENTIAL_HEADER) == [CREDENTIAL]

    # A09 rule 5: 4xx -> `operation_refused`, attempt `not_applied`; rule 7:
    # the body is dropped whole and replaced by the fixed note.
    (execution,) = _trace(semantic_runtime, run.run_id)
    assert _enum(execution.status) == "operation_refused"
    assert _detail_text(execution) == WITHHELD
    (attempt,) = _attempts(semantic_runtime, run.run_id)
    assert _enum(attempt.status) == "not_applied"

    # A17 rule 2: the kernel never puts the value into the store.
    assert CREDENTIAL.encode("utf-8") not in semantic_runtime.store_dump()

    # Control: a 401 whose body does not echo the credential keeps its body,
    # so the note above comes from the echo, not from every 401.
    stub.on(
        "POST",
        "/drafts",
        status=401,
        body=b"invalid key",
        headers={"Content-Type": "text/plain"},
    )
    control = semantic_runtime.start_run("a09_echo_401", [_value("title", '"Q4 report"')])
    (control_execution,) = _trace(semantic_runtime, control.run_id)
    assert _enum(control_execution.status) == "operation_refused"
    assert _detail_text(control_execution) == "invalid key"


def test_credential_echo_2xx_no_output_stored(semantic_runtime):
    """[witness: verification:kernel_a09_credential_echo_2xx_no_output_stored]

    A09 Required test 8: a 2xx JSON body that echoes the credential value in a
    member an output port takes concludes `contract_violation` with that same
    `failure_detail`, and no StoredValue holds the credential.
    """
    stub = semantic_runtime.stub_service()
    stub.on("POST", "/drafts", status=200, json={"draft_id": CREDENTIAL})
    _install(semantic_runtime, SERVICE, stub.base_url)
    _operation_flow(
        semantic_runtime, "a09_echo_2xx", SERVICE, "create_draft", DRAFT_INPUTS, DRAFT_OUTPUTS
    )

    run = semantic_runtime.start_run("a09_echo_2xx", [_value("title", '"Q3 report"')])
    assert len(stub.requests) == 1

    # A09 rules 5 and 7: the echoing 2xx body is not used -> `contract_violation`
    # with the fixed note, no output stored; the attempt is `applied` (owner,
    # 2026-10-05).
    (execution,) = _trace(semantic_runtime, run.run_id)
    assert _enum(execution.status) == "contract_violation"
    assert _detail_text(execution) == WITHHELD
    assert list(execution.outputs) == []
    (attempt,) = _attempts(semantic_runtime, run.run_id)
    assert _enum(attempt.status) == "applied"
    assert _enum(run.status) == "failed"
    (missing,) = run.outputs
    assert _enum(missing.output_kind) == "missing"

    # No StoredValue (nor any other record) holds the credential.
    assert CREDENTIAL.encode("utf-8") not in semantic_runtime.store_dump()

    # Control: the same member with another value is stored as the output, so
    # the absence above comes from the echo, not from outputs never stored.
    stub.on("POST", "/drafts", status=200, json={"draft_id": "d-1"})
    control = semantic_runtime.start_run("a09_echo_2xx", [_value("title", '"Q4 report"')])
    assert _enum(control.status) == "succeeded"
    (produced,) = control.outputs
    assert produced.value.json_text == '"d-1"'
    (control_execution,) = _trace(semantic_runtime, control.run_id)
    assert len(control_execution.outputs) == 1


def test_read_unsent_or_unanswered_unreachable(semantic_runtime):
    """[witness: verification:kernel_a09_read_unsent_or_unanswered_unreachable]

    A09 Required test 9: a `read` whose connection is refused before the first
    byte of the request is written, and a `read` whose connection drops after
    the request was written, each conclude `service_unreachable`, and no
    second request is sent.
    """
    stub = semantic_runtime.stub_service()
    stub.on("GET", "/drafts", action="refuse_connection")
    _install(semantic_runtime, SERVICE, stub.base_url)
    _operation_flow(
        semantic_runtime, "a09_read_lost", SERVICE, "find_drafts", FIND_INPUTS, FIND_OUTPUTS
    )

    # Nothing could be sent (A09 rule 5, first row).
    unsent = semantic_runtime.start_run("a09_read_lost", [_value("q", '"one"')])
    assert len(stub.requests) == 0
    (unsent_execution,) = _trace(semantic_runtime, unsent.run_id)
    assert _enum(unsent_execution.status) == "service_unreachable"
    assert _enum(unsent.status) == "pending"
    assert _waits(unsent) == [("op", "service_unreachable")]

    # May have been sent, no final response (A09 rule 5, second row): for a
    # `read` the same name.
    stub.on("GET", "/drafts", action="drop_after_request")
    unanswered = semantic_runtime.start_run("a09_read_lost", [_value("q", '"two"')])
    # A09 rule 1: nothing retried inside one attempt — one request in all.
    assert len(stub.requests) == 1
    (unanswered_execution,) = _trace(semantic_runtime, unanswered.run_id)
    assert _enum(unanswered_execution.status) == "service_unreachable"
    assert _enum(unanswered.status) == "pending"
    assert _waits(unanswered) == [("op", "service_unreachable")]

    # A10 rule 6: a `read` writes no EffectAttempt in either case.
    assert list(_attempts(semantic_runtime, unsent.run_id)) == []
    assert list(_attempts(semantic_runtime, unanswered.run_id)) == []

    # Neither run was sent again between requests (A13 rule 1).
    assert len(_trace(semantic_runtime, unsent.run_id)) == 1
    assert len(stub.requests) == 1
