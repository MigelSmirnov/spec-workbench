# State 5 — Cabinet Flow owner-authority operations

Authority binds the sole owner's decision to an exact effect. It does not
authenticate the owner, schedule a run or invoke a service. Draft writes rely
on flow activation; destructive operations can never receive a standing grant.

## `public_op:owner_authority.owner_statement`

### Owner

`module:owner_authority` owns kernel-generated plain-language statements for
owner decisions.

### Callers

`module:semantic_vocabulary`, `module:operation_bindings` and
`module:flow_registry` call it for proposal acceptance, binding acceptance and
effectful-flow activation or grant statements.

### Inputs

One closed statement kind and the exact facts needed by that decision:
vocabulary proposal kind/content and motivating evidence; affected service and
operation/binding; flow version and non-read nodes; effect classes, preview
ports and decision target. Agent text may accompany the request only as clearly
separate data.

### Outputs

A bounded deterministic statement plus digest binding it to every represented
fact and version.

### Observable effect

None.

### Enforces

All material facts are included; agent text cannot replace, shorten or template
the generated part; the same facts yield the same statement/digest.

### Errors

Missing, inconsistent or unaccepted evidence and unsupported statement kind
are refused; no best-effort statement is produced.

### State impact

None.

## `public_op:owner_authority.request_approval`

### Owner

`module:owner_authority` owns construction of one exact effect preview and
single-use approval request.

### Callers

`module:run_executor` calls it when a ready `state-transition`,
`external-effect` or `destructive` node lacks a covering active grant.

### Inputs

Exact run/flow-version/node and mapped-element set; pinned binding and service
instance; all validated input digests; bounded values of declared preview
ports; file descriptions from `module:run_spool`; and the owner statement.

### Outputs

One pending EffectApproval containing the complete preview and
`preview_digest` over binding version, instance and every input digest, or a
typed refusal.

### Observable effect

The approval request is appended and becomes visible to the owner; the run may
rest `awaiting_approval`. No service call occurs.

### Enforces

One request covers exactly one node execution or the complete mapped
collection; all inputs—not only preview ports—are digested; owner sees full
preview; agent reads obey disclosure ceiling; draft-write is not routed here.

### Errors

Changed/missing input, incomplete mapped collection, invalid preview port,
unavailable file description, suspended binding or stale run pin is refused
without authority.

### State impact

One pending approval may be appended; run state is owned by
`module:run_executor`.

## `public_op:owner_authority.decide_approval`

### Owner

`module:owner_authority` owns the final owner-only approval or denial decision.

### Callers

`module:kernel_surface` calls it from an authenticated owner `owner_decide`
request.

### Inputs

The active owner ActorRef, exact pending approval, expected pending status and
decision `approved` or `denied`. A new preview or altered input is not accepted.

### Outputs

The immutable decided EffectApproval, or a typed refusal.

### Observable effect

The pending approval becomes approved or denied atomically. Approval is still
usable only if invocation inputs reproduce its digest.

### Enforces

Owner only; one decision; exact request/version; denial authorizes no call;
absence of a decision is never converted by timeout; decision cannot transfer
to another run, node, attempt or flow version.

### Errors

Agent or suspended owner, stale/decided request, changed target and concurrent
decision are refused without replacing the existing decision.

### State impact

Exactly one approval status changes; no invocation or run transition is
performed here.

## `public_op:owner_authority.authorization_for_effect`

### Owner

`module:owner_authority` owns the authoritative answer whether this exact node
execution may proceed now.

### Callers

`module:run_executor` calls it immediately before delegating a ready effectful
node to the operation-invocation boundary.

### Inputs

Exact run, flow version, node, binding version, instance and current input
digests; optional decided approval reference; current owner/binding/grant state.

### Outputs

Authorization by one unconsumed matching approval or one active covering grant,
including its reference and covered input digests; otherwise `approval_required`
or explicit denial/invalidation.

### Observable effect

An approval may be atomically marked consumed for the exact execution. Grant
execution count evidence may be reserved/recorded with the later node result.

### Enforces

Input digest equals preview digest; single use per node/element; grant matches
exact flow version, node and binding; owner and binding remain active;
destructive never uses a grant; effect-not-applied retry of `duplicates`
requires fresh approval.

### Errors

Changed input, consumed or denied approval, stale version, revoked grant,
suspended binding/owner and concurrent consumption return no authority.

### State impact

Only atomic authority-consumption bookkeeping may change; the service effect is
performed solely by `module:operation_invoker`.

## `public_op:owner_authority.grant_standing_approval`

### Owner

`module:owner_authority` owns owner-only creation of StandingGrant M43.

### Callers

`module:kernel_surface` calls it from an authenticated owner decision.

### Inputs

The active owner ActorRef, exact flow version, node and pinned accepted binding,
expected absence/current grant state, and kernel-generated statement describing
what will happen without asking and in which service.

### Outputs

One active immutable StandingGrant, or a typed refusal.

### Observable effect

The grant becomes available to future matching executions; it performs no
effect itself.

### Enforces

Owner only; exact version/node/binding; binding effect is non-destructive;
statement completeness; no inheritance by another version; compare-and-set.

### Errors

Agent or suspended owner, destructive node, unaccepted/suspended binding,
mismatched node/version, incomplete statement and conflicting active grant are
refused.

### State impact

One active grant may be appended; flows, bindings, runs and services are
unchanged.

## `public_op:owner_authority.revoke_standing_approval`

### Owner

`module:owner_authority` owns final revocation of a StandingGrant.

### Callers

`module:kernel_surface` calls it from an authenticated owner decision.

### Inputs

The active owner ActorRef, exact grant identity, expected active status and
bounded reason. `module:owner_authority` obtains `revoked_at` from its
injected `module:system_clock` at the successful compare-and-set; no
caller-supplied current time is accepted.

### Outputs

The revoked grant or a typed refusal; exact repetition cannot rewrite the
original revocation.

### Observable effect

The grant ceases to authorize the next invocation. A run already past the node
is unaffected; one waiting at it must request approval.

### Enforces

Owner only, final transition, compare-and-set, exact grant and immutable
history.

### Errors

Agent/suspended owner, unknown grant, stale state and concurrent/conflicting
revocation are refused atomically.

### State impact

Exactly one grant changes to revoked; historical executions keep their
`grant_ref`.

## `public_op:owner_authority.waiting_for_owner`

### Owner

`module:owner_authority` owns the bounded owner view of pending approvals and
active grants.

### Callers

`module:kernel_surface` calls it for owner inspection.

### Inputs

The active owner ActorRef, bounded filters and page cursor. Agent callers are
not accepted.

### Outputs

A deterministic paginated list of runs/nodes awaiting approval with complete
owner previews, plus the active-grant list and execution counts. No credential,
host path or implementation body is included.

### Observable effect

None.

### Enforces

Owner-only full preview, bounded pagination, exact pending/current states and
no timeout-generated decision.

### Errors

Non-owner or suspended owner, invalid cursor/filter and unavailable evidence
are explicit; incomplete results are not presented as complete.

### State impact

None.

