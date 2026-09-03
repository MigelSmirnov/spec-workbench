# State 1 — Existing Cabinet-owned data models

## Model M05 — CardSource

### Meaning

One logical original source associated with an owning Cabinet Card. Source
identity exists even while original bytes are unavailable.

Candidate fields common to accepted Card formats:

- owning `card_id`;
- `source_id`, stable within the owning Card;
- `kind` or `media_type` when known;
- `file_status`: stored, pending, or truthfully unavailable according to the
  owning Card contract;
- storage reference optional;
- origin context such as platform, author, publication, URL, capture time, or
  note when the owning Card type accepts it.

### Identity

entity

### Identity evidence

Substitution: sources with different owning Card/source ID pairs are not
interchangeable even if their metadata is equal. Continuity: the same source
keeps its identity when bytes arrive later or storage metadata changes.

### Source of truth

The source reference inside the owning canonical Card.

### Lifecycle candidate

`identified -> bytes_pending | bytes_stored`; later availability changes do
not replace identity. Exact allowed states remain type-specific until State 2.

### Persistence candidate

Durable as part of the owning Card; server custody is separately modeled by
M14.

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

Candidate fields are the complete accepted Invoice Card V1 contract:

- `card_type = invoice`, `card_version = 1`, stable `id`, and status;
- invoice dates/number and currency;
- supplier and buyer parties;
- required object block with optional Card ID and label;
- stable line IDs, source/original descriptions, classifications, quantities,
  decimal monetary and tax facts;
- deterministic totals;
- explicit payment status and transactions;
- exactly one stable source block;
- creation and confirmation provenance.

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


## Model M128 — InvoiceParty

Fields: `name: str`, `tax_id: str | None`, `email: str | None`, `phone: str | None`, `address: str | None`.

### Identity

value

### Identity evidence

Equal typed party facts are interchangeable. The party form was previously an
open string dictionary; its field names lived in prose and in dotted rule
paths (`supplier.tax_id`), which the type could not honour.

## Model M129 — InvoiceTotals

Fields: `net_total: Decimal`, `tax_total: Decimal`, `gross_total: Decimal`.

### Identity

value

### Identity evidence

Equal typed monetary totals are interchangeable; `totals.gross_total` is a
declared field, not a dictionary key named in prose.

## Model M130 — InvoiceObjectContext

Fields: `object_card_id: str | None`, `label: str | None`.

### Identity

value

### Identity evidence

Equal typed object-context facts are interchangeable; the object block is the
declared optional Card binding and label, not an open dictionary.
