# State 1 — Cabinet Backend domain models

## Status

Working domain-model baseline for the accepted two-tier Cabinet architecture.

This state defines concepts, identities, ownership, lifecycle vocabulary, and
relationships. It deliberately does not define APIs, SQL tables, ORM mappings,
transport payloads, retry algorithms, or deployment products.

## Modelling priorities

State 1 is assembled in this order:

1. resolve contradictions in identity, authority, revision, and synchronization;
2. define the Invoice aggregate and its source-faithful facts;
3. define local project and estimate projections;
4. define Cabinet-owned decisions, publications, and calculated views;
5. leave policy and transition details for State 2.

---

# A. Resolved modelling contradictions

## A.1 Logical Invoice versus deployment copy

`InvoiceCard` is one logical business entity. Synchronization status is not a
field of that business entity because VPS and local storage can observe different
copies and revisions at the same time.

The model therefore separates:

- `InvoiceCard` — stable logical identity;
- `InvoiceRevision` — immutable source-faithful state at one revision number;
- `InvoiceReplica` — the presence and role of that invoice at one Cabinet node;
- `InvoiceSynchronization` — transfer and acceptance state between replicas.

This avoids one shared `sync_state` field having incompatible values on two
nodes.

## A.2 Revision number versus content identity

A revision number orders revisions within one `invoice_id`. A content hash
identifies exact canonical content. They are not alternatives.

Every accepted revision has both:

- `revision_number` — monotonic within the Invoice Card;
- `content_hash` — deterministic hash of canonical revision content.

## A.3 Business confirmation versus synchronization

Confirmation means that a user or authorized actor accepts the extracted invoice
facts represented by one exact revision. It does not mean that synchronization,
project assignment, estimate matching, or Holded publication has completed.

Synchronization may transfer draft or confirmed revisions, subject to State 2
policy. A `confirmed` marker always pins an exact revision and never floats to a
later correction automatically.

## A.4 Source identity versus storage location

A received original is one logical `SourceArtifact`. VPS and local files are
storage replicas of that artifact, not separate sources merely because they live
in different zones.

## A.5 Publication record versus transport attempts

A Holded publication is the business intent and outcome for one exact confirmed
invoice revision. Retries are separate attempt records. A retry must not create a
second business publication.

## A.6 Current estimate versus repeatable analysis

PresuPro owns the mutable current estimate. Cabinet analysis and accepted matches
pin a captured `EstimateSnapshot`; they do not silently follow later PresuPro
changes.

---

# B. Shared model primitives

## ActorReference

Value object identifying the actor responsible for a domain action.

Candidate fields:

- `actor_type` — `user`, `agent`, `service`, `import`, or `system`;
- `actor_id`;
- `delegated_by` optional;
- `interaction_id` optional;
- `display_label` optional.

It records provenance, not authentication or authorization state.

## CabinetNodeIdentity

Identity of one participating Cabinet node.

Candidate fields:

- `node_id`;
- `node_kind` — `vps_cabinet` or `local_backend`;
- `status` — `active` or `revoked`;
- `contract_version`;
- `created_at`;
- `revoked_at` optional.

## EntityRevisionReference

Value object pinning exact entity content.

Candidate fields:

- `entity_type`;
- `entity_id`;
- `revision_number`;
- `content_hash`.

## Money

Value object containing decimal `amount` and ISO `currency`.

Currency conversion is never implicit. Values in different currencies cannot be
summed without an explicit conversion record and rate source.

## Quantity

Value object containing decimal `value` and normalized `unit`, while retaining
the original unit text when normalization is uncertain.

---

# C. Source evidence

## SourceArtifact

Logical source entity representing an original received invoice photograph, PDF,
or other evidence.

Candidate fields:

- `source_id`;
- `kind`;
- `content_hash`;
- `media_type`;
- `size_bytes`;
- `received_at`;
- `captured_at` optional;
- `original_filename` optional;
- `created_by`;
- `status` — `available`, `quarantined`, `corrupt`, or `deleted`.

The source identity is stable across transfer. A source is not considered
locally durable merely because metadata was synchronized.

## SourceReplica

Storage record for one `SourceArtifact` on one Cabinet node.

Candidate fields:

- `source_id`;
- `node_id`;
- `storage_zone` — `vps_working` or `local_durable`;
- `storage_ref`;
- `stored_hash`;
- `verification_status` — `pending`, `verified`, `failed`;
- `stored_at`;
- `deleted_at` optional;
- `retention_until` optional.

Durable local acceptance requires all mandatory source replicas to be stored and
hash-verified according to State 2 policy.

## SourceUse

Relationship pinning a source or a region of a source to extracted facts.

Candidate fields:

- `source_id`;
- page, region, or fragment locator optional;
- extraction method;
- confidence optional;
- observed_at.

---

# D. Invoice aggregate

## InvoiceCard

Aggregate root representing one supplier invoice, receipt, or purchase.

Candidate fields:

- `invoice_id` — created at first VPS capture and never replaced during sync;
- `created_at`;
- `created_by`;
- `current_revision_number`;
- `lifecycle_status` — `active` or `archived`.

`InvoiceCard` contains identity and revision lineage. Mutable invoice facts live
inside immutable `InvoiceRevision` records.

## InvoiceRevision

Immutable entity containing the complete source-faithful invoice state at one
point in its history.

Candidate fields:

- `invoice_id`;
- `revision_number`;
- `parent_revision_number` optional;
- `content_hash`;
- `document_status` — `draft` or `confirmed`;
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
- `source_uses`;
- `created_at`;
- `created_by`;
- `confirmation` optional;
- `correction_reason` optional.

A later correction creates a new revision. Existing confirmations, matches,
synchronization receipts, analyses, and publications continue to reference the
older exact revision unless explicitly superseded.

## InvoiceConfirmation

Decision record confirming one exact invoice revision.

Candidate fields:

- `invoice_revision`;
- `confirmed_at`;
- `confirmed_by`;
- `confirmation_scope` — baseline value `source_facts`;
- `notes` optional.

Only one active confirmation may exist for an exact revision. A new revision
requires a new confirmation before actions that require confirmed facts.

## InvoiceParty

Source-faithful supplier or buyer value object.

Candidate fields:

- `name` optional;
- `tax_id` optional;
- `address` optional;
- `email` optional;
- `phone` optional;
- original unparsed text optional.

A Cabinet provider match may reference this party but must not overwrite the
source-faithful values.

## InvoiceLine

Entity inside an `InvoiceRevision`.

Candidate fields:

- `line_id` — stable across revisions when the same logical line is edited;
- `kind` — `item`, `service`, `shipping`, `discount`, `fee`, `tax`, or `other`;
- `description_original`;
- `description_normalized` optional;
- `supplier_sku` optional;
- `quantity` optional;
- `unit_price_net` optional;
- `discount` optional;
- `tax_rate` optional;
- `net_amount` optional;
- `tax_amount` optional;
- `gross_amount` optional;
- `source_uses`.

`matched_material_id` is intentionally excluded. Material normalization and
estimate matching are Cabinet decisions outside source-faithful invoice facts.

## InvoiceTotals

Value object containing optional monetary values:

- `net`;
- `discount`;
- `tax`;
- `gross`;
- `withholding`;
- `payable`.

The model preserves printed totals even when calculated line sums differ. The
difference becomes a validation finding rather than an automatic rewrite.

## PaymentSummary

Invoice-level source statement with status:

- `unknown`;
- `unpaid`;
- `partially_paid`;
- `paid`;
- `partially_refunded`;
- `refunded`.

Candidate fields may include paid amount, refunded amount, stated method, and
source evidence. Actual accounting transactions belong to separate imported or
integration records and are not invented from absence of evidence.

---

# E. Replica ownership and synchronization

## InvoiceReplica

Entity describing the presence and authority role of one logical invoice at one
Cabinet node.

Candidate fields:

- `invoice_id`;
- `node_id`;
- `highest_present_revision`;
- `highest_verified_revision`;
- `authority_role` — `authoritative_workspace`, `durable_primary`, or
  `read_only_replica`;
- `write_status` — `editable`, `read_only`, or `checked_out`;
- `created_at`;
- `updated_at`.

Baseline authority:

- before first durable local acceptance, the VPS replica is
  `authoritative_workspace`;
- after durable local acceptance, the local replica is `durable_primary`;
- the synchronized VPS replica becomes `read_only_replica` in the baseline.

## InvoiceSynchronization

Process entity for synchronizing one logical invoice from the VPS to the local
Backend.

Candidate fields:

- `synchronization_id`;
- `invoice_id`;
- `source_node_id`;
- `target_node_id`;
- `requested_revision`;
- `status` — `pending`, `transferring`, `unknown_outcome`, `accepted`,
  `rejected`, `conflict`, or `failed`;
- `idempotency_key`;
- `expected_target_revision` optional;
- `started_at`;
- `finished_at` optional;
- `last_error_code` optional.

`local_only` and `remote_only` are not synchronization statuses. They are derived
from which `InvoiceReplica` records exist and which revisions each contains.

## InvoiceTransferManifest

Immutable value object describing the exact transfer set.

Candidate fields:

- `invoice_revision`;
- required revision chain references;
- required source artifact references and hashes;
- canonical format version;
- generated_at.

## InvoiceTransferReceipt

Durable local evidence for one idempotent synchronization request.

Candidate fields:

- `synchronization_id`;
- `idempotency_key`;
- `invoice_id`;
- `accepted_revision` optional;
- accepted source hashes;
- `target_node_id`;
- `result` — `accepted`, `already_accepted`, `rejected`, or `conflict`;
- `accepted_at` optional;
- `safe_error_code` optional.

An `accepted` receipt is valid only when the local Backend has durably stored and
verified the revision and all mandatory source artifacts.

## InvoiceSyncConflict

Entity created when expected revision checks show that neither side may overwrite
the other.

Candidate fields:

- `conflict_id`;
- `invoice_id`;
- `vps_revision`;
- `local_revision`;
- `common_ancestor_revision` optional;
- `reason`;
- `detected_at`;
- `status` — `open` or `resolved`;
- `resolution` optional;
- `resolved_by` optional;
- `resolved_at` optional.

Conflicts remain modelled even with single-owner baseline editing because they
can result from stale clients, interrupted authority transfer, operator repair,
software defects, or a future checked-out revision workflow.

## LocalBackendConnectionObservation

VPS-side operational observation, not durable business truth.

Candidate fields:

- `status` — `online`, `offline`, `unauthorized`, `incompatible`, or `unknown`;
- `backend_node_id` optional;
- `contract_version` optional;
- `observed_at`;
- `last_success_at` optional;
- `safe_error_code` optional.

---

# F. Work Object and Registry projection

## WorkObject

Local project-scoped entity whose identity equals Registry project identity:

```text
WorkObject.id = Registry ProjectRecord.id
```

Candidate fields:

- `project_id`;
- `created_at`;
- `created_by`;
- `current_registry_snapshot_id`;
- `lifecycle_status` — `active` or `archived`.

A Work Object may be created only after a successful Registry read confirms the
project identity. One Registry project has at most one persisted Work Object.

## RegistryProjectSnapshot

Immutable persisted external projection.

Candidate fields:

- `snapshot_id`;
- `project_id`;
- display name;
- address;
- status;
- customer reference;
- Registry timestamps;
- Registry version or content hash;
- `captured_at`;
- `source_contract_version`.

Registry remains authoritative. Cabinet may operate from an older snapshot while
explicitly reporting its age and freshness.

## RegistryObservationState

Operational state for a project read:

- `current`;
- `stale`;
- `unavailable`;
- `not_found`.

`not_found` is an observed Registry result and does not silently delete an
existing Work Object.

## InvoiceObjectAssignment

Cabinet-owned decision record, separate from invoice source facts.

States:

- `unreviewed`;
- `label_only`;
- `assigned`;
- `intentionally_unassigned`;
- `invalidated`.

Candidate fields:

- `assignment_id`;
- `invoice_revision`;
- `state`;
- `project_id` optional;
- `label` optional;
- `registry_snapshot_id` optional;
- `decided_at`;
- `decided_by`;
- `reason` optional.

A validated `assigned` decision requires a local Work Object and pins the
Registry snapshot used for validation. VPS-only work may preserve a label or an
assignment suggestion but cannot create a validated `assigned` decision.

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
- `zones`;
- `items`;
- `totals`;
- `captured_at`;
- `source_contract_version`.

## EstimateZoneSnapshot

Candidate fields:

- stable zone ID when provided;
- version-pinned fingerprint otherwise;
- name;
- position;
- parent zone reference optional.

## EstimateItemSnapshot

Read-only comparable projection.

Candidate fields:

- stable item ID when provided;
- version-pinned fingerprint otherwise;
- zone reference;
- item type;
- name and description;
- material reference optional;
- quantity and unit;
- unit price;
- waste;
- margin;
- discount;
- IVA;
- totals.

PresuPro remains authoritative for mutable plan composition. Cabinet snapshots
are evidence of what was observed, not an editable copy of the plan.

---

# H. Agent-assisted normalization and matching

## MaterialIdentificationSuggestion

Ephemeral agent proposal connecting one Invoice Line to a known material or
normalized product concept.

It may include confidence, explanation, alternatives, actor, and timestamp. It
never modifies the source-faithful Invoice Line.

## EstimateMatchSuggestion

Ephemeral agent proposal connecting one exact invoice line revision to one exact
Estimate Item Snapshot.

Candidate fields include confidence, explanation, alternatives, actor, and
timestamp. It is not analytical truth.

## InvoiceLineEstimateMatch

Cabinet-owned decision entity.

Candidate fields:

- `match_id`;
- exact invoice revision and line ID;
- exact estimate snapshot and item reference;
- `status` — `confirmed`, `rejected`, or `invalidated`;
- `decided_at`;
- `decided_by`;
- suggestion provenance optional;
- invalidation reason optional.

Baseline cardinality:

- one invoice line in one exact revision has at most one active confirmed match;
- one estimate item may have many matched invoice lines;
- distribution of one invoice line across multiple estimate items is deferred.

A later invoice revision or incompatible estimate snapshot does not silently
retarget the match. State 2 defines invalidation rules.

---

# I. Plan-versus-actual analysis

## PlanActualAnalysisRequest

Value object pinning all analysis inputs:

- `project_id`;
- `estimate_snapshot_id`;
- included confirmed invoice revisions;
- included confirmed match IDs;
- requested_at;
- requested_by;
- forecast assumptions optional.

## PlanActualAnalysis

Calculated view, not a source-of-truth entity.

May contain:

- planned and actual quantity and amount;
- average actual price;
- remaining quantity and budget;
- variance;
- matched and unmatched coverage;
- stale-input warnings;
- explicit forecast assumptions;
- input references and calculation version.

Complete project analysis uses locally available synchronized invoices and local
project data. VPS-only invoices may be discussed from their own facts but are not
presented as complete project actuals.

---

# J. Holded publication

## HoldedPublication

Business entity representing publication of one exact confirmed Invoice
Revision.

Candidate fields:

- `publication_id`;
- `invoice_revision`;
- `idempotency_key`;
- `status` — `pending`, `succeeded`, `failed`, `ambiguous`, `cancelled`, or
  `superseded`;
- `external_document_id` optional;
- `created_at`;
- `created_by`;
- `completed_at` optional;
- correction or supersession reference optional.

Publication eligibility is independent from PresuPro matching.

## HoldedPublicationAttempt

Technical attempt record owned through the Holded integration boundary.

Candidate fields:

- `attempt_id`;
- `publication_id`;
- `attempt_number`;
- `started_at`;
- `finished_at` optional;
- result;
- gateway receipt optional;
- safe error optional.

Credentials, transport retries, and reconciliation stay inside Holded Gateway.

---

# K. Remaining Cabinet Cards

The local durable domain retains:

- `ProviderCard`;
- `ContactCard`;
- `MaterialListCard` and `MaterialListItem`;
- `DocumentCard`;
- embedded baseline `ProjectNote`.

These models require further assembly. They remain local-only unless a later
product decision grants a specific VPS lifecycle.

A generic `Card` superclass is not yet accepted. Shared search, provenance, and
revision capabilities may be implemented through common interfaces or metadata
without forcing unrelated aggregates into one lifecycle.

---

# L. Relationship map

```text
InvoiceCard 1 -> 1..* InvoiceRevision
InvoiceRevision 1 -> 0..1 InvoiceConfirmation
InvoiceRevision 1 -> 1..* SourceUse
SourceArtifact 1 -> 1..* SourceReplica

InvoiceCard 1 -> 1..* InvoiceReplica
InvoiceCard 1 -> 0..* InvoiceSynchronization
InvoiceSynchronization 1 -> 0..1 InvoiceTransferReceipt
InvoiceCard 1 -> 0..* InvoiceSyncConflict

Registry Project 1 <-> 0..1 WorkObject
WorkObject 1 -> 1..* RegistryProjectSnapshot
InvoiceRevision 1 -> 0..* InvoiceObjectAssignment
WorkObject 1 <- 0..* validated InvoiceObjectAssignment

PresuPro Estimate 1 -> 1..* EstimateSnapshot
EstimateSnapshot 1 -> 0..* EstimateItemSnapshot
Invoice Line Revision 1 -> 0..1 active confirmed InvoiceLineEstimateMatch
Estimate Item Snapshot 1 -> 0..* InvoiceLineEstimateMatch

Confirmed InvoiceRevision 1 -> 0..* HoldedPublication
HoldedPublication 1 -> 0..* HoldedPublicationAttempt
```

---

# M. Persisted versus calculated

Persisted on VPS for the fresh working set:

- logical Invoice Cards and revisions created there;
- protected source artifacts and VPS source replicas;
- confirmations and provenance;
- VPS Invoice Replica records;
- synchronization processes, manifests, and received receipts;
- connection observations needed for operation.

Persisted locally:

- complete Invoice Card revision history accepted by the local Backend;
- durable source replicas and verification evidence;
- local Invoice Replica and synchronization receipts;
- Work Objects and Registry snapshots;
- Estimate Snapshots;
- assignment and match decisions;
- Holded publication evidence;
- other Cabinet Cards and history.

Calculated on demand:

- replica-derived labels such as `remote_only`, `local_only`, and
  `synchronized`;
- totals across invoices;
- average actual prices;
- remaining planned quantities;
- plan-versus-actual variance;
- coverage and forecasts.

---

# N. Degraded-operation behaviour

## Local Backend offline

Available on VPS:

- fresh invoice capture and source preservation;
- extraction, revision editing, confirmation, search, and discussion inside the
  VPS working set;
- creation of labels and assignment suggestions;
- queued idempotent synchronization intent.

Unavailable or limited:

- validated Registry assignment;
- current PresuPro retrieval;
- complete historical search;
- durable estimate matching and complete project analytics;
- local integration actions.

## Local Backend online, Registry unavailable

Existing local Work Objects and Registry snapshots remain usable with explicit
freshness warnings. New unknown Work Objects cannot be validated.

## PresuPro unavailable

Invoices and prior decisions remain readable. Repeatable analysis may use an
explicitly selected existing Estimate Snapshot; it must not claim to represent
the current plan unless freshness is known.

## Holded unavailable

Invoice capture, synchronization, assignment, matching, and analytics remain
available. Publication records a failed or ambiguous attempt without duplicating
the business publication.

---

# O. State 1 closure questions

Questions are ordered by risk to model consistency.

1. Is the baseline after-sync VPS policy strictly read-only, or is an explicit
   checked-out revision required in the first product?
2. Which revision chain and source artifacts form the minimum atomic durable
   acceptance set?
3. May draft revisions synchronize, or only confirmed revisions?
4. Can a newer draft exist after an older confirmed revision, and which revision
   is shown as the current working revision?
5. What exact VPS retention and deletion guarantees apply after local durable
   acceptance?
6. How is `unknown_outcome` reconciled and when may a transfer be retried?
7. Which authority-transfer failures create a conflict rather than a retryable
   synchronization failure?
8. How does Cabinet select the relevant PresuPro estimate for a project?
9. Which stable IDs exist for PresuPro zones and items?
10. Who may validate project assignments and confirm estimate matches?
11. Which invoice, assignment, Registry, and estimate changes invalidate a
    confirmed match?
12. How are corrected invoices represented after successful Holded publication?
13. Which remaining Card types need revision history, and which need a VPS
    working lifecycle?
14. What backup, quarantine, retention, and deletion guarantees apply to each
    source storage zone?

State 2 will define invariants, state transitions, authority transfer,
synchronization policy, validation matrices, invalidation rules, and calculation
semantics.
