# State 0 — Registry product boundary

## Status

Draft of 2026-10-26, **not accepted by the owner** as a whole; R0-06 to R0-14
are the owner's decisions of 2026-10-26 (the recommendations of OQ-01 to OQ-09,
accepted). Reverse-engineered from the
running Registry and its v1 specification (`SOURCE.md`): every decision below
names the v1 decision (V1-n) or the legacy finding (Ln) it keeps, narrows or
replaces. Nothing the code does is a decision until it is written here or in a
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
  the owner. It acts for the owner and holds the staff credential for every
  action it takes, publishing included; it holds no service token.
- **Consumer services** — PresuPro, Client Portal, Cabinet Kernel, the Cabinet
  Web mirror. They validate a project id and read its context; Cabinet Kernel
  and the operator also create projects and rooms, and publish artifacts as
  producers (below). They reach Registry over HTTP on the host's loopback or
  private network; a service that writes holds a service token (R0-09).
- **Producers** — any caller that publishes an artifact pointer: today
  PresuPro (estimates), Cabinet Kernel and the operator script; planners by
  name only. The pointer names its owner service, which is the authority for
  the artifact itself; Registry holds the pointer (V1-4). The type must belong
  to the pointer's owner service (R0-08). A service publishing with its token
  publishes only as the service the token names; staff, and the operator
  acting as staff, publish for any owner service (R0-09).
- **Browser** — the Registry frontend from its own origin; CORS admits exactly
  that origin.
- **Customer** — the person or company a project is for. Never reaches
  Registry; staff record their contact data in a Customer record (R0-06).
- **Network surface** — one HTTP API on loopback and the private network.
  Reading projects, rooms, artifacts, `validate` and `context` needs no
  credential there; every write and every read of contact data does (R0-09).
- **Secrets** — service tokens and the staff credential, in the instance's
  protected configuration; never in a record, a log line or an answer.
- **Personal data** — the customer's contact data (R0-06); readable by staff
  only (R0-09).

## Primary actions

| action | who | output | failure |
|---|---|---|---|
| create a project | staff, consumer service | the project with its identity — supplied by the caller or minted (R0-07) — status `active` | missing name or address refused; an equal replay returns the existing project, a different one with the same id is refused (R0-07) |
| read a project | any caller | the project card (any status, V1-7) with its rooms; the project's id stands at the top of the answer (R0-13) | unknown id refused as not found |
| list projects | any caller | the projects, archived only when asked, in a declared order (L10), as one answer object (R0-13) | — |
| correct a project | staff | the project with the new name, address or customer | unknown id refused; an archived project refused (R0-12) |
| archive a project | staff | the project, status `archived`; nothing is deleted (V1-7); archiving an archived project returns it unchanged (R0-12) | unknown id refused |
| validate a project reference | consumer service | exists, active, and why not (`not_found`, `archived`) | — (the answer carries the failure) |
| read a project context | consumer service | the snapshot a consumer keeps: id, display name, status, address, customer, created and updated times | unknown id refused |
| record a customer | staff | the Customer with its identity (`customer_ref`) and contact data | missing name refused |
| correct a customer | staff | the Customer with the new contact data | unknown customer refused; an erased customer cannot be corrected |
| read a customer | staff, operator | name, phone, e-mail, language | unknown customer refused; an erased customer answers that it was erased, with no contact data |
| list customers | staff, operator | the customers, each with its `customer_ref` and name; erased ones only as erased, without contact data — this is how a customer is found for a new project | — |
| erase a customer's contact data | staff | the Customer keeps only its identity and the fact that it was erased; name, phone, e-mail and language are gone; projects still name it (R0-06) | unknown customer refused; erasing an erased customer returns it unchanged |
| add a room | staff, consumer service | the room in the project (R0-10) | unknown or archived project refused |
| list rooms | staff, consumer service | the project's rooms in a declared order | unknown project refused as not found (replaces L21) |
| publish an artifact pointer | producer service | the new version, `published`; the previous published version of that type becomes `superseded` | unknown or archived project refused; a type not in the configured vocabulary, or not the caller's service's, refused (R0-08) |
| withdraw an artifact pointer | the producer service that owns it, or staff | the pointer, status `withdrawn`; it stays in the history (R0-14) | unknown pointer refused; a pointer of another service, or already withdrawn or superseded, refused |
| list artifacts | consumer service | every pointer of the project — published, superseded and withdrawn — each with its type, version and status; this is how history is read (R0-02) | unknown project refused as not found |
| read the latest artifact of a type | consumer service | the one published pointer of that type | unknown project; no published pointer of that type — also after a withdrawal, which never falls back to an earlier version (R0-14) |

## Decisions

### R0-01 — Registry owns project identity, nothing else (keeps V1-1, V1-2)

Registry is the single living owner of a project's identity: id, name, address,
customer reference and rooms. Consumers snapshot it at read time and never write
it back. Registry stores no service domain data.

### R0-02 — Artifacts are pointers (keeps V1-4)

An artifact is catalogue metadata and a service-owned reference (`uri`,
`payload_ref`). Registry never reads or stores the payload. Publishing a new
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
name) stays in PresuPro, which changes for a different reason. The Factory's
WhatsApp link reads the phone from here. Name, phone, e-mail and language are
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
artifacts, `validate` and `context` stay open on loopback and the private
network. How the frontend obtains the staff credential belongs to the frontend.

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

## Explicit exclusions

- The Registry frontend and the operator script `onboard_object`. This case
  designs the HTTP service; both are clients of its API, like any consumer, and
  are designed elsewhere; they follow R0-13.
- Drawings, measurements, planner documents, estimates, payments, photos (R0-01).
- Orchestrating downstream services: Registry gives the launch context
  (`project_id`, optional `room_id`) and nothing else (V1-3).
- Fiscal customer data (NIF, legal name): PresuPro owns it.
- Sending anything to a customer.

## Open questions

None open. OQ-01 to OQ-09 were decided by the owner on 2026-10-26: R0-06 to
R0-14.
