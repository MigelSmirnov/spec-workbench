# State 5 — Cabinet Flow identity operations

The identity module computes names; it does not store, interpret or authorize
the records being named. Content-derived operations are deterministic and
idempotent. `mint_identity` is reserved for continuing entities whose identity
is not their content.

## `public_op:identity.identify_contract_version`

### Owner

`module:identity` owns canonical serialization and digest identity for M20.

### Callers

`module:slot_registry` calls it while issuing an immutable contract version.

### Inputs

Only the defining contract content: exact slot reference, ordered typed ports,
resource bounds and sandbox-runtime revision. Version ID, author, time,
rationale and storage facts are forbidden.

### Outputs

The content digest as `contract_version_id` with its canonicalization-version
identifier.

### Observable effect

None.

### Enforces

Stable field ordering and normalization; every defining field participates;
non-defining provenance does not; equal defining content yields one identity.

### Errors

Caller-supplied identity, missing defining field, non-canonicalizable value,
unknown canonicalization version and out-of-domain numeric/text form are
refused rather than normalized ambiguously.

### State impact

None; `module:slot_registry` owns idempotent lookup and persistence.

## `public_op:identity.identify_implementation`

### Owner

`module:identity` owns the digest identity of immutable implementation bytes.

### Callers

`module:slot_registry` calls it before storing submitted code.

### Inputs

The exact implementation byte sequence and the identity-relevant runtime/code
format discriminator. Filename, author, submission time, rationale and a
claimed implementation ID are not defining inputs.

### Outputs

The content digest as `implementation_id`.

### Observable effect

None.

### Enforces

Byte-exact repeatability, no identity copied from a file or request, and the
same bytes producing one identity across delegations and submission times.

### Errors

Caller-supplied ID, absent bytes, unsupported format discriminator and input
beyond the release ceiling are refused; code is never imported or executed.

### State impact

None; storage and slot association remain `module:slot_registry` concerns.

## `public_op:identity.identify_trial_case`

### Owner

`module:identity` owns canonical digest identity for TrialCase M24.

### Callers

`module:trial_corpus` calls it before append-only corpus registration.

### Inputs

The exact contract-version reference, typed input values or fixture digests,
expected-output evidence and protected-case classification that define the
case. Author, capture time, rationale and claimed case ID are excluded.

### Outputs

The content digest as `trial_case_id`.

### Observable effect

None.

### Enforces

Stable ordering of ports and collections, digest references for fixture bytes,
and identity change whenever any defining test evidence changes.

### Errors

Caller-supplied ID, incomplete defining evidence, duplicate ambiguous port,
non-canonical value or unresolved fixture digest is refused.

### State impact

None; the corpus owns idempotent registration and lifecycle.

## `public_op:identity.identify_binding_version`

### Owner

`module:identity` owns canonical digest identity for OperationBindingVersion
M30.

### Callers

`module:operation_bindings` calls it when proposing or reissuing a binding
version.

### Inputs

Exact manifest operation identity and digest, typed input/output ports, effect
class, replay behavior, idempotency and precondition facts, preview ports and
outcome-read binding reference. Author, acceptance time, rationale and claimed
version ID are excluded.

### Outputs

The content digest as `binding_version_id`.

### Observable effect

None.

### Enforces

Every behavior-affecting manifest and typing fact participates; equal defining
content yields one version identity; provenance cannot perturb identity.

### Errors

Caller-supplied ID, incomplete manifest pin, duplicate/ambiguous port,
non-canonical field or unsupported defining variant is refused.

### State impact

None; proposal, acceptance and persistence belong to
`module:operation_bindings`.

## `public_op:identity.identify_flow_version`

### Owner

`module:identity` owns canonical digest identity for FlowVersion M32.

### Callers

`module:flow_registry` calls it during immutable graph registration.

### Inputs

The exact Flow reference and complete defining graph: ordered nodes with pinned
versions, ports, edges and their bases, constants, guards, mappings, inputs and
outputs. Author, registration time, rationale, proof and activation are
excluded.

### Outputs

The content digest as `flow_version_id`.

### Observable effect

None.

### Enforces

Graph ordering is canonical rather than request-order dependent; every
behavior-changing constant, guard, mapping and pin changes identity; proof and
authority records never do.

### Errors

Caller-supplied ID, duplicate graph-local identity, incomplete graph variant,
non-canonical constant or unsupported canonicalization version is refused.

### State impact

None; registration, proof and activation remain separate operations.

## `public_op:identity.digest_value`

### Owner

`module:identity` owns canonical content digesting for StoredValue M38.

### Callers

`module:value_store` calls it before content-addressed storage or evidence
comparison.

### Inputs

The validated value in its exact declared schema, including type/schema
identity needed to prevent cross-schema ambiguity. Retention, disclosure,
producer, time and storage location are not part of the content digest.

### Outputs

One deterministic value digest.

### Observable effect

None.

### Enforces

Schema-aware canonical representation, stable ordering and numeric/text
normalization, with equal validated values producing equal digests.

### Errors

Unvalidated value, schema mismatch, non-canonical number/text, unsupported
value family and content beyond the digesting ceiling are refused.

### State impact

None; storage, disclosure and retention remain `module:value_store` policy.

## `public_op:identity.mint_identity`

### Owner

`module:identity` owns collision-resistant identity minting for continuing
entities whose identity is not derived from content.

### Callers

`module:access_control` calls it when issuing a new AgentDelegation in the
State 4 delegation flow.

### Inputs

One closed entity-kind discriminator and installation namespace. No requested
identity, semantic label, timestamp-derived identity or caller-controlled
entropy is accepted.

### Outputs

One new opaque stable identity in the namespace of the requested entity kind.

### Observable effect

It consumes the module's protected entropy/counter mechanism. It does not
create the entity or reserve business meaning.

### Enforces

Correct namespace, non-predictable/collision-resistant generation, no identity
chosen by an actor, and no accidental equality between entity kinds.

### Errors

Unknown entity kind, caller-supplied candidate, unavailable safe entropy or
detected collision refuses minting; no fallback based on time, label or random
request data is permitted.

### State impact

Only identity-generator bookkeeping may change. Delegation persistence and
transactionality belong to `module:access_control` and
`module:operational_store`.

