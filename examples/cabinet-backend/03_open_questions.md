# Cabinet Backend — open questions

## Status

This document records decisions that are intentionally not resolved yet.

An entry here is not a placeholder and not an implementation TODO. It marks a
real dependency on another application's accepted contract, repository evidence,
or a later product decision.

Accepted behavior already defined in `01_models*.md` and `02_rules.md` remains
normative while these questions are open.

---

## OQ-001 — Registry status mapping

### Question

Which concrete Registry status values map to Cabinet Backend's accepted semantic
categories `active`, `completed`, and `unavailable`?

### Why it remains open

The exact Registry lifecycle vocabulary and status field contract have not yet
been verified against authoritative Registry evidence.

### Current Cabinet Backend baseline

- Registry is authoritative for project status.
- `active` projects produce normal project costs.
- `completed` projects may receive `late_project_cost` invoices without being
  reopened automatically.
- `unavailable` or unknown projects require assignment review.
- Project status alone never rejects or deletes a valid confirmed Invoice Card.

### Required verification

- canonical Registry status field and complete value vocabulary;
- exact mapping of each Registry value to `active`, `completed`, or
  `unavailable`;
- whether completion, closure, archival, blocking, and deletion are distinct
  Registry states;
- how missing or deleted project records are represented;
- status version or observation evidence required to preserve the mapping result.

### Explicit non-decision

Cabinet Backend does not guess a mapping for an unverified Registry value. An
unmapped value is treated as unavailable and requires manual review.

---

## OQ-002 — PresuPro estimate family and version lineage

### Question

How does PresuPro represent a new version of an existing estimate?

### Why it remains open

Cabinet Backend requires immutable `EstimateSnapshot` records, but the current
PresuPro contract has not yet been verified for explicit version lineage.

### Current Cabinet Backend baseline

- every accepted estimate snapshot is immutable;
- a changed estimate arrives as a new snapshot;
- existing invoice-line matches remain pinned to the exact old snapshot;
- matches are never moved automatically to a new estimate.

### Required verification

- stable `estimate_id` semantics;
- whether a new version keeps or changes `estimate_id`;
- presence of an `estimate_family_id` or equivalent;
- presence of `previous_estimate_id`, parent, predecessor, or replacement links;
- explicit estimate version number or content hash;
- accepted/frozen status semantics;
- whether multiple independent estimates for one project are distinguishable from
  revisions of the same estimate.

### Possible PresuPro enhancement

If PresuPro does not expose lineage, it may need an accepted contract extension
that provides stable family identity and predecessor/replacement references.
Cabinet Backend must not infer lineage only from similar content or project ID.

---

## OQ-003 — Registry catalogue exact field contract

### Question

What is the final minimal Registry catalogue payload published by Cabinet Backend
to Cabinet?

### Current accepted minimum

The working minimum is:

- `project_id`;
- display name;
- address or short context;
- Registry project status;
- Registry observation time;
- catalogue version or content hash.

### Why it remains open

The exact Registry field names, nullable behavior, lifecycle vocabulary, and
version evidence have not yet been checked against the Registry contract.

### Required verification

- canonical field names and identifiers;
- whether address is a single field or structured data;
- project status vocabulary;
- Registry record version, ETag, content hash, or update timestamp;
- whether catalogue completeness or filtering must be declared;
- whether customer display context is required to disambiguate projects.

### Explicit constraint

The catalogue must remain compact. Cabinet does not receive the complete Registry
project record merely because more fields are available.

---

## OQ-004 — Cabinet WorkObject catalogue application behavior

### Question

How exactly does the Cabinet web application create and update its `WorkObject`
Card from a newly published Registry catalogue?

### Ownership

This is primarily a Cabinet web-application question, not a Cabinet Backend
business rule.

### Current Cabinet Backend responsibility

- read Registry through the platform integration;
- preserve immutable Registry project snapshots;
- publish a compact versioned catalogue to Cabinet;
- retain catalogue provenance returned with completed Invoice Cards;
- validate returned `project_id` values against current Registry information.

### Required Cabinet verification

- whether `WorkObject` is created automatically or only after user selection;
- which fields are refreshed from a new catalogue;
- how local Cabinet notes and relationships survive display-field changes;
- how removed or closed projects remain visible for historical work;
- whether Cabinet records the exact catalogue version used to create or update the
  Card.

### Explicit constraint

Cabinet Backend does not edit `WorkObject` directly and Cabinet does not call
Registry directly.

---

## OQ-005 — Holded correction and reconciliation workflow

### Question

What is the accepted business process when a new confirmed Invoice Card revision
appears after an older revision has already been published successfully to
Holded?

### Current accepted constraints

- Holded publication is pinned to one exact confirmed Card revision;
- an invoice without required original evidence is not eligible for Holded;
- Cabinet Backend never edits an accepted Card revision;
- a later correction is a new confirmed Card revision.

### Required decision

Choose and specify one or more accepted workflows:

- manual reconciliation only;
- create a corrective document in Holded;
- cancel and recreate when legally and technically permitted;
- record the new revision without changing Holded;
- explicit publication prohibition until an operator resolves the discrepancy.

### Required Holded verification

- supported correction and cancellation operations;
- external document mutability;
- idempotency support;
- legal/accounting constraints for posted purchases;
- representation of credit notes and replacement invoices.

---

## OQ-006 — Additional Cabinet Card types in the local Backend

### Question

Which Cabinet Card types beyond Invoice Card must be supported offline and
synchronized in the first Cabinet Backend implementation?

### Candidate types

- `ProviderCard`;
- `ContactCard`;
- `MaterialListCard` and items;
- `DocumentCard`;
- project-linked notes and relationships.

### Why it remains open

State 1 deliberately avoids inventing replacement schemas for Card types whose
accepted Cabinet contracts have not been reviewed.

### Required verification

For each Card type:

- accepted schema and validator;
- draft/confirmed lifecycle;
- immutable revision identity;
- source-file semantics;
- synchronization package eligibility;
- local durability requirements;
- Registry, PresuPro, Holded, and Client Portal dependencies.

---

## OQ-007 — Final authentication and authorization model

### Question

How does the local synchronization client authenticate to Cabinet, and how are
local agent and HTML attachment operations authorized?

### Current accepted constraints

- Cabinet Backend initiates synchronization;
- Cabinet never exposes or calls the local Backend;
- the local HTML uploader is local-only;
- agent and HTML workflows use the same Backend attachment operation;
- every exceptional acceptance or attachment records actor provenance.

### Required decision

- node credential format and rotation;
- revocation behavior;
- whether synchronization credentials are per device or per installation;
- local-user authentication for the HTML uploader;
- authorization boundaries for read, attach, reconcile, release, and publish
  operations;
- audit requirements for agent-delegated actions.

---

## Resolution protocol

When an open question is resolved:

1. verify the authoritative external contract or accept the product decision;
2. add the normative model clarification to State 1 or the deterministic rule to
   State 2;
3. add required tests and failure behavior;
4. replace the open entry with a short resolution reference rather than silently
   deleting the historical question.
