# Cabinet Backend — Holded Purchase Publication Verification

## Status

Accepted clarification for `02_rules.md`.

This rule is based on a successful runtime experiment against the official
Holded v1 document API using a validated Cabinet Invoice Card fixture.

It defines first publication and post-create verification only.

It does not define update, deletion, refund, rectification, or revision
reconciliation behavior.

---

## Verified runtime facts

A validated Cabinet Invoice Card was published as exactly one Holded purchase.

The experiment confirmed:

- one successful purchase creation request;
- HTTP `200`;
- returned Holded `documentId`;
- successful GET of the created document;
- no repeated POST;
- no PUT;
- no DELETE;
- no separate supplier creation;
- no separate product creation.

The created Holded document preserved:

- document identity;
- supplier invoice number through returned `docNumber`;
- date;
- description;
- currency;
- supplier name;
- line count and order;
- line names;
- quantities;
- IVA rates;
- final gross total.

The experiment also observed:

- supplier SKU was not preserved in the returned Holded lines;
- Holded recalculated intermediate monetary values using its own line-rounding
  behavior;
- Holded returned a numeric status whose business meaning remains unverified.

---

## Accepted decision — create once, then verify by GET

Cabinet Backend publishes a new supplier invoice to Holded by creating one
purchase document and then reading that exact document back.

A successful POST response alone is not sufficient publication evidence.

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

---

## Publication identity

Every successful publication record must link:

```text
invoice_id
invoice_revision_hash
holded_document_id
published_at
```

The Holded document identifier is the canonical external reference for later
reads and reconciliation.

The supplier invoice number is not the Holded identity key.

---

## Payload rules

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
or returns it.

In particular, supplier SKU must not be treated as verified Holded line identity
until runtime evidence confirms persistence.

---

## Required POST-to-GET verification

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
number.

Backend must not require a separate GET field named `invoiceNum`.

---

## Monetary reconciliation

The Invoice Card remains authoritative for captured source values.

Holded may recalculate line, tax, and subtotal amounts according to its own
rounding rules.

Backend must store both:

```text
source_invoice_totals
holded_document_totals
```

### Accepted comparison rule

Differences in intermediate values such as net subtotal or tax total are not
publication failures when:

1. the source lines, quantities, and tax rates are preserved;
2. the final gross total matches within the currency precision;
3. the difference is consistent with Holded rounding behavior.

For EUR, gross comparison uses cent precision.

```text
round(source_gross, 2) = round(holded_total, 2)
```

### Failure condition

If the final gross total does not match within currency precision:

```text
publication_status = verification_failed
holded_reconciliation_required = true
```

Backend must preserve:

- the immutable Invoice Card revision;
- the Holded document identifier;
- source totals;
- returned Holded totals;
- the observed discrepancy.

Backend must not silently alter Invoice Card totals to match Holded.

---

## Line verification

Line order and count are part of the current verification baseline.

For every line, Backend verifies:

```text
name
units
tax
```

Description may also be recorded and compared when returned.

Supplier SKU is not part of successful verification because the runtime GET did
not return it.

Absence of returned SKU must not be interpreted as a publication failure.

---

## Supplier behavior

The verified experiment did not require separate supplier creation.

Cabinet Backend may create the purchase using:

```text
contactCode
contactName
```

This does not establish a general rule that every Holded account or supplier can
always be resolved this way.

Supplier resolution conflicts remain implementation and future discovery
concerns.

---

## Holded status

The returned Holded status is numeric.

Until its meaning is verified:

1. Backend stores the raw status value.
2. Backend must not label it as draft, approved, paid, posted, or cancelled.
3. `approveDoc = false` must not be used as proof of the returned accounting
   state.
4. Status-based mutation rules remain open.

---

## Idempotency and retry safety

The runtime experiment proves only one successful create request.

It does not prove that Holded create is idempotent.

Therefore:

1. Backend must not automatically repeat POST after an ambiguous timeout.
2. Every attempt must have a stable local publication attempt identifier.
3. Before any manual retry, Backend should search or verify whether a Holded
   document was already created.
4. Automatic duplicate prevention requires separate runtime evidence or a
   verified external-reference mechanism.

---

## Formal invariants

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

---

## Required tests

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

---

## Open questions

The following remain outside this decision:

1. exact meaning of Holded numeric status values;
2. update behavior for existing purchases;
3. purchase refund or rectification behavior;
4. deletion and cancellation behavior;
5. attachment upload and retrieval;
6. safe retry or idempotency mechanism;
7. reconciliation of a later Invoice Card revision with an already published
   purchase.

---

## Consequence

Cabinet Backend may perform a verified first publication to Holded.

Holded becomes an external accounting representation of one exact Invoice Card
revision, not the authority for the original captured document.

Publication succeeds only after read-back verification, while Holded-specific
rounding is preserved as external-system evidence rather than written back into
the Invoice Card.
