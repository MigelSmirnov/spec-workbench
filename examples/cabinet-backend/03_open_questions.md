# Cabinet Backend — open questions

## Status

This document records decisions that are intentionally not resolved yet.

An entry here is not a placeholder and not an implementation TODO. It marks a
real dependency on another application's accepted contract, repository evidence,
or a later product decision.

Accepted behavior already defined in `01_models*.md` and `02_rules.md` remains
normative while these questions are open.

---

## OQ-001 — Registry completion semantics

### Question

Should Registry expose a separate authoritative project-completion fact, distinct
from `active` and `archived`?

### Why it remains open

Registry discovery confirmed only `active` and `archived`. It does not reveal
whether an archived project was completed, cancelled, hidden administratively, or
archived for another reason.

### Current Cabinet Backend baseline

- `active` maps to normal project availability.
- `archived` maps to unavailable and requires review.
- a missing project maps to unavailable and requires review.
- `archived` is never interpreted as `completed`.
- no current Registry value produces `late_project_cost`.

### Required decision

- add a distinct Registry completion field or status and define its lifecycle; or
- keep completion outside Registry and identify its authoritative owner.

### Explicit non-decision

Cabinet Backend does not infer completion from `archived`, invoice timing,
project inactivity, or any other heuristic.

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

**Status:** Resolved by accepted decision A34 in `02_rules.md`.

The compact catalogue contains `project_id`, `display_name`, `address`,
`status`, and `registry_updated_at`, projected from the full Registry project
list. See `registry_discovery.md` for the factual source contract and limitations.

---

## OQ-004 — Cabinet WorkObject catalogue application behavior

**Status:** Resolved by accepted decision A35 in `02_rules.md`.

Cabinet maintains at most one `WorkObject` for each observed Registry
`project_id`. Catalogue refreshes update only Registry-derived fields; Cabinet
fields, archived objects, and objects absent from a later catalogue remain
preserved. The projection is one-way and never writes to Registry.

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
