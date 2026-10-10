# State 5 — Cabinet Flow whole-graph proof operation

A25 clock contract: every operational timestamp written by this module is KernelInstant M47 obtained from its injected `module:system_clock.now` at the atomic event it owns. No public operation accepts caller-, gateway- or surface-supplied current time.

Proof judges one immutable flow version against exact accepted evidence. It
does not repair, suggest, activate or execute the graph, and no actor can supply
or override its verdict.

## `public_op:flow_proof.prove_flow`

### Owner

`module:flow_proof` owns the complete deterministic proof required by A02, A03
and A04, including every finding and its stable ordering.

### Callers

`module:flow_registry` calls it after registering one immutable FlowVersion and
before considering that version for activation.

### Inputs

One exact FlowVersion reference. The operation resolves every pinned function
contract through `module:slot_registry.contract_version`, accepted
operation-binding versions through `module:operation_bindings`, and the exact
accepted semantic term and relation revisions through
`module:semantic_vocabulary`. The caller
cannot provide a verdict, suppress a check, substitute a newer dependency or
ask the proof to choose an edge basis.

### Outputs

One immutable FlowProof containing the flow-version identity, complete
`vocabulary_basis`, `proven` or `refused` verdict, deterministically ordered
findings, derived disclosure class for every function output, and the highest
effect class of the pinned operation nodes. A refused proof reports every
finding rather than stopping at the first.

### Observable effect

The operation appends one content-consistent proof result or returns the
existing equivalent proof for the same flow version and vocabulary basis. It
does not create a FlowActivation and invokes no node.

### Enforces

Every function node pins an existing contract version whose owning Slot is
active at proof time, every operation node pins an accepted binding version;
every edge has exact-term or accepted-relation evidence with schema acceptance
without coercion; conversion and resolution relations require their declared
function node; byte-stream carriage, media types and ceilings match;
cardinality and `map_over_port` agree; disclosure classes only propagate upward
and fit target ceilings; every required input is supplied exactly once; the
graph is acyclic; every pure node reaches a flow output; guards use closed
values; and no required output can remain behind a guard.

### Errors

Findings include unknown or unaccepted pins, `edge_without_basis`, invalid or
retired relation, conversion without its required slot, `shape_incompatible`,
carriage/media incompatibility, `cardinality_incompatible`,
`disclosure_exceeded`, missing or multiply supplied input, cycle,
`unreachable_node`, `guard_on_open_value`, invalid map and
`required_output_behind_guard`. Unavailable evidence refuses proof; it never
becomes a warning-only success.

### State impact

Only an immutable FlowProof may be appended. The FlowVersion, vocabulary,
contracts, bindings, activations and service state remain unchanged. A binding
suspended later does not rewrite the proof; invocation availability is checked
at run time by its owning modules.

