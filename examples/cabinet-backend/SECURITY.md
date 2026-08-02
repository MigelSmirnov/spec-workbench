# Cabinet Backend — Layer 0 security boundary

## Status

The primary deployment and trust boundary is **ACCEPTED** for the first personal
product. Detailed implementation choices remain for later states.

Cabinet is split across two locations:

```text
ChatGPT
  → Cabinet MCP / Cabinet application on VPS
  → authenticated private connection available only while the local platform is online
  → Cabinet Backend on the user's local machine
  → local PostgreSQL, source files, Registry, and PresuPro
```

Cabinet Backend is not a public ChatGPT integration and is not an MCP server.
ChatGPT communicates only with Cabinet. Cabinet is the only remote client of
Cabinet Backend.

## Accepted architectural boundary

### VPS side

The VPS hosts the user-facing Cabinet application and its MCP boundary. It may:

- authenticate the user-facing session;
- expose narrow Cabinet tools to the conversational agent;
- display local-platform availability;
- request reads and commands from the local Backend while the private connection
  is active;
- retain only the explicitly selected cache or transfer evidence.

The VPS does not become the authoritative store for Cabinet business data by
default. It does not directly connect to local PostgreSQL, Registry, PresuPro,
or local source-file storage.

### Local side

The user's local environment hosts:

- Cabinet Backend;
- authoritative Cabinet PostgreSQL data;
- authoritative original invoice and document files unless a later decision
  selects another private store;
- Registry;
- PresuPro;
- local integration adapters needed by Cabinet Backend.

Cabinet Backend is the durable source of truth for Cabinet Cards, accepted
relationships, history, and integration evidence. Registry and PresuPro remain
their own sources of truth for project context and estimates.

### Connection model

The local Backend initiates or accepts only an authenticated private connection
between the known VPS Cabinet instance and the known local platform. Candidate
implementations include a private overlay network such as Tailscale or an
explicit SSH reverse tunnel.

The accepted requirements are implementation-neutral:

- no public Cabinet Backend port;
- no public PostgreSQL port;
- no public Registry or PresuPro port merely for Cabinet access;
- transport encryption;
- machine identity for both ends;
- allow-list of the single authorized Cabinet instance;
- revocable credentials;
- no trust based only on possession of an IP address or `project_id`.

A specific tunnel technology is still a later deployment choice.

## Availability boundary

The local platform is intentionally connect-on-demand. When the local machine
or private connection is unavailable, Cabinet on the VPS must report the local
Backend as offline.

In the first product, Cabinet must not silently queue authoritative mutations
for later execution. Operations that require the local Backend are rejected
with a clear unavailable result.

A future cache may support explicitly labelled stale or read-only views, but it
must not become an accidental second source of truth. Cached data must preserve:

- source system;
- source identity;
- observed revision or content hash when available;
- captured time;
- freshness state;
- sensitivity and retention classification.

## Identity and authentication

### Human boundary

The user's ChatGPT or Cabinet session authenticates access to Cabinet on the
VPS. This authentication terminates at Cabinet; it does not directly
authenticate to Cabinet Backend, Registry, PresuPro, or PostgreSQL.

The first product may be single-user. A separate Cabinet Backend end-user account
system is not required while Cabinet is its only client.

### Machine boundary

Cabinet VPS and local Cabinet Backend require separate machine-to-machine trust.
This trust may be provided by private-network identity, SSH keys, mTLS, signed
short-lived service credentials, or an equivalent deliberate mechanism.

Human authentication and machine authentication are independent:

```text
human identity → Cabinet VPS
Cabinet service identity → local Cabinet Backend
```

Compromise of a browser session must not automatically reveal reusable local
platform credentials.

## Authorization boundary

Cabinet exposes narrow product capabilities to the agent. The agent never gets
raw access to Cabinet Backend, PostgreSQL, local files, Registry, PresuPro,
shell, or network credentials.

Cabinet Backend remains responsible for deterministic validation of every
accepted command. At minimum it distinguishes:

- read and search;
- create or edit draft data;
- confirm or archive Invoice Cards;
- assign invoices to Work Objects;
- confirm or reject PresuPro matches;
- request source files;
- publish an eligible invoice through Holded Gateway;
- export or delete data;
- administer connection and integration credentials.

The single-user baseline may grant these capabilities to one owner, but the
service boundary and sensitive-action confirmations still apply.

## Sensitive-action confirmations

The first product must require explicit user intent for operations with external
or destructive effects, including:

- confirming extracted invoice facts when they become durable business facts;
- publishing an invoice to Holded;
- correcting an invoice already published to Holded;
- deleting original source evidence;
- exporting fiscal or personal data;
- replacing connection or integration credentials.

Agent-proposed estimate matching may be accepted conversationally, but the
accepted match remains a separate Cabinet decision with provenance. An
unconfirmed heuristic proposal never enters plan-versus-actual calculations.

## Local data protection

Because the source of truth is local, the local machine is a production data
host and must not be treated as an unprotected developer laptop.

Required baseline controls include:

- operating-system account protection and disk encryption where supported;
- PostgreSQL bound only to localhost or a private local network;
- least-privilege database identity for Cabinet Backend;
- source files outside public or shared web directories;
- encrypted backup of both PostgreSQL and original files;
- restore testing;
- secrets outside source code, Cards, prompts, logs, and database business
  records;
- safe temporary-file cleanup;
- patching and revocation procedure if the machine or VPS is lost.

The exact backup store, key owner, rotation schedule, recovery objectives, and
retention period remain later choices.

## VPS data minimization

The VPS should retain the minimum information needed for the Cabinet experience.
The first design must classify every VPS-persisted value as one of:

- session or connection state;
- non-sensitive UI configuration;
- short-lived transfer buffer;
- explicit encrypted stale cache;
- durable audit evidence that cannot contain invoice bodies, source files,
  credentials, or unrestricted personal data.

Full invoice documents, database dumps, PresuPro estimates, and reusable local
platform credentials are not stored on the VPS by default.

## Integration boundaries

### Registry and PresuPro

Cabinet VPS does not call local Registry or PresuPro directly. Cabinet Backend
performs those calls inside the local trust zone and validates that returned
`project_id`, estimate identity, and revision evidence match the request.

### Holded Gateway

Holded publication remains independent. Holded credentials stay in Holded
Gateway, never in ChatGPT, Cabinet prompts, Cabinet Cards, or the local source
files. Cabinet Backend sends one authorized publication request with an exact
Invoice Card revision and receives a technical receipt.

The network location of Holded Gateway remains an open deployment choice. If it
is remote, the local Backend initiates an authenticated outbound connection.

## Untrusted content and agent safety

Invoice text, PDFs, images, supplier descriptions, notes, and PresuPro item names
are untrusted data. Instructions contained inside them do not grant tool access
or authorize commands.

The agent receives only narrow Cabinet tools. Tool calls are treated as requests,
not as proof of authorization. Cabinet and Cabinet Backend validate scope,
record state, revision, and confirmation requirements.

## Remaining security choices

The architecture now makes the main security direction clear, but these items
still require explicit design:

1. private connection technology and credential rotation;
2. Cabinet VPS login/session implementation;
3. exact cache policy and whether any business data persists on the VPS;
4. local disk encryption and operating-system hardening standard;
5. PostgreSQL and source-file backup destination, keys, retention, and restore
   procedure;
6. audit-event vocabulary and safe log retention;
7. Holded Gateway network placement and service authentication;
8. incident procedure for a lost local machine, compromised VPS, or leaked
   connection credential;
9. later multi-user authorization if Cabinet stops being a personal system.

## Layer 0 security decisions

1. Cabinet application and MCP boundary run on the VPS.
2. Cabinet Backend and authoritative Cabinet storage run locally for the user.
3. Registry and PresuPro remain in the local platform trust zone.
4. ChatGPT and the agent never connect directly to Cabinet Backend.
5. Cabinet VPS is the only remote Backend client.
6. Backend, PostgreSQL, Registry, PresuPro, and original files are not publicly
   exposed.
7. VPS-to-local communication uses authenticated encrypted private transport.
8. The local Backend is intentionally available only while the local platform
   and connection are running.
9. Authoritative writes are not silently queued while the local Backend is
   offline in the first product.
10. The VPS is not a second source of truth; any cache is explicit, minimal,
    labelled, and revocable.
11. Cabinet Backend validates persisted changes and external effects even when
    the request originated from an authenticated Cabinet session.
12. Holded credentials remain exclusively inside Holded Gateway.
