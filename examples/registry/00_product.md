# State 0 — Registry product boundary

## Status

Accepted by the owner as a whole on 2026-10-26 (R0-15); every action,
decision and exclusion below is input of the later states. R0-06 onward are the
owner's decisions, each dated in its heading; one dated after 2026-10-26 joins
the accepted whole on its date. R0-01 to R0-05 were drafted from the
v1 specification and accepted with the whole. Reverse-engineered from the
running Registry and its v1 specification (`SOURCE.md`): a decision that keeps,
narrows or replaces a v1 decision (V1-n) or a legacy finding (Ln) names it; an
owner decision on a question the v1 never raised names none. Nothing the code does is a decision until it is written here or in a
later state; the open questions are the owner's.

## Product statement

Registry is the platform's catalogue of renovation objects. It says which
projects exist, where each one is, which customer it belongs to and which rooms
it has, and it keeps a catalogue of the documents other services published about
a project. Every other service names a project by the Registry's identity and
reads that identity as a snapshot; none of them writes it back (V1-2).

Registry stores identity and pointers only. Drawings, measurements, estimates,
payments, photos and planner documents stay in the services that own them
(V1-1, V1-4).

## Actors and trust boundaries

- **Owner / staff** — create, correct and archive projects and record customers,
  through the Registry frontend or an operator script (`onboard_object`). They
  authenticate with a staff credential (R0-09); today no route authenticates
  anyone (L15).
- **Operator** — `onboard_object`, or an agent preparing a client message for
  the owner (the WhatsApp link of the Factory's `AGENTS.md`). It acts for the
  owner and holds the staff credential for every action it takes, publishing
  and reading a customer's phone included; no service token is given to it. On
  the host it is the owner (Host, below).
- **Consumer services** — PresuPro, Client Portal, Cabinet Kernel, the Cabinet
  Web mirror. They validate a project id and read its context; today Cabinet
  Kernel and the operator also create projects and rooms, and publish artifacts as
  producers (below). They reach Registry over HTTP on the host's loopback or the
  host's internal network (R0-19); a service that writes holds a
  service token (R0-09).
- **Producers** — any caller that publishes an artifact pointer: today
  PresuPro (estimates), Cabinet Kernel and the operator script. No planner
  publishes today: a planner may be the owner service of a configured type
  (R0-08), and its pointers are then published by staff until the planner
  itself holds a service token. The pointer names its owner service, which is the authority for
  the artifact itself; Registry holds the pointer (V1-4). The type must belong
  to the pointer's owner service (R0-08). A service publishing with its token
  publishes only as the service the token names; staff, and the operator
  acting as staff, publish for any owner service (R0-09).
- **Browser** — the Registry frontend from its own origin, on Registry's own
  host; CORS admits exactly that origin. A frontend used from another machine
  reaches Registry through its own server on Registry's host (R0-22).
- **Customer** — the person or company a project is for. Never reaches
  Registry; staff record their contact data in a Customer record (R0-06).
- **Network surface** — one HTTP API, listening only on loopback or on the
  host's internal network (R0-19). Reading projects, rooms, artifacts, `validate` and `context` needs no
  credential there; every write and every read of contact data does (R0-09).
- **Host** — Registry's guarantees hold against callers of its API, and only
  against them. Everything that runs with the owner's access to Registry's
  host is the owner: the owner, an agent the owner runs, `onboard_object`
  run by either, any process or container the owner started. Each may read
  and change the store, the configuration and every secret directly, around
  the API, and the configuration "readable only by the owner" (R0-23) is
  readable by each. What such a component sends elsewhere is the owner's act,
  not Registry's: an agent passes whatever it reads — contact data,
  configuration, secrets — to the provider of the model the owner runs it on
  (today Anthropic for Claude Code, OpenAI for Codex) under that provider's
  own terms, and Registry limits nothing of it. Traffic inside the host is
  plain HTTP. The credentials tell callers of the API apart; they protect
  nothing from the host. The owner accepts this (owner, 2026-10-27).
- **Secrets** — service tokens and the staff credential, in the instance's
  configuration, which only the owner changes, outside the API (R0-20). The
  owner generates every secret, keeps its original in the owner's own password
  vault (Bitwarden) and writes it by hand into Registry's configuration and its
  holders' (R0-23); never in a record, a log line or an answer.
- **Personal data** — the customer's contact data (R0-06); readable by staff
  only (R0-09).

## Primary actions

| action | who | output | failure |
|---|---|---|---|
| create a project | staff, a service with a service token (today Cabinet Kernel) | the project with its identity — supplied by the caller or minted (R0-07) — status `active` | missing name or address refused; a customer reference that is unknown or erased refused (R0-16); an equal replay returns the existing project, a different one with the same id is refused (R0-07) |
| read a project | any caller | the project card (any status, V1-7) with its rooms; the project's id stands at the top of the answer (R0-13) | unknown id refused as not found |
| list projects | any caller | the active projects, and when asked the archived ones together with them (never the archived alone), in a declared order (L10), as one answer object (R0-13) | — |
| correct a project | staff | the project with the new name, address or customer | unknown id refused; an archived project refused (R0-12); a customer reference that is unknown or erased refused (R0-16) |
| archive a project | staff | the project, status `archived`; nothing is deleted (V1-7); archiving an archived project returns it unchanged (R0-12) | unknown id refused |
| validate a project reference | any caller | exists, active, and why not (`not_found`, `archived`) | — (the answer carries the failure) |
| read a project context | any caller | the snapshot a consumer keeps: id, display name, status, address, customer, created and updated times | unknown id refused |
| record a customer | staff | the Customer with the identity (`customer_ref`) Registry minted for it (R0-16) and its contact data | missing name refused; recording the same person again makes a second Customer (R0-16) |
| correct a customer | staff | the Customer with the new contact data | unknown customer refused; an erased customer cannot be corrected |
| read a customer | staff, operator | name, phone, e-mail, language | unknown customer refused; an erased customer answers that it was erased, with no contact data |
| list customers | staff, operator | the customers, each with its `customer_ref` and name; erased ones only as erased, without contact data — this is how a customer is found for a new project | — |
| erase a customer's contact data | staff | the Customer keeps only its identity and the fact that it was erased; name, phone, e-mail and language are gone; projects still name it (R0-06) | unknown customer refused; erasing an erased customer returns it unchanged |
| add a room | staff, a service with a service token (today Cabinet Kernel) | the room: an identity Registry mints, the given name, its project (R0-10) | missing name refused; unknown or archived project refused; a second room of the same name is a second room (R0-10) |
| list rooms | any caller | the project's rooms in a declared order | unknown project refused as not found (replaces L21) |
| publish an artifact pointer | producer service; staff for any owner service (R0-09) | the new pointer with the identity and version Registry assigns (R0-17), `published`; the previous published version of that type becomes `superseded` | unknown or archived project refused; a type not in the configured vocabulary, or not the owner service's, refused (R0-08); neither `uri` nor `payload_ref` given refused (R0-17) |
| withdraw an artifact pointer | the producer service that owns it, or staff | the pointer, status `withdrawn`; it stays in the history (R0-14) | unknown pointer refused; a pointer of another service, or already withdrawn or superseded, refused; a pointer of an archived project refused (R0-17) |
| list artifacts | any caller | every pointer of the project — published, superseded and withdrawn — each with its type, version and status; this is how history is read (R0-02) | unknown project refused as not found |
| read the latest artifact of a type | any caller | the one published pointer of that type | unknown project refused as not found; a type not in the configured vocabulary refused as an unknown type (R0-17); a configured type with no published pointer answers that none is published — also after a withdrawal, which never falls back to an earlier version (R0-14) |

## Decisions

### R0-01 — Registry owns project identity, nothing else (keeps V1-1, V1-2)

Registry is the single living owner of a project's identity: id, name, address,
customer reference and rooms. Consumers snapshot it at read time and never write
it back. Registry stores no service domain data.

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

### R0-05 — One instance, one store (narrows L19)

An instance holds its own store. Two instances share nothing; the same physical
object in two instances is two projects unless the caller gives both the same
id (R0-07).

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

### R0-07 — The caller may supply a project's identity (owner, 2026-10-26; closes OQ-02, replaces V1-5, L01, L02)

A caller may give the `project_id` when creating a project. A repeated create
with that id and equal content returns the existing project; with different
content it is refused, and nothing changes. Without an id the server still
mints one. One physical object can therefore carry one id across instances
(R0-05). V1-5 ("MUST NOT reuse caller-supplied identifiers") is replaced.
Options (b), a per-instance idempotency key, and (c), keeping server minting,
were declined.

### R0-08 — The artifact vocabulary is configured, one owner per type (owner, 2026-10-26; closes OQ-03, replaces L08)

The artifact types an instance accepts, and the one owner service of each, are
a list in the instance's configuration, not in the specification: adding a type
needs no spec change. A pointer whose type is not listed, or whose owner service
is not that type's owner, is refused.

### R0-09 — Writes and contact data need a credential (owner, 2026-10-26; closes OQ-04, replaces L15)

Each writing service holds a service token that names it; staff hold a staff
credential. Every write needs one of them; recording, correcting, reading or
erasing a customer needs the staff credential. Reads of projects, rooms,
artifacts, `validate` and `context` stay open on loopback and the host's
internal network (R0-19). How the frontend obtains the staff credential belongs to the frontend.

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

### R0-18 — No launch-context action (owner, 2026-10-26; narrows V1-3)

Registry is the entrypoint only in that its project card holds what a
downstream service needs to open: `project_id` and the rooms with their ids.
Registry has no action that builds, validates or returns a launch context, and
calls no downstream service. V1-3's `source=registry` is the opening client's
concern.

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

### R0-20 — The owner changes the configuration, outside the API (owner, 2026-10-27)

Service tokens, the staff credential, the artifact vocabulary (R0-08) and the
frontend origin are the instance's configuration. The owner, as the host's
administrator, changes it outside Registry; a change takes effect when the
instance restarts, and a replaced token stops working at that restart, with no
overlap. Registry has no action that reads or changes its configuration.

### R0-21 — One id in two instances is a link, not one record (owner, 2026-10-27; narrows R0-05, R0-07)

When two instances hold a project under the same id, they hold two
independent records of one physical object. Each instance is the only owner of
its record (R0-01); the records may differ, and Registry neither copies,
synchronises nor compares them. A consumer reads the instance it is configured
with.

### R0-22 — The browser reaches Registry only on its host (owner, 2026-10-27)

The Registry frontend calls the API from the browser, admitted by CORS, only
where the browser runs on Registry's own host and reaches it on loopback. A
frontend used from another machine goes through a server of its own on
Registry's host; that server is a caller inside the host's network like any
other, holds the staff credential for staff actions, and is designed with the
frontend, not here.

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

## Explicit exclusions

- The Registry frontend and the operator script `onboard_object`. This case
  designs the HTTP service; both are clients of its API, like any consumer, and
  are designed elsewhere; they follow R0-13.
- Drawings, measurements, planner documents, estimates, payments, photos (R0-01).
- Orchestrating downstream services and building their launch context: a
  client that opens a downstream service takes `project_id` and `room_id` from
  the project card (R0-18).
- Fiscal customer data (NIF, legal name): PresuPro owns it.
- Sending anything to a customer.

## Open questions

None open. OQ-01 to OQ-09 were decided by the owner on 2026-10-26: R0-06 to
R0-14; the product choices of the first question round (Codex): R0-15 to R0-18.

## Carried to later states

Questions the rounds judged to belong to a later state. Each is closed there,
not here.

- **State 1 (models).** The fields of Project, Customer, Room and artifact
  pointer and of each create request; the format of every identity (R0-07,
  R0-16, R0-17); timestamps and which actions move a project's updated time
  (L16); how an erased Customer is represented in reads and lists.
- **State 2 (rules).** What counts as equal content in a project-create replay,
  and a replay of an archived project's id; correction semantics of projects
  and customers — partial or whole, clearing a field (L04); the declared orders
  of every list (L10); how a credential's holder is checked against the 'who'
  of each action, and what each service token may do; the shape and checks of
  the configured artifact vocabulary, and what a change of it does to existing
  pointers; publication as one transaction (L07).
- **States 5 and 6 (public APIs, contracts).** The field names of every list
  answer and of the project card; the exact `validate` and `context` answers
  (R0-04, the consumer table in `SOURCE.md`); the fields of the artifact
  history; the error answer (L14); how a credential is presented and refused;
  the configured frontend origin of CORS.
