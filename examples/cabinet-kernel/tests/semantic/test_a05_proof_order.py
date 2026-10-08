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
- ``prove_flow_version(flow_version_id)`` -> ProofResult (M17).
"""

TEXT = '{"type":"string"}'
NUMBER = '{"type":"integer"}'


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
