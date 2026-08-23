# State 1 repair — local Linux access-control records

## Status

Accepted Stage 8.1 repair for the concrete local implementation behind
`AccessControlBackend`. Cabinet Backend is a complete single-owner Linux
application. Codex and Claude Code authenticate as distinct local service
principals; neither inherits authority merely by running on the machine.

## Model M92 — PrincipalStatus

Closed status of a local principal or credential (`kind: enum`): `active`, `revoked`.

### Identity

enum (no runtime identity).

---

## Model M93 — AuthorizationReasonCode

Closed reason vocabulary shared by `AuthorizationDecision` and `SecurityAuditRecord`
(`kind: enum`): `authentication_required`, `unknown_credential`, `credential_revoked`,
`principal_revoked`, `stale_context`, `throttled_delay`, `throttled_block`,
`secret_mismatch`, `operation_forbidden`. The façade maps the first five to
`AuthenticationRequiredError` and `operation_forbidden` to `OperationForbiddenError`;
no string prefix or message is ever inspected.

### Identity

enum (no runtime identity).

---

## Model M94 — SecurityAuditResult

`kind: enum`: `allowed`, `refused`.

### Identity

enum (no runtime identity).

---

## Model M95 — SecurityAuditEventType

`kind: enum`: `authentication`, `authorization`, `enrollment`, `rotation`, `revocation`.

### Identity

enum (no runtime identity).

---

## Model M58 — LocalServicePrincipal

Persistent identity and exact capability assignment for one enrolled local
agent or service.

Fields:

- `principal_id: str`;
- `display_name: str`;
- `principal_kind: str` — `agent` or `service`;
- `status: PrincipalStatus` — M92: `active` or `revoked`;
- `capabilities: tuple[str, ...]` — exact protected operation identifiers;
- `created_at: datetime`;
- `revoked_at: datetime | None`.

### Identity

entity

### Identity evidence

The stable `principal_id` preserves the identity of the enrolled consumer while
credentials rotate and capabilities change. A different principal is not
interchangeable even when its current capability set is equal.

### Lifecycle

`active -> revoked`. Revocation is terminal; re-enrollment creates another
principal.

### Persistence candidate

PostgreSQL master record.

## Model M59 — LocalServiceCredential

Persistent verifier and lifecycle record for one credential issued to one
local service principal. It never contains the reusable bearer secret.

Fields:

- `credential_id: str`;
- `principal_id: str`;
- `secret_hash: str`;
- `status: PrincipalStatus` — M92: `active` or `revoked`;
- `issued_at: datetime`;
- `rotated_from_credential_id: str | None`;
- `revoked_at: datetime | None`;
- `last_authenticated_at: datetime | None`.

### Identity

entity

### Identity evidence

The stable `credential_id` identifies one issued verifier through use and
revocation. Rotation creates a different credential record.

### Lifecycle

`active -> revoked`. The plaintext secret exists only in the issuance result.

### Persistence candidate

PostgreSQL master record containing an Argon2id hash, never plaintext.

## Model M60 — AuthenticationThrottleState

Persistent abuse-control state derived from a non-secret hash of the attempted
credential context.

Fields:

- `abuse_context_hash: str`;
- `credential_id: str | None`;
- `consecutive_failures: int`;
- `delay_until: datetime | None`;
- `blocked_until: datetime | None`;
- `updated_at: datetime`.

### Identity

entity

### Identity evidence

The stable `abuse_context_hash` identifies one bounded failure context across
attempts without persisting the presented bearer secret.

### Lifecycle

Created on failure, updated by later failures, reset after successful
authentication, and retained as security evidence according to deployment
retention policy.

### Persistence candidate

PostgreSQL master record.

## Model M61 — SecurityAuditRecord

Immutable evidence for enrollment, authentication, authorization, rotation,
revocation, throttling, and refusal.

Fields:

- `evidence_id: str`;
- `event_type: SecurityAuditEventType` — M95;
- `principal_id: str | None`;
- `credential_id: str | None`;
- `operation: str | None`;
- `result: SecurityAuditResult` — M94;
- `reason_code: AuthorizationReasonCode | None` — M93;
- `occurred_at: datetime`.

### Identity

entity

### Identity evidence

Every `evidence_id` identifies one issued audit fact. Equal projected fields do
not make two authentication or authorization events interchangeable.

### Lifecycle

Issued append-only evidence; never updated or deleted by access-control
operations.

### Persistence candidate

PostgreSQL issued record.

## Model M62 — IssuedServiceCredential

One-time issuance result returned only by the offline local administration
command.

Fields:

- `principal_id: str`;
- `credential_id: str`;
- `credential: str`;
- `issued_at: datetime`.

### Identity

value

### Identity evidence

Equal issuance values are interchangeable. The value has no lifecycle and is
never persisted or logged by Cabinet Backend.

