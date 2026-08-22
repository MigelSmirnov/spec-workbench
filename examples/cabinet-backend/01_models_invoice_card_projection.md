# State 1 repair — Invoice Card V1 projection and comparable estimate items

## Why

`StoredInvoiceCardRevision.canonical_card` was `dict[str, object]`: the card structure that
`registry_context`, `plan_actual`, and `holded_publication` consume (object block, lines, supplier,
totals) was declared nowhere, so generated services invented fields. The structure is accepted
product data — Cabinet_web `docs/01-storage/INVOICE_CARD_FORMAT.md` — and is projected here with
full fidelity so that the canonical JSON round-trips unchanged. Money is `Decimal` with two places,
quantities up to four; `StoredInvoiceCardRevision.canonical_card: InvoiceCardV1`.

## Model M79 — InvoiceCardParty

A party of the invoice (supplier or buyer) as captured in the card.

Fields:

- `name: str | None`;
- `tax_id: str | None`;
- `address: str | None`;

### Identity

value

### Identity evidence

Equal name, tax id, and address are the same party evidence.

---

## Model M80 — InvoiceCardObjectBlock

The primary object context captured with the invoice; never a Registry project identifier.

Fields:

- `card_id: str | None`;
- `label: str | None`;

### Identity

value

### Identity evidence

Equal card id and label are the same capture evidence; assignment validation is recorded separately (M17).

---

## Model M81 — InvoiceCardLine

One invoice line with its two authoritative monetary facts: net_amount (post-discount, tax-exclusive) and gross_amount (tax-inclusive).

Fields:

- `line_id: str`;
- `kind: str`;
- `description_original: str`;
- `description_normalized: str | None`;
- `supplier_sku: str | None`;
- `matched_material_id: str | None`;
- `quantity: Decimal`;
- `unit: str`;
- `unit_price_net: Decimal`;
- `discount_percent: Decimal`;
- `discount_amount: Decimal`;
- `net_amount: Decimal`;
- `tax_rate: Decimal`;
- `tax_amount: Decimal`;
- `gross_amount: Decimal`;

### Identity

value

### Identity evidence

Equal line_id within one revision is the same line; monetary facts are never recomputed by the Backend.

---

## Model M82 — InvoiceCardTotals

The card totals as stated by the source.

Fields:

- `net: Decimal`;
- `discount: Decimal`;
- `tax: Decimal`;
- `gross: Decimal`;
- `withholding: Decimal`;
- `payable: Decimal`;

### Identity

value

### Identity evidence

Equal totals are interchangeable; the validator reports arithmetic discrepancies, never rewrites them.

---

## Model M83 — InvoiceCardPaymentEvidence

Origin of a payment fact.

Fields:

- `basis: str`;
- `source_ref: str | None`;

### Identity

value

### Identity evidence

Equal basis and source reference are the same evidence.

---

## Model M84 — InvoiceCardPaymentTransaction

One recorded payment transaction.

Fields:

- `payment_id: str`;
- `method: str`;
- `paid_at: datetime`;
- `currency: str`;
- `tendered_amount: Decimal | None`;
- `applied_amount: Decimal`;
- `change_amount: Decimal | None`;
- `reference: str | None`;
- `evidence: InvoiceCardPaymentEvidence`;

### Identity

value

### Identity evidence

Equal payment_id within one card is the same transaction.

---

## Model M85 — InvoiceCardPayment

Payment state and transactions; unknown state is explicit.

Fields:

- `status: str`;
- `transactions: tuple[InvoiceCardPaymentTransaction, ...]`;

### Identity

value

### Identity evidence

Equal status and transactions are the same payment evidence.

---

## Model M86 — InvoiceCardSourceBlock

The source reference block of the card.

Fields:

- `source_id: str`;
- `kind: str`;
- `file_ref: str | None`;
- `file_status: str`;
- `note: str | None`;

### Identity

value

### Identity evidence

Equal source id and status are the same source evidence.

---

## Model M87 — InvoiceCardProvenance

Creation and confirmation provenance of the card.

Fields:

- `created_at: datetime`;
- `confirmed_at: datetime | None`;
- `created_by: str`;

### Identity

value

### Identity evidence

Equal timestamps and creator are the same provenance.

---

## M01 — InvoiceCardV1 (refinement, identity unchanged: entity)

The complete Version 1 card as the typed projection of `StoredInvoiceCardRevision.canonical_card`:

- `card_type: str`;
- `card_version: int`;
- `id: str`;
- `status: str`;
- `invoice_number: str`;
- `issue_date: date`;
- `service_date: date | None`;
- `due_date: date | None`;
- `currency: str`;
- `supplier: InvoiceCardParty`;
- `buyer: InvoiceCardParty`;
- `object: InvoiceCardObjectBlock`;
- `lines: tuple[InvoiceCardLine, ...]`;
- `totals: InvoiceCardTotals`;
- `payment: InvoiceCardPayment`;
- `source: InvoiceCardSourceBlock`;
- `provenance: InvoiceCardProvenance`;

---

## Monetary basis closure (resolves `01_models_plan_actual_monetary_gap.md`)

The basis is a fact of the data, not a global constant. `EstimateItemSnapshot` (M29) gains `currency`
and `monetary_basis` (`net` or `gross`) as observed from PresuPro; `PresuProEstimateObservation` gains
`currency` and the typed `items` it was parsed into. Plan/actual takes `InvoiceCardLine.net_amount` for
a `net` item and `gross_amount` for a `gross` item; any other pairing is a basis mismatch unless an
accepted assumption is pinned. The rule address `actual_amount_source = confirmed_matched_invoice_line.total`
reads as "the line amount of the item's basis".

## Card → Registry project

`CardObjectAssignmentObservation` (M17) gains `observation_id` and storage in `registry_context_persistence`
(`load_assignment_observation`, `insert_assignment_observation`). `validate_card_assignment` reads the
project from the stored observation; `canonical_card.object` is capture evidence only. Who produces the
observation at capture time remains an open item in `30_modules_persistence_boundary.md`.
