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

# B. Decisions still open

The next decision concerns source bytes: whether a confirmed Card may be accepted
when one or more referenced photographs or PDFs are missing, and which Card
source states make absence of bytes intentional rather than an import failure.
