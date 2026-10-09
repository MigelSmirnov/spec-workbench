"""Witness tests for accepted decision A15 (02_rules_runs.md).

Every concluded attempt at an element, every skipped node and every
`upstream_failed` node writes exactly one NodeExecution, which no operation
edits; a record holds no payload and no text beyond `failure_detail_bytes_max`;
a run's files live in its spool under the spool ceilings, and outlive the run
only when captured as trial fixtures. Each test carries the witness name its
Required test declares.

The Factory project supplies the ``semantic_runtime`` pytest fixture. It binds
these scenarios to the generated public operations of State 5 — named here by
their operation names, with arguments shaped as the State 6 models — without
changing the assertions below. Each test gets a fresh, empty kernel store.

Fixture surface used here:

- ``issue_contract_version(slot_id, purpose, inputs, outputs,
  resource_bounds=None)`` -> contract_version_id;
  ``add_trial_case(contract_version_id, inputs)`` -> ShownAddedTrialCase;
  ``submit_implementation(contract_version_id, code)`` -> ShownSubmission,
  which activates an admitted implementation (A04 rule 4); all three act as
  agent ``author``;
- ``propose_binding(service_id, operation_name, inputs, outputs)`` ->
  OperationBinding (agent ``author``); ``accept_binding(binding_id)`` ->
  OperationBinding (the owner);
- ``compose_flow_version(flow_id, purpose, inputs, outputs, nodes, edges,
  constants)`` -> ComposedFlowVersion (agent ``author``);
  ``activate_flow_version(flow_version_id)`` -> FlowActivation (the owner);
- ``start_run(flow_id, inputs)``, ``resume_run(run_id)``,
  ``release_run(run_id)``, ``cancel_run(run_id)``,
  ``continue_after_approval(approval_id, decision)``,
  ``continue_after_resolution(attempt, resolution)``, ``read_run(run_id)`` ->
  ShownRun; inputs are RequestJsonValue dicts, ``attempt`` an AttemptKey dict;
- ``capture_failed_execution(execution, contract_version_id)`` ->
  ShownTrialCase (the owner);
- ``page_records(record_type, record_filter, page_size)`` -> RecordPageAnswer;
  node executions and effect attempts are read from its ``records`` (newest
  first);
- ``read_spooled_file(file)`` -> SpooledFileContent, ``file`` a SpooledFileKey
  dict; ``read_fixture_file(value_id)`` -> FixtureFileContent (owner only);
- every call takes ``actor=`` (an Actor M27 dict); omitted, it is the owner
  for owner operations and agent ``author`` for authoring operations.

Capabilities used here: ``stub_service()`` (a loopback HTTP service whose
received requests are listed in ``stub.requests``; ``set_down``, ``action``
``"drop_after_request"``), ``manifest.write_record``,
``installation.select_instance``, ``installation.set_credential``,
``run_spool(run_id)``, ``store_dump()`` and ``restart()``.
"""

import base64
import json

import pytest

OWNER = {"kind": "owner", "agent_name": None}
AUTHOR = {"kind": "agent", "agent_name": "author"}

TEXT = '{"type":"string"}'
NUMBER = '{"type":"integer"}'
ROUTE = '{"type":"string","enum":["duplicate","new"]}'
FILE_SCHEMA = "{}"
PHOTO = "image/png"

INSTANCE = "rig"
CREDENTIAL_HEADER = "X-Api-Key"

# A20 rule 1, release v1
WALL_TIME_MS = 30000
MEMORY_BYTES = 536870912
OUTPUT_BYTES = 67108864
PROCESS_COUNT = 8
SPOOL_FILE_BYTES_MAX = 134217728
SPOOL_RUN_BYTES_MAX = 536870912
FAILURE_DETAIL_BYTES_MAX = 4096

# Every bound at its ceiling, so that no bound below a ceiling decides first.
CEILING_BOUNDS = {
    "wall_time_ms": WALL_TIME_MS,
    "memory_bytes": MEMORY_BYTES,
    "output_bytes": OUTPUT_BYTES,
    "process_count": PROCESS_COUNT,
}

ECHO_CODE = """
def run(inputs):
    if inputs["x"] == "fail":
        raise ValueError("refused word")
    return {"y": inputs["x"]}
"""

ROUTE_CODE = """
def run(inputs):
    return {"route": "duplicate", "text": inputs["x"]}
"""

DOUBLE_CODE = """
def run(inputs):
    return {"y": inputs["x"] * 2}
"""

PHOTO_CODE = """
def run(inputs):
    return {"photo": inputs["x"].encode("utf-8")}
"""

# A file of exactly `n` bytes (n >= 5), starting with b"crash".
SIZED_FILE_CODE = """
def run(inputs):
    return {"photo": b"crash" + bytes(inputs["n"] - 5)}
"""

# A file of exactly `n` bytes, generated inside the sandbox, and `ok` = 0.
FILLER_CODE = """
def run(inputs):
    return {"photo": b"x" * inputs["n"], "ok": 0}
"""

# Two files, 5 and 6 bytes, and `ok` = 0.
TWO_FILES_CODE = """
def run(inputs):
    return {"first": b"x" * 5, "second": b"y" * 6, "ok": 0}
"""

CHECK_CODE = """
def run(inputs):
    photo = inputs["photo"]
    if photo.startswith(b"crash"):
        raise ValueError("unreadable photo")
    return {"size": len(photo)}
"""

# The secret-shaped string is assembled at run time, so the stored code does
# not hold it; it is printed, and the exception raised after it is longer than
# `failure_detail_bytes_max` — or, on "brief", short enough that a cut to
# `failure_detail_bytes_max` would keep whatever followed it.
SECRET = "sk-live-" + "7f3a9c2e5b1d4086"
LEAK_CODE = """
def run(inputs):
    secret = "sk-live-" + "".join(reversed("6804d1b5e2c9a3f7"))
    print(secret)
    if inputs["x"] == "boom":
        raise RuntimeError("detail-marker " + "x" * 10000)
    if inputs["x"] == "brief":
        raise RuntimeError("detail-marker")
    return {"y": inputs["x"]}
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
        service_id, CREDENTIAL_HEADER, f"{service_id}-a15-credential-value"
    )
    return stub


def _note_binding(semantic_runtime, service_id, operation_name):
    """An accepted binding with one `value` input `note` and no output ports."""
    proposed = semantic_runtime.propose_binding(
        service_id,
        operation_name,
        inputs=[_port("note", "input", TEXT, "open")],
        outputs=[],
    )
    return semantic_runtime.accept_binding(proposed.binding_id).binding_id


def _function(
    semantic_runtime, slot_id, inputs, outputs, code, trial_inputs, resource_bounds=None
):
    """A contract version with one passing trial case and an admitted, active
    implementation."""
    if resource_bounds is None:
        contract_version_id = semantic_runtime.issue_contract_version(
            slot_id, purpose=f"A15 witness: {slot_id}", inputs=inputs, outputs=outputs
        )
    else:
        contract_version_id = semantic_runtime.issue_contract_version(
            slot_id,
            purpose=f"A15 witness: {slot_id}",
            inputs=inputs,
            outputs=outputs,
            resource_bounds=resource_bounds,
        )
    semantic_runtime.add_trial_case(contract_version_id, inputs=trial_inputs)
    submission = semantic_runtime.submit_implementation(contract_version_id, code)
    assert _v(submission.verdict.verdict) == "admitted"
    assert submission.activation is not None
    return contract_version_id


def _echo_function(semantic_runtime):
    """`echo` returns its text, and crashes on the word "fail"."""
    return _function(
        semantic_runtime,
        "echo",
        [_port("x", "input", TEXT, "open")],
        [_port("y", "output", TEXT)],
        ECHO_CODE,
        [_json("x", "ok")],
    )


def _check_function(semantic_runtime):
    """`check` crashes on a photo starting with b"crash", else returns its size."""
    return _function(
        semantic_runtime,
        "check",
        [_file_port("photo", "input", "open")],
        [_port("size", "output", NUMBER)],
        CHECK_CODE,
        [_file("photo", b"ok-photo")],
    )


def _sized_file_function(semantic_runtime, slot_id):
    """A function spooling a file of `n` bytes, every bound at its ceiling."""
    return _function(
        semantic_runtime,
        slot_id,
        [_port("n", "input", NUMBER, "open")],
        [_file_port("photo", "output")],
        SIZED_FILE_CODE,
        [_json("n", 8)],
        resource_bounds=CEILING_BOUNDS,
    )


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


def _edge(from_node, from_port, to_node, to_port, guard=None):
    return {
        "from_node": from_node,
        "from_port": from_port,
        "to_node": to_node,
        "to_port": to_port,
        "guard": guard,
    }


def _active_flow(semantic_runtime, flow_id, inputs, outputs, nodes, edges):
    composed = semantic_runtime.compose_flow_version(
        flow_id,
        purpose=f"A15 witness: {flow_id}",
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


def _by_run(run_id):
    return {"filter_kind": "equals", "field": "run_id", "value": run_id}


def _trace(semantic_runtime, run_id):
    """The run's NodeExecutions in store order."""
    page = semantic_runtime.page_records("node_execution", _by_run(run_id), page_size=200)
    return list(reversed(page.records.node_executions))


def _attempts(semantic_runtime, run_id):
    page = semantic_runtime.page_records("effect_attempt", _by_run(run_id), page_size=200)
    return list(reversed(page.records.effect_attempts))


def _key(record):
    return (record.node_id, record.map_index, record.attempt_number)


def _by_key(trace):
    keyed = {_key(record): record for record in trace}
    assert len(keyed) == len(trace)
    return keyed


def _waits(run):
    return [
        (w.node_id, w.map_index, _v(w.reason), w.approval_id) for w in run.waiting
    ]


def _steps(trace, node_id):
    return [
        (e.attempt_number, _v(e.status)) for e in trace if e.node_id == node_id
    ]


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


def _only_file(port_list):
    (port,) = port_list
    (item,) = port.items
    assert _v(item.shown_kind) == "file"
    return item


def test_node_execution_immutable(semantic_runtime):
    """[witness: verification:kernel_a15_node_execution_immutable]

    A15 Required test 1: no operation alters a written NodeExecution.
    """
    outbox = _service(semantic_runtime, "outbox", [("put_draft", "POST", "/drafts", "draft-write")])
    vault = _service(semantic_runtime, "vault", [("save_record", "POST", "/records", "draft-write")])
    ledger = _service(semantic_runtime, "ledger", [("post_entry", "POST", "/entries", "state-transition")])
    outbox.on("POST", "/drafts", json={})
    outbox.set_down(True)
    vault.on("POST", "/records", action="drop_after_request")
    ledger.on("POST", "/entries", json={})

    echo = _echo_function(semantic_runtime)
    photo = _function(
        semantic_runtime,
        "photo",
        [_port("x", "input", TEXT, "open")],
        [_file_port("photo", "output")],
        PHOTO_CODE,
        [_json("x", "ok-photo")],
    )
    put = _note_binding(semantic_runtime, "outbox", "put_draft")
    save = _note_binding(semantic_runtime, "vault", "save_record")
    post = _note_binding(semantic_runtime, "ledger", "post_entry")
    _active_flow(
        semantic_runtime,
        "a15_immutable",
        inputs=[_port("word", "input", TEXT, "open")],
        outputs=[_port("echoed", "output", TEXT)],
        nodes=[
            _fn_node("a_fail", echo),
            _op_node("b_save", put),
            _op_node("c_drop", save),
            _op_node("d_post", post),
            _fn_node("e_photo", photo),
        ],
        edges=[
            _edge("", "word", "a_fail", "x"),
            _edge("a_fail", "y", "", "echoed"),
            _edge("", "word", "b_save", "note"),
            _edge("", "word", "c_drop", "note"),
            _edge("", "word", "d_post", "note"),
            _edge("", "word", "e_photo", "x"),
        ],
    )

    # `a_fail` crashes, `b_save` is unreachable, `c_drop` ends unknown,
    # `d_post` waits for the owner's approval and `e_photo` spools a file.
    run = semantic_runtime.start_run("a15_immutable", inputs=[_json("word", "fail")])
    run_id = run.run_id
    assert _v(run.status) == "awaiting_approval"
    ((_, _, _, approval_id),) = [w for w in _waits(run) if w[0] == "d_post"]

    written = _by_key(_trace(semantic_runtime, run_id))
    assert set(written) == {
        ("a_fail", None, 1),
        ("b_save", None, 1),
        ("c_drop", None, 1),
        ("e_photo", None, 1),
    }
    # A record naming a spooled file, so that the release and the restart's
    # spool removal below meet a record whose file they remove (State 5,
    # `read_spooled_file`: the record outlives its bytes).
    spooled = _only_file(written[("e_photo", None, 1)].outputs)
    assert spooled.spooled_file is not None

    def assert_unaltered():
        """Every record written so far is still there, field for field; new
        records only add to the trace."""
        current = _by_key(_trace(semantic_runtime, run_id))
        for key, record in written.items():
            assert current[key] == record
        written.update(current)

    # A resume that resends `b_save`.
    outbox.set_down(False)
    semantic_runtime.resume_run(run_id)
    assert_unaltered()
    assert _steps(_trace(semantic_runtime, run_id), "b_save") == [
        (1, "service_unreachable"),
        (2, "succeeded"),
    ]

    # The owner's resolution of `c_drop`'s unknown outcome (A11 rule 3: its
    # one NodeExecution keeps `outcome_unknown`).
    semantic_runtime.continue_after_resolution(
        {"run_id": run_id, "node_id": "c_drop", "map_index": None, "attempt_number": 1},
        "applied",
    )
    assert_unaltered()
    assert _steps(_trace(semantic_runtime, run_id), "c_drop") == [(1, "outcome_unknown")]

    # The owner's approval of `d_post`; the run then ends `failed`.
    ended = semantic_runtime.continue_after_approval(approval_id, "approve")
    assert _v(ended.status) == "failed"
    assert_unaltered()

    # A refused cancel of the ended run.
    with pytest.raises(Exception) as exc:
        semantic_runtime.cancel_run(run_id)
    assert exc.value.code == "refused"
    assert_unaltered()

    # A capture of `a_fail`'s failed execution into its corpus.
    semantic_runtime.capture_failed_execution(
        {"run_id": run_id, "node_id": "a_fail", "map_index": None, "attempt_number": 1},
        echo,
    )
    assert_unaltered()

    # The release of the failed run's spool.
    semantic_runtime.release_run(run_id)
    assert_unaltered()

    # A restart, whose start-up derives and recovers runs (A14 rule 5).
    assert semantic_runtime.restart().started is True
    assert_unaltered()

    assert set(written) == {
        ("a_fail", None, 1),
        ("b_save", None, 1),
        ("b_save", None, 2),
        ("c_drop", None, 1),
        ("d_post", None, 1),
        ("e_photo", None, 1),
    }


def test_failure_detail_bounded_no_secret(semantic_runtime):
    """[witness: verification:kernel_a15_failure_detail_bounded_no_secret]

    A15 Required test 2: a function that raises after printing a
    secret-shaped string leaves a bounded `failure_detail` without it.
    """
    leak = _function(
        semantic_runtime,
        "leak",
        [_port("x", "input", TEXT, "open")],
        [_port("y", "output", TEXT)],
        LEAK_CODE,
        [_json("x", "ok")],
    )
    _active_flow(
        semantic_runtime,
        "a15_leak",
        inputs=[_port("word", "input", TEXT, "open")],
        outputs=[_port("echoed", "output", TEXT)],
        nodes=[_fn_node("leak", leak)],
        edges=[_edge("", "word", "leak", "x"), _edge("leak", "y", "", "echoed")],
    )

    run = semantic_runtime.start_run("a15_leak", inputs=[_json("word", "boom")])
    assert _v(run.status) == "failed"
    (record,) = _trace(semantic_runtime, run.run_id)
    assert _v(record.status) == "crashed"

    detail = record.failure_detail
    assert _v(detail.detail_kind) == "text"
    # A15 rule 2, A20 rule 2: no text beyond `failure_detail_bytes_max`.
    assert len(detail.text.encode("utf-8")) <= FAILURE_DETAIL_BYTES_MAX
    # A03 rule 6: the detail is the exception, never stdout.
    assert "detail-marker" in detail.text
    assert SECRET not in detail.text

    # Control: a short exception leaves room in the detail, so a detail that
    # appends the printed output after the exception is not hidden by the cut.
    brief = semantic_runtime.start_run("a15_leak", inputs=[_json("word", "brief")])
    assert _v(brief.status) == "failed"
    (brief_record,) = _trace(semantic_runtime, brief.run_id)
    assert _v(brief_record.status) == "crashed"
    brief_detail = brief_record.failure_detail
    assert _v(brief_detail.detail_kind) == "text"
    assert "detail-marker" in brief_detail.text
    assert SECRET not in brief_detail.text

    # The printed string is in no record the store holds.
    assert SECRET.encode("utf-8") not in semantic_runtime.store_dump()


def test_spool_file_ceiling(semantic_runtime):
    """[witness: verification:kernel_a15_spool_file_ceiling]

    A15 Required test 3: a function writing a file one byte over
    `spool_file_bytes_max` concludes `resource_exhausted` — under release v1
    already by `output_bytes`, which is lower — and leaves nothing in the spool.
    """
    sized = _sized_file_function(semantic_runtime, "sized_file")
    check = _check_function(semantic_runtime)
    _active_flow(
        semantic_runtime,
        "a15_spool_file",
        inputs=[_port("n", "input", NUMBER, "open")],
        outputs=[_port("size", "output", NUMBER)],
        nodes=[_fn_node("a_file", sized), _fn_node("b_check", check)],
        edges=[
            _edge("", "n", "a_file", "n"),
            _edge("a_file", "photo", "b_check", "photo"),
            _edge("b_check", "size", "", "size"),
        ],
    )

    # Note: under release v1 a function's whole output is bounded by
    # `output_bytes` (64 MiB), below `spool_file_bytes_max` (128 MiB); both
    # conclude `resource_exhausted` (A03 rule 5, A15 rule 3).
    run = semantic_runtime.start_run(
        "a15_spool_file", inputs=[_json("n", SPOOL_FILE_BYTES_MAX + 1)]
    )
    # The run ends `failed`, so it keeps its spool (A14 rule 4) — which holds
    # nothing: the attempt's file is discarded (A15 rule 3, A13 rule 3).
    assert _v(run.status) == "failed"
    trace = _trace(semantic_runtime, run.run_id)
    (record,) = [e for e in trace if e.node_id == "a_file"]
    assert _v(record.status) == "resource_exhausted"
    assert record.outputs == ()
    assert _steps(trace, "b_check") == [(1, "upstream_failed")]
    assert semantic_runtime.run_spool(run.run_id) == []

    # Control: the same function writing a small file spools it, and a run
    # ending `failed` keeps it, so the empty spool above is the ceiling's.
    control = semantic_runtime.start_run("a15_spool_file", inputs=[_json("n", 8)])
    assert _v(control.status) == "failed"
    control_trace = _trace(semantic_runtime, control.run_id)
    assert _steps(control_trace, "a_file") == [(1, "succeeded")]
    assert _steps(control_trace, "b_check") == [(1, "crashed")]
    assert len(semantic_runtime.run_spool(control.run_id)) == 1


def test_spool_run_ceiling(semantic_runtime):
    """[witness: verification:kernel_a15_spool_run_ceiling]

    A15 Required test 4: a function whose second spooled file brings its run's
    spool one byte over `spool_run_bytes_max` concludes `resource_exhausted`;
    only that attempt's files are discarded and the file spooled earlier stays.
    """
    # The run's spool is filled by eight earlier nodes. Each filler's output
    # count is its file plus the canonical JSON of `ok` (0, one byte), so a
    # filler file is at most `output_bytes` - 1 (A03 rule 5).
    filler_max = OUTPUT_BYTES - 1
    filled = SPOOL_RUN_BYTES_MAX - 10
    filler_sizes = [filler_max] * 7 + [filled - 7 * filler_max]
    assert sum(filler_sizes) == filled
    assert all(0 < size <= filler_max for size in filler_sizes)

    fillers = [
        _function(
            semantic_runtime,
            f"filler_{i}",
            [_port("n", "input", NUMBER, "open")],
            [_file_port("photo", "output"), _port("ok", "output", NUMBER)],
            FILLER_CODE,
            [_json("n", 8)],
            resource_bounds=CEILING_BOUNDS,
        )
        for i in range(1, 9)
    ]
    # The tested function spools a first file of 5 bytes, which fits
    # (SPOOL_RUN_BYTES_MAX - 5), and a second of 6, one byte over.
    tested = _function(
        semantic_runtime,
        "two_files",
        [],
        [
            _file_port("first", "output"),
            _file_port("second", "output"),
            _port("ok", "output", NUMBER),
        ],
        TWO_FILES_CODE,
        [],
    )
    filler_ids = [f"a_fill_{i}" for i in range(1, 9)]
    _active_flow(
        semantic_runtime,
        "a15_spool_run",
        inputs=[
            _port("n_full", "input", NUMBER, "open"),
            _port("n_last", "input", NUMBER, "open"),
        ],
        outputs=[_port(f"ok_{i}", "output", NUMBER) for i in range(1, 9)]
        + [_port("ok_tested", "output", NUMBER)],
        nodes=[_fn_node(node_id, cv) for node_id, cv in zip(filler_ids, fillers)]
        + [_fn_node("b_two_files", tested)],
        edges=[
            _edge("", "n_full" if i < 8 else "n_last", node_id, "n")
            for i, node_id in enumerate(filler_ids, start=1)
        ]
        + [_edge(node_id, "ok", "", f"ok_{i}") for i, node_id in enumerate(filler_ids, start=1)]
        + [_edge("b_two_files", "ok", "", "ok_tested")],
    )

    run = semantic_runtime.start_run(
        "a15_spool_run",
        inputs=[_json("n_full", filler_sizes[0]), _json("n_last", filler_sizes[-1])],
    )
    run_id = run.run_id
    # The tested node failed and nothing waits: the run ends `failed`, so it
    # keeps its spool (A14 rule 4).
    assert _v(run.status) == "failed"
    trace = _trace(semantic_runtime, run_id)

    # A13 rule 2: the fillers (smaller node ids) executed first and spooled.
    filler_files = []
    for node_id, size in zip(filler_ids, filler_sizes):
        assert _steps(trace, node_id) == [(1, "succeeded")]
        (record,) = [e for e in trace if e.node_id == node_id]
        (photo_port,) = [p for p in record.outputs if p.port == "photo"]
        (item,) = photo_port.items
        assert item.size_bytes == size
        filler_files.append((_spooled_key(item), size))

    # A15 rule 3: the run's spool over `spool_run_bytes_max` concludes the
    # producing element `resource_exhausted`; it keeps no output.
    (tested_record,) = [e for e in trace if e.node_id == "b_two_files"]
    assert _v(tested_record.status) == "resource_exhausted"
    assert tested_record.outputs == ()

    # Only that attempt's files are discarded (both of them, A13 rule 3: an
    # element that does not succeed keeps no output); the files spooled
    # earlier stay and are served.
    assert len(semantic_runtime.run_spool(run_id)) == len(filler_files)
    for key, size in filler_files:
        assert semantic_runtime.read_spooled_file(key).file.size_bytes == size
    for port in ("first", "second"):
        with pytest.raises(Exception) as exc:
            semantic_runtime.read_spooled_file(
                {
                    "run_id": run_id,
                    "producer_node_id": "b_two_files",
                    "map_index": None,
                    "attempt_number": 1,
                    "producer_port": port,
                    "list_index": None,
                }
            )
        # No SpooledFile record names a discarded file.
        assert exc.value.code == "unknown_reference"

    # Control: one byte less from the last filler brings the second file to
    # exactly `spool_run_bytes_max`, which does not exceed it, so the same node
    # succeeds with both files. The first run keeps its spool meanwhile: the
    # ceiling counts one run's files, never another run's.
    control = semantic_runtime.start_run(
        "a15_spool_run",
        inputs=[_json("n_full", filler_sizes[0]), _json("n_last", filler_sizes[-1] - 1)],
    )
    assert _v(control.status) == "succeeded"
    control_trace = _trace(semantic_runtime, control.run_id)
    assert _steps(control_trace, "b_two_files") == [(1, "succeeded")]
    (control_record,) = [e for e in control_trace if e.node_id == "b_two_files"]
    assert sorted(
        (port.port, _only_file([port]).size_bytes)
        for port in control_record.outputs
        if port.port != "ok"
    ) == [("first", 5), ("second", 6)]


def test_file_outlives_run_only_as_fixture(semantic_runtime):
    """[witness: verification:kernel_a15_file_outlives_run_only_as_fixture]

    A15 Required test 5: capturing a failed execution whose input was a
    spooled photo creates a case whose fixture has the photo's digest; after
    release the run's spool is empty and the fixture remains.
    """
    photo = _function(
        semantic_runtime,
        "photo",
        [_port("x", "input", TEXT, "open")],
        [_file_port("photo", "output")],
        PHOTO_CODE,
        [_json("x", "ok-photo")],
    )
    check = _check_function(semantic_runtime)
    _active_flow(
        semantic_runtime,
        "a15_capture",
        inputs=[_port("word", "input", TEXT, "open")],
        outputs=[_port("size", "output", NUMBER)],
        nodes=[_fn_node("a_photo", photo), _fn_node("b_check", check)],
        edges=[
            _edge("", "word", "a_photo", "x"),
            _edge("a_photo", "photo", "b_check", "photo"),
            _edge("b_check", "size", "", "size"),
        ],
    )

    run = semantic_runtime.start_run("a15_capture", inputs=[_json("word", "crash-photo")])
    run_id = run.run_id
    assert _v(run.status) == "failed"
    trace = _trace(semantic_runtime, run_id)
    (failed,) = [e for e in trace if e.node_id == "b_check"]
    assert _v(failed.status) == "crashed"
    # A15 rule 5: it ran in the sandbox — its record names the resources used.
    assert failed.resources_used is not None
    spooled = _only_file(failed.inputs)
    photo_digest = spooled.content_digest
    photo_key = _spooled_key(spooled)
    assert semantic_runtime.read_spooled_file(photo_key).content == b"crash-photo"

    case = semantic_runtime.capture_failed_execution(
        {"run_id": run_id, "node_id": "b_check", "map_index": None, "attempt_number": 1},
        check,
    )
    assert _v(case.origin) == "captured"
    assert case.captured_from.run_id == run_id
    assert case.captured_from.node_id == "b_check"
    # A15 rule 5: the spooled input is copied into the case as a file fixture
    # with the photo's digest.
    fixture = _only_file(case.inputs)
    assert fixture.content_digest == photo_digest
    assert fixture.value_id is not None

    released = semantic_runtime.release_run(run_id)
    assert released.released_at is not None
    # A14 rule 4: the run's spool is empty and none of its files is served.
    assert semantic_runtime.run_spool(run_id) == []
    with pytest.raises(Exception) as exc:
        semantic_runtime.read_spooled_file(photo_key)
    assert exc.value.code == "refused"

    # The fixture remains, with the photo's bytes.
    kept = semantic_runtime.read_fixture_file(fixture.value_id)
    assert kept.content == b"crash-photo"
    assert _v(kept.value.carriage) == "file"


def test_one_record_per_conclusion(semantic_runtime):
    """[witness: verification:kernel_a15_one_record_per_conclusion]

    A15 Required test 6: a run with a three-element mapped node, a skipped
    node and an `upstream_failed` node holds exactly one NodeExecution per
    element, none of the mapped node's own, and one per skipped and per
    `upstream_failed` node; an owner's resolution of an unknown outcome adds
    none.
    """
    vault = _service(semantic_runtime, "vault", [("save_record", "POST", "/records", "draft-write")])
    vault.on("POST", "/records", action="drop_after_request")

    echo = _echo_function(semantic_runtime)
    route = _function(
        semantic_runtime,
        "route",
        [_port("x", "input", TEXT, "open")],
        [_port("route", "output", ROUTE), _port("text", "output", TEXT)],
        ROUTE_CODE,
        [_json("x", "ok")],
    )
    double = _function(
        semantic_runtime,
        "double",
        [_port("x", "input", NUMBER, "open")],
        [_port("y", "output", NUMBER)],
        DOUBLE_CODE,
        [_json("x", 2)],
    )
    save = _note_binding(semantic_runtime, "vault", "save_record")
    _active_flow(
        semantic_runtime,
        "a15_one_record",
        inputs=[
            _port("items", "input", NUMBER, "open", cardinality="many"),
            _port("word", "input", TEXT, "open"),
        ],
        outputs=[
            _port("doubled", "output", NUMBER, cardinality="many"),
            _port("relayed", "output", TEXT),
            _port("saved", "output", TEXT),
        ],
        nodes=[
            _fn_node("f_fail", echo),
            _fn_node("g_route", route),
            _fn_node("m_double", double, map_over="x"),
            _op_node("o_drop", save),
            _fn_node("s_save", echo),
            _fn_node("u_after", echo),
        ],
        edges=[
            _edge("", "word", "f_fail", "x"),
            _edge("", "word", "g_route", "x"),
            _edge("", "items", "m_double", "x"),
            _edge("", "word", "o_drop", "note"),
            # `g_route` always answers "duplicate", so this edge never
            # delivers and `s_save` is skipped (A13 rule 4).
            _edge(
                "g_route",
                "text",
                "s_save",
                "x",
                guard={"guard_port": "route", "guard_value": '"new"'},
            ),
            _edge("f_fail", "y", "u_after", "x"),
            _edge("m_double", "y", "", "doubled"),
            _edge("s_save", "y", "", "saved"),
            _edge("u_after", "y", "", "relayed"),
        ],
    )

    run = semantic_runtime.start_run(
        "a15_one_record", inputs=[_json("items", [1, 2, 3]), _json("word", "fail")]
    )
    run_id = run.run_id
    # `o_drop`'s request is dropped after it was written: it waits on its
    # unknown outcome.
    assert _v(run.status) == "pending"
    assert _waits(run) == [("o_drop", None, "outcome_unknown", None)]

    trace = _trace(semantic_runtime, run_id)
    # A15 rule 1: one record per concluded element, per skipped and per
    # `upstream_failed` node; the mapped node has none of its own (it ran
    # elements), so no `m_double` record without `map_index`.
    assert sorted(
        ((e.node_id, -1 if e.map_index is None else e.map_index), _v(e.status))
        for e in trace
    ) == [
        (("f_fail", -1), "crashed"),
        (("g_route", -1), "succeeded"),
        (("m_double", 0), "succeeded"),
        (("m_double", 1), "succeeded"),
        (("m_double", 2), "succeeded"),
        (("o_drop", -1), "outcome_unknown"),
        (("s_save", -1), "skipped_by_guard"),
        (("u_after", -1), "upstream_failed"),
    ]
    assert all(e.attempt_number == 1 for e in trace)

    # A15 rule 1, A11 rule 3: the owner's resolution writes no NodeExecution.
    resolved = semantic_runtime.continue_after_resolution(
        {"run_id": run_id, "node_id": "o_drop", "map_index": None, "attempt_number": 1},
        "applied",
    )
    # The resolved element counts as succeeded; `f_fail` failed (A13 rule 7).
    assert _v(resolved.status) == "failed"
    assert _trace(semantic_runtime, run_id) == trace
    (attempt,) = _attempts(semantic_runtime, run_id)
    assert _v(attempt.status) == "applied"
    assert _v(attempt.resolved_by.kind) == "owner"
    assert len(vault.requests) == 1
