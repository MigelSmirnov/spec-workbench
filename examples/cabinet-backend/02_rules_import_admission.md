# State 2 — import admission reconciliation

## Accepted decision A77 — A20 governs import admission; A2 border rejection superseded (2026-09-03)

The product owner confirmed (2026-09-03) the runtime product shape: Cabinet Web
remains the main daily working surface; the local Backend is the durable archive
that downloads and preserves its data. No cross-boundary draft-editing workflow
is planned. Synchronization is therefore backup and archive transfer, exactly as
A20 B.1 records — not a business confirmation boundary.

### Normative rules

1. A20 sections B.1, D, and E govern import admission at
   `durable_archive.accept_transfer_manifest`. A2 rules 3–5 (border rejection of
   a `draft` revision with `card_not_confirmed`) are superseded.
2. A delivered `draft` revision is archived truthfully: the stored head and
   revision carry `observed_status = draft`; import never changes lifecycle
   status (A20 B.2.3).
3. The surviving A2 exclusions move to the eligibility gates: Holded publication
   refuses a revision whose `observed_status` is not `confirmed` with the
   deterministic reason `card_not_confirmed` (the A2 result name survives at the
   gate, not at the border), and confirmed actual totals continue to use only
   explicitly confirmed matching decisions (A41/A73).
4. A delivered card revision whose `card_version` is not the accepted Invoice
   Card V1 version is quarantined per A20 D.4/E.1: the receipt result is
   `quarantined` with `safe_error_code = quarantine_required`, and no archive
   head or revision is created or advanced. It is never silently parsed as V1.
5. An unsupported Cabinet Card type is structurally unrepresentable at the
   import boundary: the typed transfer package carries `InvoiceCardV1` only
   (A6's closed scope is enforced by the model contract, not by a runtime
   check).
6. Persisting `ImportQuarantine` evidence rows requires an `ArchiveUnitOfWork`
   surface addition that this decision does not make; until that separate
   surface decision, the classified quarantined receipt is the enforced
   obligation, and the VPS retains its authoritative working copy (A20 E.2.4).

### Formal invariants

```text
draft_revision -> archived_with_observed_status_draft
draft_revision -/> holded_eligible
unsupported_card_version -> quarantined_receipt AND no_archive_head_transition
non_v1_card_type -/> representable_at_import_boundary
```

### Required tests

1. A delivered `draft` revision is archived with truthful `draft` status.
   [witness: verification:witness_A77]
2. A `draft` revision with complete sources is refused Holded publication with
   reason `card_not_confirmed`.
3. A delivered revision with an unsupported `card_version` yields a
   `quarantined` receipt and creates no archive head.
4. A non-V1 canonical card cannot be represented in the typed transfer package.

### Consequence

The June-era border-rejection reading of A1/A2/A6 is reconciled with the
accepted runtime import design without any model change: `draft` archives
truthfully, exclusion is enforced where the business risk lives (publication
and analytics eligibility), and unsupported contracts quarantine instead of
silently degrading.

## Accepted decision A78 — the archived card is the product Invoice Card V1 without narrowing (2026-09-05)

The product owner fixed (2026-09-05) `InvoiceCardV1` at Cabinet_web `c897897`
(`schemas/invoice-card-v1.schema.json`) as the canonical version-1 contract
for every consumer. The Backend's typed projection (M01, M84, M86) narrowed
three facts the product states as nullable and omitted the product's
`source.source_id`; because the archive models forbid unknown fields, every
product card would have been refused at the import boundary. The projection
is corrected to the product schema; the Holded projection is the only place
where a lossy mapping may live, and it refuses rather than invents.

### Normative rules

1. `InvoiceCardV1.invoice_number` and `issue_date` are nullable exactly as the
   product schema states; `InvoiceCardPaymentTransaction.paid_at` is nullable.
   Import archives such a card truthfully and never substitutes a value.
2. `InvoiceCardSourceBlock` carries the product `source_id` as preserved card
   content. The required-source set of an invoice is still
   `InvoiceTransferManifest.source_references` and locally attached
   `SourceBinary` rows (A20); the card's `source_id` is not read as a
   required-source identity.
3. Holded publication refuses a revision whose `invoice_number` or
   `issue_date` is `None` before any gateway interaction with the
   deterministic reason `card_incomplete`; the purchase payload is projected
   only from a card that passed this gate, so `invoice_num` and `date` are
   never manufactured.

### Formal invariants

```text
product_card(c897897) -> representable_at_import_boundary
invoice_number_none OR issue_date_none -/> holded_eligible
card.source.source_id -/> required_source_identity
```

### Required tests

1. A product card with `invoice_number = null` and `issue_date = null` is
   archived truthfully and is refused Holded publication with reason
   `card_incomplete`. [witness: verification:witness_A78]
2. A product card carrying `source.source_id` is accepted at the import
   boundary; its required sources are still taken from the manifest.
   [witness: verification:witness_A78]

### Consequence

The Backend stops being a second, narrower definition of the invoice: the
archive preserves the product card as stated, and the only lossy projection
stays inside the Holded adapter behind an explicit refusal.
