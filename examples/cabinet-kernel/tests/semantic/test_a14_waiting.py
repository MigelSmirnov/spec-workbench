"""Witness tests for accepted decision A14 (02_rules_runs.md).

A run rests with one waiting point per waiting element; no time limit ends,
fails, approves or retries anything. Resume resends only elements waiting on an
unreachable service, cancel is the owner's and ends an unended run, a run's
spool is emptied when it ends `succeeded`, `refused` or `cancelled` and kept
for a `failed` run until it is released, and on start the kernel turns
`in_flight` attempts `unknown` and advances runs left `running` before the
surface answers. Each test carries the witness name its Required test declares.

The Factory project supplies the ``semantic_runtime`` pytest fixture. It binds
these scenarios to the generated public operations of State 5 — named here by
their operation names, with arguments shaped as the State 6 models — without
changing the assertions below. Each test gets a fresh, empty kernel store.

Fixture surface used here:

- ``issue_contract_version(slot_id, purpose, inputs, outputs)`` ->
  contract_version_id; ``add_trial_case(contract_version_id, inputs)`` ->
  ShownAddedTrialCase; ``submit_implementation(contract_version_id, code)`` ->
  ShownSubmission, which activates an admitted implementation (A04 rule 4);
  all three act as agent ``author``;
- ``propose_binding(service_id, operation_name, inputs, outputs)`` ->
  OperationBinding (agent ``author``); ``accept_binding(binding_id)`` ->
  OperationBinding (the owner);
- ``compose_flow_version(flow_id, purpose, inputs, outputs, nodes, edges,
  constants)`` -> ComposedFlowVersion (agent ``author``);
  ``activate_flow_version(flow_version_id)`` -> FlowActivation (the owner);
- ``start_run(flow_id, inputs)``, ``resume_run(run_id)``,
  ``release_run(run_id)``, ``cancel_run(run_id)``,
  ``continue_after_approval(approval_id, decision)``, ``read_run(run_id)`` ->
  ShownRun; inputs are RequestJsonValue dicts;
- ``page_records(record_type, record_filter, page_size)`` -> RecordPageAnswer;
  runs, node executions, effect attempts and approvals are read from its
  ``records`` (newest first);
- ``read_spooled_file(file)`` -> SpooledFileContent, ``file`` a SpooledFileKey
  dict (owner only);
- every call takes ``actor=`` (an Actor M27 dict); omitted, it is the owner
  for owner operations and agent ``author`` for authoring operations.

Capabilities used here: ``stub_service()`` (a loopback HTTP service whose
received requests are listed in ``stub.requests``; ``set_down``, ``action``
``"drop_after_request"`` and ``"kill_kernel"``), ``manifest.write_record``,
``installation.select_instance``, ``installation.set_credential``,
``run_spool(run_id)``, ``kill_on_sandbox_start(nth)``, ``KernelStopped``,
``restart()`` and ``clock.advance``.
"""

import base64
import json

import pytest

OWNER = {"kind": "owner", "agent_name": None}
AUTHOR = {"kind": "agent", "agent_name": "author"}
HELPER = {"kind": "agent", "agent_name": "helper"}

TEXT = '{"type":"string"}'
NUMBER = '{"type":"integer"}'
FILE_SCHEMA = "{}"
PHOTO = "image/png"

INSTANCE = "rig"
CREDENTIAL_HEADER = "X-Api-Key"

# A20 rule 1, release v1
TRANSPORT_TIMEOUT_MS = 60000

UPPER_CODE = """
def run(inputs):
    return {"y": inputs["x"].upper()}
"""

PHOTO_CODE = """
def run(inputs):
    return {"photo": inputs["x"].encode("utf-8")}
"""

CHECK_CODE = """
def run(inputs):
    photo = inputs["photo"]
    if photo.startswith(b"crash"):
        raise ValueError("unreadable photo")
    return {"size": len(photo)}
"""


def _v(x):
    return getattr(x, "value", x)


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


def _file_port(name, direction, disclosure_class=None):
    return {
        "name": name,
        "direction": direction,
        "value_schema": FILE_SCHEMA,
        "carriage": "file",
        "media_type": PHOTO,
        "cardinality": "one",
        "disclosure_class": disclosure_class,
    }


def _json(port, value):
    return {"payload_kind": "json", "port": port, "json_text": json.dumps(value)}


def _file(port, content):
    return {
        "payload_kind": "file",
        "port": port,
        "content_base64": base64.b64encode(content).decode("ascii"),
    }


def _service(semantic_runtime, service_id, operations):
    """A stub service, its manifest record, selected instance and credential.

    ``operations`` are (name, method, path, effect_class). Written before the
    kernel's first start, so the first start reads them.
    """
    stub = semantic_runtime.stub_service()
    semantic_runtime.manifest.write_record(
        service_id,
        {
            "service": service_id,
            "capabilities": [
                {
                    "name": name,
                    "exposed_as": {"http_api": [f"{method} {path}"]},
                    "effect_class": effect_class,
                    "idempotency_key": None,
                }
                for name, method, path, effect_class in operations
            ],
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
    semantic_runtime.installation.select_instance(service_id, INSTANCE)
    # A17 rule 2: a service without a credential fails its pre-send check.
    semantic_runtime.installation.set_credential(
        service_id, CREDENTIAL_HEADER, f"{service_id}-a14-credential-value"
    )
    return stub


def _binding(semantic_runtime, service_id, operation_name, inputs, outputs=()):
    proposed = semantic_runtime.propose_binding(
        service_id, operation_name, inputs=list(inputs), outputs=list(outputs)
    )
    return semantic_runtime.accept_binding(proposed.binding_id).binding_id


def _note_binding(semantic_runtime, service_id, operation_name):
    """An accepted binding with one `value` input `note` and no output ports."""
    return _binding(
        semantic_runtime,
        service_id,
        operation_name,
        inputs=[_port("note", "input", TEXT, "open")],
    )


def _function(semantic_runtime, slot_id, inputs, outputs, code, trial_inputs):
    """A contract version with one passing trial case and an admitted, active
    implementation."""
    contract_version_id = semantic_runtime.issue_contract_version(
        slot_id,
        purpose=f"A14 witness: {slot_id}",
        inputs=inputs,
        outputs=outputs,
    )
    semantic_runtime.add_trial_case(contract_version_id, inputs=trial_inputs)
    submission = semantic_runtime.submit_implementation(contract_version_id, code)
    assert _v(submission.verdict.verdict) == "admitted"
    assert submission.activation is not None
    return contract_version_id


def _upper_function(semantic_runtime):
    return _function(
        semantic_runtime,
        "upper",
        [_port("x", "input", TEXT, "open")],
        [_port("y", "output", TEXT)],
        UPPER_CODE,
        [_json("x", "ok")],
    )


def _photo_functions(semantic_runtime):
    """`photo` spools its input's bytes as a file; `check` crashes on a photo
    starting with b"crash" and otherwise returns its size."""
    photo = _function(
        semantic_runtime,
        "photo",
        [_port("x", "input", TEXT, "open")],
        [_file_port("photo", "output")],
        PHOTO_CODE,
        [_json("x", "ok-photo")],
    )
    check = _function(
        semantic_runtime,
        "check",
        [_file_port("photo", "input", "open")],
        [_port("size", "output", NUMBER)],
        CHECK_CODE,
        [_file("photo", b"ok-photo")],
    )
    return photo, check


def _fn_node(node_id, contract_version_id, map_over=None):
    return {
        "node_id": node_id,
        "kind": "function",
        "contract_version_id": contract_version_id,
        "binding_id": None,
        "map_over": map_over,
    }


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


def _active_flow(semantic_runtime, flow_id, inputs, outputs, nodes, edges):
    composed = semantic_runtime.compose_flow_version(
        flow_id,
        purpose=f"A14 witness: {flow_id}",
        inputs=inputs,
        outputs=outputs,
        nodes=nodes,
        edges=edges,
        constants=[],
    )
    assert composed.proof.proven is True
    flow_version_id = composed.flow_version.flow_version_id
    semantic_runtime.activate_flow_version(flow_version_id)
    return flow_version_id


def _photo_check_flow(semantic_runtime, flow_id, photo, check):
    """word -> a_photo (spools a file) -> b_check -> flow output `size`."""
    return _active_flow(
        semantic_runtime,
        flow_id,
        inputs=[_port("word", "input", TEXT, "open")],
        outputs=[_port("size", "output", NUMBER)],
        nodes=[_fn_node("a_photo", photo), _fn_node("b_check", check)],
        edges=[
            _edge("", "word", "a_photo", "x"),
            _edge("a_photo", "photo", "b_check", "photo"),
            _edge("b_check", "size", "", "size"),
        ],
    )


def _photo_wait_flow(semantic_runtime, flow_id, photo, check, post_binding):
    """As `_photo_check_flow`, plus `c_post`, an operation fed by `word`."""
    return _active_flow(
        semantic_runtime,
        flow_id,
        inputs=[_port("word", "input", TEXT, "open")],
        outputs=[_port("size", "output", NUMBER)],
        nodes=[
            _fn_node("a_photo", photo),
            _fn_node("b_check", check),
            _op_node("c_post", post_binding),
        ],
        edges=[
            _edge("", "word", "a_photo", "x"),
            _edge("a_photo", "photo", "b_check", "photo"),
            _edge("b_check", "size", "", "size"),
            _edge("", "word", "c_post", "note"),
        ],
    )


def _by_run(run_id):
    return {"filter_kind": "equals", "field": "run_id", "value": run_id}


def _trace(semantic_runtime, run_id):
    """The run's NodeExecutions in store order."""
    page = semantic_runtime.page_records("node_execution", _by_run(run_id), page_size=200)
    return list(reversed(page.records.node_executions))


def _attempts(semantic_runtime, run_id):
    page = semantic_runtime.page_records("effect_attempt", _by_run(run_id), page_size=200)
    return list(reversed(page.records.effect_attempts))


def _approvals(semantic_runtime, run_id):
    page = semantic_runtime.page_records("approval", _by_run(run_id), page_size=200)
    return list(reversed(page.records.approvals))


def _runs_of(semantic_runtime, flow_version_id):
    page = semantic_runtime.page_records(
        "run",
        {"filter_kind": "equals", "field": "flow_version_id", "value": flow_version_id},
        page_size=200,
    )
    return list(reversed(page.records.runs))


def _waits(run):
    return [
        (w.node_id, w.map_index, _v(w.reason), w.approval_id) for w in run.waiting
    ]


def _produced(run):
    return {
        o.port: o.value.json_text
        for o in run.outputs
        if _v(o.output_kind) == "produced"
    }


def _steps(trace, node_id):
    return [
        (e.attempt_number, _v(e.status)) for e in trace if e.node_id == node_id
    ]


def _actor(actor):
    return (_v(actor.kind), actor.agent_name)


def _spooled_key(shown_file):
    key = shown_file.spooled_file
    return {
        "run_id": key.run_id,
        "producer_node_id": key.producer_node_id,
        "map_index": key.map_index,
        "attempt_number": key.attempt_number,
        "producer_port": key.producer_port,
        "list_index": key.list_index,
    }


def _photo_file(trace):
    """The SpooledFileKey of the file `a_photo` produced, from the trace."""
    (record,) = [e for e in trace if e.node_id == "a_photo"]
    (port,) = record.outputs
    (item,) = port.items
    assert _v(item.shown_kind) == "file"
    return _spooled_key(item)


def test_resume_resends_unreachable(semantic_runtime):
    """[witness: verification:kernel_a14_resume_resends_unreachable]

    A14 Required test 1: with a service down, a run rests `pending`, its
    independent read branch finishes, and a resume after the service returns
    completes it without new inputs.
    """
    vault = _service(semantic_runtime, "vault", [("save_draft", "POST", "/drafts", "draft-write")])
    catalog = _service(semantic_runtime, "catalog", [("look_up", "GET", "/items", "read")])
    vault.on("POST", "/drafts", json={"receipt": "r-1"})
    vault.set_down(True)
    catalog.on("GET", "/items", json={"title": "Ledger 2026"})

    save = _binding(
        semantic_runtime,
        "vault",
        "save_draft",
        inputs=[_port("note", "input", TEXT, "open")],
        outputs=[_port("receipt", "output", TEXT, "open")],
    )
    look_up = _binding(
        semantic_runtime,
        "catalog",
        "look_up",
        inputs=[_port("item", "input", TEXT, "open")],
        outputs=[_port("title", "output", TEXT, "open")],
    )
    _active_flow(
        semantic_runtime,
        "a14_resume",
        inputs=[_port("word", "input", TEXT, "open")],
        outputs=[_port("receipt", "output", TEXT), _port("title", "output", TEXT)],
        nodes=[_op_node("lookup", look_up), _op_node("save", save)],
        edges=[
            _edge("", "word", "lookup", "item"),
            _edge("", "word", "save", "note"),
            _edge("lookup", "title", "", "title"),
            _edge("save", "receipt", "", "receipt"),
        ],
    )

    run = semantic_runtime.start_run("a14_resume", inputs=[_json("word", "ledger")])
    run_id = run.run_id
    # A13 rule 8: an element waits on `service_unreachable`, none on approval.
    assert _v(run.status) == "pending"
    # A14 rule 1: one waiting point per waiting element, with its reason.
    assert _waits(run) == [("save", None, "service_unreachable", None)]
    # The independent read branch finished; a resting run shows only what it
    # produced so far (A13 rule 7).
    assert _produced(run) == {"title": '"Ledger 2026"'}
    assert [_v(o.output_kind) for o in run.outputs] == ["produced"]
    assert len(catalog.requests) == 1
    assert vault.requests == []

    # Control: the service returning advances nothing by itself; the run
    # rests until a request moves it (A13 rule 1).
    vault.set_down(False)
    resting = semantic_runtime.read_run(run_id)
    assert _v(resting.status) == "pending"
    assert _waits(resting) == [("save", None, "service_unreachable", None)]
    assert vault.requests == []

    # A14 rule 2: resume, by the owner or an agent, takes only the run.
    resumed = semantic_runtime.resume_run(run_id, actor=HELPER)
    assert _v(resumed.status) == "succeeded"
    assert resumed.waiting == ()
    assert _produced(resumed) == {"receipt": '"r-1"', "title": '"Ledger 2026"'}

    # The resend carries the run's own input; the read is not sent again.
    assert len(vault.requests) == 1
    assert vault.requests[0].method == "POST"
    assert json.loads(vault.requests[0].body) == {"note": "ledger"}
    assert len(catalog.requests) == 1

    trace = _trace(semantic_runtime, run_id)
    assert _steps(trace, "lookup") == [(1, "succeeded")]
    assert _steps(trace, "save") == [(1, "service_unreachable"), (2, "succeeded")]
    attempts = _attempts(semantic_runtime, run_id)
    assert [(a.node_id, a.attempt_number, _v(a.status)) for a in attempts] == [
        ("save", 1, "not_sent"),
        ("save", 2, "applied"),
    ]
    # A14 rule 2: a `draft-write` resend goes under the flow activation the
    # run started under, as the first send did.
    assert [_v(a.authority.authority_kind) for a in attempts] == [
        "flow_activation",
        "flow_activation",
    ]
    assert attempts[0].authority.store_position == attempts[1].authority.store_position


def test_resume_without_unreachable_refused(semantic_runtime):
    """[witness: verification:kernel_a14_resume_without_unreachable_refused]

    A14 Required test 2: a resume of a run waiting only for approval is
    refused.
    """
    ledger = _service(semantic_runtime, "ledger", [("post_entry", "POST", "/entries", "state-transition")])
    outbox = _service(semantic_runtime, "outbox", [("put_draft", "POST", "/drafts", "draft-write")])
    ledger.on("POST", "/entries", json={})
    outbox.on("POST", "/drafts", json={})
    outbox.set_down(True)

    post = _note_binding(semantic_runtime, "ledger", "post_entry")
    put = _note_binding(semantic_runtime, "outbox", "put_draft")
    word = [_port("word", "input", TEXT, "open")]
    _active_flow(
        semantic_runtime,
        "a14_approval_only",
        inputs=word,
        outputs=[],
        nodes=[_op_node("post", post)],
        edges=[_edge("", "word", "post", "note")],
    )
    _active_flow(
        semantic_runtime,
        "a14_unreachable_only",
        inputs=word,
        outputs=[],
        nodes=[_op_node("put", put)],
        edges=[_edge("", "word", "put", "note")],
    )

    run = semantic_runtime.start_run("a14_approval_only", inputs=[_json("word", "entry")])
    run_id = run.run_id
    assert _v(run.status) == "awaiting_approval"
    ((node_id, map_index, reason, approval_id),) = _waits(run)
    assert (node_id, map_index, reason) == ("post", None, "owner_approval")
    assert approval_id is not None

    trace_before = _trace(semantic_runtime, run_id)
    approvals_before = _approvals(semantic_runtime, run_id)

    # A14 rule 2: a run with no element waiting on `service_unreachable` is
    # refused.
    with pytest.raises(Exception) as exc:
        semantic_runtime.resume_run(run_id)
    assert exc.value.code == "refused"

    # The refusal recorded nothing and left the approval wait untouched
    # (A14 rule 2: elements waiting on approval are not touched).
    after = semantic_runtime.read_run(run_id)
    assert after == run
    assert _trace(semantic_runtime, run_id) == trace_before
    assert _approvals(semantic_runtime, run_id) == approvals_before
    assert [_v(a.status) for a in approvals_before] == ["requested"]
    assert _attempts(semantic_runtime, run_id) == []
    assert ledger.requests == []

    # Control: a run that does wait on `service_unreachable` is resumed — the
    # refusal above comes from the missing unreachable element, not from
    # resume itself. The service is still down, so the resend is again
    # `service_unreachable`, as the run's next attempt.
    other = semantic_runtime.start_run("a14_unreachable_only", inputs=[_json("word", "draft")])
    assert _v(other.status) == "pending"
    resumed = semantic_runtime.resume_run(other.run_id)
    assert _v(resumed.status) == "pending"
    assert _waits(resumed) == [("put", None, "service_unreachable", None)]
    assert _steps(_trace(semantic_runtime, other.run_id), "put") == [
        (1, "service_unreachable"),
        (2, "service_unreachable"),
    ]


def test_restart_in_flight_becomes_unknown(semantic_runtime):
    """[witness: verification:kernel_a14_restart_in_flight_becomes_unknown]

    A14 Required test 3: restarting the kernel during a function execution
    executes it again with the same output digest; during an effect it yields
    `unknown` and no second request.
    """
    vault = _service(semantic_runtime, "vault", [("save_record", "POST", "/records", "draft-write")])
    vault.on("POST", "/records", action="kill_kernel")

    upper = _upper_function(semantic_runtime)
    save = _note_binding(semantic_runtime, "vault", "save_record")
    function_version = _active_flow(
        semantic_runtime,
        "a14_restart_function",
        inputs=[_port("word", "input", TEXT, "open")],
        outputs=[_port("shout", "output", TEXT)],
        nodes=[_fn_node("f", upper)],
        edges=[_edge("", "word", "f", "x"), _edge("f", "y", "", "shout")],
    )
    effect_version = _active_flow(
        semantic_runtime,
        "a14_restart_effect",
        inputs=[_port("word", "input", TEXT, "open")],
        outputs=[],
        nodes=[_op_node("save", save)],
        edges=[_edge("", "word", "save", "note")],
    )

    # During a function execution: the kernel dies when the next sandbox
    # execution after this call (the run's `f`) starts.
    semantic_runtime.kill_on_sandbox_start(nth=1)
    with pytest.raises(semantic_runtime.KernelStopped):
        semantic_runtime.start_run("a14_restart_function", inputs=[_json("word", "ledger")])
    assert semantic_runtime.restart().started is True

    # A14 rule 5: the run left `running` is advanced on start; a function
    # element without a concluded record is executed again (it is pure).
    (recovered,) = _runs_of(semantic_runtime, function_version)
    assert _v(recovered.status) == "succeeded"
    trace = _trace(semantic_runtime, recovered.run_id)
    # The interrupted execution concluded nothing, so it left no record.
    assert _steps(trace, "f") == [(1, "succeeded")]

    # Control: the same input in an uninterrupted run gives the same output
    # value, so the same digest (value_id is computed from it, A01 rule 1).
    control = semantic_runtime.start_run("a14_restart_function", inputs=[_json("word", "ledger")])
    assert _v(control.status) == "succeeded"
    assert _produced(recovered) == _produced(control) == {"shout": '"LEDGER"'}
    (recovered_output,) = recovered.outputs
    (control_output,) = control.outputs
    assert recovered_output.value.value_id == control_output.value.value_id

    # During an effect: the kernel dies after the request reached the service
    # and before it answered. From now on the service answers, so a second
    # send would succeed and be seen here.
    with pytest.raises(semantic_runtime.KernelStopped):
        semantic_runtime.start_run("a14_restart_effect", inputs=[_json("word", "ledger")])
    assert len(vault.requests) == 1
    vault.on("POST", "/records", json={})
    assert semantic_runtime.restart().started is True

    # A14 rule 5, A11 rule 4: the `in_flight` attempt is `unknown`, its
    # NodeExecution `outcome_unknown`; the service is not asked again.
    (effect_run,) = _runs_of(semantic_runtime, effect_version)
    attempts = _attempts(semantic_runtime, effect_run.run_id)
    assert [(a.node_id, a.attempt_number, _v(a.status)) for a in attempts] == [
        ("save", 1, "unknown")
    ]
    assert _steps(_trace(semantic_runtime, effect_run.run_id), "save") == [
        (1, "outcome_unknown")
    ]
    assert _v(effect_run.status) == "pending"
    assert _waits(effect_run) == [("save", None, "outcome_unknown", None)]
    assert len(vault.requests) == 1


def test_cancel_empties_spool_keeps_trace(semantic_runtime):
    """[witness: verification:kernel_a14_cancel_empties_spool_keeps_trace]

    A14 Required test 4: a cancelled run executes nothing further, keeps its
    trace and has no spool.
    """
    ledger = _service(semantic_runtime, "ledger", [("post_entry", "POST", "/entries", "state-transition")])
    ledger.on("POST", "/entries", json={})

    photo, check = _photo_functions(semantic_runtime)
    post = _note_binding(semantic_runtime, "ledger", "post_entry")
    _photo_wait_flow(semantic_runtime, "a14_cancel", photo, check, post)

    run = semantic_runtime.start_run("a14_cancel", inputs=[_json("word", "photo-1")])
    run_id = run.run_id
    assert _v(run.status) == "awaiting_approval"
    ((_, _, _, approval_id),) = _waits(run)
    trace_before = _trace(semantic_runtime, run_id)
    photo_file = _photo_file(trace_before)
    # The run holds a spooled file before it is cancelled.
    assert len(semantic_runtime.run_spool(run_id)) == 1
    assert semantic_runtime.read_spooled_file(photo_file).content == b"photo-1"

    cancelled = semantic_runtime.cancel_run(run_id)
    # A14 rule 3: the run ends `cancelled` by the owner.
    assert _v(cancelled.status) == "cancelled"
    assert _actor(cancelled.cancelled_by) == ("owner", None)
    assert cancelled.ended_at is not None
    # A14 rule 1: when a run ends its waiting points are removed.
    assert cancelled.waiting == ()

    # A14 rule 3: the spool is emptied; no file of the run is served.
    assert semantic_runtime.run_spool(run_id) == []
    with pytest.raises(Exception) as exc:
        semantic_runtime.read_spooled_file(photo_file)
    assert exc.value.code == "refused"

    # A14 rule 3: nothing further is sent; the undecided approval can no
    # longer be decided, and resume finds nothing to resend.
    with pytest.raises(Exception) as exc:
        semantic_runtime.continue_after_approval(approval_id, "approve")
    assert exc.value.code == "refused"
    with pytest.raises(Exception) as exc:
        semantic_runtime.resume_run(run_id)
    assert exc.value.code == "refused"
    assert ledger.requests == []
    assert [_v(a.status) for a in _approvals(semantic_runtime, run_id)] == ["requested"]

    # Every concluded record stays, and none is added.
    assert _trace(semantic_runtime, run_id) == trace_before
    assert _v(semantic_runtime.read_run(run_id).status) == "cancelled"


def test_failed_spool_kept_until_release(semantic_runtime):
    """[witness: verification:kernel_a14_failed_spool_kept_until_release]

    A14 Required test 5: a `failed` run keeps its spooled files until
    released; releasing twice is refused.
    """
    photo, check = _photo_functions(semantic_runtime)
    _photo_check_flow(semantic_runtime, "a14_failed_spool", photo, check)

    run = semantic_runtime.start_run("a14_failed_spool", inputs=[_json("word", "crash-photo")])
    run_id = run.run_id
    assert _v(run.status) == "failed"
    trace = _trace(semantic_runtime, run_id)
    assert _steps(trace, "b_check") == [(1, "crashed")]
    photo_file = _photo_file(trace)

    # A14 rule 4: a `failed` run keeps its spool — across a restart too, whose
    # start removes only spools of runs that keep none (A18 rule 4).
    assert len(semantic_runtime.run_spool(run_id)) == 1
    assert semantic_runtime.read_spooled_file(photo_file).content == b"crash-photo"
    assert semantic_runtime.restart().started is True
    assert len(semantic_runtime.run_spool(run_id)) == 1
    assert semantic_runtime.read_spooled_file(photo_file).content == b"crash-photo"
    assert semantic_runtime.read_run(run_id).released_by is None

    # A14 rule 4: release, by the owner or an agent, removes the files and
    # records who and when.
    released = semantic_runtime.release_run(run_id, actor=HELPER)
    assert _v(released.status) == "failed"
    assert _actor(released.released_by) == ("agent", "helper")
    assert released.released_at is not None
    assert semantic_runtime.run_spool(run_id) == []
    with pytest.raises(Exception) as exc:
        semantic_runtime.read_spooled_file(photo_file)
    assert exc.value.code == "refused"

    # A14 rule 4: a run already released is refused, and keeps its release.
    with pytest.raises(Exception) as exc:
        semantic_runtime.release_run(run_id)
    assert exc.value.code == "refused"
    again = semantic_runtime.read_run(run_id)
    assert _actor(again.released_by) == ("agent", "helper")
    assert again.released_at == released.released_at


def test_elapsed_wait_changes_nothing(semantic_runtime):
    """[witness: verification:kernel_a14_elapsed_wait_changes_nothing]

    A14 Required test 6: runs resting on `owner_approval`, on
    `service_unreachable` and on `outcome_unknown` are unchanged — status,
    waiting points and records — after the clock is moved past any interval:
    nothing is retried, failed or approved.
    """
    ledger = _service(semantic_runtime, "ledger", [("post_entry", "POST", "/entries", "state-transition")])
    outbox = _service(semantic_runtime, "outbox", [("put_draft", "POST", "/drafts", "draft-write")])
    vault = _service(semantic_runtime, "vault", [("save_record", "POST", "/records", "draft-write")])
    ledger.on("POST", "/entries", json={})
    outbox.on("POST", "/drafts", json={})
    outbox.set_down(True)
    vault.on("POST", "/records", action="drop_after_request")

    word = [_port("word", "input", TEXT, "open")]
    for flow_id, service_id, operation_name in (
        ("a14_wait_approval", "ledger", "post_entry"),
        ("a14_wait_unreachable", "outbox", "put_draft"),
        ("a14_wait_unknown", "vault", "save_record"),
    ):
        binding = _note_binding(semantic_runtime, service_id, operation_name)
        _active_flow(
            semantic_runtime,
            flow_id,
            inputs=word,
            outputs=[],
            nodes=[_op_node("send", binding)],
            edges=[_edge("", "word", "send", "note")],
        )

    approval_run = semantic_runtime.start_run("a14_wait_approval", inputs=[_json("word", "a")])
    unreachable_run = semantic_runtime.start_run("a14_wait_unreachable", inputs=[_json("word", "b")])
    unknown_run = semantic_runtime.start_run("a14_wait_unknown", inputs=[_json("word", "c")])
    assert _v(approval_run.status) == "awaiting_approval"
    assert [w[2] for w in _waits(approval_run)] == ["owner_approval"]
    assert _v(unreachable_run.status) == "pending"
    assert _waits(unreachable_run) == [("send", None, "service_unreachable", None)]
    assert _v(unknown_run.status) == "pending"
    assert _waits(unknown_run) == [("send", None, "outcome_unknown", None)]

    def snapshot():
        return {
            run.run_id: (
                semantic_runtime.read_run(run.run_id),
                _trace(semantic_runtime, run.run_id),
                _attempts(semantic_runtime, run.run_id),
                _approvals(semantic_runtime, run.run_id),
            )
            for run in (approval_run, unreachable_run, unknown_run)
        }

    before = snapshot()
    requests_before = (len(ledger.requests), len(outbox.requests), len(vault.requests))
    assert requests_before == (0, 0, 1)

    # Every service would now answer: a retry, if any, would succeed and be
    # seen by its stub.
    outbox.set_down(False)
    vault.on("POST", "/records", json={})
    # A14 rule 1: no time limit ends, fails, approves or retries anything.
    semantic_runtime.clock.advance(ms=TRANSPORT_TIMEOUT_MS, days=400)

    after = snapshot()
    assert after == before
    assert (len(ledger.requests), len(outbox.requests), len(vault.requests)) == requests_before
    approval_records = after[approval_run.run_id][3]
    assert [_v(a.status) for a in approval_records] == ["requested"]
    unknown_attempts = after[unknown_run.run_id][2]
    assert [_v(a.status) for a in unknown_attempts] == ["unknown"]


def test_resume_leaves_other_waits_untouched(semantic_runtime):
    """[witness: verification:kernel_a14_resume_leaves_other_waits_untouched]

    A14 Required test 7: a resume of a run with one element waiting on
    `service_unreachable`, one on approval and one on `outcome_unknown` sends
    only the first again; the other two waiting points stay as they were.
    """
    outbox = _service(semantic_runtime, "outbox", [("put_draft", "POST", "/drafts", "draft-write")])
    ledger = _service(semantic_runtime, "ledger", [("post_entry", "POST", "/entries", "state-transition")])
    vault = _service(semantic_runtime, "vault", [("save_record", "POST", "/records", "draft-write")])
    outbox.on("POST", "/drafts", json={})
    outbox.set_down(True)
    ledger.on("POST", "/entries", json={})
    vault.on("POST", "/records", action="drop_after_request")

    put = _note_binding(semantic_runtime, "outbox", "put_draft")
    post = _note_binding(semantic_runtime, "ledger", "post_entry")
    save = _note_binding(semantic_runtime, "vault", "save_record")
    _active_flow(
        semantic_runtime,
        "a14_three_waits",
        inputs=[_port("word", "input", TEXT, "open")],
        outputs=[],
        nodes=[
            _op_node("a_outbox", put),
            _op_node("b_ledger", post),
            _op_node("c_vault", save),
        ],
        edges=[
            _edge("", "word", "a_outbox", "note"),
            _edge("", "word", "b_ledger", "note"),
            _edge("", "word", "c_vault", "note"),
        ],
    )

    run = semantic_runtime.start_run("a14_three_waits", inputs=[_json("word", "entry")])
    run_id = run.run_id
    # A13 rule 8: an element waits for the owner's approval.
    assert _v(run.status) == "awaiting_approval"
    waits = _waits(run)
    assert [(n, m, r) for n, m, r, _ in waits] == [
        ("a_outbox", None, "service_unreachable"),
        ("b_ledger", None, "owner_approval"),
        ("c_vault", None, "outcome_unknown"),
    ]
    approval_id = waits[1][3]
    assert approval_id is not None
    approvals_before = _approvals(semantic_runtime, run_id)
    vault_attempts_before = [
        a for a in _attempts(semantic_runtime, run_id) if a.node_id == "c_vault"
    ]
    assert [_v(a.status) for a in vault_attempts_before] == ["unknown"]
    assert (len(outbox.requests), len(ledger.requests), len(vault.requests)) == (0, 0, 1)

    # Every service would now answer.
    outbox.set_down(False)
    vault.on("POST", "/records", json={})

    resumed = semantic_runtime.resume_run(run_id)
    # A14 rule 2: only the `service_unreachable` element is sent again.
    assert (len(outbox.requests), len(ledger.requests), len(vault.requests)) == (1, 0, 1)
    # The other two waiting points stay as they were.
    assert _v(resumed.status) == "awaiting_approval"
    assert _waits(resumed) == [
        ("b_ledger", None, "owner_approval", approval_id),
        ("c_vault", None, "outcome_unknown", None),
    ]
    assert _approvals(semantic_runtime, run_id) == approvals_before
    assert [
        a for a in _attempts(semantic_runtime, run_id) if a.node_id == "c_vault"
    ] == vault_attempts_before

    trace = _trace(semantic_runtime, run_id)
    assert _steps(trace, "a_outbox") == [(1, "service_unreachable"), (2, "succeeded")]
    assert _steps(trace, "b_ledger") == []
    assert _steps(trace, "c_vault") == [(1, "outcome_unknown")]


def test_cancel_owner_only_unended_only(semantic_runtime):
    """[witness: verification:kernel_a14_cancel_owner_only_unended_only]

    A14 Required test 8: a cancel by an agent, or of a run that has ended,
    does not cancel the run: it keeps its status, its trace and its spool.
    """
    ledger = _service(semantic_runtime, "ledger", [("post_entry", "POST", "/entries", "state-transition")])
    ledger.on("POST", "/entries", json={})

    photo, check = _photo_functions(semantic_runtime)
    post = _note_binding(semantic_runtime, "ledger", "post_entry")
    _photo_wait_flow(semantic_runtime, "a14_cancel_waiting", photo, check, post)
    _photo_check_flow(semantic_runtime, "a14_cancel_failed", photo, check)

    # A cancel by an agent, of a run that has not ended.
    waiting = semantic_runtime.start_run("a14_cancel_waiting", inputs=[_json("word", "photo-1")])
    assert _v(waiting.status) == "awaiting_approval"
    trace_before = _trace(semantic_runtime, waiting.run_id)
    photo_file = _photo_file(trace_before)
    spool_before = semantic_runtime.run_spool(waiting.run_id)
    assert len(spool_before) == 1

    with pytest.raises(Exception) as exc:
        semantic_runtime.cancel_run(waiting.run_id, actor=AUTHOR)
    # A16 rule 3: cancel is the owner's only.
    assert exc.value.code == "not_permitted"
    assert semantic_runtime.read_run(waiting.run_id) == waiting
    assert _trace(semantic_runtime, waiting.run_id) == trace_before
    assert semantic_runtime.run_spool(waiting.run_id) == spool_before
    assert semantic_runtime.read_spooled_file(photo_file).content == b"photo-1"

    # A cancel of a run that has ended (`failed`, which keeps its spool).
    failed = semantic_runtime.start_run("a14_cancel_failed", inputs=[_json("word", "crash-photo")])
    assert _v(failed.status) == "failed"
    failed_trace = _trace(semantic_runtime, failed.run_id)
    failed_file = _photo_file(failed_trace)
    failed_spool = semantic_runtime.run_spool(failed.run_id)
    assert len(failed_spool) == 1

    with pytest.raises(Exception) as exc:
        semantic_runtime.cancel_run(failed.run_id)
    # A14 rule 3: only a run that has not ended is cancelled.
    assert exc.value.code == "refused"
    assert semantic_runtime.read_run(failed.run_id) == failed
    assert _trace(semantic_runtime, failed.run_id) == failed_trace
    assert semantic_runtime.run_spool(failed.run_id) == failed_spool
    assert semantic_runtime.read_spooled_file(failed_file).content == b"crash-photo"

    # A cancel of a run that ended `succeeded` is refused too: "ended" is
    # every ended status, not only `failed` (A13 rule 7, A14 rule 3).
    succeeded = semantic_runtime.start_run("a14_cancel_failed", inputs=[_json("word", "photo-ok")])
    assert _v(succeeded.status) == "succeeded"
    succeeded_trace = _trace(semantic_runtime, succeeded.run_id)
    with pytest.raises(Exception) as exc:
        semantic_runtime.cancel_run(succeeded.run_id)
    assert exc.value.code == "refused"
    assert semantic_runtime.read_run(succeeded.run_id) == succeeded
    assert _trace(semantic_runtime, succeeded.run_id) == succeeded_trace

    # Control: the owner's cancel of the unended run succeeds, so the refusals
    # above come from the actor and from the ended run.
    cancelled = semantic_runtime.cancel_run(waiting.run_id)
    assert _v(cancelled.status) == "cancelled"
    assert _actor(cancelled.cancelled_by) == ("owner", None)
    assert semantic_runtime.run_spool(waiting.run_id) == []


def test_spool_emptied_on_succeeded_refused(semantic_runtime):
    """[witness: verification:kernel_a14_spool_emptied_on_succeeded_refused]

    A14 Required test 9: a run that spooled a file and ends `succeeded`, and
    one that spooled a file and ends `refused`, keep no spooled file.
    """
    ledger = _service(semantic_runtime, "ledger", [("post_entry", "POST", "/entries", "state-transition")])
    ledger.on("POST", "/entries", json={})

    photo, check = _photo_functions(semantic_runtime)
    post = _note_binding(semantic_runtime, "ledger", "post_entry")
    _photo_check_flow(semantic_runtime, "a14_spool_check", photo, check)
    _photo_wait_flow(semantic_runtime, "a14_spool_wait", photo, check, post)

    # Ends `succeeded`: its trace names the file it spooled.
    succeeded = semantic_runtime.start_run("a14_spool_check", inputs=[_json("word", "photo-ok")])
    assert _v(succeeded.status) == "succeeded"
    assert _produced(succeeded) == {"size": "8"}
    succeeded_file = _photo_file(_trace(semantic_runtime, succeeded.run_id))
    # A14 rule 4: emptied when the run ends `succeeded`; no file is served.
    assert semantic_runtime.run_spool(succeeded.run_id) == []
    with pytest.raises(Exception) as exc:
        semantic_runtime.read_spooled_file(succeeded_file)
    assert exc.value.code == "refused"

    # Ends `refused`: the spool holds the file until the owner refuses.
    waiting = semantic_runtime.start_run("a14_spool_wait", inputs=[_json("word", "photo-2")])
    assert _v(waiting.status) == "awaiting_approval"
    ((_, _, _, approval_id),) = _waits(waiting)
    refused_file = _photo_file(_trace(semantic_runtime, waiting.run_id))
    assert len(semantic_runtime.run_spool(waiting.run_id)) == 1
    refused = semantic_runtime.continue_after_approval(approval_id, "refuse")
    assert _v(refused.status) == "refused"
    # A14 rule 4: emptied when the run ends `refused`.
    assert semantic_runtime.run_spool(waiting.run_id) == []
    with pytest.raises(Exception) as exc:
        semantic_runtime.read_spooled_file(refused_file)
    assert exc.value.code == "refused"
    assert ledger.requests == []

    # Control: a run of the same flow that ends `failed` keeps its spooled
    # file, so the empty spools above come from how those runs ended.
    failed = semantic_runtime.start_run("a14_spool_check", inputs=[_json("word", "crash-photo")])
    assert _v(failed.status) == "failed"
    assert len(semantic_runtime.run_spool(failed.run_id)) == 1


def test_recovery_completes_before_surface(semantic_runtime):
    """[witness: verification:kernel_a14_recovery_completes_before_surface]

    A14 Required test 10: after a restart, the first request the surface
    answers finds no EffectAttempt `in_flight` and every run that derivation
    left `running` already advanced by the kernel.
    """
    vault = _service(semantic_runtime, "vault", [("save_record", "POST", "/records", "draft-write")])
    vault.on("POST", "/records", action="kill_kernel")

    upper = _upper_function(semantic_runtime)
    save = _note_binding(semantic_runtime, "vault", "save_record")
    flow_version_id = _active_flow(
        semantic_runtime,
        "a14_recovery",
        inputs=[_port("word", "input", TEXT, "open")],
        outputs=[_port("shout", "output", TEXT)],
        nodes=[_op_node("a_save", save), _fn_node("b_upper", upper)],
        edges=[
            _edge("", "word", "a_save", "note"),
            _edge("", "word", "b_upper", "x"),
            _edge("b_upper", "y", "", "shout"),
        ],
    )

    # A13 rule 2: `a_save` executes first; the kernel dies while its request
    # is out, leaving its attempt `in_flight` and `b_upper` not yet executed.
    with pytest.raises(semantic_runtime.KernelStopped):
        semantic_runtime.start_run("a14_recovery", inputs=[_json("word", "ledger")])
    assert len(vault.requests) == 1
    vault.on("POST", "/records", json={})

    assert semantic_runtime.restart().started is True

    # The first request the surface answers: no attempt is `in_flight`.
    page = semantic_runtime.page_records("effect_attempt", None, page_size=200)
    attempts = page.records.effect_attempts
    assert [(a.node_id, a.attempt_number, _v(a.status)) for a in attempts] == [
        ("a_save", 1, "unknown")
    ]

    # A read advances nothing (A13 rule 1), so what it shows was done before
    # the surface opened: the run was derived and advanced by the kernel.
    (run,) = _runs_of(semantic_runtime, flow_version_id)
    assert _v(run.status) == "pending"
    assert _waits(run) == [("a_save", None, "outcome_unknown", None)]
    assert _produced(run) == {"shout": '"LEDGER"'}
    trace = _trace(semantic_runtime, run.run_id)
    assert _steps(trace, "a_save") == [(1, "outcome_unknown")]
    assert _steps(trace, "b_upper") == [(1, "succeeded")]
    # The kernel did not ask the service again (A11 rule 4).
    assert len(vault.requests) == 1
