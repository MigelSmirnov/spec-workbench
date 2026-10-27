# State 0 — Registry product boundary

## Status

Reopened by the owner on 2026-10-27 for Registry vNext (R0-24). The first
frame was accepted as a whole on 2026-10-26 (R0-15) and closed after question
round 17. The owner's requirements document
`sources/registry_vnext_requirements_20261027.md` ("Registry — Project Identity
& Trusted Context", cited as vNext §n) and the owner's answers of 2026-10-27 on
its conflicts with that frame are recorded as R0-24 to R0-60; each names the
earlier decisions it replaces or narrows, and a replaced decision says so under
its heading. In decisions before R0-24, "staff" reads "the owner" (R0-30) and
"the Registry frontend" reads "the owner interface" (R0-29). The sections above
the decisions describe the frame as it stands after them. The owner accepted
the reopened State 0 as a whole on 2026-10-27 (R0-75); a change found by a
later question round is a new owner decision here.

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
works on, handing each agent session a bounded set of projects and nothing more
(vNext §1, §6). Every other service names a project by the Registry's identity
and reads that identity as a snapshot; none of them writes it back (V1-2).
Registry is the one home of a customer's personal data and of the object's
address and identifying characteristics: the platform's target is that no other
service keeps a customer record or a copy of these values, except as fixed in a
document it issued and in Client Portal's offline projection (R0-80). Copies
that remain until each service removes them are listed in the governance
(R0-81). A consumer's kept
snapshot holds identity — id, alias, status, `customer_ref` — never a
personal value such as the address or the display name (R0-82).

Registry stores only identity — projects, their objects and rooms, customers
with their contact and fiscal data (R0-80) — the project access of each agent session and its
pending request, artifact pointers, and its own audit log. Drawings, measurements, estimates, invoices, payments, funds, photos,
client publications, planner documents, Kernel functions and flows stay in the
services that own them (V1-1, V1-4, vNext §2). Registry is not a CRM, an ERP,
a ledger, a flow orchestrator, a runtime for agent code, a deployment manager
or the platform's general permission system (vNext §17).

## Actors and trust boundaries

- **Owner** — the one human principal. Creates, corrects and archives projects,
  sees the whole catalogue, records and corrects customers and objects, chooses
  the working project of each agent session, imports projects and
  reads personal data, through the owner interface Registry serves (R0-29),
  signed in with the owner credential (R0-30). The owner interface is a
  trusted surface of the owner, never a tool of an agent (vNext §5).
- **Agent** — any language-model agent acting for the owner. It reaches
  Registry only through Cabinet Kernel, with agent authority (R0-25, R0-31): it
  works only on the projects the owner granted its session (R0-41, R0-46),
  sees each through a minimal projection without any value Registry holds as
  `personal_data` (R0-43; free text written by others, R0-68),
  creates no project, never sees the catalogue and never adds a project to its
  own set (R0-41, R0-46); it may ask the owner for access but never grants it. It holds no owner credential and no Registry
  service token, never receives a value Registry holds as `personal_data` (R0-26;
  for free text written by others see R0-68), and has no
  administrative access to the production host, its store, configuration,
  secrets or deployment (R0-25). Its language model runs at an external AI
  provider, which receives whatever the agent sees — from Registry, the agent
  projection, the access of its session and the answers to its operations — and
  is a recipient the governance records. Registry's guarantee covers what
  Registry gives Cabinet Kernel; that no other service passes a Registry
  `personal_data` value on to the agent is Cabinet Kernel's decision K-14 and
  that service's own contract (R0-74, R0-76). Preparing the owner's WhatsApp link no longer
  reads the customer's phone (R0-25).
- **Cabinet Kernel** — a consumer service that calls Registry's declared
  operations on the agent's behalf, with a service token that carries agent
  authority (R0-31) and never allows `personal_data` (R0-74). Registry does not know Kernel functions or flows (vNext
  §7).
- **Consumer services** — PresuPro, Client Portal, Cabinet. The Cabinet Web
  mirror holds no token and no longer reads Registry (R0-73). Each authenticates with its own service token (R0-27), validates a
  project id and reads what its token allows; `context` only with a token that
  allows `personal_data` — PresuPro, Client Portal and Cabinet, which receives the
  current projects (R0-43, R0-76).
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
- **Production host** — the trusted VM Platform on the owner's home server,
  where Registry, Cabinet Kernel, Cabinet and PresuPro run. The agent runs in a
  separate VM Agent on the same server, with no shell, store, configuration,
  secret or deployment access to VM Platform (R0-28, R0-48). Everything with
  administrative access to VM Platform or to the server is the owner. Registry's guarantees hold against callers of its surfaces; the owner
  administers the host outside them.
- **Test instances** — any other instance (the agent's machine, a rig, a
  developer laptop). Each holds its own identity space and no production
  personal data; nothing moves between an instance and production except by an
  explicit import (R0-34).
- **Legacy instances** — the v1 Registries running before production: the one
  on the VPS, inside Client Portal's network, and the local one. They hold real
  personal data, are administered by the owner and stand outside this
  document's guarantees. The VPS one is the migration's only source; each is
  retired once the migration is done (R0-79).
- **Network surface** — two surfaces of one process: the service API for
  services, reachable only inside VM Platform and over the WireGuard channel
  from the VPS, never from VM Agent (R0-28, R0-48); and the owner interface,
  reachable from outside only through the owner's VPN, over HTTPS (R0-29,
  R0-48). Every request on either is authenticated; anything not
  authenticated is refused (R0-27).
- **Secrets** — service tokens and the owner credential, in the production
  instance's configuration, which only the owner changes, outside Registry
  (R0-20, R0-23); never in a record, a log line, an audit entry or an answer.
- **Personal data** — the customer's contact and fiscal data and the object's
  address and identifying characteristics are `personal_data`; a project's identity is not
  anonymous by itself (R0-26). `personal_data` values reach the owner, and a
  trusted service only where its token allows that class (R0-26, R0-43); never
  an agent. The customer's contact data reaches the owner alone; its billing data
  reaches the owner and a service whose token allows reading it (R0-80).

## Primary actions

| action | who | output | failure |
|---|---|---|---|
| create a project | owner | the project with the identity Registry mints (R0-44), its object (R0-45), its display name and, when given, its alias (R0-82), status `active`, revision 1 | missing name, or an object without an address, refused (R0-45); a customer reference that is unknown, erased, restricted or ended refused (R0-16, R0-51, R0-57); a retried create never makes a second project (R0-36) |
| read a project | owner; a trusted service whose token allows `personal_data` (R0-43) | the project card (any status, V1-7) with its object and rooms, its revision, and for an archived project the date it was archived (R0-60); the project's id stands at the top of the answer (R0-13) | unknown id refused as not found; an anonymised project answers that it was erased (R0-62); any other caller refused — Kernel for the agent reads the agent projection (R0-43) |
| list projects | owner; a trusted service whose token allows `personal_data`; never Kernel for the agent (R0-41, R0-43) | the active projects, and when asked the archived ones together with them (never the archived alone), in a declared order (L10), as one answer object (R0-13); an anonymised project is never listed (R0-62) | — |
| correct a project | owner | the project with the new name, alias (R0-82), customer or object — address, kind, characteristics (R0-45) — next revision of the project | unknown id refused; an archived project refused (R0-12); newly naming a customer that is unknown, erased, restricted or ended refused (R0-16, R0-51, R0-57); a stale revision refused, nothing changes (R0-35) |
| archive a project | owner, after confirming | the project, status `archived`; nothing is deleted (V1-7); archiving an archived project returns it unchanged (R0-12) | unknown id refused |
| validate a project reference | owner; a trusted service; Kernel for the agent on a project its session is granted (R0-41, R0-46) | exists, active, and why not (`not_found`, `archived`) | — (the answer carries the failure) |
| read a project context | owner; a trusted service whose token allows `personal_data` (R0-43) | the project's context: id, display name, status, address, `customer_ref` (never contact data), created and updated times (R0-04) | unknown id refused; an anonymised project answers that it was erased (R0-62); a caller whose token does not allow `personal_data` refused |
| record a customer | owner | the Customer with the identity (`customer_ref`) Registry minted for it (R0-16), its kind — person or company — its contact data (R0-06, R0-37) and, when given, its fiscal data: tax id (NIF/NIE/CIF) and legal name (R0-80) | missing name or kind refused; recording the same person again makes a second Customer (R0-16) |
| correct a customer | owner | the Customer with the new contact data, kind or fiscal data — tax id, legal name (R0-80) — next revision | unknown customer refused; an erased customer cannot be corrected; a stale revision refused (R0-35) |
| read a customer | owner | name, kind, phone, e-mail, language, tax id and legal name; whether it is restricted, and the date its relationship was marked ended if it is (R0-60) | unknown customer refused; an erased customer answers that it was erased, with no contact data |
| list customers | owner | the customers, each with its `customer_ref`, name, and whether it is restricted or its relationship ended (R0-60); erased ones only as erased, without contact data — this is how a customer is found for a new project | — |
| erase a customer's contact data | owner | the Customer keeps only its identity and the fact that it was erased; name, phone, e-mail and language are gone; projects still name it (R0-06) | unknown customer refused; erasing an erased customer returns it unchanged |
| restrict or lift a restriction on a customer | owner | the Customer marked restricted, or no longer restricted where a lawful ground allows it; while restricted, its contact and fiscal data stay stored and reach no one but the owner (R0-80), no project may newly name it, and every other use of its contact data is refused — Registry admits no exception; where a lawful ground allows processing, the owner lifts the restriction (R0-65); corrections of its existing projects that do not use that data go on, and `context` keeps its `customer_ref` (R0-37, R0-51, R0-55) | unknown or erased customer refused |
| read the agent projection | Cabinet Kernel for the agent, on a project its session is granted (R0-46) (R0-41, R0-43) | the minimal projection of that project: its id, its alias when the owner gave one (R0-82), status, rooms and artifact pointers — no display name (R0-68), address, customer or other value Registry holds as `personal_data`; room names, the alias and pointer values are as their writers wrote them (R0-68, R0-82) | a project the session is not granted refused; an anonymised project answers that it was erased (R0-62) |
| add a room | owner; Cabinet Kernel for the agent, on a project its session is granted (R0-41, R0-46) | the room: an identity Registry mints, the given name, its project (R0-10) | missing name refused; unknown or archived project refused; a second room of the same name is a second room (R0-10); a project the session is not granted refused |
| list rooms | owner; a trusted service; Kernel for the agent on a project its session is granted (R0-46) | the project's rooms in a declared order | unknown project refused as not found (replaces L21); an anonymised project answers that it was erased (R0-62) |
| publish an artifact pointer | producer service; Cabinet Kernel only for the agent, on a project its session is granted (R0-41, R0-46); the owner for any owner service | the new pointer with the identity and version Registry assigns (R0-17), its content digest when given (R0-33), `published`; the previous published version of that type becomes `superseded` | unknown or archived project refused; a type the specification does not declare, or not the owner service's, refused (R0-33); neither `uri` nor `payload_ref` given refused (R0-17) |
| withdraw an artifact pointer | the producer service that owns it — Cabinet Kernel only for the agent, on a project its session is granted (R0-46) — or the owner | the pointer, status `withdrawn`; it stays in the history (R0-14) | unknown pointer refused; a pointer of another service, or already withdrawn or superseded, refused; a pointer of an archived project refused (R0-17) |
| list artifacts | owner; a trusted service; Kernel for the agent on a project its session is granted (R0-46) | every pointer of the project — published, superseded and withdrawn — each with its type, version and status; this is how history is read (R0-02) | unknown project refused as not found |
| read the latest artifact of a type | owner; a trusted service; Kernel for the agent on a project its session is granted (R0-46) | the one published pointer of that type | unknown project refused as not found; a type the specification does not declare refused as an unknown type (R0-17); a declared type with no published pointer answers that none is published — also after a withdrawal, which never falls back to an earlier version (R0-14) |
| list agent sessions | owner | the registered sessions, each with its granted project ids, its active project if any and its pending request if any (R0-47) | — |
| grant a project to an agent session | owner | the project joins the session's granted set; the owner may also make it the session's active project (R0-46) | unknown or archived project refused; unknown session refused |
| read the session's access | Cabinet Kernel for one agent session; owner | the session's granted project ids, its active project if any, whether it has a pending request, and the access version — no `personal_data` value (R0-32, R0-46, R0-64) | for Kernel, a session that is not registered refused like a call outside the set (R0-53); for the owner, an unknown session refused |
| request access to a project | Cabinet Kernel for one agent session | a pending request of that session, in free text, the owner sees in the owner interface, replacing the session's earlier pending one; the session's access does not change, and the answer says nothing about which projects exist (R0-46, R0-47) | a session that is not registered refused like a call outside the set (R0-53) |
| answer an access request | owner | either answer clears the pending request; granting adds the project the owner picks from the catalogue to the session's set (and, if asked, makes it active); declining leaves the set unchanged and keeps no reason; the session reads the outcome in its access (R0-46, R0-47, R0-64) | a request no longer pending refused |
| change the active project or revoke a project | owner | the session's active project changes, or is cleared, which revokes nothing (R0-70); or the project leaves the session's set, and every later operation on it in that session — a running flow's next step included — is refused (R0-46) | unknown session refused, as for granting; a project not in the set answers that it is not granted; an archived project cannot be made active (R0-70) |
| import projects with their identity | owner, confirming, from the VPS instance: the projects the owner picks (R0-79), each with a new display name and alias when the owner gives them (R0-85) | those projects under the identities they carry, with their customers, objects, rooms and pointers (ids kept), links intact (R0-34, R0-44, R0-50); a v1 `customer_ref` that is not a Registry-minted id becomes a new Customer with a minted `customer_ref`, the old value moving to its tax id when it is one, and its projects are linked to that Customer (R0-80) | any conflict with an id production holds refuses the whole import, nothing applied, and the owner may retry after correcting it; after the first successful import the operation is closed and refused (R0-79) |
| register an agent session | Cabinet Kernel | the session Registry knows, with no granted project; the owner sees it in the owner interface (R0-47) | — |
| end or resume a customer relationship | owner | the Customer marked as ended on the date the owner gives — today when none is given (R0-84) — or the mark cleared; archiving its projects does not end it (R0-49, R0-57, R0-60) | unknown or erased customer refused; an end date later than today refused (R0-84) |
| erase an archived project | owner, confirming | the project anonymised — its id, status and artifact pointers stay, its name, object and customer link go, `validate` answers `archived` — or deleted whole, `validate` answering `not_found`; the owner chooses (R0-60); either way it leaves every agent session's set and is active in none (R0-61) | unknown or active project refused; anonymising an anonymised project returns it unchanged, and deleting it whole is refused (R0-71) |
| read a customer's billing data | a trusted service whose token allows it — today PresuPro, when it renders a document, a draft or preview included, or issues one (R0-80); Registry checks the token, not the purpose of the call, which the service's own contract and the governance bind | the customer named by `customer_ref`: kind, tax id and legal name — for a person, the full name as on the identity document, which the owner records as its legal name — never its contact data, the ordinary name included; a fiscal value never recorded is marked absent, and the read is not refused for it (R0-83) | unknown customer refused; an erased or restricted customer refused (R0-65); any other caller refused |
| read the audit log | owner | the entries of significant changes of state, in time order (R0-58) | — |
| erase audit entries before a date | owner, confirming | every entry older than the date the owner gives is gone; the erasure leaves an entry of its own naming the date (R0-66) | — |

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

Narrowed by R0-60: the owner may erase an archived project, anonymised or
whole.

### R0-04 — The context and validate answers are external contracts (new, from the consumer table in `SOURCE.md`)

PresuPro and Client Portal read `validate` and `context` and pin their field
names. The re-authored Registry keeps both answers field for field (R0-13).

Narrowed by R0-26 and R0-27: the fields stay, but every read is authenticated
and carries the disclosure class of what it returns. Narrowed by R0-80: a consumer
keeps identity only; the address is read when used, not kept. Narrowed by
R0-82: the display name is read when used too; a kept snapshot holds the alias.

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
processing joins erasure) and R0-60 (erasing an archived project is a second
exception to R0-03, so erasure is no longer the only one) and R0-80 (fiscal data
joins the record; PresuPro keeps none).

### R0-07 — The caller may supply a project's identity (owner, 2026-10-26; closes OQ-02, replaces V1-5, L01, L02)

A caller may give the `project_id` when creating a project. A repeated create
with that id and equal content returns the existing project; with different
content it is refused, and nothing changes. Without an id the server still
mints one. One physical object can therefore carry one id across instances
(R0-05). V1-5 ("MUST NOT reuse caller-supplied identifiers") is replaced.
Options (b), a per-instance idempotency key, and (c), keeping server minting,
were declined.

Narrowed by R0-34 (an id crosses into production only by an explicit import),
R0-36 (a create without an id is replay-safe too) and R0-44 (in production
Registry mints every id on create; a caller-supplied id enters only by import).

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

Narrowed by R0-29 and R0-63: both are retired.

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

Narrowed by R0-73: the mirror receives no token.

### R0-28 — One production Registry on the owner's home server (owner, 2026-10-27; replaces R0-19's topology)

The one authoritative production instance runs on the owner's home server, a
machine on which no agent runs and to which no agent has administrative access
(R0-25). Client Portal stays on the VPS and reaches it over a protected channel
between the two hosts (R0-39). When the home server or the channel is down,
Registry gives no consumer a stale or partial answer, and nothing changes in
Registry because of it (vNext §10); what a consumer then shows from its own
snapshot is its own (R0-39). The service API is
reachable only on the production host and over that channel.

Narrowed by R0-48: the production host is VM Platform on the home server; the
agent runs in VM Agent beside it. "A machine on which no agent runs" reads "VM
Platform, in which no agent runs".

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

Narrowed by R0-45 (the interface carries every owner action) and R0-48 (from
outside it is reachable only through the owner's VPN).

### R0-30 — The owner credential (owner, 2026-10-27; replaces the staff credential of R0-09, R0-23)

There is one human principal, the owner. The owner signs in to the owner
interface with the owner credential and gets a protected session; the session
and its expiry belong to State 2. The owner credential is a secret as in R0-23
and is held by no tool, agent or service.

### R0-31 — The agent's operations go through Cabinet Kernel (owner, 2026-10-27; vNext §7)

Registry publishes its operations through the platform manifest
(`platform/manifest/registry.json`); the agent studies them, proposes operation
bindings, writes pure functions and runs flows in Kernel, and receives only
what Cabinet Kernel's decision K-14 lets through (case `cabinet-kernel`: no
`personal_data` value reaches an agent). Kernel's Registry token carries agent authority: the
operations and classes the owner allows the agent, confined to the working
context (R0-32). Registry stores no function or flow. No agent reaches
Registry's store; other trusted services reach Registry through their own
tokens.

Narrowed by R0-74: the classes Kernel's token allows never include
`personal_data`. Narrowed by R0-78: the manifest record is derived from the
specification and fits Kernel's binding rules.

### R0-32 — The owner chooses the working project (owner, 2026-10-27; vNext §6, narrows R0-18)

The owner chooses a project in the owner interface. The choice makes a working
context: an opaque reference to the project, whether it is active, the
context's version, the scope it allows and, when it expires, its expiry. The
context is bound to the owner's authorization, not to anything the agent sends.
It grants no read of personal data and no operation by itself. Operations with
agent authority on a project are confined to the project of the current context;
naming another `project_id` does not switch the context. The agent may request
a switch; only the owner confirms it.

Narrowed by R0-46: the owner grants each agent session a set of projects, one
of them optionally active; "the project of the current context" reads "a
project of the session's set".

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

Narrowed by R0-45: the object has no revision of its own; a change of it moves
the project's.

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
- **Retention.** The periods are the owner's policy in the governance, applied
  by the owner's periodic review with Registry's erase actions (R0-60).
- **Audit.** A minimal log of significant changes of state (R0-58): time, the
  acting principal (owner, which service, agent through Kernel), the change,
  the project or customer, the outcome, the contract and release version, and
  a confirmation id where the owner confirmed. No personal value, whole request
  or secret enters it. Only the owner reads it; it is kept for its documented
  period, and the owner erases older entries (R0-66).
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

Replaced by R0-60: the periods move to the governance's retention schedule.

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

### R0-41 — The agent works on its session's project only (owner, 2026-10-27; round 3 T1; narrows R0-31, R0-32)

Narrowed by R0-46: "its session's project" reads "a project its session is
granted".

Through Cabinet Kernel the agent reads and writes only the project the owner
chose for its session: it reads the agent projection (R0-43), validates that
project, lists and adds its rooms, publishes and withdraws Kernel's pointers on
it and reads its artifacts. Creating a project and seeing the catalogue — the
project list, other projects, customers — stay with the owner. Kernel no longer
creates projects (v1 kernel scenarios R1–R3 are history).

### R0-42 — A working context belongs to one agent session (owner, 2026-10-27; round 3 T13, T3; narrows R0-32)

Replaced by R0-46.

There is no global working project. Each agent session Kernel names has its own
working context, which the owner chooses, confirms on request or withdraws. A
session has at most one pending switch request; a newer one replaces it. A flow
pins the `project_id` of its context when it starts; a later switch or
withdrawal changes no flow already running. Archiving a project leaves a
context on it inactive, so agent writes on it are refused (R0-12). How Kernel
names a session, and what ends one, belong to State 2.

### R0-43 — The full context goes to trusted services; the agent gets a minimal projection (owner, 2026-10-27; round 3 T5; narrows R0-04, R0-26)

`context` keeps its fields (R0-04) and answers only a trusted service whose
token allows `personal_data` — today PresuPro and Client Portal. The agent,
through Kernel, reads a separate minimal projection of a project its session
is granted (R0-46)
with no personal value: id, display name, status, rooms and artifact pointers.
No answer mixes the two. The same holds for 'read a project' and 'list
projects': they carry the object's address and answer only a caller cleared
for `personal_data`. `context` names the customer by `customer_ref` only; no
contact data leaves Registry except to the owner.

Narrowed by R0-68: the projection carries no display name. Narrowed by R0-82:
it carries the project's alias when the owner gave one. Narrowed by R0-76:
Cabinet is a trusted service cleared for `personal_data` too.

### R0-44 — Production mints identities; import keeps them (owner, 2026-10-27; round 3 T10; narrows R0-07, R0-34)

In production Registry mints every project's id on create; a caller supplies
none. A project that already has an identity elsewhere enters production only
by import: a separate operation the owner confirms, which keeps the identity
and refuses a conflict with an id production already holds, changing nothing.
Where imports come from is R0-50.

### R0-45 — Object at creation, edited with the card, covered by the owner interface (proposed to the owner 2026-10-27 after round 3 T8, T11, T12, no objection; narrows R0-29, R0-35, R0-38)

A project is created with its object, and the object's address is required, as
in v1; `context` therefore always has an address. The object is part of the
project card: it changes through 'correct a project' and moves the project's
revision. The owner interface carries every action whose 'who' names the owner.

### R0-46 — An agent session is granted a set of projects (owner, 2026-10-27; round 4 T1–T3; replaces R0-42, narrows R0-32, R0-41)

The owner grants an agent session, in the owner interface, access to one or
more projects. Registry keeps for each session the set of granted
`project_id`s and at most one active project, the default when the agent names
none. The agent never receives the catalogue and never adds a project to its
set; it may request access, which only the owner grants. Comparing several
projects in one session is allowed within its set.

Kernel checks on every call that the `project_id` belongs to the session's
set, and Registry checks it again on every call, independently of Kernel, and
refuses an agent-authority operation outside it (R0-32, R0-47).
Changing the active project revokes nothing; the owner may also clear it, and
revoking the active project clears it (round 6 T10). Revoking a project blocks every
later operation on it in that session. A flow pins its project ids when it
starts; after a revocation each further step is checked again and refused for
the revoked project. Archiving a project keeps it in a set but refuses agent
writes on it (R0-12).

Narrowed by R0-61 (erasing a project removes it from every set), R0-64
(answering a request clears it), R0-69 (no project named and none active is
refused) and R0-70 (clearing the active project; no archived one is made
active).

### R0-47 — Sessions are registered by Kernel; requests are free text; Registry checks access itself (owner, 2026-10-27; closes OQ-16; narrows R0-46)

Cabinet Kernel registers each agent session with Registry; the owner sees the
registered sessions in the owner interface and grants each its projects. The
agent asks for a further project in free text; the owner picks the project from
the catalogue. Nothing the agent receives — an answer, a refusal, an access
read — tells it whether any project outside its set exists. Registry checks on
every agent-authority call, independently of Kernel, that the project belongs
to the session's set; a revocation holds for flows already running at their
next operation. Every agent-authority operation answers a project outside the
set exactly as it answers a project that does not exist, so a refusal reveals
nothing; Kernel's token never reaches a project outside the session's set,
whatever operation it calls (round 5 T3–T5).

### R0-48 — VM Platform and VM Agent on the home server (owner, 2026-10-27; closes OQ-17; narrows R0-28, R0-29)

Registry, Cabinet Kernel, Cabinet and PresuPro run on the owner's home server in
the trusted VM Platform. The agent runs in a separate VM Agent on the same
server and reaches the platform only through Kernel's agent channel; Registry's
service API is not reachable from VM Agent. Client Portal stays on the VPS and
reaches the home services over the WireGuard tunnel the home server opens
(R0-39). The owner reaches the owner interface from outside only through the
owner's VPN; it has no public port.

### R0-49 — The owner records the end of a customer relationship (owner, 2026-10-27; closes OQ-18; narrows R0-40)

The end of a relationship with a customer is recorded by the owner, by an
explicit action; archiving the customer's projects does not end it. When the
applicable period ends, Registry itself erases or anonymises the data, keeping
it longer only where a lawful ground for further retention applies.

Narrowed by R0-60: the mark stays; Registry erases nothing on its own. Narrowed by
R0-84: the owner gives the end date, today by default, never a later one.

### R0-50 — One controlled migration (owner, 2026-10-27; closes OQ-13; narrows R0-34, R0-44)

Import is a one-time, controlled migration of the data the running instances
hold today, through the owner interface and confirmed by the owner. It keeps
every identity and link: project ids, `customer_ref`s, room and pointer ids and
versions. Any conflict refuses the whole import; nothing is applied in part.
Data of test instances is never carried over automatically.

Narrowed by R0-79: one import, from the VPS, of the projects the owner picks.
Narrowed by R0-80: project, object, room and pointer ids and versions are kept,
and so is a `customer_ref` Registry minted; a v1 `customer_ref` that is not one
is replaced by the new Customer's minted `customer_ref`, and the import links
the projects that named it to that Customer.

### R0-51 — Restriction of processing (owner, 2026-10-27; closes OQ-14; narrows R0-37)

The owner restricts a customer's processing and may lift the restriction where
a lawful ground allows it. While it holds, ordinary processing of the customer
stops: its contact data reaches no one but the owner, and no project may newly
name it. Correcting and erasing the customer stay allowed, as the GDPR
provides.

### R0-52 — What survives retention (owner, 2026-10-27; closes OQ-15; narrows R0-03, R0-40)

When a period ends, the personal data and the links that identify a person are
removed. A project's technical identity, status and artifact pointers are kept
only where it is shown that they no longer allow re-identification and a
justified purpose for keeping them is recorded; `validate` then answers
`archived`. Otherwise the record is deleted whole, and `validate` answers
`not_found`.

Narrowed by R0-60: the owner chooses between the two when erasing; the showing
and the purpose are recorded in the governance.

### R0-53 — Registry trusts Kernel to name the session, not the network (owner, 2026-10-27; round 5 T1; narrows R0-46, R0-47)

On every agent-authority call Registry checks three things: the calling
service authenticates with its own token — being inside VM Platform
authenticates nothing (R0-27); the session it names is registered; and the
`project_id` is in that session's set. The third applies to operations on a
project; the session's own operations — registering it, reading its access,
requesting access — name no project and are checked for the first two only. Sessions carry no secret of their own:
Kernel, in the trusted VM Platform, is trusted to name the session it acts
for. A compromised Kernel is outside Registry's guarantees. A call naming a
session that is not registered is refused like a call outside the set (R0-47),
an access request included; registering a session already registered returns
it unchanged (round 6 T2).

Narrowed by R0-77: Kernel names the session from its own run context, never
from a value the agent's flow supplies.

### R0-54 — The migration's sources and retry (owner, 2026-10-27; round 5 T2; narrows R0-50)

The sources are the instances on the VPS and on the test rig; the owner picks
one for each import. An import is atomic: a conflict refuses all of it, and the
owner may retry after correcting the cause. Each source's first successful
import into production closes the operation for that source (R0-59). Nothing of a test instance comes
over unless the owner picks it as a source. The owner exports the chosen
source and uploads the export through the owner interface; production Registry
never calls the source instance and holds no credential for it (R0-18; round 6
T7).

Narrowed by R0-72: the export is made by a one-time migration script outside
Registry. Narrowed by R0-79: the VPS is the only source, imported once.

### R0-55 — What a restriction stops (owner, 2026-10-27; round 5 T6; narrows R0-51)

A restriction stops every operation that uses the restricted customer's
personal data, except where the law provides otherwise; it does not stop
changes to the customer's existing projects that do not use that data. `context`
keeps answering the customer's `customer_ref` to PresuPro and Client Portal,
without contact data.

Narrowed by R0-65: Registry admits no legal exception; the owner lifts the
restriction. Narrowed by R0-76: Cabinet reads `context` too.

### R0-56 — Retention erasures are recorded; holdbacks are documented (owner, 2026-10-27; round 5 T7; narrows R0-37, R0-49, R0-52)

Every erasure or anonymisation at the end of a period leaves an audit entry that
names what was erased, never the erased values. The owner may record, for a
customer or a project, a documented lawful ground and the date until which the
data is held back. When that date comes, the need to keep the data is assessed
again: the owner records a new ground and date, or the data is erased.

Replaced by R0-60: the erasure entry stays (R0-58); holdbacks are not
Registry's — the restriction (R0-51) serves while data must be kept but not
used.

### R0-57 — An ended relationship (owner, 2026-10-27; round 5 T9; narrows R0-49)

A customer whose relationship has ended cannot be newly named by a project, at
its creation or by a correction — as for a restricted customer (R0-51; round 6
T4). Its
contact data may still be corrected. Until its record is deleted the owner may
resume the relationship; its deletion date is then reconsidered for the new
purpose of processing.

Narrowed by R0-60: resuming clears the mark; Registry keeps no deletion date.
Narrowed by R0-67: no Customer record is deleted; "until its record is
deleted" reads "until its contact data is erased".

### R0-58 — A minimal log of significant changes (owner, 2026-10-27; round 6 T12; narrows R0-37, R0-56)

Registry records only significant changes of state: changes to projects and
customer records, granting and revoking an agent session's projects,
restricting processing and lifting it, and erasures and anonymisations. Ordinary reads, agent calls and the inner steps of flows
are not recorded in Registry; security events of the infrastructure are
handled by the infrastructure, outside Registry. The log holds no personal
value, no whole request and no secret, and is kept for a limited period the
governance documents (R0-60) and the owner applies (R0-66). The platform manifest describes Registry's capabilities and
contracts; the log records changes of state only.

### R0-59 — The simplest answers to round 6 T3, T5 (drafted 2026-10-27 under the owner's instruction "do not complicate, add no responsibilities"; confirmed by the owner 2026-10-27)

- A restriction (R0-51, R0-55) covers the customer's contact data; the object's
  address stays project data and is served as before.
- The migration closes per source: the VPS and the test rig may each be
  imported successfully once (R0-54).

Narrowed by R0-79: the second point is replaced; the VPS is the only source.
Narrowed by R0-80: the first point reads "the customer's contact and fiscal
data" — a restriction refuses the billing-data read too (R0-65).

### R0-60 — Retention is the owner's policy, not Registry's clock (owner, 2026-10-27; replaces R0-40, R0-56; narrows R0-03, R0-49, R0-52, R0-57)

GDPR asks that retention periods be set, documented and kept (Art. 5(1)(e),
Art. 30, Recital 39); it does not ask Registry to count them. The periods —
the owner's provisional ones of R0-40 among them, to be checked against
accounting, tax, claim and building-warranty periods — are the governance's
retention schedule, applied by the owner's periodic review (once a year, say).
Registry gives that review what it needs and nothing more:

- the date a project was archived, and the owner's mark that a customer
  relationship has ended (R0-49), which the owner may clear (R0-57);
- erasing a customer's contact data (R0-06) and restricting processing while
  data must be kept but not used (R0-51, the Spanish *bloqueo*);
- erasing an archived project: anonymised (id, status and pointers stay, name,
  object and customer link go; `validate` answers `archived`) or deleted whole
  (`validate` answers `not_found`), as the owner chooses (R0-52);
- a log entry for every erasure, without the erased values (R0-58).

Registry erases nothing on its own, keeps no deletion dates or holdbacks, and
sends no reminders.

Narrowed by R0-61 and R0-62 (what erasing a project does to sessions and
reads), R0-66 (the owner erases old audit entries) and R0-71 (anonymisation is
final).

### R0-61 — Erasing a project removes it from every session (proposed to the owner 2026-10-27 after round 18 T3, accepted; narrows R0-46, R0-60)

When the owner anonymises or deletes an archived project, it leaves the granted
set of every agent session, and a session whose active project it was has none.
No session keeps a grant on an erased project.

### R0-62 — An anonymised project answers only what it keeps (proposed to the owner 2026-10-27 after round 18 T11, accepted; narrows R0-43, R0-45, R0-60)

An anonymised project keeps its id, status and artifact pointers and nothing
else. `validate` answers `archived`, and its artifacts are listed and read as
before. 'Read a project', `context`, 'list rooms' and the agent projection answer that
it was erased, and 'list projects' never lists it. R0-45's "`context` therefore always
has an address" holds for every project that is not erased.

### R0-63 — `onboard_object` is retired (proposed to the owner 2026-10-27 after round 18 T4, accepted; narrows R0-13, R0-30)

The operator script `onboard_object` holds no token and calls no production
Registry. Its work is done by the owner in the owner interface and by Kernel
flows.

### R0-64 — Answering a request clears it (proposed to the owner 2026-10-27 after round 18 T5, accepted; narrows R0-46, R0-47)

Granting or declining clears the session's pending request. A session's access
says whether it has a pending request; a request gone with the project not in
the set is a decline. Registry keeps no reason for a decline.

### R0-65 — Registry judges no lawful exception (proposed to the owner 2026-10-27 after round 18 T7, accepted; narrows R0-51, R0-55)

While a customer is restricted, its contact data reaches the owner alone, who
may still read, correct and erase it (R0-51); every other use is refused.
Registry takes no input asserting a legal exception: where a lawful ground
allows processing, the owner lifts the restriction.

### R0-66 — The owner erases old audit entries (proposed to the owner 2026-10-27 after round 18 T10, accepted; narrows R0-37, R0-58, R0-60)

The audit log's period is the governance's. In the periodic review the owner
erases, confirming, every entry older than a date the owner gives; that erasure
leaves an entry of its own naming the date. Registry erases no entry on its own.

### R0-67 — A Customer record is never deleted (proposed to the owner 2026-10-27 after round 18 T15, accepted; narrows R0-06, R0-57, R0-60)

Erasing a customer's contact data (R0-06) is the end of its record: the
Customer keeps its identity and the fact that it was erased, and projects keep
naming it. There is no action that deletes a Customer whole.

### R0-68 — The agent sees no free text that may name a person (proposed to the owner 2026-10-27 after round 19 T5, accepted; narrows R0-41, R0-43)

Registry cannot tell a person's name from any other word, so the agent
projection leaves out the project's display name: the agent works by the
project's id. Room names and artifact pointers stay in it; the owner names rooms
without names or addresses of people, and a producer publishes `uri`,
`payload_ref` and digest without them. Registry does not inspect these values:
the rule binds their writers and is not a check of Registry, and a value that
breaks it is not refused and does reach the agent. Registry's own guarantee
(R0-26) covers every value it holds as `personal_data`.
The rule closes the path by which a `personal_data` value would reach an agent
through Cabinet Kernel and so the agent's AI provider (R0-25, R0-26).

Narrowed by R0-82: the projection carries the project's alias, under the same
writer rule.

### R0-69 — No project named and none active is refused (proposed to the owner 2026-10-27 after round 19 T10, accepted; narrows R0-46)

An agent-authority operation on a project that names none, in a session with
no active project, is refused exactly as a call outside the session's set (R0-47);
Registry never picks a project for it.

### R0-70 — Clearing the active project; an archived project is never made active (proposed to the owner 2026-10-27 after round 19 T12, accepted; narrows R0-46)

The owner may clear a session's active project, which revokes nothing. Making
an archived project active is refused, as granting one is; a project archived
while active stays active, and agent writes on it are refused (R0-12).

### R0-71 — Anonymisation is final (proposed to the owner 2026-10-27 after round 19 T14, accepted; narrows R0-60)

An anonymised project stays as it is: anonymising it again returns it
unchanged, and deleting it whole is refused. It holds no personal value (R0-52),
so the owner has nothing further to erase in it.

### R0-72 — The migration export is a one-time script outside Registry (proposed to the owner 2026-10-27 after round 20 T7, accepted; narrows R0-50, R0-54)

The owner makes the export of a source with a one-time migration script run on
that source's host. The script is not a Registry operation: production Registry
gains no export action, and the source keeps none after the migration. What
Registry defines is the file it accepts on import; its format belongs to States
5 and 6.

### R0-73 — The Cabinet Web mirror gets no token (proposed to the owner 2026-10-27 after round 20 T8, accepted; narrows R0-27)

Cabinet Web is off active development. Its mirror receives no Registry token,
so it no longer reads Registry, and Registry has no network path for it.

### R0-74 — Kernel's token never allows `personal_data` (owner, 2026-10-27, after the review of Kernel's sandbox side channels; narrows R0-26, R0-31, R0-43)

Code an agent writes runs in Kernel and may turn any value it receives into an
observable effect — a run's status, a digest — one bit at a time. Registry
therefore gives Kernel nothing to turn: the classes Kernel's Registry token
allows never include `personal_data`. This is a boundary of Registry, not a
setting the owner may widen; a Kernel need for a personal value is met by the
owner, outside the agent's reach. What other services cleared for
`personal_data` pass on to Kernel is bounded by their own contracts, not here.

### R0-75 — The reopened State 0 is accepted as a whole (owner, 2026-10-27; renews R0-15)

The whole of this document as it stands with R0-24 to R0-74, not only the
numbered decisions, is the product frame the later states build on. A change to
it is a new owner decision here.

### R0-76 — Cabinet receives the current projects (owner, 2026-10-27, after round 21 T2; narrows R0-43)

Cabinet receives the package of current projects and their context, so its
token allows `personal_data` like those of PresuPro and Client Portal: it lists
projects and reads `context`. What Cabinet passes on to Cabinet Kernel is
bounded by Cabinet's own contract (R0-74).

### R0-77 — Kernel names the session from its run context (owner, 2026-10-27, after reading Kernel's A08; narrows R0-53)

The session an agent-authority call names is set by Cabinet Kernel from the
context of its own run, never by a value the agent's flow supplies: a flow that
could set it could name another session and reach that session's projects.
Kernel's binding rules today add no field of their own to a request (Kernel
A08 rule 4), so this is a requirement Registry places on Kernel, to be met in
the case `cabinet-kernel`; until it is met, no agent-authority operation of
Registry is bound in Kernel.

### R0-78 — Registry's manifest record is derived and fits Kernel's bindings (owner, 2026-10-27; narrows R0-31, R0-33; vNext §9)

Registry's record in `platform/manifest/registry.json` is derived from the
specification (`origin: derived`), not written by hand. Every operation an
agent may reach through Kernel has exactly one HTTP route, one of the five
effect classes, its idempotency key as input fields when it writes (R0-36),
the disclosure class of each output — never `personal_data` (R0-74) — and its
replay behaviour. The owner interface's routes are declared under
`not_declared`, kept off the agent. The fields the current manifest format
lacks — disclosure classes, input and output schemas, contract version, known
limits — are the platform's to add in the Code Factory; until they exist the
record is incomplete.

### R0-79 — The migration: two projects from the VPS (owner, 2026-10-27; replaces the sources of R0-54 and R0-59; narrows R0-50)

The only source is the Registry on the VPS, imported once. At the import the
owner picks any subset of its projects; the import accepts whatever the owner
picks then, and the choice recorded here binds nothing. The owner's choice of
2026-10-27 is "Comunidad de Propietarios C/ del Progreso 140"
(`37241411-f235-4a32-bb31-9629d1079dd2`) and the project of Uliana Kolpacheva
(`c276a851-9b8a-44c7-bbf7-20e363b0ad5f`), under the ids Client Portal already
names. The local instance and the test rig are not sources; what they and the
VPS otherwise hold stays behind and is retired with its instance. A project not
in any source is created anew in production. Consumers that name an id
production does not hold — PresuPro's estimates among them — are relinked in
those services, not by Registry (R0-34).

### R0-80 — Registry is the one home of customer personal data (owner, 2026-10-27; replaces R0-06's fiscal-data clause; narrows R0-37, R0-43)

A customer's living personal data — name, contact data, tax id (NIF/NIE/CIF),
legal name — and the object's address and identifying characteristics are held
only by Registry, as the target R0-81 sets for the other services. Other services
keep no customer record and no copy of these values; they read them by
`customer_ref` or project id when they use them. A document a service issues —
an invoice, an estimate sent to the customer, a publication in Client Portal —
fixes the values of its date and is kept under the lawful ground and period the
governance records (R0-60); an erasure in Registry does not rewrite it. A
document is issued when it leaves the service to the customer — an invoice
issued, an estimate sent, a publication made; a draft, a preview or an unsent
version is not issued, keeps no personal value and reads it when rendered. A
service whose token allows it — today PresuPro, to issue documents — reads the
customer's billing data; contact data still reaches the owner alone. Client
Portal's offline projection (R0-39) is Portal's publication to the customer:
it holds only what the customer's own cabinet shows, never a tax id, and is the
one kept copy this rule admits besides issued documents. A snapshot a consumer
keeps (R0-04, V1-2) holds identity only — id, display name, status,
`customer_ref` — and a personal value such as the address is read when it is
used, not kept. PresuPro keeps a tax
id or legal name only inside the documents it issued. Removing the stores and
copies the services keep today is each service's own change (R0-81).

Narrowed by R0-82: the display name is not kept either; a kept snapshot holds
id, alias, status and `customer_ref`.

### R0-82 — Projects are named by their object; the agent sees an alias (owner, 2026-10-27, after round 24 T7; narrows R0-04, R0-68, R0-80)

The owner names a project by its object and work, never by a person: the
customer's name lives in its Customer record. A name such as "Reforma Pedreres
35" still carries a private object's address, which can identify a person, so
the display name is held as `personal_data`: it reaches the owner and a service
cleared for `personal_data` (R0-43), never the agent, and a consumer reads it
when it uses it instead of keeping it. A project may also carry an alias — a
short neutral label the owner gives it, with no person's name, no address and
nothing else that identifies the object or its customer. The alias is the name
the agent sees in its projection and the one a consumer's kept snapshot holds.
Like room names (R0-68), the alias is a rule on its writer, the owner: Registry
does not inspect it, and an alias that breaks the rule is not refused. A
project without an alias is shown to the agent by its id. Projects imported
under a person's name (R0-79) are renamed by the owner after the import.

Narrowed by R0-85: they are renamed in the import itself, which also reaches
archived projects.

### R0-83 — The billing read returns what is recorded (owner, 2026-10-27, after round 24 T1; narrows R0-80)

The read of a customer's billing data returns the kind and the fiscal values
recorded, and marks each one never recorded as absent; Registry does not refuse
the read because a tax id or legal name is missing. Whether a document may be
issued without them is decided by PresuPro under its own contract, not by
Registry.

### R0-84 — The owner dates the end of a customer relationship (owner, 2026-10-27, after round 25 T6; narrows R0-49, R0-57)

Ending a customer relationship records the date the owner gives — the day the
relationship in fact ended, which may be earlier than the action — or today when
the owner gives none. A date later than today is refused. The retention review
counts from that date (R0-60). What ending an ended relationship again, or
resuming one that is not ended, does is settled in State 2.

### R0-85 — The import renames what it brings in (owner, 2026-10-27, after round 26 T5; narrows R0-12, R0-79, R0-82)

When the owner picks the projects to import, the owner may give each a new
display name and an alias (R0-82); the project arrives under them, its id kept.
This is how an archived project named after a person loses that name: an
archived project still cannot be corrected (R0-12), and the import is the one
moment its name is set.

### R0-81 — The one-home rule is a target the services reach; Registry does not wait (owner, 2026-10-27, after round 23 T1; narrows R0-80)

Production Registry starts without waiting for the other services. From its
start Registry holds the customer's personal data as R0-80 says and gives each
service what it needs to stop keeping copies. Each service removes its own
customer records and copies in its own case — PresuPro's project snapshots and
database backups, Cabinet's package of projects, the legacy instances once
retired (R0-79). Until each has, the governance's records of processing list
the copies that remain, with their service and the change that removes them.

## Explicit exclusions

- The operator script `onboard_object`: retired (R0-63); its role is taken by
  the owner interface and Kernel flows.
- Drawings, measurements, planner documents, estimates and prices, invoices,
  payments, expense allocation, funds, photos, client publications, Kernel
  functions and flows (R0-01, R0-24). Splitting an invoice across projects is
  Cabinet's financial operation; Registry gives the canonical `project_id`.
- Orchestrating downstream services and building their launch context (R0-18).
- Exporting from the migration's source instances: a one-time script outside
  Registry (R0-72).
- The documents a service issues, with the customer's values fixed at their
  date (R0-80).
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
R0-40); OQ-13 to OQ-18, raised by the emulated question rounds 3 and 4
(`experiments/registry-pochemuchka/state0/`), on 2026-10-27 (R0-47 to R0-52). The answers to question rounds 18 to 20 were
proposed to the owner and accepted on 2026-10-27 (R0-61 to R0-73); R0-76 to
R0-81 followed the same day, R0-82 and R0-83 answered round 24, R0-84
round 25 and R0-85 round 26.

## Carried to later states

Questions the rounds judged to belong to a later state. Each is closed there,
not here.

- **State 1 (models).** The fields of Project, Customer, Object, Room, artifact
  pointer, agent session access, access request and audit entry, and of each create
  request; the format of every identity (R0-07, R0-16, R0-17), and how a test
  instance's identity space is told apart from production's (R0-34); what an
  anonymised project keeps exactly (R0-60); revisions
  (R0-35); timestamps and which actions move a project's updated time (L16);
  how an erased or restricted Customer is represented in reads and lists; the
  project alias's format and whether it must be unique (R0-82); how the billing
  read marks an absent fiscal value (R0-83); the
  disclosure class of each field (R0-26).
- **State 2 (rules).** What counts as equal content in a project-create replay,
  and a replay of an archived project's id; how a create without an id is made
  replay-safe (R0-36); correction semantics of projects, customers and objects —
  partial or whole, clearing a field (L04); the declared orders of every list
  (L10); what each service token and Kernel's agent authority may do, and which
  disclosure class each may receive (R0-27, R0-31); the session access's scope
  values, expiry and what ends it (R0-32); the owner session's lifetime and
  sign-in throttling (R0-30); the declared artifact vocabulary and what a change
  of it does to existing pointers (R0-33); publication as one transaction
  (L07); the import's mapping check (R0-34), and how Registry knows the import has succeeded (R0-79); how the audit log is protected
  (R0-37); how Kernel registers a session and what ends one (R0-47); backup and tested
  restore (vNext §11), how long backups are kept and how an erasure reaches
  them, and encryption of the store and backups at rest (owner, 2026-10-27).
- **States 5 and 6 (public APIs, contracts).** The field names of every list
  answer and of the project card; the exact `validate` and `context` answers
  (R0-04, the consumer table in `SOURCE.md`) and their disclosure classes; the
  fields of the artifact history; the error answer (L14); the format of the migration file
  import accepts (R0-72); how a credential is
  presented and refused; the owner interface's routes; the manifest record of
  each operation (R0-78) — purpose, channel, route, input and output schemas, classes,
  effect class and preconditions, idempotency, contract version, known limits
  (vNext §9).
