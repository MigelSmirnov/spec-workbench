# State 1 companion — operation binding and flow models

## Purpose

This document closes identity and data shape for the second node kind and for
composition, under State 0 decisions D0-035, D0-038, D0-039 and D0-040: the
binding that gives one manifest operation typed ports, and the flow as versioned,
proven data.

## Model M28 — ManifestOperationRef

### Meaning

The exact identification of one operation of one microservice as the platform
manifest declared it at one moment.

Candidate fields:

- `service_id`: the manifest record's service name;
- `capability_id`: the capability inside that record;
- `channel`: `mcp`, `http_api` or `operator`;
- `operation`: the tool name, method and path, or entry-point name on that
  channel;
- `manifest_record_digest`: digest of the service's manifest record the
  reference was taken from.

### Identity

value

### Identity evidence

Substitution: equal service, capability, channel, operation and record digest
are interchangeable. Continuity belongs to the manifest; a changed record gives
another digest and therefore another reference.

### Source of truth

The platform manifest of the Factory repository at the named digest.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Embedded in operation binding versions and in node-execution evidence.

### Open questions

None.

## Model M29 — OperationBinding

### Meaning

The continuing declaration that one microservice operation is available to flows
as an operation node.

Candidate fields:

- `binding_id`: stable namespaced identity;
- `service_id`, `capability_id`, `channel`: the operation it stands for;
- `purpose`: bounded human-readable statement of what the node does, in the
  owner's words;
- `status`: `proposed`, `accepted`, `suspended` or `retired`;
- `current_version_id`;
- `proposed_by`: ActorRef.

### Identity

entity

### Identity evidence

Substitution: two bindings are never interchangeable, even for the same
operation, because flows and approvals refer to one of them. Continuity: the
binding stays the same while versions are issued after manifest changes and
while its status changes.

### Source of truth

The kernel's binding registry. Only the owner moves a binding to `accepted`.

### Lifecycle candidate

`proposed -> accepted -> retired`, with `accepted -> suspended -> accepted`. The
kernel suspends a binding by itself when the manifest operation it names has
changed or disappeared; only the owner's acceptance of a new version lifts the
suspension. No operation node runs through a binding that is not `accepted`.

### Persistence candidate

Durable entity of the kernel's operational store.

### Open questions

None.

## Model M30 — OperationBindingVersion

### Meaning

One immutable typed description of a manifest operation: its ports, and the
effect, idempotency and replay facts the kernel must honour when invoking it.

Candidate fields:

- `binding_id`;
- `binding_version_id`: content-derived identity;
- `manifest_operation_ref`: one ManifestOperationRef;
- `input_ports`, `output_ports`: SemanticPort values;
- `effect_class`: `read`, `draft-write`, `state-transition`, `external-effect`
  or `destructive`, copied from the manifest record at that digest;
- `replay`: `safe`, `refuses`, `returns_existing`, `overwrites` or `duplicates`,
  copied likewise;
- `idempotency_key_ports`: the input ports whose values form the manifest's
  idempotency key, empty when the manifest declares none;
- `outcome_read_binding_ref`: the `read` binding through which an undetermined
  outcome of this operation is reconciled; required unless `effect_class` is
  `read`;
- `preview_ports`: the input ports shown to the owner in an approval preview;
- `accepted_by`: ActorRef of the owner; `accepted_at`. Both are absent on a
  proposed version: only the owner accepts (A10), so acceptance facts exist only
  once `accept_binding_version` has written them, exactly once.

Effect class and replay are never authored. They are copied from the manifest so
that a binding cannot present a write as a read.

### Identity

value

### Identity evidence

Substitution: equal content-derived identity is interchangeable. Continuity: a
version never changes; a changed manifest record or a changed port requires
another version and another acceptance.

### Source of truth

The owner's acceptance of an agent's or the owner's proposal, checked by the
kernel against the manifest record at the named digest.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Durable, pinned by flow nodes, approvals, grants and node executions.

### Open questions

None.

## Model M31 — Flow

### Meaning

One continuing named composition that answers one kind of request, across all
its versions.

Candidate fields:

- `flow_id`: stable namespaced identity;
- `name`: bounded human-readable name the flow is known by;
- `purpose`: bounded human-readable statement in the owner's words;
- `status`: `active` or `retired`;
- `created_by`: ActorRef; `created_at`;
- `retired_by`: ActorRef, `retired_at` and `retirement_reason`: absent while the
  flow is active; written once by retirement and never rewritten.

### Identity

entity

### Identity evidence

Substitution: two flows are never interchangeable, even with identical current
graphs; runs, approvals and grants belong to one of them. Continuity: the flow
stays the same while versions replace one another.

### Source of truth

The kernel's flow registry, written through the kernel surface.

### Lifecycle candidate

`active -> retired`. A retired flow starts no run; its past runs stay readable.

### Persistence candidate

Durable entity of the kernel's operational store.

### Open questions

None.

## Model M32 — FlowVersion

### Meaning

One immutable acyclic graph of function nodes and operation nodes with typed
edges, typed flow inputs and outputs, and pinned constants.

Candidate fields:

- `flow_id`;
- `flow_version_id`: content-derived identity over the flow, its inputs,
  outputs, nodes, edges and constants — never over author or time, so the same
  graph authored twice is the same version;
- `flow_inputs`: SemanticPort values a run must supply;
- `flow_outputs`: SemanticPort values a run returns;
- `nodes`: FlowNode values;
- `edges`: FlowEdge values;
- `constants`: FlowConstant values;
- `highest_effect_class`: derived from the pinned binding versions, never
  authored;
- `authored_by`: ActorRef; `authored_at`.

A flow version holds no code, expression, loop or reference to "latest". It pins
contract versions and binding versions; which implementation serves a contract
version is pinned per run.

### Identity

value

### Identity evidence

Substitution: equal content-derived identity is interchangeable. Continuity: a
version never changes. The smallest edit is another version, which needs its own
proof, its own activation and, where effects are present, its own approval.

### Source of truth

The kernel, from an authoring request.

### Lifecycle candidate

No independent lifecycle. Whether it may run is stated by FlowProof and
FlowActivation.

### Persistence candidate

Durable, referenced by proofs, activations, grants and runs.

### Open questions

None.

## Model M33 — FlowNode

### Meaning

One position of a flow version that executes either a function or a
microservice operation.

Candidate fields:

- `node_id`: stable only inside its flow version;
- `node_kind`: `function` or `operation`;
- `contract_version_ref` when the kind is `function`;
- `binding_version_ref` when the kind is `operation`;
- `map_over_port`: optional; the one `many` input port over whose elements the
  node is executed once each, the outputs being collected in element order.

Exactly one of the two references is present. There is no third node kind.

### Identity

value

### Identity evidence

Substitution: equal node identity, kind, pinned reference and map declaration
inside the same flow version are interchangeable. Continuity: a node has no
identity outside its flow version.

### Source of truth

The flow version.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Embedded in FlowVersion.

### Open questions

None.

## Model M34 — FlowEdge

### Meaning

One directed, typed delivery of a value from a source to a target inside a flow
version, together with the evidence that the delivery is meaningful.

Candidate fields:

- `source`: one of a flow input port, a constant, or a node's output port;
- `target`: one of a node's input port or a flow output port;
- `composition_basis`: `same_term` with the shared semantic-term revision, or
  `relation` with the exact SemanticRelationRevision;
- `guard`: optional; one output port of the source node whose value schema is a
  closed set, and the one value that enables this edge.

An edge whose basis is a relation that requires execution is not an edge; the
required capability appears as a node between the two ports. A disabled guard
makes the target node not executed, which is an outcome and not a failure.

### Identity

value

### Identity evidence

Substitution: equal source, target, basis and guard inside the same flow version
are interchangeable. Continuity: an edge has no identity outside its flow
version.

### Source of truth

The flow version, verified by FlowProof.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Embedded in FlowVersion.

### Open questions

None.

## Model M35 — FlowConstant

### Meaning

One typed literal that a flow version supplies to a port, such as a tax rate or
a threshold.

Candidate fields:

- `constant_id`: stable only inside its flow version;
- `semantic_term_revision_ref`;
- `value`: one bounded value of the term's value family;
- `explanation`: bounded text stating where the number comes from.

A constant is part of the flow version's identity. Changing it is another flow
version, so a run can never be explained by a value that has since moved.

### Identity

value

### Identity evidence

Substitution: equal term, value and explanation inside the same flow version are
interchangeable. Continuity: none outside its flow version.

### Source of truth

The flow version.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Embedded in FlowVersion.

### Open questions

None.

## Model M36 — FlowProof

### Meaning

The kernel's deterministic verdict that one flow version is well formed and that
every one of its edges is meaningful under the vocabulary as it stood.

Candidate fields:

- `proof_id`;
- `flow_version_ref`;
- `vocabulary_basis`: the exact term and relation revisions relied upon;
- `verdict`: `proven` or `refused`;
- `findings`: closed set, each naming the node, port or edge —
  `unknown_contract_version`, `unknown_binding_version`, `binding_not_accepted`,
  `untyped_port`, `edge_without_basis`, `shape_incompatible`,
  `cardinality_incompatible`, `disclosure_exceeded`,
  `unsupplied_required_input`, `multiple_edges_into_input`, `cycle`,
  `guard_on_open_value`, `map_on_non_collection`,
  `required_output_behind_guard` or `unreachable_node`;
- `decided_at`.

A refused proof names every finding, not the first. No one can record, override
or waive a proof.

### Identity

value

### Identity evidence

Substitution: equal proof identity is interchangeable. A later proof of the same
flow version against a changed vocabulary is another proof. Continuity: the
record never changes.

### Source of truth

The kernel.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Durable evidence, referenced by flow activations and runs.

### Open questions

None.

## Model M37 — FlowActivation

### Meaning

The immutable record that one proven flow version may be run, and on whose
authority.

Candidate fields:

- `flow_activation_id`;
- `flow_version_ref`;
- `proof_ref`: a `proven` FlowProof of that version;
- `activated_by`: ActorRef — `kernel` when `highest_effect_class` is `read`,
  otherwise the owner;
- `owner_statement`: bounded text the owner approved, required when the owner
  activates; it states in plain words what the flow will change and where;
- `previous_flow_activation_ref`;
- `activated_at`.

The version of a flow that runs by default is the one named by its latest
activation. Returning to an earlier version is a new activation.

### Identity

value

### Identity evidence

Substitution: equal activation identity is interchangeable; two activations of
the same version at different times are distinct facts. Continuity: the record
never changes.

### Source of truth

The kernel for read-only flows; the owner's recorded decision for every other
flow.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Durable, referenced by runs.

### Open questions

None.
