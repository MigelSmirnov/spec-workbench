# State 5 — Cabinet Flow access-control operations

A25 clock contract: every operational timestamp written by this module is KernelInstant M47 obtained from its injected `module:system_clock.now` at the atomic event it owns. No public operation accepts caller-, gateway- or surface-supplied current time.

These operations implement the trusted entrance of A21. Authentication resolves
who is acting; authorization decides whether that actor may request one closed
catalogue action. Neither operation decides the business result of that action.
Delegation mutation is reachable only through the owner-decision surface.

## `public_op:access_control.resolve_actor`

### Owner

`module:access_control` owns channel authentication, active-delegation lookup,
per-credential failure throttling and construction of the immutable ActorRef.

### Callers

`module:mcp_gateway` and `module:http_gateway` call it after framing a request
and before any resource reference in the request is evaluated.

### Inputs

The channel (`mcp` or `http_api`) and the listener-established credential
material or binding handle. `module:access_control` obtains KernelInstant M47
directly from its injected `module:system_clock` for throttling evidence.
Actor kind, principal identity, delegation identity and current time are not
accepted from the request body or gateway.

### Outputs

Exactly one ActorRef of kind `owner` or `agent` naming the installation owner,
channel and, for an agent, one active delegation; otherwise one uniform
authentication refusal. Credential values are never returned.

### Observable effect

A successful resolution has no durable domain effect. Failed authentication
updates only bounded per-credential/channel throttling state and may produce a
bounded owner-visible security report.

### Enforces

Every request resolves to the sole owner XOR one active delegation; owner and
agent credentials are distinct; revoked delegations fail before the next
request; agent-channel failures cannot throttle the owner's access; existence
of any requested record is not consulted or disclosed.

### Errors

Missing, invalid, ambiguous or revoked credential, channel mismatch and active
throttle all yield the same public refusal shape. Protected lookup, clock or
throttling failures refuse closed and reveal no credential, host path, record
identity or stack trace.

### State impact

No kernel record is created or changed on success. Only bounded authentication
failure/throttle evidence may change on refusal; a historical ActorRef embedded
in an earlier record is never rewritten after delegation revocation.

## `public_op:access_control.authorize_action`

### Owner

`module:access_control` owns the closed mapping from catalogue action kind to
owner-only, authoring, inspect/run or disclosure requirements.

### Callers

`module:mcp_gateway` and `module:http_gateway` call it with the ActorRef returned
by `public_op:access_control.resolve_actor` and the already-framed catalogue
action kind.

### Inputs

One resolved ActorRef, one closed catalogue action kind and the disclosure
class requested by a read when applicable. It does not accept an asserted
permission, proof, admission, approval, reconciliation or owner decision.

### Outputs

An authorization result carrying the same ActorRef and the effective disclosure
ceiling, or a uniform not-permitted refusal. Success grants permission only to
evaluate this one request; it is not a reusable authority token.

### Observable effect

None. The operation neither performs nor approves the requested catalogue
action and does not change a delegation.

### Enforces

Owner-only actions require `actor_kind = owner`; `may_author = false` permits
only inspect, run and trace reads; `may_author = true` adds the authoring,
trial-request and implementation-activation actions enumerated by A21; no
delegation can express owner authority; returned content cannot exceed the
delegation disclosure ceiling.

### Errors

Unknown action kind, owner-only action by an agent, authoring action without
`may_author`, disclosure above the ceiling, suspended owner and malformed
ActorRef are refused without revealing whether a target record exists.

### State impact

None. The ActorRef may later be embedded by the owning operation if that
operation succeeds, but authorization itself appends no action record.

## `public_op:access_control.issue_delegation`

### Owner

`module:access_control` owns issuance of the immutable continuing permission
represented by AgentDelegation M17.

### Callers

`module:kernel_surface` calls it only from an authorized
`owner_decide` request whose actor is the active owner.

### Inputs

The owner ActorRef, bounded agent label, one channel (`mcp` or `http_api`), a
protected installation credential-binding reference, `may_author`, disclosure
ceiling and expected installation owner identity. `module:access_control`
obtains `issued_at` from its injected `module:system_clock` at the atomic
write. No raw credential, owner-only permission flag or caller-supplied current
time is accepted.

### Outputs

The newly issued active AgentDelegation with a kernel-minted stable identity,
or a typed refusal. The returned record contains only the credential-binding
reference, never credential material.

### Observable effect

Exactly one active delegation is appended atomically. Equal fields do not reuse
another delegation identity because every future action must remain attributable
to the exact permission under which it occurred.

### Enforces

Only the sole active owner may issue; channel and credential binding agree;
the protected binding exists in installation configuration; authoring is one
boolean; disclosure ceiling is one closed class; owner-only actions are absent
and unrepresentable; all persisted identities are computed or minted by the
kernel.

### Errors

Non-owner or suspended owner, unknown/mismatched credential binding, invalid
channel or disclosure class, oversized label, caller-supplied delegation ID and
lost transactional write are refused with no partial delegation.

### State impact

One durable AgentDelegation in `active` state is appended in one unit of work.
Existing delegations, credentials and the OwnerPrincipal are unchanged.

## `public_op:access_control.revoke_delegation`

### Owner

`module:access_control` owns the final `active -> revoked` transition of an
AgentDelegation.

### Callers

`module:kernel_surface` calls it only from an authorized
`owner_decide` request whose actor is the active owner.

### Inputs

The owner ActorRef, exact delegation identity, expected active status and a
bounded owner reason. `module:access_control` obtains `revoked_at` from its
injected `module:system_clock` at the successful compare-and-set. It accepts
neither a credential value, a caller-supplied current time nor a request to
cancel runs started under the delegation.

### Outputs

The revoked delegation with `revoked_at`, or a typed refusal. Repeating the
same exact revocation may return the already-revoked record but cannot create a
second transition or alter its time and reason.

### Observable effect

The target delegation becomes permanently revoked atomically and cannot
authenticate the next request.

### Enforces

Only the sole active owner may revoke; revocation is final; changing permissions
requires a new delegation; historical ActorRefs remain attributable; runs
already started or awaiting approval continue under `module:run_executor` and
are not cancelled as a side effect.

### Errors

Non-owner or suspended owner, unknown delegation, owner/delegation mismatch,
stale expected state, conflicting repeated revocation and transactional failure
are refused without modifying any run or revealing credential material.

### State impact

Exactly one delegation changes from `active` to `revoked` with an immutable
revocation time and reason. No historical action record, run or credential is
rewritten or deleted.

