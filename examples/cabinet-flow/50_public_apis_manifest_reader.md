# State 5 — Cabinet Flow manifest-reader operations

The manifest reader is a read-only, revision-pinned projection. It reports what
the platform declares; `operation_bindings` decides what those facts mean for a
binding, and `installation` decides which instance the kernel targets.

## `public_op:manifest_reader.manifest_operation`

### Owner

`module:manifest_reader` owns parsing and digest-pinned projection of one
declared service operation.

### Callers

`module:operation_bindings` calls it while proposing a binding and during
drift checks before startup or invocation.

### Inputs

The configured manifest revision from `module:installation`, exact service and
operation identities, and optionally an exact expected manifest-record digest.
Arbitrary repository paths, revisions, queries and caller-authored operation
facts are not accepted.

### Outputs

A typed immutable operation projection containing service/operation identity,
the exact-file-byte manifest-record digest, channel, effect class, replay
behavior, opaque `string | null` idempotency-key declaration, preconditions and
optional non-normative manifest note. It contains no credential, typed-port
mapping, owner purpose or kernel binding policy.

### Observable effect

None; the manifest repository is read only.

### Enforces

Facts come from `<service_id>.json` at the configured immutable revision and
the digest is SHA-256 of its exact bytes; closed enums and required manifest
fields are validated; effect/replay/idempotency facts are reported verbatim
rather than inferred or repaired.

### Errors

Absent service or operation, digest mismatch, malformed record, unknown closed
value, duplicate identity and unavailable configured revision are explicit
typed refusals. No nearest-name or latest-revision fallback is permitted.

### State impact

None.

## `public_op:manifest_reader.operation_facts_changed`

### Owner

`module:manifest_reader` owns deterministic comparison of invocation-relevant
facts between two exact manifest operation records.

### Callers

`module:operation_bindings` calls it when sweeping accepted bindings after a
manifest change and before invocation.

### Inputs

Exact service and operation identities, prior and current manifest-record
digests. The prior digest is resolved only among committed versions of the same
service-record path in ancestors of the configured revision. A caller cannot
select a path, branch or which fields count as material.

### Outputs

A typed comparison stating whether the operation is absent, materially changed
or digest-changed-with-equivalent-invocation-facts, plus the exact changed fact
names among channel, effect class, replay, idempotency key and preconditions.

### Observable effect

None. It neither suspends nor reissues a binding.

### Enforces

Closed material-fact set, exact digest provenance, deterministic field-by-field
comparison and distinction between operation-local material change and edits to
unrelated service facts.

### Errors

Unknown or ambiguous prior digest, malformed either record, mismatched
service/operation identity and unavailable manifest history are explicit;
uncertainty is never reported as “unchanged”.

### State impact

None; suspension or automatic reissue belongs to
`module:operation_bindings`.

## `public_op:manifest_reader.service_instance`

### Owner

`module:manifest_reader` owns the typed projection of one manifest-declared
service instance.

### Callers

`module:operation_bindings` calls it to show and validate the installation's
selected instance while connecting an operation.

### Inputs

The configured manifest revision, exact service identity and exact instance
identity selected by `module:installation`. A request cannot provide a base
address, alternate instance or environment override.

### Outputs

A typed immutable instance projection containing service/instance identity,
exact-file-byte manifest-record digest, environment class and, when declared,
one `http_api` endpoint from `api_base_url` with required-header names. Both
credential-binding references and secret values are absent.

### Observable effect

None.

### Enforces

The instance belongs to the named service at the configured revision; routing
facts and environment class come only from the manifest; credentials come only
from installation configuration; redirects, inferred `mcp`/`operator`
endpoints and derived alternate hosts are not produced.

### Errors

Absent service or instance, service/instance mismatch, malformed endpoint,
unknown channel or environment class and unavailable revision are explicit
typed refusals.

### State impact

None; target selection belongs to `module:installation` and request execution
belongs to `module:service_transport`.
