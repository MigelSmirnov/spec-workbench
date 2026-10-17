# State 5 — Cabinet Flow slot-registry operations

A25 clock contract: every operational timestamp written by this module is KernelInstant M47 obtained from its injected `module:system_clock.now` at the atomic event it owns. No public operation accepts caller-, gateway- or surface-supplied current time.

The slot registry owns replaceable pure-function definitions: the continuing
Slot identity, immutable contract versions and immutable implementation
submissions. It never executes, admits or activates code. Exact read operations
let peer modules depend on the registry without reading its storage directly.

## `public_op:slot_registry.create_slot`

### Owner

`module:slot_registry` owns creation and lifecycle of Slot M19.

### Callers

`module:kernel_surface` calls it from the closed `author` operation after
authoring permission is resolved.

### Inputs

The resolved ActorRef, bounded slot name/label and one bounded purpose statement
describing the single responsibility. A caller-supplied `slot_id`, initial
contract, implementation, corpus, activation or serving status is not accepted.

### Outputs

One newly created active Slot with a kernel-minted stable namespaced identity,
creator and creation time; or the exact existing Slot for an explicitly
idempotent request.

### Observable effect

Exactly one continuing Slot entity may be appended. No contract version,
implementation, trial case, admission or activation is created.

### Enforces

Kernel-owned stable identity; bounded authoring text treated only as data;
one-way Slot lifecycle; separation between the continuing slot container and
its immutable versions/submissions; no identity reuse after retirement.

### Errors

Unauthorized author, caller-supplied identity, conflicting duplicate,
invalid/unbounded text and transactional failure are refused without a partial
Slot.

### State impact

One active Slot may be added. Every other slot-owned or execution-owned record
is unchanged.

## `public_op:slot_registry.issue_contract_version`

### Owner

`module:slot_registry` owns issuance of immutable SlotContractVersion M20.

### Callers

`module:kernel_surface` calls it from the closed `author` operation for an
active Slot.

### Inputs

The resolved ActorRef; exact active Slot reference; complete ordered input and
output SemanticPort drafts; requested ResourceBounds; and exact
SandboxRuntimeRevision. No contract-version identity, ordinal, admission,
activation or implementation identity is accepted.

### Outputs

The immutable SlotContractVersion whose identity is computed by
`module:identity.identify_contract_version`, including the deterministic
version ordinal, exact normalized ports, release-clamped ResourceBounds and
runtime revision; or the existing equal version when defining content is
identical.

### Observable effect

When defining content is new, one immutable contract version is appended.
Issuing a contract never creates a corpus, runs code or selects an
implementation.

### Enforces

The Slot is active; every input port has an exact semantic term; every authored
term reference resolves through
`module:semantic_vocabulary.term_revision` to an active term on an active
axis; output without a term is allowed only as the explicit uncomposable-output
case; every schema and carriage is known and permitted; `byte_stream` is
limited to slot-contract ports with bounded accepted media types/size;
ResourceBounds are deterministically clamped to the injected ReleaseCeilings
M48; the runtime revision is offered for new contracts; all normalized defining
content participates in identity.

### Errors

Retired/unknown Slot, retired/unknown semantic term or axis, unknown schema,
invalid direction/cardinality/carriage, invalid byte-stream media contract,
unsupported/withdrawn runtime, malformed bounds, caller-supplied identity and
transaction failure are refused. No partially issued contract exists.

### State impact

At most one immutable SlotContractVersion is appended. Earlier versions,
implementations, corpus, activations and flows remain unchanged.

## `public_op:slot_registry.submit_implementation`

### Owner

`module:slot_registry` owns immutable Implementation M23 submission and
content-addressed code storage.

### Callers

`module:kernel_surface` calls it from the closed `author` operation.

### Inputs

The resolved ActorRef; exact existing SlotContractVersion; exact bounded
entry-point name; exact implementation code bytes; and bounded rationale with
optional motivating trace references. A caller-supplied
`implementation_id`, admission or activation is not accepted.

### Outputs

The immutable Implementation whose identity is computed by
`module:identity.identify_implementation` over
`(contract_version_ref, entry_point, code_bytes)`, plus its content-addressed
code reference; or the exact existing Implementation for identical defining
content.

### Observable effect

New code bytes are stored once under their digest and one immutable
Implementation may be appended. The code is not imported, executed, trialed or
activated.

### Enforces

Owning Slot is still active; contract exists exactly; code and entry point obey
release size/shape ceilings; identity is kernel-computed from every
execution-defining field and excludes author/time/rationale; equal defining
content is idempotent; implementation bytes are immutable and never deleted.

### Errors

Unknown contract, retired Slot, caller-supplied identity, missing/oversized code,
invalid/unbounded entry point, conflicting content-addressed storage and
transaction failure are refused without a partial implementation.

### State impact

At most one immutable Implementation and one deduplicated code object are
appended. Contract, corpus, admission and activation state do not change.

## `public_op:slot_registry.contract_version`

### Owner

`module:slot_registry` owns authoritative exact reads of immutable
SlotContractVersion records and their owning Slot lifecycle state.

### Callers

`module:trial_corpus` calls it to validate authored/captured/copied cases.
`module:admission` calls it for exact ports, runtime and bounds.
`module:flow_proof` calls it for function-node port semantics.
`module:run_executor` calls it to validate and pin function execution.
`module:slot_activation` calls it to verify activation targets and owning-slot
status.

### Inputs

One exact contract-version reference. No "latest contract", fallback version or
caller-selected replacement is accepted.

### Outputs

The exact immutable SlotContractVersion, including normalized ports,
ResourceBounds, runtime revision and its owning Slot identity/status. Historical
versions remain readable after Slot retirement.

### Observable effect

None.

### Enforces

Exact identity lookup; immutable content; no silent upgrade to another version;
owning Slot status is returned explicitly so callers can distinguish historical
evidence from a version eligible for new proof/activation/authoring.

### Errors

Unknown/malformed contract reference, integrity mismatch and unavailable
registry are explicit. A retired owning Slot does not erase the version.

### State impact

None.

## `public_op:slot_registry.implementation_record`

### Owner

`module:slot_registry` owns authoritative reads of immutable Implementation
metadata and the tightly restricted executable code body.

### Callers

`module:admission` calls it for exact implementation/contract/entry-point
metadata while constructing trial evidence.
`module:slot_activation` calls it to verify that an activation target belongs
to the exact contract version.
`module:sandbox_supervisor` calls it immediately before one execution to
obtain the exact immutable code bytes and entry point.

### Inputs

One exact Implementation reference and the closed internal read purpose
`evidence`, `activation_check` or `sandbox_execution`. Surface callers do
not address this operation directly.

### Outputs

For admission/activation purposes: immutable implementation identity,
contract-version reference, entry point, code digest/reference and provenance
metadata, but no code bytes. For `sandbox_execution`: the same metadata plus
the exact stored code bytes after digest verification.

### Observable effect

None.

### Enforces

Exact implementation identity and contract association; code digest integrity;
no fallback to another submission; executable bytes are disclosed only to
`module:sandbox_supervisor`; admission and activation cannot read or replace
the body; author-facing code visibility, when permitted by A22, is provided
only through `slot_authoring_view`.

### Errors

Unknown implementation, contract mismatch, corrupted/missing code object,
unsupported read purpose and unavailable storage are explicit. Missing code is
never reconstructed from rationale or another implementation.

### State impact

None.

## `public_op:slot_registry.retire_slot`

### Owner

`module:slot_registry` owns the final `active -> retired` transition of Slot
M19.

### Callers

`module:kernel_surface` calls it from the closed `author` operation after
authoring permission is resolved.

### Inputs

The resolved ActorRef; exact active Slot identity; expected active status; and a
bounded retirement reason. No request to delete versions, implementations,
corpus, activations or historical flow references is accepted.

### Outputs

The same Slot in final `retired` status with retirement evidence, or a typed
refusal.

### Observable effect

Exactly one Slot may become retired. Existing contract versions,
implementations, activations, FlowVersions, Runs and trace evidence remain.

### Enforces

Final compare-and-set transition; a retired Slot accepts no new contract
version, implementation or SlotActivation, and a new FlowProof cannot treat its
contract as eligible for new composition; already-proven flow versions and
already-created Runs retain their immutable pins and evidence.

### Errors

Unknown Slot, stale/already-retired status, conflicting repeat, invalid reason
and transaction failure are refused atomically.

### State impact

Only Slot lifecycle metadata changes to retired. Nothing historical is deleted
or rewritten.

## `public_op:slot_registry.slot_authoring_view`

### Owner

`module:slot_registry` owns the bounded authoring/inspection projection of the
records it owns for one Slot.

### Callers

`module:kernel_surface` calls it while composing the fixed slot inspection
view with corpus, activation-health and trace views from their separate owners.

### Inputs

The exact Slot identity, resolved ActorRef/effective authoring scope,
disclosure context, bounded page cursor and optional explicit request for one
implementation body. The caller cannot request corpus, admission, activation,
Run or trace state from this operation.

### Outputs

A bounded deterministic view of the Slot lifecycle, immutable contract versions
and submitted Implementation metadata. By default implementation bodies are
represented by digest/reference; an exact code body is returned only when A22
authoring visibility permits that actor to inspect that implementation of this
Slot. Corpus, serving activation, contract health and execution evidence are
absent and are composed by `module:kernel_surface` from their owners.

### Observable effect

None.

### Enforces

Exact Slot scope; bounded pagination; immutable version/submission history;
authoring/disclosure limits; no code body outside permitted authoring scope; no
cross-module fabricated state and no raw storage path.

### Errors

Unknown/invisible Slot, invalid cursor, unauthorized code-body request,
unreadable immutable record and storage-integrity failure are explicit.
Unavailable records are never replaced by another Slot's data.

### State impact

None.
