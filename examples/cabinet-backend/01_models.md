# State 1 — Cabinet Backend domain models

## Status

Working domain-model baseline for the accepted Cabinet Backend operating cycle.

This state defines Backend-owned concepts, identities, ownership, lifecycle
vocabulary, and relationships. It does not redefine the already implemented
Cabinet Invoice Card V1 contract. It also does not define APIs, SQL tables, ORM
mappings, transport payloads, retry algorithms, or deployment products.

## State 1 boundary

Cabinet Backend must:

1. accept and preserve an existing Invoice Card V1 without changing its meaning;
2. store every accepted Card content revision and its original source bytes;
3. publish a versioned Registry project catalogue to the VPS for offline use;
4. retain evidence of which catalogue was used when an object was selected;
5. import daytime VPS work into the local durable archive idempotently;
6. distinguish received, validated, quarantined, and durably accepted work;
7. validate the selected Registry project after reconnection without erasing the
   user's original Card context;
8. keep PresuPro matching, analytics, synchronization state, duplicate review,
   and Holded publication outside immutable Invoice Card facts.

---

# A. Accepted Invoice Card boundary

## Invoice Card V1

Invoice Card V1 is an existing Cabinet contract. Backend consumes the complete
canonical Card JSON and validates it using the accepted Cabinet validator or a
contract-compatible implementation.

The Card already owns:

- stable `id`;
- `card_type` and `card_version`;
- lifecycle `status` — `draft`, `confirmed`, or `archived`;
- invoice number and dates;
- supplier and buyer facts;
- currency, lines, totals, and payment transactions;
- required primary `object` block;
- source metadata;
- provenance;
- canonical SHA-256 content revision.

Backend must preserve unknown or currently unused Card fields. It must not
introduce alternative line kinds, payment meanings, arithmetic rules, object
shape, source shape, or invoice revision numbering.

## InvoiceCardRevisionReference

Value object pinning one exact accepted Card payload.

Candidate fields:

- `invoice_id`;
- `card_version`;
- `content_hash`;
- `observed_status`;
- `observed_at`.

`content_hash` is the Card revision identity already defined by Cabinet.

---

# B. Shared Backend primitives

## ActorReference

Provenance value object.

Candidate fields:

- `actor_type` — `user`, `agent`, `service`, `import`, or `system`;
- `actor_id`;
- `delegated_by` optional;
- `interaction_id` optional;
- `display_label` optional.

It is not an authentication session.

## CabinetNodeIdentity

Identity of one participating Cabinet node.

Candidate fields:

- `node_id`;
- `node_kind` — `vps_cabinet` or `local_backend`;
- `status` — `active` or `revoked`;
- `contract_version`;
- `created_at`;
- `revoked_at` optional.

## ContentReference

Value object referencing immutable content.

Candidate fields:

- `content_kind`;
- `content_id`;
- `content_hash`;
- `size_bytes` optional;
- `media_type` optional.

---

# C. Accepted Card archive

## StoredInvoiceCard

Local archive identity for one logical Invoice Card.

Candidate fields:

- `invoice_id` — equal to Card `id`;
- `card_version`;
- `current_content_hash`;
- `current_status`;
- `first_received_at`;
- `last_received_at`;
- `durable_at` optional;
- `archive_status` — `active` or `archived`.

## StoredInvoiceCardRevision

Immutable storage record for one exact canonical Card JSON payload.

Candidate fields:

- exact Card revision reference;
- complete canonical Card payload;
- `received_at`;
- `received_from_node_id`;
- `received_by`;
- validation record reference;
- predecessor content hash optional;
- superseded-by content hash optional.

A later Cabinet correction is another Card content revision. Backend does not
split it into a competing invoice-facts schema.

## InvoiceCardValidationRecord

Deterministic validation evidence.

Candidate fields:

- `validation_id`;
- exact Card revision reference;
- validator contract and version;
- `result` — `valid`, `valid_with_warnings`, or `invalid`;
- error codes;
- warning codes;
- acknowledgement evidence optional;
- `validated_at`.

Validation never silently rewrites the Card.

## DuplicateCandidateReview

Review record for possible duplicate logical invoices.

Candidate fields:

- `review_id`;
- incoming Card revision reference;
- candidate invoice IDs and revision hashes;
- matching reasons and evidence;
- `status` — `open`, `not_duplicate`, `confirmed_duplicate`, or `resolved`;
- decision actor and time optional;
- resolution reference optional.

Duplicate candidates are not automatically merged.

---

# D. Source binary archive

## SourceBinary

Immutable binary object corresponding to source metadata in an Invoice Card.

Candidate fields:

- `source_id` — from Card `source.source_id`;
- owning `invoice_id`;
- source kind from the Card;
- binary content hash;
- media type;
- size bytes;
- original filename optional;
- first received time;
- `byte_status` — `available`, `missing`, `quarantined`, `corrupt`, or `deleted`.

The Card remains authoritative for accepted source metadata. `SourceBinary`
records byte handling and verification.

## SourceBinaryReplica

Storage record for one binary on one Cabinet node.

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

A Card may temporarily reference a source whose bytes are not yet available.
That condition is explicit and is not equivalent to durable local acceptance.

---

# E. Registry catalogue and offline object work

## RegistryProjectSnapshot

Immutable projection of one Registry project.

Candidate fields:

- `snapshot_id`;
- `project_id`;
- display name;
- address or compact context;
- Registry status;
- customer reference optional;
- Registry version or content hash;
- Registry timestamps;
- `captured_at`;
- source contract version.

Registry remains authoritative for project identity and current context.

## RegistryCatalogueSnapshot

Immutable compact project catalogue prepared for offline VPS use.

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

The catalogue exposes its age. It is usable offline but never claims Registry is
currently reachable.

## RegistryCataloguePublication

Backend record of publishing one catalogue snapshot from local to VPS.

Candidate fields:

- `publication_id`;
- `catalogue_id`;
- source and target node IDs;
- idempotency key;
- `status` — `pending`, `transferring`, `accepted`, `failed`, or
  `unknown_outcome`;
- requested, completed, and acknowledged times;
- safe error code optional.

## RegistryCatalogueReplica

Record that one exact catalogue snapshot is available on one Cabinet node.

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

Cabinet owns relationships, invoices, notes, matches, and history linked to the
Registry `project_id`; it does not own Registry name, address, or lifecycle.

## CardObjectAssignmentObservation

Backend interpretation of the primary object context already stored in the Card
`object` block.

Candidate fields:

- exact Card revision reference;
- observed `object.card_id` optional;
- observed `object.label` optional;
- catalogue ID used during capture optional;
- Registry project snapshot used during capture optional;
- decision context — `online_current`, `offline_cached`, `label_only`, or
  `unassigned`;
- observed time.

This record adds provenance that Invoice Card V1 does not carry. It does not
replace the Card `object` block.

## ObjectAssignmentValidation

Post-reconnection validation against current Registry data.

Candidate fields:

- `validation_id`;
- exact Card revision reference;
- observed project ID optional;
- current Registry snapshot reference optional;
- `result` — `valid`, `project_missing`, `project_closed`,
  `materially_changed`, `registry_unavailable`, or `inconclusive`;
- validated time and actor;
- warnings and safe details.

A non-valid result does not erase the original Card context. Changing the object
requires an explicit new Card revision through Cabinet.

---

# F. VPS-to-local transfer and import

## InvoiceTransferManifest

Immutable description of one exact work package sent by the VPS.

Candidate fields:

- `manifest_id`;
- invoice ID;
- included complete Card payloads and content hashes;
- included source IDs, binary hashes, sizes, and media types;
- included Registry-catalogue provenance records;
- included Backend decision references when applicable;
- canonical manifest version;
- generated time;
- manifest hash.

## InvoiceSynchronization

Transport process for one manifest.

Candidate fields:

- `synchronization_id`;
- invoice ID;
- source and target node IDs;
- manifest hash;
- `status` — `pending`, `transferring`, `unknown_outcome`, `delivered`,
  `failed`, or `cancelled`;
- idempotency key;
- started and finished times optional;
- safe error code optional.

`delivered` means the target received the package. It does not by itself mean
that the package was validated or committed to the durable archive.

## InvoiceImport

Local Backend process that validates and commits one delivered manifest.

Candidate fields:

- `import_id`;
- synchronization ID and manifest hash;
- invoice ID;
- `status` — `received`, `validating`, `quarantined`, `accepted`, `rejected`,
  or `already_accepted`;
- received time;
- validation completed time optional;
- durable commit time optional;
- rejection or quarantine reason codes;
- accepted Card hashes;
- accepted source hashes;
- duplicate-review reference optional.

This separation prevents transport success from being mistaken for durable
business acceptance.

## ImportQuarantine

Record for a package that arrived but cannot yet be accepted or rejected safely.

Candidate fields:

- `quarantine_id`;
- import ID;
- missing or invalid component references;
- reason — `missing_source_bytes`, `hash_mismatch`, `invalid_card`,
  `unsupported_card_version`, `incomplete_manifest`, `duplicate_review`, or
  `operator_review`;
- opened time;
- status — `open`, `resolved`, or `discarded`;
- resolution evidence optional.

Quarantine preserves the received package without presenting it as part of the
normal durable archive.

## InvoiceTransferReceipt

Durable target evidence returned to the VPS.

Candidate fields:

- synchronization ID;
- import ID optional;
- idempotency key;
- invoice ID;
- manifest hash;
- `result` — `accepted`, `already_accepted`, `quarantined`, `rejected`, or
  `unknown`;
- accepted Card and source hashes;
- receipt time;
- safe error code optional.

A retry with the same idempotency key and manifest must resolve to the same
logical import and must not create a second invoice.

## InvoiceWorkingReplica

Record describing which exact Card revisions and source bytes are available on
one Cabinet node.

Candidate fields:

- invoice ID;
- node ID;
- accepted Card content hashes;
- current Card hash optional;
- source manifest hash;
- role — `vps_working`, `local_durable`, or `read_only_cache`;
- updated time.

## SynchronizationConflict

Exceptional record for incompatible accepted Card revisions or Backend decisions
on two nodes.

Candidate fields:

- `conflict_id`;
- invoice ID;
- affected record type;
- VPS and local references;
- common predecessor optional;
- reason;
- detected time;
- status — `open` or `resolved`;
- explicit resolution evidence optional.

Source bytes are immutable. Conflicts concern Card JSON revisions or
Backend-owned operational decisions.

## LocalBackendConnectionObservation

VPS-side reachability observation.

Candidate fields:

- `status` — `online`, `offline`, `unauthorized`, `incompatible`, or `unknown`;
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
- PresuPro version, content hash, or observed update time;
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

Ephemeral agent proposal connecting one exact Card line to one exact Estimate
Item Snapshot. It is not analytical truth.

## InvoiceLineEstimateMatch

Backend-owned decision entity.

Candidate fields:

- `match_id`;
- exact confirmed Card revision and line ID;
- exact estimate snapshot and item reference;
- `status` — `confirmed`, `rejected`, or `invalidated`;
- decided time and actor;
- explanation optional;
- invalidation reason optional.

Baseline cardinality:

- one invoice line has at most one active confirmed estimate-item match;
- one estimate item may have many matched invoice lines;
- splitting one invoice line across several estimate items is deferred.

Card field `matched_material_id` may assist material identification but is not a
confirmed PresuPro Estimate Item match.

---

# H. Analytics

## PlanActualAnalysis

Calculated view assembled from:

- one exact Estimate Snapshot;
- locally accepted confirmed Invoice Card revisions;
- valid or explicitly accepted object assignments;
- confirmed estimate matches;
- explicit forecast assumptions.

It may contain planned amount, actual amount, average actual price, remaining
quantity, variance, unmatched coverage, warnings, and forecasts.

Fresh VPS-only Cards may be searched and discussed, but complete project analysis
requires the local archive and a PresuPro snapshot.

---

# I. Holded publication

## HoldedPublication

Business record for publishing one exact confirmed Card revision.

Candidate fields:

- `publication_id`;
- exact Card revision reference;
- idempotency key;
- `status` — `pending`, `succeeded`, `failed`, `ambiguous`, or `cancelled`;
- external document ID optional;
- created and completed times;
- safe outcome details.

## HoldedPublicationAttempt

Technical attempt belonging to one `HoldedPublication`. Retries create attempts,
not new business publications.

Holded publication is independent from PresuPro matching.

---

# J. Remaining Cabinet Cards

Backend remains the durable core for the wider Cabinet product direction:

- `ProviderCard`;
- `ContactCard`;
- `MaterialListCard` and `MaterialListItem`;
- `DocumentCard`;
- project-linked notes and relationships.

Their shapes belong to their accepted Cabinet Card specifications. Backend State
1 must not invent replacement schemas for them.

---

# K. Relationship map

```text
Registry Project 1 -> 0..* RegistryProjectSnapshots
RegistryCatalogueSnapshot 1 -> 0..* RegistryProjectSnapshots
RegistryCatalogueSnapshot 1 -> 0..* CataloguePublications and Replicas

StoredInvoiceCard 1 -> 1..* StoredInvoiceCardRevisions
StoredInvoiceCardRevision 1 -> 0..* ValidationRecords
StoredInvoiceCard 1 -> 0..* DuplicateCandidateReviews
StoredInvoiceCard 1 -> 0..* SourceBinaries
SourceBinary 1 -> 1..* SourceBinaryReplicas
StoredInvoiceCardRevision 1 -> 0..1 CardObjectAssignmentObservation
CardObjectAssignmentObservation 1 -> 0..* ObjectAssignmentValidations

InvoiceTransferManifest 1 -> 1 InvoiceSynchronization
InvoiceSynchronization 1 -> 0..1 InvoiceImport
InvoiceImport 1 -> 0..1 ImportQuarantine
InvoiceImport 1 -> 1 InvoiceTransferReceipt

Invoice Card Line 1 -> 0..1 active confirmed EstimateMatch
Estimate Item 1 -> 0..* matched Invoice Card Lines
StoredInvoiceCard 1 -> 0..* HoldedPublications
```

---

# L. Persisted versus calculated

Persisted on VPS for the working set:

- accepted Invoice Card JSON revisions;
- source binaries and storage state;
- cached Registry catalogue snapshots;
- catalogue provenance for selected objects;
- synchronization manifests, states, and receipts;
- minimal connection and session state.

Persisted locally:

- complete accepted Cabinet Card archive;
- durable source binary replicas;
- validation, import, quarantine, and duplicate-review history;
- Registry project and catalogue snapshots;
- catalogue publication and object-validation history;
- Estimate Snapshots and accepted matches;
- Holded publication evidence;
- other accepted Cabinet Cards and relationships.

Calculated on demand:

- validation presentation from stored findings;
- totals across invoices;
- average actual prices;
- remaining planned quantities;
- plan-versus-actual variance;
- coverage and forecasts.

---

# M. Degraded-operation matrix

## Local platform offline

Available:

- Invoice Card V1 creation and update through accepted Cabinet operations;
- source capture and VPS preservation;
- deterministic Card validation and confirmation;
- search and discussion inside the VPS working set;
- browsing the cached Registry catalogue;
- selecting a cached object in the Card `object` block;
- preserving all work for later transfer.

Unavailable or limited:

- current Registry refresh and validation;
- current PresuPro retrieval;
- complete historical search;
- durable estimate matching and full analytics;
- local integration actions.

## Transfer delivered but import quarantined

The VPS retains its authoritative working copy. The local package is preserved
for repair or review but is excluded from normal local archive queries,
analytics, matching, and Holded publication until accepted.

## Local Backend online, Registry unavailable

Existing Registry snapshots remain readable. New validation records
`registry_unavailable` or `inconclusive`; Card object context is not erased.

## PresuPro unavailable

Cards and accepted matches remain readable. Fresh current-plan analysis may be
unavailable unless a suitable Estimate Snapshot exists.

## Holded unavailable

Capture, synchronization, object validation, matching, and analytics remain
available. Publication records failure or ambiguity.

---

# N. State 1 closure questions

Questions requiring State 2 policy or local-platform evidence:

1. Which exact Invoice Card validator version must Backend use, and how are newer
   Card versions negotiated?
2. May draft Cards enter the durable archive, or does normal acceptance require
   `confirmed`?
3. Which source-byte states permit acceptance when Card metadata says
   `file_status = not_stored`?
4. Must Card payloads and mandatory source bytes commit atomically, or may a
   quarantined partial import later become accepted?
5. Which duplicate signals block acceptance, require acknowledgement, or only
   open review?
6. What exact fields belong in the compact VPS Registry catalogue?
7. Is the catalogue complete for all active projects or filtered?
8. How old may a catalogue be before Cabinet warns or blocks selection?
9. Which Registry changes require attention for a previously selected project?
10. How is `unknown_outcome` reconciled for catalogue publication and invoice
    transfer?
11. What VPS retention and backup policy protects unsynchronized work?
12. How does Cabinet select the relevant PresuPro estimate for a project?
13. Which PresuPro changes invalidate accepted matches?
14. How is a corrected confirmed Card handled after successful Holded
    publication?
15. Which additional Cabinet Card types require their own VPS working lifecycle?

State 2 will define invariants, transitions, validation and acceptance policy,
synchronization and reconciliation rules, retention, and calculation semantics.
