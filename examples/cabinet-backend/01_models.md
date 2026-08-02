# State 1 — Cabinet Backend domain models

## Status

Working domain-model baseline for the accepted Cabinet Backend operating cycle.

This state defines Backend-owned concepts, identities, ownership, lifecycle
vocabulary, and relationships. It does not redefine the already implemented
Cabinet Invoice Card V1 contract. It also does not define APIs, SQL tables, ORM
mappings, transport payloads, retry algorithms, or deployment products.

## Modelling priorities

State 1 is assembled around the real operating workflow:

1. accept and preserve an existing Cabinet Invoice Card V1 without changing its
   meaning;
2. durably store the original source bytes referenced by the Card;
3. make Registry objects available on the VPS through a versioned cached
   catalogue;
4. allow object selection while the local platform is offline;
5. transfer daytime work into the local durable archive idempotently;
6. validate the selected Registry object after reconnection without erasing the
   user's decision;
7. keep PresuPro matching, analytics, synchronization state, and Holded
   publication outside immutable Invoice Card facts.

---

# A. Accepted Invoice Card boundary

## A.1 Invoice Card V1 is an existing contract

The Cabinet repository already defines and validates Invoice Card V1. Cabinet
Backend consumes that accepted contract; it does not invent a replacement
invoice model.

The accepted Card contains, among other fields:

- `card_type = invoice`;
- `card_version = 1`;
- stable `id`;
- lifecycle `status` — `draft`, `confirmed`, or `archived`;
- invoice number and dates;
- currency;
- supplier and buyer facts;
- required primary `object` block;
- invoice `lines`;
- `totals`;
- required `payment` block with zero or more transactions;
- `source` metadata;
- `provenance`.

The Backend must preserve the complete accepted Card payload, including fields
that it does not currently use.

## A.2 Backend must not redefine Card fields

The following remain governed by Invoice Card V1 and its validator:

- allowed line kinds;
- decimal-string representation;
- line and total arithmetic checks;
- payment statuses and transaction methods;
- cash tendered, applied, and change semantics;
- warning and confirmation behavior;
- object block shape;
- source metadata shape;
- content hashing and optimistic concurrency behavior.

State 1 may reference these facts but must not introduce conflicting field names,
new Card-only statuses, or alternative arithmetic meanings.

## A.3 Card facts versus Backend operational state

The Invoice Card contains factual purchase information and primary capture
context.

The Backend separately owns mutable operational information such as:

- synchronization and import state;
- local binary-storage state;
- Registry catalogue snapshots;
- Registry validation of the selected object;
- PresuPro estimate snapshots and matches;
- plan-versus-actual calculations;
- Holded publication state;
- deduplication review and integration evidence.

Operational records may reference an exact Card revision but do not rewrite the
Card silently.

---

# B. Shared primitives

## ActorReference

Value object identifying the actor responsible for a Backend action.

Candidate fields:

- `actor_type` — `user`, `agent`, `service`, `import`, or `system`;
- `actor_id`;
- `delegated_by` optional;
- `interaction_id` optional;
- `display_label` optional.

It records provenance, not authentication state.

## CabinetNodeIdentity

Identity of one participating Cabinet node.

Candidate fields:

- `node_id`;
- `node_kind` — `vps_cabinet` or `local_backend`;
- `status` — `active` or `revoked`;
- `contract_version`;
- `created_at`;
- `revoked_at` optional.

## InvoiceCardRevisionReference

Value object pinning one exact accepted Invoice Card revision.

Candidate fields:

- `invoice_id`;
- `card_version`;
- `content_hash`;
- `observed_status`;
- `observed_at`.

The `content_hash` is the canonical content revision already used by Cabinet.
Backend does not introduce a competing invoice revision-number system in State 1.

---

# C. Accepted Card storage

## StoredInvoiceCard

Backend archive entity for one logical Cabinet Invoice Card.

Candidate fields:

- `invoice_id` — equal to the accepted Card `id`;
- `card_version`;
- `current_content_hash`;
- `current_status`;
- `first_received_at`;
- `last_received_at`;
- `durable_at` optional;
- `archive_status` — `active` or `archived`.

The complete Card JSON is retained for every accepted content revision needed by
history and provenance.

## StoredInvoiceCardRevision

Immutable record of one exact accepted Card JSON payload.

Candidate fields:

- `invoice_id`;
- `content_hash`;
- complete canonical Card payload;
- Card status at this revision;
- `received_at`;
- `received_from_node_id`;
- `received_by`;
- validation result reference;
- superseded-by hash optional.

A correction made through Cabinet produces another accepted Card content hash.
The Backend stores it as another revision; it does not decompose the Card into a
separate competing `InvoiceFactsVersion` model.

## InvoiceCardValidationRecord

Deterministic validation evidence produced with the accepted Cabinet validator
or a contract-compatible implementation.

Candidate fields:

- `validation_id`;
- exact Card revision reference;
- validator version;
- `result` — `valid`, `valid_with_warnings`, or `invalid`;
- error codes;
- warning codes;
- acknowledgement evidence optional;
- `validated_at`.

Backend acceptance policy belongs to State 2. Validation findings never silently
rewrite Card values.

## DuplicateCandidateReview

Backend review record for possible duplicate invoices.

Candidate fields:

- `review_id`;
- incoming Card revision reference;
- candidate invoice IDs and content hashes;
- matching reasons;
- `status` — `open`, `not_duplicate`, `confirmed_duplicate`, or `resolved`;
- decision actor and timestamp optional.

A duplicate candidate is not automatically merged because the accepted Cabinet
behavior reports candidates rather than silently combining Cards.

---

# D. Source binary storage

## SourceBinary

Immutable binary object corresponding to source metadata already present in an
Invoice Card.

Candidate fields:

- `source_id` — from the Card `source.source_id`;
- owning `invoice_id`;
- `kind` — from Card source metadata;
- content hash;
- media type;
- size;
- original filename optional;
- first received time;
- byte status — `available`, `missing`, `quarantined`, `corrupt`, or `deleted`.

The Card remains the source of truth for its accepted source metadata. This
Backend entity records durable byte handling and verification.

## SourceBinaryReplica

Storage record for one `SourceBinary` on one Cabinet node.

Candidate fields:

- `source_id`;
- `node_id`;
- `storage_zone` — `vps_working` or `local_durable`;
- storage reference;
- stored hash;
- verification status — `pending`, `verified`, or `failed`;
- stored time;
- retention deadline optional;
- deletion time optional.

Durable local acceptance of source bytes requires successful hash verification.
A Card may temporarily reference source metadata whose binary file has not yet
been transferred; that condition must remain explicit.

---

# E. Registry catalogue and offline object work

## RegistryProjectSnapshot

Immutable projection of one Registry project.

Candidate fields:

- `snapshot_id`;
- `project_id`;
- display name;
- address or short context;
- Registry status;
- customer reference optional;
- Registry version or content hash;
- Registry timestamps;
- `captured_at`;
- source contract version.

Registry remains authoritative for project identity and current context.

## RegistryCatalogueSnapshot

Immutable compact object catalogue prepared for offline VPS use.

Candidate fields:

- `catalogue_id`;
- `generated_at`;
- `generated_by_node_id`;
- Registry observation time;
- Registry contract version;
- catalogue content hash;
- included project snapshot references;
- project count;
- completeness or filter description optional.

The catalogue must expose its age. It is a usable offline snapshot, not a claim
that Registry is currently reachable.

## RegistryCatalogueReplica

Record that one catalogue snapshot is stored on a Cabinet node.

Candidate fields:

- `catalogue_id`;
- `node_id`;
- `stored_at`;
- verification status;
- expiry time optional.

## WorkObject

Cabinet working projection for one Registry project.

```text
WorkObject.id = Registry ProjectRecord.id
```

Candidate fields:

- `project_id`;
- current Registry snapshot reference;
- first seen time;
- last seen time;
- Cabinet attention status — `active`, `historical`, or `needs_attention`.

Cabinet does not own Registry name, address, or lifecycle. Cabinet owns the
relationships, invoices, notes, matches, and history linked to `project_id`.

## CardObjectAssignmentObservation

Backend interpretation of the primary object context already stored in the
Invoice Card `object` block.

Candidate fields:

- exact Card revision reference;
- Card `object.card_id` optional;
- Card `object.label` optional;
- catalogue ID used during capture optional;
- Registry snapshot reference used during capture optional;
- decision context — `online_current`, `offline_cached`, `label_only`, or
  `unassigned`;
- observed time.

This record does not replace the Card `object` block. It adds provenance that the
V1 Card schema does not itself carry.

## ObjectAssignmentValidation

Post-reconnection validation of the Card's selected object against current
Registry data.

Candidate fields:

- `validation_id`;
- exact Card revision reference;
- observed project ID optional;
- current Registry snapshot reference optional;
- result — `valid`, `project_missing`, `project_closed`, `materially_changed`,
  `registry_unavailable`, or `inconclusive`;
- validated time;
- validated by;
- warnings and safe details.

A non-valid result does not erase or silently rewrite the Card's original object
context. A changed assignment requires an explicit new Card revision through the
accepted Cabinet workflow.

---

# F. Synchronization and import

## InvoiceWorkingReplica

Record describing which exact Invoice Card revision and source bytes are
available on one Cabinet node.

Candidate fields:

- `invoice_id`;
- `node_id`;
- highest accepted content hash;
- Card status at that hash;
- source manifest hash;
- role — `vps_working`, `local_durable`, or `read_only_cache`;
- updated time.

## InvoiceTransferManifest

Immutable description of one exact VPS-to-local transfer package.

Candidate fields:

- invoice ID;
- included Card content hashes;
- included complete Card payloads;
- included source IDs and binary hashes;
- included Registry-catalogue provenance records;
- included operational decision references;
- canonical manifest version;
- generated time;
- manifest hash.

## InvoiceSynchronization

Process entity for transferring one invoice work package from VPS to local.

Candidate fields:

- `synchronization_id`;
- `invoice_id`;
- source node ID;
- target node ID;
- transfer manifest hash;
- status — `pending`, `transferring`, `unknown_outcome`, `accepted`, `rejected`,
  `conflict`, or `failed`;
- idempotency key;
- started time;
- finished time optional;
- safe error code optional.

Synchronization state is Backend operational state and never becomes a field of
Invoice Card V1.

## InvoiceTransferReceipt

Durable local evidence for one idempotent transfer.

Candidate fields:

- synchronization ID;
- idempotency key;
- invoice ID;
- accepted manifest hash;
- accepted Card content hashes;
- accepted source hashes;
- target node ID;
- result — `accepted`, `already_accepted`, `rejected`, or `conflict`;
- accepted time optional;
- safe error code optional.

A retry with the same idempotency key and manifest must not create a second
invoice.

## SynchronizationConflict

Exceptional record for incompatible accepted Card revisions or Backend decisions
on the two nodes.

Candidate fields:

- `conflict_id`;
- invoice ID;
- affected record type;
- VPS content or decision reference;
- local content or decision reference;
- common predecessor optional;
- reason;
- detected time;
- status — `open` or `resolved`;
- explicit resolution evidence optional.

Source bytes are immutable. Conflicts concern accepted Card JSON revisions or
Backend-owned operational decisions.

## LocalBackendConnectionObservation

VPS-side operational observation.

Candidate fields:

- status — `online`, `offline`, `unauthorized`, `incompatible`, or `unknown`;
- Backend node ID optional;
- contract version optional;
- observed time;
- last success time optional;
- safe error code optional.

---

# G. PresuPro projection and matching

## EstimateReference

Value object containing:

- `estimate_id`;
- `project_id`;
- PresuPro version, content hash, or observed update timestamp;
- PresuPro status optional.

## EstimateSnapshot

Immutable local projection used for repeatable analysis.

Candidate fields:

- `snapshot_id`;
- estimate reference;
- currency;
- zones;
- items;
- totals;
- captured time;
- source contract version.

PresuPro remains authoritative for mutable estimate composition.

## EstimateItemSnapshot

Read-only comparable projection including stable item identity when available,
zone, type, description, material reference, quantity, unit, unit price, waste,
margin, discount, IVA, and totals.

## EstimateMatchSuggestion

Ephemeral agent proposal connecting one exact Invoice Card line to one exact
Estimate Item Snapshot.

Candidate fields may include confidence, explanation, alternatives, actor, and
timestamp. It is not analytical truth.

## InvoiceLineEstimateMatch

Backend-owned decision entity.

Candidate fields:

- `match_id`;
- exact confirmed Card revision and line ID;
- exact estimate snapshot and item reference;
- status — `confirmed`, `rejected`, or `invalidated`;
- decided time;
- decided by;
- explanation optional;
- invalidation reason optional.

Baseline cardinality:

- one invoice line has at most one active confirmed estimate-item match;
- one estimate item may have many matched invoice lines;
- splitting one invoice line across several estimate items is deferred.

The accepted Invoice Card V1 contains optional `matched_material_id`. That field
may assist material identification, but it is not the same record as a confirmed
Invoice Line to PresuPro Estimate Item match.

---

# H. Analytics

## PlanActualAnalysis

Calculated view assembled from:

- one exact Estimate Snapshot;
- synchronized confirmed Invoice Card revisions;
- valid or explicitly accepted object assignments;
- confirmed estimate matches;
- explicit forecast assumptions.

It may contain planned amount, actual amount, average actual price, remaining
quantity, variance, unmatched coverage, warnings, and forecasts.

Fresh VPS-only Cards may be searched and discussed using their own accepted
facts, but complete project analysis requires the local archive and PresuPro
snapshot.

---

# I. Holded publication

## HoldedPublication

Business record for publishing one exact confirmed Invoice Card revision.

Status vocabulary:

- `pending`;
- `succeeded`;
- `failed`;
- `ambiguous`;
- `cancelled`.

Candidate fields:

- `publication_id`;
- exact Card revision reference;
- idempotency key;
- external document ID optional;
- current status;
- created and completed times;
- safe outcome details.

## HoldedPublicationAttempt

Technical attempt record belonging to one `HoldedPublication`.

Retries create new attempts, not new business publications. Holded publication
is independent from PresuPro matching.

---

# J. Remaining Cabinet Cards

The Backend remains the durable core for the wider Cabinet product direction:

- `ProviderCard`;
- `ContactCard`;
- `MaterialListCard` and `MaterialListItem`;
- `DocumentCard`;
- project-linked notes and relationships.

Their exact contracts belong to their own accepted Cabinet Card specifications.
Backend State 1 must not invent replacement Card schemas for them either.

---

# K. Relationship map

```text
Registry Project 1 -> 0..* RegistryProjectSnapshots
RegistryCatalogueSnapshot 1 -> 0..* RegistryProjectSnapshots
VPS Cabinet 1 -> 0..* cached RegistryCatalogueSnapshots

StoredInvoiceCard 1 -> 1..* StoredInvoiceCardRevisions
StoredInvoiceCardRevision 1 -> 0..* validation records
StoredInvoiceCard 1 -> 0..* duplicate reviews
StoredInvoiceCard 1 -> 0..* SourceBinaries
SourceBinary 1 -> 1..* SourceBinaryReplicas
StoredInvoiceCardRevision 1 -> 0..1 CardObjectAssignmentObservation
CardObjectAssignmentObservation 1 -> 0..* ObjectAssignmentValidations

StoredInvoiceCard 1 -> 0..* synchronization transfers and receipts
Invoice Card Line 1 -> 0..1 active confirmed Estimate Match
Estimate Item 1 -> 0..* matched Invoice Card Lines
StoredInvoiceCard 1 -> 0..* Holded Publications
```

---

# L. Persisted versus calculated

Persisted on VPS for the working set:

- accepted Invoice Card JSON revisions;
- source binaries and their storage state;
- cached Registry catalogue snapshots;
- offline catalogue provenance for selected objects;
- synchronization state and receipts;
- minimal connection and session state.

Persisted locally:

- complete accepted Cabinet Card archive;
- durable source binary replicas;
- validation and duplicate-review history;
- Registry project and catalogue snapshots;
- object-validation history;
- Estimate Snapshots;
- accepted matches;
- Holded publication evidence;
- other accepted Cabinet Cards and relationships.

Calculated on demand:

- validation presentation derived from stored findings;
- totals across invoices;
- average actual prices;
- remaining planned quantities;
- plan-versus-actual variance;
- coverage and forecasts.

---

# M. Degraded-operation matrix

## Local platform offline

Available:

- creation and update of Invoice Card V1 through accepted Cabinet operations;
- source capture and VPS preservation;
- deterministic Card validation and confirmation;
- search and discussion inside the VPS working set;
- browsing the cached Registry object catalogue;
- selecting a cached object in the Card's primary `object` block;
- preserving all work for later transfer.

Unavailable or limited:

- current Registry refresh and validation;
- current PresuPro retrieval;
- complete historical search;
- durable estimate matching and full analytics;
- local integration actions.

## Local Backend online, Registry unavailable

Existing Registry snapshots remain readable. New object validation is recorded as
`registry_unavailable` or `inconclusive`; the Card's object context is not erased.

## PresuPro unavailable

Invoice Cards and accepted matches remain readable. Fresh current-plan analysis
may be unavailable unless a suitable local Estimate Snapshot exists.

## Holded unavailable

Capture, synchronization, object validation, matching, and analytics remain
available. Publication records failure or ambiguity.

---

# N. State 1 closure questions

Priority questions for State 2:

1. Which exact Invoice Card V1 validator version must the Backend use, and how is
   compatibility handled when Card versions change?
2. Does local acceptance require a `confirmed` Card, or may drafts synchronize
   and remain drafts in the durable archive?
3. Which source byte states are acceptable when the Card currently says
   `file_status = not_stored`?
4. How are later `invoice_attach_source` Card revisions transferred and retained?
5. What exact fields belong in the compact VPS Registry catalogue?
6. Is the catalogue complete for all active projects or filtered?
7. How old may a cached catalogue be before Cabinet warns or blocks selection?
8. Which Registry changes make the Card's selected object require attention?
9. Which Card payloads and source binaries must transfer atomically?
10. How is `unknown_outcome` reconciled after a timeout?
11. What exact VPS retention and backup policy protects unsynchronized work?
12. Which duplicate signals block acceptance, require acknowledgement, or only
    create a review record?
13. How does Cabinet select the relevant PresuPro estimate for a project?
14. Which PresuPro changes invalidate accepted matches?
15. How is a corrected confirmed Card handled after successful Holded publication?
16. Which additional Cabinet Card types require their own VPS working lifecycle?

State 2 will define invariants, transitions, validation policy, synchronization
policy, conflict handling, retention rules, and calculation semantics.
