# State 5 — Cabinet Flow value-store operations

A25 clock contract: retention-time comparisons use KernelInstant M47 from the injected `module:system_clock.now`; retention durations are module policy and no caller supplies current time.

The value store keeps bounded, content-addressed evidence values without
becoming a business database. Content visibility follows disclosure class, and
retention may remove bytes while preserving the identities needed to explain a
run.

## `public_op:value_store.put_value`

### Owner

`module:value_store` owns canonical storage, deduplication by digest, size
enforcement, disclosure metadata and retention-class accounting for StoredValue
M38.

### Callers

`module:run_executor` stores validated values produced or accepted by a run.
`module:trial_corpus` stores authored or captured trial values and the only
file bytes retained by the store: `byte_stream` trial fixtures.

### Inputs

Canonical bounded value bytes or a bounded trial-fixture stream; exact semantic
term revision and schema; carriage `value` or permitted trial
`byte_stream`; disclosure class; retention class; and the owning record
context that requires retention. A caller-supplied digest is never accepted as
identity authority.

### Outputs

The immutable StoredValue identity and metadata, including the kernel-computed
content digest, size, carriage, term/schema references, disclosure class and
effective retention requirement. Equal canonical bytes reuse the existing
stored content while adding any longer required retention reference.

### Observable effect

Content may be written once under its digest and one retention reference may be
added. The operation never writes a microservice business record and never
turns a run-spool file into durable content unless `module:trial_corpus`
explicitly captures it as a trial fixture.

### Enforces

Release size ceiling; canonical digest identity; exact accepted semantic and
schema references; `byte_stream` persistence only for trial fixtures;
retention equal to the longest live naming requirement; immutable metadata for
a digest; and no overwrite with different bytes.

### Errors

Oversized content, unsupported carriage, invalid semantic/schema reference,
non-trial durable file, digest collision/inconsistent existing metadata,
unreadable input stream and unavailable durable storage are typed refusals.
Partial content is never exposed as a StoredValue.

### State impact

One content object and/or one retention reference may be appended
idempotently. Existing StoredValue identity and content are never rewritten.

## `public_op:value_store.read_value`

### Owner

`module:value_store` owns disclosure-aware reads of StoredValue content and
metadata.

### Callers

`module:run_executor` reads pinned values needed to validate and execute the
next node. `module:trial_corpus` reads corpus values within the requesting
actor's ceiling. `module:kernel_surface` delegates fixed inspection/result
reads to the store.

### Inputs

An exact StoredValue reference; the resolved reader or internal execution
context; required read purpose; and, where applicable, the actor's disclosure
ceiling. Raw storage keys and host paths are not accepted.

### Outputs

When permitted and still retained, canonical content plus digest, term, schema,
carriage and class. When content is above the reader's ceiling or has expired,
the result contains only the permitted digest/reference metadata and an
explicit content-unavailable reason.

### Observable effect

None.

### Enforces

Disclosure ceiling before content release; exact digest lookup; no existence
leak through alternate storage paths; trial and run reads remain within their
own scope; expired content is never reconstructed or fabricated.

### Errors

Unknown or malformed reference, unauthorized scope, invalid reader context,
content removed by retention, unavailable storage and integrity mismatch are
explicit. A lower disclosure ceiling is a bounded metadata result, not an
authorization bypass.

### State impact

None.

## `public_op:value_store.derive_output_class`

### Owner

`module:value_store` owns the deterministic disclosure-class derivation for a
function output from the classes of the values actually supplied to that
execution.

### Callers

`module:run_executor` calls it after function output validation and before the
output is persisted or exposed to a dependant.

### Inputs

The exact input StoredValue references used by one function execution, the
validated output port and its declared semantic/schema constraints. Caller text
or a requested lower class is not an input.

### Outputs

One deterministic disclosure class for the output, together with the input
class evidence used to derive it.

### Observable effect

None.

### Enforces

The derived class cannot be less restrictive than the information classes that
contributed to the output; only the exact execution inputs participate; missing
or unreadable class evidence fails closed; operation-node service semantics are
not reclassified here.

### Errors

Missing input reference, inconsistent execution evidence, unknown class or
unsupported output context is refused without producing a fallback class.

### State impact

None.

## `public_op:value_store.expire_values`

### Owner

`module:value_store` owns retention expiry of stored value content while
preserving explanatory metadata.

### Callers

The long-lived `boundary:kernel_process` invokes this operation during the
bounded retention sweep defined by `flow:expire_evidence`.

### Inputs

No caller-authored clock or retention duration. The operation obtains current
time from `module:system_clock` and evaluates persisted retention references,
run terminal state and disclosure class under the accepted A20 policy.

### Outputs

A bounded deterministic sweep result identifying counts of content removed,
content retained because it is still required, and explicit failures. It never
returns removed bytes.

### Observable effect

Eligible `run_evidence` content is deleted while digest, term, schema,
carriage and disclosure metadata remain. Trial-corpus and approval evidence are
not expired by this policy, and content named by any non-terminal run or longer
retention reference remains present.

### Enforces

Thirty-day removal for personal-data run evidence, ninety-day removal for other
run evidence, longest-reference retention, non-terminal-run protection,
idempotent repeated sweeps and atomic failure through the operational store.

### Errors

Unavailable clock/store, inconsistent retention reference, indeterminate run
state or failed atomic sweep aborts the affected unit of work. The operation
never guesses that content is safe to delete.

### State impact

Only eligible stored content bytes are removed. StoredValue identities,
retention history and every record that names their digests remain immutable.
