# Cabinet Backend — Authentication and Authorization Model

## Status

Accepted clarification for `02_rules.md`.

This rule defines the initial authentication and authorization model for:

- Cabinet Backend synchronization;
- local HTML source attachment;
- agent-assisted local operations;
- manual reconciliation;
- VPS retention release;
- Holded publication.

The initial model is intentionally small and installation-scoped.

---

## Accepted decision — separate machine and local-user identities

Cabinet Backend uses two distinct identity classes:

```text
SyncNodeCredential
LocalUserIdentity
```

They must not be interchangeable.

A synchronization credential authenticates one Cabinet Backend installation to
the VPS Cabinet application.

A local-user identity authorizes human or agent-assisted operations inside the
local Backend.

---

## Trust boundary

The synchronization direction remains:

```text
Cabinet Backend -> VPS Cabinet
```

Cabinet Backend initiates every synchronization request.

VPS Cabinet must not initiate inbound connections to the local Backend.

The local Backend does not need a public internet endpoint for synchronization.

---

## Sync node credential

Each Cabinet Backend installation receives one unique node credential.

The credential identifies:

```text
installation_id
credential_id
issued_at
status
```

Optional operational metadata may include:

```text
last_used_at
rotated_at
revoked_at
```

### Normative rules

1. A node credential belongs to exactly one Backend installation.
2. Credentials must not be shared between installations.
3. The credential must be transmitted only over an authenticated encrypted
   transport.
4. The credential must be stored outside the repository and outside exported
   business data.
5. Logs must never contain the full credential.
6. The VPS Cabinet validates the credential before returning synchronization
   data.
7. A revoked credential must stop authorizing new synchronization requests.
8. Credential rotation must not change the logical `installation_id`.
9. Synchronization authorization is installation-scoped, not user-scoped.
10. A synchronization credential cannot authorize local HTML, reconciliation,
    release, or Holded publication operations.

---

## Credential lifecycle

Supported credential states:

```text
active
revoked
```

Rotation creates a new active credential and revokes the old credential.

Backend must not rely on expiry alone as the only revocation mechanism.

If the credential is rejected:

```text
synchronization_status = authentication_failed
```

No synchronization payload is accepted as authoritative for that attempt.

---

## Local user identity

Sensitive local operations require an authenticated local-user identity.

The initial implementation may use a local account store owned by Cabinet
Backend.

Every local user has:

```text
local_user_id
display_name
status
roles
```

Supported user states:

```text
active
disabled
```

A disabled user cannot start new authenticated operations.

---

## Local-only HTML uploader

The HTML uploader is a local interface to the same Backend source-attachment
operation used by agent workflows.

### Normative rules

1. The uploader binds only to a local or explicitly trusted private interface.
2. It must not be exposed as a public internet service.
3. Opening the HTML page does not itself authorize mutation.
4. Source attachment requires an authenticated active local user.
5. Browser sessions must expire.
6. State-changing requests require protection against cross-site request
   forgery or an equivalent same-origin mechanism.
7. Uploaded files are processed by the Backend operation, not stored by the UI
   as a separate authority.
8. The uploader cannot bypass invoice resolution, hash verification, source
   status, or provenance rules.
9. The uploader cannot authorize Holded publication, reconciliation, or retention
   release unless the user also has the corresponding permission.

---

## Agent-assisted operations

An agent does not become an independent trusted identity merely because it runs
locally.

Agent-assisted mutations must execute under one of:

```text
authenticated local user delegation
explicit service identity
```

The initial baseline uses authenticated local-user delegation.

### Delegation rules

1. The agent must identify the delegating local user.
2. The Backend authorizes the requested operation against that user's roles.
3. Audit evidence records both:
   - the local user;
   - the agent or client identifier.
4. The agent must not receive the user's reusable password.
5. The agent must not reuse the sync node credential.
6. Agent delegation expires with the local session or operation grant.
7. The Backend remains the final authorization authority.

---

## Roles

The initial role set is:

```text
viewer
operator
accounting
administrator
```

A user may hold more than one role.

### viewer

May:

- read accepted Invoice Cards;
- read source-package status;
- read synchronization status;
- read Registry and PresuPro projections;
- read Holded publication state.

May not perform mutations.

### operator

May:

- perform all viewer operations;
- attach source files;
- resolve local invoice selection;
- record manual project-assignment review outcomes;
- accept explicitly allowed incomplete-source workflows when separately
  permitted by the relevant rule.

May not publish to Holded or manage credentials.

### accounting

May:

- perform all viewer operations;
- initiate verified Holded purchase publication;
- record reconciliation decisions;
- approve accounting-sensitive retries or correction workflows when those
  operations are later accepted.

May not manage node credentials or local users.

### administrator

May:

- perform all local operations;
- create, disable, and assign roles to local users;
- rotate and revoke sync node credentials;
- release VPS-retained copies when the relevant retention rule permits it;
- change local security configuration.

Administrator actions remain audited.

---

## Permission matrix

| Operation | viewer | operator | accounting | administrator |
|---|---:|---:|---:|---:|
| Read archive and status | yes | yes | yes | yes |
| Attach source file | no | yes | no | yes |
| Resolve project assignment | no | yes | no | yes |
| Accept incomplete source evidence | no | yes | no | yes |
| Publish purchase to Holded | no | no | yes | yes |
| Record Holded reconciliation | no | no | yes | yes |
| Release VPS-retained copy | no | no | no | yes |
| Manage local users and roles | no | no | no | yes |
| Rotate or revoke sync credential | no | no | no | yes |

A future accepted decision may refine this matrix.

---

## High-risk operations

The following operations require explicit user intent and must never execute as a
side effect of read or synchronization requests:

```text
accept incomplete source evidence
attach or replace source evidence
resolve project assignment
publish to Holded
reconcile a published Holded document
release VPS-retained copies
rotate or revoke credentials
change roles
disable users
```

The Backend must show or record the exact target before execution.

---

## Audit record

Every authenticated mutation must record:

```text
operation_id
operation_type
actor_type
local_user_id
agent_or_client_id
target_type
target_id
requested_at
completed_at
result
reason
```

Where relevant, it also records:

```text
invoice_revision_hash
source_id
holded_document_id
previous_state
new_state
```

Audit records are append-only.

A failed authorization attempt must also be auditable without storing secrets.

---

## Authorization invariants

Machine and user identity separation:

```text
SyncNodeCredential != LocalUserIdentity
```

Synchronization credential scope:

```text
sync credential -> synchronization only
```

Local mutation rule:

```text
state-changing local operation
-> authenticated active local user
-> required role
```

Agent rule:

```text
agent mutation
-> delegated authenticated user
-> Backend authorization check
```

Audit rule:

```text
every authorized mutation -> append-only audit record
```

---

## Secret handling

1. Secrets must not be committed to Git.
2. Secrets must not be embedded in synchronization packages.
3. Secrets must not be written to normal application logs.
4. Configuration exports must redact secrets.
5. Backup and restore procedures must distinguish encrypted secrets from ordinary
   business data.
6. Holded API credentials are separate from sync node credentials.
7. Holded credentials authorize only the dedicated Holded gateway.
8. Local user password material must be stored using a modern password-hashing
   mechanism; plaintext passwords are forbidden.

The exact cryptographic algorithms and storage technology belong to the
implementation security specification.

---

## Session behavior

Local authenticated sessions must:

```text
have finite lifetime
support explicit logout
be invalidated when the user is disabled
not expose reusable credentials to the browser after login
```

High-risk operations may require recent authentication.

The exact timeout values belong to configuration and implementation.

---

## Failure behavior

Authentication failure:

```text
result = authentication_failed
mutation = not executed
```

Authorization failure:

```text
result = forbidden
mutation = not executed
```

Disabled user:

```text
result = user_disabled
mutation = not executed
```

Revoked sync credential:

```text
result = node_credential_revoked
synchronization = not performed
```

Failures must not disclose secret material or unnecessary identity details.

---

## Required tests

1. A valid active node credential permits Backend-initiated synchronization.
2. A revoked node credential is rejected.
3. One installation cannot use another installation's credential.
4. A sync credential cannot authorize a local mutation.
5. An unauthenticated local user cannot attach a source file.
6. A viewer cannot perform mutations.
7. An operator can attach a valid source file.
8. An operator cannot publish to Holded.
9. An accounting user can initiate accepted Holded publication.
10. An accounting user cannot rotate node credentials.
11. An administrator can rotate and revoke node credentials.
12. Disabling a user invalidates new operations and active sessions.
13. Agent-assisted mutation records both user and agent identity.
14. Every successful mutation creates an append-only audit record.
15. Every forbidden mutation performs no state change.
16. Secrets are absent from logs, repository files, and synchronization payloads.
17. The HTML uploader cannot bypass Backend validation and authorization.
18. State-changing browser requests reject missing or invalid request-origin
    protection.

---

## Resolution of OQ-007

`OQ-007` is resolved for the initial Cabinet Backend implementation:

- synchronization uses a unique per-installation node credential;
- node credentials authorize synchronization only;
- local mutations require authenticated local users;
- agent operations use local-user delegation;
- the local HTML uploader uses the same authorized Backend operation;
- roles separate read, operational, accounting, and administrative permissions;
- all mutations and exceptional decisions are audited;
- secrets remain outside source control and business payloads.

---

## Consequence

The initial Backend security model keeps machine synchronization, local human
actions, agent delegation, accounting publication, and administration as
separate authorization concerns.

This model is sufficient to design the first implementation without exposing the
local Backend publicly or granting broad authority to one shared credential.
