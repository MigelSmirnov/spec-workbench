# State 5 repair — local access-control composition API

## `public_op:bootstrap.create_local_app`

### Owner

`module:bootstrap`

### Callers

Local Linux process launcher.

### Inputs

No business inputs. Deployment configuration is read from the environment names
declared in `config.access_control`.

### Outputs

A configured FastAPI application whose access-control dependency is a concrete
`PostgresAccessControlBackend`.

### Observable effect

Validates required deployment configuration and constructs the local runtime.

### Enforces

No permissive or in-memory fallback when PostgreSQL or the credential pepper is
missing.

### Errors

Startup fails before serving requests when required configuration is missing or
the access-control store cannot be initialized.

### State impact

May initialize deterministic PostgreSQL storage projection; does not enroll a
principal implicitly.

## `public_op:bootstrap.enroll_local_agent`

### Owner

`module:bootstrap`

### Callers

Offline CLI invoked by the Linux deployment owner.

### Inputs

Agent display name and a non-empty tuple of exact protected operation
capabilities.

### Outputs

`IssuedServiceCredential`, containing the only plaintext copy of the newly
issued bearer credential.

### Observable effect

Atomically creates one active service principal, one active credential verifier,
and append-only enrollment audit evidence.

### Enforces

Linux-owner-only offline administration, explicit capabilities, distinct
principal identity, one-time secret disclosure, and no HTTP/MCP exposure.

### Errors

Rejects a non-owner invocation, empty/unknown capabilities, duplicate active
agent identity, missing deployment secrets, or failed atomic persistence.

### State impact

Creates PostgreSQL principal, credential, and audit records.

## `public_op:bootstrap.rotate_local_agent_credential`

### Owner

`module:bootstrap`

### Callers

Offline CLI invoked by the Linux deployment owner.

### Inputs

Exact active local service `principal_id`.

### Outputs

A one-time `IssuedServiceCredential` for the replacement credential.

### Observable effect

Atomically revokes the prior active credential, issues its replacement, and
records rotation evidence.

### Enforces

Linux-owner-only offline administration, exact active-principal targeting,
atomic revoke-then-issue with no window of two active credentials, one-time
secret disclosure, and no HTTP/MCP exposure.

### Errors

Rejects a non-owner invocation, unknown/revoked principal, missing deployment
secrets, or failed atomic persistence.

### State impact

Updates credential lifecycle and appends security evidence without changing the
principal identity or capabilities.

## `public_op:bootstrap.revoke_local_agent`

### Owner

`module:bootstrap`

### Callers

Offline CLI invoked by the Linux deployment owner.

### Inputs

Exact active local service `principal_id`.

### Outputs

None after the revocation transaction commits.

### Observable effect

Atomically revokes the principal and every active credential and records audit
evidence.

### Enforces

Linux-owner-only offline administration, exact active-principal targeting,
terminal one-way revocation covering every active credential, append-only audit
history, and no HTTP/MCP exposure.

### Errors

Rejects a non-owner invocation, unknown/already-revoked principal, missing
deployment secrets, or failed atomic persistence.

### State impact

Performs the terminal local principal transition without deleting history.

> Persistence-boundary refinement (later, authoritative): `PostgresAccessControlBackend` is realised as
> `LocalAccessControlService` (policy) over `PostgresAccessControlRepository` (storage) and
> `credential_security` (mechanism); see `30_modules_persistence_boundary.md`.
