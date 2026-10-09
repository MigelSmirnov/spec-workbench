"""Witness tests for accepted decision A05 (02_rules_flows.md).

A proof checks one flow version in a fixed order of phases and reports the
first failure. Each test carries the witness name its Required test declares.

The Factory project supplies the ``semantic_runtime`` pytest fixture. It binds
these scenarios to the generated public operations of State 5 — named here by
their operation names, with arguments shaped as the State 6 models — without
changing the assertions below. Each test gets a fresh, empty kernel store.

Fixture surface used here:

- ``issue_contract_version(slot_id, purpose, inputs, outputs)`` ->
  contract_version_id; ports are dicts with the fields of Port (M01); the
  fixture supplies resource bounds within the installation's ceilings (A02
  rule 2 refuses omitted ones; A05 does not depend on them) and acts as an
  author agent;
- ``compose_flow_version(flow_id, purpose, inputs, outputs, nodes, edges,
  constants)`` -> ComposedFlowVersion (fields of the State 6 model);
- ``prove_flow_version(flow_version_id)`` -> ProofResult (M17);
- ``propose_binding(service_id, operation_name, inputs, outputs)`` ->
  OperationBinding (M11), as an author agent; ``accept_binding(binding_id)``
  -> OperationBinding, as the owner;
- ``page_records(record_type, record_filter)`` -> RecordPageAnswer, as the
  owner; here only to count the versions of one flow.

Capabilities used here (operation nodes need an accepted binding, which needs a
manifest record and a selected instance):

- ``stub_service()`` -> a loopback HTTP stub whose ``base_url`` is the
  instance's ``api_base_url``; the proof sends nothing, so no route is set;
- ``manifest.write_record(service_id, record)`` -> the service's record at
  the configured revision, written before the kernel starts;
- ``installation.select_instance(service_id, instance_name)``.
"""

TEXT = '{"type":"string"}'
NUMBER = '{"type":"integer"}'
VERDICT = '{"enum":["new","duplicate"]}'


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


def _function(semantic_runtime, slot_id, schema):
    """A function of one input `x` and one output `y`, both of `schema`."""
    return semantic_runtime.issue_contract_version(
        slot_id,
        purpose=f"A05 witness: {slot_id}",
        inputs=[_port("x", "input", schema, "open")],
        outputs=[_port("y", "output", schema)],
    )


def _node(node_id, contract_version_id):
    return {
        "node_id": node_id,
        "kind": "function",
        "contract_version_id": contract_version_id,
        "binding_id": None,
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


def _phase(failure):
    phase = failure.phase
    return getattr(phase, "value", phase)


def _edge_key(failure):
    edge = failure.edge
    return (edge.from_node, edge.from_port, edge.to_node, edge.to_port)


def _value(field):
    return getattr(field, "value", field)


def _list_port(name, direction, schema, disclosure_class=None):
    """A `many` port; its schema is the schema of each element (A13 rule 3)."""
    port = _port(name, direction, schema, disclosure_class)
    port["cardinality"] = "many"
    return port


def _contract(semantic_runtime, slot_id, inputs, outputs):
    return semantic_runtime.issue_contract_version(
        slot_id,
        purpose=f"A05 witness: {slot_id}",
        inputs=inputs,
        outputs=outputs,
    )


def _operation_node(node_id, binding_id):
    return {
        "node_id": node_id,
        "kind": "operation",
        "contract_version_id": None,
        "binding_id": binding_id,
        "map_over": None,
    }


def _guarded(from_node, from_port, to_node, to_port, guard_port, guard_value):
    edge = _edge(from_node, from_port, to_node, to_port)
    edge["guard"] = {"guard_port": guard_port, "guard_value": guard_value}
    return edge


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


def _proposed(semantic_runtime, service_id, operation_name, inputs, outputs):
    binding = semantic_runtime.propose_binding(
        service_id, operation_name, inputs=inputs, outputs=outputs
    )
    assert _value(binding.status) == "proposed"
    return binding.binding_id


def _accepted(semantic_runtime, service_id, operation_name, inputs, outputs):
    binding_id = _proposed(semantic_runtime, service_id, operation_name, inputs, outputs)
    accepted = semantic_runtime.accept_binding(binding_id)
    assert _value(accepted.status) == "accepted"
    return binding_id


def test_first_failure_by_phase_order(semantic_runtime):
    """[witness: verification:kernel_a05_first_failure_by_phase_order]

    A05 Required test 1: a flow with a cycle and an edge between different
    schemas fails in phase 3 at that edge, not at the cycle.
    """
    text_fn = _function(semantic_runtime, "text_step", TEXT)
    number_fn = _function(semantic_runtime, "number_step", NUMBER)

    # a <-> b is a cycle (phase 7); a.y -> c.x joins a text output to a number
    # input (phase 3). Every other check of phases 1-6 passes: each node names
    # an existing contract version, no constants, every node input has exactly
    # one edge, no guards, all ports `one`.
    cycle = [
        _edge("a", "y", "b", "x"),
        _edge("b", "y", "a", "x"),
    ]
    mismatch = _edge("a", "y", "c", "x")

    composed = semantic_runtime.compose_flow_version(
        "a05_phase_order",
        purpose="A05 witness: phase order",
        inputs=[],
        outputs=[],
        nodes=[_node("a", text_fn), _node("b", text_fn), _node("c", number_fn)],
        edges=cycle + [mismatch],
        constants=[],
    )
    proof = composed.proof
    assert proof.proven is False
    assert _phase(proof.failure) == "edges"
    assert _edge_key(proof.failure) == ("a", "y", "c", "x")

    # The proof is recomputed on demand and gives the same first failure.
    again = semantic_runtime.prove_flow_version(composed.flow_version.flow_version_id)
    assert again.proven is False
    assert _phase(again.failure) == "edges"
    assert _edge_key(again.failure) == ("a", "y", "c", "x")

    # Control: without the mismatched edge the same cycle is found in phase 7,
    # so the result above comes from the order, not from a missing cycle check.
    control = semantic_runtime.compose_flow_version(
        "a05_phase_order_control",
        purpose="A05 witness: phase order control",
        inputs=[],
        outputs=[],
        nodes=[_node("a", text_fn), _node("b", text_fn)],
        edges=cycle,
        constants=[],
    )
    assert control.proof.proven is False
    assert _phase(control.proof.failure) == "cycles"
    assert control.proof.failure.node_id == "a"


def test_first_failure_in_edge_order(semantic_runtime):
    """[witness: verification:kernel_a05_first_failure_in_edge_order]

    A05 Required test 2: two failing edges report the one first in edge order,
    every time.
    """
    text_fn = _function(semantic_runtime, "text_step", TEXT)
    number_fn = _function(semantic_runtime, "number_step", NUMBER)
    nodes = [
        _node("a", text_fn),
        _node("b", text_fn),
        _node("m", number_fn),
        _node("n", number_fn),
    ]
    # Both edges join a text output to a number input (phase 3). A05 rule 1
    # phase 3: edges are ordered by (to_node, to_port, from_node, from_port), so
    # b.y -> m.x comes first although its source `b` sorts after `a` and it is
    # listed second.
    into_m = _edge("b", "y", "m", "x")
    into_n = _edge("a", "y", "n", "x")

    composed = semantic_runtime.compose_flow_version(
        "a05_edge_order",
        purpose="A05 witness: edge order",
        inputs=[],
        outputs=[],
        nodes=nodes,
        edges=[into_n, into_m],
        constants=[],
    )
    flow_version_id = composed.flow_version.flow_version_id
    assert composed.proof.proven is False
    assert _phase(composed.proof.failure) == "edges"
    assert _edge_key(composed.proof.failure) == ("b", "y", "m", "x")

    # Every time: proving again gives the same first failure.
    for _ in range(3):
        again = semantic_runtime.prove_flow_version(flow_version_id)
        assert again.proven is False
        assert _phase(again.failure) == "edges"
        assert _edge_key(again.failure) == ("b", "y", "m", "x")

    # The same content listed in the other order is the same version (A01
    # rule 1 sorts nodes and edges) and fails at the same edge.
    reordered = semantic_runtime.compose_flow_version(
        "a05_edge_order",
        purpose="A05 witness: edge order",
        inputs=[],
        outputs=[],
        nodes=list(reversed(nodes)),
        edges=[into_m, into_n],
        constants=[],
    )
    assert reordered.flow_version.flow_version_id == flow_version_id
    assert _phase(reordered.proof.failure) == "edges"
    assert _edge_key(reordered.proof.failure) == ("b", "y", "m", "x")

    # Control: two failing edges into the same port tie on (to_node, to_port)
    # and are ordered by from_node, so the edge from `a` is named although it
    # is listed second.
    tie = semantic_runtime.compose_flow_version(
        "a05_edge_order_tie",
        purpose="A05 witness: edge order tie",
        inputs=[],
        outputs=[],
        nodes=[_node("a", text_fn), _node("b", text_fn), _node("m", number_fn)],
        edges=[_edge("b", "y", "m", "x"), _edge("a", "y", "m", "x")],
        constants=[],
    )
    assert tie.proof.proven is False
    assert _phase(tie.proof.failure) == "edges"
    assert _edge_key(tie.proof.failure) == ("a", "y", "m", "x")


def test_fan_in_one_delivering_edge_per_port(semantic_runtime):
    """[witness: verification:kernel_a05_fan_in_one_delivering_edge_per_port]

    A05 Required test 3: two unguarded edges into one `many` input are refused
    in phase 6.
    """
    split_fn = _contract(
        semantic_runtime,
        "split_step",
        inputs=[_port("x", "input", TEXT, "open")],
        outputs=[_list_port("ys", "output", TEXT)],
    )
    join_fn = _contract(
        semantic_runtime,
        "join_step",
        inputs=[_list_port("xs", "input", TEXT, "open")],
        outputs=[_port("y", "output", TEXT)],
    )
    nodes = [_node("c", join_fn), _node("p", split_fn), _node("q", split_fn)]
    feed = [
        _edge("", "seed", "p", "x"),
        _edge("", "seed", "q", "x"),
        _edge("c", "y", "", "out"),
    ]

    # Phases 1-5 pass: `many` outputs feed a `many` input (phase 5). A05 rule 1
    # phase 6 and rule 3: both unguarded edges into c.xs can deliver, and the
    # kernel does not concatenate lists.
    composed = semantic_runtime.compose_flow_version(
        "a05_fan_in",
        purpose="A05 witness: fan-in",
        inputs=[_port("seed", "input", TEXT, "open")],
        outputs=[_port("out", "output", TEXT)],
        nodes=nodes,
        edges=feed + [_edge("p", "ys", "c", "xs"), _edge("q", "ys", "c", "xs")],
        constants=[],
    )
    assert composed.proof.proven is False
    assert _phase(composed.proof.failure) == "fan_in"
    assert composed.proof.failure.node_id == "c"
    assert composed.proof.failure.port == "xs"

    # Control: with one of the two edges the same graph is proven, so the
    # refusal above comes from the second delivering edge alone.
    control = semantic_runtime.compose_flow_version(
        "a05_fan_in_control",
        purpose="A05 witness: fan-in control",
        inputs=[_port("seed", "input", TEXT, "open")],
        outputs=[_port("out", "output", TEXT)],
        nodes=[_node("c", join_fn), _node("p", split_fn)],
        edges=[_edge("", "seed", "p", "x"), _edge("c", "y", "", "out"), _edge("p", "ys", "c", "xs")],
        constants=[],
    )
    assert control.proof.proven is True
    assert control.proof.failure is None


def _check_contract(semantic_runtime):
    """`check_step`: one text input `x`; text outputs `a`, `b`; closed-set `kind`, `verdict`."""
    return _contract(
        semantic_runtime,
        "check_step",
        inputs=[_port("x", "input", TEXT, "open")],
        outputs=[
            _port("a", "output", TEXT),
            _port("b", "output", TEXT),
            _port("kind", "output", VERDICT),
            _port("verdict", "output", VERDICT),
        ],
    )


def _guard_flow(semantic_runtime, flow_id, guard_values, guard_ports=("verdict", "verdict")):
    """`check` routes the item to `save.x` over two edges from two of its outputs.

    `guard_values` gives the guard value of each edge, or None for an unguarded
    edge; `guard_ports` the output of `check` each edge is guarded on —
    `verdict` or `kind`, both closed sets of `new` and `duplicate`.
    """
    check_fn = _check_contract(semantic_runtime)
    save_fn = _function(semantic_runtime, "save_step", TEXT)
    routes = []
    for from_port, guard_port, guard_value in zip(("a", "b"), guard_ports, guard_values):
        if guard_value is None:
            routes.append(_edge("check", from_port, "save", "x"))
        else:
            routes.append(_guarded("check", from_port, "save", "x", guard_port, guard_value))
    return semantic_runtime.compose_flow_version(
        flow_id,
        purpose=f"A05 witness: {flow_id}",
        inputs=[_port("item", "input", TEXT, "open")],
        outputs=[_port("out", "output", TEXT)],
        nodes=[_node("check", check_fn), _node("save", save_fn)],
        edges=[_edge("", "item", "check", "x"), _edge("save", "y", "", "out")] + routes,
        constants=[],
    )


def test_exclusive_guards_share_input_port(semantic_runtime):
    """[witness: verification:kernel_a05_exclusive_guards_share_input_port]

    A05 Required test 4: two edges guarded on the same port with values `new`
    and `duplicate` into one input are proven.
    """
    # A05 rule 3: guarded on the same guard port of the same source node with
    # different values, the two edges cannot both deliver. Guard values are JSON
    # text (State 5, "Values enter canonical").
    composed = _guard_flow(semantic_runtime, "a05_exclusive_guards", ('"new"', '"duplicate"'))
    assert composed.proof.proven is True
    assert composed.proof.failure is None
    assert _value(composed.proof.highest_effect_class) == "read"

    # Control: the same two edges unguarded are refused in phase 6, so the
    # proof above passed the fan-in check, it did not skip it.
    control = _guard_flow(semantic_runtime, "a05_exclusive_guards_control", (None, None))
    assert control.proof.proven is False
    assert _phase(control.proof.failure) == "fan_in"
    assert control.proof.failure.node_id == "save"
    assert control.proof.failure.port == "x"

    # Control: the same values on two different guard ports of `check` can
    # both deliver (A05 rule 3: only the same guard port excludes), so the
    # proof above compared the guard ports, not only the values.
    other_ports = _guard_flow(
        semantic_runtime,
        "a05_exclusive_guards_other_ports",
        ('"new"', '"duplicate"'),
        guard_ports=("verdict", "kind"),
    )
    assert other_ports.proof.proven is False
    assert _phase(other_ports.proof.failure) == "fan_in"
    assert other_ports.proof.failure.node_id == "save"
    assert other_ports.proof.failure.port == "x"

    # Control: guard ports of the same name on two different source nodes can
    # both deliver too (A05 rule 3: the same guard port of the same source
    # node), so the proof above compared the source nodes as well.
    check_fn = _check_contract(semantic_runtime)
    save_fn = _function(semantic_runtime, "save_step", TEXT)
    other_sources = semantic_runtime.compose_flow_version(
        "a05_exclusive_guards_other_sources",
        purpose="A05 witness: a05_exclusive_guards_other_sources",
        inputs=[_port("item", "input", TEXT, "open")],
        outputs=[_port("out", "output", TEXT)],
        nodes=[_node("check", check_fn), _node("check2", check_fn), _node("save", save_fn)],
        edges=[
            _edge("", "item", "check", "x"),
            _edge("", "item", "check2", "x"),
            _edge("save", "y", "", "out"),
            _guarded("check", "a", "save", "x", "verdict", '"new"'),
            _guarded("check2", "a", "save", "x", "verdict", '"duplicate"'),
        ],
        constants=[],
    )
    assert other_sources.proof.proven is False
    assert _phase(other_sources.proof.failure) == "fan_in"
    assert other_sources.proof.failure.node_id == "save"
    assert other_sources.proof.failure.port == "x"


def test_proof_recomputed_on_demand(semantic_runtime):
    """[witness: verification:kernel_a05_proof_recomputed_on_demand]

    A05 Required test 5: a version refused because its binding is `proposed` is
    proven after the owner accepts the binding, with the same
    `flow_version_id`.
    """
    _service(
        semantic_runtime,
        "archive",
        [_capability("save_draft", "POST /drafts", "draft-write")],
    )
    binding_id = _proposed(
        semantic_runtime,
        "archive",
        "save_draft",
        inputs=[_port("material", "input", TEXT, "business_confidential")],
        outputs=[],
    )

    def compose():
        return semantic_runtime.compose_flow_version(
            "a05_recomputed",
            purpose="A05 witness: proof recomputed",
            inputs=[_port("material", "input", TEXT, "open")],
            outputs=[],
            nodes=[_operation_node("save", binding_id)],
            edges=[_edge("", "material", "save", "material")],
            constants=[],
        )

    composed = compose()
    flow_version_id = composed.flow_version.flow_version_id
    # A05 rule 1 phase 1: an operation node names a binding in status `accepted`.
    assert composed.proof.proven is False
    assert _phase(composed.proof.failure) == "nodes"
    assert composed.proof.failure.node_id == "save"
    # A05 rule 6: while the binding keeps its status, the result is the same.
    still = semantic_runtime.prove_flow_version(flow_version_id)
    assert still.proven is False
    assert _phase(still.failure) == "nodes"

    accepted = semantic_runtime.accept_binding(binding_id)
    assert _value(accepted.status) == "accepted"

    proof = semantic_runtime.prove_flow_version(flow_version_id)
    assert proof.flow_version_id == flow_version_id
    assert proof.proven is True
    assert proof.failure is None
    # A05 rule 5: the highest effect class of its operation nodes.
    assert _value(proof.highest_effect_class) == "draft-write"

    # No new version: composing the same content returns the same version, now
    # proven, and the flow has exactly one version.
    again = compose()
    assert again.flow_version.flow_version_id == flow_version_id
    assert again.proof.proven is True
    versions = semantic_runtime.page_records(
        "flow_version",
        {"filter_kind": "equals", "field": "flow_id", "value": "a05_recomputed"},
        page_size=200,
    )
    assert [v.flow_version_id for v in versions.records.flow_versions] == [flow_version_id]


def test_codepoint_identifier_order(semantic_runtime):
    """[witness: verification:kernel_a05_codepoint_identifier_order]

    A05 Required test 8: an edge into node `Z` and an edge into node `a`, each
    between different schemas, fail in phase 3 at the edge into `Z`; with a
    third such edge into a flow output added, the proof fails at that edge
    instead.
    """
    text_fn = _function(semantic_runtime, "text_step", TEXT)
    number_fn = _function(semantic_runtime, "number_step", NUMBER)
    nodes = [_node("Z", number_fn), _node("a", number_fn), _node("src", text_fn)]
    into_a = _edge("src", "y", "a", "x")
    into_z = _edge("src", "y", "Z", "x")

    # A05 rule 2: identifiers compare by Unicode code point, so `Z` (U+005A)
    # orders before `a` (U+0061), unlike a case-folding order.
    composed = semantic_runtime.compose_flow_version(
        "a05_codepoint",
        purpose="A05 witness: code point order",
        inputs=[],
        outputs=[],
        nodes=nodes,
        edges=[into_a, into_z],
        constants=[],
    )
    assert composed.proof.proven is False
    assert _phase(composed.proof.failure) == "edges"
    assert _edge_key(composed.proof.failure) == ("src", "y", "Z", "x")

    # A05 rule 2: a flow output endpoint has the empty string as its node, so
    # an edge into it orders before every node.
    with_output = semantic_runtime.compose_flow_version(
        "a05_codepoint_output",
        purpose="A05 witness: code point order with a flow output",
        inputs=[],
        outputs=[_port("out", "output", NUMBER)],
        nodes=nodes,
        edges=[into_a, into_z, _edge("src", "y", "", "out")],
        constants=[],
    )
    assert with_output.proof.proven is False
    assert _phase(with_output.proof.failure) == "edges"
    assert _edge_key(with_output.proof.failure) == ("src", "y", "", "out")


def test_highest_effect_class_max_or_read(semantic_runtime):
    """[witness: verification:kernel_a05_highest_effect_class_max_or_read]

    A05 Required test 9: a proven version with no operation node has
    `highest_effect_class` `read`; one with a `read` and a `draft-write`
    operation node has `draft-write`.
    """
    _service(
        semantic_runtime,
        "archive",
        [
            _capability("lookup", "GET /records", "read"),
            _capability("save_draft", "POST /drafts", "draft-write"),
        ],
    )
    lookup = _accepted(
        semantic_runtime,
        "archive",
        "lookup",
        inputs=[_port("q", "input", TEXT, "open")],
        outputs=[_port("record", "output", TEXT, "business_confidential")],
    )
    save = _accepted(
        semantic_runtime,
        "archive",
        "save_draft",
        inputs=[_port("material", "input", TEXT, "business_confidential")],
        outputs=[],
    )
    step_fn = _function(semantic_runtime, "text_step", TEXT)

    no_operation = semantic_runtime.compose_flow_version(
        "a05_effect_none",
        purpose="A05 witness: no operation node",
        inputs=[_port("item", "input", TEXT, "open")],
        outputs=[_port("out", "output", TEXT)],
        nodes=[_node("step", step_fn)],
        edges=[_edge("", "item", "step", "x"), _edge("step", "y", "", "out")],
        constants=[],
    )
    assert no_operation.proof.proven is True
    # A05 rule 5: `read` when the version has no operation node.
    assert _value(no_operation.proof.highest_effect_class) == "read"

    both = semantic_runtime.compose_flow_version(
        "a05_effect_both",
        purpose="A05 witness: read and draft-write",
        inputs=[
            _port("material", "input", TEXT, "open"),
            _port("query", "input", TEXT, "open"),
        ],
        outputs=[],
        nodes=[_operation_node("lookup", lookup), _operation_node("save", save)],
        edges=[
            _edge("", "query", "lookup", "q"),
            _edge("", "material", "save", "material"),
        ],
        constants=[],
    )
    assert both.proof.proven is True
    # A05 rule 5: the highest in the order of M10 (read < draft-write < ...);
    # as text, "read" would sort after "draft-write".
    assert _value(both.proof.highest_effect_class) == "draft-write"
    again = semantic_runtime.prove_flow_version(both.flow_version.flow_version_id)
    assert _value(again.highest_effect_class) == "draft-write"

    # The same two operation nodes with the `draft-write` node first in
    # `node_id` order: still `draft-write`, so the class is the maximum, not
    # that of the first or of the last operation node.
    swapped = semantic_runtime.compose_flow_version(
        "a05_effect_both_swapped",
        purpose="A05 witness: draft-write node first",
        inputs=[
            _port("material", "input", TEXT, "open"),
            _port("query", "input", TEXT, "open"),
        ],
        outputs=[],
        nodes=[_operation_node("a_save", save), _operation_node("b_lookup", lookup)],
        edges=[
            _edge("", "query", "b_lookup", "q"),
            _edge("", "material", "a_save", "material"),
        ],
        constants=[],
    )
    assert swapped.proof.proven is True
    assert _value(swapped.proof.highest_effect_class) == "draft-write"

    # Control: a version whose only operation node is `read` has `read`, so
    # `draft-write` above is the maximum, not "any operation node".
    read_only = semantic_runtime.compose_flow_version(
        "a05_effect_read",
        purpose="A05 witness: read operation only",
        inputs=[_port("query", "input", TEXT, "open")],
        outputs=[],
        nodes=[_operation_node("lookup", lookup)],
        edges=[_edge("", "query", "lookup", "q")],
        constants=[],
    )
    assert read_only.proof.proven is True
    assert _value(read_only.proof.highest_effect_class) == "read"


def test_same_guard_value_edges_refused(semantic_runtime):
    """[witness: verification:kernel_a05_same_guard_value_edges_refused]

    A05 Required test 10: two edges guarded on the same port with the same value
    into one input are refused in phase 6.
    """
    # A05 rule 3: same guard port, same guard value, so both can deliver.
    composed = _guard_flow(semantic_runtime, "a05_same_guard", ('"new"', '"new"'))
    assert composed.proof.proven is False
    assert _phase(composed.proof.failure) == "fan_in"
    assert composed.proof.failure.node_id == "save"
    assert composed.proof.failure.port == "x"

    # Control: with values `new` and `duplicate` the same graph is proven, so
    # the refusal comes from the equal guard values.
    control = _guard_flow(semantic_runtime, "a05_same_guard_control", ('"new"', '"duplicate"'))
    assert control.proof.proven is True
