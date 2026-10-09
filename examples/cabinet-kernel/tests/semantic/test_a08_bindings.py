"""Witness tests for accepted decision A08 (02_rules_services.md).

A binding pins one manifest operation: the kernel reads a service's record only
at its one path and revision, accepts only an operation exposed as exactly one
HTTP route whose key fields are input ports, and pins the digest of that one
capability entry, so a changed entry stops the send and nothing reaches the
service. Each test carries the witness name its Required test declares.

The Factory project supplies the ``semantic_runtime`` pytest fixture. It binds
these scenarios to the generated public operations of State 5 — named here by
their operation names, with arguments shaped as the State 6 models — without
changing the assertions below. Each test gets a fresh, empty kernel store; the
installation starts with the owner, agent ``author`` and agent ``helper``, no
service selected and no credential.

Fixture surface used here:

- ``propose_binding(service_id, operation_name, inputs, outputs)`` ->
  OperationBinding (M11), as agent ``author``; ``accept_binding(binding_id)``
  and ``read_binding(binding_id)`` -> OperationBinding, as the owner;
- ``compose_flow_version(flow_id, purpose, inputs, outputs, nodes, edges,
  constants)`` -> ComposedFlowVersion, as agent ``author``;
  ``activate_flow_version(flow_version_id)`` -> FlowActivation, as the owner;
- ``start_run(flow_id, inputs)`` -> ShownRun, as the owner; inputs are
  RequestJsonValue dicts;
- ``page_records(record_type, record_filter, page_size)`` -> RecordPageAnswer:
  ``binding``, ``node_execution`` (the trace) and ``effect_attempt``;
- capabilities: ``manifest.write_record`` (with ``revision=`` and
  ``file_name=``), ``manifest.new_revision``,
  ``installation.set_manifest_revision``, ``installation.select_instance``,
  ``installation.set_credential``, ``stub_service`` and ``restart``.
"""

import pytest

TEXT = '{"type":"string"}'
NUMBER = '{"type":"integer"}'

SERVICE = "drafts"
INSTANCE = "rig"
CREDENTIAL_HEADER = "X-Api-Key"
CREDENTIAL = "a08-canary-credential-7f3c"


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


def _capability(name, routes, effect_class, idempotency_key=None, **extra):
    capability = {
        "name": name,
        "exposed_as": {"http_api": list(routes)},
        "effect_class": effect_class,
        "idempotency_key": idempotency_key,
    }
    capability.update(extra)
    return capability


def _record(service, capabilities, base_url):
    return {
        "service": service,
        "capabilities": capabilities,
        "instances": [
            {
                "instance_name": INSTANCE,
                "api_base_url": base_url,
                "required_headers": None,
                "instance_class": "disposable_rig",
            }
        ],
    }


def _select(semantic_runtime, service_id):
    semantic_runtime.installation.select_instance(service_id, INSTANCE)


def _install(semantic_runtime, service_id):
    """Select the instance and give the service its credential (A17)."""
    _select(semantic_runtime, service_id)
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


def _started(outcome):
    return outcome["started"] if isinstance(outcome, dict) else outcome.started


def _operation_flow(semantic_runtime, flow_id, binding_id, inputs, outputs):
    """An active flow of one operation node `op`, its ports wired to the
    flow's own inputs and outputs (a flow endpoint is node "", A05 rule 2)."""
    composed = semantic_runtime.compose_flow_version(
        flow_id,
        purpose=f"A08 witness: {flow_id}",
        inputs=[_port(p["name"], "input", p["value_schema"]) for p in inputs],
        outputs=[_port(p["name"], "output", p["value_schema"], None) for p in outputs],
        nodes=[_node("op", binding_id)],
        edges=[_edge("", p["name"], "op", p["name"]) for p in inputs]
        + [_edge("op", p["name"], "", p["name"]) for p in outputs],
        constants=[],
    )
    assert composed.proof.proven is True
    semantic_runtime.activate_flow_version(composed.flow_version.flow_version_id)
    return flow_id


def _trace(semantic_runtime, run_id):
    page = semantic_runtime.page_records(
        "node_execution",
        {"filter_kind": "equals", "field": "run_id", "value": run_id},
        page_size=200,
    )
    return page.records.node_executions


def _attempts(semantic_runtime, run_id):
    page = semantic_runtime.page_records(
        "effect_attempt",
        {"filter_kind": "equals", "field": "run_id", "value": run_id},
        page_size=200,
    )
    return page.records.effect_attempts


def _bindings(semantic_runtime):
    return semantic_runtime.page_records("binding", page_size=200).records.bindings


DRAFT_INPUTS = [_port("title", "input", TEXT)]
DRAFT_OUTPUTS = [_port("draft_id", "output", TEXT)]


def test_invocable_only_single_http_route(semantic_runtime):
    """[witness: verification:kernel_a08_invocable_only_single_http_route]

    A08 Required test 1: a proposal for an operation exposed only over `mcp` is
    refused naming rule 3.
    """
    stub = semantic_runtime.stub_service()
    mcp_only = {
        "name": "list_drafts_mcp",
        "exposed_as": {"mcp": ["list_drafts"]},
        "effect_class": "read",
        "idempotency_key": None,
    }
    over_http = _capability("list_drafts", ["GET /drafts"], "read")
    semantic_runtime.manifest.write_record(
        SERVICE, _record(SERVICE, [mcp_only, over_http], stub.base_url)
    )
    _install(semantic_runtime, SERVICE)

    inputs = [_port("q", "input", TEXT)]
    outputs = [_port("count", "output", NUMBER)]

    # Every check of A08 rule 5 before rule 3 passes: the record is at its
    # path, the operation exists, its effect class is one of M10's five.
    with pytest.raises(Exception) as exc:
        semantic_runtime.propose_binding(SERVICE, "list_drafts_mcp", inputs, outputs)
    # A08 rule 3: no `exposed_as.http_api` route -> not invocable.
    assert exc.value.code == "refused"
    # A refusal writes nothing (State 5, Conventions).
    assert list(_bindings(semantic_runtime)) == []

    # Control: the same record, ports and instance with one HTTP route is
    # proposed, so the refusal above is rule 3's, not another check's.
    control = semantic_runtime.propose_binding(SERVICE, "list_drafts", inputs, outputs)
    assert _enum(control.status) == "proposed"
    assert _enum(control.effect_class) == "read"
    assert [b.binding_id for b in _bindings(semantic_runtime)] == [control.binding_id]


def test_non_read_key_field_must_be_input_port(semantic_runtime):
    """[witness: verification:kernel_a08_non_read_key_field_must_be_input_port]

    A08 Required test 2: a proposal for a `draft-write` operation whose key
    field `material_id` is not an input port is refused.
    """
    stub = semantic_runtime.stub_service()
    save = _capability(
        "save_draft", ["POST /drafts"], "draft-write", idempotency_key="material_id"
    )
    semantic_runtime.manifest.write_record(
        SERVICE, _record(SERVICE, [save], stub.base_url)
    )
    _install(semantic_runtime, SERVICE)

    # A08 rules 4-5: for an operation other than `read`, each key field must be
    # the name of one `value` input port of the proposal. `material_id` is
    # first no port at all, then an output port: a port of the other direction
    # is still not an input port.
    for outputs in (
        DRAFT_OUTPUTS,
        DRAFT_OUTPUTS + [_port("material_id", "output", TEXT)],
    ):
        with pytest.raises(Exception) as exc:
            semantic_runtime.propose_binding(
                SERVICE, "save_draft", [_port("title", "input", TEXT)], outputs
            )
        assert exc.value.code == "refused", [p["name"] for p in outputs]
    assert list(_bindings(semantic_runtime)) == []

    # Control: with `material_id` as a value input port the same proposal is
    # recorded, its class and key fields copied from the manifest (M11).
    control = semantic_runtime.propose_binding(
        SERVICE,
        "save_draft",
        [_port("material_id", "input", TEXT), _port("title", "input", TEXT)],
        DRAFT_OUTPUTS,
    )
    assert _enum(control.status) == "proposed"
    assert _enum(control.effect_class) == "draft-write"
    assert tuple(control.idempotency_key_fields) == ("material_id",)
    assert [b.binding_id for b in _bindings(semantic_runtime)] == [control.binding_id]


def test_digest_covers_only_own_capability_entry(semantic_runtime):
    """[witness: verification:kernel_a08_digest_covers_only_own_capability_entry]

    A08 Required test 3: editing another capability's `note` in the same
    service record leaves the binding invocable.
    """
    stub = semantic_runtime.stub_service()
    stub.on("POST", "/drafts", status=200, json={"draft_id": "d-1"})

    create = _capability("create_draft", ["POST /drafts"], "draft-write")
    listing_v1 = _capability("list_drafts", ["GET /drafts"], "read", note="v1")
    semantic_runtime.manifest.write_record(
        SERVICE, _record(SERVICE, [create, listing_v1], stub.base_url)
    )
    _install(semantic_runtime, SERVICE)

    binding = semantic_runtime.propose_binding(
        SERVICE, "create_draft", DRAFT_INPUTS, DRAFT_OUTPUTS
    )
    semantic_runtime.accept_binding(binding.binding_id)
    flow_id = _operation_flow(
        semantic_runtime, "a08_own_entry", binding.binding_id, DRAFT_INPUTS, DRAFT_OUTPUTS
    )
    first = semantic_runtime.start_run(flow_id, [_value("title", '"one"')])
    assert _enum(first.status) == "succeeded"
    assert len(stub.requests) == 1

    # Only the other capability's `note` changes; the manifest revision is
    # read at start, so the change takes effect at a restart (A08 rule 6).
    listing_v2 = _capability("list_drafts", ["GET /drafts"], "read", note="v2")
    other_edited = semantic_runtime.manifest.new_revision()
    semantic_runtime.manifest.write_record(
        SERVICE,
        _record(SERVICE, [create, listing_v2], stub.base_url),
        revision=other_edited,
    )
    semantic_runtime.installation.set_manifest_revision(other_edited)
    assert _started(semantic_runtime.restart()) is True

    second = semantic_runtime.start_run(flow_id, [_value("title", '"two"')])
    # A08 rule 2: the digest covers only the `create_draft` entry, so the
    # binding still matches and the request is sent.
    assert _enum(second.status) == "succeeded"
    assert len(stub.requests) == 2
    (execution,) = _trace(semantic_runtime, second.run_id)
    assert _enum(execution.status) == "succeeded"
    assert execution.detail_code is None

    # Control: the same edit made to the binding's own entry stops the send,
    # so the result above comes from the digest's scope, not from a digest
    # that is never compared.
    create_noted = _capability("create_draft", ["POST /drafts"], "draft-write", note="v2")
    own_edited = semantic_runtime.manifest.new_revision()
    semantic_runtime.manifest.write_record(
        SERVICE,
        _record(SERVICE, [create_noted, listing_v2], stub.base_url),
        revision=own_edited,
    )
    semantic_runtime.installation.set_manifest_revision(own_edited)
    assert _started(semantic_runtime.restart()) is True

    third = semantic_runtime.start_run(flow_id, [_value("title", '"three"')])
    (stale,) = _trace(semantic_runtime, third.run_id)
    assert _enum(stale.status) == "operation_failed"
    assert _enum(stale.detail_code) == "binding_stale"
    assert len(stub.requests) == 2


def test_changed_digest_stale_nothing_sent(semantic_runtime):
    """[witness: verification:kernel_a08_changed_digest_stale_nothing_sent]

    A08 Required test 4: after a restart with a revision that changes the
    operation's entry, the node concludes `binding_stale` and no request
    reaches the service.
    """
    stub = semantic_runtime.stub_service()
    stub.on("POST", "/drafts", status=200, json={"draft_id": "d-1"})
    stub.on("POST", "/v2/drafts", status=200, json={"draft_id": "d-2"})

    create_v1 = _capability("create_draft", ["POST /drafts"], "draft-write")
    semantic_runtime.manifest.write_record(
        SERVICE, _record(SERVICE, [create_v1], stub.base_url)
    )
    _install(semantic_runtime, SERVICE)

    binding = semantic_runtime.propose_binding(
        SERVICE, "create_draft", DRAFT_INPUTS, DRAFT_OUTPUTS
    )
    accepted = semantic_runtime.accept_binding(binding.binding_id)
    flow_id = _operation_flow(
        semantic_runtime, "a08_stale", binding.binding_id, DRAFT_INPUTS, DRAFT_OUTPUTS
    )

    # Control: before the change the same flow reaches the service once.
    before = semantic_runtime.start_run(flow_id, [_value("title", '"before"')])
    assert _enum(before.status) == "succeeded"
    assert len(stub.requests) == 1

    # The operation's own entry changes (still invocable, another path).
    create_v2 = _capability("create_draft", ["POST /v2/drafts"], "draft-write")
    changed = semantic_runtime.manifest.new_revision()
    semantic_runtime.manifest.write_record(
        SERVICE, _record(SERVICE, [create_v2], stub.base_url), revision=changed
    )
    semantic_runtime.installation.set_manifest_revision(changed)
    assert _started(semantic_runtime.restart()) is True

    run = semantic_runtime.start_run(flow_id, [_value("title", '"after"')])

    # A08 rule 6: nothing is sent and the element concludes `operation_failed`
    # with detail `binding_stale`; A09 rule 6: no EffectAttempt exists for it.
    (execution,) = _trace(semantic_runtime, run.run_id)
    assert execution.node_id == "op"
    assert execution.attempt_number == 1
    assert _enum(execution.status) == "operation_failed"
    assert _enum(execution.detail_code) == "binding_stale"
    assert list(execution.outputs) == []
    assert list(_attempts(semantic_runtime, run.run_id)) == []
    assert len(stub.requests) == 1
    # A13 rule 7: an `operation_failed` node with nothing waiting ends the run
    # `failed`.
    assert _enum(run.status) == "failed"

    # A08 rule 6: the binding itself does not change.
    after = semantic_runtime.read_binding(binding.binding_id)
    assert _enum(after.status) == "accepted"
    assert after.record_digest == accepted.record_digest


def test_record_read_only_at_pinned_path(semantic_runtime):
    """[witness: verification:kernel_a08_record_read_only_at_pinned_path]

    A08 Required test 6: a record present only under another file name in
    `manifest_location`, or only at a revision other than the configured one,
    is not read: the proposal is refused naming the absent record. A record
    whose `service` field differs from `service_id` is refused naming that
    check, and a `service_id` holding an uppercase letter or a `/` is refused
    before any path is built.
    """
    stub = semantic_runtime.stub_service()
    write = semantic_runtime.manifest.write_record

    def record(service):
        return _record(
            service, [_capability("list_drafts", ["GET /drafts"], "read")], stub.base_url
        )

    # Under another file name in `manifest_location`.
    write("renamed", record("renamed"), file_name="renamed_record.json")
    # Only at a revision that is not the configured one.
    other_revision = semantic_runtime.manifest.new_revision()
    write("archived", record("archived"), revision=other_revision)
    # At the pinned path, with another `service` field.
    write("mismatch", record(SERVICE), file_name="mismatch.json")
    # At the path a kernel would build from the raw identity, each with a
    # matching `service` field and a selected instance: only the identity
    # check can refuse these.
    write("Drafts", record("Drafts"), file_name="Drafts.json")
    write("nested/drafts", record("nested/drafts"), file_name="nested/drafts.json")
    # Control record at its pinned path.
    write(SERVICE, record(SERVICE))
    for service_id in (
        "renamed", "archived", "mismatch", "Drafts", "nested/drafts", SERVICE
    ):
        _select(semantic_runtime, service_id)

    inputs = [_port("q", "input", TEXT)]
    outputs = [_port("count", "output", NUMBER)]

    # A08 rule 1: only `<manifest_location>/<service_id>.json` at the
    # configured revision is read, and only when its `service` field equals
    # `service_id`; A08 rule 5: absent record, then differing `service` field.
    for service_id in ("renamed", "archived", "mismatch"):
        with pytest.raises(Exception) as exc:
            semantic_runtime.propose_binding(service_id, "list_drafts", inputs, outputs)
        assert exc.value.code == "refused", service_id

    # A08 rule 1: lowercase letters, digits and `_` only, refused before a path
    # is built.
    for service_id in ("Drafts", "nested/drafts"):
        with pytest.raises(Exception) as exc:
            semantic_runtime.propose_binding(service_id, "list_drafts", inputs, outputs)
        assert exc.value.code == "refused", service_id

    assert list(_bindings(semantic_runtime)) == []

    # Control: the same record at its pinned path is read and proposed.
    control = semantic_runtime.propose_binding(SERVICE, "list_drafts", inputs, outputs)
    assert _enum(control.status) == "proposed"
    assert control.service_id == SERVICE
    assert [b.binding_id for b in _bindings(semantic_runtime)] == [control.binding_id]


def test_several_http_routes_not_invocable(semantic_runtime):
    """[witness: verification:kernel_a08_several_http_routes_not_invocable]

    A08 Required test 7: a proposal for an operation whose
    `exposed_as.http_api` names two routes, or one route with text before the
    method, is refused naming rule 3.
    """
    stub = semantic_runtime.stub_service()
    capabilities = [
        _capability("two_routes", ["POST /drafts", "PUT /drafts"], "draft-write"),
        _capability("prefixed", ["call POST /drafts"], "draft-write"),
        _capability("create_draft", ["POST /drafts"], "draft-write"),
    ]
    semantic_runtime.manifest.write_record(
        SERVICE, _record(SERVICE, capabilities, stub.base_url)
    )
    _install(semantic_runtime, SERVICE)

    # A08 rule 3: exactly one string of the method, one space and the path,
    # with nothing before or after; several routes are not invocable.
    for operation_name in ("two_routes", "prefixed"):
        with pytest.raises(Exception) as exc:
            semantic_runtime.propose_binding(
                SERVICE, operation_name, DRAFT_INPUTS, DRAFT_OUTPUTS
            )
        assert exc.value.code == "refused", operation_name
    assert list(_bindings(semantic_runtime)) == []

    # Control: one route of the same method and path, same ports, is proposed.
    control = semantic_runtime.propose_binding(
        SERVICE, "create_draft", DRAFT_INPUTS, DRAFT_OUTPUTS
    )
    assert _enum(control.status) == "proposed"
    assert _enum(control.effect_class) == "draft-write"
    assert [b.binding_id for b in _bindings(semantic_runtime)] == [control.binding_id]
