# State 0 — Cabinet Backend security boundary

## Status

The primary trust boundary is accepted. Cabinet uses two protected data zones:
a continuously available VPS Invoice Workspace and a local durable Backend.

```text
ChatGPT
  → Cabinet application and MCP boundary on VPS
     → protected fresh-invoice workspace
     → authenticated encrypted synchronization
  → Local Cabinet Backend
     → local PostgreSQL, durable files, Registry, and PresuPro
```

ChatGPT and the agent communicate only with Cabinet. They never receive direct
access to PostgreSQL, filesystems, Registry, PresuPro, Holded credentials, or a
generic Backend interface.

## Security consequence of the two-tier model

The VPS is no longer only a UI host. It stores real invoice originals and
structured fiscal data for fresh invoices. It must therefore be treated as a
production data host with a deliberately limited scope.

The local environment remains the full durable archive and integration zone.
Neither side is trusted merely because it belongs to the same owner.

## VPS trust zone

The VPS may store only the working set required for fresh invoices:

- original photograph or PDF;
- extracted and accepted Invoice Card facts;
- invoice revisions and provenance;
- user-visible discussion context needed for the active workflow;
- synchronization state and transfer evidence.

The VPS must not automatically receive the complete historical Cabinet archive,
all PresuPro estimates, local database dumps, Registry storage, or reusable
local-platform credentials.

Required controls include:

- strong user/session authentication;
- HTTPS and secure session handling;
- private, non-predictable source-file access;
- encryption at rest where supported and encrypted backups if backups exist;
- strict upload size and media validation;
- malware-safe and resource-limited document processing;
- log redaction for invoice bodies, tax IDs, payment references, and file URLs;
- retention rules for synchronized originals and revisions;
- immediate revocation of VPS-to-local credentials after compromise.

## Local trust zone

The local platform hosts:

- Cabinet Backend;
- full Cabinet PostgreSQL archive;
- durable source files;
- Registry;
- PresuPro;
- local integration adapters and durable synchronization receipts.

Required controls include:

- disk and operating-system account protection;
- PostgreSQL bound only to localhost or a private local interface;
- least-privilege database credentials;
- source files outside public/shared web paths;
- encrypted tested backups for database and files;
- safe secret storage outside Cards, prompts, source control, and logs;
- recovery and revocation procedures for a lost machine.

## Identity boundaries

### Human identity

The user authenticates to Cabinet on the VPS. This session controls access to
Cabinet tools and the VPS Invoice Workspace.

The first product may be single-user, but session expiry, revocation, recovery,
and sensitive-action confirmation remain required.

### Machine identity

VPS Cabinet and the local Backend authenticate separately from the human
session. Acceptable implementations may include Tailscale identity, SSH keys,
mTLS, or short-lived signed service credentials.

Requirements:

- encrypted private transport;
- allow-list of the expected Cabinet installation;
- revocable and rotatable credentials;
- no trust based only on IP address or `project_id`;
- no reusable local credential exposed to browser JavaScript or agent prompts.

## Invoice authority and synchronization security

A fresh invoice created on the VPS receives a stable `invoice_id`. Transfer to
the local Backend must include:

- invoice identity;
- exact revision or content hash;
- original-source hash and metadata;
- provenance and actor evidence;
- idempotency key;
- expected prior synchronization state.

The local Backend must reject:

- duplicate logical creation with a different identity;
- stale overwrites;
- source hash mismatch;
- project assignment claims not validated through local Registry;
- unsupported contract versions;
- commands from an unrecognized Cabinet installation.

A transport timeout produces an unknown outcome until reconciliation. The VPS
must query transfer status using the same idempotency key rather than creating a
new invoice.

## Editing boundary

The baseline avoids unrestricted multi-master editing.

- `remote_only`: the VPS owns the current fresh revision;
- `syncing`: changes are frozen or explicitly versioned during transfer;
- `synchronized`: the local Backend owns the durable primary revision;
- subsequent VPS editing is read-only or requires an explicit checked-out/new
  revision workflow;
- `conflict`: neither side silently wins.

## Source retention and deletion

The VPS may delete or expire an original only after the local Backend confirms
that both source bytes and the accepted revision are durably stored.

Deletion policy must distinguish:

- unsynchronized source — never deleted by normal retention;
- synchronized working copy — eligible for expiry after a selected period;
- legal/accounting retention — may require continued local preservation;
- user-requested deletion — cannot claim deletion from Holded or backups unless
  those systems separately confirm it.

## Agent safety

The agent may help extract, explain, edit, search, and compare fresh invoices,
but receives only narrow Cabinet tools.

Document text, OCR output, filenames, supplier descriptions, and PresuPro item
names are untrusted content. Instructions found inside them do not authorize
file access, synchronization, project assignment, deletion, export, or Holded
publication.

Sensitive actions require explicit user intent, including:

- confirming extracted invoice facts;
- synchronizing or replacing an already synchronized revision when conflict is
  possible;
- publishing to Holded;
- deleting source evidence;
- exporting fiscal data;
- replacing connection credentials.

## Integration boundaries

- Registry and PresuPro are accessed only through the local Backend.
- A VPS invoice may retain an object label or suggestion, but validated
  `assigned` status requires local Registry evidence.
- Full plan-versus-actual analysis requires local estimate and historical data.
- Holded credentials remain exclusively inside Holded Gateway.

## Availability and incident behavior

If the local platform is offline, fresh-invoice work on the VPS remains
available. Synchronization and local integrations show an explicit unavailable
state.

If the VPS is compromised:

- revoke machine credentials;
- block local synchronization;
- rotate user sessions and service credentials;
- identify exposed working-set invoices;
- do not assume the local archive is compromised without evidence.

If the local machine is lost:

- revoke its service identity;
- restore the local archive from tested backups;
- preserve unsynchronized VPS invoices for later recovery.

## Remaining implementation choices

1. Tailscale, SSH reverse tunnel, mTLS, or equivalent private transport;
2. VPS session mechanism and recovery;
3. VPS storage encryption and backup policy;
4. retention period after successful synchronization;
5. exact checked-out/read-only policy after synchronization;
6. conflict reconciliation UX;
7. local backup destination, keys, RPO, and RTO;
8. audit vocabulary and log retention;
9. Holded Gateway placement and authentication.

## Accepted decision A60 — Cabinet trust boundary inventory

1. VPS Cabinet is a protected working data zone for fresh invoices.
2. Fresh invoices remain usable while the local platform is offline.
3. The local Backend is the full durable archive and platform-integration zone.
4. One logical invoice identity is preserved across both zones.
5. Synchronization is authenticated, encrypted, revision-aware, and idempotent.
6. Unrestricted two-way editing is not accepted in the baseline.
7. The VPS stores a limited working set, not the complete archive by default.
8. Registry and PresuPro remain local-only integrations.
9. ChatGPT and the agent never receive raw storage or service credentials.
10. Holded credentials remain inside Holded Gateway.

### Actors and authentication boundaries

- The human user authenticates at Cabinet VPS for the remote working set and at
  Local Cabinet Backend for local mutations.
- Agent-assisted actions use narrow Cabinet tools and delegated local-user
  authority; agent identity alone grants no mutation permission.
- Each Backend installation has a separate revocable machine identity for
  Backend-initiated synchronization with VPS Cabinet.

### Browser and client boundary

Browser, ChatGPT, agent, OCR text, filenames, and client-side state are untrusted
inputs. They do not authorize storage access or privileged state changes. The
public VPS client and the local-only uploader terminate at different
authentication and network surfaces.

### External and integration boundaries

Registry, PresuPro, PostgreSQL, durable local files, and Holded credentials stay
behind Local Cabinet Backend. Holded is reached through its dedicated gateway.
The accepted product has no inbound webhook callback; synchronization is
initiated by Local Cabinet Backend and authenticates the VPS response/package
boundary before acceptance.

### Upload and file boundary

Photographs and PDFs enter through the VPS capture workflow or the local
attachment operation. Their bytes, declared type, filename, extracted text, and
document contents are untrusted. Accepted originals are immutable evidence and
must not gain filesystem-path or executable authority from user-controlled
metadata.

### Secrets and network surfaces

VPS Cabinet is the only accepted public network surface. Local Backend,
PostgreSQL, Registry, PresuPro, and local durable storage remain local or on an
explicitly trusted private interface. Human sessions, sync-node credentials,
local-user password material, and Holded credentials are distinct secrets and
must not cross into Cards, prompts, exports, generated files, or ordinary logs.
