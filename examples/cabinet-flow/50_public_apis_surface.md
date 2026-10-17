# State 5 — Cabinet Flow fixed kernel surface

This slice freezes the operations that cross the process and channel boundary.
It does not make the gateways policy owners: both gateways frame a request and
delegate to the closed catalogue in `kernel_surface`. Exact Python signatures
and transport DTOs belong to State 6.

## `public_op:bootstrap.start_kernel`

### Owner

`module:bootstrap` owns the one fail-closed kernel start sequence.

### Callers

`boundary:kernel_process` calls this operation once for an installation start.

### Inputs

The host-selected installation identity and protected configuration references;
no service target, credential value, manifest fact or release ceiling is
accepted from a request or persisted domain record.

### Outputs

A bounded readiness result that identifies the pinned manifest revision and
states whether every required store, sandbox, binding sweep, resumed run and
gateway is ready. It contains no credential or host path.

### Observable effect

The operation validates the installation, seeds only missing installation
vocabulary idempotently, sweeps binding drift, resumes non-terminal runs and
starts the fixed MCP and HTTP listeners only after all mandatory checks pass.

### Enforces

One installation selects one service instance set; mixed production and rig
targets are refused; unhealthy sandbox supervision or unavailable durable
state prevents serving; no warning-only start is permitted.

### Errors

It returns typed start refusal for invalid configuration, unavailable durable
store, invalid or missing manifest revision, mixed instance class, failed
sandbox health, failed binding sweep, failed recovery, or listener failure.

### State impact

It may append idempotent installation seed records, binding suspension or
reissue records, and recovery conclusions. It never creates business facts.

## `public_op:mcp_gateway.serve_mcp`

### Owner

`module:mcp_gateway` owns MCP framing and nothing else.

### Callers

`boundary:mcp_client` sends an authenticated MCP request after kernel startup
has opened the listener.

### Inputs

One bounded MCP request envelope containing a catalogue operation name,
strictly typed arguments and a channel credential reference established by the
host listener.

### Outputs

One bounded MCP success or uniform typed refusal translated from the result of
`module:kernel_surface`; internal exceptions, host paths and credentials are
never returned.

### Observable effect

The gateway performs framing, size and unknown-field checks, delegates exactly
one request, and serializes exactly one response. It makes no domain decision.

### Enforces

Only the fixed catalogue is addressable; request fields are strict; channel
identity cannot be supplied inside the payload; transport never bypasses
`module:access_control` or calls a deep module directly.

### Errors

Malformed envelopes, unknown operations, unknown fields and payloads above
injected M48 `surface_request_bytes_max` are refused before delegation.
Authentication, authorization and domain errors
remain owned by their modules and are mapped without revealing record existence.

### State impact

None of its own. Any state change is the documented effect of the delegated
catalogue operation and carries the resolved ActorRef.

## `public_op:http_gateway.serve_http`

### Owner

`module:http_gateway` owns HTTP framing and nothing else.

### Callers

`boundary:http_client` sends an authenticated HTTP API request after kernel
startup has opened the listener.

### Inputs

One bounded HTTP request whose route maps to a fixed catalogue operation,
strict schema arguments and a listener-established channel credential
reference. Arbitrary module paths are not inputs.

### Outputs

One bounded schema response or uniform typed refusal derived from
`module:kernel_surface`, without a stack trace, host path or credential.

### Observable effect

The gateway validates route, media type, size and schema, delegates exactly one
catalogue request and maps its typed result to HTTP. It owns no retry or policy.

### Enforces

The HTTP API is a transport of the same closed catalogue as MCP; it is not a
database proxy, filesystem, shell or free-form code-execution endpoint.

### Errors

Unknown route, unsupported media type, malformed body, unknown field and body
above injected M48 `surface_request_bytes_max` are refused before delegation.
Owned module errors are mapped to
stable public error forms without existence disclosure.

### State impact

None of its own. Any state change belongs to the delegated catalogue operation.

## `public_op:kernel_surface.inspect`

### Owner

`module:kernel_surface` owns this fixed catalogue operation and delegates the
read to the module that owns the requested resource.

### Callers

`boundary:authenticated_kernel_client` calls it through either fixed gateway.

### Inputs

The resolved ActorRef, one closed inspection kind, an exact resource reference
or bounded query, and an optional bounded page cursor. The caller cannot name a
store, table, file path or implementation-internal module.

### Outputs

A bounded typed view of vocabulary, slots, bindings, flows, runs or traces,
with values reduced to digest-and-reference form whenever the actor's disclosure
ceiling does not permit content.

### Observable effect

None. Inspection reads accepted kernel records and returns only the view owned
by the selected deep module.

### Enforces

Actor authorization, disclosure ceiling, slot-scoped authoring visibility and
injected M48 pagination bounds: omitted page size uses `page_size_default`
and any requested size above `page_size_max` is refused; another actor's data,
credentials, implementation bodies during composition and raw storage layout
are never exposed.

### Errors

Unknown inspection kind, malformed reference, unauthorized kind and invisible
or absent record produce stable uniform refusals. A lower disclosure ceiling
returns permitted evidence rather than leaking hidden content.

### State impact

None.

## `public_op:kernel_surface.author`

### Owner

`module:kernel_surface` owns the fixed authoring catalogue entry and routes each
closed authoring request to `module:semantic_vocabulary`, `module:slot_registry`,
`module:trial_corpus`, `module:operation_bindings` or `module:flow_registry`.

### Callers

`boundary:authenticated_kernel_client` calls it through either fixed gateway.

### Inputs

The resolved ActorRef, one closed authoring command, and the exact typed draft
for a proposal, slot, contract version, implementation, trial case, binding,
flow or flow version. Caller-supplied content identities are not accepted.

### Outputs

The immutable accepted record reference or a typed refusal with all applicable
structural findings. Acceptance as data is distinct from admission, activation
and owner decision.

### Observable effect

It may append one proposal or immutable authoring record through its owning
module. It never runs code, activates a version, approves an effect or invokes a
service.

### Enforces

Authoring delegation, strict command variants, computed identities, immutable
versions, accepted semantic references, injected ReleaseCeilings M48 for code,
fixture and bounded-text sizes, and separation of proposal, proof, admission,
activation and authority.

### Errors

Non-authoring actor, unknown command, supplied identity, stale or retired owner,
invalid port, unknown schema or semantic revision, duplicate conflicting
content and oversized code or fixture are returned as owned typed refusals.

### State impact

Only the owning module's append-only or versioned authoring records may change;
serving selections, flow activations and external services do not.

## `public_op:kernel_surface.request_trial`

### Owner

`module:kernel_surface` owns the fixed request entry;
`module:admission` owns trial orchestration and the verdict.

### Callers

`boundary:authenticated_kernel_client` calls it through either fixed gateway.

### Inputs

The resolved ActorRef, exact contract-version and implementation references,
and no caller-authored verdict, case selection or sandbox configuration.

### Outputs

The recorded deterministic admission verdict reference with the complete set of
trial execution results and refusal reasons visible within the actor's
disclosure ceiling.

### Observable effect

Every active case is executed in a fresh sandbox; trial evidence and one
deterministic verdict are appended. No implementation is activated.

### Enforces

The entire non-empty active corpus, exact runtime revision and resource bounds,
strict input and output validation, external sandbox enforcement and confirmed
cleanup before another execution.

### Errors

Unknown or mismatched references, empty corpus, denied attempt, resource breach,
crash, invalid output, missing execution or unconfirmed cleanup appear in the
verdict; infrastructure inability to produce complete evidence refuses the
request without fabricating admission.

### State impact

Append-only trial execution and admission evidence only. Slot activation is
unchanged.

## `public_op:kernel_surface.activate`

### Owner

`module:kernel_surface` owns the fixed activation entry and delegates selection
to `module:slot_activation` or `module:flow_registry`.

### Callers

`boundary:authenticated_kernel_client` calls it through either fixed gateway.

### Inputs

The resolved ActorRef, activation kind, exact contract and implementation or
flow-version references, expected current activation for compare-and-set, and a
bounded reason when the operation is a rollback.

### Outputs

The appended activation record and resulting serving/current activation, or a
typed refusal that identifies stale evidence or missing authority without
changing selection.

### Observable effect

It appends a slot or flow activation. A read-only proven flow may be activated
by kernel policy; an effectful flow requires the owner. Rollback is another
activation, never history deletion.

### Enforces

Fresh admission over the current corpus, complete flow proof, highest effect
class, owner-only effectful flow activation, compare-and-set and refusal of
retired or known-failing targets.

### Errors

Stale admission, corpus growth, unproven flow, insufficient actor authority,
lost compare-and-set, retired target and rollback to an implementation failing
a newer case are typed refusals.

### State impact

Exactly one append-only activation record on success; contracts,
implementations, flow versions, proofs and earlier activations remain immutable.

## `public_op:kernel_surface.run_flow`

### Owner

`module:kernel_surface` owns the fixed run entry; `module:run_executor` owns the
run and its state machine.

### Callers

`boundary:authenticated_kernel_client` calls it through either fixed gateway.

### Inputs

The resolved ActorRef, an exact flow reference or its current activation, and
strict typed values for every declared flow input. A request cannot choose a
service instance, credential, implementation hash or operation binding outside
the pinned flow and installation.

### Outputs

A run reference and bounded current status. Completed results are returned as
validated values or digest-and-reference views under the actor's disclosure
ceiling; partial results are explicitly labelled partial.

### Observable effect

It creates a durable run, pins all versions and advances ready nodes. Function
nodes execute only in the sandbox; operation nodes invoke only accepted manifest
bindings; effectful nodes wait for required owner authority.

### Enforces

Activated proven flow, strict inputs, installation-selected instances,
disclosure compatibility, replay behavior, approval bound to exact inputs,
immutable trace, truthful pending/awaiting states and no guessed completion.

### Errors

Invalid input, inactive or retired flow, unserved contract, suspended binding,
unreachable service, refused operation, function failure and unknown effect
outcome become typed run state and trace evidence rather than transport success.

### State impact

It appends the run, node executions, approvals requested, invocation attempts,
stored values and trace records owned by their modules. Business state may
change only through an authorized operation node.

## `public_op:kernel_surface.owner_decide`

### Owner

`module:kernel_surface` owns the fixed owner-decision entry and routes the
closed decision kind to the module that owns it.

### Callers

`boundary:authenticated_owner_client` calls it through either fixed gateway.

### Inputs

The resolved owner ActorRef, one closed decision kind, the exact vocabulary or
binding proposal, vocabulary entry to retire, activation, approval, grant,
delegation or protected-corpus reference, its expected current revision/status,
and the owner's decision. Agent-authored explanatory text is not used as the
kernel's statement of effect.

### Outputs

The accepted decision record and resulting exact state, or a typed refusal with
no partial mutation.

### Observable effect

Depending on the closed kind, it may accept or reject a vocabulary or binding
proposal, retire an active vocabulary entry for future use, activate an
effectful flow, approve or deny one exact effect, grant or revoke a standing
approval, issue or revoke a delegation, cancel a waiting run, or authorize a
protected trial-corpus action.

### Enforces

The sole owner principal, kernel-generated plain-language statement, exact
version and input digest, single-use approval, destructive-grant prohibition,
compare-and-set and atomic owned-module mutation.

### Errors

Non-owner actor, stale revision, changed effect input, consumed approval,
destructive standing grant, suspended binding, invalid target and concurrent
decision are typed refusals and leave prior state unchanged.

### State impact

Exactly the decision record and owning aggregate named by the closed decision
kind may change; no free-form command or cross-module partial write is allowed.

