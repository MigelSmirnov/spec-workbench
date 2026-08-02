# State 1 — Cabinet Backend domain models

## Status

Structured domain-model baseline for the accepted two-tier Cabinet architecture.
It defines concepts and ownership, not APIs, tables, transports, or algorithms.

## State 1 boundary

State 1 defines:

- entities, value objects, external projections, decision records, and calculated
  views;
- stable identity and lifecycle vocabulary;
- VPS versus local ownership;
- synchronization and conflict concepts;
- persisted versus calculated information;
- unresolved model questions.

State 1 does not define endpoints, ORM mappings, SQL schemas, exact sync
protocols, retry algorithms, formulas, or deployment product choices.

---

# A. Shared models

## Card

Entity abstraction for searchable and revisable Cabinet knowledge.

Candidate fields:

- `id`;
- `card_type`;
- `title` or typed display context;
- `status`;
- `created_at`;
- `updated_at`;
- `revision`;
- `created_by`;
- `sources`.

Generic lifecycle: `active`, `archived`. Specialized Cards may define richer
lifecycles.

## ActorReference

Value object identifying `user`, `agent`, `service`, `import`, or `system`.
It is provenance, not an authentication session.

Candidate fields:

- `actor_type`;
- `actor_id`;
- `delegated_by` optional;
- `interaction_id` optional;
- `display_label` optional.

## SourceReference

Entity or value object referencing original evidence.

Candidate fields:

- `source_id`;
- `kind`;
- `storage_zone` — `vps_working` or `local_durable`;
- `file_ref`;
- `file_status`;
- `content_hash`;
- `media_type`;
- `received_at`;
- `captured_at` optional;
- `size_bytes` optional.

## RevisionReference

Value object pinning one exact entity revision.

- `entity_id`;
- `revision` or `content_hash`;
- `observed_at` optional.

---

# B. Two-tier Cabinet access and synchronization

## CabinetInstallationIdentity

Security/integration identity for one Cabinet deployment, not a business Card.

Candidate fields:

- `installation_id`;
- `installation_kind` — `vps_cabinet` or `local_backend`;
- `status` — `active`, `revoked`;
- `created_at`;
- `revoked_at` optional.

## LocalBackendConnectionState

VPS-side value object describing current local-platform reachability.

Status vocabulary:

- `online`;
- `offline`;
- `unauthorized`;
- `incompatible`;
- `unknown`.

Candidate fields:

- `status`;
- `backend_instance_id` optional;
- `contract_version` optional;
- `last_attempt_at`;
- `last_success_at` optional;
- `last_error_code` optional.

## InvoiceSyncState

Mutable state associated with one logical Invoice Card.

Status vocabulary:

- `remote_only` — current revision exists only in VPS working storage;
- `syncing` — one exact revision is being transferred;
- `synchronized` — local Backend durably accepted the source and revision;
- `local_only` — historical invoice exists only in the local archive;
- `conflict` — both sides contain incompatible later revisions;
- `failed` — synchronization failed with a known retryable or terminal result;
- `unknown_outcome` — transport ended without knowing whether local acceptance
  occurred.

Candidate fields:

- `invoice_id`;
- `status`;
- `vps_revision` optional;
- `local_revision` optional;
- `last_attempt_at` optional;
- `last_success_at` optional;
- `idempotency_key` optional;
- `last_error_code` optional;
- `conflict_ref` optional.

## InvoiceTransferCommand

Integration command value object for one revision transfer.

Candidate fields:

- `command_id`;
- `idempotency_key`;
- `invoice_id`;
- `invoice_revision`;
- `expected_local_revision` optional;
- `source_manifest`;
- `actor_reference`;
- `sent_at`.

## InvoiceTransferReceipt

Durable evidence returned by the local Backend.

Candidate fields:

- `command_id`;
- `invoice_id`;
- `accepted_revision`;
- `source_hash`;
- `backend_instance_id`;
- `accepted_at`;
- `result` — `accepted`, `already_accepted`, `rejected`, `conflict`;
- `safe_error_code` optional.

## InvoiceSyncConflict

Decision-support entity when neither side may silently overwrite the other.

Candidate fields:

- `conflict_id`;
- `invoice_id`;
- `vps_revision`;
- `local_revision`;
- `detected_at`;
- `reason`;
- `status` — `open`, `resolved`;
- `resolution` optional;
- `resolved_by` optional;
- `resolved_at` optional.

Baseline direction: unrestricted multi-master editing is not supported. After
successful synchronization, the VPS record is read-only unless an explicit
checked-out/new-revision workflow is introduced.

---

# C. Invoice aggregate

## InvoiceCard

Entity and aggregate root representing one supplier invoice, receipt, or
purchase.

Candidate fields:

- `id` — stable across VPS and local storage;
- `status` — `draft`, `confirmed`, `archived`;
- `invoice_number` optional;
- dates and currency;
- `supplier` and `buyer`;
- `object_assignment`;
- `lines`;
- `totals`;
- `payment`;
- `sources`;
- `provenance`;
- `revision` or canonical hash;
- `sync_state`.

Authority rules:

- a `remote_only` invoice is authoritative on the VPS;
- a synchronized invoice is durably owned by the local Backend;
- stable identity and accepted revision history survive transfer;
- estimate matches and Holded publication remain separate records.

## InvoiceParty

Source-faithful supplier or buyer value object with optional `name`, `tax_id`,
and `address`.

## InvoiceLine

Entity inside Invoice Card.

Candidate fields:

- `line_id`;
- `kind`;
- `description_original`;
- `description_normalized` optional;
- `supplier_sku` optional;
- `matched_material_id` optional;
- `quantity`;
- `unit`;
- `unit_price_net`;
- discount, tax, net, and gross fields.

Invoice Line meanings are intentionally comparable with PresuPro Estimate Item
meanings without copying plan data into invoice facts.

## InvoiceTotals

Value object: `net`, `discount`, `tax`, `gross`, `withholding`, `payable`.

## Payment and PaymentTransaction

Payment status vocabulary:

- `unknown`;
- `unpaid`;
- `partially_paid`;
- `paid`;
- `refunded`.

Several transactions may represent split cash/card settlement. Absence of
evidence means `unknown`.

## InvoiceObjectAssignment

Mutable decision with states:

- `unreviewed`;
- `assigned`;
- `intentionally_unassigned`;
- `label_only`.

A VPS-only invoice may hold `unreviewed`, `intentionally_unassigned`, or
`label_only`. Validated `assigned` requires an existing local Work Object backed
by Registry evidence.

---

# D. Work Object and Registry

## WorkObject

Project-scoped entity whose identity is Registry project identity:

```text
WorkObject.id = Registry ProjectRecord.id
```

Created locally after a successful first Registry context read.

Candidate fields:

- `id`;
- `registry_snapshot`;
- `registry_sync`;
- `created_at`;
- `updated_at`;
- `revision`.

## RegistryProjectSnapshot

Persisted external projection containing project ID, display name, address,
status, customer reference, Registry timestamps, and Cabinet capture time.

## RegistrySyncState

Statuses: `current`, `stale`, `unavailable`, `not_found`.

Registry unavailability is distinct from Local Backend unavailability.

---

# E. PresuPro estimate projection

## EstimateReference

Value object containing:

- `estimate_id`;
- `project_id`;
- `estimate_updated_at`;
- `estimate_content_hash` or stable version;
- optional status.

## EstimateSnapshot

Local persisted external projection used for repeatable analysis and accepted
matches.

Candidate fields:

- `reference`;
- `currency`;
- `zones`;
- `totals`;
- `captured_at`;
- `source_contract_version`.

PresuPro remains authoritative. Snapshot persistence does not make Cabinet the
plan owner.

## EstimateZoneReference and EstimateItemReference

References include stable IDs when provided, otherwise version-pinned
fingerprints and temporary locators.

## EstimateComparableItem

Read-only projection including type, name, material reference, quantity, unit,
unit price, discounts, IVA, waste, and margin.

---

# F. Agent-assisted matching and analytics

## EstimateMatchSuggestion

Ephemeral agent proposal with invoice line, estimate item, confidence,
explanation, alternatives, actor, and timestamp. It is not analytical truth.

## InvoiceLineEstimateMatch

Cabinet-owned decision entity.

Statuses:

- `confirmed`;
- `rejected`;
- `invalidated`.

Baseline cardinality:

- one Invoice Line has at most one active confirmed match;
- one Estimate Item may have many Invoice Lines;
- one-line-to-many-item distribution is deferred.

Only confirmed matches participate in plan-versus-actual analysis.

## PlanActualAnalysis

Calculated view assembled from an Estimate Snapshot, synchronized confirmed
Invoice Cards, and confirmed matches.

May contain item-level and project-level planned amount, actual amount, average
price, remaining quantity, variance, unmatched coverage, warnings, and explicit
forecast assumptions.

Fresh VPS-only invoices may be analyzed locally within their own facts, but they
are excluded from complete project plan-versus-actual until synchronized and
matched against local project data.

---

# G. Holded publication

## HoldedPublication

Integration entity for one exact confirmed Invoice Card revision.

Statuses:

- `pending`;
- `succeeded`;
- `failed`;
- `ambiguous`;
- `cancelled`.

Candidate fields include publication ID, invoice ID and revision, idempotency
key, timestamps, external document ID, gateway receipt, and safe errors.

Holded publication is independent from PresuPro matching. Holded credentials
remain inside Holded Gateway.

---

# H. Remaining Cabinet Cards

State 1 retains these entities:

- `ProviderCard`;
- `ContactCard`;
- `MaterialListCard` and `MaterialListItem`;
- `DocumentCard`;
- embedded baseline `ProjectNote`.

They remain local durable archive models unless a later product decision grants
a specific VPS working lifecycle.

---

# I. Relationship map

```text
VPS Cabinet Installation 1 -> 0..* remote_only fresh Invoice Cards
Local Cabinet Backend 1 -> 0..* synchronized and historical Cabinet Cards

Logical Invoice Card 1 -> 1 current InvoiceSyncState
Invoice Card 1 -> 1..* revisions
Invoice Card 1 -> 1..* source references
Invoice Card 1 -> 1..* invoice lines
Invoice Card 1 -> 0..* transfer commands and receipts
Invoice Card 1 -> 0..* synchronization conflicts

Registry Project 1 <-> 0..1 Work Object
Work Object 1 <-> 0..* synchronized Invoice Cards
PresuPro Estimate 1 -> 0..* Estimate Items
Invoice Line 1 -> 0..1 active confirmed Estimate Match
Estimate Item 1 -> 0..* matched Invoice Lines
Invoice Card 1 -> 0..* Holded Publication attempts
```

---

# J. Persisted versus calculated

Persisted on VPS for the fresh working set:

- unsynchronized Invoice Cards and revisions;
- their protected originals;
- provenance;
- synchronization state and receipts;
- minimal user/session and connection state.

Persisted locally:

- complete Cabinet archive;
- synchronized originals and revisions;
- Work Objects and Registry snapshots;
- Estimate Snapshots;
- accepted matches;
- Holded publication evidence;
- other Cabinet Cards and history.

Calculated on demand:

- totals across invoices;
- average actual prices;
- remaining planned quantities;
- plan-versus-actual variance;
- coverage and forecasts.

---

# K. Degraded-operation matrix

## Local Backend offline

Available:

- fresh invoice capture, extraction, editing, confirmation, search, and
  discussion inside the VPS working set.

Unavailable or limited:

- validated Registry assignment;
- current PresuPro retrieval;
- complete historical search;
- durable matching and full project analytics;
- local integration actions.

## Local Backend online, Registry unavailable

Existing local Cabinet data and Work Objects remain available from snapshots;
new unknown Work Objects cannot be validated.

## PresuPro unavailable

Invoices and accepted matches remain readable; fresh current-plan analysis may
be unavailable unless a suitable local Estimate Snapshot exists.

## Holded unavailable

Invoice capture, synchronization, matching, and analytics remain available;
publication records failure or ambiguity.

---

# L. State 1 closure questions

1. After synchronization, is the VPS invoice strictly read-only or may Cabinet
   explicitly check out a new revision?
2. What exact VPS working-set retention applies after local acceptance?
3. Are confirmed invoices allowed to synchronize before source OCR/extraction is
   complete?
4. Which source files and revision history must be transferred atomically?
5. How is `unknown_outcome` reconciled?
6. What conflicts can exist if baseline editing is single-owner after sync?
7. How does Cabinet select the relevant PresuPro estimate for a project?
8. Which stable IDs exist for estimate zones and items?
9. Who may confirm estimate matches?
10. Which changes invalidate confirmed matches?
11. How are corrected invoices handled after successful Holded publication?
12. Which remaining Card types need a VPS working lifecycle?
13. What is the precise partial-refund meaning of `refunded`?
14. What source retention, backup, and deletion guarantees apply in each zone?

State 2 will define invariants, transitions, conflict rules, synchronization
policy, calculation semantics, and validation tables.
