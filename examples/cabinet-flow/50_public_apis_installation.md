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

`module:bootstrap` reads and validates the complete record once during
fail-closed startup and injects that same immutable M48 value into every
consumer.

### Inputs

None. The operation reads the ReleaseCeilings M48 record shipped with the exact
running kernel release. No category selector, host override or per-flow value is
accepted.

### Outputs

Exactly one ReleaseCeilings M48 value containing the complete release-v1 limits
for sandbox resources, code/value/fixture/spool sizes, surface/text/pagination
bounds and transport timeout.

### Observable effect

None.

### Enforces

The returned fields exactly equal the M48 values of the running release; every
field is positive and internally consistent; callers cannot raise, replace or
partially select ceilings; runtime images and dependency versions are pinned.

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

## `public_op:installation.load_installation`

### Owner

`module:installation` owns the one reading of the operator-written protected
configuration.

### Callers

`module:bootstrap`, first of all startup work.

### Inputs

The installation identity the operator started the process for and the
reference of the protected configuration file. Nothing from a request, a flow
or a record.

### Outputs

The installation facts the rest of startup needs: installation identity, owner
identity and display name, the data directory and the host state directory.
No secret, no credential
binding and no manifest detail.

### Observable effect

The file is read and validated once and its content is kept for this process;
no kernel record is written.

### Enforces

The closed format of `rules.installation_configuration`: exactly the declared
keys, a file mode no wider than the declared one, an absolute data directory,
an installation identity equal to the one started, a secret location per
credential binding and exactly one purpose per binding (A29). A second loading
in the same process is refused.

### Errors

Missing or unreadable file, wider file mode, unknown or missing key, identity
mismatch, relative path and malformed binding are one typed startup refusal
without host path or secret.

### State impact

None in the kernel store.
