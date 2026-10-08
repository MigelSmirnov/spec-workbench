"""Witness tests for accepted decision A17 (02_rules_installation.md).

Secrets and service instances are the installation's: a credential is resolved
from its secret file only while a request to its service is built, is never
written by the kernel anywhere, and a service's instance is the one the
installation selects. Each test carries the witness name its Required test
declares.

The Factory project supplies the ``semantic_runtime`` pytest fixture. It binds
these scenarios to the generated public operations of State 5 — named here by
their operation names, with arguments shaped as the State 6 models — without
changing the assertions below. Each test gets a fresh, empty kernel store.

Fixture surface used here:

- ``propose_binding(service_id, operation_name, inputs, outputs)`` ->
  OperationBinding (acts as agent ``author``);
  ``accept_binding(binding_id)`` -> OperationBinding (acts as the owner);
- ``compose_flow_version(flow_id, purpose, inputs, outputs, nodes, edges,
  constants)`` -> ComposedFlowVersion (acts as agent ``author``);
  ``activate_flow_version(flow_version_id)`` -> FlowActivation;
- ``start_run(flow_id, inputs)`` -> ShownRun; ``continue_after_approval(
  approval_id, decision)`` -> ShownRun;
- ``page_records(record_type, record_filter, page_size)`` ->
  RecordPageAnswer, for the trace and the approvals of a run;
- capabilities: ``manifest.write_record``, ``stub_service()``,
  ``installation.select_instance``, ``installation.set_credential``,
  ``installation.write_secret``, ``installation.set_config_mode``,
  ``restart()``, ``mcp_request``, ``store_dump()``, ``host_output()``,
  ``process_arguments()``, ``surface_answers()``.
"""

import pytest

TEXT = '{"type":"string"}'

CANARY = "a17-canary-credential-6f1d3c9e8b2a4d70"
CREDENTIAL_HEADER = "X-Api-Key"
WITHHELD = "error body withheld: it contained the credential"


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


def _instance(instance_name, stub):
    return {
        "instance_name": instance_name,
        "api_base_url": stub.base_url,
        "required_headers": None,
        "instance_class": "local_dev",
    }


def _record(service_id, capabilities, instances):
    return {
        "service": service_id,
        "capabilities": capabilities,
        "instances": instances,
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


def _json_input(port, json_text):
    return {"payload_kind": "json", "port": port, "json_text": json_text}


def _value(x):
    return getattr(x, "value", x)


def _by_run(run_id):
    return {"filter_kind": "equals", "field": "run_id", "value": run_id}


def _executions(semantic_runtime, run_id):
    page = semantic_runtime.page_records(
        "node_execution", _by_run(run_id), page_size=200
    )
    return page.records.node_executions


def _header_values(request, name):
    return [value for key, value in request.headers if key.lower() == name.lower()]


def _contains(haystack, needle):
    """True when the text `needle` occurs in anything `haystack` holds."""
    if isinstance(haystack, (bytes, bytearray)):
        return needle.encode("utf-8") in haystack
    if isinstance(haystack, str):
        return needle in haystack
    if isinstance(haystack, dict):
        return any(
            _contains(key, needle) or _contains(value, needle)
            for key, value in haystack.items()
        )
    if isinstance(haystack, (list, tuple, set, frozenset)):
        return any(_contains(item, needle) for item in haystack)
    return needle in str(haystack)


def _fetch_binding(semantic_runtime, service_id):
    """A `read` binding of `GET /notes/{note_id}` answering member `note`."""
    proposed = semantic_runtime.propose_binding(
        service_id,
        "fetch_note",
        inputs=[_port("note_id", "input", TEXT, "open")],
        outputs=[_port("note", "output", TEXT, "open")],
    )
    return semantic_runtime.accept_binding(proposed.binding_id).binding_id


def _fetch_flow(semantic_runtime, flow_id, binding_id):
    """flow input note_id -> fetch(binding) -> flow output note; activated."""
    composed = semantic_runtime.compose_flow_version(
        flow_id,
        purpose=f"A17 witness: {flow_id}",
        inputs=[_port("note_id", "input", TEXT, "open")],
        outputs=[_port("note", "output", TEXT)],
        nodes=[_operation_node("fetch", binding_id)],
        edges=[
            _edge("", "note_id", "fetch", "note_id"),
            _edge("fetch", "note", "", "note"),
        ],
        constants=[],
    )
    assert composed.proof.proven is True
    semantic_runtime.activate_flow_version(composed.flow_version.flow_version_id)
    return flow_id


def test_canary_credential_never_written(semantic_runtime):
    """[witness: verification:kernel_a17_canary_credential_never_written]

    A17 Required test 1: a canary credential appears in no store record, trace,
    preview, failure detail, log line, process argument or response after a run
    that used it.
    """
    stub = semantic_runtime.stub_service()
    stub.on("GET", "/notes/n1", json={"note": "first note"})
    stub.on("POST", "/notes/n1/archive", status=409, body=b"conflict: note n1 is locked")
    semantic_runtime.manifest.write_record(
        "notes",
        _record(
            "notes",
            [
                _capability("fetch_note", "GET /notes/{note_id}", "read"),
                _capability(
                    "archive_note", "POST /notes/{note_id}/archive", "state-transition"
                ),
            ],
            [_instance("local", stub)],
        ),
    )
    semantic_runtime.installation.select_instance("notes", "local")
    semantic_runtime.installation.set_credential("notes", CREDENTIAL_HEADER, CANARY)

    fetch = _fetch_binding(semantic_runtime, "notes")
    archive = semantic_runtime.accept_binding(
        semantic_runtime.propose_binding(
            "notes",
            "archive_note",
            inputs=[_port("note_id", "input", TEXT, "open")],
            outputs=[],
        ).binding_id
    ).binding_id

    # One run uses the credential twice: a `read` send that succeeds, and a
    # `state-transition` send that first waits for approval (a preview is
    # recorded) and is then answered 409 (a failure detail is recorded).
    composed = semantic_runtime.compose_flow_version(
        "a17_canary",
        purpose="A17 witness: canary credential",
        inputs=[_port("note_id", "input", TEXT, "open")],
        outputs=[_port("note", "output", TEXT)],
        nodes=[_operation_node("archive", archive), _operation_node("fetch", fetch)],
        edges=[
            _edge("", "note_id", "archive", "note_id"),
            _edge("", "note_id", "fetch", "note_id"),
            _edge("fetch", "note", "", "note"),
        ],
        constants=[],
    )
    assert composed.proof.proven is True
    semantic_runtime.activate_flow_version(composed.flow_version.flow_version_id)

    run = semantic_runtime.start_run("a17_canary", [_json_input("note_id", '"n1"')])
    assert _value(run.status) == "awaiting_approval"
    waits = [w for w in run.waiting if w.node_id == "archive"]
    assert len(waits) == 1 and _value(waits[0].reason) == "owner_approval"

    approvals = semantic_runtime.page_records(
        "approval", _by_run(run.run_id), page_size=200
    ).records.approvals
    assert len(approvals) == 1
    preview_headers = approvals[0].preview.request.headers
    # A10 rule 7: the credential header appears by name only, lower-cased.
    credential_described = [
        h for h in preview_headers if h.name == CREDENTIAL_HEADER.lower()
    ]
    assert len(credential_described) == 1
    assert credential_described[0].value is None

    semantic_runtime.continue_after_approval(approvals[0].approval_id, "approve")

    executions = {e.node_id: e for e in _executions(semantic_runtime, run.run_id)}
    assert _value(executions["fetch"].status) == "succeeded"
    assert _value(executions["archive"].status) == "operation_refused"
    # A09 rule 7: the unused 4xx body is kept as the failure detail.
    assert executions["archive"].failure_detail.text == "conflict: note n1 is locked"

    # Control: the run did use the canary — both sends carried it as the
    # credential header (A17 rule 2), so the absences below are not vacuous.
    assert len(stub.requests) == 2
    for request in stub.requests:
        assert _header_values(request, CREDENTIAL_HEADER) == [CANARY]

    # A17 rule 2: never in the store, a record, a trace, a preview, a failure
    # detail, a log line, a process argument or a response.
    assert not _contains(semantic_runtime.store_dump(), CANARY)
    assert not _contains(semantic_runtime.host_output(), CANARY)
    assert not _contains(semantic_runtime.process_arguments(), CANARY)
    assert not _contains(semantic_runtime.surface_answers(), CANARY)


def test_config_file_owner_only(semantic_runtime):
    """[witness: verification:kernel_a17_config_file_owner_only]

    A17 Required test 2: a configuration file readable by others stops the
    start.
    """
    # Control: the installation the fixture starts with (owner-only file)
    # starts and answers.
    semantic_runtime.page_records("slot")

    # A17 rule 1: no permission for group or others, or the kernel refuses to
    # start.
    semantic_runtime.installation.set_config_mode(0o604)
    readable_by_others = semantic_runtime.restart()
    assert readable_by_others.started is False
    assert readable_by_others.exit_code not in (None, 0)

    semantic_runtime.installation.set_config_mode(0o640)
    readable_by_group = semantic_runtime.restart()
    assert readable_by_group.started is False
    assert readable_by_group.exit_code not in (None, 0)

    # Control: the same file, made owner-only again, starts on the same data
    # directory, so the refusals above came from the mode alone.
    semantic_runtime.installation.set_config_mode(0o600)
    owner_only = semantic_runtime.restart()
    assert owner_only.started is True
    semantic_runtime.page_records("slot")


def test_instance_fixed_by_installation(semantic_runtime):
    """[witness: verification:kernel_a17_instance_fixed_by_installation]

    A17 Required test 3: no request field can make an operation node reach
    another instance.
    """
    chosen = semantic_runtime.stub_service()
    other = semantic_runtime.stub_service()
    for stub in (chosen, other):
        stub.on("GET", "/notes/n1", json={"note": "first note"})
    semantic_runtime.manifest.write_record(
        "notes",
        _record(
            "notes",
            [_capability("fetch_note", "GET /notes/{note_id}", "read")],
            [_instance("chosen", chosen), _instance("other", other)],
        ),
    )
    semantic_runtime.installation.select_instance("notes", "chosen")
    semantic_runtime.installation.set_credential("notes", CREDENTIAL_HEADER, CANARY)

    author_token = semantic_runtime.installation.agent_token("author")
    owner_token = semantic_runtime.installation.owner_token
    ports_in = [_port("note_id", "input", TEXT, "open")]
    ports_out = [_port("note", "output", TEXT, "open")]

    # A16 rule 4 / A17 rule 4: a proposal naming an instance is refused as an
    # unknown field; nothing is recorded.
    with pytest.raises(Exception) as exc:
        semantic_runtime.mcp_request(
            "propose_binding",
            {
                "service_id": "notes",
                "operation_name": "fetch_note",
                "inputs": ports_in,
                "outputs": ports_out,
                "instance_name": "other",
            },
            token=author_token,
        )
    assert exc.value.code == "invalid_request"
    assert len(semantic_runtime.page_records("binding").records.bindings) == 0

    binding_id = _fetch_binding(semantic_runtime, "notes")

    # A flow node naming an instance is refused the same way.
    with pytest.raises(Exception) as exc:
        semantic_runtime.mcp_request(
            "compose_flow_version",
            {
                "flow_id": "a17_instance",
                "purpose": "A17 witness: instance",
                "inputs": ports_in,
                "outputs": [_port("note", "output", TEXT)],
                "nodes": [
                    dict(_operation_node("fetch", binding_id), instance_name="other")
                ],
                "edges": [
                    _edge("", "note_id", "fetch", "note_id"),
                    _edge("fetch", "note", "", "note"),
                ],
                "constants": [],
            },
            token=author_token,
        )
    assert exc.value.code == "invalid_request"
    assert len(semantic_runtime.page_records("flow").records.flows) == 0

    _fetch_flow(semantic_runtime, "a17_instance", binding_id)

    # A run request naming an instance is refused and starts no run.
    with pytest.raises(Exception) as exc:
        semantic_runtime.mcp_request(
            "start_run",
            {
                "flow_id": "a17_instance",
                "inputs": [_json_input("note_id", '"n1"')],
                "instance_name": "other",
            },
            token=owner_token,
        )
    assert exc.value.code == "invalid_request"
    assert len(semantic_runtime.page_records("run").records.runs) == 0
    assert len(chosen.requests) == 0 and len(other.requests) == 0

    # A run input holding the other instance's address is a value placed in
    # the path segment (A09 rules 1-2), never a target: the request goes to the
    # selected instance.
    semantic_runtime.start_run(
        "a17_instance", [_json_input("note_id", '"' + other.base_url + '"')]
    )
    assert len(chosen.requests) == 1
    assert len(other.requests) == 0

    # Control: the instance does decide where a node goes — only through the
    # installation. Selecting `other` and restarting sends there.
    semantic_runtime.installation.select_instance("notes", "other")
    assert semantic_runtime.restart().started is True
    rerun = semantic_runtime.start_run("a17_instance", [_json_input("note_id", '"n1"')])
    assert _value(rerun.status) == "succeeded"
    assert len(other.requests) == 1
    assert len(chosen.requests) == 1


def test_echoed_credential_body_withheld(semantic_runtime):
    """[witness: verification:kernel_a17_echoed_credential_body_withheld]

    A17 Required test 4: a service answer whose body echoes the canary
    credential verbatim, with a 2xx status, is withheld and never used as an
    output.
    """
    stub = semantic_runtime.stub_service()
    semantic_runtime.manifest.write_record(
        "notes",
        _record(
            "notes",
            [_capability("fetch_note", "GET /notes/{note_id}", "read")],
            [_instance("local", stub)],
        ),
    )
    semantic_runtime.installation.select_instance("notes", "local")
    semantic_runtime.installation.set_credential("notes", CREDENTIAL_HEADER, CANARY)

    binding_id = _fetch_binding(semantic_runtime, "notes")
    _fetch_flow(semantic_runtime, "a17_echo", binding_id)

    # Control: the same answer shape without the canary is used as the output,
    # so the withholding below is not a general failure of the binding.
    stub.on("GET", "/notes/n1", json={"note": "plain note"})
    control = semantic_runtime.start_run("a17_echo", [_json_input("note_id", '"n1"')])
    assert _value(control.status) == "succeeded"
    assert [_value(o.output_kind) for o in control.outputs] == ["produced"]
    assert control.outputs[0].value.json_text == '"plain note"'

    stub.on("GET", "/notes/n1", json={"note": CANARY})
    run = semantic_runtime.start_run("a17_echo", [_json_input("note_id", '"n1"')])

    # A09 rules 5 and 7: a 2xx body echoing the credential is not used — the
    # answer is `contract_violation`, the body is dropped whole and the detail
    # is exactly the withheld note; no output is stored.
    (execution,) = _executions(semantic_runtime, run.run_id)
    assert _value(execution.status) == "contract_violation"
    assert len(execution.outputs) == 0
    assert execution.failure_detail.text == WITHHELD

    # A13 rule 7: the run fails and its output is reported not produced.
    assert _value(run.status) == "failed"
    assert len(run.outputs) == 1
    assert _value(run.outputs[0].output_kind) == "missing"
    assert run.outputs[0].port == "note"
    assert _value(run.outputs[0].reason) == "not_produced"

    # The request did carry the canary, and the canary was written nowhere.
    assert _header_values(stub.requests[-1], CREDENTIAL_HEADER) == [CANARY]
    assert not _contains(semantic_runtime.store_dump(), CANARY)
    assert not _contains(semantic_runtime.surface_answers(), CANARY)


def test_credential_resolved_per_request(semantic_runtime):
    """[witness: verification:kernel_a17_credential_resolved_per_request]

    A17 Required test 5: with service A given a canary credential and service B
    none: the kernel starts while A's secret file is missing; a request to B
    fails its pre-send check `credential_unresolved`; after A's secret file is
    written, the next request to A carries its value without a restart.
    """
    stub_a = semantic_runtime.stub_service()
    stub_b = semantic_runtime.stub_service()
    for service_id, stub in (("service_a", stub_a), ("service_b", stub_b)):
        stub.on("GET", "/notes/n1", json={"note": "first note"})
        semantic_runtime.manifest.write_record(
            service_id,
            _record(
                service_id,
                [_capability("fetch_note", "GET /notes/{note_id}", "read")],
                [_instance("local", stub)],
            ),
        )
        semantic_runtime.installation.select_instance(service_id, "local")
    # A's reference names a secret file that does not exist; B has none.
    semantic_runtime.installation.set_credential("service_a", CREDENTIAL_HEADER, None)

    # A17 rule 1: a missing secret file does not stop the start (rule 2: it
    # fails only its own requests).
    semantic_runtime.page_records("slot")
    started = semantic_runtime.restart()
    assert started.started is True

    _fetch_flow(
        semantic_runtime, "a17_service_a", _fetch_binding(semantic_runtime, "service_a")
    )
    _fetch_flow(
        semantic_runtime, "a17_service_b", _fetch_binding(semantic_runtime, "service_b")
    )

    # A17 rule 2, A09 rule 6: B has no credential — its pre-send check
    # `credential_unresolved` fails, nothing is sent and no attempt exists.
    run_b = semantic_runtime.start_run("a17_service_b", [_json_input("note_id", '"n1"')])
    (execution_b,) = _executions(semantic_runtime, run_b.run_id)
    assert _value(execution_b.status) == "operation_failed"
    assert _value(execution_b.detail_code) == "credential_unresolved"
    assert len(stub_b.requests) == 0

    # While A's secret file is missing, A's request fails the same check.
    before = semantic_runtime.start_run("a17_service_a", [_json_input("note_id", '"n1"')])
    (execution_before,) = _executions(semantic_runtime, before.run_id)
    assert _value(execution_before.status) == "operation_failed"
    assert _value(execution_before.detail_code) == "credential_unresolved"
    assert len(stub_a.requests) == 0

    # A17 rule 2: the secret file is read when a request is built — written
    # now, the next request carries it, with no restart in between.
    semantic_runtime.installation.write_secret("service_a", CANARY)
    after = semantic_runtime.start_run("a17_service_a", [_json_input("note_id", '"n1"')])
    assert _value(after.status) == "succeeded"
    assert len(stub_a.requests) == 1
    assert _header_values(stub_a.requests[0], CREDENTIAL_HEADER) == [CANARY]
    assert len(stub_b.requests) == 0
