# Holded purchase status and PUT discovery

## Status

Factual runtime discovery through H3.

The read-only H1 observation and same-document UI correlation are reproducible.
The metadata-only H2 PUT and restoring H3 PUT were each executed exactly once and
verified by GET. The final API response is byte-identical to the original H1 GET.

No POST, DELETE, attachment, payment, approval, or `purchaserefund` request was
executed. Exactly two PUT requests changed only `desc`, first forward and then
back to the original value.

This document is factual evidence, not a normative Cabinet Backend rule.

---

## Environment

```text
observed_at: 2026-08-06T19:31:05Z
H2 pre-PUT GET: 2026-08-06T19:54:07Z
H2 PUT: 2026-08-06T19:54:18Z
H2 post-PUT GET: 2026-08-06T19:54:36Z
H3 pre-PUT GET: 2026-08-06T20:02:17Z
H3 PUT: 2026-08-06T20:02:25Z
H3 post-PUT GET: 2026-08-06T20:02:39Z
runtime: local Cabinet/spec-workbench environment
credential source: HOLDED_V1_API_KEY from /home/smirnov/jestor_VBC/.env
credential value: not recorded
transport: HTTPS
```

The configured credential was present and non-empty. Neither the credential nor
the authorization header was printed or stored in this repository.

## Test document

The supplied document was confirmed by GET before any mutation:

```text
documentId: 6a74cd787765e9f84a0297d3
document type requested: purchase
description: CABINET API TEST
docNumber: 036-0008-424824
currency: eur
gross total: 11.75
product lines: 3
```

All supplied identity checks matched. The document was not replaced or recreated.

## API endpoint and version

```text
GET https://api.holded.com/api/invoicing/v1/documents/purchase/{documentId}
PUT https://api.holded.com/api/invoicing/v1/documents/{docType}/{documentId}
```

The GET endpoint returned HTTP `200`.

The official Holded API reference documents `desc` as an accepted PUT body
field, together with other optional fields. It does not state whether omitted
fields are preserved, whether PUT is a full replacement or partial update, or
what accounting effects an update has.

Official references:

- https://developers.holded.com/reference/getdocument-1
- https://developers.holded.com/reference/update-document-1

## Status observations

The GET response contained:

```text
numeric status: 0
draft: null
approvedAt: null
paymentsTotal: 0
paymentsPending: 11.75
paymentsRefunds: 0
accountingDate: null
created_at or equivalent: absent
updated_at or equivalent: absent
```

The Holded UI for the same document showed `Este documento aún no ha sido
aprobado` and the separate action `Aprobar`. It also showed total `11.75 EUR`,
payment state `pending`, and pending amount `11.75 EUR`.

Therefore, for this observed purchase:

```text
numeric status = 0 -> not approved / unapproved
```

This is a same-document correlation. It does not establish the meaning of every
other numeric status value.

## PUT request semantics

The official reference confirms that the update operation exists and accepts
`desc`. It does not resolve:

- full replacement versus partial update;
- preservation of omitted fields;
- whether all product lines must be repeated;
- preservation of unknown fields;
- accounting consequences;
- optimistic concurrency behavior.

The GET response and response headers exposed no ETag, content version,
last-modified value, revision hash, or update timestamp suitable for concurrent
update protection.

For this unapproved purchase, both forward and restoring bodies containing only
`desc` preserved every other returned top-level field. The observed runtime
behavior is therefore a reversible partial metadata update, despite the HTTP
method being PUT. This does not prove the same preservation behavior for
financial fields, approved documents, or fields not exposed by GET.

## Metadata PUT result

H2 was executed exactly once:

```json
{
  "desc": "CABINET API TEST PUT METADATA"
}
```

```text
HTTP method: PUT
sanitized path: /api/invoicing/v1/documents/purchase/{documentId}
HTTP status: 200
sanitized response: {"status":1,"info":"Updated"}
```

The PUT response's `status = 1` is an operation-result field. It is not the
purchase document status: the following GET still returned numeric document
status `0`.

H3 was then authorized and executed exactly once:

```json
{
  "desc": "CABINET API TEST"
}
```

```text
HTTP method: PUT
sanitized path: /api/invoicing/v1/documents/purchase/{documentId}
HTTP status: 200
sanitized response: {"status":1,"info":"Updated"}
```

No retry occurred for either PUT.

## Read-back verification

Two consecutive read-only GET requests returned HTTP `200` and byte-identical
JSON bodies. The second body was saved transiently before the planned PUT and
sanitized for inspection.

Sanitized GET structure:

```json
{
  "id": "6a74cd787765e9f84a0297d3",
  "contact": "[redacted]",
  "contactName": "[redacted]",
  "desc": "CABINET API TEST",
  "date": 1785535200,
  "dueDate": null,
  "accountingDate": null,
  "approvedAt": null,
  "draft": null,
  "docNumber": "036-0008-424824",
  "currency": "eur",
  "status": 0,
  "subtotal": 9.7200000000000006,
  "tax": 2.0299999999999998,
  "total": 11.75,
  "paymentsTotal": 0,
  "paymentsPending": 11.75,
  "paymentsRefunds": 0,
  "products": [
    {"name": "[redacted]", "price": 2.0661160000000001, "units": 1, "tax": 21, "discount": 0},
    {"name": "[redacted]", "price": 1.859504, "units": 2, "tax": 21, "discount": 0},
    {"name": "[redacted]", "price": 3.9256199999999999, "units": 1, "tax": 21, "discount": 0}
  ]
}
```

The sanitized snapshot SHA-256 is:

```text
3f0099c520131e14c2674a8bd4bde7827f252f4b70d460ce2239d70598847c3d
```

The post-PUT GET returned HTTP `200`. Its sanitized snapshot SHA-256 is:

```text
48edfdffef51693d6748985917d0e573bc430e0b9a2a8368f10179843c02d641
```

The only changed top-level response key was `desc`. The comparison confirmed:

```text
documentId: preserved
docNumber: preserved
currency: preserved
product count and order: preserved
complete product objects: preserved
subtotal: preserved at 9.7200000000000006
tax: preserved at 2.0299999999999998
total: preserved at 11.75
document numeric status: preserved at 0
paymentsTotal: preserved at 0
paymentsPending: preserved at 11.75
paymentsRefunds: preserved at 0
```

Before H3, a fresh GET reproduced the H2 post-PUT body and sanitized hash. After
H3, GET returned HTTP `200`; again, the only key changed relative to the H3
pre-PUT response was `desc`.

The final sanitized snapshot SHA-256 is:

```text
3f0099c520131e14c2674a8bd4bde7827f252f4b70d460ce2239d70598847c3d
```

The final raw JSON body is byte-identical to the original H1 raw GET. Thus the
complete API-visible representation was restored, not only the selected
comparison fields.

## UI verification

Before H2, user inspection of the same document confirmed:

```text
approval state: not approved / unapproved
available action: Aprobar
payment state: pending
pending amount: 11.75 EUR
```

The user explicitly authorized H3 as safe after H2. The current runtime still
cannot independently inspect the UI. A final UI check may confirm that the
description is again `CABINET API TEST`, approval remains unapproved, payment
remains pending at `11.75 EUR`, and no new accounting or audit event appeared.

## Accounting consequences

The API-visible document status, payment fields, lines, taxes, subtotal, and total
did not change after H2 or H3. The API exposed no new accounting or timestamp
field.

The current runtime cannot inspect Holded accounting UI or audit events.
Therefore absence of an invisible accounting or audit consequence is not proven
by API read-back alone.

## Experiment record

```text
experiment_id: H1
observed_at: 2026-08-06T19:31:05Z
HTTP method: GET
sanitized path: /api/invoicing/v1/documents/purchase/{documentId}
sanitized request: no body
HTTP status: 200
sanitized response: recorded above
documentId: 6a74cd787765e9f84a0297d3
numeric status before: 0
numeric status after: 0 (second byte-identical GET)
totals before: subtotal 9.72, tax 2.03, total 11.75 EUR
totals after: unchanged across two GET observations
UI state before: not approved / unapproved; payment pending 11.75 EUR
UI state after: unchanged during H1; no mutation
```

```text
experiment_id: H2
observed_at: 2026-08-06T19:54:07Z through 2026-08-06T19:54:36Z
HTTP method: GET, one PUT, GET
sanitized path: /api/invoicing/v1/documents/purchase/{documentId}
sanitized request: {"desc":"CABINET API TEST PUT METADATA"}
PUT HTTP status: 200
sanitized PUT response: {"status":1,"info":"Updated"}
post-PUT GET HTTP status: 200
documentId: 6a74cd787765e9f84a0297d3
numeric document status before: 0
numeric document status after: 0
totals before: subtotal 9.72, tax 2.03, total 11.75 EUR
totals after: subtotal 9.72, tax 2.03, total 11.75 EUR
UI state before: not approved / unapproved; payment pending 11.75 EUR
UI state after: not independently recorded; H3 subsequently authorized by user
```

```text
experiment_id: H3
observed_at: 2026-08-06T20:02:17Z through 2026-08-06T20:02:39Z
HTTP method: GET, one PUT, GET
sanitized path: /api/invoicing/v1/documents/purchase/{documentId}
sanitized request: {"desc":"CABINET API TEST"}
PUT HTTP status: 200
sanitized PUT response: {"status":1,"info":"Updated"}
post-PUT GET HTTP status: 200
documentId: 6a74cd787765e9f84a0297d3
numeric document status before: 0
numeric document status after: 0
totals before: subtotal 9.72, tax 2.03, total 11.75 EUR
totals after: subtotal 9.72, tax 2.03, total 11.75 EUR
description before: CABINET API TEST PUT METADATA
description after: CABINET API TEST
final raw response matches original H1 response: yes
UI state before: H3 explicitly authorized by user
UI state after: pending optional final verification
```

## Limitations

- Only `status = 0` has a same-document UI correlation.
- Final UI and accounting-event verification is not available to this runtime.
- Reversible partial-update behavior is verified only for `desc` on one
  unapproved purchase.
- Behavior for approved or paid documents remains unknown.
- The API exposed no usable concurrency token or update version.
- No financial PUT behavior was tested.

## Remaining questions

1. Does the final UI preserve the unapproved and pending states after H2 and H3?
2. Did H2 or H3 create any accounting or audit event visible in Holded?
3. Does partial-update behavior remain safe for approved or paid documents?
4. Which other numeric status values map to which visible UI states?
5. Which financial changes are accepted, and what accounting consequences do
   they have?

## Current answers

1. For this document, numeric `status = 0` means not approved / unapproved.
2. A `desc`-only PUT succeeds on this unapproved purchase.
3. Identifier, number, complete ordered products, taxes, totals, document status,
   and payment fields were preserved in API read-back.
4. No API-visible accounting state changed; UI accounting consequences remain to
   be checked independently.
5. PUT behaves as a reversible partial update for the observed `desc`-only
   requests. H3 restored a raw response byte-identical to H1.
6. Metadata PUT is safe at the verified API-data level for changing `desc` on
   this unapproved test purchase. This evidence does not justify general PUT
   reconciliation, approved-document updates, or financial changes.
7. No financial mutation should be attempted before a separate plan covers
   approved-state behavior, line/tax/total read-back, accounting entries,
   concurrency, and correction strategy.
8. Evidence is sufficient for a narrowly scoped factual statement about
   unapproved `desc` updates, but remains insufficient for a normative Invoice
   Card reconciliation rule.
