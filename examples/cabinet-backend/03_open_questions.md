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

**Status:** Resolved by accepted decision A43 in `02_rules.md`.

PresuPro exposes one stable mutable `Estimate.id` but no authoritative family,
predecessor, replacement, or revision lineage. Cabinet therefore stores every
observed content state as an immutable snapshot, permits several snapshots to
share one PresuPro estimate ID, treats different estimate IDs as independent,
and never infers lineage. See `presupro_estimate_lineage_discovery.md` for the
verified source behavior.

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

## OQ-005 — Unverified Holded operations and revision reconciliation

### Question

Which Holded operations and status semantics can Cabinet Backend safely use after
the verified first purchase publication defined by accepted decision A51?

### Current accepted constraints

- Holded publication is pinned to one exact confirmed Card revision;
- an invoice without required original evidence is not eligible for Holded;
- Cabinet Backend never edits an accepted Card revision;
- a later correction is a new confirmed Card revision;
- first publication uses exactly one POST followed by GET verification;
- an ambiguous create outcome is never retried automatically;
- Holded-specific intermediate rounding does not rewrite Invoice Card totals.

### Remaining verification

Only the following Holded areas remain open in this question:

1. exact meaning of returned numeric status values;
2. PUT behavior and accounting consequences for an existing purchase;
3. purchase refund or rectification behavior and linkage to the source purchase;
4. attachment upload, listing, retrieval, and persistence behavior;
5. create idempotency or another safe duplicate-prevention mechanism;
6. reconciliation of a later confirmed Invoice Card revision with an already
   published purchase.

### Explicit non-decisions

Until separately verified and accepted, Backend must not infer status semantics,
automatically update a purchase, create a refund, upload attachments, retry an
ambiguous POST, or reconcile a later Invoice Card revision by mutating Holded.

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
