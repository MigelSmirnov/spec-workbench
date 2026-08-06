# Holded purchase status and PUT discovery

## Status

Partial factual runtime discovery.

The read-only H1 observation is reproducible. The run stopped before H2 because
the current runtime has no authenticated Holded UI session and therefore cannot
correlate numeric API status with the visible state of the same document.

No POST, PUT, DELETE, attachment, or `purchaserefund` request was executed.

This document is factual evidence, not a normative Cabinet Backend rule.

---

## Environment

```text
observed_at: 2026-08-06T19:31:05Z
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

The payment fields show that the full amount remained pending at observation
time. They do not prove whether the document was visibly draft, approved,
cancelled, or in another Holded UI state.

No semantic label is assigned to `status = 0` because the same document could not
be inspected in an authenticated Holded UI session from this runtime.

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

## Metadata PUT result

Not executed.

H2 was blocked by the explicit stop condition: the numeric status could not be
correlated with the visible UI state before mutation. Consequently H3 was also
not executed.

The intended H2 request remains:

```json
{
  "desc": "CABINET API TEST PUT METADATA"
}
```

This payload was not sent.

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

## UI verification

Not available in the current runtime. No authenticated Holded browser session or
safe UI automation capability was available.

Required next evidence is the visible state of document
`6a74cd787765e9f84a0297d3` in Holded immediately before H2, selected from:

```text
draft
approved
paid
partially paid
cancelled
other
```

## Accounting consequences

No mutation occurred, so no accounting event or state change was produced by
this run.

The current API response is insufficient to prove whether a metadata-only PUT
would create or alter accounting entries.

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
UI state before: not verified
UI state after: not applicable; no mutation
```

## Limitations

- Numeric status semantics remain unknown without same-document UI correlation.
- Metadata PUT was not executed.
- PUT replacement versus patch behavior remains unknown.
- Accounting consequences remain unknown.
- The API exposed no usable concurrency token or update version.
- No financial PUT behavior was tested.

## Remaining questions

1. What visible Holded UI state corresponds to `status = 0` for this document?
2. Does a `desc`-only PUT preserve identifier, number, products, taxes, totals,
   payment fields, and UI state?
3. Does reverting the description produce the same preservation result?
4. Is PUT partial in practice, despite the operation being named PUT?
5. Does metadata PUT create any accounting event or audit entry?
6. Which financial changes are accepted, and what accounting consequences do
   they have?

## Current answers

1. Numeric `status = 0` was observed, but its UI meaning is not yet proven.
2. Description-only update is documented as syntactically supported but was not
   executed.
3. Preservation after metadata PUT is not yet proven.
4. Accounting state was unchanged because no PUT occurred; PUT consequences are
   unknown.
5. Full-replacement versus partial-update semantics remain undocumented and
   untested.
6. Metadata PUT cannot yet be declared safe for Cabinet Backend.
7. UI correlation, H2/H3 read-back comparison, and accounting-event inspection
   are required before any financial-field test plan is considered.
8. Evidence is insufficient for a new normative rule.
