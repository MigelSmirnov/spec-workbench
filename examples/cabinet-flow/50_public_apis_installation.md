# State 5 — Cabinet Flow installation operations

The installation boundary is host-controlled. These operations reveal only
typed configuration facts or a component-local credential handle; no request,
flow, binding or persisted record can select another target, secret or ceiling.

## `public_op:installation.manifest_revision`

### Owner

`module:installation` owns the one configured platform-manifest repository
revision used by this kernel process.

### Callers

`module:bootstrap` reads it during fail-closed startup;
`module:manifest_reader` uses it to pin every manifest projection.

### Inputs

No caller-controlled revision. The operation reads the protected installation
configuration established by the operator.

### Outputs

One immutable repository revision identifier and the configured manifest-root
reference needed by `module:manifest_reader`, without a host filesystem path or
credential.

### Observable effect

None.

### Enforces

Exactly one manifest revision per running kernel; requests and records cannot
override it; all service and operation facts in a run resolve from that pinned
revision.

### Errors

Missing, malformed, unavailable or unverifiable revision refuses startup or
manifest access. The operation never falls back to a moving branch or latest
revision.

### State impact

None.

## `public_op:installation.release_ceilings`

### Owner

`module:installation` owns immutable ceilings shipped with the exact kernel
release and accepted sandbox-runtime revisions.

### Callers

`module:bootstrap` validates them at startup; `module:slot_registry`,
`module:trial_corpus`, `module:sandbox_supervisor`, `module:value_store` and
`module:run_spool` apply the relevant resource, code, fixture, value and spool
limits.

### Inputs

An optional closed ceiling category. No caller-proposed override or per-flow
limit increase is accepted.

### Outputs

The typed bounded set of maximum execution time, memory, process count, code
size, output size, value size, trial-fixture size and run-spool size for the
installed release and runtime revisions.

### Observable effect

None.

### Enforces

Authored bounds may only be equal to or below release ceilings; runtime images
and dependency versions are pinned; withdrawing a runtime prevents its use in
new contracts without mutating existing evidence.

### Errors

Unknown category, missing release metadata, unsupported or digest-mismatched
runtime revision and internally inconsistent ceilings refuse closed. No
unbounded fallback is permitted.

### State impact

None.

## `public_op:installation.resolve_credential`

### Owner

`module:installation` owns protected host credential lookup and containment.

### Callers

`module:access_control` resolves channel credentials during authentication;
`module:service_transport` resolves a selected service credential immediately
before one request.

### Inputs

A credential-binding reference, expected credential purpose, channel or service
instance identity, and the calling component's closed kind. Raw credential
values, arbitrary secret names and host paths are not accepted.

### Outputs

A short-lived component-local credential handle usable only by the authorized
calling component for the stated purpose. The credential value is not
serializable, persistable or returnable through a public response.

### Observable effect

Protected host lookup may occur; no operational-store record is written and no
credential is logged, traced, previewed or placed in process arguments.

### Enforces

Purpose and target binding, least exposure, resolution at moment of use, no
credential in a function environment, and no leakage into errors or records.

### Errors

Unknown reference, purpose/target mismatch, unavailable protected store,
expired or malformed secret and unauthorized component are uniform typed
refusals containing no secret or host-location detail.

### State impact

None in the kernel store. Any protected-provider access audit remains outside
domain records and contains no credential value.

## `public_op:installation.resolve_service_target`

### Owner

`module:installation` owns the single selected manifest instance per service
and the prohibition on mixed production/non-production targets.

### Callers

`module:bootstrap` resolves all configured targets for startup validation;
`module:run_executor` resolves and pins required ServiceTargets when creating a
run.

### Inputs

An exact service identity from a pinned accepted binding or the startup request
to validate all configured services. Instance ID, base address, channel,
headers and environment class cannot be supplied by a flow or caller.

### Outputs

One ServiceTarget M39 containing the selected manifest instance identity,
class, declared channel and non-secret routing facts, tied to the configured
manifest revision. Credentials remain references resolved separately.

### Observable effect

None. Run creation may persist the returned ServiceTarget as part of the run's
pinned execution evidence.

### Enforces

One host-selected instance per service; target belongs to the pinned manifest;
all targets in the installation have a compatible production or non-production
class; redirects or request parameters cannot replace the target.

### Errors

Unknown service, missing selected instance, instance absent from the pinned
manifest, mixed environment classes, unsupported channel and invalid protected
configuration refuse startup or run creation before any node executes.

### State impact

None inside `module:installation`; the caller may embed the immutable resolved
target in a newly created run.

