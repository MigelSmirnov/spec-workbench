# State 0 — Cabinet Backend security boundary

## Status

The primary trust boundary is accepted. Cabinet uses two protected data zones:
a continuously available VPS Invoice Workspace and a local durable Backend.

```text
Remote user / ChatGPT / remote agent
  → Cabinet application and MCP boundary on VPS
     → protected fresh-invoice workspace
     → authenticated encrypted synchronization

Local user / local agent
  → Local Cabinet Backend private application/tool boundary
     → local PostgreSQL, durable files, Registry, and PresuPro
```

Agents communicate only through accepted Cabinet application/tool boundaries on
the node where they run. They never receive direct access to PostgreSQL,
filesystem paths, Registry storage, PresuPro storage, Holded credentials, or a
generic unrestricted Backend interface.

## Security consequence of the two-tier model

The VPS is no longer only a UI host. It stores real invoice originals and
structured fiscal data for fresh invoices. It must therefore be treated as a
production data host with a deliberately limited scope.

The local environment remains the full durable archive, local agent runtime, and
integration zone. Neither side is trusted merely because it belongs to the same
owner, and localhost/private-network reachability is not authorization proof.

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
- local agent/application tool boundary;
- local integration adapters and durable synchronization receipts.

Required controls include:

- disk and operating-system account protection;
- PostgreSQL bound only to localhost or a private local interface;
- local Cabinet agent/application endpoints bound only to localhost, local IPC,
  or an explicitly trusted private interface;
- least-privilege database credentials;
- source files outside public/shared web paths;
- encrypted tested backups for database and files;
- safe secret storage outside Cards, prompts, source control, and logs;
- explicit local service/agent enrollment, authorization, rotation, and
  revocation where reusable service credentials are used;
- recovery and revocation procedures for a lost machine.

## Identity boundaries

### Remote human identity

The user authenticates to Cabinet on the VPS with an account identifier and
password. The authenticated finite-lived session controls access to Cabinet
tools and the VPS Invoice Workspace.

The first product may be single-user, but session expiry, revocation, recovery,
and sensitive-action confirmation remain required.

The accepted recovery authority is the user's recovery email address bound to
the account before recovery begins. Recovery proves control through a
single-use, short-lived token or link delivered to that pre-bound email channel.
Security questions, Cabinet business data, and knowledge of entity identifiers
are not accepted recovery proof.

A successful recovery revokes all active human sessions. Ordinary
forgotten-password recovery does not automatically revoke separate local/remote
agent service credentials or the synchronization credential. Known or suspected
account or device compromise expands revocation/rotation to the affected
non-human credentials according to the incident scope. Concrete abuse limits,
temporary blocking, and machine/service replay response are enforced by A67.

### Local interactive human context

The single-user local baseline may delegate interactive human trust to the
already authenticated operating-system session on the protected local machine.
A separate Cabinet-owned local password store is not required.

This does not make the local UI an authorization authority. Cabinet Backend
still authorizes protected operations, and a future multi-user, remotely
accessible, or separately authenticated local deployment requires a new accepted
product/security decision.

### Local agent and service identity

A local agent or other non-human local consumer authenticates separately at the
private Cabinet Backend tool boundary. Acceptable mechanisms may include a
rotatable local service credential, OS/IPC peer identity, or another deployment
mechanism that maps the caller to one explicit enrolled service principal.

Requirements:

- local reachability alone grants no authority;
- the Backend authorizes the exact operation and target;
- each service principal receives only required capabilities;
- the agent never receives a reusable human password;
- local service identity is revocable and rotatable;
- local service identity cannot be reused for VPS synchronization;
- audit/provenance distinguishes the acting agent/service from any human
  interaction on whose behalf it acted.

### Synchronization machine identity

VPS Cabinet and the local Backend authenticate separately from human and local
agent/service contexts for synchronization. Acceptable implementations may
include Tailscale identity, SSH keys, mTLS, or short-lived signed service
credentials.

Requirements:

- encrypted private transport;
- allow-list of the expected Cabinet installation;
- revocable and rotatable credentials;
- no trust based only on IP address or `project_id`;
- no sync credential exposed to browser JavaScript or agent prompts;
- no sync credential accepted as local agent/application authority.

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

Remote and local agents may help extract, explain, edit, search, compare, and
perform other accepted Cabinet operations, but receive only narrow tools exposed
by their current Cabinet node.

The VPS agent sees only data and capabilities accepted for the VPS working set.
The local agent may use full-archive, Registry, PresuPro, source-file, analytics,
and local-integration operations only when the local Backend exposes and
authorizes those capabilities.

Document text, OCR output, filenames, supplier descriptions, and PresuPro item
names are untrusted content. Instructions found inside them do not authorize
file access, synchronization, project assignment, deletion, export, Holded
publication, tool selection, or capability escalation.

Sensitive actions require explicit user intent where required by the owning
Cabinet rule, including:

- confirming extracted invoice facts;
- synchronizing or replacing an already synchronized revision when conflict is
  possible;
- publishing to Holded;
- deleting source evidence;
- exporting fiscal data;
- replacing connection credentials.

## Integration boundaries

- Registry and PresuPro are accessed only through the local Backend.
- The local agent reaches Registry/PresuPro capabilities only through narrow
  Cabinet Backend operations; it does not receive their storage or reusable
  credentials directly.
- A VPS invoice may retain an object label or suggestion, but validated
  `assigned` status requires local Registry evidence.
- Full plan-versus-actual analysis requires local estimate and historical data.
- Holded credentials remain exclusively inside Holded Gateway.

## Availability and incident behavior

If the local platform is offline, fresh-invoice work and remote agent operations
on the VPS remain available. Synchronization, local agent operations, and local
integrations show an explicit unavailable state.

If the VPS is compromised:

- revoke affected machine/service credentials;
- block local synchronization until trust is restored;
- rotate user sessions and affected remote service credentials;
- identify exposed working-set invoices;
- do not assume the local archive is compromised without evidence.

If the local machine is lost or compromised:

- revoke its synchronization identity and affected local service identities;
- recover or re-secure the operating-system account/device trust boundary;
- restore the local archive from tested backups when necessary;
- preserve unsynchronized VPS invoices for later recovery.

## Remaining implementation choices

1. Tailscale, SSH reverse tunnel, mTLS, or equivalent private synchronization
   transport;
2. exact local service/agent credential or OS/IPC peer-identity mechanism;
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
9. Remote and local agents never receive raw storage or integration credentials.
10. Holded credentials remain inside Holded Gateway.
11. Cabinet has an agent/application trust boundary on both VPS and Local
    Backend.
12. The Local Cabinet Backend tool boundary is private; it is not a second public
    internet surface.

### Actors and authentication boundaries

- The remote human user authenticates at Cabinet VPS with account/password and
  recovers access only through the pre-bound email recovery channel.
- Successful VPS human recovery revokes all active human sessions.
- The single-user local interactive baseline may rely on the authenticated OS
  session rather than a Cabinet-owned local password account.
- Remote agent/service actions authenticate at the VPS Cabinet tool boundary.
- Local agent/service actions authenticate at the private Local Cabinet Backend
  tool boundary through an enrolled service/peer identity.
- Each Backend installation has a separate revocable machine identity for
  Backend-initiated synchronization with VPS Cabinet.
- Human context, local/remote agent service identity, and synchronization
  identity are non-interchangeable.

### Browser and client boundary

Browser, ChatGPT, agent, OCR text, filenames, and client-side state are untrusted
inputs. They do not authorize storage access or privileged state changes. The
public VPS client and any local-only UI/tool transport terminate at different
authentication and network surfaces.

### External and integration boundaries

Registry, PresuPro, PostgreSQL, durable local files, and Holded credentials stay
behind Local Cabinet Backend. Local agents reach them only through authorized
Cabinet operations. Holded is reached through its dedicated gateway. The
accepted product has no inbound webhook callback; synchronization is initiated
by Local Cabinet Backend and authenticates the VPS response/package boundary
before acceptance.

### Upload and file boundary

Photographs and PDFs enter through the VPS capture workflow or the local
attachment operation. Their bytes, declared type, filename, extracted text, and
document contents are untrusted. Accepted originals are immutable evidence and
must not gain filesystem-path or executable authority from user-controlled
metadata.

### Secrets and network surfaces

VPS Cabinet is the only accepted public network surface. Local Backend,
PostgreSQL, Registry, PresuPro, local agent/application transports, and local
durable storage remain local or on an explicitly trusted private interface.
Remote human session secrets, recovery tokens, sync-node credentials,
local/remote service credentials, and Holded credentials are distinct secrets
and must not cross into Cards, prompts, exports, generated files, or ordinary
logs.
