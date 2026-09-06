# State 1 — Existing Cabinet-owned data models

## Model M05 — CardSource

### Meaning

One logical original source associated with an owning Provider, Client, or
Project Card. Source identity exists even while original bytes are unavailable.

Scope corrected 2026-09-05 by D0-010: the Invoice Card does not use this
shape; it carries the product `InvoiceCardSourceBlock` (`source_id`, `kind`,
opaque `file_ref`, `file_status`, `note`). Exact custody states and storage
confirmations for every card live separately by `source_id` in M14
`SourceCustodyRecord`.

Fields: owning `card_id`; `source_id`, stable within the owning Card;
`media_type` when known; `file_status`: stored, pending, or truthfully
unavailable according to the source-file vocabulary; `storage_reference`,
present only when Cabinet Web itself holds the bytes; `origin_context`, a
string map naming where the source came from.

### Identity

entity

### Identity evidence

Substitution: the pair (`card_id`, `source_id`) names one logical source across
custody states. Continuity: the same pair survives byte arrival, verification,
and durable storage.

### Source of truth

Owned by Cabinet Web inside the owning Card.

### Lifecycle candidate

Follows the owning Card.

### Persistence candidate

Master data embedded in the owning Card record.

### Open questions

None.

## Model M06 — SourceContentReference

### Meaning

An immutable description of exact source bytes without exposing a storage path
or granting retrieval authority.

Candidate fields:

- owning `card_id` and `source_id`;
- `content_hash`;
- `size_bytes`;
- accepted `media_type`;
- original display filename optional.

### Identity

value

### Identity evidence

Substitution: equal owner, source, hash, size, media type, and display filename
facts describe the same exact bytes. Continuity: changed bytes create another
value rather than mutating this reference.

### Source of truth

Derived by Cabinet Web from bytes it has actually accepted into custody.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Embedded in custody, transfer, and acknowledgement evidence.

### Open questions

None.

## Model M07 — ProviderCard

### Meaning

The existing independent Cabinet working object for a person, organisation, or
not-yet-classified provider offering services. Drivers, carriers, workers, and
shops remain Provider Cards.

Candidate fields preserved from Cabinet_web:

- stable `id`, type `provider`, non-unique `title`, and lifecycle `status`;
- contacts with kind, display value, normalized value, and source reference;
- offered services and service areas;
- communication languages with evidence basis;
- user notes and sources.

### Identity

entity

### Identity evidence

Substitution: equal contact or service facts do not make two Provider Card IDs
interchangeable. Continuity: one Provider Card is enriched, corrected, and
archived without changing its stable ID.

### Source of truth

The canonical Cabinet Provider Card.

### Lifecycle candidate

Existing active/archived Card lifecycle; enrichment creates a new content
revision of the same Card.

### Persistence candidate

Durable canonical Card with rebuildable search/catalogue projections.

### Open questions

None.

## Model M08 — ClientCard

### Meaning

The existing independent Cabinet working object for one client and its known
contact and project relationships.

Candidate fields preserved from Cabinet_web:

- stable `id`, type `client`, title, status;
- tax ID and country when known;
- direct contacts and contact people;
- stable related `project_ids`;
- notes and sources.

### Identity

entity

### Identity evidence

Substitution: equal names or contacts do not make different Client Card IDs
interchangeable. Continuity: one client remains the same working object while
contacts, projects, notes, and status change.

### Source of truth

The canonical Cabinet Client Card.

### Lifecycle candidate

Existing Card lifecycle with revision history; archiving does not delete
history.

### Persistence candidate

Durable canonical Card.

### Open questions

None.

## Model M09 — ProjectCard

### Meaning

The existing independent Cabinet working object for one job/object, distinct
from a Registry project snapshot and from the local Backend's operational
records.

Candidate fields preserved from Cabinet_web:

- stable `id`, type `project`, title, status, and `client_id`;
- contact people, object name/address, currency, and scope;
- accepted estimate facts;
- financial invoice and payment facts;
- procurement estimate items and actual purchases;
- shopping-list references;
- notes, sources, and rebuildable analytics inputs.

### Identity

entity

### Identity evidence

Substitution: equal object labels or financial totals do not make different
Project Card IDs interchangeable. Continuity: the same project remains the
same Cabinet working object while estimates, payments, purchases, lists, and
status change through accepted revisions.

### Source of truth

The canonical Cabinet Project Card owns Cabinet project facts. Registry remains
authoritative only for separate M17 Registry project snapshots.

### Lifecycle candidate

Existing Card lifecycle with revision history. Estimate replacement and
project archiving do not rewrite prior source evidence.

### Persistence candidate

Durable canonical Card; summaries are rebuildable projections.

### Open questions

None.

## Model M10 — InvoiceCardV1

### Meaning

The implemented Cabinet Invoice Card V1 containing one invoice's confirmed or
draft supplier facts, lines, totals, payment evidence, object context, source,
and provenance.

Fields are exactly the product contract `schemas/invoice-card-v1.schema.json`
(`LIVE_PRODUCT_EVIDENCE_20260905_c897897.md`, D0-010), carried without loss:

`card_type: str`, `card_version: int`, `id: str`, `status: str`,
`invoice_number: str | None`, `issue_date: date | None`,
`service_date: date | None`, `due_date: date | None`, `currency: str`,
`supplier: InvoiceCardParty`, `buyer: InvoiceCardParty`,
`object: InvoiceCardObjectBlock`, `lines: tuple[InvoiceCardLine, ...]`,
`totals: InvoiceCardTotals`, `payment: InvoiceCardPayment`,
`source: InvoiceCardSourceBlock`, `provenance: InvoiceCardProvenance`.

`status` is one M141 `InvoiceLifecycleState` member. No reduced Invoice form
exists beside this one; the former M128–M130, M31 and M05 shapes are retired.

### Identity

entity

### Identity evidence

Substitution: two Invoice Cards are not interchangeable when their stable IDs
or canonical revisions differ even if visible invoice facts match. Continuity:
one Invoice keeps its ID while draft content, confirmation, correction
revisions, payment evidence, source availability, and archive status change.

### Source of truth

The canonical Cabinet Invoice Card V1 and its accepted validator. Cabinet Web
owns the Card; local `cabinet_backend` is a preserving consumer.

### Lifecycle candidate

`draft -> confirmed -> archived`; confirmed corrections require an explicit
revision workflow rather than an in-place draft update.

### Persistence candidate

Durable complete canonical revisions. Transfer and local acceptance evidence
do not become fields of this Card.

### Open questions

None.

## Model M11 — AcceptedEstimateSnapshot

### Meaning

The exact accepted commercial estimate embedded in a Project Card, preserving
planned scope, section lines, totals, status, identity, version, and issue
times independently from invoices and payments.

### Identity

entity

### Identity evidence

Substitution: estimates with different accepted estimate identities or
versions are not interchangeable even when totals match. Continuity: one
estimate identity may progress to an accepted version; replacement evidence is
preserved rather than rewriting the earlier issued snapshot.

### Source of truth

The owning Project Card's accepted estimate facts and accepted estimate input
contract.

### Lifecycle candidate

Prepared/accepted according to the existing estimate status; an accepted
issued version is immutable and replacement creates a later version or
identity.

### Persistence candidate

Durable within the Project Card; validation and summaries are calculated.

### Open questions

None.

## Model M12 — ShoppingListSnapshot

### Meaning

One versioned, issued procurement list derived from an exact accepted estimate
for one Project Card.

Candidate fields preserved from the existing artifact:

- stable list `id`, `version`, `project_id`, and `estimate_id`;
- status, currency, creation time, and source status;
- ordered items with stable estimate-item relationship and planned facts;
- net, tax, and gross totals.

### Identity

entity

### Identity evidence

Substitution: list IDs and versions distinguish issued procurement snapshots
even when their current items are equal. Continuity: one issued list version
remains fixed; regeneration from changed estimate facts creates a later
version, not silent mutation.

### Source of truth

Cabinet Web issues the snapshot from the exact accepted estimate revision.

### Lifecycle candidate

Issued versioned snapshot with its existing status; a later version supersedes
but does not rewrite it.

### Persistence candidate

Durable project-owned artifact; HTML is a rebuildable projection.

### Open questions

None.

## Model M13 — ProjectInvoiceLink

### Meaning

The accepted separate artifact that links one Invoice Card and its individual
lines to one Project Card and estimate items without rewriting either source
Card.

Candidate fields follow the accepted schema:

- stable link identity and schema version;
- exact Project and Invoice Card identities/revisions;
- line-level match decisions such as exact, accepted substitute, manual,
  unmatched, or ambiguous;
- referenced estimate item identities and decision provenance.

### Identity

entity

### Identity evidence

Substitution: different link IDs or pinned Card revisions represent distinct
matching evidence even when mappings look equal. Continuity: one link remains
the review subject while explicit matching decisions are added or revised with
history.

### Source of truth

Cabinet Web owns an accepted link artifact when one is created; Invoice Card
facts and Project estimate facts remain authoritative in their own Cards.

### Lifecycle candidate

Reviewable mapping evidence; ambiguous and unmatched lines remain explicit.
Exact transition policy belongs to State 2.

### Persistence candidate

Durable separate artifact when instantiated; analytics are calculated from it.

### Open questions

None for identity closure.


## Retirement record M128 — InvoiceParty (retired 2026-09-05)

Retired by D0-010: the product Invoice contract carries typed sub-blocks
(`InvoiceCardParty`, `InvoiceCardTotals`, `InvoiceCardObjectBlock`); no
competing reduced form remains.


## Retirement record M129 — InvoiceTotals (retired 2026-09-05)

Retired by D0-010: the product Invoice contract carries typed sub-blocks
(`InvoiceCardParty`, `InvoiceCardTotals`, `InvoiceCardObjectBlock`); no
competing reduced form remains.


## Retirement record M130 — InvoiceObjectContext (retired 2026-09-05)

Retired by D0-010: the product Invoice contract carries typed sub-blocks
(`InvoiceCardParty`, `InvoiceCardTotals`, `InvoiceCardObjectBlock`); no
competing reduced form remains.

## Model M165 — InvoiceCardParty

Fields: `name: str | None`, `tax_id: str | None`, `address: str | None`.

### Identity

value

### Identity evidence

Equal typed party facts are interchangeable. Reciprocal with the product
schema `party` and the accepted `cabinet_backend` boundary model.

## Model M166 — InvoiceCardObjectBlock

Fields: `card_id: str | None`, `label: str | None`.

### Identity

value

### Identity evidence

Equal typed object-assignment facts are interchangeable; an unassigned
Invoice carries both null (product warning `invoice_object_unassigned`).

## Model M167 — InvoiceCardTotals

Fields: `net: Decimal`, `discount: Decimal`, `tax: Decimal`, `gross: Decimal`,
`withholding: Decimal`, `payable: Decimal`.

### Identity

value

### Identity evidence

Equal typed monetary totals are interchangeable; `payable = gross -
withholding` is a hard product check, `net`/`tax` versus line sums a warning.

## Model M168 — InvoiceCardPaymentEvidence

Fields: `basis: str`, `source_ref: str | None`.

### Identity

value

### Identity evidence

Equal typed evidence facts are interchangeable; `basis` is one M176
`PaymentEvidenceBasis` member.

## Model M169 — InvoiceCardPaymentTransaction

Fields: `payment_id: str`, `method: str`, `paid_at: datetime | None`,
`currency: str`, `tendered_amount: Decimal | None`, `applied_amount: Decimal`,
`change_amount: Decimal | None`, `reference: str | None`,
`evidence: InvoiceCardPaymentEvidence`.

### Identity

value

### Identity evidence

Equal typed transaction facts are interchangeable within one Card;
`payment_id` is unique within the Card, `method` is one M175
`InvoicePaymentMethod` member, `currency` equals the Card currency.

## Model M170 — InvoiceCardPayment

Fields: `status: str`, `transactions: tuple[InvoiceCardPaymentTransaction, ...]`.

### Identity

value

### Identity evidence

Equal typed payment facts are interchangeable; `status` is one M174
`InvoicePaymentStatus` member and its consistency with the applied sum is a
hard product check.

## Model M171 — InvoiceCardSourceBlock

Fields: `source_id: str`, `kind: str`, `file_ref: str | None`,
`file_status: str`, `note: str | None`.

### Identity

value

### Identity evidence

Equal typed source facts are interchangeable; `source_id` is the source
identity, `kind` one M177 `InvoiceSourceKind` member, `file_status` one M178
`InvoiceSourceFileStatus` member, `file_ref` an opaque source reference —
never a GitHub, Syncthing or filesystem path (D0-010).

## Model M172 — InvoiceCardProvenance

Fields: `created_at: datetime`, `confirmed_at: datetime | None`, `created_by: str`.

### Identity

value

### Identity evidence

Equal typed provenance facts are interchangeable; `created_by` is one M179
`ProvenanceCreator` member.
