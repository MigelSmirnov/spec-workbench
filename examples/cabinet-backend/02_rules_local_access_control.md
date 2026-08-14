# State 2 repair — concrete local access control

## Accepted decision A69 — PostgreSQL local service access control

Cabinet Backend is generated as a complete application for one owner-operated
Linux machine. Codex and Claude Code use separately enrolled local service
identities. The concrete implementation is part of Cabinet Backend and is not
supplied by an unspecified deployment extension.

### Normative rules

1. `PostgresAccessControlBackend` is the concrete local implementation of the
   `AccessControlBackend` port.
2. Each Codex, Claude Code, or other local non-human consumer has a distinct
   `LocalServicePrincipal` and credential. Credentials are never shared.
3. Enrollment is an offline local administration operation. It must run under
   the Linux deployment owner, must not be exposed through HTTP/MCP, and must
   require an explicit non-empty capability set.
4. Enrollment and rotation generate a cryptographically random bearer secret,
   return it exactly once, and persist only an Argon2id hash plus its stable
   credential identifier.
5. The plaintext credential must not enter PostgreSQL, logs, audit records,
   exported data, Cards, source files, prompts, or generated artifacts.
6. Authentication resolves exactly one active credential and active principal.
   Revoked, malformed, unknown, delayed, or temporarily blocked credentials
   create no authenticated context.
7. Authorization rereads current principal and credential state. A previously
   issued `AuthenticatedPrincipalContext` does not cache authority.
8. Authorization succeeds only when the exact requested operation occurs in the
   principal's explicit capability set. Localhost reachability, process name,
   prompt text, or possession of an entity identifier grants nothing.
9. A successful decision records append-only `SecurityAuditRecord` evidence and
   returns its `evidence_id`. Refusal and authentication failure are also
   audited without secrets.
10. After five consecutive failures in one credential abuse context, progressive
    delay applies. After ten, new attempts for that context are blocked for 15
    minutes.
11. Successful authentication resets the active consecutive-failure counter but
    never deletes prior audit evidence.
12. Rotation creates a new active credential and atomically revokes the prior
    active credential. It does not change the principal identity or capability
    assignment.
13. Revoking a principal revokes all its active credentials atomically. A
    revoked principal cannot be reactivated; re-enrollment creates a new one.
14. PostgreSQL is the authoritative local store for principals, credential
    verifiers, throttle state, and security audit evidence.
15. Database connection details and credential pepper are read from named
    environment variables. Their values are deployment secrets and never enter
    the specification.

### Formal invariants

```text
plaintext_credential -> returned_once AND not_persisted AND not_logged

authenticated_context
-> active_credential AND active_principal

authorization_allowed
-> exact_operation in current_principal.capabilities

consecutive_failures >= 5 -> progressive_delay
consecutive_failures >= 10 -> blocked_for_15_minutes

credential_rotation
-> new_credential.active AND previous_credential.revoked

principal_revoked
-> all_principal_credentials.revoked
```

### Required tests

1. Codex and Claude Code receive distinct principals and credentials.
2. Enrollment with an empty or unknown capability is rejected without issuing a
   credential.
3. Plaintext credentials are absent from database rows, logs, and audit records.
4. An active credential authenticates to its exact principal.
5. Unknown, malformed, rotated, or revoked credentials are rejected.
6. A principal cannot perform an operation outside its exact capability set.
7. A stale authenticated context is refused after credential or principal
   revocation.
8. Five failures apply progressive delay and ten failures block attempts for 15
   minutes.
9. Successful authentication resets the counter without deleting audit history.
10. Rotation atomically issues a new credential and revokes the old one.
11. Principal revocation invalidates every active credential.
12. HTTP/MCP routes expose no enrollment, rotation, or revocation operation.

### Consequence

The generated local application contains a concrete, persistent access-control
implementation and can construct its own runtime dependency. It needs only
deployment-provided PostgreSQL connection and pepper secrets, not custom Python
code supplied after generation.

