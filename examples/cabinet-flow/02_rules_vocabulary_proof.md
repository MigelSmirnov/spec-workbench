# State 2 — Cabinet Flow vocabulary and flow-proof rules

## Accepted decision A01 — the vocabulary changes only by the owner's acceptance

### Normative rules

1. A SemanticAxis M01, SemanticTerm M03 or SemanticRelation M06 exists only by
   installation seed or by the owner's acceptance of a VocabularyProposal M45.
   No other operation creates, edits or reactivates one.
2. A revision M02, M04 or M07 is immutable. A changed meaning, shape, qualifier
   or relation kind issues another revision with a content-derived identity;
   the stable entity keeps its identity.
3. An agent with authoring delegation may submit a proposal. A proposal carries
   a plain statement the owner can decide without reading a schema, and the
   proof finding or UncomposableOutput M15 that motivated it.
4. A proposal is never composition evidence. No port, edge or relation may cite
   a proposal or content that exists only inside one.
5. Acceptance is atomic: the proposal becomes `accepted`, the revision is
   issued, and `resulting_revision_ref` names it, or nothing changes.
6. Retiring a term or relation never invalidates a FlowProof M36 already
   recorded against its revision and never alters a pinned run. It refuses new
   contract versions, binding versions and proofs that would cite it.
7. A proposal whose content equals an existing active revision is refused with
   a reference to that revision rather than accepted as a duplicate.

### Formal invariants

```text
vocabulary_entry_exists
-> installation_seed OR accepted_proposal_by_owner

composition_basis(edge) -> accepted_revision
composition_basis(edge) -/> proposal

revision_issued -> immutable
term_retired -/> existing_proof_invalidated
```

### Required tests

1. An agent's authoring request that names an unknown term is refused and
   creates no term.
2. An edge citing a `proposed` relation is refused by proof.
3. Accepting a proposal issues exactly one revision and links it; a failure
   midway leaves the proposal `proposed` and the registry unchanged.
4. After a term is retired, a run pinned to a flow proven on it completes, and a
   new contract version citing it is refused.
5. A proposal equal to an active revision is refused with that revision's
   identity.

### Consequence

Meaning is the one thing the agent cannot give itself. Everything else it
authors is checked against a vocabulary only the owner can extend.

## Accepted decision A02 — an edge is proven by exact term or exact relation

### Normative rules

1. Every SemanticPort M05 of a contract version M20, binding version M30 or
   flow version M32 names one accepted SemanticTermRevision M04 and one value
   schema. A port without both cannot be issued.
2. A FlowEdge M34 is valid on basis `same_term` only when source and target
   ports name the identical term revision and the source schema is accepted by
   the target schema without coercion.
3. A FlowEdge is valid on basis `relation` only when it cites one active
   SemanticRelationRevision M07 whose source term revision and target term
   revision equal those of the two ports, whose schemas match the ports, and
   whose kind is `exact_identity`, `lossless_projection` or `role_binding`.
4. A relation of kind `explicit_conversion` or `resolution` is never an edge
   basis. It is satisfied only by a function node of the slot named by
   `required_slot_ref`, placed between the two ports, each of whose own edges is
   proven under rule 2 or 3.
5. Cardinality is proven: `one` feeds `one` or `optional`; `optional` feeds only
   `optional`; `many` feeds `many`, or feeds `one` on a node whose
   `map_over_port` is that input.
6. Sharing an axis, a value family, a primitive type or a field name is never
   evidence. An edge with no valid basis is refused; the proof does not search
   for or suggest a basis on its own authority.
7. A port of carriage `byte_stream` carries a file and exists on slot contract
   versions and operation binding versions. An edge from a `byte_stream` output
   is valid only into a `byte_stream` input, of a function node or an operation
   node, under the same term and relation rules, and only when every media type
   the source may produce is accepted by the target and the source's size
   ceiling does not exceed the target's. It is never valid into a `value` port,
   a flow output or a guard. Cardinality and mapping apply to files as to
   values: a collection of photos is mapped element by element.
8. An output port without a term produces an UncomposableOutput M15. It may be a
   flow output returned to the caller and may not be the source of any edge to a
   node.

### Formal invariants

```text
edge_valid
<-> (same_term_revision AND schema_accepted)
    OR (cited_active_relation_revision
        AND relation.source = source_port.term
        AND relation.target = target_port.term
        AND relation.kind IN {exact_identity, lossless_projection, role_binding})

relation.kind IN {explicit_conversion, resolution}
-> satisfied_only_by_node(required_slot)

same_axis OR same_primitive_type -/> edge_valid
```

### Required tests

1. Invoice issue date wired to delivery occurrence date, both local dates, is
   refused as `edge_without_basis`.
2. The same wiring with an accepted `role_binding` relation is proven.
3. An edge citing a `resolution` relation directly is refused; the same path
   through a node of the required slot is proven.
4. `optional` feeding `one`, and `many` feeding `one` without a map, are refused
   as `cardinality_incompatible`.
5. A term-less output wired to a node input is refused; wired to a flow output
   it is accepted and returned as UncomposableOutput.
6. A `byte_stream` output wired to a `value` input or to a flow output is
   refused. Wired to a `byte_stream` input of a function or of an operation under
   the same term it is proven; wired to an input that accepts only JPEG while
   the source may produce PNG it is refused as `shape_incompatible`.

### Consequence

The agent chooses the composition and the kernel decides whether it means
anything. No composition runs on resemblance.

## Accepted decision A03 — a disclosure class is derived, never authored down

### Normative rules

1. The classes are ordered `open < business_confidential < personal_data`.
2. An operation binding version declares the class of each output port and the
   highest class each input port accepts. These declarations are part of what
   the owner accepts.
3. A function contract's input port declares the highest class it accepts. Its
   output ports carry no authored class.
4. At proof time the class of a function node's every output is the highest
   class that can reach any of its inputs over the graph. At run time the class
   recorded on a StoredValue M38 produced by a function is the highest class
   among the values that execution actually received.
5. A FlowConstant M35 is `open`. A flow input port declares its class and a run
   must supply a value at or below it.
6. An edge delivering a class above what the target input accepts is refused as
   `disclosure_exceeded`. No function, relation or flow construct lowers a
   class.
7. The surface returns a value to an agent only when the value's class is at or
   below the delegation's `disclosure_ceiling`; otherwise it returns the digest,
   the term and the class, and no content.
8. The only way personal data reaches an `external-effect` operation is an
   accepted binding version whose input port accepts `personal_data`.

### Formal invariants

```text
class(function_output) = max(class(received_inputs))
class(constant) = open

edge_valid -> class(source) <= accepts(target_input)

value_returned_to_agent -> class(value) <= delegation.disclosure_ceiling
```

### Required tests

1. A function that receives a `personal_data` value and returns one unrelated
   integer yields an output of class `personal_data`.
2. A path from a personal-data read through three functions to a binding whose
   input accepts `business_confidential` is refused by proof.
3. The same path to a binding accepting `personal_data` is proven.
4. An agent with ceiling `business_confidential` reading a run receives digests
   and classes for personal-data values and content for the rest.
5. A run supplying a flow input above the port's declared class is refused
   before any node executes.

### Consequence

Client data cannot leave the platform through a chain of innocent-looking
functions. Where it may go is a property of bindings the owner accepted.

## Accepted decision A04 — a flow is proven whole before it can be activated

### Normative rules

1. FlowProof M36 evaluates one exact flow version against the vocabulary
   revisions in force and records them as `vocabulary_basis`.
2. Proof verifies, completely and in one pass: every node pins an existing
   contract version or an `accepted` binding's version; every edge satisfies
   A02 and A03; every required input port of every node has exactly one incoming
   edge; no input port has more than one; the graph is acyclic; every node
   reaches a flow output or is an operation node with an effect class other than
   `read`; every guard names an output port whose schema is a closed set and one
   value of that set; every `map_over_port` is a `many` input.
3. A required flow output that can be left unproduced by a guard is refused as
   `required_output_behind_guard`. A flow output behind a guard must be
   `optional`.
4. A refused proof lists every finding. It never stops at the first.
5. A proof is deterministic: the same flow version and vocabulary basis yield
   the same verdict and findings.
6. No actor records, edits, overrides or waives a proof. A flow version without
   a `proven` proof cannot receive a FlowActivation M37.
7. When a binding named by a proven flow version is later suspended, the proof
   stands and runs stop at that node under A10. Proof is about meaning, not
   about availability.

### Formal invariants

```text
flow_activation_exists -> proven_proof_of_same_flow_version

proven
<-> all_nodes_pinned AND all_edges_valid AND inputs_supplied_exactly_once
    AND acyclic AND no_unreachable_pure_node
    AND guards_on_closed_values AND maps_on_many_ports
    AND required_outputs_not_behind_guard

same(flow_version, vocabulary_basis) -> same(verdict, findings)
```

### Required tests

1. A flow with a cycle, an unsupplied required input and an invalid edge is
   refused with all three findings.
2. A function node whose outputs reach nothing is refused as
   `unreachable_node`; an effectful operation node with no consumed output is
   accepted.
3. A guard on a free-text port is refused as `guard_on_open_value`.
4. A required flow output behind a guard is refused; the same output declared
   `optional` is proven.
5. Proving the same version twice yields identical verdict and findings.
6. An activation request for an unproven or refused version is refused.

### Consequence

A flow never runs partially understood. What the owner is asked to activate has
already been shown to be well formed and meaningful.
