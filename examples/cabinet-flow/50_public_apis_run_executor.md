# State 5 — Cabinet Flow run-executor operations

The run executor owns the durable dataflow state machine. It decides what is
ready, what waits and what may run next; it delegates isolation, service
invocation, authority, value/file storage and immutable trace recording to their
owning modules.

## `public_op:run_executor.create_run`

### Owner

`module:run_executor` owns creation of Run M40 with every execution choice
pinned before work begins.

### Callers

`module:kernel_surface` calls it from the fixed `run_flow` operation after
the actor and requested flow are authorized.

### Inputs

The resolved ActorRef; exact active flow reference or activation; and strict
typed values for every declared flow input. The caller cannot choose an
implementation hash, operation-binding version, service instance, credential,
runtime revision or hidden node input.

### Outputs

One durable Run reference with the exact flow activation/version/proof, pinned
slot activations, pinned accepted operation bindings, installation-selected
ServiceTarget, validated input StoredValue references, initiating actor and
initial status. No node is reported as concluded merely because the run exists.

### Observable effect

The operation resolves every function node's exact immutable contract through
`module:slot_registry.contract_version`, resolves and pins the serving
activation for that same contract, pins every accepted operation binding and
installation target, validates every supplied flow input at its declared
boundary, stores bounded input values through `module:value_store`, and
appends one Run. It performs no function execution or external service effect
itself.

### Enforces

Activated and non-retired proven flow; exact input set with no unknown or
missing required fields; serving implementation for every function node;
accepted non-suspended binding for every operation node; one installation
ServiceTarget; disclosure compatibility; immutable pins for the lifetime of the
run; no caller-authored identity or service target.

### Errors

Inactive/retired flow, incomplete proof, invalid input, unavailable serving
implementation, suspended/missing binding, unavailable installation target,
oversized value and transactional persistence failure refuse creation without a
partial Run.

### State impact

Exactly one Run and its accepted input-value references may be appended
atomically. Flow, activation, slot, binding and service records remain
unchanged.

## `public_op:run_executor.advance_run`

### Owner

`module:run_executor` owns readiness, mapping, guards, dependency failure
propagation and all truthful Run state transitions for one advancement pass.

### Callers

`module:kernel_surface` calls it after run creation and after a surface action
such as an owner decision can make work ready. The long-lived
`boundary:kernel_process` calls it for bounded pending-run wake-ups after the
executor's own back-off. Elapsed time itself is never authority and never a
state transition.

### Inputs

The exact non-terminal Run reference and a bounded wake reason. When evaluating
persisted retry/back-off deadlines, the executor calls its injected
`module:system_clock.now` and receives KernelInstant M47. All executable facts
are re-read from the Run's immutable pins and durable evidence; callers cannot
supply a ready-node list, success flag, approval result, retry decision, clock
value or alternate dependency.

### Outputs

The same Run with its new truthful status and waiting reasons, plus bounded
references to NodeExecutions and outputs appended during this pass. The pass
stops at a terminal state or when no further node can make immediate progress.

### Observable effect

For every data-ready node, the executor validates source and target ports,
applies exact guards and mapping, obtains current effect authority when needed,
delegates a function to `module:sandbox_supervisor` or an operation to
`module:operation_invoker`, stores validated outputs through
`module:value_store`, carries run files through `module:run_spool`, and asks
`module:trace_journal` to append exactly one NodeExecution per concluded
attempt. Independent ready branches may progress while another branch waits.

### Enforces

Data-driven readiness; single supply of each required input; source and target
validation; deterministic mapped-element order and one NodeExecution per
element attempt; guard semantics; no dependant execution after failed required
input; exact pinned implementations/bindings/target; owner approval bound to the
current effect inputs; no guessed result from an unreachable service or unknown
effect outcome; `succeeded` only after every required node/output satisfies
A17.

### Errors

Contract violation, sandbox failure, service refusal/unreachability, suspended
binding, denied approval, unavailable authority, value/file bound failure and
unknown outcome become their owned NodeExecution or Run waiting/failure state.
Infrastructure failure before an atomic unit commits leaves durable prior state
intact and is never translated into success.

### State impact

Run state, waiting reasons, stored output references and execution bookkeeping
may advance atomically with the owned records of collaborating modules. On a
terminal transition the executor asks `module:run_spool` to release the run's
temporary files. Earlier evidence is never rewritten.

## `public_op:run_executor.resume_runs`

### Owner

`module:run_executor` owns reconstruction and safe resumption of every
non-terminal Run after kernel restart.

### Callers

`module:bootstrap` calls it during fail-closed startup before either gateway
begins serving requests.

### Inputs

No caller-selected run list or recovery verdict. The executor reads all
non-terminal Runs and their durable pins, NodeExecutions, approvals, in-flight
effect attempts, reconciliations, values and waiting reasons from the
operational store.

### Outputs

A bounded recovery report for every non-terminal Run: resumed/progressed,
still-waiting with exact reason, terminal after recovery, or explicit recovery
failure. The report identifies unknown outcomes rather than resolving them by
assumption.

### Observable effect

A function attempt lacking a concluded NodeExecution may be executed again under
the same pinned pure runtime. A read operation lacking a conclusion may be
invoked again. A non-read operation with durable in-flight evidence and no
conclusion becomes `outcome_unknown` and is reconciled only through
`module:operation_invoker.reconcile_outcome`; validated reconciliation may
then permit further advancement.

### Enforces

Recovery from durable records only; no loss or re-supply of accepted input,
approval or value; no second effect while an earlier send may have happened;
same immutable pins as before restart; waiting has no timeout-generated
decision; service absence stays `pending`; owner approval stays
`awaiting_approval`.

### Errors

Unreadable/inconsistent durable evidence, missing immutable pin, unavailable
required store, impossible attempt numbering or reconciliation inconsistency
fails startup recovery for the affected Run and prevents fabricated progress.
Unknown remains unknown.

### State impact

Recovery may append missing truthful NodeExecution/reconciliation evidence and
advance Run state under the normal rules. It never rewrites pre-restart
evidence or silently creates replacement pins.

## `public_op:run_executor.cancel_run`

### Owner

`module:run_executor` owns the final owner-requested cancellation transition
of a non-terminal Run.

### Callers

`module:kernel_surface` calls it from the closed owner-decision operation
after resolving and authorizing the sole owner.

### Inputs

The active owner ActorRef, exact Run identity, expected non-terminal status and
bounded cancellation reason. A caller cannot mark an individual node succeeded
or erase an unknown effect outcome.

### Outputs

The exact Run in `cancelled` state with preserved waiting/unknown-outcome
evidence, or a typed refusal if cancellation cannot be applied.

### Observable effect

The Run becomes terminal and no new node attempt may start. Temporary run files
are released through `module:run_spool`; immutable trace, approvals,
reconciliations and evidence remain.

### Enforces

Owner only; compare-and-set against the expected non-terminal state; terminal
states are final; cancellation is not denial, rollback or evidence deletion;
an undetermined external effect remains explicitly undetermined in history.

### Errors

Non-owner/suspended owner, unknown Run, stale expected state, already-terminal
Run and concurrent transition are refused atomically without changing execution
evidence.

### State impact

Exactly one Run transitions to `cancelled` and temporary spool content is
released. No service compensation or business rollback is implied.

## `public_op:run_executor.run_status`

### Owner

`module:run_executor` owns the authoritative bounded status view of one Run.

### Callers

`module:kernel_surface` calls it for `run_flow` responses and fixed
inspection of a Run.

### Inputs

The exact Run reference, resolved ActorRef/disclosure context and bounded
request for current status. Raw store keys, trace-log paths and caller-authored
state interpretations are not accepted.

### Outputs

The current status, exact `waiting_on` node/reason set, pinned flow identity,
terminal timestamps when present, and bounded output/value references labelled
complete or partial. Content above the actor's ceiling is represented only by
permitted references/digests; detailed immutable attempt history comes from
`module:trace_journal`.

### Observable effect

None.

### Enforces

Truthful persisted state only; `pending`, `awaiting_approval`, `refused`,
`failed`, `cancelled` and `succeeded` remain distinct; partial outputs are
never presented as final; no timeout inference; disclosure ceiling and actor
scope apply to output references.

### Errors

Unknown/invisible Run, unauthorized actor, inconsistent persisted state and
unreadable required evidence are explicit. Missing evidence is never converted
to `succeeded`.

### State impact

None.
