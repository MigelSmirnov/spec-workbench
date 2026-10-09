"""Witness tests for accepted decision A06 (02_rules_flows.md).

Activating a flow version proves it again; a read-only version is activated by
the kernel for anyone who asks, any other only by the owner, and a new version
inherits nothing. Each test carries the witness name its Required test
declares.

The Factory project supplies the ``semantic_runtime`` pytest fixture. It binds
these scenarios to the generated public operations of State 5 — named here by
their operation names, with arguments shaped as the State 6 models — without
changing the assertions below. Each test gets a fresh, empty kernel store.

Fixture surface used here:

- ``issue_contract_version(slot_id, purpose, inputs, outputs)`` ->
  contract_version_id; ports are dicts with the fields of Port (M01); the
  fixture supplies resource bounds within the installation's ceilings and acts
  as an author agent;
- ``compose_flow_version(flow_id, purpose, inputs, outputs, nodes, edges,
  constants)`` -> ComposedFlowVersion, as an author agent; constants are
  RequestConstant dicts;
- ``propose_binding(service_id, operation_name, inputs, outputs)`` ->
  OperationBinding (M11), as an author agent; ``accept_binding(binding_id)``
  -> OperationBinding, as the owner;
- ``activate_flow_version(flow_version_id, actor=...)`` -> FlowActivation
  (M18); the actor is passed wherever the test is about it;
- ``active_flow_version(flow_id)`` -> FlowAnswer (MCP ``get_flow``);
- ``start_run(flow_id, inputs)`` -> ShownRun, inputs RequestJsonValue dicts;
  ``continue_after_approval(approval_id, decision)`` -> ShownRun;
  ``grant_standing_approval(flow_id, node_id)`` -> StandingGrant; all as the
  owner;
- ``page_records(record_type, record_filter, page_size)`` ->
  RecordPageAnswer, as the owner: flow versions, grants, approvals and effect
  attempts.

Capabilities used here (operation nodes need an accepted binding, which needs a
manifest record and a selected instance):

- ``stub_service()`` -> a loopback HTTP stub whose ``base_url`` is the
  instance's ``api_base_url``; ``stub.on(method, path, status, json)`` sets
  its answer and ``stub.requests`` lists what reached it;
- ``manifest.write_record(service_id, record)`` -> the service's record at
  the configured revision, written before the kernel starts;
- ``installation.select_instance(service_id, instance_name)``.
"""

import pytest

TEXT = '{"type":"string"}'

OWNER = {"kind": "owner", "agent_name": None}
AUTHOR = {"kind": "agent", "agent_name": "author"}
HELPER = {"kind": "agent", "agent_name": "helper"}


def _value(field):
    return getattr(field, "value", field)


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


def _function(semantic_runtime, slot_id):
    """A function of one text input `x` and one text output `y`."""
    return semantic_runtime.issue_contract_version(
        slot_id,
        purpose=f"A06 witness: {slot_id}",
        inputs=[_port("x", "input", TEXT, "open")],
        outputs=[_port("y", "output", TEXT)],
    )


def _node(node_id, contract_version_id):
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
    return {
        "from_node": from_node,
        "from_port": from_port,
        "to_node": to_node,
        "to_port": to_port,
        "guard": None,
    }


def _constant(to_node, to_port, json_text):
    return {
        "to_node": to_node,
        "to_port": to_port,
        "value_schema": TEXT,
        "json_text": json_text,
        "disclosure_class": "open",
    }


def _json(port, json_text):
    return {"payload_kind": "json", "port": port, "json_text": json_text}


def _capability(name, route, effect_class):
    return {
        "name": name,
        "exposed_as": {"http_api": [route]},
        "effect_class": effect_class,
        "idempotency_key": None,
    }


def _service(semantic_runtime, service_id, capabilities):
    """The service's manifest record with one selected loopback instance.

    Called before any operation, so it shapes the kernel's first start.
    """
    stub = semantic_runtime.stub_service()
    semantic_runtime.manifest.write_record(
        service_id,
        {
            "service": service_id,
            "capabilities": capabilities,
            "instances": [
                {
                    "instance_name": "local",
                    "api_base_url": stub.base_url,
                    "required_headers": None,
                    "instance_class": "local_dev",
                }
            ],
        },
    )
    semantic_runtime.installation.select_instance(service_id, "local")
    return stub


def _propose(semantic_runtime, service_id, operation_name, inputs, outputs):
    binding = semantic_runtime.propose_binding(
        service_id, operation_name, inputs=inputs, outputs=outputs
    )
    assert _value(binding.status) == "proposed"
    return binding.binding_id


def _accepted(semantic_runtime, service_id, operation_name, inputs, outputs):
    binding_id = _propose(semantic_runtime, service_id, operation_name, inputs, outputs)
    accepted = semantic_runtime.accept_binding(binding_id)
    assert _value(accepted.status) == "accepted"
    return binding_id


def _save_draft(semantic_runtime):
    """An `archive` service whose `save_draft` is `draft-write`, bound and accepted."""
    stub = _service(
        semantic_runtime,
        "archive",
        [_capability("save_draft", "POST /drafts", "draft-write")],
    )
    stub.on("POST", "/drafts", status=200, json={})
    binding_id = _accepted(
        semantic_runtime,
        "archive",
        "save_draft",
        inputs=[_port("material", "input", TEXT, "business_confidential")],
        outputs=[],
    )
    return stub, binding_id


def _read_only_version(semantic_runtime, flow_id, slot_id):
    step_fn = _function(semantic_runtime, slot_id)
    return semantic_runtime.compose_flow_version(
        flow_id,
        purpose=f"A06 witness: {flow_id}",
        inputs=[_port("item", "input", TEXT, "open")],
        outputs=[_port("out", "output", TEXT)],
        nodes=[_node("step", step_fn)],
        edges=[_edge("", "item", "step", "x"), _edge("step", "y", "", "out")],
        constants=[],
    )


def _of(field, value):
    return {"filter_kind": "equals", "field": field, "value": value}


def test_read_only_flow_activated_by_kernel(semantic_runtime):
    """[witness: verification:kernel_a06_read_only_flow_activated_by_kernel]

    A06 Required test 1: a proven read-only flow asked for by an agent is active
    at once and records the kernel as actor.
    """
    composed = _read_only_version(semantic_runtime, "a06_read_only", "tidy_step")
    flow_version_id = composed.flow_version.flow_version_id
    assert composed.proof.proven is True
    assert _value(composed.proof.highest_effect_class) == "read"

    # A06 rule 2: any agent may ask (`helper` has no author right); the
    # activation names the kernel, not the agent that asked.
    activation = semantic_runtime.activate_flow_version(flow_version_id, actor=HELPER)
    assert activation.flow_version_id == flow_version_id
    assert _value(activation.highest_effect_class) == "read"
    assert _value(activation.activated_by.kind) == "kernel"
    assert activation.activated_by.agent_name is None

    # Active at once: the flow's active version is this one, under this
    # activation.
    flow = semantic_runtime.active_flow_version("a06_read_only", actor=HELPER)
    assert flow.active_version.flow_version_id == flow_version_id
    assert flow.activation.store_position == activation.store_position
    assert _value(flow.activation.activated_by.kind) == "kernel"

    # Control: the owner asking for another read-only flow is recorded as the
    # kernel too, so the actor above is the rule, not "whoever is no owner".
    other = _read_only_version(semantic_runtime, "a06_read_only_owner", "tidy_step")
    by_owner = semantic_runtime.activate_flow_version(
        other.flow_version.flow_version_id, actor=OWNER
    )
    assert _value(by_owner.activated_by.kind) == "kernel"


def test_effectful_flow_owner_only_activation(semantic_runtime):
    """[witness: verification:kernel_a06_effectful_flow_owner_only_activation]

    A06 Required test 2: adding one `draft-write` node produces a version an
    agent cannot activate — the refusal keeps nothing for the owner — and the
    owner can.
    """
    _, save = _save_draft(semantic_runtime)
    step_fn = _function(semantic_runtime, "tidy_step")
    flow_id = "a06_effectful"
    purpose = "A06 witness: effectful flow"
    item = [_port("item", "input", TEXT, "open")]
    out = [_port("out", "output", TEXT)]
    base_edges = [_edge("", "item", "step", "x"), _edge("step", "y", "", "out")]

    first = semantic_runtime.compose_flow_version(
        flow_id,
        purpose=purpose,
        inputs=item,
        outputs=out,
        nodes=[_node("step", step_fn)],
        edges=base_edges,
        constants=[],
    )
    first_activation = semantic_runtime.activate_flow_version(
        first.flow_version.flow_version_id, actor=AUTHOR
    )
    assert _value(first_activation.activated_by.kind) == "kernel"

    # The same flow with one `draft-write` node added.
    second = semantic_runtime.compose_flow_version(
        flow_id,
        purpose=purpose,
        inputs=item,
        outputs=out,
        nodes=[_node("step", step_fn), _operation_node("save", save)],
        edges=base_edges + [_edge("", "item", "save", "material")],
        constants=[],
    )
    second_id = second.flow_version.flow_version_id
    assert second.proof.proven is True
    assert _value(second.proof.highest_effect_class) == "draft-write"

    # A06 rule 3: an agent asking is refused, and nothing is kept for the
    # owner: the flow's activation is still the first one.
    with pytest.raises(Exception) as exc:
        semantic_runtime.activate_flow_version(second_id, actor=AUTHOR)
    assert exc.value.code == "refused"
    flow = semantic_runtime.active_flow_version(flow_id)
    assert flow.active_version.flow_version_id == first.flow_version.flow_version_id
    assert flow.activation.store_position == first_activation.store_position

    # The owner can: the activation names the owner (A06 rule 3) and replaces
    # the previous one at once (A06 rule 4).
    activation = semantic_runtime.activate_flow_version(second_id, actor=OWNER)
    assert activation.flow_version_id == second_id
    assert _value(activation.highest_effect_class) == "draft-write"
    assert _value(activation.activated_by.kind) == "owner"
    assert activation.store_position > first_activation.store_position
    flow = semantic_runtime.active_flow_version(flow_id)
    assert flow.active_version.flow_version_id == second_id
    assert flow.activation.store_position == activation.store_position

    # A06 rule 4: an agent asking for a version above `read` is refused even
    # when that version is already active, and that changes nothing.
    with pytest.raises(Exception) as exc:
        semantic_runtime.activate_flow_version(second_id, actor=AUTHOR)
    assert exc.value.code == "refused"
    flow = semantic_runtime.active_flow_version(flow_id)
    assert flow.activation.store_position == activation.store_position


def test_activation_proves_version_again(semantic_runtime):
    """[witness: verification:kernel_a06_activation_proves_version_again]

    A06 Required test 5: activating a version whose proof failed because its
    binding was `proposed` is refused with that proof failure; after the owner
    accepts the binding, the owner activating the same version succeeds with no
    new version.
    """
    stub = _service(
        semantic_runtime,
        "archive",
        [_capability("save_draft", "POST /drafts", "draft-write")],
    )
    stub.on("POST", "/drafts", status=200, json={})
    save = _propose(
        semantic_runtime,
        "archive",
        "save_draft",
        inputs=[_port("material", "input", TEXT, "business_confidential")],
        outputs=[],
    )
    flow_id = "a06_prove_again"
    composed = semantic_runtime.compose_flow_version(
        flow_id,
        purpose="A06 witness: prove again",
        inputs=[_port("material", "input", TEXT, "open")],
        outputs=[],
        nodes=[_operation_node("save", save)],
        edges=[_edge("", "material", "save", "material")],
        constants=[],
    )
    flow_version_id = composed.flow_version.flow_version_id
    assert composed.proof.proven is False
    assert _value(composed.proof.failure.phase) == "nodes"
    assert composed.proof.failure.node_id == "save"

    # A06 rule 1: activation proves the version again; unproven, it is refused
    # and nothing is activated.
    with pytest.raises(Exception) as exc:
        semantic_runtime.activate_flow_version(flow_version_id, actor=OWNER)
    assert exc.value.code == "refused"
    # A06 rule 1: refused with its proof failure, which names the node `save`
    # (A05 rule 1 phase 1), not with some other check.
    assert "save" in exc.value.reason
    flow = semantic_runtime.active_flow_version(flow_id)
    assert flow.active_version is None
    assert flow.activation is None

    semantic_runtime.accept_binding(save)

    activation = semantic_runtime.activate_flow_version(flow_version_id, actor=OWNER)
    assert activation.flow_version_id == flow_version_id
    assert _value(activation.highest_effect_class) == "draft-write"
    assert _value(activation.activated_by.kind) == "owner"
    flow = semantic_runtime.active_flow_version(flow_id)
    assert flow.active_version.flow_version_id == flow_version_id

    # No new version: the flow still has exactly the one version.
    versions = semantic_runtime.page_records(
        "flow_version", _of("flow_id", flow_id), page_size=200
    )
    assert [v.flow_version_id for v in versions.records.flow_versions] == [flow_version_id]


def test_new_version_inherits_nothing(semantic_runtime):
    """[witness: verification:kernel_a06_new_version_inherits_nothing]

    A06 Required test 6: a new version of an owner-activated flow with a
    `state-transition` node, differing only in one constant, is not active,
    and no approval or standing grant of the earlier version applies to it.
    """
    # Besides the `draft-write` node `save`, both versions hold a
    # `state-transition` node `publish`, the kind of node an approval or a
    # grant authorizes (A10 rule 1); a `draft-write` send is authorized by the
    # activation of its version (A10 rule 6).
    stub = _service(
        semantic_runtime,
        "archive",
        [
            _capability("save_draft", "POST /drafts", "draft-write"),
            _capability("publish", "POST /publications", "state-transition"),
        ],
    )
    stub.on("POST", "/drafts", status=200, json={})
    stub.on("POST", "/publications", status=200, json={})
    save = _accepted(
        semantic_runtime,
        "archive",
        "save_draft",
        inputs=[
            _port("material", "input", TEXT, "business_confidential"),
            _port("note", "input", TEXT, "open"),
        ],
        outputs=[],
    )
    publish = _accepted(
        semantic_runtime,
        "archive",
        "publish",
        inputs=[_port("material", "input", TEXT, "business_confidential")],
        outputs=[],
    )
    flow_id = "a06_inherit"

    def compose(note):
        return semantic_runtime.compose_flow_version(
            flow_id,
            purpose="A06 witness: new version inherits nothing",
            inputs=[_port("material", "input", TEXT, "business_confidential")],
            outputs=[],
            nodes=[_operation_node("publish", publish), _operation_node("save", save)],
            edges=[
                _edge("", "material", "publish", "material"),
                _edge("", "material", "save", "material"),
            ],
            constants=[_constant("save", "note", note)],
        )

    def publications():
        return [r for r in stub.requests if r.method == "POST" and r.target == "/publications"]

    def attempts(run_id):
        page = semantic_runtime.page_records(
            "effect_attempt", _of("run_id", run_id), page_size=200
        )
        return {a.node_id: a for a in page.records.effect_attempts}

    first = compose('"first"')
    first_id = first.flow_version.flow_version_id
    first_activation = semantic_runtime.activate_flow_version(first_id, actor=OWNER)
    assert _value(first_activation.activated_by.kind) == "owner"

    # An approval of the first version: a run waits at `publish`, the owner
    # approves, it is sent once.
    approved_run = semantic_runtime.start_run(flow_id, [_json("material", '"m-1"')])
    assert approved_run.flow_version_id == first_id
    assert _value(approved_run.status) == "awaiting_approval"
    [wait] = approved_run.waiting
    assert wait.node_id == "publish"
    assert _value(wait.reason) == "owner_approval"
    first_approval_id = wait.approval_id
    approved_run = semantic_runtime.continue_after_approval(first_approval_id, "approve")
    assert _value(approved_run.status) == "succeeded"
    assert len(publications()) == 1

    # A standing grant of the first version's `publish` node.
    grant = semantic_runtime.grant_standing_approval(flow_id, "publish")
    assert grant.flow_version_id == first_id
    assert _value(grant.status) == "active"

    # Control: under the grant, a run of the first version sends `publish`
    # without asking, and its attempt names the grant.
    granted_run = semantic_runtime.start_run(flow_id, [_json("material", '"m-1"')])
    assert _value(granted_run.status) == "succeeded"
    assert list(granted_run.waiting) == []
    assert len(publications()) == 2
    granted_authority = attempts(granted_run.run_id)["publish"].authority
    assert _value(granted_authority.authority_kind) == "grant"
    assert granted_authority.grant_id == grant.grant_id

    # The new version differs only in the constant on `save.note`.
    second = compose('"second"')
    second_id = second.flow_version.flow_version_id
    assert second_id != first_id
    assert second.proof.proven is True
    assert _value(second.proof.highest_effect_class) == "state-transition"

    # A06 rule 5: it inherits no activation: the first version stays active.
    flow = semantic_runtime.active_flow_version(flow_id)
    assert flow.active_version.flow_version_id == first_id
    assert flow.activation.store_position == first_activation.store_position
    # ... and no grant: none names it.
    grants = semantic_runtime.page_records(
        "grant", _of("flow_version_id", second_id), page_size=200
    )
    assert list(grants.records.grants) == []

    # Once the owner activates it, a run of it inherits neither the grant nor
    # the approval of the first version: `publish` waits for a new approval of
    # its own, and nothing more is sent.
    second_activation = semantic_runtime.activate_flow_version(second_id, actor=OWNER)
    assert second_activation.flow_version_id == second_id
    run = semantic_runtime.start_run(flow_id, [_json("material", '"m-1"')])
    assert run.flow_version_id == second_id
    assert _value(run.status) == "awaiting_approval"
    [wait] = run.waiting
    assert wait.node_id == "publish"
    assert _value(wait.reason) == "owner_approval"
    assert wait.approval_id != first_approval_id
    assert len(publications()) == 2
    approvals = semantic_runtime.page_records(
        "approval", _of("run_id", run.run_id), page_size=200
    )
    [approval] = approvals.records.approvals
    assert approval.approval_id == wait.approval_id
    assert _value(approval.status) == "requested"

    # The grant still names the first version only and is still active.
    grants = semantic_runtime.page_records(
        "grant", _of("flow_version_id", first_id), page_size=200
    )
    [kept] = grants.records.grants
    assert kept.grant_id == grant.grant_id
    assert _value(kept.status) == "active"

    # The `draft-write` send of the new version is authorized by its own
    # activation, not by the first version's (A10 rule 6).
    save_authority = attempts(run.run_id)["save"].authority
    assert _value(save_authority.authority_kind) == "flow_activation"
    assert save_authority.store_position == second_activation.store_position
