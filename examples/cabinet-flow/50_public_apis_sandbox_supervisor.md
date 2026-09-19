# State 5 — Cabinet Flow sandbox-supervisor operations

The sandbox supervisor executes untrusted function code and nothing else. It
owns isolation, external resource enforcement, denied-attempt evidence and
confirmed cleanup; semantic contract validation, admission, run scheduling and
activation remain outside the sandbox boundary.

## `public_op:sandbox_supervisor.execute_function`

### Owner

`module:sandbox_supervisor` owns one disposable execution of one exact
implementation under one exact SandboxRuntimeRevision and externally enforced
ResourceBounds.

### Callers

`module:admission` calls it once per active TrialCase while constructing trial
evidence. `module:run_executor` calls it for one ready function node or mapped
element of a real Run.

### Inputs

The exact immutable Implementation reference; exact sandbox runtime revision;
release-clamped ResourceBounds; one bounded set of already validated input
values; and file inputs whose bytes, observed media type and size have already
been accepted for their ports. The supervisor resolves the implementation's
contract, entry point and executable bytes only through
`module:slot_registry.implementation_record`; no caller supplies or substitutes
code bytes. In a real Run, files are delivered through
`module:run_spool`; a trial fixture remains a `StoredValue` of carriage
`byte_stream` and is supplied directly as a bounded read-only stream. No
credential, network target, host path outside the assigned exchange, clock,
entropy source, environment variable or kernel-store handle is an input.

### Outputs

One immutable sandbox-execution result containing collected bounded value
outputs and file-output streams/descriptors, runtime identity, enforced bounds,
resources used, all denied attempts, cleanup confirmation and one closed
execution outcome such as completed, `denied_attempt`, `timeout`,
`resource_exhausted`, `crashed` or `cleanup_failed`. A completed sandbox
result is not by itself a contract-conforming TrialExecution or successful
NodeExecution; the caller performs semantic/output validation.

### Observable effect

The supervisor creates one disposable environment containing only the runtime,
implementation and this execution's validated inputs; launches the code under
external limits; collects output over the bounded exchange; terminates every
descendant; and destroys the environment. For real-run file outputs it streams
the bytes into `module:run_spool` only after bounded collection. It performs
no service effect and writes no business state.

### Enforces

No ambient network, clock, entropy, credential or environment access; no
filesystem outside read-only inputs and the bounded scratch directory; process,
CPU, memory, wall-time, scratch and aggregate-output ceilings; every denied
attempt is observable and makes the execution non-successful even if code later
returns; file media type is observed from bytes rather than filename; no
truncation of oversized output; isolation between concurrent executions; and
identical implementation/input/runtime must be deterministic.

### Errors

Denied network/filesystem/process/clock/entropy/environment access, timeout,
resource exhaustion, crash, malformed exchange, oversized output, invalid
file-carriage/media envelope, collection failure and cleanup failure are closed
execution outcomes. On unconfirmed cleanup, all output is discarded and the
supervisor enters unhealthy state that refuses further execution until the leak
is cleared.

### State impact

No domain record is owned here. Ephemeral sandbox/process state exists only for
the execution. A real-run file may create temporary SpooledBytes through
`module:run_spool`; TrialExecution, StoredValue, NodeExecution, Run and
AdmissionVerdict records are appended only by their owning modules.

## `public_op:sandbox_supervisor.supervisor_health`

### Owner

`module:sandbox_supervisor` owns the authoritative readiness answer for the
execution isolation subsystem.

### Callers

`module:bootstrap` calls it during fail-closed startup before any gateway is
opened.

### Inputs

No caller-authored health status or override. The supervisor inspects its own
runtime-image readiness, execution backend and cleanup/leak state.

### Outputs

A bounded deterministic readiness result: healthy with the supported runtime
revisions needed by the installation, or unhealthy with a closed reason such as
unconfirmed cleanup, unavailable isolation backend or invalid runtime image.
No host path, process dump or credential is returned.

### Observable effect

None beyond bounded self-checks. The operation never clears a leak by assertion
and never starts a user execution.

### Enforces

Any previously unconfirmed sandbox or descendant cleanup keeps the supervisor
unhealthy; required runtime revisions must be verifiably available; health is
based on supervisor-owned evidence rather than a warning or caller override.

### Errors

Unavailable backend, unverifiable runtime, failed self-check or unresolved
cleanup is returned as unhealthy and therefore blocks kernel startup.

### State impact

None. Recovery of the underlying isolation subsystem is operational; the health
operation only reports whether new executions may safely be accepted.
