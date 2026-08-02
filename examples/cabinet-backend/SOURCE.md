# Cabinet Backend — source context

## Purpose of this case study

This case study designs the transition of Cabinet from repository-backed Cards
to a continuously running backend with PostgreSQL while preserving Cabinet's
original product idea:

> The user communicates naturally; the agent organises incoming working
> information; Cabinet stores the resulting structured, searchable knowledge.

The target is not a separate Project Cost Integration product and not an
extension of Registry. Cabinet Backend becomes the durable operational core
for Cabinet Cards, relationships, purchases represented by Invoice Cards,
material lists, sources, and history.

## Original Cabinet intent

The inspected `MigelSmirnov/cabinet` repository establishes:

- Cabinet is a personal workspace for everyday work;
- conversation is the primary write interface;
- AI extracts, searches, creates, and enriches Cards;
- Provider, Contact, Material List, Document, Invoice, and Work Object Cards
  belong to the product direction;
- original documents and source context are preserved;
- AI, Web UI, API, and future clients use the same structured information;
- repository storage is a Version 1 decision that may move to a server without
  changing accepted domain facts.

The current Provider implementation is narrower than the full product boundary
and does not redefine that boundary.

## Implemented Cabinet Invoice Card V1

Inspected merged work: Cabinet pull request `#3`, originally developed on
`agent/invoice-presupro-alignment` and merged into `main` on 2026-08-02.

Confirmed implementation facts:

- one Invoice Card represents one supplier invoice or purchase;
- lifecycle states are `draft`, `confirmed`, and `archived`;
- the `object` block is structurally required;
- `object.card_id` is an optional Cabinet Object Card identifier;
- `object.label` is an optional free-form working label;
- both object values may be null, producing an unassigned warning rather than
  making the card invalid;
- Invoice Card V1 stores one primary object assignment only;
- line-level allocation and distribution across several objects are explicitly
  outside immutable Invoice Card facts;
- payment is represented by a status and an array of transactions;
- multiple transactions may use different methods and therefore already
  support split settlement such as cash plus card;
- the validator checks paid amount against invoice payable amount;
- cash transactions distinguish tendered, applied, and returned change;
- accepted payment statuses are `unknown`, `unpaid`, `partially_paid`, `paid`,
  and `refunded`;
- missing payment evidence is `unknown`, not inferred as `unpaid`;
- Object Card implementation itself remains deferred.

## Product interpretation of “invoice”

For this Cabinet use case, the user is primarily recording a material purchase
made in a physical shop or online. In user-facing language the concept may be
called “purchase” or “material purchase”.

The existing Cabinet entity remains Invoice Card because it preserves the
source receipt or invoice facts. The backend design must not reinterpret it as
a payable workflow merely because the entity is named Invoice.

The normal product flow is:

```text
purchase materials
→ pay immediately
→ capture receipt/invoice
→ validate extracted facts
→ optionally assign one Work Object
→ store confirmed Cabinet record
```

A purchase may remain “without object”. A purchase may also record several
payment transactions when settlement was split between payment methods.

## Work Object correction

The original Cabinet domain document identifies Work Object as a Card but does
not yet define its specialized fields. There is no accepted implementation
fact requiring every Work Object to originate in Registry.

The product decision for this case study is therefore:

- a Cabinet Work Object may exist standalone;
- it has its own Cabinet Card identity;
- it may later link to a Registry project;
- Registry owns the external project UUID and current Registry context;
- Registry linkage does not replace Cabinet identity or erase Cabinet history;
- an unassigned purchase does not require creation of a synthetic Work Object.

State 1 must define the exact Work Object fields and the optional Registry link
without inventing implementation details in State 0.

## Platform systems

### Registry

Factory project: `registry_sandbox`.

Registry creates and owns stable Registry project UUIDs and current project
context. Cabinet may retain an optional validated Registry link for a Work
Object. Registry-owned name, address, and status may be consumed as a read-only
projection.

Cabinet-owned Card identity, notes, relationships, purchase history, contact
facts, and fiscal information remain Cabinet-owned and must not be silently
overwritten from Registry.

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
for an agreed Client Portal intake boundary. Cabinet does not write directly to
Client Portal storage.

### Holded and Holded Gateway

Holded is the external online accounting system.

The selected platform direction is a dedicated Holded Gateway used by both
Cabinet and PresuPro:

- Cabinet decides whether a confirmed supplier purchase is eligible for
  accounting publication;
- PresuPro decides whether an approved estimate produces a sales-side
  accounting document;
- Holded Gateway owns credentials, Holded HTTP behavior, retries,
  reconciliation, provider request/response decoding, and technical receipts;
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
classification, candidate matching, material-name matching, preparation of a
primary object suggestion, and plan-versus-actual calculations. Cabinet Backend
owns deterministic acceptance:

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
- No cross-invoice payment system in the first complete product.
- No multi-object Invoice Card allocation in the first complete product.
- Shared MCP design remains a separate cross-card task.
- VPS and whole-platform production operations remain outside the current
  design state.
- Exact endpoints, contracts, tables, and module paths belong to later design
  states.
