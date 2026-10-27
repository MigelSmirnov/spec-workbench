# State 0 — Registry product boundary

## Status

Reopened by the owner on 2026-10-27 for Registry vNext (R0-24). The first
frame was accepted as a whole on 2026-10-26 (R0-15) and closed after question
round 17. The owner's requirements document
`sources/registry_vnext_requirements_20261027.md` ("Registry — Project Identity
& Trusted Context", cited as vNext §n) and the owner's answers of 2026-10-27 on
its conflicts with that frame are recorded as R0-24 to R0-40; each names the
earlier decisions it replaces or narrows, and a replaced decision says so under
its heading. The sections above the decisions describe the frame as it stands
after them. State 0 closes again when its question rounds are clear; the owner
then accepts it as a whole.

Reverse-engineered from the running Registry and its v1 specification
(`SOURCE.md`): a decision that keeps, narrows or replaces a v1 decision (V1-n)
or a legacy finding (Ln) names it; an owner decision on a question the v1 never
raised names none. Nothing the code does is a decision until it is written here
or in a later state; the open questions are the owner's.

## Product statement

Registry is the platform's trusted entry point for project identity. It says
which projects exist, which customer each is for, which object it renovates and
which rooms it has; it keeps a catalogue of the documents other services
published about a project; and it lets the owner choose the project the agent
works on, handing the agent a bounded working context and nothing more
(vNext §1, §6). Every other service names a project by the Registry's identity
and reads that identity as a snapshot; none of them writes it back (V1-2).

Registry stores identity, the owner's choice of working project and pointers
only. Drawings, measurements, estimates, invoices, payments, funds, photos,
client publications, planner documents, Kernel functions and flows stay in the
services that own them (V1-1, V1-4, vNext §2). Registry is not a CRM, an ERP,
a ledger, a flow orchestrator, a runtime for agent code, a deployment manager
or the platform's general permission system (vNext §17).

## Actors and trust boundaries

- **Owner** — the one human principal. Creates, corrects and archives projects,
  records and corrects customers and objects, chooses the working project and
  reads personal data, through the owner interface Registry serves (R0-29),
  signed in with the owner credential (R0-30). The owner interface is a
  trusted surface of the owner, never a tool of an agent (vNext §5).
- **Agent** — any language-model agent acting for the owner. It reaches
  Registry only through Cabinet Kernel, with agent authority (R0-25, R0-31): it
  reads what the disclosure classes allow, works inside the working context the
  owner chose (R0-32), and may ask the owner to switch projects but never
  confirms a switch itself. It holds no owner credential and no Registry
  service token, never receives a `personal_data` value (R0-26), and has no
  administrative access to the production host, its store, configuration,
  secrets or deployment (R0-25). Preparing the owner's WhatsApp link no longer
  reads the customer's phone (R0-25).
- **Cabinet Kernel** — a consumer service that calls Registry's declared
  operations on the agent's behalf, with a service token that carries agent
  authority (R0-31). Registry does not know Kernel functions or flows (vNext
  §7).
- **Consumer services** — PresuPro, Client Portal, Cabinet, the Cabinet Web
  mirror. Each authenticates with its own service token (R0-27), validates a
  project id and reads its context in the disclosure class its token allows.
  Client Portal runs on the VPS and reaches the production Registry over a
  WireGuard channel the home server opens (R0-28, R0-39).
- **Producers** — any service publishing an artifact pointer with its own
  token: today PresuPro (estimates) and Cabinet Kernel. The pointer names its
  owner service, which is the authority for the artifact itself; Registry
  holds the pointer (V1-4). The type and its owner service come from the
  vocabulary the specification declares (R0-33). A service publishes only as
  the service its token names; the owner publishes for any owner service.
- **Browser** — the owner's browser, on the owner interface only, over HTTPS
  when it is not on Registry's host (R0-29). No other browser origin reaches
  Registry; the old frontend on its own origin is retired (R0-29).
- **Customer** — the person or company a project is for. Never reaches
  Registry; the owner records their contact data in a Customer record (R0-06).
- **Production host** — the owner's home server, a machine on which no agent
  runs and to which no agent has shell, store, configuration, secret or
  deployment access (R0-28). Everything with administrative access to it is the
  owner. Registry's guarantees hold against callers of its surfaces; the owner
  administers the host outside them.
- **Test instances** — any other instance (the agent's machine, a rig, a
  developer laptop). Each holds its own identity space and no production
  personal data; nothing moves between an instance and production except by an
  explicit import (R0-34).
- **Network surface** — two surfaces of one process: the service API for
  services, reachable only on the production host and over the protected
  channel (R0-28); and the owner interface, reachable remotely only through
  HTTPS (R0-29). Every request on either is authenticated; anything not
  authenticated is refused (R0-27).
- **Secrets** — service tokens and the owner credential, in the production
  instance's configuration, which only the owner changes, outside Registry
  (R0-20, R0-23); never in a record, a log line, an audit entry or an answer.
- **Personal data** — the customer's contact data and the object's address and
  identifying characteristics are `personal_data`; a project's identity is not
  anonymous by itself (R0-26). Only the owner reads `personal_data` values.

## Primary actions

| action | who | output | failure |
|---|---|---|---|
| create a project | owner; a service with a service token (today Cabinet Kernel) | the project with its identity — supplied by the caller or minted (R0-07) — status `active`, revision 1 | missing name refused; a customer reference that is unknown or erased refused (R0-16); an equal replay returns the existing project, a different one with the same id is refused (R0-07); a replay without an id never creates a second project (R0-36) |
| read a project | owner; a service, in its disclosure class (R0-26) | the project card (any status, V1-7) with its object and rooms, its revision; the project's id stands at the top of the answer (R0-13) | unknown id refused as not found; a caller without access refused |
| list projects | owner; a service, in its disclosure class | the active projects, and when asked the archived ones together with them (never the archived alone), in a declared order (L10), as one answer object (R0-13) | — |
| correct a project | owner | the project with the new name, customer or object, next revision | unknown id refused; an archived project refused (R0-12); a customer reference that is unknown or erased refused (R0-16); a stale revision refused, nothing changes (R0-35) |
| archive a project | owner, after confirming | the project, status `archived`; nothing is deleted (V1-7); archiving an archived project returns it unchanged (R0-12) | unknown id refused |
| validate a project reference | owner; a service | exists, active, and why not (`not_found`, `archived`) | — (the answer carries the failure) |
| read a project context | owner; a service, in its disclosure class | the snapshot a consumer keeps: id, display name, status, address, customer, created and updated times (R0-04) | unknown id refused |
| record a customer | owner | the Customer with the identity (`customer_ref`) Registry minted for it (R0-16), its kind — person or company — and its contact data (R0-06, R0-37) | missing name or kind refused; recording the same person again makes a second Customer (R0-16) |
| correct a customer | owner | the Customer with the new contact data, next revision | unknown customer refused; an erased customer cannot be corrected; a stale revision refused (R0-35) |
| read a customer | owner | name, kind, phone, e-mail, language | unknown customer refused; an erased customer answers that it was erased, with no contact data |
| list customers | owner | the customers, each with its `customer_ref` and name; erased ones only as erased, without contact data — this is how a customer is found for a new project | — |
| erase a customer's contact data | owner | the Customer keeps only its identity and the fact that it was erased; name, phone, e-mail and language are gone; projects still name it (R0-06) | unknown customer refused; erasing an erased customer returns it unchanged |
| restrict processing of a customer | owner | the Customer marked restricted: its contact data stays stored but leaves Registry to no one but the owner (R0-37) | unknown or erased customer refused |
| record or correct a project's object | owner | the object: its address, kind and the characteristics the specification declares; one object per project (R0-38) | unknown or archived project refused; a stale revision refused |
| add a room | owner; a service with a service token (today Cabinet Kernel) | the room: an identity Registry mints, the given name, its project (R0-10) | missing name refused; unknown or archived project refused; a second room of the same name is a second room (R0-10) |
| list rooms | owner; a service | the project's rooms in a declared order | unknown project refused as not found (replaces L21) |
| publish an artifact pointer | producer service; the owner for any owner service | the new pointer with the identity and version Registry assigns (R0-17), its content digest when given (R0-33), `published`; the previous published version of that type becomes `superseded` | unknown or archived project refused; a type the specification does not declare, or not the owner service's, refused (R0-33); neither `uri` nor `payload_ref` given refused (R0-17) |
| withdraw an artifact pointer | the producer service that owns it, or the owner | the pointer, status `withdrawn`; it stays in the history (R0-14) | unknown pointer refused; a pointer of another service, or already withdrawn or superseded, refused; a pointer of an archived project refused (R0-17) |
| list artifacts | owner; a service | every pointer of the project — published, superseded and withdrawn — each with its type, version and status; this is how history is read (R0-02) | unknown project refused as not found |
| read the latest artifact of a type | owner; a service | the one published pointer of that type | unknown project refused as not found; a type the specification does not declare refused as an unknown type (R0-17); a declared type with no published pointer answers that none is published — also after a withdrawal, which never falls back to an earlier version (R0-14) |
| choose the working project | owner | the working context: an opaque reference to the project, whether it is active, the context's version, the scope it allows and its expiry (R0-32) | unknown or archived project refused |
| read the working context | Cabinet Kernel for the agent; owner | the current working context, without any `personal_data` value | none chosen, expired or withdrawn answers that there is none |
| request a project switch | Cabinet Kernel for the agent | a pending request the owner sees in the owner interface; the working context does not change (R0-32) | unknown project refused |
| import a project with its identity | owner | the project under the identity it carries in its source, with its customer, object, rooms and pointers, after the owner checked the mapping (R0-34) | an id already held with different content refused; a mapping the owner has not confirmed refused |
| read the audit log | owner | the audit entries of significant operations, in time order (R0-37) | — |

## Decisions

### R0-01 — Registry owns project identity, nothing else (keeps V1-1, V1-2)

Registry is the single living owner of a project's identity: id, name, address,
customer reference and rooms. Consumers snapshot it at read time and never write
it back. Registry stores no service domain data.

Narrowed by R0-24: the working-context choice and the object are Registry's
too.

### R0-02 — Artifacts are pointers (keeps V1-4)

An artifact is catalogue metadata and a service-owned reference: `uri`,
`payload_ref`, at least one of them (R0-17). Registry never reads or stores the
payload. Publishing a new
version of a type supersedes the previous one; the history stays readable.

### R0-03 — Archived is readable (keeps V1-7)

Archiving never deletes. An archived project, its rooms and its artifacts stay
readable by id; lists leave archived projects out unless asked.

### R0-04 — The context and validate answers are external contracts (new, from the consumer table in `SOURCE.md`)

PresuPro and Client Portal read `validate` and `context` and pin their field
names. The re-authored Registry keeps both answers field for field (R0-13).

Narrowed by R0-26 and R0-27: the fields stay, but every read is authenticated
and carries the disclosure class of what it returns.

### R0-05 — One instance, one store (narrows L19)

An instance holds its own store. Two instances share nothing; the same physical
object in two instances is two projects unless the caller gives both the same
id (R0-07).

Narrowed by R0-34: exactly one instance is production; the others are test
instances with their own identity space.

### R0-06 — The customer is a Registry record (owner, 2026-10-26; closes OQ-01, L03)

Registry holds a Customer record: who the project is for and how to reach
them — name, phone, e-mail, language. `customer_ref` becomes the Customer's
identity, and a project names its customer by it. Fiscal data (NIF, legal
name) stays in PresuPro, which changes for a different reason. The operator
preparing the owner's WhatsApp link reads the phone from here, as staff. Name, phone, e-mail and language are
all the customer's contact data: personal data, readable by staff only (R0-09),
and erasable as a whole. Erasing leaves the Customer's identity and the fact
that it was erased, nothing else — the name does not survive. Erasure is an
explicit exception to R0-03, the only one.
Option (b), PresuPro `Client`, and option (c), nowhere, were declined.

Narrowed by R0-25 (no operator reads the phone; only the owner reads contact
data) and R0-37 (the customer's kind joins the record; restriction of
processing joins erasure).

### R0-07 — The caller may supply a project's identity (owner, 2026-10-26; closes OQ-02, replaces V1-5, L01, L02)

A caller may give the `project_id` when creating a project. A repeated create
with that id and equal content returns the existing project; with different
content it is refused, and nothing changes. Without an id the server still
mints one. One physical object can therefore carry one id across instances
(R0-05). V1-5 ("MUST NOT reuse caller-supplied identifiers") is replaced.
Options (b), a per-instance idempotency key, and (c), keeping server minting,
were declined.

Narrowed by R0-34 (an id crosses into production only by an explicit import)
and R0-36 (a create without an id is replay-safe too).

### R0-08 — The artifact vocabulary is configured, one owner per type (owner, 2026-10-26; closes OQ-03, replaces L08)

The artifact types an instance accepts, and the one owner service of each, are
a list in the instance's configuration, not in the specification: adding a type
needs no spec change. A pointer whose type is not listed, or whose owner service
is not that type's owner, is refused.

Replaced by R0-33.

### R0-09 — Writes and contact data need a credential (owner, 2026-10-26; closes OQ-04, replaces L15)

Each writing service holds a service token that names it; staff hold a staff
credential. Every write needs one of them; recording, correcting, reading or
erasing a customer needs the staff credential. Reads of projects, rooms,
artifacts, `validate` and `context` stay open on loopback and the host's
internal network (R0-19). How the frontend obtains the staff credential belongs to the frontend.

Replaced by R0-27 and R0-30.

### R0-10 — Rooms stay as they are (owner, 2026-10-26; closes OQ-05)

A room is created in a project and listed; it is never renamed or removed.
Nothing more is added until a consumer needs it.

### R0-11 — `project.list_active` is dropped (owner, 2026-10-26; closes OQ-06)

No consumer reads it (L11); `list projects` without archived answers the same
question.

### R0-12 — Archive is final (owner, 2026-10-26; closes OQ-07, replaces L05, L06)

An archived project never returns to `active` and cannot be corrected.
Archiving it again returns it unchanged — its updated time does not move.

### R0-13 — Lists answer an object; the project answer leads with its id (owner, 2026-10-26; closes OQ-08, replaces L09, L20)

Every list answers one object whose items are in a named field, never a bare
array. A project's answer carries its id at the top level, rooms beside it.
`validate` and `context` do not change (R0-04). The Registry frontend and
`onboard_object` follow the new shapes.

### R0-14 — A producer may withdraw its pointer (owner, 2026-10-26; closes OQ-09, replaces L22)

The owner service of a pointer, or staff, may withdraw it. A withdrawn pointer stays in the
history; "latest of a type" then answers that none is published and never falls
back to an earlier version.

### R0-15 — State 0 is accepted as a whole (owner, 2026-10-26)

The whole of this document, not only the numbered owner decisions, is the
product frame the later states build on. A change to it is a new owner decision
here.

### R0-16 — Registry mints `customer_ref`; a project's customer is optional (owner, 2026-10-26)

Recording a customer makes a new Customer whose `customer_ref` Registry mints;
a caller never supplies one, and recording the same person twice makes two
Customers — staff find an existing one with 'list customers' before recording.
A project may name no customer. When it names one, at creation or correction,
that Customer exists and is not erased; a project whose customer is erased
later keeps naming it (R0-06).

### R0-17 — Artifact pointers: references, versions, archive (owner, 2026-10-26)

A pointer carries `uri`, `payload_ref` or both; one with neither is refused.
Registry mints the pointer's identity and its version: 1 for the first pointer
of a type in a project, then one more than that type's last. Every accepted
publish is a new version, a repeat with equal content included; the previous
one is superseded and nothing is merged. Archiving a project freezes its
pointers: publishing and withdrawing on it are refused, reading stays open
(R0-03). Asking for the latest pointer of a type the instance does not
configure is refused as an unknown type, distinct from a configured type with
nothing published.

Narrowed by R0-33: "configure" reads "the specification declares".

### R0-18 — No launch-context action (owner, 2026-10-26; narrows V1-3)

Registry is the entrypoint only in that its project card holds what a
downstream service needs to open: `project_id` and the rooms with their ids.
Registry has no action that builds, validates or returns a launch context, and
calls no downstream service. V1-3's `source=registry` is the opening client's
concern.

Narrowed by R0-32: the working context the owner chooses is not a launch
context; Registry still calls no downstream service.

### R0-19 — Open reads stay inside the host (owner, 2026-10-27)

An instance listens only on its host's loopback or on an internal network of
that same host — on the VPS the compose network, where Client Portal reaches
it as `registry:8000` — and that network publishes no Registry port beyond the
host. Only processes and containers of that host belong to it; a private
network spanning several hosts does not. The owner's deployment definition enforces this — `--host 127.0.0.1`
locally, a compose service with no published port on the VPS — and the owner
checks it when deploying; no component detects an exposure, and Registry
starts and answers as usual either way. Registry itself does not tell callers
apart by address. An instance reachable from beyond its host is a wrong
deployment, not an allowed configuration: every unauthenticated read assumes
the caller is inside.

Replaced by R0-27 (no unauthenticated read), R0-28 (production on the home
server, Portal over a protected channel) and R0-29 (the owner interface over
HTTPS).

### R0-20 — The owner changes the configuration, outside the API (owner, 2026-10-27)

Service tokens, the staff credential, the artifact vocabulary (R0-08) and the
frontend origin are the instance's configuration. The owner, as the host's
administrator, changes it outside Registry; a change takes effect when the
instance restarts, and a replaced token stops working at that restart, with no
overlap. Registry has no action that reads or changes its configuration.

Narrowed by R0-29, R0-30 and R0-33: the configuration holds service tokens and
the owner credential; the vocabulary moves to the specification and the
frontend origin goes away.

### R0-21 — One id in two instances is a link, not one record (owner, 2026-10-27; narrows R0-05, R0-07)

When two instances hold a project under the same id, they hold two
independent records of one physical object. Each instance is the only owner of
its record (R0-01); the records may differ, and Registry neither copies,
synchronises nor compares them. A consumer reads the instance it is configured
with.

Narrowed by R0-34: production holds the authoritative record; a test instance
never shares production's identity space.

### R0-22 — The browser reaches Registry only on its host (owner, 2026-10-27)

The Registry frontend calls the API from the browser, admitted by CORS, only
where the browser runs on Registry's own host and reaches it on loopback. A
frontend used from another machine goes through a server of its own on
Registry's host; that server is a caller inside the host's network like any
other, holds the staff credential for staff actions, and is designed with the
frontend, not here.

Replaced by R0-29.

### R0-23 — Configuration is set on the host; secrets travel by the owner's hand (owner, 2026-10-27)

An instance's configuration is set on its host, readable only by the owner and
the Registry process: on the VPS the compose environment file, on a local
instance the environment it is started with. The owner generates each service
token and the staff credential, keeps the original in the owner's own password
vault (Bitwarden), and writes it into Registry's configuration and into the
configuration of its holders: a service token into the one service it names,
the one staff credential into each tool acting as staff — the operator, a
frontend server. Neither Registry nor any holder reaches the vault; the
platform has no secret manager. A secret crosses from the owner to a host only
by the owner's hand, so the owner is that trust boundary. A token the owner has
not written into Registry's configuration is refused like any wrong one.

Narrowed by R0-25 and R0-30: the staff credential becomes the owner
credential, and no tool an agent runs holds it.

### R0-24 — Registry vNext: identity and trusted context (owner, 2026-10-27)

The owner reopens State 0 with the requirements document
`sources/registry_vnext_requirements_20261027.md`. Registry becomes the
platform's trusted entry point: it keeps identity (project, customer, object,
rooms, artifact pointers) and the owner's choice of working project, and gives
the agent a bounded context of it. Every business entity has one authoritative
owner (vNext §2); the list of what Registry does not own (Product statement)
is part of this decision. A new responsibility enters Registry only by a
separate architecture decision (vNext §17).

### R0-25 — The agent is not the owner (owner, 2026-10-27; replaces the Host clause and the Operator actor of 2026-10-27, narrows R0-06, R0-23)

The agent acts for the owner but holds none of the owner's access. It reaches
Registry only through Cabinet Kernel, with agent authority (R0-31); it holds no
owner credential, no Registry service token, and no shell, store,
configuration, secret or deployment access to the production host (R0-28). No
`personal_data` value reaches it (R0-26). The WhatsApp message the owner sends
a customer is prepared without the phone: the agent emits the link without a
number and the owner picks the contact, or the owner interface supplies the
number to the owner. (The Factory's `AGENTS.md`/`CLAUDE.md` rule that reads
the phone from the Registry record is to be changed accordingly; that is the
Factory's change, not this case's.) The former Host clause — everything with
the owner's access to the host is the owner, an agent included — is withdrawn.

### R0-26 — Disclosure classes on every operation (owner, 2026-10-27; vNext §8)

Registry uses Cabinet Kernel's classes `open`, `business_confidential` and
`personal_data`. Every operation that returns data declares the class of each
output, checked by contract and semantic tests. The customer's contact data and
the object's address and identifying characteristics are `personal_data`; a
project's id is not anonymous by itself and is never `open` merely for being
an id. An answer that contains a `personal_data` value is never `open`; where a
caller needs both, Registry offers separate outputs or a dedicated projection
rather than one mixed answer. A `personal_data` value leaves Registry to the
owner and to a service whose token allows that class (R0-27) — never to an agent
(R0-25). Diagnostics never carry one (R0-37).

### R0-27 — Every request is authenticated; denial is the default (owner, 2026-10-27; replaces R0-09, R0-19's open reads)

No operation of Registry answers an unauthenticated caller. The owner signs in
to the owner interface (R0-30); each service — PresuPro, Client Portal,
Cabinet, Cabinet Kernel — holds its own service token, which names it and the
operations and highest disclosure class it may use. Anything a token does not
allow is refused. The Cabinet Web mirror, off active development, keeps its
read only if it receives a token of its own.

### R0-28 — One production Registry on the owner's home server (owner, 2026-10-27; replaces R0-19's topology)

The one authoritative production instance runs on the owner's home server, a
machine on which no agent runs and to which no agent has administrative access
(R0-25). Client Portal stays on the VPS and reaches it over a protected channel
between the two hosts (R0-39). When the home server or the channel is down,
Registry gives no consumer a stale or partial answer, and nothing changes in
Registry because of it (vNext §10); what a consumer then shows from its own
snapshot is its own (R0-39). The service API is
reachable only on the production host and over that channel.

### R0-29 — Registry serves the owner interface (owner, 2026-10-27; replaces R0-22 and the frontend exclusion)

Registry serves simple server-rendered HTML forms over its own operations
(vNext §5): the project list, creating a project, reading and correcting its
card (customer and object included), choosing the working project, archiving
with confirmation, and the customer, audit and switch-request views the
primary actions need. No client-side JavaScript is required. Reached from
another machine, the interface is reachable only through HTTPS; it never
exposes the service API beyond R0-28. Every change carries CSRF protection and
is validated on the server; a change made against an older revision is refused
(R0-35). No personal value appears in a URL. The old frontend on its own origin
(port 5174) and its CORS admission are retired.

### R0-30 — The owner credential (owner, 2026-10-27; replaces the staff credential of R0-09, R0-23)

There is one human principal, the owner. The owner signs in to the owner
interface with the owner credential and gets a protected session; the session
and its expiry belong to State 2. The owner credential is a secret as in R0-23
and is held by no tool, agent or service.

### R0-31 — The agent's operations go through Cabinet Kernel (owner, 2026-10-27; vNext §7)

Registry publishes its operations through the platform manifest
(`platform/manifest/registry.json`); the agent studies them, proposes operation
bindings, writes pure functions and runs flows in Kernel, and receives only
what K-14 lets through. Kernel's Registry token carries agent authority: the
operations and classes the owner allows the agent, confined to the working
context (R0-32). Registry stores no function or flow. No agent reaches
Registry's store; other trusted services reach Registry through their own
tokens.

### R0-32 — The owner chooses the working project (owner, 2026-10-27; vNext §6, narrows R0-18)

The owner chooses a project in the owner interface. The choice makes a working
context: an opaque reference to the project, whether it is active, the
context's version, the scope it allows and, when it expires, its expiry. The
context is bound to the owner's authorization, not to anything the agent sends.
It grants no read of personal data and no operation by itself. Operations with
agent authority on a project are confined to the project of the current context;
naming another `project_id` does not switch the context. The agent may request
a switch; only the owner confirms it.

### R0-33 — The artifact vocabulary is declared in the specification (owner, 2026-10-27; replaces R0-08, narrows R0-17)

The artifact types Registry accepts, and the one owner service of each, are
declared in the specification and in the platform manifest; a new type enters
by a specification change and a verified release, so the manifest always
matches the implementation (vNext §3.4, §9). A pointer may carry a content
digest of the artifact; Registry stores it and never computes or checks it
against the payload.

### R0-34 — Production identity is authoritative; test instances are separate (owner, 2026-10-27; narrows R0-05, R0-07, R0-21; vNext §4)

One project has one canonical `project_id` in production, used by Cabinet,
PresuPro and Client Portal. Test instances use an identity space of their own
and hold no production personal data. A project crosses into production only by
an explicit import whose mapping the owner checks — the projects already held
by the running instances included (migration) — and it keeps its links:
customer, object, rooms, pointers. Registry never merges two projects because
their name, address or customer look alike.

### R0-35 — Records carry a revision; stale changes are refused (owner, 2026-10-27; vNext §3.1, §11)

A project, a customer and an object carry a revision that every accepted change
moves. A change states the revision it was made against; a change against an
older revision is refused and nothing changes. Every change is atomic.

### R0-36 — No retried request creates a duplicate (owner, 2026-10-27; narrows R0-07, closes L02 for creates without id)

A create repeated after a lost answer — with or without a caller-supplied id —
never silently makes a second project, customer or room, and never damages one.
The mechanism belongs to State 2.

### R0-37 — Data protection the specification guarantees (owner, 2026-10-27; vNext §12, §13; narrows R0-06)

The specification guarantees the technical side of data protection and the
Code Factory checks it; the legal side is the governance's (Explicit
exclusions).

- **Customer.** The record keeps the customer's kind — person or company — next
  to the contact data; fiscal data stays in PresuPro (R0-06). Data is kept only
  where a stated purpose needs it and not duplicated.
- **Subject rights.** The owner can read, correct and erase a customer's contact
  data (R0-06), and restrict its processing: a restricted customer's data stays
  stored and reaches only the owner.
- **Retention.** Each kind of personal data and the audit log has a retention
  period after which it is erased; the periods are the owner's (R0-40).
- **Audit.** Every significant operation leaves an audit entry: time, the
  acting principal (owner, which service, agent through Kernel), the operation,
  the project, the outcome, the contract and release version, and a
  confirmation id where the owner confirmed. No password, token, whole card or
  unneeded personal value enters it. Only the owner reads it; its integrity is
  protected; it is kept for its retention period.
- **Diagnostics.** Logs other than the audit log carry no personal value and no
  secret.

### R0-38 — One project, one object (owner, 2026-10-27; closes OQ-10)

A project has exactly one object: its address, its kind and the technical
characteristics the specification declares. The address moves from the project
to the object; `context` keeps answering `address`, read from the object
(R0-04). Rooms stay on the project (R0-10). Options (b), an object carrying
several projects with the rooms on it, and (c), no separate object, were
declined.

### R0-39 — WireGuard from home; Portal keeps its own projection (owner, 2026-10-27; closes OQ-11, narrows R0-28)

Client Portal on the VPS reaches the production Registry over a WireGuard
tunnel that the home server initiates; the home server publishes no listening
port to the internet for it. The tunnel carries the service API only, with
Portal's service token as on any other request (R0-27). When home is
unreachable, Portal serves the last projection it was permitted to keep
locally: Portal's own snapshot of what its contract allowed (V1-2), never an
answer of Registry, and Portal changes nothing in Registry meanwhile. What the
projection holds and how old it may be is Portal's design, bounded by the
disclosure classes its token allows (R0-26).

### R0-40 — Retention periods (owner, 2026-10-27; closes OQ-12; provisional, subject to legal review)

- A customer's contact data: until the relationship with the customer ends,
  plus one year.
- The object's address and characteristics, and archived projects: five years
  after the project is closed (archived), unless another legal obligation
  requires longer.
- The audit log: two years.

When a period ends the data is erased or anonymised, respecting the mandatory
retention of the documents linked to it. The periods are provisional: the
legal review of the governance (Explicit exclusions) may change them, by a new
owner decision here.

## Explicit exclusions

- The operator script `onboard_object`: a client of the API like any consumer,
  designed elsewhere; its staff-credential use ends with R0-30, and its role is
  taken by the owner interface and Kernel flows.
- Drawings, measurements, planner documents, estimates and prices, invoices,
  payments, expense allocation, funds, photos, client publications, Kernel
  functions and flows (R0-01, R0-24). Splitting an invoice across projects is
  Cabinet's financial operation; Registry gives the canonical `project_id`.
- Orchestrating downstream services and building their launch context (R0-18).
- Fiscal customer data (NIF, legal name): PresuPro owns it (R0-06, R0-37).
- Sending anything to a customer.
- Capability Box package transfer: packages carry verifiable project references
  and source revisions; the receiver checks them (vNext §10).
- Deploying Registry, its release process and the host's administration (vNext
  §15). Registry does not manage deployment.
- The records of processing, the DPIA screening and, when needed, the DPIA
  itself, incident response and the other organisational measures. They are
  kept as platform-wide governance — Registry, Cabinet Kernel, Cabinet,
  PresuPro, Client Portal and the external AI providers — outside this case,
  citing the accepted Workbench decisions. The Code Factory checks the technical
  guarantees; the legal documents and the actual operation are subject to a
  separate independent review. This document is not a statement of GDPR
  compliance.

## Open questions

None open. OQ-01 to OQ-09 were decided by the owner on 2026-10-26 (R0-06 to
R0-14); OQ-10 to OQ-12, raised by the vNext reopening, on 2026-10-27 (R0-38 to
R0-40).

## Carried to later states

Questions the rounds judged to belong to a later state. Each is closed there,
not here.

- **State 1 (models).** The fields of Project, Customer, Object, Room, artifact
  pointer, working context, switch request and audit entry, and of each create
  request; the format of every identity (R0-07, R0-16, R0-17), and how a test
  instance's identity space is told apart from production's (R0-34); how the
  end of a customer relationship is recorded, and what an anonymised project,
  object or customer keeps (R0-40); revisions
  (R0-35); timestamps and which actions move a project's updated time (L16);
  how an erased or restricted Customer is represented in reads and lists; the
  disclosure class of each field (R0-26).
- **State 2 (rules).** What counts as equal content in a project-create replay,
  and a replay of an archived project's id; how a create without an id is made
  replay-safe (R0-36); correction semantics of projects, customers and objects —
  partial or whole, clearing a field (L04); the declared orders of every list
  (L10); what each service token and Kernel's agent authority may do, and which
  disclosure class each may receive (R0-27, R0-31); the working context's scope
  values, expiry and what ends it (R0-32); the owner session's lifetime and
  sign-in throttling (R0-30); the declared artifact vocabulary and what a change
  of it does to existing pointers (R0-33); publication as one transaction
  (L07); the import's mapping check (R0-34); audit-log integrity protection
  (R0-37); when and how expired data is erased or anonymised, and how linked
  documents' mandatory retention holds it back (R0-40); backup and tested
  restore (vNext §11).
- **States 5 and 6 (public APIs, contracts).** The field names of every list
  answer and of the project card; the exact `validate` and `context` answers
  (R0-04, the consumer table in `SOURCE.md`) and their disclosure classes; the
  fields of the artifact history; the error answer (L14); how a credential is
  presented and refused; the owner interface's routes; the manifest record of
  each operation — purpose, channel, route, input and output schemas, classes,
  effect class and preconditions, idempotency, contract version, known limits
  (vNext §9).
