# State 3 repair — concrete local access-control backend

## Status

Accepted repair for the Stage 8.1 finding in
`81_access_control_module_review.md`.

## Refinement — access_control

The existing module ownership remains authoritative and is refined as follows.

### Concrete implementation

`PostgresAccessControlBackend` is generated inside `module:access_control` and
implements `AccessControlBackend`. It owns:

- PostgreSQL transactions for principals, credential verifiers, throttle state,
  and append-only security audit evidence;
- Argon2id verification and cryptographically random credential issuance;
- exact capability evaluation against current stored state;
- atomic rotation and principal revocation;
- the offline Linux-owner enrollment boundary.

### Public surface

Runtime consumers continue to depend only on `AccessControlBackend` and
`authorize_operation`. The concrete class is exported only to the application
composition root and offline administration entry point.

### Internal capabilities

```text
enroll_local_service
rotate_local_service_credential
revoke_local_service_principal
record_authentication_failure
reset_authentication_failures
append_security_audit
```

These are not HTTP/MCP operations. Factory may split them into focused private
generation units, but callers must not depend on those internal paths.

### Must not own

- HTTP/MCP request parsing or route policy;
- synchronization-node credentials;
- Cabinet business-object authorization rules beyond exact capability matching;
- PostgreSQL schema decisions not derivable from declared models and
  persistence;
- a Cabinet human password or recovery system for the single-owner Linux
  baseline.

### Composition

The application composition root reads the configured environment-variable
names, constructs `PostgresAccessControlBackend`, and supplies it to
`create_app`. Missing database or pepper configuration fails startup; it must
not create an in-memory permissive fallback.

## Persistence-boundary refinement (later, authoritative)

`PostgresAccessControlBackend` is superseded by three owners
(`30_modules_persistence_boundary.md`):

- `credential_security` — the deterministic credential mechanism
  (`rules.credential_security_backend/v2`);
- `access_control_persistence` — `PostgresAccessControlRepository`, the
  deterministic storage shape (`persistence_backend/v3`);
- `access_control` — `LocalAccessControlService`, the `policy` implementation
  of `AccessControlBackend`: throttle thresholds from `rules.access_control`,
  exact capability evaluation, atomic lifecycle transitions, and audit
  evidence, composed over the repository port and the mechanism functions.

The internal capabilities listed above remain the service's responsibilities;
`record_authentication_failure`, `reset_authentication_failures`, and
`append_security_audit` are realised through the repository's plain rows.
