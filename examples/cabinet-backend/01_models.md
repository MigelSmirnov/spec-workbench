# State 1 — Cabinet Backend domain models

## Status

Working domain-model baseline for the accepted Cabinet operating cycle.

This state defines concepts, identities, ownership, lifecycle vocabulary, and
relationships. It does not define APIs, SQL tables, ORM mappings, transport
payloads, retry algorithms, or deployment products.

## Modelling priorities

State 1 is assembled around the real product workflow:

1. preserve the received invoice image or PDF as immutable source evidence;
2. separate machine extraction from confirmed human-understood facts;
3. make Registry objects available on the VPS through a versioned cached
   catalogue;
4. permit real offline object assignment with explicit snapshot provenance;
5. transfer daytime work into the durable local archive idempotently;
6. keep PresuPro matching, analytics, and Holded publication as separate Cabinet
   decisions and integrations.

---

# A. Resolved modelling contradictions

## A.1 Source document versus Cabinet interpretation

The paper invoice, photograph, or PDF is not an editable Cabinet record. It is
primary evidence.

The model separates:

- `InvoiceDocument` — one real-world invoice or receipt known to Cabinet;
- `SourceArtifact` — one immutable received image, PDF, or other source file;
- `InvoiceExtraction` — one machine interpretation of source evidence;
- `InvoiceFactsVersion` — one structured Cabinet interpretation after edits or
  corrections;
- `InvoiceConfirmation` — acceptance of one exact facts version;
- Cabinet decisions such as object assignment, estimate matching, and Holded
  publication.

A correction changes Cabinet's interpretation. It never rewrites the source.

## A.2 Invoice identity versus storage copy

One logical invoice has one stable `invoice_id`. The VPS and local Backend may
hold different physical copies at different moments.

The model therefore separates:

- logical invoice identity;
- source and facts replicas at each Cabinet node;
- transfer and durable acceptance state.

Synchronization status is not a property of the real-world invoice itself.

## A.3 Work Object identity

Registry owns work-object identity and current context.

```text
WorkObject.id = Registry ProjectRecord.id
```

Cabinet does not create a competing standalone Work Object in this baseline. It
stores Registry snapshots and Cabinet-owned relationships linked to the same
`project_id`.

## A.4 Offline assignment validity

A VPS invoice may be assigned to an object from the cached Registry catalogue
while the local platform is offline.

This assignment is a real Cabinet decision, not merely a text suggestion. Its
provenance records the exact Registry snapshot or catalogue version used.

Current Registry validation occurs after reconnection. A validation warning does
not silently erase the user's original assignment.

## A.5 Confirmation versus later decisions

Confirmation means that an actor accepts what Cabinet currently believes the
source document says. It does not imply:

- current Registry validation;
- PresuPro matching;
- complete analytics;
- Holded publication;
- successful local synchronization.

Each later decision references the exact confirmed facts version it used.

---

# B. Shared model primitives

## ActorReference

Value object identifying the actor responsible for an action.

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

## Money

Value object containing decimal `amount` and ISO `currency`.

Currency conversion is never implicit.

## Quantity

Value object containing decimal `value`, normalized `unit`, and optional original
unit text.

## ExactVersionReference

Value object pinning exact accepted content.

Candidate fields:

- `entity_type`;
- `entity_id`;
- `version_number`;
- `content_hash`.

---

# C. Invoice source evidence

## InvoiceDocument

Aggregate root representing one real-world supplier invoice, receipt, or purchase
document known to Cabinet.

Candidate fields:

- `invoice_id` — created at first VPS capture and preserved locally;
- `created_at`;
- `created_by`;
- `lifecycle_status` — `active` or `archived`;
- `current_facts_version` optional;
- `current_confirmation_id` optional.

`InvoiceDocument` is the stable Cabinet identity around the source evidence and
its interpretation history.

## SourceArtifact

Immutable source entity representing one received photograph, PDF, or other
piece of evidence.

Candidate fields:

- `source_id`;
- `invoice_id`;
- `kind` — `photo`, `pdf`, `scan`, or `other`;
- `content_hash`;
- `media_type`;
- `size_bytes`;
- `received_at`;
- `captured_at` optional;
- `original_filename` optional;
- `created_by`;
- `source_role` — `primary`, `additional_view`, or `supporting`;
- `status` — `available`, `quarantined`, `corrupt`, or `deleted`.

The byte content is immutable. A better photograph creates another
`SourceArtifact`; it does not replace the earlier one.

## SourceReplica

Storage record for one `SourceArtifact` on one Cabinet node.

Candidate fields:

- `source_id`;
- `node_id`;
- `storage_zone` — `vps_working` or `local_durable`;
- `storage_ref`;
- `stored_hash`;
- `verification_status` — `pending`, `verified`, or `failed`;
- `stored_at`;
- `retention_until` optional;
- `deleted_at` optional.

A source is durably accepted locally only after required bytes are stored and
hash-verified.

## SourceRegionReference

Value object linking extracted data to evidence.

Candidate fields:

- `source_id`;
- page optional;
- region or fragment locator optional;
- observed_text optional.

---

# D. Extraction and confirmed invoice facts

## InvoiceExtraction

Immutable record of one machine extraction attempt.

Candidate fields:

- `extraction_id`;
- `invoice_id`;
- source artifact references;
- extraction engine and version;
- raw extracted text optional;
- structured candidate facts;
- field-level confidence and source regions;
- `created_at`;
- `created_by`;
- `status` — `completed`, `partial`, or `failed`.

An extraction is evidence of what the machine proposed. It is never silently
rewritten after a human correction.

## InvoiceFactsVersion

Immutable structured Cabinet interpretation of what the invoice says.

Candidate fields:

- `invoice_id`;
- `version_number`;
- `parent_version_number` optional;
- `content_hash`;
- `based_on_extraction_ids`;
- `invoice_number` optional;
- `issue_date` optional;
- `supply_date` optional;
- `due_date` optional;
- `currency`;
- `supplier`;
- `buyer`;
- `lines`;
- `totals`;
- `payment_summary`;
- field-level source references;
- `created_at`;
- `created_by`;
- `change_reason` optional.

A correction creates a new facts version. Earlier versions remain available for
history and provenance.

## InvoiceConfirmation

Decision record accepting one exact `InvoiceFactsVersion`.

Candidate fields:

- `confirmation_id`;
- exact facts-version reference;
- `confirmed_at`;
- `confirmed_by`;
- `scope` — baseline value `source_facts`;
- `notes` optional;
- `status` — `active` or `superseded`.

A new facts version requires a new confirmation before actions that require
confirmed facts.

## InvoiceParty

Source-faithful supplier or buyer value object.

Candidate fields:

- `name` optional;
- `tax_id` optional;
- `address` optional;
- `email` optional;
- `phone` optional;
- original unparsed text optional.

A Provider Card match may link to this party but must not overwrite the
source-faithful values.

## InvoiceLine

Entity inside an `InvoiceFactsVersion`.

Candidate fields:

- `line_id`;
- `kind` — `item`, `service`, `shipping`, `discount`, `fee`, `tax`, or `other`;
- `description_original`;
- `supplier_sku` optional;
- `quantity` optional;
- `unit_price_net` optional;
- `discount` optional;
- `tax_rate` optional;
- `net_amount` optional;
- `tax_amount` optional;
- `gross_amount` optional;
- source region references.

Material normalization and estimate matching are separate Cabinet decisions.

## InvoiceTotals

Value object containing optional monetary values:

- `net`;
- `discount`;
- `tax`;
- `gross`;
- `withholding`;
- `payable`.

Printed totals are preserved even when calculated line sums differ. The
difference becomes a validation finding.

## PaymentSummary

Source-faithful payment statement.

Status vocabulary:

- `unknown`;
- `unpaid`;
- `partially_paid`;
- `paid`;
- `partially_refunded`;
- `refunded`.

Candidate fields may include paid amount, refunded amount, stated method, and
source evidence. Cabinet does not invent payment facts from absence of evidence.

---

# E. Registry object catalogue and offline assignment

## RegistryProjectSnapshot

Immutable local projection of one Registry object.

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
- `source_contract_version`.

Registry remains authoritative for identity and current context.

## RegistryCatalogueSnapshot

Immutable snapshot of the compact object catalogue published to the VPS.

Candidate fields:

- `catalogue_id`;
- `generated_at`;
- `generated_by_node_id`;
- Registry observation time;
- Registry contract version;
- catalogue content hash;
- included project snapshot references;
- project count;
- optional completeness or filter description.

The catalogue is not claimed to be current after its capture time. Its age must
be available to the user and agent.

## RegistryCatalogueReplica

Record that a specific catalogue snapshot is available on a Cabinet node.

Candidate fields:

- `catalogue_id`;
- `node_id`;
- `stored_at`;
- `verification_status`;
- `expires_at` optional.

## WorkObject

Cabinet working projection for one Registry project.

```text
WorkObject.id = Registry ProjectRecord.id
```

Candidate fields:

- `project_id`;
- `current_registry_snapshot_id`;
- `first_seen_at`;
- `last_seen_at`;
- `cabinet_status` — `active`, `historical`, or `needs_attention`.

The Work Object does not own Registry name, address, or lifecycle. Cabinet owns
relationships and history linked to the `project_id`.

## InvoiceObjectAssignment

Cabinet-owned decision assigning an invoice to one Registry work object or
intentionally leaving it unassigned.

State vocabulary:

- `unreviewed`;
- `assigned`;
- `intentionally_unassigned`;
- `invalidated`;
- `needs_attention`.

Candidate fields:

- `assignment_id`;
- `invoice_id`;
- exact facts-version reference optional;
- `state`;
- `project_id` optional;
- `catalogue_id` optional;
- `registry_snapshot_id` optional;
- `decision_context` — `online_current`, `offline_cached`, or `manual_unassigned`;
- `decided_at`;
- `decided_by`;
- `reason` optional;
- `supersedes_assignment_id` optional.

An `offline_cached` assignment is valid Cabinet work. It records the catalogue
and project snapshot used for selection.

## AssignmentValidation

Post-reconnection validation of one assignment against current Registry data.

Candidate fields:

- `validation_id`;
- `assignment_id`;
- current Registry snapshot reference optional;
- `result` — `valid`, `project_missing`, `project_closed`, `materially_changed`,
  `registry_unavailable`, or `inconclusive`;
- `validated_at`;
- `validated_by`;
- warnings;
- safe details optional.

A non-valid result does not overwrite the assignment. It changes its attention
state or leads to an explicit replacement decision.

---

# F. Replica ownership and synchronization

## InvoiceWorkingReplica

Record describing invoice work available at one Cabinet node.

Candidate fields:

- `invoice_id`;
- `node_id`;
- highest facts version present;
- active confirmation present optional;
- source artifact manifest hash;
- `role` — `vps_working`, `local_durable`, or `read_only_cache`;
- `updated_at`.

The VPS is the working owner before durable local acceptance. The local Backend
becomes the complete durable archive after acceptance.

## InvoiceSynchronization

Process entity for transferring one invoice work package from VPS to local.

Candidate fields:

- `synchronization_id`;
- `invoice_id`;
- `source_node_id`;
- `target_node_id`;
- exact transfer-manifest hash;
- `status` — `pending`, `transferring`, `unknown_outcome`, `accepted`,
  `rejected`, `conflict`, or `failed`;
- `idempotency_key`;
- `started_at`;
- `finished_at` optional;
- `last_error_code` optional.

## InvoiceTransferManifest

Immutable value object describing the exact transfer set.

Candidate fields:

- invoice identity;
- included source artifact IDs and hashes;
- included extraction IDs;
- included facts-version references;
- included confirmation references;
- included assignment and assignment-validation references;
- other included Cabinet decision references;
- canonical format version;
- generated time and manifest hash.

## InvoiceTransferReceipt

Durable local evidence for one idempotent transfer.

Candidate fields:

- `synchronization_id`;
- `idempotency_key`;
- `invoice_id`;
- accepted manifest hash;
- accepted source hashes;
- `target_node_id`;
- `result` — `accepted`, `already_accepted`, `rejected`, or `conflict`;
- `accepted_at` optional;
- `safe_error_code` optional.

Acceptance requires durable storage and verification of all mandatory source
artifacts and structured records in the manifest.

## SynchronizationConflict

Exceptional entity created when the same logical record has incompatible later
changes on both nodes or when expected-version checks fail.

Candidate fields:

- `conflict_id`;
- `invoice_id`;
- affected record type and identity;
- VPS version reference;
- local version reference;
- common ancestor optional;
- reason;
- `detected_at`;
- `status` — `open` or `resolved`;
- explicit resolution evidence optional.

Conflicts concern Cabinet interpretations or decisions, never mutation of source
bytes.

## LocalBackendConnectionObservation

VPS-side operational observation.

Candidate fields:

- `status` — `online`, `offline`, `unauthorized`, `incompatible`, or `unknown`;
- backend node ID optional;
- contract version optional;
- `observed_at`;
- `last_success_at` optional;
- safe error code optional.

---

# G. PresuPro estimate projection

## EstimateReference

Value object containing:

- `estimate_id`;
- `project_id`;
- PresuPro version, content hash, or observed update timestamp;
- optional PresuPro status.

## EstimateSnapshot

Immutable local external projection used for repeatable analysis.

Candidate fields:

- `snapshot_id`;
- `reference`;
- `currency`;
- zones;
- items;
- totals;
- `captured_at`;
- `source_contract_version`.

## EstimateItemSnapshot

Read-only comparable projection including stable item identity when available,
zone, type, description, material reference, quantity, unit, unit price, waste,
margin, discount, IVA, and totals.

PresuPro remains authoritative for mutable plan composition.

---

# H. Agent-assisted normalization and matching

## MaterialIdentificationSuggestion

Ephemeral agent proposal connecting one invoice line to a known material or
normalized product concept.

It may include confidence, explanation, alternatives, actor, and timestamp. It
never modifies source-faithful invoice facts.

## EstimateMatchSuggestion

Ephemeral agent proposal connecting one exact invoice line facts version to one
exact Estimate Item Snapshot.

It is not analytical truth.

## InvoiceLineEstimateMatch

Cabinet-owned decision entity.

Candidate fields:

- `match_id`;
- exact confirmed invoice facts version and line ID;
- exact estimate snapshot and item reference;
- `status` — `confirmed`, `rejected`, or `invalidated`;
- `decided_at`;
- `decided_by`;
- explanation optional;
- invalidation reason optional.

Baseline cardinality:

- one invoice line has at most one active confirmed match;
- one estimate item may have many matched invoice lines;
- splitting one invoice line across several estimate items is deferred.

---

# I. Analytics

## PlanActualAnalysis

Calculated view assembled from:

- one exact Estimate Snapshot;
- synchronized confirmed invoice facts;
- valid object assignments;
- confirmed estimate matches;
- explicit forecast assumptions.

It may contain planned amount, actual amount, average price, remaining quantity,
variance, unmatched coverage, warnings, and forecasts.

Fresh VPS-only invoices may be discussed using their own facts, but complete
project analysis requires the local archive and PresuPro snapshot.

---

# J. Holded publication

## HoldedPublication

Business record for publishing one exact confirmed invoice facts version.

Status vocabulary:

- `pending`;
- `succeeded`;
- `failed`;
- `ambiguous`;
- `cancelled`.

Candidate fields:

- `publication_id`;
- exact confirmation reference;
- idempotency key;
- external document ID optional;
- current status;
- created and completed timestamps;
- safe outcome details.

## HoldedPublicationAttempt

Technical attempt record belonging to one `HoldedPublication`.

Retries create new attempts, not new business publications.

Holded publication is independent from PresuPro matching.

---

# K. Remaining Cabinet Cards

State 1 retains the broader Cabinet product direction:

- `ProviderCard`;
- `ContactCard`;
- `MaterialListCard` and `MaterialListItem`;
- `DocumentCard`;
- project-linked notes and relationships.

Their exact fields belong to later focused modelling. They remain part of the
same personal working-memory product rather than separate systems.

---

# L. Relationship map

```text
Registry Project 1 -> 0..* RegistryProjectSnapshots
RegistryCatalogueSnapshot 1 -> 0..* RegistryProjectSnapshots
VPS Cabinet 1 -> 0..* cached RegistryCatalogueSnapshots

InvoiceDocument 1 -> 1..* SourceArtifacts
SourceArtifact 1 -> 1..* SourceReplicas
InvoiceDocument 1 -> 0..* InvoiceExtractions
InvoiceDocument 1 -> 1..* InvoiceFactsVersions
InvoiceFactsVersion 1 -> 0..1 active InvoiceConfirmation
InvoiceDocument 1 -> 0..* InvoiceObjectAssignments
InvoiceObjectAssignment 1 -> 0..* AssignmentValidations

InvoiceDocument 1 -> 0..* synchronization transfers and receipts
Invoice Line 1 -> 0..1 active confirmed Estimate Match
Estimate Item 1 -> 0..* matched Invoice Lines
InvoiceDocument 1 -> 0..* Holded Publications
```

---

# M. Persisted versus calculated

Persisted on VPS for the working set:

- immutable received source artifacts;
- extraction attempts;
- invoice facts versions and confirmations;
- cached Registry catalogue snapshots;
- offline object assignments and provenance;
- synchronization state and receipts;
- minimal connection and session state.

Persisted locally:

- complete Cabinet archive;
- durable source replicas;
- all extraction and correction history;
- Registry project and catalogue snapshots;
- assignments and validation history;
- Estimate Snapshots;
- accepted matches;
- Holded publication evidence;
- other Cabinet Cards and relationships.

Calculated on demand:

- invoice validation findings;
- totals across invoices;
- average actual prices;
- remaining planned quantities;
- plan-versus-actual variance;
- coverage and forecasts.

---

# N. Degraded-operation matrix

## Local platform offline

Available:

- invoice capture and immutable source preservation;
- extraction, correction, and confirmation;
- search and discussion inside the VPS working set;
- browsing the cached Registry object catalogue;
- assigning invoices to cached objects;
- preserving all work for later transfer.

Unavailable or limited:

- current Registry refresh;
- current PresuPro retrieval;
- complete historical search;
- durable estimate matching and full analytics;
- local integration actions.

## Local Backend online, Registry unavailable

Existing snapshots and cached assignments remain readable. New validation is
recorded as `registry_unavailable`; prior user decisions are not erased.

## PresuPro unavailable

Invoices and accepted matches remain readable. Fresh current-plan analysis may be
unavailable unless a suitable local Estimate Snapshot exists.

## Holded unavailable

Capture, synchronization, assignment, matching, and analytics remain available.
Publication records failure or ambiguity.

---

# O. State 1 closure questions

Priority questions for State 2:

1. What exact fields belong in the compact VPS Registry catalogue?
2. Is the catalogue complete for all active objects or filtered by user or
   business status?
3. How old may a cached catalogue be before Cabinet warns or blocks assignment?
4. Which Registry changes make an offline assignment `needs_attention` rather
   than still valid?
5. May a source document contain several photos and one PDF, and how are they
   grouped as one real-world invoice?
6. Which extracted fields require explicit human confirmation?
7. Can confirmation be partial when one field remains unreadable?
8. Which facts corrections invalidate object assignment, estimate matching, or
   Holded eligibility?
9. Which source artifacts and structured records must transfer atomically?
10. How is `unknown_outcome` reconciled after a timeout?
11. What exact VPS retention and backup policy protects unsynchronized work?
12. How does Cabinet select the relevant PresuPro estimate for a project?
13. Which PresuPro changes invalidate accepted matches?
14. How are corrected facts handled after successful Holded publication?
15. Which additional Cabinet Card types require their own VPS working lifecycle?

State 2 will define invariants, transitions, validation rules, synchronization
policy, conflict handling, and calculation semantics.
