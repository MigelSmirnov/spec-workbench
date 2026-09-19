# State 2 — Cabinet Flow run, trace and retention rules

## Accepted decision A16 — a run pins everything it will execute when it is created

### Normative rules

1. A FlowRun M40 is created from one FlowActivation M37, by default the flow's
   latest. Creation pins the flow version, its proof, the SlotActivation M27 of
   every function node, the binding version of every operation node and the
   ServiceTarget M39 of the installation.
2. Creation validates every supplied flow input against its port's schema, term
   and disclosure class, and refuses the run before any node executes when one
   fails or a required input is missing.
3. Creation is refused when a function node's contract version is unserved,
   when a pinned binding is not `accepted`, when the flow is retired, or when
   the initiating delegation is not active.
4. Nothing recorded after creation changes what the run executes: not a new
   slot activation, a new flow activation, a vocabulary change or a
   reconfigured installation. Only a binding suspension can stop it, and it
   stops; it never substitutes another version.
5. A run is started by the owner or by an agent under an active delegation.
   The initiator is recorded and never changes. Material from an outside sender
   enters only as input values that the initiator supplies, with the sender
   recorded inside the data's provenance.
6. Two runs of the same flow version on equal inputs are two runs. Protection
   against a duplicate effect is the operation's idempotency under A14, not a
   deduplication of runs.

### Formal invariants

```text
run_created
-> pinned(flow_version, proof, slot_activations, binding_versions, service_target)
   AND all_inputs_valid

later_change -/> alters(pinned_set(run))
binding_suspended -> run_stops_at_node AND no_substitution
```

### Required tests

1. A run created before a new slot activation executes the earlier
   implementation throughout, including after a long wait for approval.
2. A run with an input of the wrong term revision or above the port's
   disclosure class is refused with no node executed.
3. A run of a flow pinning an unserved contract version is refused at creation.
4. Reconfiguring the installation's target while a run waits does not change the
   instance that run reaches.
5. Two runs on equal inputs have distinct identities and distinct traces.

### Consequence

A run means one thing from start to finish, so its trace can always be read
against exactly what it executed.

## Accepted decision A17 — execution follows the data, and a failure stops only its dependants

### Normative rules

1. A node becomes ready when every one of its input edges has delivered a
   validated value or has been disabled by its guard. Ready nodes with no data
   dependency between them may execute concurrently.
2. A value is validated against the source port before it leaves a node and
   against the target port before it enters one. A violation on output concludes
   the source node as `contract_violation`; a violation on input concludes the
   target node as `contract_violation`. In neither case is the value delivered.
3. A node with `map_over_port` executes once per element, each element with its
   own NodeExecution M41 and `map_index`. Its outputs are collected in element
   order. The mapped node succeeds only when every element succeeded.
4. An edge with a guard delivers only when the source node's named output
   equals the guard value. A node with any disabled required input edge
   concludes `skipped_by_guard`, and so, transitively, does every node that
   requires its outputs.
5. When a node concludes in any failure status, every node that requires its
   outputs concludes `not_executed_upstream_failed`. Nodes with no dependency on
   it continue to their own conclusion.
6. An effectful operation node never executes ahead of a failed or unknown
   upstream it depends on, and is never executed speculatively.
7. A run is `succeeded` when every node concluded `succeeded` or
   `skipped_by_guard` and every non-optional flow output was produced and
   validated. It is `failed` when any node concluded in a failure status and no
   node is still waiting or executable. It is `refused` when the owner denied an
   approval.
8. A `failed` run reports, per flow output, whether it was produced. A partially
   produced result is returned as partial and labelled so; it is never presented
   as the flow's result.
9. No node executes twice within one run except as a recorded further attempt
   under A14 or A18.

### Formal invariants

```text
node_ready <-> for_all input_edge: delivered_valid OR guard_disabled

value_delivered -> valid_at_source_port AND valid_at_target_port

node_failed -> for_all dependant: not_executed_upstream_failed
guard_disabled(required_input) -> skipped_by_guard   (transitive)

run.succeeded
<-> for_all node: status IN {succeeded, skipped_by_guard}
    AND for_all non_optional_output: produced_and_valid
```

### Required tests

1. A function returning an extra or mistyped field concludes
   `contract_violation` and its dependants do not execute.
2. A duplicate-check node whose guard disables the save branch yields
   `skipped_by_guard` on the save node and a `succeeded` run with its optional
   output absent.
3. One failing element of a nine-element map fails the mapped node, keeps nine
   separate node executions, and leaves an effectful dependant unexecuted.
4. With two independent branches, a failure in one lets the other conclude and
   the run ends `failed` with the produced output labelled partial.
5. No effectful node executes when any node it depends on is failed, unknown or
   waiting.

### Consequence

Bad data never travels one step further than the node that produced it, and the
kernel never does more than it can stand behind.

## Accepted decision A18 — waiting is truthful and survives restart

### Normative rules

1. A run rests `awaiting_approval` for the owner, or `pending` with a recorded
   reason: `service_unreachable`, `binding_suspended` or `outcome_unknown`.
   `waiting_on` names every node and reason. Independent branches keep executing
   while others rest.
2. A wait has no timeout. Time alone never approves, denies, fails or completes
   anything. Only the owner cancels.
3. Every state needed to resume a run is durable before it is acted on: node
   executions as they conclude, approvals as they are decided, in-flight effect
   attempts before the call.
4. On restart the kernel resumes every non-terminal run from its records. A
   function node with no concluded execution is executed again; this is safe
   because it is pure. An operation node with an in-flight record and no
   concluded execution is concluded `outcome_unknown` and reconciled under A15.
   A `read` operation with no concluded execution is invoked again.
5. A supplied input, an approval and a produced value are never lost by a
   restart or by a service being away. Work waiting for an absent service is
   reported as waiting, never as done and never as failed.
6. Cancellation by the owner is final. It stops further execution, leaves every
   concluded node execution in place, and records whether any effect's outcome
   was still undetermined.
7. The owner is shown, in one place, every run that is waiting for the owner and
   every run that is waiting for a service, with the plain-words reason.

### Formal invariants

```text
wait_elapsed -/> state_change
resume_after_restart -> from_durable_records_only

restart AND in_flight_effect_without_conclusion -> outcome_unknown
restart AND function_without_conclusion -> execute_again

service_absent -> run.status = pending   (never succeeded, never failed)
```

### Required tests

1. With the local service down, a flow needing it rests `pending`, its
   independent read branch completes, and the run completes after the service
   returns without any input being supplied again.
2. Restarting the kernel while a run is `awaiting_approval` preserves the
   preview, and approval afterwards performs the effect once.
3. Restarting during a function execution re-executes it and yields the same
   output digest.
4. Restarting during an effectful call yields `outcome_unknown` and
   reconciliation, not a second call.
5. A cancelled run executes nothing further and keeps its trace.

### Consequence

The owner can switch a machine off, lose a connection or take a week to answer,
and what was sent is still there, in the state it was truly in.

## Accepted decision A19 — the trace is immutable data without secrets

### Normative rules

1. Every concluded attempt to execute a node writes exactly one NodeExecution
   M41. The record is append-only: no operation edits or deletes one, and a
   further attempt is a further record.
2. `succeeded` is written only after the node's outputs validated. There is no
   default status and no status inferred from the absence of an error.
3. A record names what executed by identity — the Implementation M23 and runtime
   revision, or the binding version and service instance — so the trace never
   depends on what is current.
4. Inputs and outputs are recorded by StoredValue digest with term, schema and
   disclosure class. The trace holds no source bytes, no credential, no token,
   no header value and no unbounded text. `failure_detail` is bounded and is
   scrubbed of any value above `open` class.
5. Reading a trace follows A03: an agent receives content at or below its
   ceiling and digest, term and class above it. The owner reads everything.
6. For slot repair an authoring agent receives the recent node executions and
   trial executions of that one slot, within its ceiling. It does not receive
   the traces of other slots in the same run.
7. The trace is the only source the kernel uses to explain, reproduce or resume.
   Process logs are operational diagnostics, contain no business value, and are
   never an input to a kernel decision.

### Formal invariants

```text
node_attempt_concluded -> exactly_one_node_execution_written
node_execution -> immutable

status = succeeded -> outputs_validated
secret OR source_bytes IN trace -> never
```

### Required tests

1. No surface or internal operation can alter a written node execution.
2. A function that raises after printing a secret-shaped string leaves a
   bounded `failure_detail` with no such string.
3. A reproduced function execution from a trace record yields the recorded
   output digest.
4. An agent repairing one slot cannot read node executions of another slot in
   the same run.
5. Deleting process logs changes no kernel behavior and loses no run.

### Consequence

The trace is the system's memory of what it did. It can be trusted because
nobody, including the kernel, can rewrite it.

## Accepted decision A20 — the kernel keeps evidence, not business data

### Normative rules

1. The kernel's operational store holds only the records of States 1 M01–M45.
   It holds no copy of a microservice's business record beyond the bounded
   values that crossed an edge.
2. The store keeps no file except trial fixtures. A file at rest belongs to its
   owning service and travels as a SourceReference M13. A file in flight is
   SpooledBytes M46: whatever node produces it — an operation reading it from a
   service or a function generating it — the kernel takes it into the run's
   spool, computes its digest and observes its size and media type from the
   bytes, and delivers it from the spool to the next node. Approval of an effect
   under A12 covers that digest, so it happens after the file exists and before
   it is sent, and the owner's preview shows the file itself. The spool is
   emptied when the run reaches a terminal state and is bounded per run;
   exceeding the bound fails the producing node as `contract_violation` with
   reason `value_too_large`. A file the business must keep is handed by an
   operation node to the service that owns it before the run ends.
3. A StoredValue M38 has a size ceiling fixed by the kernel release. A value
   above it fails the producing node as `contract_violation` with reason
   `value_too_large`; large data belongs behind a reference in its service.
4. Retention by class: `trial_corpus` and `approval_evidence` are kept for the
   life of the installation. `run_evidence` content is removed 90 days after the
   run ended; content of class `personal_data` is removed 30 days after the run
   ended. Removal deletes the bytes and keeps the digest, term, schema and class
   in every record that named them.
5. Content of a non-terminal run is never removed, whatever its age.
6. Removal never alters a NodeExecution, approval or proof. A trace whose
   content expired still shows what ran, on which digests, with which verdicts.
7. A value is stored once per digest. Its retention is the longest required by
   any record that names it.
8. The store is backed up as one unit. A restored store resumes runs under A18;
   effects whose conclusion post-dates the backup are found as in-flight or
   missing and reconciled under A15 rather than repeated.

### Formal invariants

```text
store_contents SUBSET_OF {M01..M45 records, bounded stored values}
source_bytes IN store -> never

content_removed(value) -> digest_and_metadata_retained
run.non_terminal -> content_retained

retention(value) = max(retention(record) for record naming value)
```

### Required tests

1. A flow that reads a photo from one service, normalizes it in a function and
   gives it to another service holds both files in the run's spool only, shows
   the owner the file and digest about to be sent, sends exactly those bytes,
   and leaves no bytes after the run ends.
2. A node output above the size ceiling fails with `value_too_large`.
3. After the retention period a run's trace is readable with digests and
   verdicts, and its expired content is absent.
4. A value named both by an expired run and by a trial case stays present.
5. A run waiting for approval for longer than the retention period keeps all its
   content.
6. Restoring an older backup reconciles, and does not repeat, an effect that was
   applied after the backup.

### Consequence

The kernel can always explain itself and can never become a second, stale copy
of the business.

## Accepted decision A25 — kernel wall time has exactly one source

### Normative rules

1. Every operational timestamp in State 1 is KernelInstant M47. Business event
   time remains TemporalValue M08 and is never filled from the kernel clock.
2. The only production code allowed to read host wall-clock time is
   `module:system_clock`. Its `now()` implementation takes exactly one sample
   with Python `time.time_ns()` and returns
   `KernelInstant(epoch_us = sample_ns // 1_000)`.
3. No other module may call or import a wall-clock source for a domain decision
   or persisted timestamp: `datetime.now`, `datetime.utcnow`,
   `date.today`, `time.time`, `time.time_ns`,
   `time.clock_gettime(CLOCK_REALTIME)` and equivalent framework helpers are
   forbidden outside `system_clock`.
4. A module that owns a record with a timestamp receives `system_clock` as an
   injected dependency and calls `now()` at the atomic event it owns. Public
   requests, gateways and `kernel_surface` never supply "current time" to a
   deep operation.
5. A trusted internal module may pass an already-created KernelInstant as
   evidence of an earlier event, for example a node-attempt start time. Such a
   value must originate from `system_clock.now()`; it is not reinterpreted as
   current time.
6. Retention, retry/back-off, throttling and lifecycle arithmetic belong to the
   consuming module. `system_clock` performs no policy arithmetic and elapsed
   time alone never authorizes an effect or changes a decision.
7. Local elapsed-duration enforcement is separate from wall time.
   `sandbox_supervisor` and `service_transport` may use only
   `time.monotonic_ns()` for non-persisted timeout measurement. A monotonic
   reading is never stored as KernelInstant and never participates in domain
   ordering across restart.
8. Tests inject a deterministic clock. Tests that exercise time-dependent
   behavior advance that clock explicitly; sleeping and monkeypatching global
   wall-clock functions are not accepted as the semantic oracle.
9. A timestamp produced by a microservice, manifest-declared operation or
   external system is never KernelInstant merely because it represents an
   instant. It remains typed business/service data, normally TemporalValue M08
   when it participates in semantic composition, or exact service-owned
   concurrency/precondition evidence when an API contract uses it that way.
10. Service/application clocks are outside the kernel clock trust boundary.
    Their values never supply kernel `now`, operational record timestamps,
    retry/back-off deadlines, retention expiry, authentication throttling,
    approval/grant authority or run lifecycle time.
11. The kernel never corrects, normalizes against, synchronizes with or assumes
    bounded skew between service clocks. Cross-service causal ordering is not
    inferred from comparing service timestamps. Causality comes from pinned
    versions, immutable references, digests, invocation/reconciliation evidence
    and explicit semantic relations.
12. When a binding exposes a service timestamp as an input/output/precondition,
    `service_transport` carries its exact declared representation and
    `operation_invoker` validates it against the binding. Neither converts it
    to M47. If business logic intentionally compares temporal facts, that occurs
    as typed TemporalValue semantics under the vocabulary/flow proof, not as
    kernel wall-clock authority.

### Formal invariants

```text
kernel_timestamp -> KernelInstant
KernelInstant.source -> system_clock.now

host_wall_clock_read
-> module = system_clock
   AND primitive = time.time_ns

current_time_request_field -> forbidden

service_timestamp -/> KernelInstant
service_timestamp -/> kernel_now
service_timestamp -/> retry_deadline
service_timestamp -/> retention_deadline
service_timestamp -/> authority

cross_service_ordering
-/> inferred_from(service_timestamp_comparison)

persisted_monotonic_value -> never

elapsed_timeout_measurement
-> module IN {sandbox_supervisor, service_transport}
   AND primitive = time.monotonic_ns
```

### Required tests

1. Static source audit fails when any generated module other than
   `system_clock` calls `datetime.now`, `utcnow`, `date.today`,
   `time.time`, `time.time_ns` or another realtime-clock helper.
2. Static source audit fails when `system_clock.now` does not use exactly one
   `time.time_ns()` sample or returns a float/string/naive datetime instead of
   integer-microsecond KernelInstant.
3. Static source audit permits `time.monotonic_ns()` only in
   `sandbox_supervisor` and `service_transport`, and rejects other monotonic
   or performance-clock APIs as sources of persisted/domain time.
4. A fixed injected clock yields byte-for-byte identical operational timestamps
   for the same deterministic test sequence.
5. Advancing the injected clock across retry and retention boundaries changes
   only the owning module's time-dependent decision; it never changes approval
   authority, semantic meaning or pinned execution identity.
6. A request containing a field intended to override current time is rejected
   by its strict schema.
7. A service response containing a timestamp far in the future or past does not
   change kernel retry, retention, authorization, run state or any operational
   record timestamp.
8. Two services may return mutually inconsistent wall-clock timestamps without
   changing kernel causal ordering; the kernel orders only by its own records
   and explicit references/evidence.
9. A service-owned optimistic-concurrency timestamp/precondition is replayed
   exactly according to its binding contract and is never converted to M47.

### Consequence

Generated modules have no freedom to invent their own clock. There is one wall
time representation, one production wall-clock primitive and one dependency
through which every owning module obtains it.

