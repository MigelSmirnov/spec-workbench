# State 2 — Cabinet Backend rules and invariants

## Status

Working rules baseline. Decisions are added one at a time and become normative
only when explicitly accepted here.

This state defines deterministic validation, acceptance, transition, and
reconciliation semantics for the domain models in `01_models.md`. It does not
introduce speculative compatibility, placeholder policies, APIs, SQL tables, ORM
mappings, or transport payloads.

---

# A. Invoice Card contract acceptance

## Accepted decision A1 — supported Card contract

Cabinet Backend supports exactly the currently accepted Cabinet Invoice Card V1
contract.

There are no other accepted Invoice Card contract versions at this time.
Backend therefore must not implement speculative multi-version negotiation,
implicit migration, best-effort interpretation, or forward compatibility with an
unknown Card contract.

### Normative rules

1. An incoming Invoice Card is eligible for validation only when its declared
   `card_type` and `card_version` identify the currently accepted Invoice Card V1
   contract.
2. Backend validates the complete canonical Card payload with the currently
   accepted Invoice Card V1 validator or a proven contract-equivalent
   implementation.
3. A Card declaring any other version is not accepted as an Invoice Card V1 and
   receives the deterministic result `unsupported_card_version`.
4. Backend must preserve the rejected payload and safe rejection evidence when it
   arrived through a synchronization or import boundary, but it must not publish
   that payload into the accepted Card archive.
5. Backend must not rewrite, downgrade, partially interpret, or silently discard
   fields in order to make an unsupported Card appear compatible.
6. Support for any future Card version requires a separate accepted specification
   change that defines its validator, compatibility boundary, migration behavior,
   and relationship to stored V1 revisions.

### Formal invariants

For every `StoredInvoiceCardRevision` in the accepted archive:

```text
revision.card_type = accepted_invoice_card_type
revision.card_version = accepted_invoice_card_v1_version
```

For every `InvoiceCardValidationRecord` with result `valid` or
`valid_with_warnings`:

```text
validation.validator_contract = accepted_invoice_card_v1_contract
validation.validator_version = accepted_invoice_card_v1_validator_version
```

An unsupported declared Card version may produce import rejection or quarantine
evidence, but it cannot create or replace:

- `StoredInvoiceCard`;
- `StoredInvoiceCardRevision`;
- `current_content_hash`;
- an accepted `InvoiceWorkingReplica` entry.

### Required tests

1. A valid Invoice Card V1 is evaluated by the accepted V1 validator.
2. A payload declaring an unknown Card version returns
   `unsupported_card_version`.
3. An unknown version does not create an accepted Card revision.
4. An unknown version is not silently interpreted as V1 even when its fields look
   similar to V1.
5. Repeating the same unsupported payload preserves deterministic rejection
   semantics and does not create duplicate accepted records.

### Consequence

Version negotiation is not a runtime product feature in the current baseline.
The supported contract changes only through an explicit specification and
implementation update.

---

## Accepted decision A2 — only finished Cards enter Local Backend

Invoice capture, OCR, model extraction, poor-photo handling, re-photographing,
field completion, and user correction belong to the continuously available
Cabinet workspace on the VPS.

Local Cabinet Backend is not a workspace for incomplete recognition attempts. It
receives the finished Invoice Card only after Cabinet has completed the working
cycle and marked the Card `confirmed`.

### Normative rules

1. VPS Cabinet may create and retain `draft` Invoice Card revisions while the
   document is being recognised, corrected, or completed.
2. A poor photograph, failed extraction, missing field, replacement photograph,
   or unfinished user review must be resolved in VPS Cabinet before normal
   synchronization to Local Backend.
3. Normal Backend import accepts only Invoice Card V1 revisions whose Card
   lifecycle status is `confirmed`.
4. A `draft` Card received at the import boundary is rejected with the
   deterministic result `card_not_confirmed`.
5. Rejecting a `draft` import must not create or replace a
   `StoredInvoiceCardRevision`, change `current_content_hash`, or make the Card
   visible in the durable archive.
6. Backend does not reconstruct OCR sessions, intermediate model outputs, or
   abandoned correction attempts from the VPS working process.
7. Source artifacts belonging to the final confirmed Card are transferred under
   the source-package rules defined separately in this state.
8. Later correction of an already accepted invoice is represented by a new
   `confirmed` Card content revision, not by importing an intermediate `draft`.

### Formal invariants

For every `StoredInvoiceCardRevision` in the accepted Local Backend archive:

```text
revision.observed_status = confirmed
```

For every `InvoiceImport` with status `accepted` or `already_accepted`:

```text
all imported Card revisions have status = confirmed
```

A Card revision with status `draft` cannot create or replace:

- `StoredInvoiceCard`;
- `StoredInvoiceCardRevision`;
- `current_content_hash`;
- an accepted `InvoiceWorkingReplica` entry;
- PresuPro matching input;
- PlanActualAnalysis input;
- Holded publication eligibility.

### Required tests

1. A valid confirmed Invoice Card V1 may proceed to normal Backend validation.
2. A valid but `draft` Invoice Card V1 returns `card_not_confirmed`.
3. A rejected draft does not appear in durable archive queries.
4. Re-photographing and repeated extraction on the VPS do not create Backend Card
   revisions until a confirmed Card is synchronized.
5. A later corrected and confirmed payload for an existing `invoice_id` is
   evaluated as a new Card content revision.

### Consequence

`draft` remains a VPS Cabinet working lifecycle state. It is not a durable Local
Backend business state in the current baseline.

---

## Accepted decision A3 — intentional Card acceptance without source bytes

A confirmed Invoice Card may be accepted into Local Backend even when one or more
referenced photographs or PDFs are not included in the import. This is allowed
only as an explicit, auditable decision. Missing bytes must never be treated as
successful transfer by accident.

This capability supports recovery and local operation when the VPS application or
its working storage is unavailable, while the application source code remains
recoverable from GitHub. A source file may later be attached directly to the
local Backend by an authorised agent or by a minimal local HTML upload surface.

### Normative rules

1. Normal synchronization expects every source artifact declared as stored and
   available by the confirmed Card to be included and hash-verifiable.
2. If expected source bytes are missing, the Card is not accepted by default.
3. Acceptance without those bytes requires an explicit request flag:

   ```text
   accept_without_source_bytes = true
   ```

4. The explicit request must record an `ActorReference`, decision time, reason,
   and the exact Card revision and missing source references covered by the
   decision.
5. Acceptance with missing bytes creates the Card revision in the accepted
   archive but records each absent source as `SourceBinary.byte_status = missing`.
6. Such acceptance does not claim that the source package is complete or durable.
   Card acceptance and source completeness are separate facts.
7. A source whose Card contract explicitly declares that bytes were not stored
   does not require the override flag. Its absence is intentional contract data,
   not a transfer failure.
8. A declared content hash mismatch, corrupt upload, or attachment to the wrong
   invoice cannot be overridden by `accept_without_source_bytes`.
9. Source bytes may be attached later through an authorised local operation used
   by either an agent tool or a minimal HTML uploader.
10. Later attachment creates or completes `SourceBinary` and
    `SourceBinaryReplica` records. It does not rewrite the immutable accepted Card
    payload.
11. The attachment operation must calculate the binary hash, verify it against
    the expected Card source hash when one exists, and preserve actor, time,
    filename, media type, and attachment provenance.
12. If the Card contains no expected hash, the locally calculated hash becomes
    storage evidence but not retroactive Card content. Updating Card source
    metadata requires a new confirmed Card revision.

### Invoice resolution for local attachment

The canonical target of an attachment is `invoice_id`, optionally narrowed by an
expected Card revision hash and `source_id`.

Human and agent workflows may search by invoice number, but invoice number is not
a unique identifier and must not be used as the final mutation key.

A search result should expose enough context to choose safely, including where
available:

- `invoice_id`;
- invoice number;
- supplier name or tax identifier;
- invoice date;
- total amount and currency;
- current Card revision hash;
- existing and missing source references.

The attachment action may proceed only after the search resolves to exactly one
selected `invoice_id`. Multiple candidates require explicit selection. No match
must return a not-found result rather than creating an unrelated invoice.

### Formal invariants

For every accepted Card revision with missing expected source bytes:

```text
explicit_missing_source_acceptance exists
and explicit_missing_source_acceptance.invoice_id = revision.invoice_id
and explicit_missing_source_acceptance.content_hash = revision.content_hash
```

For every source replica marked `verified`:

```text
replica.stored_hash = SHA256(stored_bytes)
```

When the Card declares an expected source hash:

```text
replica.verification_status = verified
only if replica.stored_hash = expected_source_hash
```

An attachment mutation must target one stable logical invoice:

```text
attachment.target_invoice_id = StoredInvoiceCard.invoice_id
```

Invoice number alone cannot satisfy that invariant.

### Required tests

1. A confirmed Card with all required source bytes is accepted without an
   override.
2. A confirmed Card missing expected bytes is rejected or quarantined when the
   explicit flag is absent.
3. The same Card may be accepted when the explicit flag is present and complete
   decision evidence is recorded.
4. Acceptance with missing bytes does not mark the source package complete.
5. A later local upload with the expected hash changes the source from `missing`
   to available with a verified local replica.
6. A later upload with a different hash is rejected and does not replace expected
   source evidence.
7. Search by a unique invoice number may resolve to one `invoice_id` and allow
   attachment after explicit selection.
8. Search returning several invoices with the same number requires disambiguation
   and performs no mutation before selection.
9. Direct attachment by `invoice_id` does not depend on invoice-number uniqueness.
10. Retrying the same file attachment is idempotent by invoice, source identity,
    and binary hash.

### Consequence

Local Backend may preserve a finished invoice before its source bytes are
available, but incompleteness is visible and intentional. Recovery does not rely
on GitHub storing invoice photographs: files can be supplied later through a
narrow local attachment capability.

---

# B. Invoice Card follow-up rules

## Accepted decision A4 — semantic duplicate detection belongs to Cabinet

Semantic duplicate detection is owned by the Cabinet web application during the
interactive user workflow. Cabinet Backend does not repeat heuristic duplicate
search by supplier, invoice number, date, amount, line similarity, OCR text, or
other business signals.

### Normative rules

1. Cabinet resolves suspected semantic duplicates before publishing a confirmed
   Invoice Card for synchronization.
2. Cabinet Backend protects against technical duplication only:
   - repeated delivery of the same transfer manifest;
   - repeated import of the same Card content revision;
   - repeated attachment of the same source binary.
3. Repeating the same immutable payload must be idempotent and must not create a
   second logical invoice, revision, import, or source replica.
4. A new confirmed content revision for an existing `invoice_id` is a normal Card
   revision and is not a duplicate invoice.
5. If two accepted Invoice Cards are later discovered to describe the same real
   invoice, resolution requires an explicit human decision.
6. Cabinet Backend must not automatically merge, delete, or rewrite either Card.
7. A manual duplicate resolution may link the records and exclude one from chosen
   downstream views, but both accepted histories and their evidence remain
   auditable.

### Required tests

1. Repeating one manifest does not create a second import.
2. Repeating one Card content hash does not create a second revision.
3. Reattaching identical bytes to the same source target is idempotent.
4. A different confirmed content hash for the same `invoice_id` is accepted as a
   revision rather than classified as a duplicate.
5. Two different invoice IDs are never merged automatically by Backend.

### Consequence

Cabinet owns semantic understanding; Cabinet Backend owns deterministic identity,
idempotency, persistence, and audit.

---

## Accepted decision A5 — Backend project assignment decisions do not edit Invoice Card

A local project reassignment or resolution is Backend-owned operational evidence.
It does not modify the immutable Invoice Card payload received from Cabinet.

### Normative rules

1. Cabinet Backend never edits the stored Card `object` block.
2. A local assignment decision references:
   - the exact Invoice Card revision;
   - the selected Registry `project_id`;
   - the previous unresolved or conflicting context;
   - the deciding actor;
   - decision time;
   - reason or evidence.
3. Replacing a local assignment creates a new auditable decision or supersedes the
   previous decision explicitly; history is not overwritten silently.
4. The effective Backend assignment may be used for local analytics and eligible
   integrations while the original Card remains unchanged.
5. If Cabinet later issues a new confirmed Card revision with corrected object
   data, Backend stores that revision normally and reconciles the separate local
   decision without rewriting either history.
6. Backend must not synthesize and publish a modified Card revision on Cabinet's
   behalf.

### Formal invariant

```text
stored_card_payload_after_acceptance = stored_card_payload_at_acceptance
```

Backend-owned decisions may change effective operational interpretation but not
Card bytes or content hash.

### Required tests

1. Adding a local project assignment leaves the Card payload and content hash
   unchanged.
2. Changing an assignment preserves the previous decision history.
3. A later corrected Cabinet revision is stored as a new revision.
4. Removing a local decision restores unresolved interpretation without mutating
   the Card.

---

## Accepted decision A6 — initial Cabinet Card scope is Invoice Card V1 only

The first Cabinet Backend implementation supports exactly one Cabinet Card type:

```text
Invoice Card V1
```

No other Cabinet Card type is included in the initial offline, synchronization,
durability, or local-processing scope.

---

### Normative rules

1. Cabinet Backend accepts only the currently accepted `Invoice Card V1`
   contract.
2. Other Cabinet Card types must not be interpreted as Invoice Cards.
3. Unsupported Card types must not create partial local records.
4. Unsupported Card types must not enter the durable Cabinet Backend archive.
5. Unsupported Card types must not be included in normal synchronization
   packages for the first implementation.
6. Cabinet Backend must not invent replacement schemas for unsupported Card
   types.
7. Cabinet Backend must not infer lifecycle, identity, revision, attachment, or
   synchronization semantics for unsupported Card types.
8. Support for an additional Card type requires a separate accepted contract.
9. Adding one Card type does not implicitly add related Card types.
10. The absence of local Backend support does not prevent Cabinet from using those
    Card types inside the VPS application.

---

### Explicitly out of scope

The following candidate Card types are not supported by the first Cabinet Backend
implementation:

```text
ProviderCard
ContactCard
MaterialListCard
MaterialListItem
DocumentCard
project-linked notes
project-linked relationships
```

This list is descriptive, not exhaustive.

Any Cabinet Card type other than `Invoice Card V1` is unsupported until
separately accepted.

---

### Unsupported Card behavior

When synchronization encounters an unsupported Card type, Backend must produce a
deterministic result such as:

```text
unsupported_card_type
```

The result must preserve enough safe evidence to diagnose the synchronization
attempt, including where available:

```text
declared_card_type
declared_card_version
source_package_id
observed_at
```

The unsupported payload must not be silently discarded when it arrived through
an auditable synchronization boundary, but it must not be promoted into the
accepted Card archive.

---

### Requirements for adding a Card type

A new Cabinet Card type may enter Backend scope only after its accepted contract
defines:

1. canonical schema;
2. validator;
3. stable logical identity;
4. immutable revision identity;
5. draft and confirmed lifecycle;
6. source-file semantics;
7. synchronization eligibility;
8. local durability requirements;
9. conflict and retry behavior;
10. dependencies on Registry, PresuPro, Holded, or Client Portal;
11. required authorization;
12. required tests and deterministic rejection behavior.

A field resemblance to an existing Card is not sufficient.

---

### Synchronization package rule

The first synchronization package may contain:

```text
Invoice Card V1 revisions
their accepted source-package evidence
related technical synchronization metadata
```

It must not include unsupported Cabinet Card payloads as accepted business
records.

A future synchronization package version may extend the supported type set only
through a separate accepted decision.

---

### Formal invariants

Supported type set:

```text
supported_card_types = { Invoice Card V1 }
```

Acceptance:

```text
card_type != Invoice Card V1
-> unsupported_card_type
```

No speculative model:

```text
unsupported Card type
-> no accepted local domain record
```

Scope extension:

```text
new Card support
-> separate accepted contract and tests
```

---

### Required tests

1. A valid confirmed Invoice Card V1 enters normal Backend validation.
2. An unknown Card type returns `unsupported_card_type`.
3. A known but unsupported Cabinet Card type returns
   `unsupported_card_type`.
4. An unsupported Card does not create an accepted local business record.
5. An unsupported Card does not alter an existing Invoice Card.
6. Diagnostic evidence preserves the declared type and version.
7. Similar fields do not cause an unsupported Card to be interpreted as an
   Invoice Card.
8. Synchronization remains deterministic when the same unsupported payload is
   observed repeatedly.

### Consequence

The first Cabinet Backend implementation remains focused on one complete,
verified business flow rather than partially supporting several undefined Card
types.

Cabinet may continue using additional Card types on the VPS without implying
local Backend support.

---

# C. Source package semantics

## Accepted decision A12 — one logical source package per Invoice Card

One Invoice Card is associated with one logical `SourcePackage`. The package may
contain one or many files that together represent the original evidence used to
produce or support the Card.

### Normative rules

1. A source package may contain one photograph, several ordered photographs, a
   PDF, or a combination of source files.
2. Several photographs of a long receipt or invoice are parts of one logical
   source package, not separate invoices.
3. Cabinet produces one confirmed Invoice Card from the complete working source
   package.
4. Cabinet Backend preserves the declared file identities and display order.
5. The package is complete only when all expected parts are available and verified
   locally, except parts explicitly declared as not stored by the Card contract.
6. Missing one expected part makes the source package incomplete without deleting
   or invalidating the accepted Card.
7. Additional supporting originals may be attached later, including a PDF found
   after photographs were synchronized.
8. A late attachment records actor, time, origin, filename, media type, calculated
   hash, and whether it fills an expected missing part or adds supplementary
   evidence.
9. Adding source bytes never rewrites the immutable accepted Invoice Card.
10. If source metadata inside the Card must change, Cabinet must produce a new
    confirmed Card revision.

### Required tests

1. Three ordered photographs can form one complete source package.
2. Absence of one declared photograph produces an incomplete package.
3. Adding the missing verified photograph completes the package.
4. Adding a later PDF preserves the original photographs and provenance.
5. Repeating an identical attachment does not create a duplicate binary record.

---

## Accepted decision A13 — partial source package handling

This decision refines A3. It defines business acceptance semantics only.
Temporary storage, upload chunking, retry intervals, timeout handling, and other
transport details remain implementation concerns.

A confirmed Invoice Card and its source files do not have to become visible in
the durable archive as one indivisible transaction.

If one or more expected source files fail to arrive or fail verification, the
default result is an incomplete source package. The missing or invalid file must
not be represented as successfully stored.

### Normative rules

1. A confirmed Invoice Card may be preserved while its Source Package remains
   incomplete.
2. Incomplete transfer does not silently complete the import.
3. Every missing, failed, corrupt, or hash-mismatched source must retain an
   explicit status and provenance.
4. Without an explicit acceptance decision, the invoice remains outside normal
   downstream processing that requires complete source evidence.
5. An authorised actor may explicitly accept the Invoice Card with incomplete
   source evidence under A3.
6. Explicit acceptance records:
   - actor;
   - decision time;
   - reason;
   - Card revision;
   - exact missing or failed source references.
7. After explicit acceptance, the invoice may enter the durable archive with an
   explicit `source_package_status = incomplete`.
8. Incomplete source evidence does not prevent analytical use or Client Portal
   visibility when those workflows do not require originals.
9. An invoice with incomplete source evidence is not eligible for Holded
   publication.
10. Missing source files may be attached later through the authorised local
    attachment operation.
11. A later successful attachment updates source availability and package
    completeness but does not rewrite the immutable accepted Invoice Card.
12. A corrupt file, wrong invoice target, or hash mismatch cannot be converted
    into a successful attachment by the acceptance override.

---

### Formal invariants

For every expected source reference:

```text
exactly one current availability state exists:
available | missing | failed_verification
```

A source may be marked `available` only when:

```text
stored_hash = SHA256(stored_bytes)
and, when expected_hash exists:
stored_hash = expected_hash
```

For every accepted invoice with incomplete source evidence:

```text
source_package_status = incomplete
and explicit_missing_source_acceptance exists
```

Holded publication eligibility requires:

```text
source_package_status = complete
```

---

### Required tests

1. One failed file leaves the Source Package incomplete.
2. A failed file is never represented as available.
3. Without explicit acceptance, the incomplete invoice cannot enter workflows
   that require complete source evidence.
4. Explicit acceptance preserves the invoice with an auditable incomplete state.
5. Holded publication remains blocked while the Source Package is incomplete.
6. A later verified attachment may change the package from incomplete to
   complete.
7. Retrying the same verified attachment is idempotent.
8. A hash mismatch remains a verification failure and cannot be overridden as a
   successful upload.

---

### Consequence

The specification does not require a distributed all-or-nothing transaction
between Card data and every source file.

It requires truthful, deterministic state:

- complete evidence;
- incomplete but explicitly accepted evidence;
- or unaccepted incomplete transfer.

No implementation may treat a partial upload as silent success.

---

# D. Registry project validation and local decisions

## Accepted decision A31 — missing or unresolved project assignment requires review, not data loss

A confirmed Invoice Card may arrive with no usable Registry project assignment or
with a project identifier that cannot currently be resolved. This may occur when
an invoice is created between projects, before a project exists in Registry, or
with stale or incorrect context.

### Normative rules

1. Failure to resolve a project does not discard the Card or its source package.
2. Backend accepts the invoice into the durable archive when all independent Card
   and source acceptance requirements are satisfied.
3. The project assignment state becomes `unresolved` or `needs_review`.
4. The invoice is excluded from project-specific analytics until a project
   assignment decision is confirmed.
5. The invoice is not automatically published to Holded while the required
   project assignment remains unresolved.
6. A later project assignment may reference an existing Registry project or a
   project created after the invoice was accepted.
7. No arbitrary project is created automatically to satisfy the missing link.
8. The original object context from the Card is always preserved for audit.

### Required tests

1. A Card with no resolved project is preserved and marked for review.
2. Its source evidence remains accessible.
3. It does not enter project-specific analysis before resolution.
4. It does not become Holded-eligible solely through archival acceptance.
5. A later explicit assignment makes it eligible for the downstream operations
   whose other requirements are satisfied.

---

## Accepted decision A32 — a closed Registry project does not invalidate an invoice

An invoice may legitimately be issued, received, corrected, refunded, or processed
after the related project has been closed in Registry.

### Normative rules

1. A confirmed Invoice Card referencing an existing but closed Registry project is
   eligible for normal archival acceptance.
2. `project_closed` is contextual information, not a Card validation failure.
3. Backend preserves the project status observed at validation time.
4. The closed status may be shown as a warning or used by downstream policies, but
   it must not erase the Card's original object context.
5. Late invoices, final invoices, refunds, corrections, and additional charges may
   remain linked to a closed project.
6. Any separate restriction on Holded publication or project reporting must be
   specified explicitly and must not be inferred merely from project closure.

### Required tests

1. A valid confirmed Card for a closed existing project is accepted.
2. The validation record preserves `project_closed` context.
3. The Card's object block remains unchanged.
4. Existing project-linked history remains queryable after closure.

---

## Accepted decision A33 — project status does not reject an invoice

This decision defines how Cabinet Backend interprets project availability for
invoice processing. Registry remains the authoritative source of project status.
Concrete Registry status names and transport fields remain part of the Registry
contract and are not invented here.

Cabinet Backend must preserve a valid confirmed Invoice Card even when the linked
project is completed, archived, blocked, missing, or otherwise unavailable for
normal work.

Project status affects classification and review requirements, not the existence
of the invoice in the durable archive.

### Normative rules

1. Registry is authoritative for the current project status.
2. Cabinet Backend must not infer or rewrite Registry project status.
3. An invoice linked to an active project follows normal processing.
4. An invoice linked to a completed project is accepted and marked as a late
   project cost.
5. A completed project is not automatically reopened by Cabinet Backend.
6. An invoice linked to an archived, blocked, deleted, or otherwise unavailable
   project is preserved but requires manual review of the project assignment.
7. An invoice whose project cannot be found in the current Registry catalogue is
   preserved and requires manual review.
8. Project status alone must never cause deletion, silent rejection, or loss of a
   valid confirmed Invoice Card.
9. Project review state is stored separately from the immutable Invoice Card.
10. A later Registry refresh may resolve the review state without rewriting the
    accepted Invoice Card.
11. Cabinet Backend must not invent a replacement project automatically.
12. Downstream analytics must be able to distinguish:
    - normal project cost;
    - late project cost;
    - project assignment requiring review.

---

### Logical classification

The following semantic categories are normative even if Registry uses different
status names:

#### Active

The project is available for normal work.

```text
project_cost_classification = normal
project_assignment_requires_review = false
```

#### Completed

The project is formally complete but may still receive legitimate late expenses.

```text
project_cost_classification = late_project_cost
project_assignment_requires_review = false
```

#### Unavailable

The project is archived, blocked, deleted, inaccessible, or otherwise unsuitable
for automatic assignment.

```text
project_cost_classification = unresolved
project_assignment_requires_review = true
```

#### Unknown

No authoritative project record can be resolved from the current Registry
catalogue.

```text
project_cost_classification = unresolved
project_assignment_requires_review = true
```

---

### Formal invariants

A valid confirmed Invoice Card is not rejected solely because of project status:

```text
invoice_acceptance != rejected_by_project_status
```

For every completed project assignment:

```text
project_cost_classification = late_project_cost
```

For every unavailable or unknown project assignment:

```text
project_assignment_requires_review = true
```

Cabinet Backend cannot mutate Registry lifecycle state:

```text
backend_may_reopen_project = false
backend_may_change_registry_status = false
```

---

### Required tests

1. An invoice for an active project enters normal processing.
2. An invoice for a completed project is accepted and marked
   `late_project_cost`.
3. A completed project is not reopened automatically.
4. An invoice for an archived or blocked project is preserved and marked for
   manual review.
5. An invoice for an unknown project is preserved and marked for manual review.
6. A later Registry refresh may resolve the assignment without changing the
   immutable Invoice Card.
7. No project status causes silent invoice loss.
8. Downstream analytics can distinguish normal, late, and unresolved project
   costs.

---

### Open dependency

Registry currently exposes only `active` and `archived`. A34 maps `active` to
normal availability and `archived` or a missing project to unavailable review
states.

The only remaining status dependency is whether Registry will expose a separate
authoritative completion fact. Until it does, no Registry status produces the
`completed` category or `late_project_cost`.

---

### Consequence

Project completion is an analytical and workflow state, not a hard acceptance
boundary.

Cabinet Backend preserves the invoice, records the project context truthfully,
and escalates only the assignment decision that cannot be made safely.

---

## Accepted decision A34 — minimal Registry catalogue

This decision is based on observed Registry Sandbox behavior recorded in
`registry_discovery.md`. It defines the minimum catalogue projection required by
Cabinet Backend and does not extend the Registry contract.

Cabinet Backend maintains a compact local projection of Registry projects for
Cabinet synchronization and project-assignment workflows.

The catalogue contains only fields already available from the current Registry
project list.

### Catalogue fields

Each catalogue entry contains:

```text
project_id
display_name
address
status
registry_updated_at
```

### Field mapping

| Catalogue field | Registry source |
|---|---|
| `project_id` | `id` |
| `display_name` | `name` |
| `address` | `address` |
| `status` | `status` |
| `registry_updated_at` | `updated_at` |

The value of Registry `id` is preserved unchanged when projected as
`project_id`.

---

### Refresh source

The authoritative refresh source is:

```text
GET /projects?include_archived=true
```

The active-project reference endpoint is not sufficient because it omits address
and freshness evidence.

---

### Refresh semantics

1. Cabinet Backend performs a full catalogue poll.
2. The returned collection is transformed into the compact catalogue projection.
3. The local projection is replaced as one refreshed catalogue observation.
4. Cabinet Backend compares entries by stable `project_id`.
5. `registry_updated_at` is preserved as Registry freshness evidence.
6. No incremental cursor, event stream, tombstone, ETag, or catalogue revision is
   assumed.
7. Missing entries are not interpreted as confirmed deletion.
8. Incremental synchronization requires a future Registry contract and is not part
   of the current baseline.

---

### Status mapping

The current Registry contract exposes only:

```text
active
archived
```

Cabinet Backend maps them as follows:

| Registry status | Cabinet meaning |
|---|---|
| `active` | available for normal automatic project assignment |
| `archived` | unavailable for automatic assignment; manual review required |

Registry currently exposes no distinct completion status.

Therefore:

- `archived` must not be interpreted as `completed`;
- Cabinet Backend must not derive `late_project_cost` from `archived`;
- project completion remains an unresolved business fact until Registry exposes a
  separate authoritative contract.

---

### Missing project behavior

When a referenced `project_id` is absent from the current catalogue:

```text
project_assignment_requires_review = true
```

Cabinet Backend must preserve the invoice and must not infer whether the project:

- never existed;
- was removed outside the public Registry API;
- is temporarily unavailable;
- is hidden by an unknown operational condition.

No replacement project may be selected automatically.

---

### Excluded fields

The current compact catalogue does not include:

```text
customer_ref
created_at
```

These fields are excluded because they require per-project context requests and
are not required by the accepted minimum Cabinet workflow.

Adding either field requires a separate accepted decision.

---

### Formal invariants

For every catalogue entry:

```text
project_id = Registry.id
display_name = Registry.name
address = Registry.address
status = Registry.status
registry_updated_at = Registry.updated_at
```

Automatic assignment is allowed only when:

```text
status = active
```

Manual review is required when:

```text
status = archived
or project_id is absent from the current catalogue
```

Cabinet Backend must not claim:

```text
catalogue_is_incremental = true
catalogue_has_deletion_tombstones = true
archived_means_completed = true
```

---

### Required tests

1. A full Registry list is projected into the five accepted catalogue fields.
2. Registry `id` is preserved unchanged as `project_id`.
3. An active project is available for normal assignment.
4. An archived project requires manual review.
5. An archived project is not classified as completed.
6. A missing project requires manual review and does not reject the invoice.
7. `customer_ref` and `created_at` are not required for catalogue refresh.
8. A refresh does not depend on incremental cursors, ETags, or tombstones.
9. An absent entry is not recorded as confirmed deletion.

---

### Consequence

The current catalogue contract is intentionally small and polling-based.

It is sufficient for Cabinet project selection and safe assignment review without
introducing unsupported Registry capabilities.

---

## Accepted decision A35 — one-way WorkObject projection

This decision closes OQ-004. It defines a one-way projection from Registry
into Cabinet. Cabinet never mutates Registry and never synchronizes `WorkObject`
data back to Registry.

For every Registry project known to Cabinet, Cabinet maintains a corresponding
`WorkObject`.

`WorkObject` is a Cabinet-owned local copy of project data used by Cabinet
workflows.

The relationship is one-way:

```text
Registry project -> Cabinet WorkObject
```

There is no reverse synchronization.

---

### Normative rules

1. Registry remains authoritative for Registry-owned project fields.
2. Cabinet must not create, edit, archive, reopen, delete, or otherwise mutate
   Registry projects.
3. Cabinet must not send `WorkObject` changes back to Registry.
4. Cabinet stores all Registry projects, including both `active` and `archived`
   projects.
5. A catalogue refresh creates a `WorkObject` when no local object exists for the
   Registry `project_id`.
6. A catalogue refresh updates Registry-derived fields in an existing
   `WorkObject`.
7. A catalogue refresh must not overwrite Cabinet-owned local fields.
8. Registry-derived fields and Cabinet-owned fields must remain distinguishable.
9. An archived Registry project remains stored as a `WorkObject`.
10. If a project is absent from a later Registry catalogue response, Cabinet does
    not delete the existing `WorkObject`.
11. Absence from one refresh is recorded as unresolved source availability, not
    as confirmed deletion.
12. Cabinet must not automatically replace one `WorkObject` with another project.
13. One Registry `project_id` maps to at most one current Cabinet `WorkObject`.
14. A `WorkObject` must preserve the stable Registry `project_id` used to create
    it.

---

### Registry-derived fields

The current Registry-derived projection contains:

```text
project_id
display_name
address
status
registry_updated_at
```

These fields are refreshed from the compact Registry catalogue defined by A34.

---

### Cabinet-owned fields

Any field created exclusively for Cabinet workflows is Cabinet-owned.

Examples may include local presentation, workflow, notes, assignment, or
application state.

The exact Cabinet-owned field set belongs to the Cabinet contract and is not
defined by this rule.

Registry refresh must never overwrite a Cabinet-owned field merely because the
corresponding Registry project changed.

---

### Refresh behavior

For every catalogue entry:

#### WorkObject does not exist

Cabinet creates a new `WorkObject` with:

```text
registry_project_id = catalogue.project_id
registry-derived fields = catalogue values
```

#### WorkObject already exists

Cabinet updates only Registry-derived fields.

```text
registry-derived fields <- latest catalogue values
Cabinet-owned fields <- unchanged
```

#### Existing WorkObject is absent from refreshed catalogue

Cabinet preserves the `WorkObject`.

```text
work_object_deleted = false
registry_presence = unresolved
```

No confirmed deletion is inferred.

---

### Status behavior

#### Active Registry project

The corresponding `WorkObject` remains available for normal Cabinet workflows.

#### Archived Registry project

The corresponding `WorkObject` remains stored.

Its Registry status is updated to `archived`, and it is not treated as available
for normal automatic project assignment.

Archiving in Registry does not delete or archive Cabinet-owned information.

---

### Formal invariants

One-way ownership:

```text
Cabinet_may_mutate_Registry = false
WorkObject_changes_flow_to_Registry = false
```

Stable identity:

```text
one Registry project_id -> at most one current WorkObject
```

Refresh safety:

```text
Registry refresh updates only Registry-derived fields
```

Retention:

```text
archived Registry project -> WorkObject remains stored
missing catalogue entry -> WorkObject remains stored
```

---

### Required tests

1. A new Registry project creates one corresponding `WorkObject`.
2. Repeating the same catalogue refresh does not create a duplicate
   `WorkObject`.
3. A Registry name or address change updates the Registry-derived fields.
4. A Registry refresh does not overwrite Cabinet-owned fields.
5. An archived project remains stored as a `WorkObject`.
6. An archived project is not available for normal automatic assignment.
7. A project absent from a later catalogue response does not delete its
   `WorkObject`.
8. A missing catalogue entry is not interpreted as confirmed deletion.
9. Cabinet performs no Registry mutation during create, update, archive, or
   retention handling.
10. Local `WorkObject` changes never produce Registry writes.

---

### Consequence

Cabinet keeps a durable local `WorkObject` for every Registry project it has
observed.

Registry supplies authoritative project facts. Cabinet copies and refreshes those
facts for local use while preserving its own local state independently.

---

# E. PresuPro estimates and matching

## Accepted decision A40 — accepted Estimate Snapshots are immutable

An estimate accepted from PresuPro is stored as an immutable `EstimateSnapshot`.
PresuPro does not edit an already accepted estimate in place for Backend purposes.
A changed estimate is represented by a new snapshot.

### Normative rules

1. Cabinet Backend never overwrites an accepted Estimate Snapshot.
2. Existing snapshots remain available for historical and reproducible analysis.
3. Every `InvoiceLineEstimateMatch` references one exact Estimate Snapshot and one
   exact item in that snapshot.
4. Arrival of a new estimate does not alter or invalidate historical matches to
   an older estimate automatically.
5. Backend must not transfer old matches to a new snapshot automatically.
6. Analysis against a newer estimate requires new Cabinet decisions.
7. Successive observed states and distinct PresuPro estimate identities follow
   the verified snapshot and no-inferred-lineage semantics defined by A43.

### Formal invariant

```text
accepted EstimateSnapshot content is immutable
```

A new content identity must create a new snapshot record rather than mutate an
existing one.

### Required tests

1. Reimporting identical estimate content is idempotent.
2. Different estimate content creates a new snapshot.
3. Existing matches continue to reference their original snapshot.
4. A new snapshot receives no copied confirmed matches by default.

---

## Accepted decision A41 — unmatched purchases are normal analytical facts

An invoice line may have no matching item in the analysed estimate. This is not a
Card validation error and does not block invoice acceptance.

### Normative rules

1. One invoice line has at most one active confirmed estimate-item match in the
   current baseline.
2. Splitting one invoice line across several estimate items is not supported in
   the current baseline.
3. A line without a confirmed match remains explicitly unmatched.
4. Unmatched status may represent additional work, a consumable, delivery, a
   tool, a substitution, an omitted estimate item, or another Cabinet explanation.
5. Cabinet owns semantic classification and explanation of the unmatched line.
6. Cabinet Backend stores the confirmed result and optional explanation
   provenance; it does not invent a category.
7. Unmatched lines remain available to coverage and variance analytics.

### Required tests

1. An invoice containing unmatched lines is accepted normally.
2. An unmatched line does not create a placeholder estimate item.
3. Backend rejects attempts to create two simultaneous active confirmed matches
   for one line.
4. Rejecting or removing a match returns the line to explicit unmatched status
   without changing the Invoice Card.

---

## Accepted decision A42 — PresuPro semantic analysis belongs to Cabinet

Cabinet performs the semantic and assisted analysis that connects purchased goods
to estimates. This includes cases where estimate prices refer to one supplier but
actual purchases were made from another supplier.

Cabinet Backend does not choose the relevant estimate, infer product equivalence,
or independently create semantic matches.

### Normative rules

1. Cabinet may use AI and human confirmation to analyse invoice lines against one
   or more PresuPro estimates.
2. Cabinet Backend stores imported immutable estimate projections and accepted
   matching decisions.
3. Backend may verify that referenced invoices, Card revisions, lines, estimate
   snapshots, and estimate items exist.
4. Backend must not confirm a semantic match merely because textual descriptions,
   prices, suppliers, or quantities look similar.
5. A suggestion is not analytical truth until Cabinet submits a confirmed
   decision with sufficient provenance.
6. Deterministic totals and reports may be calculated from confirmed decisions;
   semantic interpretation remains outside Backend.

### Consequence

Cabinet answers why two commercial items should be treated as corresponding.
Cabinet Backend records exactly what was confirmed and calculates from that fact.

---

## Accepted decision A43 — Cabinet-owned immutable PresuPro estimate snapshots

This decision is based on the factual reconnaissance recorded in
`presupro_estimate_lineage_discovery.md`. It defines how Cabinet Backend
preserves PresuPro estimate content when PresuPro does not expose authoritative
revision-family or predecessor semantics.

### Verified PresuPro facts

The current PresuPro contract behaves as follows:

1. `Estimate.id` is the stable identity of one mutable PresuPro estimate record.
2. Editing preserves `Estimate.id` and `created_at`.
3. Editing changes `updated_at`.
4. Editing overwrites the same stored estimate record.
5. PresuPro does not retain previous estimate content.
6. PresuPro exposes no estimate revision table, history table, content hash,
   family identifier, predecessor, replacement, supersession, or copy reference.
7. A new estimate with equivalent content and a different ID is indistinguishable
   from an independent estimate.
8. Multiple independent estimates may reference the same Registry project.
9. Status values such as `accepted` and `archived` do not themselves block edit.
10. Conversion creates `invoice_ref`, sets `locked = true`, and prevents later
    content modification.
11. Export preserves only the current estimate identity, status, and timestamps.
12. Export does not preserve lineage because no lineage exists in the current
    PresuPro contract.

---

### Cabinet-owned immutable snapshots

Cabinet Backend preserves every observed PresuPro estimate content state as an
immutable `EstimateSnapshot`.

PresuPro remains authoritative for the current mutable estimate record.
Cabinet Backend becomes authoritative for the immutable evidence it has already
accepted.

---

### Snapshot identity

Every `EstimateSnapshot` must contain at least:

```text
snapshot_id
presupro_estimate_id
content_hash
observed_at
presupro_updated_at
project_id
status
locked
content
```

The exact storage model belongs to the implementation specification.

#### Stable source identity

`presupro_estimate_id` preserves the exact PresuPro `Estimate.id`.

Several Cabinet Backend snapshots may share the same
`presupro_estimate_id`.

```text
one PresuPro Estimate.id -> zero or more immutable EstimateSnapshots
```

---

### Snapshot creation

Cabinet Backend creates a new snapshot when the accepted PresuPro estimate
content differs from the latest stored snapshot for the same
`presupro_estimate_id`.

Comparison must use canonical content hashing or an equivalent deterministic
content comparison.

A change in `updated_at` alone is not sufficient when the content is unchanged.

A content change is sufficient even when PresuPro preserves the same
`Estimate.id`.

---

### Idempotency

Repeating import of the same canonical estimate content must not create a
duplicate snapshot.

```text
same presupro_estimate_id
and same canonical content_hash
-> same logical EstimateSnapshot
```

Operational import attempts may be recorded separately.

---

### No inferred lineage

Cabinet Backend must not infer any of the following:

```text
estimate_family_id
previous_estimate_id
next_estimate_id
replaces_estimate_id
supersedes_estimate_id
copied_from_estimate_id
revision_number
```

These relationships do not exist in the verified PresuPro contract.

Cabinet Backend must not infer lineage from:

- shared Registry project;
- similar or identical line content;
- nearby timestamps;
- supplier overlap;
- estimate naming;
- user-visible numbering;
- one estimate being created after another.

---

### Different PresuPro IDs

Different `presupro_estimate_id` values always represent independent estimates
for Cabinet Backend unless a future accepted PresuPro contract explicitly
provides lineage.

This remains true when:

- both estimates belong to the same project;
- both contain identical lines;
- one appears to be a manual copy of the other.

---

### Snapshot sequence

Cabinet Backend may order snapshots observed for the same
`presupro_estimate_id` by local observation time and PresuPro `updated_at`.

This order is an observation sequence only.

It must not be described as authoritative PresuPro revision lineage.

Allowed terminology:

```text
earlier observed snapshot
later observed snapshot
```

Disallowed terminology without a future contract:

```text
parent revision
child revision
official version 2
superseding estimate
replacement estimate
```

---

### Matching behavior

Confirmed invoice-line matches remain pinned to the exact
`EstimateSnapshot.snapshot_id` used when the match was accepted.

A later snapshot for the same `presupro_estimate_id` must not:

- move existing matches;
- rewrite existing matches;
- inherit existing matches automatically;
- invalidate the old snapshot;
- delete analytical history.

A later snapshot may be used for new matching decisions only.

---

### Locked and converted estimates

When PresuPro reports:

```text
locked = true
```

Cabinet Backend preserves that fact in the snapshot.

A lock indicates that PresuPro currently rejects later content modification for
that estimate record.

The lock does not create missing revision lineage and does not turn prior mutable
states into PresuPro-authored historical revisions.

---

### Status handling

Cabinet Backend stores the raw PresuPro status value.

Because the Backend accepts arbitrary status strings and the five common values
are frontend conventions, Cabinet Backend must not infer lifecycle guarantees
from status alone.

In particular:

```text
status = accepted
```

does not prove immutability.

```text
status = archived
```

does not prove immutability.

Only verified `locked = true` is accepted as evidence that PresuPro currently
blocks content edits.

---

### Formal invariants

Snapshot immutability:

```text
EstimateSnapshot content never changes after acceptance
```

Same-record history:

```text
multiple snapshots may share one presupro_estimate_id
```

Independent identities:

```text
different presupro_estimate_id values -> independent estimates
```

No inferred family:

```text
estimate_family_id is absent unless supplied by a future accepted contract
```

Match stability:

```text
confirmed match -> exact immutable snapshot_id
```

---

### Required tests

1. First import of an estimate creates one immutable snapshot.
2. Re-import of identical content does not create a duplicate snapshot.
3. Editing PresuPro content under the same `Estimate.id` creates a new snapshot.
4. The previous snapshot remains unchanged and queryable.
5. A timestamp-only change with identical content does not require a new logical
   snapshot.
6. Two estimates with different IDs remain independent even when content is
   identical.
7. Two estimates for one project are not grouped into one family.
8. A later snapshot does not inherit confirmed invoice-line matches.
9. Existing matches remain linked to the original snapshot.
10. Raw status is preserved without assuming immutability.
11. `locked = true` is preserved without inventing predecessor or revision
    semantics.
12. Export metadata does not create lineage that PresuPro does not provide.

### Consequence

Cabinet Backend preserves reliable historical estimate evidence without
pretending that PresuPro supplies version-family semantics.

The design remains safe under PresuPro's current mutable-record model and can be
extended later if PresuPro introduces explicit lineage.

---

# F. Holded purchase publication

## Accepted decision A51 — create one Holded purchase and verify it by GET

Cabinet Backend publishes a new supplier invoice to Holded by creating exactly
one purchase document and then reading that exact document back. A successful
POST response alone is not sufficient publication evidence.

This decision is based on a successful runtime experiment against the official
Holded v1 document API using a validated Cabinet Invoice Card fixture. It defines
first publication and post-create verification only. It does not define update,
refund, attachment, idempotency, status interpretation, or later-revision
reconciliation behavior.

### Verified runtime baseline

The experiment confirmed:

- exactly one successful purchase creation request;
- HTTP `200` and a returned Holded `documentId`;
- successful GET of the created document;
- no repeated POST, PUT, or DELETE;
- no separate supplier or product creation request;
- preservation of supplier invoice number through returned `docNumber`, date,
  description, currency, supplier name, line count and order, line names,
  quantities, IVA rates, and final gross total;
- absence of preserved supplier SKU values in the returned lines;
- Holded recalculation of intermediate monetary values using its own line-rounding
  behavior;
- a numeric Holded status whose business meaning remains unverified.

### Normative sequence

1. Validate the immutable Invoice Card revision.
2. Build the Holded purchase payload.
3. Send exactly one create request for the publication attempt.
4. Record the returned Holded `documentId`.
5. Read the created document by that `documentId`.
6. Compare the returned document with the published Invoice Card revision.
7. Record the verified Holded representation separately from the immutable
   Invoice Card.
8. Mark the publication successful only after the GET verification passes.

### Publication identity

Every successful publication record must link:

```text
invoice_id
invoice_revision_hash
holded_document_id
published_at
```

The Holded document identifier is the canonical external reference for later
reads and reconciliation. The supplier invoice number is not the Holded identity
key.

### Payload rules

The first supported purchase payload may include:

```text
applyContactDefaults
contactCode
contactName
desc
date
approveDoc
items
invoiceNum
currency
```

Each item may include:

```text
name
desc
units
subtotal
discount
tax
sku
```

A field being accepted in the create payload does not prove that Holded persists
or returns it. In particular, supplier SKU must not be treated as verified Holded
line identity until runtime evidence confirms persistence.

### Required POST-to-GET verification

Backend must verify at least:

```text
holded_document_id
supplier invoice number
document date
currency
supplier name
line count
line order
line names
line quantities
line tax rates
gross total
```

The returned Holded `docNumber` may be compared with the source supplier invoice
number. Backend must not require a separate GET field named `invoiceNum`.

### Monetary reconciliation

The Invoice Card remains authoritative for captured source values. Holded may
recalculate line, tax, and subtotal amounts according to its own rounding rules.

Backend must store both:

```text
source_invoice_totals
holded_document_totals
```

Differences in intermediate values such as net subtotal or tax total are not
publication failures when:

1. the source lines, quantities, and tax rates are preserved;
2. the final gross total matches within the currency precision;
3. the difference is consistent with Holded rounding behavior.

For EUR, gross comparison uses cent precision:

```text
round(source_gross, 2) = round(holded_total, 2)
```

If the final gross total does not match within currency precision:

```text
publication_status = verification_failed
holded_reconciliation_required = true
```

Backend must preserve the immutable Invoice Card revision, Holded document
identifier, source totals, returned Holded totals, and observed discrepancy. It
must not silently alter Invoice Card totals to match Holded.

### Line verification

Line order and count are part of the current verification baseline. For every
line, Backend verifies:

```text
name
units
tax
```

Description may also be recorded and compared when returned. Supplier SKU is not
part of successful verification because the runtime GET did not preserve it.
Absence of returned SKU must not be interpreted as a publication failure.

### Supplier behavior

The verified experiment did not require a separate supplier-creation request.
Cabinet Backend may create the purchase using `contactCode` and `contactName`.
This does not establish a general rule that every Holded account or supplier can
always be resolved this way. Supplier resolution conflicts remain implementation
and future discovery concerns.

### Holded status

The returned Holded status is numeric. Until its meaning is verified:

1. Backend stores the raw status value.
2. Backend must not label it as draft, approved, paid, posted, or cancelled.
3. `approveDoc = false` must not be used as proof of the returned accounting
   state.
4. Status-based mutation rules remain open.

### Idempotency and retry safety

The runtime experiment proves only one successful create request. It does not
prove that Holded create is idempotent.

Therefore:

1. Backend must not automatically repeat POST after an ambiguous timeout.
2. Every attempt must have a stable local publication attempt identifier.
3. Before any manual retry, Backend should search or verify whether a Holded
   document was already created.
4. Automatic duplicate prevention requires separate runtime evidence or a
   verified external-reference mechanism.

### Formal invariants

A successful publication requires:

```text
POST succeeded
and holded_document_id exists
and GET by holded_document_id succeeded
and gross total matches within currency precision
```

Invoice Card immutability:

```text
Holded recalculation does not modify Invoice Card
```

Publication linkage:

```text
one publication record -> one invoice revision hash
```

Unknown status semantics:

```text
numeric Holded status -> stored raw, not interpreted
```

### Required tests

1. A valid Invoice Card creates exactly one purchase.
2. The returned `documentId` is stored.
3. GET of the created document succeeds.
4. `docNumber` matches the supplier invoice number.
5. Date, currency, supplier name, line count, line order, quantities, tax rates,
   and gross total match the expected source values.
6. Intermediate net and tax differences caused by Holded rounding do not fail
   publication when gross total matches to currency precision.
7. A gross-total mismatch produces `verification_failed` and
   `holded_reconciliation_required`.
8. Missing returned SKU does not fail verification.
9. Raw numeric Holded status is stored without business interpretation.
10. An ambiguous create timeout does not trigger an automatic repeated POST.
11. A failed verification never rewrites the immutable Invoice Card.

### Consequence

Cabinet Backend may perform a verified first publication to Holded. Holded is an
external accounting representation of one exact Invoice Card revision, not the
authority for the original captured document. Publication succeeds only after
read-back verification, while Holded-specific rounding is preserved as
external-system evidence rather than written back into the Invoice Card.

---
