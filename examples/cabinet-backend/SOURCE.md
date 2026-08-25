# Cabinet Backend — source context

## Purpose of this case study

This case study designs the transition of Cabinet from repository-backed Cards
to a continuously available assistant backed by VPS working storage and a local
PostgreSQL archive.

Cabinet preserves its original product idea:

> The user communicates naturally; the agent organises incoming working
> information; Cabinet stores the resulting structured, searchable knowledge.

Cabinet is a personal operational memory for everyday work. Invoice capture is
one important workflow inside that larger product, not a separate accounting or
payables application.

## Original Cabinet intent

The inspected `MigelSmirnov/Cabinet_web` repository establishes:

- conversation is the primary write interface;
- AI extracts, searches, creates, links, and enriches Cards;
- Provider, Contact, Material List, Document, Invoice, and Work Object views
  belong to the product direction;
- original documents and source context are preserved;
- AI, Web UI, API, and future clients use the same structured information;
- repository storage is a Version 1 implementation choice, not a permanent
  domain boundary.

## Product interpretation of an invoice

In the normal Cabinet workflow, an invoice is usually evidence of a material or
service purchase made in a shop, online, or from a tradesperson.

The user may photograph a Spanish invoice or receipt while away from the local
platform, or upload an existing image or PDF. The paper document, received image,
or PDF is the primary source. Cabinet does not edit that source.

Cabinet may improve its understanding of the source by:

- adding another photograph of the same paper document;
- running OCR or another extraction method;
- correcting an extraction error;
- confirming the extracted facts;
- assigning the purchase to a known work object;
- linking lines to PresuPro estimate items;
- publishing an eligible confirmed purchase to Holded.

These are interpretations and Cabinet decisions around the source. They are not
changes to the original invoice.

The normal field workflow is:

```text
purchase materials or receive a tradesperson invoice
→ photograph or upload the source on the VPS
→ extract and review invoice facts
→ select a work object from the cached Registry object list, or leave unassigned
→ keep working while the local platform is offline
→ later connect the local platform
→ transfer sources, extracted facts, confirmation, and Cabinet decisions
→ validate the selected object against current Registry data
→ continue with PresuPro analysis and other local integrations
```

## Implemented Cabinet Invoice Card V1

Inspected merged work: Cabinet pull request `#3`, originally developed on
`agent/invoice-presupro-alignment` and merged into `main` on 2026-08-02.

Confirmed implementation facts:

- one Invoice Card represents one supplier invoice, receipt, or purchase;
- lifecycle states are `draft`, `confirmed`, and `archived`;
- one primary object assignment is supported;
- a purchase may remain unassigned;
- line-level distribution across several objects is outside the baseline;
- payment is represented by a status and an array of transactions;
- split settlement such as cash plus card is supported;
- missing payment evidence is `unknown`, not inferred as `unpaid`;
- original source evidence must remain traceable.

## Work Object and Registry correction

Registry contains the authoritative object cards used by the working platform.
Cabinet does not create an independent competing object identity in the baseline.

The accepted product direction is:

- Registry owns each work-object `project_id` and current object context;
- the local Cabinet Backend reads Registry objects and stores versioned snapshots;
- the VPS receives a compact cached object catalogue from the local Backend;
- the cached catalogue is intentionally available while the local platform is
  offline, which is the normal daytime condition;
- a user may assign a fresh VPS invoice to an object from that cached catalogue;
- the assignment records which Registry snapshot was used and how old it was;
- after local reconnection, Cabinet validates the selected `project_id` against
  current Registry data;
- a missing, closed, or materially changed Registry object does not erase the
  user's earlier choice; it creates a validation warning requiring attention;
- an unassigned purchase does not require a synthetic Work Object.

In this case study:

```text
WorkObject.id = Registry ProjectRecord.id
```

Cabinet owns relationships, invoice history, notes, matching decisions, and
operational context linked to that Registry identity. Registry remains the owner
of the object card itself.

## Two operating periods

### Local platform connected

The local Backend can:

- refresh Registry object snapshots;
- publish the compact object catalogue to the VPS;
- receive fresh invoice sources and structured records from the VPS;
- validate cached object assignments;
- access PresuPro estimates;
- calculate complete historical analysis;
- perform controlled Holded integration.

### Local platform unavailable

The VPS remains useful and can:

- receive invoice photographs and PDFs;
- preserve immutable source files;
- extract, correct, and confirm invoice facts;
- search and discuss its retained working set;
- show the cached Registry object catalogue with freshness information;
- assign an invoice to a cached object;
- preserve all work for later local transfer.

It cannot claim current Registry freshness, retrieve current PresuPro data, or
perform complete historical analysis while disconnected.

## Platform systems

### Registry

Registry owns stable project UUIDs and current object context. Cabinet consumes
versioned read-only snapshots and a compact cached catalogue for offline use.

### PresuPro

PresuPro owns mutable estimate composition, zones, line items, totals, and its
approval or publication lifecycle. Cabinet consumes versioned plan snapshots for
comparison and accepted matching decisions.

### Client Portal

Client Portal owns client-visible Budget, Expense, allocation, progress, payment,
and visibility records. Cabinet prepares traceable operational facts for an
agreed intake boundary and does not write directly to Client Portal storage.

### Holded and Holded Gateway

Cabinet decides whether a confirmed supplier purchase is eligible for accounting
publication. Holded Gateway owns credentials, transport, retries,
reconciliation, and technical receipts.

## Selected persistence direction

PostgreSQL is the selected durable database for the local Cabinet Backend.
Original binary documents remain required evidence. PostgreSQL may retain hashes,
metadata, provenance, and storage references without necessarily storing large
binaries in rows.

The VPS stores a protected working set needed for continuous assistance while the
local platform is unavailable. The local Backend stores the complete durable
archive.

## Governing interpretation

The agent and UI may perform heuristic work such as OCR, classification, object
suggestion, material-name matching, and match proposals. Cabinet Backend owns
deterministic acceptance:

- typed Cabinet records and relationships;
- stable identity;
- source immutability and provenance;
- extraction correction history;
- validation and lifecycle;
- concurrency and idempotency;
- referential and transactional integrity;
- durable history;
- external publication state.

No prepared payload becomes trusted merely because an agent produced it.

## Current delivery constraints

- No direct agent-to-Holded production integration.
- No temporary reuse of PresuPro as a Cabinet-to-Holded proxy.
- No cross-invoice payment system in the baseline.
- No multi-object Invoice Card allocation in the baseline.
- No Cabinet-created standalone Work Object in this case study.
- Exact endpoints, contracts, tables, module paths, and transports belong to
  later design states.
