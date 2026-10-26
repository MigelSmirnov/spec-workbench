# State 0 — Registry product boundary

## Status

Draft of 2026-10-26, **not accepted by the owner**; R0-06 and R0-07 are the
owner's decisions of 2026-10-26. Reverse-engineered from the
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

- **Owner / staff** — create, correct and archive projects, through the Registry
  frontend or an operator script (`onboard_object`). Today no route
  authenticates anyone (L15): OQ-04.
- **Consumer services** — PresuPro, Client Portal, Cabinet Kernel, the Cabinet
  Web mirror. They validate a project id and read its context; Cabinet Kernel
  and the operator also create projects and rooms, and publish artifacts as
  producers (below). They
  reach Registry over HTTP on the host's loopback or private network.
- **Producers** — any caller that publishes an artifact pointer: today
  PresuPro (estimates), Cabinet Kernel and the operator script; planners by
  name only. The pointer names its owner service, which is the authority for
  the artifact itself; Registry holds the pointer (V1-4). The owner service is
  declared by the caller and checked only against the vocabulary (OQ-03);
  whether Registry verifies who the caller is belongs to OQ-04.
- **Browser** — the Registry frontend from its own origin; CORS admits exactly
  that origin.
- **Customer** — the person or company a project is for. Never reaches
  Registry; staff record their contact data in a Customer record (R0-06).
- **Network surface** — one HTTP API. Whether it is reachable from anything
  but loopback and the private network is OQ-04.
- **Secrets** — none today. If OQ-04 introduces credentials, they live in the
  instance's protected configuration and never in a record or an answer.
- **Personal data** — the customer's contact data (R0-06). Who may read it is
  OQ-04.

## Primary actions

| action | who | output | failure |
|---|---|---|---|
| create a project | staff, consumer service | the project with its identity — supplied by the caller or minted (R0-07) — status `active` | missing name or address refused; an equal replay returns the existing project, a different one with the same id is refused (R0-07) |
| read a project | anyone allowed by OQ-04 | the project card (any status, V1-7) and its rooms | unknown id refused as not found |
| list projects | staff, consumer service | the projects, archived only when asked, in a declared order (L10) | — |
| correct a project | staff | the project with the new name, address or customer | unknown id refused; correcting an archived project: OQ-07 |
| archive a project | staff | the project, status `archived`; nothing is deleted (V1-7) | unknown id refused; repeat and reversal: OQ-07 |
| validate a project reference | consumer service | exists, active, and why not (`not_found`, `archived`) | — (the answer carries the failure) |
| read a project context | consumer service | the snapshot a consumer keeps: id, display name, status, address, customer, created and updated times | unknown id refused |
| record a customer | staff | the Customer with its identity (`customer_ref`) and contact data | missing name refused |
| correct a customer | staff | the Customer with the new contact data | unknown customer refused; an erased customer cannot be corrected |
| read a customer | staff, operator preparing a client message | name, phone, e-mail, language | unknown customer refused; an erased customer answers that it was erased, with no contact data |
| erase a customer's contact data | staff | the Customer keeps its identity, its contact data is gone; projects still name it (R0-06) | unknown customer refused |
| add a room | staff, consumer service | the room in the project | unknown or archived project refused; OQ-05 |
| list rooms | staff, consumer service | the project's rooms in a declared order | unknown project refused as not found (replaces L21) |
| publish an artifact pointer | producer service | the new version, `published`; the previous published version of that type becomes `superseded` | unknown or archived project, unknown type or owner refused (OQ-03) |
| list artifacts | consumer service | every pointer of the project, published and superseded, each with its type, version and status — this is how history is read (R0-02) | unknown project refused as not found |
| read the latest artifact of a type | consumer service | the one published pointer of that type | unknown project; no published artifact of that type |

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
names. The re-authored Registry keeps both answers field for field unless the
owner decides otherwise under OQ-08.

### R0-05 — One instance, one store (narrows L19)

An instance holds its own store. Two instances share nothing; the same physical
object in two instances is two projects unless the caller gives both the same
id (R0-07).

### R0-06 — The customer is a Registry record (owner, 2026-10-26; closes OQ-01, L03)

Registry holds a Customer record: who the project is for and how to reach
them — name, phone, e-mail, language. `customer_ref` becomes the Customer's
identity, and a project names its customer by it. Fiscal data (NIF, legal
name) stays in PresuPro, which changes for a different reason. The Factory's
WhatsApp link reads the phone from here. The contact data is personal data and
can be erased or anonymised: an explicit exception to R0-03, the only one.
Option (b), PresuPro `Client`, and option (c), nowhere, were declined.

### R0-07 — The caller may supply a project's identity (owner, 2026-10-26; closes OQ-02, replaces V1-5, L01, L02)

A caller may give the `project_id` when creating a project. A repeated create
with that id and equal content returns the existing project; with different
content it is refused, and nothing changes. Without an id the server still
mints one. One physical object can therefore carry one id across instances
(R0-05). V1-5 ("MUST NOT reuse caller-supplied identifiers") is replaced.
Options (b), a per-instance idempotency key, and (c), keeping server minting,
were declined.

## Explicit exclusions

- The Registry frontend and the operator script `onboard_object`. This case
  designs the HTTP service; both are clients of its API, like any consumer, and
  are designed elsewhere. Their reads are kept compatible under OQ-08.

- Drawings, measurements, planner documents, estimates, payments, photos (R0-01).
- Orchestrating downstream services: Registry gives the launch context
  (`project_id`, optional `room_id`) and nothing else (V1-3).
- Fiscal customer data (NIF, legal name): PresuPro owns it.
- Sending anything to a customer.

## Open questions

- **OQ-01** and **OQ-02** — decided by the owner on 2026-10-26: R0-06, R0-07.
- **OQ-03 — Artifact vocabulary.** BLOCK: closed list in the spec (today, L08),
  a list in configuration, or any type named by its owner service? Must a type
  belong to exactly one owner service?
- **OQ-04 — Who may call.** BLOCK: does Registry authenticate callers (a service
  token for writes, staff login for the frontend), or stay unauthenticated
  behind loopback and the private network?
  Since R0-06, an unauthenticated Registry hands customers' phone numbers to
  any caller on that network.
- **OQ-05 — Rooms.** Who uses rooms today beyond the kernel test (L12)? Keep,
  extend (rename, remove), or drop.
- **OQ-06 — `project.list_active`.** No consumer found (L11). Keep or drop.
- **OQ-07 — Archive lifecycle.** Is archive final? May an archived project be
  corrected (L05)? Is a repeated archive a no-op or a refusal (L06)?
- **OQ-08 — Breaking the wire.** Lists answer bare arrays (L09, kernel R5) and
  the project answer nests the id (L20). May the re-authored Registry change
  these shapes, given the frontend and `onboard_object` read them?
- **OQ-09 — Withdrawing a pointer.** May a producer withdraw a pointer whose
  artifact it deleted, and what does "latest of a type" answer then — the
  previous version, or none? Today nothing withdraws (L22); a stale pointer
  stays `published`.
