# State 5 — Cabinet Flow operation-binding operations

A25 clock contract: every operational timestamp written by this module is KernelInstant M47 obtained from its injected `module:system_clock.now` at the atomic event it owns. No public operation accepts caller-, gateway- or surface-supplied current time.

Bindings give one exact manifest operation typed semantic ports without
changing what the manifest declares. Proposals may be authored by an agent;
only the owner can accept a version. Invocation remains a separate module.

## `public_op:operation_bindings.propose_binding`

### Owner

`module:operation_bindings` owns binding proposals and validation against exact
manifest facts.

### Callers

`module:kernel_surface` calls it from an authorized author request.

### Inputs

The ActorRef, exact ManifestOperationRef and digest, typed input/output
SemanticPorts, purpose, preview-port selection and, for a non-read operation,
an accepted read binding proposed as `outcome_read_binding_ref`. Effect class,
channel, replay and idempotency facts are not caller-authored.

### Outputs

An immutable proposed OperationBindingVersion whose identity is computed by
`module:identity`, with manifest-owned facts copied from
`module:manifest_reader`; or a complete typed refusal.

### Observable effect

One proposal/version may be appended. It remains non-invocable until owner
acceptance.

### Enforces

Ports name accepted term revisions and schemas; proposal facts match the exact
manifest digest; non-read bindings have preview ports and a same-service
accepted read binding for outcome reconciliation; agent text remains data.

### Errors

Missing operation, stale digest, caller contradiction of manifest facts,
invalid ports, effectful binding without preview/outcome-read, wrong-service or
non-read reconciliation binding and caller-supplied version identity are
refused.

### State impact

Only immutable proposal/version records may be appended; binding status,
manifest and service state are unchanged.

## `public_op:operation_bindings.accept_binding_version`

### Owner

`module:operation_bindings` owns the owner-only transition that makes one exact
binding version usable.

### Callers

`module:kernel_surface` calls it from an authorized `owner_decide` request.

### Inputs

The active owner ActorRef, exact binding/version references, expected proposed
status, and the kernel-generated owner statement naming service, operation,
purpose, effect class, accepted disclosure classes and preview ports.

### Outputs

The accepted binding/version and immutable acceptance record, or a typed
refusal with proposal status unchanged.

### Observable effect

The exact version becomes accepted atomically and may thereafter be pinned by
new flow versions.

### Enforces

Owner-only decision, current manifest equivalence, complete effectful safety
fields, exact generated statement, compare-and-set and no acceptance inherited
by another version.

### Errors

Non-owner or suspended owner, stale/non-proposed version, manifest drift,
incomplete safety fields, altered statement and concurrent decision are
refused without partial acceptance.

### State impact

One binding version receives an immutable accepted decision; no invocation,
flow activation, approval or grant is created.

## `public_op:operation_bindings.binding_for_invocation`

### Owner

`module:operation_bindings` owns the authoritative invocability view for one
exact pinned binding version.

### Callers

`module:run_executor` calls it while pinning a run;
`module:operation_invoker` calls it immediately before an operation attempt.

### Inputs

Exact binding and binding-version references pinned by the FlowVersion, plus
the configured manifest revision used for the mandatory drift check. No latest,
fallback or caller-selected replacement version is accepted.

### Outputs

The accepted, non-suspended immutable binding version with exact ports,
manifest facts, preview/outcome-read references and digest; otherwise an
explicit non-invocable reason.

### Observable effect

It may trigger the same deterministic drift evaluation as the sweep and append
required suspension or immaterial-reissue evidence. It invokes no service.

### Enforces

Exact pinned version, accepted status, not retired, no material manifest drift,
and no silent upgrade from a suspended or older version.

### Errors

Unknown/mismatched version, proposed or retired status, absent manifest
operation, material drift and unavailable manifest evidence refuse invocation;
no stale cached success is returned.

### State impact

Only drift-owned binding status/reissue records may change. Runs and services
are not changed by lookup.

## `public_op:operation_bindings.sweep_manifest_drift`

### Owner

`module:operation_bindings` owns deterministic reconciliation of all accepted
bindings with the configured manifest revision.

### Callers

`module:bootstrap` calls it before gateways open;
`module:operation_invoker` calls the bounded exact-binding form before sending.

### Inputs

Configured manifest revision and either all accepted bindings or one exact
binding/version. Material fact classification is fixed by A10 and cannot be
configured by the caller.

### Outputs

A deterministic report per binding: unchanged, suspended because absent or
materially changed, or automatically reissued for an immaterial digest change,
with old/new digests and exact changed facts.

### Observable effect

Material drift appends suspension; immaterial digest change appends an
identical-ports version tied to the new digest while keeping the binding
accepted. Unchanged bindings produce no write.

### Enforces

Channel, effect class, replay, idempotency key and preconditions are material;
uncertain comparison is fail-closed; every mutation is atomic and auditable;
suspended bindings invoke nothing.

### Errors

Unavailable/malformed manifest, unknown prior digest, comparison failure and
transaction failure stop the affected binding from being reported safe. Startup
cannot serve after an incomplete all-binding sweep.

### State impact

Append-only suspension or automatic reissue records and current binding status
may change; manifest, flows and grants are not rewritten.

## `public_op:operation_bindings.retire_binding`

### Owner

`module:operation_bindings` owns the final binding retirement transition.

### Callers

`module:kernel_surface` calls it from an authorized authoring request.

### Inputs

The ActorRef, exact binding identity, expected current status/version and a
bounded retirement reason. `module:operation_bindings` obtains `retired_at` as
KernelInstant M47 from its injected `module:system_clock.now` at the successful
compare-and-set. No caller-, gateway- or surface-supplied current time is
accepted.

### Outputs

The retired binding record or a typed refusal. Exact repetition may return the
existing retirement but cannot rewrite its actor, time or reason.

### Observable effect

The binding becomes unavailable to new flow versions and invocation. Existing
versions, proofs, runs and traces remain evidence.

### Enforces

Authoring permission, final lifecycle transition, compare-and-set, immutable
history and no cascade deletion or substitution.

### Errors

Actor without authoring permission, unknown binding, stale expected state,
conflicting repeat and transaction failure are refused atomically.

### State impact

Exactly one binding lifecycle status changes to retired; no manifest record,
FlowVersion, run, approval or historical binding version is deleted.

