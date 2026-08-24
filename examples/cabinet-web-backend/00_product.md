# State 0 — Cabinet_web server backend product boundary

## Status

Accepted State 0 after correction of the primary product interface.

Online ChatGPT with the already connected Cabinet server plugin is mandatory
and is the principal human UI/UX. The ordinary Cabinet Web pages are a
secondary visual and operational surface. ChatGPT owns the normal extraction
interaction; a protected Web handoff owns original-byte custody only. The
Cabinet Web Backend does not provide OCR.

The operator has selected the full synchronization cycle as the first server
slice. This document records the stable product boundary and keeps unresolved
product choices explicit when they exist. Models, modules, Python contracts, HTTP routes,
storage tables, and implementation algorithms are intentionally deferred.

## Product statement

The Cabinet Web Backend is the continuously available server companion of
`Cabinet_web` on the VPS. Its primary human interface is the online ChatGPT
conversation through the Cabinet plugin already connected to the VPS server.
This plugin access is part of the product, not an optional diagnostic channel.
The normal Invoice workflow begins by attaching the document in ChatGPT.

Its first product responsibility is to preserve and serve all information that
`Cabinet_web` already owns. The existing product set includes Provider, Client,
Project, and Invoice Cards plus current project-owned shopping-list, estimate,
procurement, payment, and financial facts.

The local integration is intentionally narrower. During an evening session,
`cabinet_backend` pulls only Invoice Cards and their source files from Cabinet
Web and publishes one compact Registry catalogue package back to Cabinet Web.
Other Cabinet Web data is not synchronized to the local backend.

The service preserves truthful transfer-side progress while the local backend
is unavailable and never claims local durable acceptance without reciprocal
evidence. It gives neither the browser nor the VPS runtime access to local
backend credentials or internals.

The service is not a replacement for `cabinet_backend`. It does not become the
owner of the complete local archive, protected local effects, PresuPro
processing, Holded integration, or backend database state.

## Product context

The current deployed Cabinet site is static. Its browser reads generated JSON,
and its nginx site has no `/api` boundary. A live Cabinet MCP service is already
available to online ChatGPT through the authenticated server tunnel. The
observed plugin currently exposes four read-only operations: provider search,
project listing, project summary, and Invoice search. That is the proven
starting transport, not the complete target product surface.

`Cabinet_web` and `cabinet_backend` are autonomous applications:

```text
Cabinet_web
  owns confirmed Card facts, Card revision identity, source identity,
  source provenance, and the user-facing synchronization state

Cabinet Web Backend on VPS
  owns safe server ingress, working custody required for delivery,
  exact Invoice transfer packages, source-byte availability,
  transfer-side evidence, Registry catalogue replica, and acknowledgements

cabinet_backend
  owns durable local replicas, protected source-byte custody,
  local effects, synchronization attempts, durable-acceptance receipts,
  reconciliation, processing evidence, and operational audit
```

Temporary unavailability of `cabinet_backend` must not make Cabinet Web
unusable or cause accepted user input to disappear.

## Actors

### Cabinet user in online ChatGPT

The human user works primarily in the online ChatGPT conversation with the
Cabinet plugin. Through narrow Cabinet Web application capabilities the user
must be able to find and inspect Cabinet information and, after explicit
authorization for effects, perform the accepted Cabinet Web changes. ChatGPT
does not access storage, deployment internals, or `cabinet_backend` directly.

The user works with all existing Cabinet Web information independently of the
local backend. The user does not manually start every transfer in the normal
cycle; the local evening session owns synchronization initiation.

For an Invoice, the user normally attaches a PDF or photo in ChatGPT. ChatGPT
may extract the facts and uses explicit Cabinet plugin effects to create or
update a draft Invoice Card and, when requested, derived shopping-list
artifacts. Uncertain or missing facts are left for user correction in the chat
or secondary form. The user confirms the effect rather than relying on
unreviewed recognition.

The user does not supply or handle a `cabinet_backend` service credential.

### Browser client (secondary surface)

The browser is an untrusted network client even when the user has passed the
current nginx Basic Auth boundary. It may call only the accepted Cabinet Web
server surface. Browser state, hidden controls, and knowledge of an entity ID
are not authorization evidence.

### Cabinet plugin server

The Cabinet plugin server is the mandatory application boundary between online
ChatGPT and Cabinet Web. It exposes named, typed, narrow operations and calls
Cabinet Web application services; it is not a generic database, filesystem, or
backend proxy.

Read and effect capabilities remain distinguishable. The existing four
read-only tools prove reachability but do not by themselves authorize create,
update, upload, delete, synchronization, or operator effects. Each target
effect must have an explicit capability, validation, idempotency behavior,
bounded result, and authorization/approval policy.

### VPS operator

The operator deploys, configures, backs up, diagnoses, and rolls back the
Cabinet Web Backend through the protected server administration boundary. The
operator boundary is not exposed as a public administration API.

### Local Cabinet Backend machine actor

The local `cabinet_backend` initiates the evening connection and authenticates
to Cabinet Web with a machine identity scoped to Invoice pull, read-only
reconciliation, and Registry catalogue publication. Cabinet Web does not call
into the local network.

Neither side may turn caller-supplied values into a principal, grant, effect
scope, backend object path, database identity, or arbitrary operation selector.

### `cabinet_backend`

The local backend is an intermittently reachable external system from the
perspective of Cabinet Web. It independently authenticates, authorizes,
validates, accepts, rejects, deduplicates, and audits every requested effect.

## First user-visible full cycle

The server product covers every currently implemented Cabinet Card type and
existing owned artifact, but the local synchronization boundary is deliberately
narrower:

```text
Cabinet Web -> cabinet_backend: Invoice Cards and their source files only
cabinet_backend -> Cabinet Web: compact Registry catalogue package only
```

Provider, Client, Project, shopping-list, estimate, procurement, and other
Cabinet Web-owned information remains in the autonomous Web application and is
not copied to the local backend by this cycle.

The first fully evidenced source-bearing cycle handles one confirmed Invoice
Card revision at a time:

```text
local cabinet_backend starts the evening synchronization session
→ authenticates to Cabinet Web and observes contract compatibility
→ discovers/selects one pending exact Invoice work item
→ pulls the exact manifest, immutable Card revision, and required source bytes
→ cabinet_backend durably accepts the package in its own archive
→ cabinet_backend verifies durable acceptance for the exact Card hash and
  required source identities
→ an uncertain transport result is reconciled through a read-only lookup and
  is never repeated blindly
→ cabinet_backend publishes the newest compact Registry catalogue package
→ Cabinet Web atomically accepts or idempotently acknowledges that catalogue
→ the local connection closes; Cabinet Web continues operating independently
```

Card acceptance and source-byte attachment are distinct effects. A Card receipt
must never claim that source bytes are stored. A source attachment must never
run against an unaccepted or mismatched Card/source identity.

## Observable outcomes

### Existing ChatGPT and Card behavior preserved

These outcomes already exist in the Cabinet_web application at the pinned
repository revision and are preserved when exposed through the server plugin:

- a search returns bounded matching Card summaries and match reasons; no match
  is a successful empty result and changes nothing;
- draft preparation returns a reviewable normalized proposal with explicit
  missing facts, warnings, validation errors, and possible duplicates;
- successful draft creation returns the stored Card identity and exact revision
  evidence; invalid input, an existing target, or an unsafe duplicate condition
  produces a structured non-write outcome;
- successful draft update returns the new exact revision; a stale expected
  revision returns a conflict and never overwrites the current Card;
- repeated identical writes with the same operation identity return the prior
  result rather than creating another logical effect;
- confirmation applies only to the exact reviewed revision after required
  warning and duplicate acknowledgement; declining or withholding confirmation
  leaves the draft unchanged;
- shopping-list derivation returns the validated list and totals from the
  accepted estimate; invalid estimate arithmetic is rejected, and derivation
  alone does not silently persist a Project Card mutation;
- failure to preserve conversation attachment bytes is reported separately and
  never changes a successful structured-Card result into a false stored-source
  result.

The currently deployed plugin exposes only part of this behavior as reads. The
new server transport must expose the accepted existing application outcomes
without moving their rules into MCP wrappers.

### Complete success

The exact confirmed Card revision and required source bytes are durably accepted
or already accepted by `cabinet_backend`. The local backend possesses its
authoritative acceptance evidence, Cabinet Web exposes truthful transfer-side
status, and the exact Registry catalogue delivery is acknowledged.

The user sees that the full cycle is complete for the exact Card content hash
and source identity.

### Backend temporarily unavailable

No outbound connection from the VPS is attempted. Cabinet Web retains its
Invoice revision and source bytes for the next evening session and does not
claim local acceptance. The local backend owns retry/reconciliation behavior
for an already issued transfer.

Cabinet Web remains available for its independent supported behavior.

### Card rejected

No source attachment is attempted. The user receives a bounded reason that can
be acted on without disclosure of backend storage, credentials, raw audit
records, or internal database identities.

### Reconciliation required

No last-write-wins overwrite occurs. Cabinet Web preserves the attempted
revision and the bounded backend-current revision identity needed for a later
explicit reconciliation decision.

### Card accepted, source attachment incomplete

The accepted Card receipt remains durable. The user sees a partial outcome and
may safely resume the source step without resending the Card as a different
revision or claiming full completion.

### Invalid or mismatched source

Malformed, unsupported, oversized, or identity-mismatched bytes are rejected
without publication as accepted backend custody. The confirmed Card is not
rewritten to manufacture a media type, hash, filename meaning, or source
identity.

### Duplicate submission or uncertain response

A timeout or repeated user action does not create a second logical delivery.
The service resumes or reconciles the existing intent and shows the resulting
bounded receipt.

## Sources of truth and ownership

| Concern | Authoritative owner | Cabinet Web Backend treatment |
| --- | --- | --- |
| Confirmed Invoice Card facts | `Cabinet_web` | Deliver the exact immutable revision; never rewrite it during transport. |
| Card revision identity | `Cabinet_web` canonical content hash plus Invoice identity | Recompute and verify before delivery; preserve in progress and receipts. |
| Source identity inside the Card | `Cabinet_web` | Preserve exactly; never mint or replace it in the backend adapter. |
| Git revision provenance | `Cabinet_web` repository history | Preserve separately from Card content identity. |
| Source bytes before local durable acceptance | Cabinet Web Backend working custody | Protect durably enough to survive backend outage and service restart. |
| Complete durable source custody | `cabinet_backend` | Accept only through the protected backend effect and report a bounded receipt. |
| Local replica and effect audit | `cabinet_backend` | Never infer from a network success alone or expose raw storage details. |
| Delivery intent, attempts, and receipts | Cabinet Web Backend | Preserve durable user-visible progress and idempotent resume evidence. |
| PresuPro mappings and local processing | `cabinet_backend` or its accepted integrations | Outside the first server slice. |

## Product-level invariants

1. One synchronization target is one exact confirmed Invoice Card revision,
   identified independently from a retry attempt.
2. The complete confirmed Card document crosses the boundary; a lossy browser
   or backend projection is not substituted for the source revision.
3. The confirmed Card is never rewritten by transport, reconciliation, media
   detection, or source attachment.
4. Source identity comes only from the owning Card.
5. Card acceptance never implies source-byte attachment.
6. Source attachment is allowed only for the already accepted matching Card and
   source identity.
7. Retry and uncertain responses do not create duplicate logical effects.
8. A stale backend base produces reconciliation, not last-write-wins overwrite.
9. Backend unavailability preserves durable pending work and never produces a
   false completed state.
10. ChatGPT and browser callers never receive machine credentials or direct
    backend access.
11. Cabinet Web remains autonomous; unrelated supported behavior does not
    require continuous `cabinet_backend` availability.
12. Success evidence is bounded and never exposes backend database keys,
    filesystem/vault paths, credentials, or raw audit storage.
13. Deployment or restart must not discard accepted uploads, pending delivery
    intents, partial receipts, or reconciliation evidence.
14. The exact deployed source/spec lineage must be identifiable and reversible.

## Persistent product information

The first slice requires Cabinet Web to preserve durable conceptual information
for:

- exact available Invoice revisions and their source relationships;
- protected source bytes until local durable acceptance permits release;
- stable manifest/work identity exposed to the local pull boundary;
- transfer-side issuance and acknowledgement evidence;
- the current accepted Registry catalogue replica and its identity;
- Registry publication idempotency and acknowledgement evidence;
- the last successful local synchronization observation;
- bounded pending, conflict, or unknown status visible to the user;
- actor and request provenance sufficient for operational audit.

The local backend, not Cabinet Web, owns:

- the synchronization attempt and its durable reservation;
- the expected local/archive base revision when applicable;
- Card and source acceptance receipts;
- read-only reconciliation of an unknown issued transfer;
- durable-acceptance verification and local retention evidence.

This list does not select a database, table layout, queue library, or physical
file layout.

## External systems and trust boundaries

### Public HTTPS, ChatGPT plugin, and browser boundary

The VPS edge terminates TLS and exposes only the accepted same-origin Cabinet
Web surface. The application server remains behind the edge rather than
publishing an unrestricted backend port.

The current nginx Basic Auth protects the secondary browser surface. It is not
the ChatGPT plugin identity or effect-authorization boundary.

### Upload/file boundary

Source bytes are untrusted input. Product acceptance must separately close
payload size and supported content, parser-backed media identity, filename/path
ownership, non-executable treatment, isolated storage, and later retrieval
authorization.

Conversation understanding and original-byte custody are distinct outcomes.
ChatGPT may extract Invoice facts from a conversation attachment, but Cabinet
Web must not claim that the original is stored until its own upload receipt
exists.

### GitHub/repository boundary

The current Cabinet repository owns accepted Card history. Repository state is
external input to the server runtime and cannot be trusted merely because a
path or commit string was caller supplied.

The deployed Cabinet release currently diverges from repository `main`; release
lineage must be reconciled before Stage 9 rather than hidden by the server
adapter.

### Cabinet backend boundary

The connection is authenticated, encrypted, capability-limited, replay-aware,
and fail-closed. Exact network direction and transport remain open until the
real `cabinet_backend` deployment boundary is available for evidence review.

### ChatGPT plugin boundary

The authenticated tunnel is mandatory transport and already works. Read-only
MCP authorization and effectful Cabinet authorization remain separate: tunnel
reachability alone does not grant an effect scope. Effectful tools must be
declared as such and receive the appropriate approval and server-side
authorization treatment.

### Operator and secret boundary

Machine credentials and deployment secrets are injected through protected host
configuration. They are absent from source, browser assets, Card documents,
receipts, logs, errors, exported evidence, and process arguments.

## Availability and recovery boundary

The VPS remains the continuously available side. The local backend may be
offline for an extended period.

The Cabinet Web side must therefore distinguish at least:

- Invoice revision and source available for local pull;
- exact package issued to the authenticated local node;
- transfer outcome unknown from the VPS perspective;
- explicit local acceptance/release evidence received, if that reciprocal
  evidence is included in the accepted boundary;
- current Registry catalogue accepted;
- Registry catalogue stale because no later evening session completed.

Archive acceptance, durable verification, and reconciliation states remain
owned by the local backend.

Process restart, container replacement, network timeout, or repeated submission
must not erase or ambiguously duplicate these states. Exact retention duration,
retry timing, and operator recovery procedure belong to State 2.

## Operational constraints visible at State 0

- the existing VPS nginx owns public ports 80 and 443;
- the Cabinet application service should remain private behind the edge;
- the existing Panelforge listener on loopback port 8008 is unrelated and must
  not be reused;
- Client Portal is a separate application and deployment;
- deployable code and runtime state must remain separable;
- health/readiness must distinguish a live Web backend from availability of the
  intermittent local backend;
- release replacement must preserve durable state and support rollback;
- backups must cover every pending Invoice revision or source artifact whose
  loss would make the next local pull incomplete.

## Explicit non-goals for the first slice

The first slice does not:

- regenerate or replace `cabinet_backend`;
- deploy `cabinet_backend` on the Cabinet Web VPS merely for convenience;
- expose the complete Cabinet server, storage, or backend API to ChatGPT or the
  browser;
- proxy arbitrary backend operation names or caller-supplied effect scopes;
- give ChatGPT, the browser, or the user direct database, vault, or filesystem
  access;
- perform PresuPro matching, Holded publication, accounting, or complete local
  analytics;
- provide server-side or deterministic OCR for Invoices or receipts;
- restart or redesign Client Portal;
- resolve conflicts by arrival order or last-write-wins;
- claim full completion after Card acceptance alone;
- invent missing Card facts, source identity, MIME identity, or upstream hashes;
- define Python functions, HTTP routes, SQL tables, container topology, or
  framework dependencies at State 0.

## Stable decisions recorded so far

1. The first server slice supports the full evening synchronization session,
   not a continuously connected distributed application.
2. The new backend belongs to `Cabinet_web` and is distinct from
   `cabinet_backend`.
3. `Cabinet_web` remains autonomous when the local backend is unavailable.
4. The backend product boundary covers Provider, Client, Project, and Invoice
   Cards plus the project-owned data and artifacts already implemented in
   `Cabinet_web`.
5. Drivers, carriers, workers, shops, and similar working resources remain
   Provider Cards unless a later product decision introduces a distinct type.
6. Only Invoice Cards and their source files flow from Cabinet Web to the local
   backend. Other Cabinet Web-owned Card and artifact types remain on the Web
   side.
7. Only a compact Registry catalogue package flows from the local backend to
   Cabinet Web; Registry remains its source of truth.
8. All network connections are initiated by the local backend during the
   evening session; the VPS never calls into the local network.
9. The normal Invoice interaction starts with a PDF or photo attached in
   ChatGPT. ChatGPT creates the structured draft through the Cabinet plugin.
   Original-byte custody uses a protected short-lived Web upload handoff bound
   to the exact `invoice_id` and Card-owned `source_id` unless direct attachment
   transfer is later proved by an integration test.
10. The first fully evidenced source-bearing semantic unit is one exact
   confirmed Invoice Card revision plus its separately attached original source
   bytes.
11. Card acceptance and source attachment remain separate protected effects with
   separate truthful outcomes.
12. The local backend owns transfer reservation, archive receipt, durable
    verification, and read-only reconciliation; Cabinet Web owns its
    transfer-side evidence and Registry acknowledgement.
13. Inter-service credentials remain server-side and never enter the browser or
   Card facts.
14. The first release is single-user and retains nginx Basic Auth for the human
    browser boundary, with same-origin and CSRF protection for state-changing
    operations; no application account/session system is introduced.
15. Human Basic Auth and the local backend machine identity are separate
    credentials and cannot substitute for each other.
16. Existing Client Portal deployment patterns may be evaluated as evidence but
   do not define Cabinet product semantics.
17. The formal legacy `Cabinet_web` Factory spec will be replaced only after the
   Workbench states, assembly review, and Stage 9 admission complete.
18. Online ChatGPT with the already connected Cabinet server plugin is the
    primary UI/UX and a mandatory release boundary; the ordinary Web UI is
    secondary.
19. The plugin calls Cabinet Web application capabilities and never
    `cabinet_backend`, storage, or arbitrary server operations directly.
20. The currently deployed four read-only plugin tools are retained as proven
    transport evidence, but they are not the full target capability set.
21. ChatGPT extraction, Card mutation, and source-byte custody are three
    separately evidenced outcomes; none implies either of the others.
22. Web upload is a secondary byte-ingress surface, not a competing primary
    UI. It stores and binds original bytes but performs no OCR or fact
    extraction.
23. ChatGPT recognition is best-effort proposal generation. Missing or
    uncertain facts require human correction; the backend does not manufacture
    certainty or add a deterministic OCR subsystem.

## Resolved State 0 decisions

### Resolved decision D0-001 — current Cabinet coverage

The first server product covers everything `Cabinet_web` already implements:

- Provider Cards, including drivers, workers, carriers, shops, and other
  service providers represented by Provider facts;
- Client Cards;
- Project Cards and their existing project-owned facts;
- Invoice Card V1;
- existing shopping-list and accepted explicit cross-record artifacts.

Concepts that are only named but not yet defined or instantiated are outside
the current set. New Card types require explicit later product acceptance.

### Resolved decision D0-002 — hybrid ChatGPT and Web source ingress

The normal first-release workflow begins with the Invoice PDF or photo attached
in ChatGPT. ChatGPT reads the document and calls explicit plugin effects with a
structured Card draft and any requested derived shopping-list facts.

Every upload is bound to an existing exact `invoice_id` and that Invoice Card's
accepted `source_id`. A filename, browser field, or upload request cannot create
or replace source identity.

Successful ingress means only that Cabinet Web has accepted the bytes into
protected VPS custody for later local pull. It does not mean that
`cabinet_backend` has received or durably accepted them.

Original bytes enter Cabinet Web custody through a protected short-lived upload
handoff bound server-side to the existing exact `invoice_id` and Card-owned
`source_id`. A filename, model-produced field, browser field, or upload request
cannot create or replace source identity.

If ChatGPT cannot extract the document reliably, the user completes or corrects
the draft in the conversation or secondary form. The Web ingress does not run
OCR and never manufactures a structured draft from source bytes.

Direct conversation-attachment byte transfer may replace the handoff later only
after an end-to-end integration test proves that the deployed ChatGPT/plugin
transport supplies the original bytes and the same custody invariants. It is
not required for the first release. Exact media formats, size limits, parser
validation, storage isolation, duplicate/conflict behavior, retrieval
authorization, and retention belong to State 2.

### Resolved decision D0-003 — human authentication boundary

The first controlled release is a single-user application and retains the
existing nginx Basic Auth boundary. It does not introduce application user
accounts, roles, registration, password recovery, or server-side human sessions.

The Cabinet Web application server remains reachable only through the trusted
same-host edge path. State-changing browser operations, including Invoice source
upload, require accepted same-origin and CSRF protection in addition to Basic
Auth. Exact enforcement, credential rotation, abuse controls, and recovery
belong to State 2.

Basic Auth authenticates the one human browser boundary only. It is never used
as the `cabinet_backend` machine credential, never reaches Card data or source
artifacts, and never authorizes a local synchronization capability.

It also does not authenticate online ChatGPT or authorize Cabinet plugin
effects. The plugin has its own authenticated server boundary and effect
approval policy.

### Resolved decision D0-004 — backend reachability direction

The local backend initiates one evening connection to the Cabinet VPS. Through
that connection it pulls Invoice work and publishes the Registry catalogue.
The VPS never initiates a connection to the local network.

The exact clock, command, and transport adapter belong to later states. Missing
pending-work discovery in the current backend interface remains a later
flow/contract gap, not a reason to reverse the connection direction.

### Resolved decision D0-005 — source attachment from the primary ChatGPT UI

Online ChatGPT is the primary UI and reads the user's attached Invoice. The
plugin receives the extracted structured proposal and performs only explicit,
authorized Cabinet effects. For durable original custody, it creates a
short-lived upload handoff to the secondary Web surface. Web ingress only
stores and binds the original; it performs no OCR. This avoids depending on
undocumented propagation of raw conversation attachment bytes into a remote
plugin tool call and avoids imposing document-recognition load on the backend.

### Resolved decision D0-006 — autonomous VPS durability

Cabinet Web is a standalone continuously available Web application, not a
cache or online façade for `cabinet_backend`. PostgreSQL on the VPS is the
authoritative metadata, identity, revision, effect, custody, transfer, conflict,
Registry-replica, and recovery store for Cabinet Web-owned facts.

Original source bytes are held in one mandatory Cabinet Web-owned protected
local filesystem store on the VPS. The store survives application replacement
and process restart, is covered by backup and restore verification, and remains
fully usable while the local backend is offline. Source identity and integrity
are content-addressed; caller filenames and metadata never select a path.

The intermittent local backend connects only to the already durable Web-side
state during the accepted evening synchronization session. Its absence never
prevents Cabinet Web from accepting, reading, revising, or safely retaining its
own Cards and source bytes, and never turns PostgreSQL or the VPS byte store
into a replica of local state.

PostgreSQL transactions are the authority boundary for logical state. File
publication uses a recoverable staging protocol: write in the protected store,
flush, reopen and verify size and SHA-256, record recoverable publication state,
then atomically rename on the same filesystem. A source becomes available only
when committed metadata and the verified final file agree. Startup recovery
finishes or safely fails incomplete publications without exposing partial
bytes.

## State 0 placeholder resistance review

- The promised result cannot be implemented as `return {}`: completion requires
  two exact protected outcomes bound to Card revision and source identity.
- A simple forwarding proxy is insufficient: Cabinet Web owns protected source
  custody, exact pull packages, transfer-side evidence, Registry replica
  acceptance, and idempotent acknowledgement; local retry, reconciliation, and
  durable receipts remain local-backend responsibilities.
- Backend unavailability cannot be hidden as a generic error: it has a durable
  user-visible state and recovery expectation.
- Generic `payload`, `metadata`, `status`, or arbitrary operation selection is
  not accepted by this product boundary.
- Transport technology cannot silently decide ownership, authentication,
  reconciliation, or source-retention policy.

## State 0 exit review

```text
product outcome concrete                         PASS
Cabinet Web / local backend autonomy             PASS
current Cabinet-owned information bounded       PASS
Invoice-only Web -> local data flow              PASS
Registry-only local -> Web data flow             PASS
local-initiated evening connection               PASS
primary online ChatGPT UI/UX selected            PASS
mandatory existing plugin transport selected    PASS
ChatGPT source attachment path                   PASS
original-byte Web handoff without server OCR     PASS
human authentication boundary selected          PASS
human and machine credentials separated         PASS
backend-offline behavior explicit                PASS
success, partial, conflict and failure visible   PASS
State 0 open questions                           0
existing Cabinet behavior evidenced              PASS
current Cabinet repository check (85 tests)      PASS
```

State 0 is accepted. State 1 model authoring has not started.
