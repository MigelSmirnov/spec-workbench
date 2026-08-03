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

# B. Decisions still open

The next decision is the import transaction boundary: whether accepted Card data
and any source bytes that are present become visible atomically, and how a partial
or failed attachment attempt is staged and retried.
