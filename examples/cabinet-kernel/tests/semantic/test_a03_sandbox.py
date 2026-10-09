"""Witness tests for accepted decision A03 (02_rules_functions.md).

Every function execution runs in a fresh isolated environment, bounded from
outside and without a clock, and ends in exactly one outcome of a closed set
taken in a fixed order. Each test carries the witness name its Required test
declares.

The Factory project supplies the ``semantic_runtime`` pytest fixture. It binds
these scenarios to the generated public operations of State 5 — named here by
their operation names, with arguments shaped as the State 6 models — without
changing the assertions below. Each test gets a fresh, empty kernel store.

Fixture surface used here:

- ``issue_contract_version(slot_id, purpose, inputs, outputs,
  resource_bounds)`` -> contract_version_id; ports are dicts with the fields
  of Port (M01), bounds a ResourceBoundsRequest dict; acts as agent
  ``author``;
- ``add_trial_case(contract_version_id, inputs, expected_outputs=None)`` ->
  ShownAddedTrialCase; inputs are RequestPayload dicts;
- ``submit_implementation(contract_version_id, code)`` -> ShownSubmission;
- ``try_implementation(implementation_id, trial_case_ids=())`` -> tuple of
  ShownTrialExecution, one per case in corpus order;
- ``compose_flow_version``, ``activate_flow_version``, ``start_run`` and
  ``page_records`` for one execution inside a run (rule 1);
- ``read_implementation``, ``read_slot`` to read back what was recorded.

Sandbox outcomes are observed through trial executions: the TrialOutcome of a
try, and the FailingCaseRefusal of the admission verdict. Capabilities are used
only where a Required test looks from outside the kernel's answers:
``sandbox_executions()`` and ``sandbox_runtime_paths()`` (processes, mounts,
interfaces), ``host.remove_bubblewrap()`` with ``restart()`` (start),
``faults.unconfirmed_cleanup(nth)`` — counted from the moment it is set — with
``kernel_exited()`` (cleanup fault).
"""

import json

import pytest

TEXT = '{"type":"string"}'
OBJECT = '{"type":"object"}'

# Bounds well below the A20 rule 1 ceilings (release v1: wall_time_ms 30000,
# memory_bytes 536870912, output_bytes 67108864, process_count 8), small enough
# that a busy, allocation or fork loop reaches them quickly.
BOUNDS = {
    "wall_time_ms": 2000,
    "memory_bytes": 268435456,
    "output_bytes": 1024,
    "process_count": 4,
}

CONFORMING = """
def run(inputs):
    return {"y": inputs["x"]}
"""


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


def _json(port, value):
    return {"payload_kind": "json", "port": port, "json_text": json.dumps(value)}


def _function(semantic_runtime, slot_id, output_schema=TEXT, bounds=BOUNDS):
    """A function of one text input `x` and one output `y`, with one case."""
    contract_version_id = semantic_runtime.issue_contract_version(
        slot_id,
        purpose=f"A03 witness: {slot_id}",
        inputs=[_port("x", "input", TEXT, "open")],
        outputs=[_port("y", "output", output_schema)],
        resource_bounds=dict(bounds),
    )
    semantic_runtime.add_trial_case(contract_version_id, inputs=[_json("x", "hello")])
    return contract_version_id


def _value(enum_or_value):
    return getattr(enum_or_value, "value", enum_or_value)


def _conclude(semantic_runtime, contract_version_id, code):
    """Submit `code` and try it on the one case; returns (submission, execution)."""
    submission = semantic_runtime.submit_implementation(contract_version_id, code)
    (execution,) = semantic_runtime.try_implementation(
        submission.implementation.implementation_id
    )
    return submission, execution


def _assert_concluded(submission, execution, outcome):
    """The try and the admission verdict name the same sandbox outcome."""
    assert _value(execution.outcome) == outcome
    if outcome == "passed":
        assert _value(submission.verdict.verdict) == "admitted"
    else:
        assert _value(submission.verdict.verdict) == "refused"
        assert submission.verdict.reason.reason_kind == "failing_case"
        assert _value(submission.verdict.reason.outcome) == outcome
        assert submission.activation is None


def _output_json(execution, port):
    (shown,) = [p for p in execution.outputs if p.port == port]
    (item,) = shown.items
    assert item.shown_kind == "content"
    return json.loads(item.json_text)


def test_trap_hit_is_sandbox_violation(semantic_runtime):
    """[witness: verification:kernel_a03_trap_hit_is_sandbox_violation]

    A03 Required test 1: Code that calls `time.time()`, `os.urandom`, opens a
    socket or reads `/etc` concludes `sandbox_violation`, also when it swallows
    the error and returns a conforming output.
    """
    cv = _function(semantic_runtime, "a03_traps")

    # Each body hits one trap of rule 4, catches whatever the trap raises and
    # then returns a dict that fits the contract exactly.
    hits = {
        "time.time()": "import time\n        time.time()",
        "os.urandom": "import os\n        os.urandom(8)",
        "socket": "import socket\n        socket.socket()",
        "read /etc": "open('/etc/passwd').read()",
    }
    for label, body in hits.items():
        swallowed = f"""
def run(inputs):
    try:
        {body}
    except BaseException:
        pass
    return {{"y": inputs["x"]}}
"""
        submission, execution = _conclude(semantic_runtime, cv, swallowed)
        # A03 rule 4: any recorded hit makes the execution sandbox_violation,
        # even when the code catches it and returns a conforming output.
        _assert_concluded(submission, execution, "sandbox_violation")
        assert not execution.outputs, label

    # Not swallowed: the trap's exception escapes `run`; rule 5 still names the
    # trap before `crashed`.
    raising = """
def run(inputs):
    import time
    time.time()
    return {"y": inputs["x"]}
"""
    submission, execution = _conclude(semantic_runtime, cv, raising)
    _assert_concluded(submission, execution, "sandbox_violation")

    # Control: the same conforming return without any trap passes, so the
    # violations above come from the traps, not from the shape of the code.
    submission, execution = _conclude(semantic_runtime, cv, CONFORMING)
    _assert_concluded(submission, execution, "passed")
    assert _output_json(execution, "y") == "hello"


def test_deadline_and_limits_classified(semantic_runtime):
    """[witness: verification:kernel_a03_deadline_and_limits_classified]

    A03 Required test 2: A busy loop ends `timeout`; an allocation loop and a
    fork loop end `resource_exhausted`; no process survives.
    """
    cv = _function(semantic_runtime, "a03_limits")

    busy = """
def run(inputs):
    while True:
        pass
"""
    allocation = """
def run(inputs):
    blocks = []
    while True:
        blocks.append(bytearray(1 << 20))
"""
    # The children keep running; the parent forks until the process count is
    # reached, then the failing fork escapes `run`.
    fork = """
def run(inputs):
    import os
    while True:
        if os.fork() == 0:
            while True:
                pass
"""
    # A03 rule 5: wall deadline passed — timeout; a memory or process-count
    # limit hit — resource_exhausted (before crashed, which the escaping
    # MemoryError or fork error would otherwise give).
    expected = [
        (busy, "timeout"),
        (allocation, "resource_exhausted"),
        (fork, "resource_exhausted"),
    ]
    for code, outcome in expected:
        submission, execution = _conclude(semantic_runtime, cv, code)
        _assert_concluded(submission, execution, outcome)

    # Control: under the same bounds conforming code passes, so the outcomes
    # above come from the loops, not from bounds too small to run at all.
    submission, execution = _conclude(semantic_runtime, cv, CONFORMING)
    _assert_concluded(submission, execution, "passed")

    # A03 rule 7: an execution completes only after every process of its
    # environment is reaped.
    executions = semantic_runtime.sandbox_executions()
    assert len(executions) >= 2 * (len(expected) + 1)
    for observed in executions:
        assert not observed.processes_left


def test_output_over_bound_not_truncated(semantic_runtime):
    """[witness: verification:kernel_a03_output_over_bound_not_truncated]

    A03 Required test 3: An output one byte over `output_bytes` is
    `resource_exhausted`, not truncated.
    """
    cv = _function(semantic_runtime, "a03_output_bound")
    bound = BOUNDS["output_bytes"]

    # A03 rule 5: the output count is the canonical JSON bytes of every value
    # output; a string of n characters `a` is n + 2 bytes with its quotes.
    over = f"""
def run(inputs):
    return {{"y": "a" * {bound - 1}}}
"""
    submission, execution = _conclude(semantic_runtime, cv, over)
    # A03 rule 5: output over the bound is a failure, never truncated.
    _assert_concluded(submission, execution, "resource_exhausted")
    assert not execution.outputs

    # Control: exactly at the bound the same code shape passes with its whole
    # output, so the failure above is the one byte, not the size check missing
    # or counting differently.
    at = f"""
def run(inputs):
    return {{"y": "a" * {bound - 2}}}
"""
    submission, execution = _conclude(semantic_runtime, cv, at)
    _assert_concluded(submission, execution, "passed")
    assert _output_json(execution, "y") == "a" * (bound - 2)
    assert execution.resources_used.output_bytes == bound


def test_unloadable_module_is_crashed(semantic_runtime):
    """[witness: verification:kernel_a03_unloadable_module_is_crashed]

    A03 Required test 4: A module without `run`, and one with a syntax error,
    are `crashed`; neither raises inside the kernel process. Submitting code
    never compiles, imports or parses it — the kernel process never interprets
    agent text (A16 rule 5) — so a module that cannot load is stored as an
    implementation like any other, its trial executions are `crashed` and
    admission refuses it (A04 rule 3). State 0's "invalid … code refused" is
    the refusal of the request itself: code over its bound or a request off
    its schema (A16 rule 4).
    """
    cv = _function(semantic_runtime, "a03_unloadable")

    no_run = """
def compute(inputs):
    return {"y": inputs["x"]}
"""
    syntax_error = """
def run(inputs)
    return {"y": inputs["x"]}
"""
    for code in (no_run, syntax_error):
        # The submission is answered, not refused: the kernel stored the code
        # without loading it.
        submission, execution = _conclude(semantic_runtime, cv, code)
        # A03 rule 5: module failed to load or has no `run` — crashed;
        # A04 rule 3: admission refuses it with that outcome.
        _assert_concluded(submission, execution, "crashed")

        implementation_id = submission.implementation.implementation_id
        read = semantic_runtime.read_implementation(implementation_id)
        assert read.implementation.implementation_id == implementation_id
        assert read.implementation.code == code

    # The kernel still serves after both: a conforming implementation passes
    # and is admitted (also the control that this corpus can pass at all).
    submission, execution = _conclude(semantic_runtime, cv, CONFORMING)
    _assert_concluded(submission, execution, "passed")
    assert submission.activation is not None


def test_extra_output_key_contract_violation(semantic_runtime):
    """[witness: verification:kernel_a03_extra_output_key_contract_violation]

    A03 Required test 5: A returned dict with an extra key is
    `contract_violation`.
    """
    cv = _function(semantic_runtime, "a03_extra_key")

    extra = """
def run(inputs):
    return {"y": inputs["x"], "z": "extra"}
"""
    submission, execution = _conclude(semantic_runtime, cv, extra)
    # A03 rule 5: the returned dict does not have exactly the output ports.
    _assert_concluded(submission, execution, "contract_violation")
    assert not execution.outputs

    # Control: the same return without the extra key passes.
    submission, execution = _conclude(semantic_runtime, cv, CONFORMING)
    _assert_concluded(submission, execution, "passed")


def test_kernel_refuses_start_without_sandbox(semantic_runtime):
    """[witness: verification:kernel_a03_kernel_refuses_start_without_sandbox]

    A03 Required test 7: With `bubblewrap` absent the kernel does not start and
    names the missing sandbox.
    """
    # Control: with bubblewrap present the kernel serves and starts again, so
    # the failed start below comes from the missing sandbox.
    _function(semantic_runtime, "a03_start")
    started = semantic_runtime.restart()
    assert started.started is True

    semantic_runtime.host.remove_bubblewrap()
    outcome = semantic_runtime.restart()

    # A03 rule 8: without bubblewrap the kernel does not start and says why;
    # State 5 serve_kernel: a stopped start names the failing step on standard
    # error with a non-zero exit.
    assert outcome.started is False
    assert outcome.exit_code not in (None, 0)
    assert "bubblewrap" in outcome.stderr or "bwrap" in outcome.stderr


def test_outcome_precedence_order(semantic_runtime):
    """[witness: verification:kernel_a03_outcome_precedence_order]

    A03 Required test 8: Code that calls `time.time()`, swallows the error and
    then busy-loops ends `timeout`, not `sandbox_violation`; code that hits a
    trap and returns a dict with an extra key ends `sandbox_violation`, not
    `contract_violation`.
    """
    cv = _function(semantic_runtime, "a03_precedence")

    trap_then_busy = """
def run(inputs):
    try:
        import time
        time.time()
    except BaseException:
        pass
    while True:
        pass
"""
    trap_then_extra = """
def run(inputs):
    try:
        import time
        time.time()
    except BaseException:
        pass
    return {"y": inputs["x"], "z": "extra"}
"""
    # A03 rule 5 order: timeout, resource_exhausted, sandbox_violation,
    # crashed, contract_violation; the first that holds decides.
    submission, execution = _conclude(semantic_runtime, cv, trap_then_busy)
    _assert_concluded(submission, execution, "timeout")

    submission, execution = _conclude(semantic_runtime, cv, trap_then_extra)
    _assert_concluded(submission, execution, "sandbox_violation")

    # Controls: each lower-ranked condition alone is detected, so the results
    # above come from the order and not from a missing check.
    trap_only = """
def run(inputs):
    try:
        import time
        time.time()
    except BaseException:
        pass
    return {"y": inputs["x"]}
"""
    extra_only = """
def run(inputs):
    return {"y": inputs["x"], "z": "extra"}
"""
    submission, execution = _conclude(semantic_runtime, cv, trap_only)
    _assert_concluded(submission, execution, "sandbox_violation")

    submission, execution = _conclude(semantic_runtime, cv, extra_only)
    _assert_concluded(submission, execution, "contract_violation")


def test_env_holds_only_hash_seed(semantic_runtime):
    """[witness: verification:kernel_a03_env_holds_only_hash_seed]

    A03 Required test 9: An implementation whose `run` returns
    `dict(os.environ)` on a `value` output port succeeds with exactly
    `{"PYTHONHASHSEED": "0"}`.
    """
    cv = semantic_runtime.issue_contract_version(
        "a03_environment",
        purpose="A03 witness: a03_environment",
        inputs=[_port("x", "input", TEXT, "open")],
        outputs=[_port("y", "output", OBJECT)],
        resource_bounds=dict(BOUNDS),
    )
    # A03 rule 1: the environment holds only PYTHONHASHSEED=0. The case states
    # that as its expected output, so admission compares digests (A04 rule 3).
    expected = {"PYTHONHASHSEED": "0"}
    semantic_runtime.add_trial_case(
        cv,
        inputs=[_json("x", "hello")],
        expected_outputs=[_json("y", expected)],
    )

    environment = """
def run(inputs):
    import os
    return {"y": dict(os.environ)}
"""
    submission, execution = _conclude(semantic_runtime, cv, environment)
    _assert_concluded(submission, execution, "passed")
    assert _output_json(execution, "y") == expected
    assert submission.activation is not None


def test_fresh_env_no_network_no_host_mounts(semantic_runtime):
    """[witness: verification:kernel_a03_fresh_env_no_network_no_host_mounts]

    A03 Required test 10: Inspected from outside it, each execution's
    environment has no network interface, mounts no host directory except the
    read-only runtime and its exchange directory, and has an exchange directory
    no other execution used.
    """
    cv = semantic_runtime.issue_contract_version(
        "a03_isolation",
        purpose="A03 witness: a03_isolation",
        inputs=[_port("x", "input", TEXT, "open")],
        outputs=[_port("y", "output", TEXT)],
        resource_bounds=dict(BOUNDS),
    )
    semantic_runtime.add_trial_case(cv, inputs=[_json("x", "one")])
    semantic_runtime.add_trial_case(cv, inputs=[_json("x", "two")])
    # Counted from here: the kernel has started, so its start probe (A03 rule
    # 8) is already behind this count.
    baseline = len(semantic_runtime.sandbox_executions())

    # Admission (two executions), a try (two more) ...
    submission = semantic_runtime.submit_implementation(cv, CONFORMING)
    assert submission.activation is not None
    semantic_runtime.try_implementation(submission.implementation.implementation_id)
    # A03 rule 1: every trial execution ran in a sandbox environment.
    assert len(semantic_runtime.sandbox_executions()) == baseline + 4

    # ... and one execution inside a run: A03 rule 1 holds for trial and run
    # alike.
    composed = semantic_runtime.compose_flow_version(
        "a03_isolation_flow",
        purpose="A03 witness: isolation in a run",
        inputs=[_port("x", "input", TEXT, "open")],
        outputs=[_port("y", "output", TEXT)],
        nodes=[
            {
                "node_id": "f",
                "kind": "function",
                "contract_version_id": cv,
                "binding_id": None,
                "map_over": None,
            }
        ],
        edges=[
            {"from_node": "", "from_port": "x", "to_node": "f", "to_port": "x", "guard": None},
            {"from_node": "f", "from_port": "y", "to_node": "", "to_port": "y", "guard": None},
        ],
        constants=[],
    )
    assert composed.proof.proven is True
    semantic_runtime.activate_flow_version(composed.flow_version.flow_version_id)
    run = semantic_runtime.start_run("a03_isolation_flow", [_json("x", "three")])
    assert _value(run.status) == "succeeded"

    executions = semantic_runtime.sandbox_executions()
    # A03 rule 1: the run's one execution ran in a sandbox environment too —
    # there is no in-process or fast path for a run.
    assert len(executions) == baseline + 5
    runtime = set(semantic_runtime.sandbox_runtime_paths())

    exchange_directories = []
    for observed in executions:
        # A03 rule 1: new network namespace with no network interface.
        assert not observed.network_interfaces
        # A03 rule 1: no host directory is mounted except the read-only
        # runtime and the one private exchange directory.
        assert observed.exchange_directory in observed.mounts
        assert set(observed.mounts) - {observed.exchange_directory} <= runtime
        exchange_directories.append(observed.exchange_directory)

    # A03 rule 1: a fresh environment each time — no exchange directory reused.
    assert len(set(exchange_directories)) == len(exchange_directories)


def test_unconfirmed_cleanup_stops_kernel(semantic_runtime):
    """[witness: verification:kernel_a03_unconfirmed_cleanup_stops_kernel]

    A03 Required test 11: When removal of the exchange directory cannot be
    confirmed, the execution is recorded `crashed` with detail
    `cleanup_failed`, its output is discarded and the kernel process stops.
    """
    cv = _function(semantic_runtime, "a03_cleanup")

    # Control: without the fault a conforming implementation passes and is
    # activated, so what follows comes from the cleanup fault alone.
    control = semantic_runtime.submit_implementation(cv, CONFORMING)
    assert _value(control.verdict.verdict) == "admitted"
    serving = control.activation
    assert serving is not None

    other = """
def run(inputs):
    return {"y": inputs["x"] + "!"}
"""
    semantic_runtime.faults.unconfirmed_cleanup(nth=1)
    with pytest.raises(Exception) as exc:
        semantic_runtime.submit_implementation(cv, other)
    # State 5 Conventions, "Stop required": the record is written, the surface
    # answers internal_error and ends the process.
    assert exc.value.code == "internal_error"

    # A03 rule 7: the kernel process stops.
    assert semantic_runtime.kernel_exited() is not None

    started = semantic_runtime.restart()
    assert started.started is True

    implementations = semantic_runtime.page_records(
        "implementation",
        {"filter_kind": "equals", "field": "contract_version_id", "value": cv},
        page_size=200,
    ).records.implementations
    # The implementation was recorded before admission began (State 5
    # submit_implementation: record_implementation, then the executions).
    control_id = control.implementation.implementation_id
    (faulted,) = [i for i in implementations if i.implementation_id != control_id]
    faulted_id = faulted.implementation_id

    (execution,) = semantic_runtime.page_records(
        "trial_execution",
        {"filter_kind": "equals", "field": "implementation_id", "value": faulted_id},
        page_size=200,
    ).records.trial_executions
    # A03 rule 7: recorded crashed with detail cleanup_failed, output discarded
    # although the code returned a conforming output.
    assert _value(execution.outcome) == "crashed"
    assert _value(execution.detail_code) == "cleanup_failed"
    assert not execution.outputs

    # A04 rule 2: no verdict is recorded for the interrupted admission, and the
    # earlier activation keeps serving.
    verdicts = semantic_runtime.page_records(
        "admission_verdict",
        {"filter_kind": "equals", "field": "implementation_id", "value": faulted_id},
        page_size=200,
    ).records.admission_verdicts
    assert len(verdicts) == 0
    slot = semantic_runtime.read_slot("a03_cleanup")
    (history,) = [
        h for h in slot.contract_versions if h.contract_version.contract_version_id == cv
    ]
    assert history.serving_activation.store_position == serving.store_position
    assert history.serving_activation.implementation_id == control_id
