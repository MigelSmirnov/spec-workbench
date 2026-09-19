# State 5 — Cabinet Flow operation-invoker operations

A25 clock contract: every operational timestamp written by this module is KernelInstant M47 obtained from its injected `module:system_clock.now` at the atomic event it owns. Retry timing belongs to `module:run_executor`; this module never invents wall time.

The invoker performs one pinned operation node safely. It neither schedules the
graph nor decides when owner approval is required. Unknown outcomes remain
unknown until validated service-owned evidence resolves them.

## `public_op:operation_invoker.invoke_operation`

### Owner

`module:operation_invoker` owns replay-safe invocation, idempotency-key
derivation, durable in-flight ordering, response validation and the exact
operation-attempt conclusion required by A14.

### Callers

`module:run_executor` calls it for one ready operation node or one mapped
element after inputs are validated and any required authority is resolved.

### Inputs

The exact run/node/element and attempt identities; pinned accepted binding
version and ServiceTarget; validated input StoredValue or spooled-file
references with digests; and, for an effect requiring authority, the exact
approval or standing-grant authorization bound to those inputs. No service
address, replay policy, idempotency key, credential or retry permission is
caller-authored.

### Outputs

One immutable attempt conclusion: validated successful outputs,
`operation_refused` with bounded structured reason, `service_unreachable`,
deterministic failure, or `outcome_unknown`; plus key digest and transport
evidence sufficient for trace and recovery. Success is impossible before every
output validates against the binding ports.

### Observable effect

For a non-read operation, the invoker first durably records the exact in-flight
attempt, then sends one bounded request through `module:service_transport` and
returns the exact attempt conclusion to `module:run_executor`. A read needs no
in-flight effect record. The immutable NodeExecution is appended separately by
`module:trace_journal`; a service may change state only through the declared
operation.

### Enforces

Binding remains accepted and non-suspended; target and input digests match the
run pins and authorization; idempotency key is derived only from declared ports;
`safe`, `refuses`, `returns_existing`, `overwrites` and `duplicates` replay
rules are exact; duplicates runs at most once per approval; overwrites reuses
only identical approved input; redirects and unvalidated responses are never
used.

### Errors

Suspended binding, unavailable authority, changed input, missing durable
in-flight write, transport definitely-not-sent/possibly-sent failure, timeout,
oversized response, schema/semantic output failure and service refusal produce
their exact typed conclusion. Ambiguity after possible send is always
`outcome_unknown`, never guessed success or failure.

### State impact

Only the durable in-flight attempt bookkeeping owned by invocation may change
here. `module:run_executor` owns the run transition and hands the returned
conclusion to `module:trace_journal` for the one immutable NodeExecution;
unknown outcomes trigger no automatic second effect.

## `public_op:operation_invoker.reconcile_outcome`

### Owner

`module:operation_invoker` owns reconciliation of one exact unknown non-read
attempt through the binding's declared service-owned read operation, as required
by A15.

### Callers

`module:run_executor` calls it while resuming or advancing a run that rests
`pending` with reason `outcome_unknown`.

### Inputs

The exact unknown attempt, original pinned binding and inputs, key digest,
declared accepted `outcome_read_binding_ref`, pinned ServiceTarget and previous
reconciliation evidence. Free-text service errors and caller assertions are not
accepted as outcome evidence.

### Outputs

One immutable OutcomeReconciliation with determination `effect_applied`,
`effect_not_applied` or `still_undetermined`, the validated read-operation
evidence, and—only for `effect_applied`—outputs validated against the original
effect binding's output ports.

### Observable effect

The operation invokes only the declared read binding and appends reconciliation
evidence. It never repeats the original effect. It performs one reconciliation
attempt only; retry timing and bounded back-off while the run remains pending
belong to `module:run_executor`.

### Enforces

Same run/node/element/attempt and key; outcome read belongs to the same service
and is accepted/non-suspended; determinations derive only from its validated
closed output; applied outputs satisfy the original binding; dependants execute
only after `effect_applied`; reattempt is possible only after confirmed
`effect_not_applied` and under A14, with fresh owner approval for `duplicates`.

### Errors

Missing or invalid outcome-read binding, unreachable read service, suspended
binding, malformed/oversized response, ambiguous closed result and output
validation failure produce `still_undetermined` or a typed reconciliation
failure while preserving the unknown state. Service free text never resolves
the outcome.

### State impact

One append-only OutcomeReconciliation may be recorded and, when applied, the
validated node conclusion is returned to `module:run_executor`. The original
in-flight/unknown evidence remains; the run transition, immutable
NodeExecution and any later reattempt belong to their owning modules.

