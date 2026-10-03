# State 2 — Cabinet Kernel flow proof, activation and disclosure rules

Draft of 2026-09-30. Rules for proving and activating flow versions and for
disclosure classes (K-06, K-07, K-08, K-14). Reuses cabinet-flow decisions 03, 04 and 11
where they still hold; semantic terms and relations are gone (K-06).

## Accepted decision A05 — a proof checks one fixed sequence and reports the first failure

Reuses cabinet-flow decision 04, narrowed to schema-proven edges and to the first failure
that M17 returns. Closes the State 1 questions of the proof order, of several
edges into one input, of flow outputs under guards, and of proving again later.

### Normative rules

1. A proof checks one flow version in this order of phases, and within a phase in
   the order named; the first check that fails is the result, with its phase, its
   node or edge and its reason:
   1. nodes, by `node_id`: a function node names an existing contract version; an
      operation node names a binding in status `accepted`;
   2. constants, by (`to_node`, `to_port`): the port exists and is an input port
      of a node — never a flow output — of `value` carriage, and the value fits its
      schema;
   3. edges, by (`to_node`, `to_port`, `from_node`, `from_port`): both ports exist
      with the right direction; both carry the same schema, the same carriage and,
      for files, the same media type (K-06) — cardinality is phase 5's; a flow
      input or output is `value` carriage;
   4. guards, by the same edge order: the guard port is an output of the edge's
      source node, its schema is a closed set, the guard value is a member;
   5. cardinality and maps, by the edge order: a `one` output feeds a `one`
      input; a `many` output feeds a `many` input, or a `one` input that is its
      node's `map_over` port; a `one` output never feeds a `many` input. Every
      output of a mapped node is `many` for its consumers. A node with
      `map_over` has exactly one input fed that way;
   6. fan-in, by (`to_node`, `to_port`): every input port of every node, and every
      flow output, has at least one source; a port with a constant has no other
      constant and no edge; and no two edges that can both deliver (rule 3) end at
      the same port, whatever its cardinality;
   7. cycles: the graph of nodes and edges is acyclic;
   8. disclosure, by the edge order, for every edge or constant ending at a node's
      input port: the class that can reach the source (A07) does not exceed the
      class that input accepts. An edge ending at a flow output is not checked: a
      flow output carries no class and its value keeps the class it arrived with
      (M01);
   9. reach: at least one output of every function node reaches, through edges
      and nodes, a flow output or an operation node, so no function runs for
      nothing; its other outputs may go unused. An output used as the guard port
      of an edge reaches wherever that edge's target reaches.
2. All orders compare identifiers as strings by Unicode code point. A flow input
   or flow output endpoint has the empty string as its node, so it orders before
   every node. Within one item, the conditions are checked in the order the phase
   lists them, and the first that fails is the reason. A check that fails at
   several items names the first of them in that check's own order; a check
   whose items have no order of their own names the smallest identifier by
   code point — for cycles (phase 7) the smallest `node_id` on any cycle, for
   reach (phase 9) the smallest `node_id` of a function node none of whose
   outputs reaches, for repeated names at composition (rule 7) the smallest
   repeated name. "The same schema" means
   equal canonical JSON (State 1); two schemas that accept the same values but
   are written differently are different.
3. Two edges into one port can both deliver unless both are guarded on the same
   guard port of the same source node with different guard values. Several edges
   into one `many` input are therefore refused like any other: the kernel does not
   concatenate lists.
4. A flow output that a guard can leave unproduced is allowed. Such an output is
   reported by the run as `skipped_by_guard` instead of a value (A13).
5. `highest_effect_class` is the highest effect class among the version's
   operation nodes in the order of M10, and `read` when it has none.
6. A proof is computed on demand and not stored (M17). The same flow version gives
   the same result as long as the bindings it names keep their status — the
   proof reads no manifest; a changed manifest entry stops a send (A08 rule 6),
   not a proof; a version whose
   proof failed because a binding was still `proposed` is proven again, with no
   new version, after the owner accepts that binding.
7. State 0's "kept either way" is about the proof: a version is kept whether or
   not it is proven. A malformed request is not a version. Composition refuses, before anything is kept, a flow version whose node ids
   repeat, whose flow input or output port names repeat within a direction, or
   which declares a flow input or output of `file` carriage (M13), a flow input
   without a class, or a flow output with one (M01) — the first of these, in
   this order, is named;
   the proof never sees such a version. Every other structural fault is a proof
   failure (rule 1). Composition keeps any other flow version
   whether or not it is proven. Activation
   proves it again (A06); a run proves nothing, it runs only an active version.

### Formal invariants

```text
proof = first_failure(phases[1..9], fixed_order) OR proven
order(identifiers) = unicode_codepoint_order

can_both_deliver(e1, e2) <-> NOT (guarded_same_port(e1, e2) AND e1.guard_value != e2.guard_value)
for_all port: count(can_both_deliver edges into port) <= 1

highest_effect_class = max(operation_nodes.effect_class) OR read
proof(version) recomputed_on_demand   (not persisted)
```

### Required tests

1. A flow with a cycle and an edge between different schemas fails in phase 3 at
   that edge, not at the cycle.
2. Two failing edges report the one first in edge order, every time.
3. Two unguarded edges into one `many` input are refused in phase 6.
4. Two edges guarded on the same port with values `new` and `duplicate` into one
   input are proven.
5. A version refused because its binding is `proposed` is proven after the owner
   accepts the binding, with the same `flow_version_id`.
6. A function node whose output reaches nothing is refused in phase 9.

### Consequence

The agent always gets the same single answer to "why is this flow not proven",
and fixes one thing at a time.

## Accepted decision A06 — the owner activates every flow that changes anything

Reuses cabinet-flow decision 11, without the generated owner statement: the owner's
approvals carry the exact input instead (K-08).

### Normative rules

1. Activating a flow version proves it again first; an unproven version is
   refused with its proof failure.
2. A proven version whose highest effect class is `read` is activated by the
   kernel as soon as the owner or an agent asks; the activation names the kernel
   as its actor (K-15).
3. Any other proven version is activated only when the owner asks. An agent asking
   to activate it is refused, and nothing is kept for the owner.
4. The checks run in this order: rule 1; an agent asking for a version above
   `read` is refused under rule 3, even when that version is already active
   (State 0); then activating the version that is already active returns the
   active activation and records nothing; then rules 2 and 3 record the
   activation. Activating any other version records a FlowActivation
   M18 that replaces the previous one at once; runs already started keep their
   pinned version (A12).
5. A new flow version inherits nothing: no activation, approval or standing grant
   of an earlier version, however small the difference.

### Formal invariants

```text
flow_activation -> proven(flow_version) at activation
highest_effect_class = read  -> activated_by = kernel
highest_effect_class > read  -> activated_by = owner
agent_asks(effectful) -> refused AND nothing_kept
new_flow_version -/> inherits(activation | grant | approval)
```

### Required tests

1. A proven read-only flow asked for by an agent is active at once and records the
   kernel as actor.
2. Adding one `draft-write` node produces a version an agent cannot activate and
   the owner can.
3. Activating the active version again records nothing.
4. A run started before a new activation finishes on its pinned version.

### Consequence

Reading and computing cost the owner nothing; the moment a flow can change
something, the owner has chosen to let it.

## Accepted decision A07 — a disclosure class only rises, and agents see personal data as digests

Reuses cabinet-flow decision 03, narrowed by K-14: one class for every agent instead of
per-agent ceilings.

### Normative rules

1. Classes are ordered `open < business_confidential < personal_data`.
2. At proof time the class that can reach a node's output is: for an operation
   node, the class its binding declares for that output; for a function node, the
   highest class that can reach any of its inputs, `open` when it has none; for a
   flow input, the class its port declares; for a constant, the class the
   composing agent declared with it.
3. At run time a value's class is set by the one rule of M21: a flow input takes
   its port's class, a constant its declared class, a function output the highest
   class its execution actually received, a binding output the class the binding
   declares, a trial case's input its contract input port's class and its
   expected output the highest class of the case's inputs. No function, edge or flow construct lowers a class.
4. An agent never receives a `personal_data` value: wherever the surface would
   return one to an agent — run inputs and outputs, trial cases and executions,
   approval previews, trace records — it returns only the value's digest and class
   (K-14), and no `value_id`. The same holds for a `personal_data` file: an agent
   gets its digest and class, and not its size, media type or spool facts. The
   owner receives every value.
5. The class of an execution is the highest class among the values and files its
   NodeExecution or TrialExecution names as inputs, and for an operation also
   among its outputs; it is computed from those records, not stored. A
   `failure_detail` of an execution whose class is above `open` is returned to an
   agent only as its length and that class.

### Formal invariants

```text
class(function_output) = max(class(received_inputs)) OR open
proof_edge_valid -> reach_class(source) <= accepts(target_input)
value_to_agent AND class = personal_data -> (digest, class) only
lowers_class(any construct) -> never
```

### Required tests

1. A function that receives a `personal_data` value and returns an integer yields
   an output of class `personal_data`.
2. A path from a personal-data read through two functions into an input accepting
   `business_confidential` is refused by the proof.
3. An agent reading that run receives digests and classes for the personal-data
   values and content for the rest; the owner receives all content.
4. An agent reading the approval preview of such a node receives no personal-data
   value.

### Consequence

Client data cannot leave through a chain of innocent-looking functions, and no
agent ever holds it.
