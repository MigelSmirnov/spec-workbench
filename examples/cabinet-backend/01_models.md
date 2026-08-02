# State 1 — Cabinet Backend domain models

## Status

Structured State 1 domain-model baseline. It records the complete model
skeleton required before rules, module responsibilities, flows, APIs,
contracts, persistence, and implementation are designed.

## State 1 boundary

This document defines:

- which domain concepts exist;
- which concepts are entities, value objects, external projections, decisions,
  and calculated views;
- stable identity and lifecycle vocabulary;
- authoritative ownership;
- candidate fields;
- cardinality and relationship intent;
- which information is persisted and which is calculated on demand;
- unresolved questions that must remain visible before State 1 closes.

This document does not define:

- PostgreSQL tables, columns, indexes, or migrations;
- ORM mappings;
- HTTP, MCP, CLI, or event endpoints;
- exact function signatures;
- module and package ownership;
- orchestration sequences;
- formulas, transition rules, validation algorithms, or retry policies;
- concrete Holded, PresuPro, Registry, or Client Portal transport shapes.

## Model categories

The State 1 model uses the following categories:

- **Entity** — has stable identity and history independent from its current
  field values;
- **Value object** — identified by its complete value and normally embedded in
  another model;
- **External projection** — typed data owned by another system and consumed by
  Cabinet without becoming Cabinet-owned truth;
- **Decision record** — Cabinet-owned accepted or rejected interpretation;
- **Calculated view** — derived on demand and not an independent source of
  truth.

---

# A. Shared Cabinet models

## Card

### Kind

Entity abstraction for user-facing Cabinet records.

### Meaning

A `Card` is an independently searchable, openable, revisable, and archivable
piece of Cabinet knowledge. Provider, Contact, Material List, Document, and
Invoice are Card types. Work Object participates in the same user-facing card
experience but uses Registry project identity directly.

### Candidate fields

- `id` — stable Card identity;
- `card_type`;
- `title` or typed display context;
- `status`;
- `created_at`;
- `updated_at`;
- `revision`;
- `created_by`;
- `sources`;
- optional tags and notes where supported by the specialized type.

### Ownership

Cabinet owns Card identity, lifecycle, relationships, revisions, and history.
External source systems may own values copied into specialized Card fields.

### Baseline lifecycle vocabulary

Generic Cards use:

- `active`;
- `archived`.

Specialized Cards may define a richer lifecycle, such as Invoice Card
`draft`, `confirmed`, and `archived`.

### Invariants deferred to State 2

- identity stability;
- archive behavior;
- revision monotonicity;
- whether a specialized lifecycle replaces or extends the generic lifecycle.

## ActorReference

### Kind

Value object.

### Meaning

Identifies the actor responsible for a Cabinet observation, decision, or
mutation without embedding authentication credentials.

### Candidate fields

- `actor_type` — `user`, `agent`, `service`, `import`, or `system`;
- `actor_id`;
- `display_label` optional.

### Boundaries

`ActorReference` is provenance, not an authorization decision and not an
identity-provider session.

## SourceReference

### Kind

Entity or value object depending on final source-storage design.

### Meaning

References original evidence from which Cabinet facts were extracted or
confirmed.

### Candidate fields

- `source_id`;
- `kind` — photograph, PDF, scan, message, imported file, or other controlled
  source kind;
- `file_ref` optional;
- `file_status`;
- `content_hash` optional;
- `media_type` optional;
- `captured_at` optional;
- `received_at`;
- `note` optional.

### Ownership

Cabinet owns source metadata and provenance. The binary-storage owner remains
an open infrastructure decision.

## RevisionReference

### Kind

Value object.

### Meaning

Pins a downstream decision or integration action to one exact revision of a
Cabinet entity.

### Candidate fields

- `entity_id`;
- `revision` or `content_hash`;
- `observed_at` optional.

### Consumers

- estimate matching;
- Holded publication;
- conflict detection;
- audit and correction workflows.

---

# B. Work Object and Registry models

## WorkObject

### Kind

Entity and project-scoped Cabinet aggregate root.

### Meaning

`WorkObject` is Cabinet's local working interface for one Registry project. It
organises Cabinet-owned purchases, material lists, documents, contacts,
providers, notes, accepted estimate matches, and integration history for that
project.

It is not a second project entity. Its identity is the platform project
identity:

```text
WorkObject.id = Registry ProjectRecord.id
```

### Creation

Cabinet creates the persisted Work Object representation lazily after receiving
a Registry `project_id` and successfully obtaining the first project context.
Repeated opening of the same `project_id` resolves to the same Work Object.

### Candidate fields

- `id` — Registry project UUID;
- `registry_snapshot` — current durable `RegistryProjectSnapshot`;
- `registry_sync` — current `RegistrySyncState`;
- `created_at` — time Cabinet first persisted the representation;
- `updated_at` — time Cabinet-owned state or external evidence last changed;
- `revision`.

A separate Cabinet alias is not required in the baseline. It may be added later
only for a concrete user need.

### Relationships

A Work Object may relate to:

- zero or more Invoice Cards through current primary assignment;
- zero or more Material List Cards;
- zero or more Document Cards;
- zero or more Contact Cards;
- zero or more Provider Cards;
- zero or more Project Notes;
- zero or more confirmed Invoice Line to Estimate Item matches;
- zero or more Holded publication records for its invoices.

### Ownership

Registry owns project identity and current project context. Cabinet owns the
local representation, stored external evidence, Cabinet relationships,
decisions, and history.

### Baseline invariants

- Work Object ID is a valid Registry project UUID;
- one Registry project resolves to at most one persisted Work Object;
- initial creation requires a successful Registry context read;
- Registry field changes do not change Work Object identity;
- Registry unavailability does not invalidate or delete an existing Work
  Object;
- ordinary Cabinet edits cannot alter Registry-owned snapshot values;
- archived Registry projects remain readable and reject new project-scoped
  operational assignment by default.

## RegistryProjectSnapshot

### Kind

Persisted external projection and historical evidence value object.

### Meaning

Cabinet's durable copy of the last successfully observed Registry project
context. It enables Cabinet UI and agents to continue basic project-scoped work
when Registry is temporarily unavailable.

### Candidate fields

- `project_id`;
- `display_name`;
- `address`;
- `project_status` — currently `active` or `archived`;
- `customer_ref` optional;
- `project_created_at`;
- `registry_updated_at`;
- `captured_at`.

### Ownership

Registry owns all values except `captured_at`, which records Cabinet observation
time.

### Baseline invariants

- `project_id` equals the parent Work Object ID;
- all fields come from one successful Registry response;
- snapshot replacement is atomic;
- fields are not edited individually by Cabinet users or agents;
- stale snapshots remain valid historical evidence but are not presented as
  current Registry truth.

## RegistrySyncState

### Kind

Persisted value object.

### Meaning

Records Cabinet's knowledge about refreshing Registry context.

### Status vocabulary

- `current`;
- `stale`;
- `unavailable`;
- `not_found`.

Registry project lifecycle remains separate inside the snapshot.

### Candidate fields

- `status`;
- `last_attempt_at`;
- `last_success_at`;
- `last_error_code` optional;
- `last_error_message` optional safe diagnostic.

---

# C. Invoice aggregate

## InvoiceCard

### Kind

Entity and aggregate root.

### Meaning

Represents one supplier invoice, receipt, or material purchase and preserves the
source-faithful facts required for validation, search, Holded publication, and
plan-versus-actual analysis.

### Candidate fields

- `id`;
- `status`;
- `invoice_number` optional;
- `issue_date` optional;
- `service_date` optional;
- `due_date` optional;
- `currency`;
- `supplier`;
- `buyer`;
- `object_assignment`;
- `lines`;
- `totals`;
- `payment`;
- `source`;
- `provenance`;
- `revision` or canonical content hash.

### Lifecycle vocabulary

- `draft`;
- `confirmed`;
- `archived`.

### Ownership

Cabinet owns Invoice Card identity, accepted structured facts, lifecycle,
source provenance, and revisions. PresuPro matches and Holded publication state
are separate mutable records and do not become invoice facts.

## InvoiceParty

### Kind

Value object.

### Meaning

Preserves supplier or buyer facts exactly as known from the invoice source or
later accepted correction.

### Candidate fields

- `name` optional;
- `tax_id` optional;
- `address` optional.

### Boundary

A party may later be linked to a Provider or Contact Card, but the source
invoice values remain independently preserved.

## InvoiceLine

### Kind

Entity inside Invoice Card, identified by `line_id` within the invoice.

### Meaning

Represents one factual invoice line. Its normalized structure is intentionally
comparable with a PresuPro estimate item while preserving original supplier
wording and monetary evidence.

### Candidate fields

- `line_id`;
- `kind`;
- `description_original`;
- `description_normalized` optional;
- `supplier_sku` optional;
- `matched_material_id` optional;
- `quantity`;
- `unit`;
- `unit_price_net`;
- `discount_percent`;
- `discount_amount`;
- `net_amount`;
- `tax_rate`;
- `tax_amount`;
- `gross_amount`.

### PresuPro alignment

Comparable meanings are intentionally aligned:

| PresuPro plan meaning | Invoice actual meaning |
| --- | --- |
| item type | `kind` |
| item name | `description_normalized` plus preserved original wording |
| material reference | optional `matched_material_id` |
| planned quantity | actual `quantity` |
| unit | `unit` |
| planned unit price | actual `unit_price_net` |
| planned discount | actual discount fields |
| planned IVA | actual tax fields |

This alignment does not make source names identical and does not let Cabinet
copy PresuPro planning values into Invoice Card facts.

## InvoiceTotals

### Kind

Value object.

### Candidate fields

- `net`;
- `discount`;
- `tax`;
- `gross`;
- `withholding`;
- `payable`.

## Payment

### Kind

Value object inside Invoice Card.

### Candidate fields

- `status`;
- `transactions`.

### Status vocabulary

- `unknown`;
- `unpaid`;
- `partially_paid`;
- `paid`;
- `refunded`.

Absence of evidence means `unknown`, not `unpaid`.

## PaymentTransaction

### Kind

Entity inside Payment, identified by `payment_id` within the invoice.

### Candidate fields

- `payment_id`;
- `method`;
- `paid_at` optional;
- `currency`;
- `tendered_amount` optional;
- `applied_amount`;
- `change_amount` optional;
- `reference` optional;
- `evidence`.

Several transactions may represent split settlement such as cash plus card.
There is no separate `mixed` payment method.

## PaymentEvidence

### Kind

Value object.

### Candidate fields

- `basis` — invoice source, user statement, or external record;
- `source_ref` optional.

## InvoiceObjectAssignment

### Kind

Cabinet-owned mutable decision associated with one Invoice Card.

### Meaning

Records the first-product primary Work Object assignment. Invoice Card identity
is independent from Work Object identity, so an invoice may exist without any
project assignment.

### State vocabulary

- `unreviewed`;
- `assigned`;
- `intentionally_unassigned`;
- `label_only`.

### Candidate fields

- `status`;
- `work_object_id` optional Registry project UUID;
- `label` optional;
- `decided_at` optional;
- `decided_by` optional;
- `invoice_revision`;
- `revision`.

### Baseline invariants

- `assigned` requires exactly one existing Work Object;
- `work_object_id` equals the Registry project UUID;
- non-assigned states have no confirmed Work Object ID;
- label-only evidence never creates a Work Object;
- one Invoice Card has at most one current primary Work Object assignment;
- reassignment preserves history;
- multi-object Invoice allocation is outside the baseline.

---

# D. PresuPro estimate projection

## EstimateReference

### Kind

External-reference value object.

### Meaning

Identifies the PresuPro estimate whose plan is used for one analysis or accepted
match.

### Candidate fields

- `estimate_id`;
- `project_id`;
- `estimate_updated_at`;
- `estimate_content_hash` or later stable version identity;
- optional `status`.

### Boundary

PresuPro owns estimate identity, mutable composition, and current values.
Cabinet must not call a mutable estimate approved merely because it exists.

## EstimateContext

### Kind

Typed external projection used for agent context and calculated analysis.

### Meaning

The detailed PresuPro plan loaded for the selected Registry project.

### Candidate fields

- `reference`;
- `currency`;
- `status`;
- `zones`;
- `totals`;
- `captured_at`.

### Persistence direction

The baseline does not require Cabinet to persist a complete permanent estimate
snapshot. Cabinet may load current plan data for analysis while pinning accepted
matches to an observed content hash or version. Offline plan-versus-actual
analysis may therefore be unavailable even while invoices and Work Object data
remain available.

## EstimateZoneReference

### Kind

External-reference value object.

### Candidate fields

- `zone_id` when PresuPro provides one;
- `zone_index` optional temporary locator;
- `zone_name`;
- `zone_fingerprint` optional.

Names and array indexes are not treated as stable identity unless PresuPro makes
that guarantee.

## EstimateItemReference

### Kind

External-reference value object.

### Candidate fields

- `estimate_id`;
- `estimate_content_hash` or version;
- `zone_reference`;
- `item_id` when available;
- `item_index` optional temporary locator;
- `item_fingerprint`;
- `display_name`.

`display_name` supports human and agent understanding but is not sufficient
identity.

## EstimateComparableItem

### Kind

Read-only external projection.

### Meaning

Contains the PresuPro fields useful for agent-assisted comparison with an
Invoice Line.

### Candidate fields

- `type`;
- `name`;
- `material_id` optional;
- `quantity`;
- `unit`;
- `unit_price`;
- `discount_percent`;
- `iva_percent`;
- `waste_percent`;
- `margin_percent`.

The projection may include additional source references and zone context, but
must not become an independently editable Cabinet plan.

## EstimateTotalsProjection

### Kind

Read-only external projection.

### Candidate fields

- materials subtotal;
- labor subtotal;
- margin total;
- discount total;
- taxable subtotal;
- IVA total and breakdown;
- grand total;
- currency.

Exact field vocabulary follows the confirmed PresuPro contract and may not be
invented in Cabinet.

---

# E. Agent-assisted plan-versus-actual matching

## EstimateMatchSuggestion

### Kind

Ephemeral or optionally persisted agent proposal.

### Meaning

Represents the agent's heuristic interpretation that one Invoice Line probably
corresponds to one PresuPro Estimate Item despite differences in shop,
manufacturer, SKU, language, or wording.

### Candidate fields

- `invoice_id`;
- `invoice_line_id`;
- `invoice_revision`;
- `estimate_item_reference`;
- `confidence` optional;
- `explanation` optional;
- `alternative_candidates` optional;
- `proposed_at`;
- `proposed_by`.

### Boundary

A suggestion is not accepted truth and does not participate in deterministic
plan-versus-actual calculations until confirmed.

## InvoiceLineEstimateMatch

### Kind

Cabinet-owned decision entity.

### Meaning

Persists an accepted, rejected, or invalidated relationship between one Invoice
Line and one PresuPro Estimate Item.

### Candidate fields

- `id`;
- `project_id`;
- `invoice_id`;
- `invoice_revision`;
- `invoice_line_id`;
- `estimate_reference`;
- `estimate_item_reference`;
- `status`;
- `proposal_confidence` optional;
- `proposal_explanation` optional;
- `proposed_by` optional;
- `confirmed_by` optional;
- `confirmed_at` optional;
- `invalidated_at` optional;
- `invalidation_reason` optional;
- `created_at`;
- `updated_at`;
- `revision`.

### Status vocabulary

- `confirmed`;
- `rejected`;
- `invalidated`.

The active calculation uses only `confirmed` matches.

### Baseline cardinality

For the first complete product:

- one Invoice Line has at most one active confirmed Estimate Item match;
- one Estimate Item may have many matched Invoice Lines from many invoices;
- partial distribution of one Invoice Line across several Estimate Items is
  deferred;
- multi-object allocation remains a separate deferred concern.

### Ownership

The agent proposes semantic equivalence. Cabinet owns acceptance, history,
referential consistency, and deterministic use of confirmed matches.

## MatchInvalidationReason

### Kind

Controlled vocabulary, to be finalized in State 2.

### Candidate values

- `invoice_changed`;
- `estimate_changed`;
- `estimate_item_missing`;
- `unit_changed`;
- `manual_rejection`;
- `project_mismatch`.

## UnitConversion

### Kind

Deferred value object.

### Baseline decision

The first complete product compares quantities only when units match. When
units differ, Cabinet may still compare monetary amounts but must report that
quantity analysis is unavailable. Explicit confirmed conversions may be added
later.

---

# F. Calculated plan-versus-actual views

## PlanActualAnalysis

### Kind

Calculated view, not an independently persisted source of truth.

### Meaning

Assembles current or pinned PresuPro plan data, confirmed Invoice Cards, and
confirmed matches into an on-demand analytical response for the user or agent.

### Candidate fields

- `project_id`;
- `estimate_reference`;
- `generated_at`;
- `coverage`;
- `items`;
- `totals`;
- `warnings`;
- `assumptions`.

## PlanActualItemView

### Kind

Calculated view.

### Candidate fields

- `estimate_item_reference`;
- `planned_quantity`;
- `planned_unit_price`;
- `planned_amount`;
- `actual_quantity` optional;
- `actual_average_unit_price` optional;
- `actual_amount`;
- `remaining_quantity` optional;
- `unit_price_variance` optional;
- `amount_variance`;
- `matched_invoice_lines`;
- `quantity_analysis_available`;
- `warnings`.

## PlanActualTotalsView

### Kind

Calculated view.

### Candidate fields

- `planned_amount`;
- `actual_amount`;
- `remaining_planned_amount` optional;
- `variance`;
- `matched_actual_amount`;
- `unmatched_invoice_amount`;
- `coverage_percent` optional.

## ForecastAssumption

### Kind

Calculated-view value object.

### Meaning

Makes a forward-looking projection explicit instead of presenting it as fact.

### Candidate fields

- `basis`;
- `description`;
- `price_basis`;
- `generated_at`.

### Candidate basis vocabulary

- `planned_price`;
- `latest_actual_price`;
- `average_actual_price`;
- `user_supplied_price`.

### Persistence boundary

Plan-versus-actual results and forecasts are normally recalculated on demand.
Cabinet persists source facts and accepted matches, not every analytical answer.

---

# G. Holded publication models

## HoldedPublication

### Kind

Cabinet-owned integration-operation entity.

### Meaning

Records the attempt to publish one exact confirmed Invoice Card revision to
Holded through Holded Gateway.

### Candidate fields

- `id`;
- `invoice_id`;
- `invoice_revision`;
- `status`;
- `idempotency_key`;
- `requested_at`;
- `completed_at` optional;
- `holded_document_id` optional;
- `gateway_receipt` optional;
- `last_error_code` optional;
- `last_error_message` optional safe diagnostic;
- `revision`.

### Status vocabulary

- `pending`;
- `succeeded`;
- `failed`;
- `ambiguous`;
- `cancelled`.

Absence of a publication record means publication was not requested; a
`not_requested` record is not required.

### Boundary

- one publication concerns one Invoice Card revision;
- publication does not alter source invoice facts;
- plan-versus-actual matching is independent from Holded publication;
- agent and Cabinet do not hold Holded credentials;
- Holded Gateway owns provider transport behavior, credentials, retries,
  reconciliation, and technical response decoding.

## HoldedPublicationReceipt

### Kind

Value object or referenced integration evidence.

### Candidate fields

- `gateway_operation_id`;
- `external_document_id` optional;
- `provider_status`;
- `received_at`;
- `safe_response_reference` optional.

Raw credentials, secrets, and unrestricted provider payloads are excluded.

---

# H. Remaining Cabinet Cards

## ProviderCard

### Kind

Entity and Card type.

### Meaning

Represents a supplier, shop, driver, delivery service, contractor, or other
working resource that may provide goods or services.

### Candidate fields

- `id`;
- `title`;
- `names`;
- `services`;
- `service_areas`;
- `contact_methods`;
- `communication_languages`;
- `notes`;
- `sources`;
- `status`;
- `created_at`;
- `updated_at`;
- `revision`.

Provider identity is not defined by a display name alone.

## ContactCard

### Kind

Entity and Card type.

### Meaning

Represents a customer, contractor, employee, professional, or other person or
organisation the user needs to contact.

### Candidate fields

- `id`;
- `display_name`;
- `kind`;
- `phones`;
- `emails`;
- `messaging_contacts`;
- `addresses`;
- `notes`;
- `sources`;
- `status`;
- `created_at`;
- `updated_at`;
- `revision`.

A later relationship may connect an InvoiceParty to a Contact or Provider Card
without replacing source invoice values.

## MaterialListCard

### Kind

Entity and Card type.

### Meaning

Represents a living shopping or material-requirement list maintained through
conversation and UI.

### Candidate fields

- `id`;
- `title`;
- `work_object_id` optional;
- `items`;
- `status`;
- `created_at`;
- `updated_at`;
- `revision`.

## MaterialListItem

### Kind

Entity inside Material List Card.

### Candidate fields

- `item_id`;
- `description`;
- `quantity` optional;
- `unit` optional;
- `status`;
- `notes` optional;
- `source` optional.

Exact item lifecycle belongs to State 2.

## DocumentCard

### Kind

Entity and Card type.

### Meaning

Represents a user-meaningful document that is not necessarily an Invoice Card.

### Candidate fields

- `id`;
- `document_kind`;
- `title`;
- `work_object_id` optional;
- `source`;
- `extracted_text` optional;
- `related_card_ids`;
- `status`;
- `created_at`;
- `updated_at`;
- `revision`.

Invoice Card remains a separate specialized Card rather than merely a generic
Document Card. Both may refer to original source evidence.

## ProjectNote

### Kind

Embedded Work Object entity in the baseline.

### Candidate fields

- `note_id`;
- `project_id`;
- `content`;
- `created_by`;
- `created_at`;
- `updated_at`.

A future product need may promote notes to standalone Cards, but that is not
required for the baseline.

---

# I. Relationship map

```text
Registry Project 1 <-> 0..1 persisted Cabinet Work Object

Work Object 1 <-> 0..* Invoice Cards through current primary assignment
Work Object 1 <-> 0..* Material List Cards
Work Object 1 <-> 0..* Document Cards
Work Object 1 <-> 0..* Contact and Provider relationships
Work Object 1 <-> 0..* Project Notes

Invoice Card 1 -> 1..* Invoice Lines
Invoice Card 1 -> 1 Invoice Object Assignment decision
Invoice Card 1 -> 1 Payment
Payment 1 -> 0..* Payment Transactions

Registry Project 1 -> 0..* PresuPro estimates externally
PresuPro Estimate 1 -> 0..* Estimate Zones
Estimate Zone 1 -> 0..* Estimate Items

Invoice Line 1 -> 0..1 active confirmed Estimate Match in the baseline
Estimate Item 1 -> 0..* confirmed matched Invoice Lines

Invoice Card 1 -> 0..* Holded Publication attempts
Invoice revision 1 -> 0..1 successful Holded publication unless correction
policy later allows another accounting action
```

The final Holded correction cardinality remains an open question.

---

# J. Lifecycle vocabulary summary

## Generic Card

- `active`;
- `archived`.

## Invoice Card

- `draft`;
- `confirmed`;
- `archived`.

## Invoice object assignment

- `unreviewed`;
- `assigned`;
- `intentionally_unassigned`;
- `label_only`.

## Estimate match

- `confirmed`;
- `rejected`;
- `invalidated`.

## Holded publication

- `pending`;
- `succeeded`;
- `failed`;
- `ambiguous`;
- `cancelled`.

## Registry synchronization

- `current`;
- `stale`;
- `unavailable`;
- `not_found`.

Transitions and terminal-state rules belong to State 2.

---

# K. Persisted versus calculated information

## Persisted Cabinet-owned or Cabinet-retained information

- Card identities, content, lifecycle, and revisions;
- Work Object relationships and history;
- Registry project snapshot and sync evidence;
- Invoice facts, payment evidence, source provenance, and assignment decisions;
- confirmed, rejected, and invalidated estimate-match decisions;
- exact references to the invoice and estimate revisions used by those
  decisions;
- Holded publication requests, statuses, and receipts;
- Provider, Contact, Material List, Document, and Project Note records.

## External current truth

- Registry current project context;
- PresuPro estimate composition, quantities, prices, margin, waste, IVA, and
  totals;
- Holded accounting document and accounting state.

## Calculated on demand

- total spending across invoices;
- actual quantity and actual amount for one estimate item;
- average actual unit price;
- remaining planned quantity;
- plan-versus-actual amount and price variance;
- matched and unmatched purchase coverage;
- project-level plan-versus-actual totals;
- forecast final cost under an explicit price assumption.

Calculated results do not become primary facts merely because an agent presents
them in conversation.

---

# L. Offline and degraded-operation model implications

When Registry is unavailable, Cabinet may use an existing Work Object and
Registry snapshot to continue basic Cabinet work.

When PresuPro is unavailable:

- stored Invoice Cards and accepted matches remain readable;
- Cabinet may report previously accepted match references;
- fresh plan-versus-actual analysis requiring current estimate data may be
  unavailable;
- Cabinet must not fabricate plan values from invoice data.

When Holded or Holded Gateway is unavailable:

- Invoice Card capture, confirmation, matching, and analysis remain usable;
- publication state records the failure or ambiguity;
- source Invoice Cards remain unchanged.

---

# M. State 1 closure questions

State 1 remains open until the following questions are answered or explicitly
accepted as deferred:

1. How does Cabinet obtain the relevant PresuPro estimate for a Registry
   `project_id`: direct PresuPro lookup, Registry artifact discovery, or another
   agreed boundary?
2. Does PresuPro already provide a reliable way to select one current estimate
   for a project, and what happens when several estimates exist?
3. Does Cabinet persist a full observed estimate snapshot, a compact projection,
   or only an `EstimateReference` with content hash/version?
4. Which stable identifiers currently exist for PresuPro zones and estimate
   items? If they do not exist, what fingerprint and invalidation evidence is
   sufficient for the baseline?
5. Is one Invoice Line to at most one Estimate Item the accepted first-product
   limit?
6. Is a rejected match a durable decision record, or may rejection live only in
   general decision history?
7. Who may confirm an estimate match: user only, user plus trusted agent, or
   another authorized actor?
8. Which invoice or estimate changes automatically invalidate a confirmed
   match?
9. How is a corrected Invoice Card handled after a successful Holded
   publication: correction document, replacement, cancellation and republish,
   or a separate workflow owned by Holded policy?
10. Which Provider, Contact, Material List, Document, and Project Note fields
    are mandatory for the first PostgreSQL-backed Cabinet release?
11. What freshness policy changes Registry sync from `current` to `stale`?
12. Does Cabinet retain historical Registry snapshots or only the current
    snapshot plus audit evidence?
13. Which historical Cabinet corrections remain allowed after Registry project
    archival?
14. Which source binaries are stored by Cabinet, and which storage service owns
    them?
15. What is the precise meaning of partial refund under the current
    `refunded` payment vocabulary?

Once the model questions are resolved, State 2 will define invariants,
transitions, calculation semantics, invalidation rules, and policy tables.
