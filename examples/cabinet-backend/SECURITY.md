# Cabinet Backend — Layer 0 security workspace

## Status

Security architecture is **OPEN**. This document records the decisions that
must be made before public API, deployment, production integration, or secret
handling can be considered stable.

Known deployment direction is incomplete:

- the Cabinet user-facing application is expected to run on a VPS;
- the deployment location and exposure model of Cabinet Backend are not yet
  selected;
- Registry, PresuPro, Holded Gateway, agents, PostgreSQL, and binary source
  storage may run in different trust zones;
- current sandbox behavior does not establish a production authentication or
  authorization contract.

No common default is accepted merely because it is convenient. Until the items
below are chosen, later design states may discuss domain behavior but must not
claim production security readiness.

## Protected assets

Cabinet handles information that requires explicit protection:

- invoice and receipt images and PDFs;
- supplier and customer names, addresses, telephone numbers, emails, tax IDs,
  and other contact or fiscal data;
- project addresses and Registry customer references;
- purchase lines, prices, payment evidence, plan-versus-actual analysis, and
  estimate data from PresuPro;
- Holded accounting document identifiers and publication receipts;
- Cabinet decisions, notes, agent suggestions, provenance, and history;
- database credentials, service credentials, API tokens, signing keys, and
  encryption keys;
- logs, backups, exports, and temporary processing files containing any of the
  above.

## Actors and trust boundaries

The security model must distinguish at least:

- human Cabinet user;
- browser or future client;
- Cabinet Web UI;
- conversational agent runtime;
- Cabinet Backend;
- PostgreSQL;
- binary source storage;
- Registry;
- PresuPro;
- Holded Gateway;
- Client Portal or future downstream consumers;
- VPS operator and infrastructure automation.

An agent is not automatically trusted as the user. A service being inside the
same VPS is not automatically authorized to read every Cabinet record or use
every external credential.

## Deployment choices to close

### SEC-DEPLOY-001 — Cabinet Backend placement

**Type:** Choice  
**Status:** OPEN

Select whether Cabinet Backend runs:

- on the same VPS as the Cabinet Web UI;
- on a separate VPS or private service host;
- inside a private platform network;
- locally for the user while only the UI is hosted;
- in another explicitly described topology.

The decision must state which components are internet-facing and which are
private-only.

### SEC-DEPLOY-002 — Database placement and reachability

**Type:** Choice  
**Status:** OPEN

Select where PostgreSQL runs and which identities may connect. Direct public
internet access to PostgreSQL must not be assumed. The decision must cover
network restrictions, TLS, database users, backup access, and administrative
access.

### SEC-DEPLOY-003 — Binary source storage

**Type:** Choice  
**Status:** OPEN

Select where invoice images, PDFs, scans, and other originals are stored. The
decision must cover access control, encryption, signed or authenticated reads,
retention, deletion, backup, and prevention of public predictable URLs.

## Identity and authentication choices

### SEC-AUTHN-001 — Human identity provider

**Type:** Choice or Snapshot  
**Status:** OPEN

Determine how a user proves identity to Cabinet. Candidates may include an
existing platform identity, an external identity provider, or a Cabinet-owned
account model. No password, magic-link, OAuth, passkey, or session mechanism is
selected yet.

Required closure parameters include:

- identity authority;
- login and recovery flow;
- multi-factor policy if applicable;
- account disable/revoke behavior;
- session creation and expiry;
- trusted-device behavior if any.

### SEC-AUTHN-002 — Service identity

**Type:** Choice  
**Status:** OPEN

Determine how Cabinet Backend authenticates Registry, PresuPro, Holded Gateway,
and other services, and how those services authenticate Cabinet Backend.
Shared static secrets, mTLS, signed service tokens, workload identity, or
another mechanism must be deliberately selected rather than inferred from
sandbox access.

### SEC-AUTHN-003 — Agent identity and delegation

**Type:** Design  
**Status:** OPEN

Determine how an agent proves:

- which user or service invoked it;
- which Cabinet capabilities were delegated;
- which project scope applies;
- how long delegation remains valid;
- whether a human confirmation is required for sensitive actions.

An agent must not receive a reusable Holded token or unrestricted database
credential.

## Authorization choices

### SEC-AUTHZ-001 — Capability model

**Type:** Design  
**Status:** OPEN

Define authorization for at least:

- read Cabinet Cards;
- create and edit drafts;
- confirm or archive Invoice Cards;
- assign invoices to Work Objects;
- confirm or reject PresuPro matches;
- read source binaries;
- request Holded publication;
- view fiscal or payment data;
- administer integrations and credentials;
- export or delete data.

The first product may be single-user, but single-user does not remove the need
to distinguish browser, agent, backend, database, and integration privileges.

### SEC-AUTHZ-002 — Project and record scope

**Type:** Design  
**Status:** OPEN

Decide whether authorization is global to one Cabinet account, scoped by
Registry `project_id`, scoped by Card, or a combination. Every cross-system
request must preserve the selected scope; possession of a project UUID alone
must not grant access.

### SEC-AUTHZ-003 — Sensitive action confirmation

**Type:** Design  
**Status:** OPEN

Determine which operations require explicit human confirmation. Candidates
include:

- confirming extracted invoice facts;
- publishing an invoice to Holded;
- correcting a previously published invoice;
- deleting original source evidence;
- accepting low-confidence estimate matching;
- exporting fiscal or personal data;
- rotating or replacing integration credentials.

## Browser and API security choices

### SEC-WEB-001 — Session and browser boundary

**Type:** Choice  
**Status:** OPEN

Select session storage and transport. The decision must cover secure cookies or
other token storage, CSRF protection, XSS exposure, session fixation, logout,
idle expiry, absolute expiry, and revocation.

Long-lived bearer credentials in browser-accessible storage are not accepted by
default.

### SEC-WEB-002 — Public exposure

**Type:** Choice  
**Status:** OPEN

Determine whether Cabinet Backend is directly internet-facing or reachable only
through the Cabinet Web UI/reverse proxy/private network. Define TLS termination,
trusted proxy handling, allowed origins, host validation, request size limits,
and upload limits.

### SEC-WEB-003 — Abuse and rate limits

**Type:** Choice  
**Status:** OPEN

Define limits for login, document upload, OCR or agent processing, searches,
export, Holded publication, and expensive plan-versus-actual requests. Failure
behavior and observability must be specified.

## Data protection choices

### SEC-DATA-001 — Encryption and key ownership

**Type:** Choice  
**Status:** OPEN

Determine encryption requirements for:

- network traffic;
- PostgreSQL storage and backups;
- binary source storage and backups;
- integration credentials;
- local temporary files and processing artifacts.

The decision must identify who owns keys, where keys live, how they rotate, and
how recovery works.

### SEC-DATA-002 — Secrets management

**Type:** Choice  
**Status:** OPEN

Select how database passwords, service credentials, Holded credentials, signing
keys, and storage credentials are provided to processes. Secrets must not be
stored in Cabinet Cards, committed configuration, logs, agent prompts, or
Gateway receipts.

### SEC-DATA-003 — Retention, deletion, and backup

**Type:** Design and Choice  
**Status:** OPEN

Define retention and deletion for Cards, originals, logs, idempotency records,
publication receipts, audit evidence, backups, and exports. Deleting a current
record must not falsely claim that immutable backups or external Holded records
were also deleted.

### SEC-DATA-004 — Logging and redaction

**Type:** Design  
**Status:** OPEN

Define what may enter logs. Tax IDs, document images, full invoice payloads,
payment references, credentials, cookies, and raw provider responses must not be
logged by default. Correlation identifiers and safe error codes should permit
operations without exposing business data.

## Integration security choices

### SEC-INT-001 — Registry and PresuPro access

**Type:** Choice  
**Status:** OPEN

Define authentication, authorization, timeout, retry, and response-validation
policy for Registry and PresuPro. Cabinet must reject identity mismatch and must
not accept client-supplied Registry or PresuPro snapshots as authoritative.

### SEC-INT-002 — Holded Gateway boundary

**Type:** Design  
**Status:** OPEN

Holded credentials belong to Holded Gateway, not Cabinet UI, Cabinet agents, or
Invoice Cards. Define how Cabinet authorizes one publication request, how the
Gateway authenticates Cabinet, what idempotency and receipt data crosses the
boundary, and how ambiguous outcomes are reconciled without exposing provider
secrets.

### SEC-INT-003 — Webhooks and callbacks

**Type:** Choice  
**Status:** OPEN

If future integrations call Cabinet, define signature verification, replay
protection, timestamp tolerance, endpoint exposure, idempotency, and secret
rotation. No unsigned webhook is assumed safe.

## Agent and AI safety boundaries

### SEC-AGENT-001 — Tool allow-list

**Type:** Design  
**Status:** OPEN

Agents receive narrow tools rather than database, shell, filesystem, or raw
external-service credentials. Tool authorization must be checked by Cabinet
Backend for each operation; prompt text alone is not authorization.

### SEC-AGENT-002 — Untrusted document content

**Type:** Design  
**Status:** OPEN

Invoice text, PDF text, images, notes, supplier descriptions, and imported
PresuPro names are untrusted data. They may contain prompt-injection-like text
or malicious file content. Extraction and matching must not convert document
instructions into tool authority.

### SEC-AGENT-003 — Confirmation and provenance

**Type:** Design  
**Status:** OPEN

Agent suggestions must preserve provenance and remain distinguishable from
human-confirmed facts. Sensitive actions and low-confidence semantic matches may
require human confirmation according to the selected authorization policy.

## Operational security choices

### SEC-OPS-001 — VPS hardening and administration

**Type:** Choice  
**Status:** OPEN

Define administrator access, SSH policy, patching, firewalling, process
isolation, least-privilege operating-system users, container policy if used,
monitoring, and incident access. The VPS must not be treated as one undivided
trusted process space.

### SEC-OPS-002 — Backups and restoration

**Type:** Choice  
**Status:** OPEN

Define encrypted backups, access, retention, restore testing, recovery point,
recovery time, and restoration of consistency between PostgreSQL records and
binary sources.

### SEC-OPS-003 — Security events and audit

**Type:** Design  
**Status:** OPEN

Determine which events require durable audit evidence, including login,
failed authorization, invoice confirmation, match confirmation, source access,
Holded publication, credential changes, export, deletion, and administrative
operations.

## Minimum gate before later states close

State 1 domain exploration may continue while these choices remain open, but
security-sensitive API, module, contract, and deployment design must not close
until at least these are selected:

1. Cabinet Backend placement and internet exposure;
2. human authentication and browser session strategy;
3. service identity and agent delegation;
4. capability and project-scope authorization;
5. PostgreSQL and binary-storage placement;
6. secrets management and Holded Gateway credential ownership;
7. encryption, backup, retention, logging, and audit policy;
8. explicit confirmation policy for sensitive actions;
9. production operational owner and incident/recovery process.

## Accepted provisional direction

Only the following security direction is currently accepted:

- security is a Layer 0 blocker and will not be silently defaulted later;
- Cabinet Backend, not the agent, enforces authorization for persisted changes;
- Holded credentials remain inside Holded Gateway;
- Registry and PresuPro remain external sources of truth accessed through typed
  boundaries;
- secrets, cookies, tokens, raw credentials, and private keys never become
  Cabinet business data;
- production exposure, identity, authorization, storage, and deployment choices
  remain OPEN.
