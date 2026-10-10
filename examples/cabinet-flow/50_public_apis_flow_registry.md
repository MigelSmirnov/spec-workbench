# State 5 — Cabinet Flow flow-registry operations

A25 clock contract: every operational timestamp written by this module is KernelInstant M47 obtained from its injected `module:system_clock.now` at the atomic event it owns. No public operation accepts caller-, gateway- or surface-supplied current time.

The registry owns immutable graphs and the selection of a runnable version. It
does not prove graphs, approve individual effects, grant standing authority or
execute nodes.

## `public_op:flow_registry.composition_view`

### Owner

`module:flow_registry` owns the bounded authoring view used to compose a graph.

### Callers

`module:kernel_surface` calls it for an authorized inspect or author request.

### Inputs

The ActorRef, bounded filters and page cursor, plus the actor's disclosure
ceiling. No implementation-body, credential or storage-path selector is
accepted.

### Outputs

A bounded, deterministically ordered view of active contract versions,
accepted operation-binding versions, their semantic ports, effect classes and
the accepted vocabulary evidence needed for composition. Function
implementation bodies are absent.

### Observable effect

None.

### Enforces

Only composable accepted versions are listed; retired and suspended facts are
labelled rather than silently substituted; pagination is bounded; disclosure
ceilings apply; composition evidence never exposes code or secrets.

### Errors

Invalid filter or cursor, unauthorized actor and unavailable required evidence
are typed refusals. An incomplete view is not presented as complete.

### State impact

None.

## `public_op:flow_registry.create_flow`

### Owner

`module:flow_registry` owns stable Flow identity and its lifecycle.

### Callers

`module:kernel_surface` calls it from an authorized author request.

### Inputs

The ActorRef, bounded flow name and purpose. A caller-supplied Flow identity,
initial graph, activation, approval or grant is not accepted.

### Outputs

The newly created active Flow record with a kernel-minted stable identity, or
the exact existing record for an explicitly idempotent request.

### Observable effect

One Flow entity is appended. No FlowVersion or activation is created.

### Enforces

Authoring permission, bounded text treated only as data, kernel-owned identity,
one stable lifecycle and separation between a flow container and immutable
versions.

### Errors

Unauthorized actor, caller-supplied identity, conflicting duplicate, invalid
bounded text and transactional failure are refused without a partial record.

### State impact

One durable Flow may be added; versions, proofs, activations and services are
unchanged.

## `public_op:flow_registry.register_flow_version`

### Owner

`module:flow_registry` owns idempotent registration of immutable FlowVersion
graphs by content identity.

### Callers

`module:kernel_surface` calls it from an authorized author request.

### Inputs

The ActorRef, exact Flow identity, complete bounded graph of function and
operation nodes, edges, constants, guards, mappings, declared inputs and
outputs, and pinned contract or binding version references. No proof,
activation, approval or caller-selected version identity is accepted.

### Outputs

The immutable FlowVersion whose identity is computed by `module:identity`, or
the existing equal version for identical defining content.

### Observable effect

One immutable FlowVersion is appended when its defining content is new. It is
not runnable merely because it was registered.

### Enforces

Complete closed graph shape, bounded counts and payloads, references expressed
as exact versions, content-derived identity, no embedded code or expressions,
and no inheritance of activation, approvals or grants from another version.

### Errors

Unknown or retired Flow, malformed graph variant, unbounded collection,
caller-supplied identity, conflicting content and transactional failure are
refused. Semantic and whole-graph findings belong to `module:flow_proof`.

### State impact

One immutable FlowVersion may be added. FlowProof and FlowActivation remain
absent until their own operations succeed.

## `public_op:flow_registry.activate_flow_version`

### Owner

`module:flow_registry` owns A11 activation and derivation of the flow's highest
effect class from its pinned binding versions.

### Callers

`module:kernel_surface` calls it after authorization. A read-only version may
be activated under the kernel actor; every higher effect class requires the
active owner ActorRef and its exact owner decision.

### Inputs

Exact Flow and FlowVersion references, the proven FlowProof for that same
version, expected current activation for compare-and-set, and either the kernel
actor for `read` or the owner ActorRef plus kernel-generated owner statement for
an effectful version. Agent-supplied prose cannot replace the statement.

### Outputs

One immutable FlowActivation naming the selected version, prior activation,
highest effect class, activating actor and reason, or a typed refusal with the
current activation unchanged.

### Observable effect

A successful selection appends one FlowActivation. Returning to an earlier
version is also a new activation; history is never rewritten.

### Enforces

Proof is `proven` for the exact version; highest effect is derived, not
declared; `read` is kernel-activated; any higher class is owner-only; every
non-read node appears in the generated statement; compare-and-set prevents
lost updates; a new version inherits no activation, approval or grant.

### Errors

Missing, refused or mismatched proof, retired flow/version, suspended owner,
agent attempt on an effectful flow, incomplete generated statement, stale
expected activation and concurrent selection are refused atomically.

### State impact

Exactly one append-only FlowActivation may be created. Flow/version/proof
content, approvals, grants and external services are unchanged.

## `public_op:flow_registry.current_flow_activation`

### Owner

`module:flow_registry` owns the authoritative current selection for one Flow.

### Callers

`module:kernel_surface` uses it for inspection and run requests;
`module:run_executor` uses the resolved selection when pinning a new run.

### Inputs

One exact Flow identity. The caller cannot nominate a fallback version or ask
for an unproven version to be treated as current.

### Outputs

The current immutable FlowActivation and selected FlowVersion reference, or an
explicit no-current-activation result. It never fabricates a default.

### Observable effect

None.

### Enforces

Latest successful compare-and-set selection, flow/version identity match,
retirement visibility and no inheritance from similarly named flows or older
versions.

### Errors

Unknown flow, corrupt activation chain or unavailable record is explicit. No
activation is treated as a runnable default.

### State impact

None.

## `public_op:flow_registry.retire_flow`

### Owner

`module:flow_registry` owns the final active-to-retired Flow transition.

### Callers

`module:kernel_surface` calls it from an authorized authoring request.

### Inputs

The owner or authoring-agent ActorRef, exact Flow identity, expected active
status and current activation, and bounded retirement reason.
`module:flow_registry` obtains the retirement KernelInstant from its injected
`module:system_clock` at the successful compare-and-set; no current-time value
is accepted from the caller.

### Outputs

The retired Flow record or a typed refusal. An exact repeated retirement may
return the existing result but cannot rewrite its time, actor or reason.

### Observable effect

The Flow becomes unavailable for new versions, activations and runs. Existing
versions, proofs, activations, runs and traces remain historical evidence.

### Enforces

Authoring permission, final transition, compare-and-set, immutable history and
no cascade deletion or cancellation of already recorded runs.

### Errors

Actor without authoring permission, unknown Flow, stale state/activation,
conflicting repeat and transactional failure are refused without partial
retirement.

### State impact

Exactly one Flow lifecycle record changes to retired; no version, proof,
activation, run, approval or grant is deleted or rewritten.
