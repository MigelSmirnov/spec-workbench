# State 4 repair — local access-control lifecycle flows

## `flow:bootstrap_local_backend`

### Trigger

The Linux deployment owner starts the generated Cabinet Backend application.

### Boundary

`module:bootstrap` owns environment/configuration composition only.
`module:access_control` owns the concrete PostgreSQL security implementation;
the deterministic `module:api` owns HTTP assembly.

### Steps

1. `module:bootstrap` resolves the required database URL and credential pepper
   from the configured environment-variable names.
2. It constructs `PostgresAccessControlBackend`; missing or unusable secure
   configuration stops startup.
3. It passes the concrete object through the `AccessControlBackend` port to
   `module:api.create_app`.
4. The deterministic router stores that exact dependency and exposes only the
   accepted protected routes.

### Outcomes

The process returns a configured FastAPI application or fails before serving a
request. It never falls back to anonymous, in-memory, or allow-all access.

### Errors

`module:bootstrap` owns configuration/startup translation. `access_control`
owns PostgreSQL and credential-verifier initialization errors. `api` does not
reinterpret either failure.

## `flow:administer_local_agent_identity`

### Trigger

The Linux deployment owner explicitly enrolls Codex or Claude Code, rotates its
credential, or revokes its local service identity through the offline command.

### Boundary

`module:bootstrap` verifies the offline Linux-owner boundary and translates CLI
input. `module:access_control` owns identities, credentials, capabilities,
transactions, throttling state, and audit evidence. No HTTP/MCP route participates.

### Steps

1. The offline command verifies that it runs as the configured deployment owner.
2. Enrollment supplies a distinct display name and explicit non-empty exact
   capability set; rotation/revocation supplies one exact principal identity.
3. `PostgresAccessControlBackend` performs the requested lifecycle transition in
   one PostgreSQL transaction and appends security evidence.
4. Enrollment or rotation returns the new plaintext credential exactly once;
   only its Argon2id verifier remains persisted.
5. Revocation returns only after the principal and all active credentials are
   durably revoked.

### Outcomes

Successful enrollment/rotation returns `IssuedServiceCredential`. Successful
revocation returns no secret. Invalid ownership, capability, target, state, or
persistence produces an explicit failure with no partial issuance.

### Errors

`bootstrap` owns refusal of non-owner CLI invocation and missing deployment
configuration. `access_control` owns invalid capability, duplicate enrollment,
unknown/revoked target, transaction, and credential-generation failures.

> Persistence-boundary refinement (later, authoritative): `PostgresAccessControlBackend` is realised as
> `LocalAccessControlService` (policy) over `PostgresAccessControlRepository` (storage) and
> `credential_security` (mechanism); see `30_modules_persistence_boundary.md`.
