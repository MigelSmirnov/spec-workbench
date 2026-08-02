# Cabinet Backend — source context

## Purpose of this case study

This case study designs the transition of Cabinet from repository-backed Cards
to a continuously running backend with PostgreSQL while preserving Cabinet's
original product idea:

> The user communicates naturally; the agent organises incoming working
> information; Cabinet stores the resulting structured, searchable knowledge.

The target is not a separate Project Cost Integration product and not an
extension of Registry. Cabinet Backend becomes the durable operational core
for Cabinet Cards, relationships, invoices, material lists, accepted
agent-prepared allocations, invoice payment facts, sources, and history.

## Original Cabinet intent

The inspected default branch establishes:

- Cabinet is a personal workspace for everyday work;
- conversation is the primary write interface;
- AI extracts, searches, creates, and enriches Cards;
- Provider, Contact, Material List, Document, and Work Object Cards belong to
  the original product direction;
- original documents and source context are preserved;
- AI, Web UI, API, and future clients use the same structured information;
- repository storage is a Version 1 decision that may move to a server without
  changing the accepted domain model.

The current Provider implementation is narrower than the original product
boundary and does not redefine that boundary.

## Current Cabinet invoice increment

Inspected branch: `agent/invoice-presupro-alignment`.

Confirmed current capabilities:

- Invoice Card V1 facts, validation, lifecycle, provenance, and revision hash;
- draft, confirmed, and archived invoice states;
- deterministic arithmetic and payment validation;
- optimistic concurrency and idempotent mutation support;
- a primary Cabinet object hint using optional `card_id` and free-text
  `label`.

Confirmed product correction:

> The Invoice Card `object` value may be entered manually at the work site.
> It is evidence for matching, not authoritative Registry project identity.

## Platform systems

### Registry

Factory project: `registry_sandbox`.

Registry creates and owns the stable project UUID and current project context.
Cabinet creates a Work Object Card only by linking it to an existing active
Registry project UUID. Registry-owned name, address, and status remain a
read-only current projection inside Cabinet, not an independently editable
copy. Unassigned invoices and notes do not create standalone Work Objects.

Cabinet-owned contact and fiscal data remains independent from Registry
`customer_ref`; Registry context never overwrites Cabinet Card data.

### PresuPro

Factory project: `PresuPro_sandbox`.

PresuPro owns mutable presupuesto composition, zones, line items, totals, and
its approval/publication lifecycle. Cabinet consumes plan data for operational
comparison and purchasing work but does not edit the estimate or silently
present the latest mutable estimate as an approved budget.

### Client Portal

Workbench case: `examples/client-portal`.

Client Portal owns client-visible Budget, Expense, allocation, progress,
payment, and visibility records. Cabinet prepares traceable operational facts
and projections for an agreed Client Portal intake boundary. Cabinet does not
write directly to Client Portal storage.

### Holded and Holded Gateway

Holded is the external online accounting system.

The selected platform direction is a dedicated Holded Gateway used by both
Cabinet and PresuPro:

- Cabinet decides whether a confirmed supplier invoice and its accepted
  payment facts are eligible for accounting publication;
- PresuPro decides whether an approved estimate produces a sales-side
  accounting document;
- Holded Gateway owns credentials, Holded HTTP behavior, retries,
  reconciliation, provider request/response decoding, and technical operation
  receipts;
- the agent does not call Holded directly and does not own the Holded token;
- Holded Gateway does not decide Cabinet or PresuPro business policy.

## Selected persistence direction

PostgreSQL is the selected durable database for Cabinet Backend.

This State 0 decision establishes the need for transactional, relational,
concurrent backend storage. It does not yet define tables, ORM mappings,
indexes, or migration files.

Original binary documents remain required source evidence. Their eventual
binary storage technology is unresolved; PostgreSQL may retain references,
hashes, media metadata, and provenance without necessarily storing large
binaries in database rows.

## Governing interpretation

Cabinet Backend is deliberately low-level but not responsibility-free.

The agent and UI may perform heuristic and computational work such as OCR,
classification, candidate matching, material-name matching, distribution of
one invoice across Work Objects, calculation of purchased/remaining
quantities, and preparation of commands. Cabinet Backend owns deterministic
acceptance:

- typed Cabinet records and relationships;
- stable identity;
- validation and lifecycle;
- source and actor provenance;
- concurrency and idempotency;
- referential and transactional integrity;
- durable history;
- external publication state.

No generic prepared payload becomes trusted merely because an agent produced
it.

## Current delivery constraints

- No temporary reuse of PresuPro as a Cabinet-to-Holded proxy.
- No direct agent-to-Holded production integration.
- Shared MCP design remains a separate cross-card task.
- VPS and whole-platform production operations remain outside the current
  design state.
- Exact endpoints, contracts, tables, and module paths belong to later design
  states.
