# State 5 — Cabinet Flow trace-journal operations

A25 clock contract: `module:trace_journal` never reads host wall time. Any `started_at`/`ended_at` KernelInstant M47 stored in NodeExecution is trusted internal evidence produced by the run executor from `module:system_clock.now`.

The trace journal is the append-only evidence boundary for concluded node
attempts. It does not schedule work, validate business values, retain content or
act as a process log.

## `public_op:trace_journal.record_node_execution`

### Owner

`module:trace_journal` owns the one immutable NodeExecution M41 written for
each concluded attempt.

### Callers

`module:run_executor` calls it after the owning execution boundary has returned
a conclusion and every applicable input/output validation has completed.

### Inputs

The exact run/node/map-index/attempt identity; the pinned implementation or
binding identity; runtime or service-instance evidence; approval/grant reference
when applicable; exact input/output StoredValue or SpooledBytes digests;
validation verdicts; bounded resource and denied-attempt evidence;
`started_at` and `ended_at` as KernelInstant M47 trusted internal evidence
captured by `module:run_executor` through its injected clock; closed status and
failure reason; and bounded candidate failure detail. No process log,
caller-supplied timestamp, credential, secret header or unbounded service text
is accepted.

### Outputs

One immutable NodeExecution reference whose fields are normalized, ordered and
scrubbed for the disclosure rules of A19. Repeating the exact same write is
idempotent; a different attempt is a different record.

### Observable effect

Exactly one append-only NodeExecution may be written for the concluded attempt.
A success record is impossible until output validation has succeeded. The
journal never edits an earlier record to represent retry or reconciliation.

### Enforces

Exact run pins; one record per attempt identity; executed implementation,
runtime, binding and service identities are historical facts rather than current
lookups; `started_at <= ended_at`; both timestamps are KernelInstant M47 and
the journal never reads wall clock itself; status is explicit; output references
exist only after validation; failure detail is bounded and stripped of secrets
and values above `open`; credentials, tokens, source bytes and unrestricted
logs are never persisted.

### Errors

Duplicate attempt identity with conflicting content, missing pin/evidence,
success without validated outputs, invalid closed status, oversized or
unscrubbable failure detail and unavailable append-only storage are typed
failures. The operation never degrades to a log-only or partial trace record.

### State impact

One immutable NodeExecution is appended. Runs, StoredValues, spool files,
approvals, service state and earlier trace records are unchanged.

## `public_op:trace_journal.run_trace`

### Owner

`module:trace_journal` owns the disclosure-bounded ordered trace view for one
run.

### Callers

`module:kernel_surface` calls it from the fixed `inspect` operation when the
authenticated client asks for run trace evidence.

### Inputs

The exact run identity; resolved ActorRef and disclosure ceiling; bounded page
cursor and page size. The caller cannot request raw process logs, storage paths
or secret fields.

### Outputs

A deterministic chronological/pinned-attempt view of NodeExecutions for the
run. Value content is represented only through the StoredValue view allowed by
the actor's disclosure ceiling; above the ceiling or after retention expiry the
trace keeps digest, semantic term, schema and class. Partial pagination is
explicit.

### Observable effect

None.

### Enforces

Only records of the named run; stable ordering by node/element/attempt and
execution time tie-breaks; disclosure ceiling; immutable historical identities;
no credential, token, host path, process environment or unrestricted service
text; expired value content is not reconstructed.

### Errors

Unknown/invisible run, invalid cursor, unauthorized inspection and unreadable
trace evidence are explicit. A lower disclosure ceiling returns redacted
evidence rather than revealing record existence through alternate errors.

### State impact

None.

## `public_op:trace_journal.slot_evidence`

### Owner

`module:trace_journal` owns the slot-scoped evidence view used to repair a
function without revealing unrelated run activity.

### Callers

`module:kernel_surface` calls it from bounded inspection for an authoring
agent. `module:trial_corpus` calls it to verify that a requested
`captured_from_run` case names a concluded execution of the exact slot and to
obtain only the evidence needed for capture. `module:slot_activation` calls it
with a bounded exact-slot query when deriving whether the currently serving
implementation is `known_failing` on an active regression case.

### Inputs

The exact slot/contract-version identity; resolved actor/disclosure context;
optional exact NodeExecution reference for capture validation; bounded recency
or page cursor. The caller cannot broaden the query to neighboring slots or the
rest of each run.

### Outputs

A deterministic bounded view of NodeExecutions and related trial-execution
references for that slot only, with implementation/runtime identities, closed
outcomes, validation findings and value/file references reduced according to
the actor's disclosure ceiling. For exact capture validation it returns the
single matching immutable execution evidence or an explicit refusal.

### Observable effect

None.

### Enforces

Exact slot ownership; concluded attempts only; no unrelated nodes or run facts;
disclosure ceiling; immutable execution identity; capture evidence must match
the contract version and referenced node execution; health derivation receives
only evidence for the exact serving slot/implementation it names; secret-free
bounded failure detail.

### Errors

Unknown slot/execution, execution belonging to another slot or contract,
non-concluded attempt, unauthorized actor, invalid cursor and unavailable
evidence are explicit. The operation never falls back to whole-run trace access.

### State impact

None. Creating or withdrawing a trial case remains owned by
`module:trial_corpus`.
