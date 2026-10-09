"""Witness tests for accepted decision A10 (02_rules_services.md).

An effect of class `state-transition`, `external-effect` or `destructive` is
sent only on the exact request the owner approved, or under the owner's
standing grant for that node of that flow version; only the owner decides,
grants and revokes, and the absence of a decision changes nothing. Each test
carries the witness name its Required test declares.

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
  ``cancel_run(run_id)``, ``continue_after_approval(approval_id, decision)``,
  ``continue_after_resolution(attempt, resolution)``, ``read_run(run_id)`` ->
  ShownRun; inputs are RequestJsonValue dicts, ``attempt`` an AttemptKey dict;
- ``grant_standing_approval(flow_id, node_id)``,
  ``revoke_standing_approval(grant_id)`` -> StandingGrant (M25);
- ``page_records(record_type, record_filter, page_size)`` -> RecordPageAnswer;
  approvals, effect attempts, node executions and grants are read from its
  ``records`` (newest first);
- every call takes ``actor=`` (an Actor M27 dict); omitted, it is the owner
  for owner operations and agent ``author`` for authoring operations.

Capabilities used here: ``stub_service()`` (a loopback HTTP service whose
received requests are listed in ``stub.requests``), ``manifest.write_record``,
``manifest.new_revision``, ``installation.select_instance``,
``installation.set_credential``, ``installation.write_secret``,
``installation.set_manifest_revision``, ``restart()`` and ``clock.advance``.
"""

import json

import pytest

OWNER = {"kind": "owner", "agent_name": None}
AUTHOR = {"kind": "agent", "agent_name": "author"}
HELPER = {"kind": "agent", "agent_name": "helper"}

TEXT = '{"type":"string"}'

SERVICE = "drafts"
INSTANCE = "local"
CREDENTIAL_HEADER = "X-Api-Key"
CREDENTIAL = "a10-credential-value-0001"


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


def _capability(name, route, effect_class):
    return {
        "name": name,
        "exposed_as": {"http_api": [route]},
        "effect_class": effect_class,
        "idempotency_key": None,
    }


def _record(stub, capabilities, required_headers=None):
    return {
        "service": SERVICE,
        "capabilities": capabilities,
        "instances": [
            {
                "instance_name": INSTANCE,
                "api_base_url": stub.base_url,
                "required_headers": required_headers,
                "instance_class": "local_dev",
            }
        ],
    }


def _install_service(semantic_runtime, stub, capabilities, required_headers=None):
    """Manifest record, selected instance and credential, before the first call."""
    semantic_runtime.manifest.write_record(
        SERVICE, _record(stub, capabilities, required_headers)
    )
    semantic_runtime.installation.select_instance(SERVICE, INSTANCE)
    semantic_runtime.installation.set_credential(
        SERVICE, CREDENTIAL_HEADER, CREDENTIAL
    )


def _binding(semantic_runtime, operation_name, input_port):
    """An accepted binding with one `value` input and no output ports."""
    proposed = semantic_runtime.propose_binding(
        SERVICE,
        operation_name,
        inputs=[_port(input_port, "input", TEXT, "open")],
        outputs=[],
    )
    return semantic_runtime.accept_binding(proposed.binding_id).binding_id


def _op_node(node_id, binding_id, map_over=None):
    return {
        "node_id": node_id,
        "kind": "operation",
        "contract_version_id": None,
        "binding_id": binding_id,
        "map_over": map_over,
    }


def _edge(from_node, from_port, to_node, to_port):
    return {
        "from_node": from_node,
        "from_port": from_port,
        "to_node": to_node,
        "to_port": to_port,
        "guard": None,
    }


def _compose(semantic_runtime, flow_id, inputs, nodes, edges, constants=()):
    composed = semantic_runtime.compose_flow_version(
        flow_id,
        purpose=f"A10 witness: {flow_id}",
        inputs=list(inputs),
        outputs=[],
        nodes=list(nodes),
        edges=list(edges),
        constants=list(constants),
    )
    assert composed.proof.proven is True
    return composed.flow_version.flow_version_id


def _send_flow(semantic_runtime, flow_id, binding_id, node_id="send", activate=True):
    """Flow input `title` -> operation node `node_id`; activated by the owner."""
    flow_version_id = _compose(
        semantic_runtime,
        flow_id,
        inputs=[_port("title", "input", TEXT, "open")],
        nodes=[_op_node(node_id, binding_id)],
        edges=[_edge("", "title", node_id, "title")],
    )
    if activate:
        semantic_runtime.activate_flow_version(flow_version_id)
    return flow_version_id


def _title(text):
    return [{"payload_kind": "json", "port": "title", "json_text": json.dumps(text)}]


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


def _executions(semantic_runtime, run_id):
    """The run's trace in store order."""
    page = semantic_runtime.page_records(
        "node_execution", _by_run(run_id), page_size=200
    )
    return list(reversed(page.records.node_executions))


def _grants(semantic_runtime, flow_version_id):
    page = semantic_runtime.page_records(
        "grant",
        {"filter_kind": "equals", "field": "flow_version_id", "value": flow_version_id},
        page_size=200,
    )
    return list(reversed(page.records.grants))


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


def _wire_header(request, name):
    return [value for header, value in request.headers if header.lower() == name]


def _described_headers(approval):
    return {h.name: h.value for h in approval.preview.request.headers}


def test_gated_send_waits_for_approval(semantic_runtime):
    """[witness: verification:kernel_a10_gated_send_waits_for_approval]

    A10 Required test 1: a run reaching a `state-transition` node sends
    nothing until the owner approves, and sends once after.
    """
    stub = semantic_runtime.stub_service()
    stub.on("POST", "/items", status=200, json={})
    _install_service(
        semantic_runtime,
        stub,
        [_capability("publish", "POST /items", "state-transition")],
    )
    binding_id = _binding(semantic_runtime, "publish", "title")
    _send_flow(semantic_runtime, "a10_gated", binding_id)

    run = semantic_runtime.start_run("a10_gated", _title("Quarterly report"))

    # A10 rule 2: without approval or grant, one approval request and the
    # element waits with reason `owner_approval`; nothing is sent.
    assert _v(run.status) == "awaiting_approval"
    approvals = _approvals(semantic_runtime, run.run_id)
    assert len(approvals) == 1
    approval = approvals[0]
    assert _v(approval.status) == "requested"
    assert (approval.node_id, approval.map_index) == ("send", None)
    assert _waits(run) == [("send", None, "owner_approval", approval.approval_id)]
    assert stub.requests == []
    # A11 rule 1: waiting for approval writes no NodeExecution and no attempt.
    assert _executions(semantic_runtime, run.run_id) == []
    assert _attempts(semantic_runtime, run.run_id) == []
    # A10 rule 7: the preview describes the request about to be sent.
    preview = approval.preview
    assert _v(preview.effect_class) == "state-transition"
    assert _v(preview.request.method) == "POST"
    assert preview.request.url == stub.base_url + "/items"
    assert preview.request.body.json_text == '{"title":"Quarterly report"}'

    after = semantic_runtime.continue_after_approval(approval.approval_id, "approve")

    # A10 rule 3: approving sends the effect at once, in the owner's request.
    assert len(stub.requests) == 1
    sent = stub.requests[0]
    assert sent.method == "POST"
    assert sent.target == "/items"
    assert sent.body == b'{"title":"Quarterly report"}'
    assert _v(after.status) == "succeeded"
    attempts = _attempts(semantic_runtime, run.run_id)
    assert len(attempts) == 1
    assert _v(attempts[0].status) == "applied"
    # A10 rule 6 / A11 rule 1: the attempt names the approval it used.
    assert _authority(attempts[0]) == ("approval", approval.approval_id)
    decided = _approvals(semantic_runtime, run.run_id)[0]
    assert _v(decided.status) == "used"
    assert _v(decided.decided_by.kind) == "owner"

    # The run is over: nothing is sent again.
    semantic_runtime.read_run(run.run_id)
    assert len(stub.requests) == 1


def test_approval_scoped_per_element(semantic_runtime):
    """[witness: verification:kernel_a10_approval_scoped_per_element]

    A10 Required test 2: a mapped node over three photos asks three
    approvals.
    """
    stub = semantic_runtime.stub_service()
    stub.on("POST", "/photos", status=200, json={})
    _install_service(
        semantic_runtime,
        stub,
        [_capability("publish_photo", "POST /photos", "state-transition")],
    )
    binding_id = _binding(semantic_runtime, "publish_photo", "photo")
    # The three photos are named by the flow input list; the node maps over it,
    # one element per photo (M14).
    flow_version_id = _compose(
        semantic_runtime,
        "a10_photos",
        inputs=[_port("photos", "input", TEXT, "open", cardinality="many")],
        nodes=[_op_node("send", binding_id, map_over="photo")],
        edges=[_edge("", "photos", "send", "photo")],
    )
    semantic_runtime.activate_flow_version(flow_version_id)

    photos = ["IMG_0001.jpg", "IMG_0002.jpg", "IMG_0003.jpg"]
    run = semantic_runtime.start_run(
        "a10_photos",
        [{"payload_kind": "json", "port": "photos", "json_text": json.dumps(photos)}],
    )

    # A10 rule 2: for a mapped node each element is one approval.
    assert _v(run.status) == "awaiting_approval"
    approvals = _approvals(semantic_runtime, run.run_id)
    assert len(approvals) == 3
    assert sorted(a.map_index for a in approvals) == [0, 1, 2]
    assert all(a.node_id == "send" for a in approvals)
    assert all(_v(a.status) == "requested" for a in approvals)
    assert len({a.approval_id for a in approvals}) == 3
    assert len({a.request_digest for a in approvals}) == 3
    by_index = {a.map_index: a for a in approvals}
    assert _waits(run) == [
        ("send", i, "owner_approval", by_index[i].approval_id) for i in (0, 1, 2)
    ]
    assert stub.requests == []

    # Control: approving one element sends that element only; the other two
    # keep waiting on their own approvals.
    after = semantic_runtime.continue_after_approval(by_index[1].approval_id, "approve")
    assert len(stub.requests) == 1
    assert stub.requests[0].body == b'{"photo":"IMG_0002.jpg"}'
    assert _v(after.status) == "awaiting_approval"
    assert _waits(after) == [
        ("send", 0, "owner_approval", by_index[0].approval_id),
        ("send", 2, "owner_approval", by_index[2].approval_id),
    ]
    statuses = {
        a.map_index: _v(a.status) for a in _approvals(semantic_runtime, run.run_id)
    }
    assert statuses == {0: "requested", 1: "used", 2: "requested"}
    attempts = _attempts(semantic_runtime, run.run_id)
    assert [(a.map_index, _authority(a)) for a in attempts] == [
        (1, ("approval", by_index[1].approval_id))
    ]


def test_grant_authorizes_never_destructive(semantic_runtime):
    """[witness: verification:kernel_a10_grant_authorizes_never_destructive]

    A10 Required test 4: with a grant, the node is sent without asking and the
    attempt names the grant; a `destructive` node cannot be granted.
    """
    stub = semantic_runtime.stub_service()
    stub.on("POST", "/items", status=200, json={})
    stub.on("POST", "/purge", status=200, json={})
    _install_service(
        semantic_runtime,
        stub,
        [
            _capability("publish", "POST /items", "state-transition"),
            _capability("purge", "POST /purge", "destructive"),
        ],
    )
    publish = _binding(semantic_runtime, "publish", "title")
    purge = _binding(semantic_runtime, "purge", "title")
    publish_version = _send_flow(semantic_runtime, "a10_granted", publish)
    purge_version = _send_flow(semantic_runtime, "a10_destructive", purge)

    # Control: before the grant, a run of the same version asks.
    before = semantic_runtime.start_run("a10_granted", _title("before grant"))
    assert _v(before.status) == "awaiting_approval"
    assert stub.requests == []

    grant = semantic_runtime.grant_standing_approval("a10_granted", "send")
    assert _v(grant.status) == "active"
    assert grant.flow_version_id == publish_version
    assert grant.node_id == "send"
    assert _v(grant.granted_by.kind) == "owner"

    run = semantic_runtime.start_run("a10_granted", _title("under grant"))

    # A10 rule 1: an active grant for the node of the run's version authorizes
    # the send; no approval is asked.
    assert _v(run.status) == "succeeded"
    assert _approvals(semantic_runtime, run.run_id) == []
    assert len(stub.requests) == 1
    assert stub.requests[0].body == b'{"title":"under grant"}'
    attempts = _attempts(semantic_runtime, run.run_id)
    assert len(attempts) == 1
    # A10 rule 6: the send records the grant as its authority.
    assert _authority(attempts[0]) == ("grant", grant.grant_id)
    assert _v(attempts[0].status) == "applied"

    # A10 rule 5: a grant is given only for a node that is not `destructive`.
    with pytest.raises(Exception) as exc:
        semantic_runtime.grant_standing_approval("a10_destructive", "send")
    assert exc.value.code == "refused"
    assert _grants(semantic_runtime, purge_version) == []

    # The destructive node keeps asking for every send.
    purge_run = semantic_runtime.start_run("a10_destructive", _title("purge"))
    assert _v(purge_run.status) == "awaiting_approval"
    assert [w[2] for w in _waits(purge_run)] == ["owner_approval"]
    assert len(stub.requests) == 1


def test_revoked_grant_no_longer_authorizes(semantic_runtime):
    """[witness: verification:kernel_a10_revoked_grant_no_longer_authorizes]

    A10 Required test 5: after revocation, the next run of that version asks
    again.
    """
    stub = semantic_runtime.stub_service()
    stub.on("POST", "/items", status=200, json={})
    _install_service(
        semantic_runtime,
        stub,
        [_capability("publish", "POST /items", "state-transition")],
    )
    binding_id = _binding(semantic_runtime, "publish", "title")
    flow_version_id = _send_flow(semantic_runtime, "a10_revoke", binding_id)
    grant = semantic_runtime.grant_standing_approval("a10_revoke", "send")

    # Control: while the grant is active the node is sent without asking.
    first = semantic_runtime.start_run("a10_revoke", _title("first"))
    assert _v(first.status) == "succeeded"
    assert len(stub.requests) == 1
    assert _authority(_attempts(semantic_runtime, first.run_id)[0]) == (
        "grant",
        grant.grant_id,
    )

    revoked = semantic_runtime.revoke_standing_approval(grant.grant_id)
    assert _v(revoked.status) == "revoked"
    assert _v(revoked.revoked_by.kind) == "owner"
    assert [_v(g.status) for g in _grants(semantic_runtime, flow_version_id)] == [
        "revoked"
    ]

    # A10 rule 5: revoking takes effect for every send after it.
    second = semantic_runtime.start_run("a10_revoke", _title("second"))
    assert _v(second.status) == "awaiting_approval"
    approvals = _approvals(semantic_runtime, second.run_id)
    assert len(approvals) == 1
    assert _waits(second) == [("send", None, "owner_approval", approvals[0].approval_id)]
    assert _attempts(semantic_runtime, second.run_id) == []
    assert len(stub.requests) == 1


def test_only_owner_decides_grants_revokes(semantic_runtime):
    """[witness: verification:kernel_a10_only_owner_decides_grants_revokes]

    A10 Required test 6: an agent's approval, grant or revocation is refused.
    """
    stub = semantic_runtime.stub_service()
    stub.on("POST", "/items", status=200, json={})
    _install_service(
        semantic_runtime,
        stub,
        [_capability("publish", "POST /items", "state-transition")],
    )
    binding_id = _binding(semantic_runtime, "publish", "title")
    flow_version_id = _send_flow(semantic_runtime, "a10_owner_only", binding_id)
    run = semantic_runtime.start_run("a10_owner_only", _title("owner only"), actor=OWNER)
    approval_id = _approvals(semantic_runtime, run.run_id)[0].approval_id

    for agent in (AUTHOR, HELPER):
        # A10 rule 3: only the owner decides (State 5: `not_permitted`).
        for decision in ("approve", "refuse"):
            with pytest.raises(Exception) as exc:
                semantic_runtime.continue_after_approval(
                    approval_id, decision, actor=agent
                )
            assert exc.value.code == "not_permitted"
        # A10 rule 5: only the owner grants.
        with pytest.raises(Exception) as exc:
            semantic_runtime.grant_standing_approval(
                "a10_owner_only", "send", actor=agent
            )
        assert exc.value.code == "not_permitted"

    # Nothing was decided, granted or sent.
    approvals = _approvals(semantic_runtime, run.run_id)
    assert [(a.approval_id, _v(a.status), a.decided_by) for a in approvals] == [
        (approval_id, "requested", None)
    ]
    assert _grants(semantic_runtime, flow_version_id) == []
    assert stub.requests == []
    assert _v(semantic_runtime.read_run(run.run_id).status) == "awaiting_approval"

    # Control: the owner may grant; an agent then may not revoke it.
    grant = semantic_runtime.grant_standing_approval("a10_owner_only", "send", actor=OWNER)
    for agent in (AUTHOR, HELPER):
        with pytest.raises(Exception) as exc:
            semantic_runtime.revoke_standing_approval(grant.grant_id, actor=agent)
        assert exc.value.code == "not_permitted"
    assert [
        (g.grant_id, _v(g.status)) for g in _grants(semantic_runtime, flow_version_id)
    ] == [(grant.grant_id, "active")]

    # Control: the owner's decision and revocation are accepted.
    after = semantic_runtime.continue_after_approval(approval_id, "approve", actor=OWNER)
    assert _v(after.status) == "succeeded"
    assert len(stub.requests) == 1
    revoked = semantic_runtime.revoke_standing_approval(grant.grant_id, actor=OWNER)
    assert _v(revoked.status) == "revoked"


def test_approval_bound_to_request_digest(semantic_runtime):
    """[witness: verification:kernel_a10_approval_bound_to_request_digest]

    A10 Required test 7: after a restart that changed a required header's
    value of the instance, an approval given before it on the same inputs
    does not cover the send: nothing is sent and the element asks again. A
    restart that only rotated the credential's value sends under the approval.
    """
    stub = semantic_runtime.stub_service()
    stub.on("POST", "/items", status=200, json={})
    capabilities = [_capability("publish", "POST /items", "state-transition")]
    _install_service(
        semantic_runtime,
        stub,
        capabilities,
        required_headers=[{"name": "X-Tenant", "value": "alpha"}],
    )
    binding_id = _binding(semantic_runtime, "publish", "title")
    _send_flow(semantic_runtime, "a10_digest", binding_id)

    # An approval given, its send not sent (connection refused): A10 rule 3
    # leaves it `approved` and unused, and the element waits on
    # `service_unreachable` for a resume.
    stub.set_down(True)
    run = semantic_runtime.start_run("a10_digest", _title("same inputs"))
    old = _approvals(semantic_runtime, run.run_id)[0]
    assert _described_headers(old)["x-tenant"] == "alpha"
    rested = semantic_runtime.continue_after_approval(old.approval_id, "approve")
    assert _waits(rested) == [("send", None, "service_unreachable", None)]
    assert _v(_approvals(semantic_runtime, run.run_id)[0].status) == "approved"
    assert [_v(a.status) for a in _attempts(semantic_runtime, run.run_id)] == [
        "not_sent"
    ]
    assert stub.requests == []

    # The instance's required header changes value; the capability entry, and
    # so the binding's digest, does not (A08 rule 2).
    revision = semantic_runtime.manifest.new_revision()
    semantic_runtime.manifest.write_record(
        SERVICE,
        _record(stub, capabilities, [{"name": "X-Tenant", "value": "beta"}]),
        revision=revision,
    )
    semantic_runtime.installation.set_manifest_revision(revision)
    assert semantic_runtime.restart().started is True
    stub.set_down(False)

    resumed = semantic_runtime.resume_run(run.run_id)

    # A10 rule 1: the request about to be sent differs in a required header's
    # value, so the approval is no authority for it; no grant applies, so the
    # element asks anew (rule 2) and nothing is sent, although the service is up.
    assert stub.requests == []
    approvals = _approvals(semantic_runtime, run.run_id)
    assert len(approvals) == 2
    first, fresh = approvals
    assert first.approval_id == old.approval_id
    assert _v(first.status) == "approved"  # stays approved and unused
    assert _v(fresh.status) == "requested"
    assert fresh.request_digest != old.request_digest
    assert _described_headers(fresh)["x-tenant"] == "beta"
    assert _v(resumed.status) == "awaiting_approval"
    assert _waits(resumed) == [("send", None, "owner_approval", fresh.approval_id)]
    assert [_v(a.status) for a in _attempts(semantic_runtime, run.run_id)] == [
        "not_sent"
    ]

    # Second scenario: only the credential's value changes between the
    # approval and the send.
    stub.set_down(True)
    other = semantic_runtime.start_run("a10_digest", _title("same inputs"))
    approval = _approvals(semantic_runtime, other.run_id)[0]
    # A10 rule 7: the credential header is described by name only.
    assert _described_headers(approval)[CREDENTIAL_HEADER.lower()] is None
    semantic_runtime.continue_after_approval(approval.approval_id, "approve")
    assert _v(_approvals(semantic_runtime, other.run_id)[0].status) == "approved"

    rotated = "a10-credential-value-0002"
    semantic_runtime.installation.write_secret(SERVICE, rotated)
    assert semantic_runtime.restart().started is True
    stub.set_down(False)

    done = semantic_runtime.resume_run(other.run_id)

    # A10 rule 7: rotating the credential voids no approval; the send goes
    # under the approval given before the restart, without asking again.
    assert len(stub.requests) == 1
    assert _wire_header(stub.requests[0], CREDENTIAL_HEADER.lower()) == [rotated]
    assert _wire_header(stub.requests[0], "x-tenant") == ["beta"]
    assert _v(done.status) == "succeeded"
    approvals = _approvals(semantic_runtime, other.run_id)
    assert [(a.approval_id, _v(a.status)) for a in approvals] == [
        (approval.approval_id, "used")
    ]
    attempts = _attempts(semantic_runtime, other.run_id)
    assert [_v(a.status) for a in attempts] == ["not_sent", "applied"]
    assert _authority(attempts[1]) == ("approval", approval.approval_id)


def test_used_approval_and_grant_do_not_cover_resend(semantic_runtime):
    """[witness: verification:kernel_a10_used_approval_and_grant_do_not_cover_resend]

    A10 Required test 9: after an approved send whose attempt the owner
    resolves `not_applied`, neither the used approval nor an active grant for
    the node covers the resend: the element waits with reason
    `owner_approval`, nothing is sent until a fresh approval is decided, and
    the resend records that fresh approval.
    """
    stub = semantic_runtime.stub_service()
    stub.on("POST", "/items", action="drop_after_request")
    _install_service(
        semantic_runtime,
        stub,
        [_capability("publish", "POST /items", "state-transition")],
    )
    binding_id = _binding(semantic_runtime, "publish", "title")
    flow_version_id = _send_flow(semantic_runtime, "a10_resend", binding_id)

    run = semantic_runtime.start_run("a10_resend", _title("resend"))
    used = _approvals(semantic_runtime, run.run_id)[0]
    unknown = semantic_runtime.continue_after_approval(used.approval_id, "approve")
    assert len(stub.requests) == 1
    assert _waits(unknown) == [("send", None, "outcome_unknown", None)]
    assert _v(_approvals(semantic_runtime, run.run_id)[0].status) == "used"

    # The owner now grants the node of the run's version, and the service
    # would answer a resend.
    grant = semantic_runtime.grant_standing_approval("a10_resend", "send")
    assert grant.flow_version_id == flow_version_id
    stub.on("POST", "/items", status=200, json={})

    waiting = semantic_runtime.continue_after_resolution(
        {"run_id": run.run_id, "node_id": "send", "map_index": None, "attempt_number": 1},
        "not_applied",
    )

    # A10 rule 1: a resend after `not_applied` needs a fresh approval; neither
    # the used approval nor the active grant covers it.
    assert len(stub.requests) == 1
    approvals = _approvals(semantic_runtime, run.run_id)
    assert len(approvals) == 2
    fresh = approvals[1]
    assert _v(fresh.status) == "requested"
    # A10 rule 1: a fresh approval is a new one, requested after the
    # resolution; the used one stays `used`. The request is unchanged, so the
    # used approval matches its digest and still is no authority for it.
    # (ShownApproval carries no `attempt_number`, State 6.)
    assert fresh.approval_id != used.approval_id
    assert fresh.request_digest == used.request_digest
    assert _v(approvals[0].status) == "used"
    assert _v(waiting.status) == "awaiting_approval"
    assert _waits(waiting) == [("send", None, "owner_approval", fresh.approval_id)]
    assert [_v(a.status) for a in _attempts(semantic_runtime, run.run_id)] == [
        "not_applied"
    ]

    done = semantic_runtime.continue_after_approval(fresh.approval_id, "approve")

    assert len(stub.requests) == 2
    assert _v(done.status) == "succeeded"
    attempts = _attempts(semantic_runtime, run.run_id)
    assert [_v(a.status) for a in attempts] == ["not_applied", "applied"]
    # A10 rule 6: the resend records its fresh approval.
    assert _authority(attempts[1]) == ("approval", fresh.approval_id)
    assert _v(_approvals(semantic_runtime, run.run_id)[1].status) == "used"

    # Control: the grant itself is active and covers an ordinary send.
    other = semantic_runtime.start_run("a10_resend", _title("ordinary"))
    assert _v(other.status) == "succeeded"
    assert len(stub.requests) == 3
    assert _authority(_attempts(semantic_runtime, other.run_id)[0]) == (
        "grant",
        grant.grant_id,
    )


def test_no_decision_changes_nothing(semantic_runtime):
    """[witness: verification:kernel_a10_no_decision_changes_nothing]

    A10 Required test 10: an approval left undecided while the clock advances
    by days stays `requested`: nothing approves, refuses or ends it, the
    element keeps waiting and the run does not end. Once the run is cancelled,
    deciding that approval is refused and its status stays `requested`.
    """
    stub = semantic_runtime.stub_service()
    stub.on("POST", "/items", status=200, json={})
    _install_service(
        semantic_runtime,
        stub,
        [_capability("publish", "POST /items", "state-transition")],
    )
    binding_id = _binding(semantic_runtime, "publish", "title")
    _send_flow(semantic_runtime, "a10_undecided", binding_id)

    run = semantic_runtime.start_run("a10_undecided", _title("undecided"))
    approval = _approvals(semantic_runtime, run.run_id)[0]
    assert _v(approval.status) == "requested"
    # Control: a second run of the same version, left waiting just as long.
    control = semantic_runtime.start_run("a10_undecided", _title("decided late"))
    control_approval = _approvals(semantic_runtime, control.run_id)[0]
    assert _v(control_approval.status) == "requested"

    semantic_runtime.clock.advance(days=30)

    # A10 rule 4: no time limit approves, refuses or ends anything.
    later = semantic_runtime.read_run(run.run_id)
    assert _v(later.status) == "awaiting_approval"
    assert later.ended_at is None
    assert _waits(later) == [("send", None, "owner_approval", approval.approval_id)]
    assert _waits(later) == _waits(run)
    still = _approvals(semantic_runtime, run.run_id)
    assert [(a.approval_id, _v(a.status), a.decided_by, a.decided_at) for a in still] == [
        (approval.approval_id, "requested", None, None)
    ]
    assert _executions(semantic_runtime, run.run_id) == []
    assert _attempts(semantic_runtime, run.run_id) == []
    assert stub.requests == []

    # Control: an approval waiting the same days is still the owner's to
    # decide — no time limit refuses the decision either — so the refusal
    # below comes from the ended run, not from the elapsed time.
    decided = semantic_runtime.continue_after_approval(
        control_approval.approval_id, "approve"
    )
    assert _v(decided.status) == "succeeded"
    assert len(stub.requests) == 1
    assert stub.requests[0].body == b'{"title":"decided late"}'

    cancelled = semantic_runtime.cancel_run(run.run_id)
    assert _v(cancelled.status) == "cancelled"

    # A10 rule 3: only an approval in a run that has not ended is decided.
    for decision in ("approve", "refuse"):
        with pytest.raises(Exception) as exc:
            semantic_runtime.continue_after_approval(approval.approval_id, decision)
        assert exc.value.code == "refused"

    # A10 rule 4: its status stays as it was; the ended run makes it void.
    after = _approvals(semantic_runtime, run.run_id)
    assert [(a.approval_id, _v(a.status), a.decided_by) for a in after] == [
        (approval.approval_id, "requested", None)
    ]
    assert _v(semantic_runtime.read_run(run.run_id).status) == "cancelled"
    assert _executions(semantic_runtime, run.run_id) == []
    assert _attempts(semantic_runtime, run.run_id) == []
    assert len(stub.requests) == 1


def test_grant_bound_to_flow_version(semantic_runtime):
    """[witness: verification:kernel_a10_grant_bound_to_flow_version]

    A10 Required test 11: a grant for a node of one flow version does not
    cover the same node in a run of another version: that run asks for
    approval. A grant request for a node of a version that is not active is
    refused.
    """
    stub = semantic_runtime.stub_service()
    stub.on("POST", "/items", status=200, json={})
    _install_service(
        semantic_runtime,
        stub,
        [_capability("publish", "POST /items", "state-transition")],
    )
    binding_id = _binding(semantic_runtime, "publish", "title")
    first_version = _send_flow(
        semantic_runtime, "a10_versions", binding_id, activate=False
    )

    # A10 rule 5: a version that is not active takes no grant — here the flow
    # has no active version at all.
    with pytest.raises(Exception) as exc:
        semantic_runtime.grant_standing_approval("a10_versions", "send")
    assert exc.value.code == "refused"
    assert _grants(semantic_runtime, first_version) == []

    semantic_runtime.activate_flow_version(first_version)
    grant = semantic_runtime.grant_standing_approval("a10_versions", "send")
    assert grant.flow_version_id == first_version

    # A second version: the same node `send`, its input from a constant.
    second_version = _compose(
        semantic_runtime,
        "a10_versions",
        inputs=[],
        nodes=[_op_node("send", binding_id)],
        edges=[],
        constants=[
            {
                "to_node": "send",
                "to_port": "title",
                "value_schema": TEXT,
                "json_text": '"fixed title"',
                "disclosure_class": "open",
            }
        ],
    )
    assert second_version != first_version
    semantic_runtime.activate_flow_version(second_version)

    run = semantic_runtime.start_run("a10_versions", [])

    # A10 rule 1: the grant is for the node of the first version; the run's
    # pinned version is the second, so the node asks for approval.
    assert run.flow_version_id == second_version
    assert _v(run.status) == "awaiting_approval"
    approvals = _approvals(semantic_runtime, run.run_id)
    assert len(approvals) == 1
    assert _waits(run) == [("send", None, "owner_approval", approvals[0].approval_id)]
    assert stub.requests == []
    # The earlier grant is still active; it simply does not apply.
    assert [(g.grant_id, _v(g.status)) for g in _grants(semantic_runtime, first_version)] == [
        (grant.grant_id, "active")
    ]

    # A10 rule 5: a node of a version that is not active is refused — a third
    # version, composed but not activated, whose node exists only there.
    _compose(
        semantic_runtime,
        "a10_versions",
        inputs=[],
        nodes=[_op_node("archive", binding_id)],
        edges=[],
        constants=[
            {
                "to_node": "archive",
                "to_port": "title",
                "value_schema": TEXT,
                "json_text": '"fixed title"',
                "disclosure_class": "open",
            }
        ],
    )
    with pytest.raises(Exception) as exc:
        semantic_runtime.grant_standing_approval("a10_versions", "archive")
    assert exc.value.code == "refused"
    assert _grants(semantic_runtime, second_version) == []

    # Control: a grant for the node of the active version covers its next run.
    current = semantic_runtime.grant_standing_approval("a10_versions", "send")
    assert current.flow_version_id == second_version
    assert current.grant_id != grant.grant_id
    covered = semantic_runtime.start_run("a10_versions", [])
    assert _v(covered.status) == "succeeded"
    assert len(stub.requests) == 1
    assert _authority(_attempts(semantic_runtime, covered.run_id)[0]) == (
        "grant",
        current.grant_id,
    )
