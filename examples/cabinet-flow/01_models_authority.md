# State 1 companion — authority models

## Purpose

This document closes identity and data shape for the actors of the kernel under
State 0 decisions D0-040, D0-043 and D0-046: one human owner, agents acting
under the owner's delegation, and the reference by which every other record
names who acted.

## Model M16 — OwnerPrincipal

### Meaning

The single human principal of one kernel installation. Every approval, grant,
acceptance of vocabulary and acceptance of an operation binding is the owner's.

Candidate fields:

- `principal_id`: stable identity, fixed when the installation is created;
- `display_name`;
- `status`: `active` or `suspended`.

An installation has exactly one OwnerPrincipal. There is no creation operation
on the kernel surface; the record is part of installing the kernel.

### Identity

entity

### Identity evidence

Substitution: the owner is never interchangeable with an agent, however broad
that agent's delegation. Continuity: the same principal persists while its
display name, credentials and status change.

### Source of truth

The kernel installation record, established by the operator who installs the
kernel.

### Lifecycle candidate

`active -> suspended -> active`. While suspended, no approval, grant or
acceptance can be recorded and effectful flows stop at their approval points.

### Persistence candidate

Durable single record of the kernel's operational store.

### Open questions

None.

## Model M17 — AgentDelegation

### Meaning

The owner's continuing permission for one agent identity to act on the kernel
surface through one channel.

Candidate fields:

- `delegation_id`: stable identity;
- `owner_principal_id`;
- `agent_label`: the owner's name for this agent, such as the machine agent or
  the mobile chat;
- `channel`: `mcp` or `http_api`;
- `credential_binding_ref`: reference to the channel credential held in
  protected host configuration, never the credential itself;
- `may_author`: whether this agent may author contracts, implementations,
  bindings and flows, or may only inspect and run;
- `disclosure_ceiling`: the highest disclosure class of a value the surface
  returns to this agent (D0-047);
- `status`: `active` or `revoked`;
- `issued_at`, `revoked_at`.

A delegation never includes approving an effect, granting a standing approval,
accepting vocabulary or accepting an operation binding. Those belong to the
owner alone and no field can express them.

### Identity

entity

### Identity evidence

Substitution: two delegations are not interchangeable even with equal fields,
because every recorded action must stay attributable to the one it was performed
under. Continuity: a delegation remains the same permission from issuance until
revocation; changing what it permits issues another delegation.

### Source of truth

The owner's recorded decision on the kernel surface.

### Lifecycle candidate

`active -> revoked`. Revocation is final. Runs already waiting for approval are
unaffected; a revoked delegation can start nothing new.

### Persistence candidate

Durable entity of the kernel's operational store.

### Open questions

None.

## Model M18 — ActorRef

### Meaning

The exact statement of who performed one recorded action.

Candidate fields:

- `actor_kind`: `owner`, `agent` or `kernel`;
- `owner_principal_id`;
- `delegation_id` when the actor is an agent;
- `channel` when the action arrived over the surface.

`kernel` names deterministic behavior performed without a request, such as an
admission verdict or the activation of a proven read-only flow. It is never used
for an action that a human or an agent requested.

An outside sender of material, such as an employee or a supplier, is never an
actor. Such a person appears only as provenance inside the data that a
microservice's intake holds (D0-046).

### Identity

value

### Identity evidence

Substitution: equal kind, principal, delegation and channel are interchangeable.
Continuity: the reference describes one past action and never changes; the
delegation it names may later be revoked without altering it.

### Source of truth

The kernel surface, which resolves the authenticated channel identity to the
owner or to one active delegation before any operation is performed.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Embedded in every record that names an author, an approver or an initiator.

### Open questions

None.

## Model M49 — AuthenticationThrottleState

### Meaning

The durable abuse-control state for one protected credential binding on one
surface channel. It contains no credential material and exists only so repeated
failed authentication cannot be reset by restarting the kernel.

Candidate fields:

- `credential_binding_ref`: protected host reference, never the secret;
- `channel`: `mcp` or `http_api`;
- `consecutive_failures`: non-negative integer;
- `last_failure_at`: KernelInstant M47 when at least one failure exists;
- `blocked_until`: optional KernelInstant M47 while the credential/channel pair
  is temporarily blocked.

Owner and agent credentials have separate records. A failure on one agent
credential never changes the owner's record or another agent's record.

### Identity

entity

### Identity evidence

Substitution: two records with the same credential-binding reference and channel
cannot coexist as different throttle states; they name the same abuse-control
state. Continuity: that state remains the same entity while
`consecutive_failures`, `last_failure_at` and `blocked_until` change across
failures, success, block expiry and restart.

### Source of truth

`module:access_control`, from authentication results and
`module:system_clock.now` under A27.

### Lifecycle candidate

Absent until the first failure; updated on failure; reset to zero/unblocked on a
successful authentication after any active block has elapsed. The record may be
retained at zero so restart behavior remains deterministic.

### Persistence candidate

Durable master state of the kernel's operational store. It contains no reusable
credential and is backed up with the rest of the kernel state.

### Open questions

None.

