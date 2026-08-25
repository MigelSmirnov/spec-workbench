# Holded purchase create idempotency discovery

## Status

Complete factual discovery of marker-based create recovery.

The official contract and read-only list behavior were inspected. Exactly one
isolated test purchase POST was executed with a unique attempt marker. Recovery
used list and GET only; no second POST was sent.

The marker was recovered exactly once, but full verification found a financial
payload mismatch. The deterministic outcome is `reconciliation_required`, not
`created_and_recovered`.

A second separately authorized test used corrected net unit amounts, a new
marker, and exactly one new POST. List recovered exactly one document and GET
passed the complete accepted verification baseline. Its deterministic outcome is
`created_and_recovered`.

No PUT, DELETE, attachment, payment, approval, or `purchaserefund` request was
executed.

This document is factual evidence and an experiment plan. It is not a normative
Cabinet Backend rule.

---

## Goal

Determine how Cabinet Backend can recover from an ambiguous create-purchase
outcome without risking a second POST.

The required distinction is:

```text
definitely not created
created exactly once but response was lost
ambiguous and still unsafe to retry
duplicate candidates already exist
```

## Environment

```text
observed_at: 2026-08-06T20:13:14Z
pre-create list: 2026-08-06T20:26:04Z
single POST: 2026-08-06T20:26:13Z
first recovery list: 2026-08-06T20:26:23.199Z
recovered document GET: 2026-08-06T20:26:40.020Z
successful pre-create list: 2026-08-06T20:34:26.972Z
successful single POST: 2026-08-06T20:34:34.620Z
successful first recovery list: 2026-08-06T20:34:45.190Z
successful recovered document GET: 2026-08-06T20:35:05.357Z
API family: Holded invoicing v1
credential source: HOLDED_V1_API_KEY from /home/smirnov/jestor_VBC/.env
credential value: not recorded
transport: HTTPS
```

Neither the API key nor authorization headers were printed or stored in this
repository.

## Observed transport envelope

The successful recovery experiment is identified as
`holded-v1-success-530df579-20260806T203434Z`. Its sanitized request envelope
confirmed the following facts for the tested Holded Invoicing V1 account:

```text
origin: https://api.holded.com
credential header name: key
credential value source: HOLDED_V1_API_KEY
create: POST /api/invoicing/v1/documents/purchase
list: GET /api/invoicing/v1/documents/purchase
exact document: GET /api/invoicing/v1/documents/purchase/{documentId}
```

The credential value was expanded only by the request process. It is absent
from the saved command transcript, this evidence document, and the specification.

## Official API contract

Create uses:

```text
POST /api/invoicing/v1/documents/{docType}
```

The documented create body supports candidate correlation fields including:

```text
desc
notes
customFields
invoiceNum
tags
```

The official create reference does not document:

- an idempotency-key request header;
- a client-supplied document ID;
- uniqueness enforcement for `invoiceNum`;
- an external-reference field with uniqueness semantics;
- replay behavior for an identical POST;
- recovery semantics after a timeout.

List uses:

```text
GET /api/invoicing/v1/documents/{docType}
```

Its documented filters are limited to:

```text
starttmp
endtmp
contactid
paid
billed
sort
```

No documented server-side filter exists for `invoiceNum`, `desc`, tags, custom
fields, payload hash, or a Cabinet publication-attempt identifier.

Official references:

- https://developers.holded.com/reference/create-document-1
- https://developers.holded.com/reference/list-documents-1
- https://developers.holded.com/reference/getdocument-1

## Read-only runtime observation

Two consecutive requests were performed:

```text
GET /api/invoicing/v1/documents/purchase
HTTP status: 200
response type: array
document count: 1
responses byte-identical: yes
```

The existing isolated test purchase appeared exactly once in the list:

```text
documentId: 6a74cd787765e9f84a0297d3
desc: CABINET API TEST
docNumber: 036-0008-424824
currency: eur
numeric status: 0
subtotal: 9.72
tax: 2.03
total: 11.75
paymentsTotal: 0
paymentsPending: 11.75
product count: 3
```

The list representation included the same top-level fields as direct GET,
including `id`, `desc`, `docNumber`, `products`, totals, payment fields, tags,
and custom fields.

The test document currently has no tag, custom field, or note marker. Its
description is the only explicit `CABINET API TEST` marker.

No rate-limit or `Retry-After` header was exposed by the observed list responses.

## Current factual conclusions

1. The public API does not advertise native create idempotency.
2. A lost create response cannot be recovered by GET-by-ID because the client
   does not yet know the Holded document ID.
3. List returns enough document content for client-side correlation.
4. List does not document a server-side filter for a unique Cabinet attempt
   marker.
5. `invoiceNum` alone is not proven unique and must not be treated as an
   idempotency key.
6. Supplier, amount, date, lines, or payload similarity alone are unsafe because
   two legitimate purchases may share them.
7. A unique `desc` marker survived create and was returned by both list and GET.
8. The new purchase appeared exactly once in the first recovery list request,
   approximately ten seconds after POST completion.
9. Finding one marker is not sufficient publication success; the recovered
   document still requires complete business-field verification.
10. With corrected net unit amounts, one marker match plus complete GET
    verification produced `created_and_recovered`.

## Candidate recovery protocol

Before the first POST, Cabinet Backend would persist locally:

```text
publication_attempt_id
invoice_id
invoice_revision_hash
canonical_holded_payload_hash
created_before
request_started_at
request_finished_at or timeout_at
attempt_state
```

The first and only POST would carry a unique non-financial marker derived from
`publication_attempt_id`. The marker must be verified as persisted and returned
by list and GET before this protocol can be accepted.

After an ambiguous response, Backend would not repeat POST. It would:

1. perform bounded read-only list polling;
2. filter locally for the exact unique attempt marker;
3. require exactly one candidate;
4. GET that candidate by returned `documentId`;
5. compare its canonical business fields with the stored payload hash inputs;
6. bind the local publication attempt only after exact verification.

Deterministic outcomes would be:

```text
one exact verified candidate -> created_and_recovered
zero candidates within bounded window -> outcome_unknown, manual review
more than one marker match -> duplicate_conflict, manual review
one marker match with payload mismatch -> reconciliation_required
```

Zero candidates must not authorize an automatic second POST because list
visibility delay and request-delivery ambiguity remain unproven.

## Controlled mutation experiment

One new isolated test purchase was authorized to verify recovery. It was marked
`CABINET API TEST` and used a unique attempt marker.

Executed sequence:

1. Generate and persist one unique `publication_attempt_id` locally.
2. Confirm by list that the marker does not already exist.
3. Build one purchase from the existing validated Cabinet fixture.
4. Add the attempt marker only to a chosen non-financial field.
5. Send exactly one POST and save the response for experiment evidence.
6. Run recovery logic as if the POST response were unavailable.
7. Poll list read-only with a small bounded request count.
8. Require exactly one marker match.
9. GET the returned ID and verify the complete purchase representation.
10. Do not repeat POST under any outcome.

The safest first candidate field is `desc`, because create accepts it and the
current runtime already proves that list and GET return it. A tag or custom field
could be cleaner but its exact create schema, persistence, visibility, and search
behavior are not yet verified.

The experiment should not deliberately force a transport timeout. Saving a
successful response for evidence while withholding it from the recovery routine
tests the same post-condition without adding network-delivery uncertainty.

## Controlled mutation result

The local attempt record was persisted before POST:

```text
publication_attempt_id: c3cd678a-f545-42d4-b865-d85f56d3e1a1
marker: CABINET API TEST ATTEMPT c3cd678a-f545-42d4-b865-d85f56d3e1a1
invoiceNum: CAB-ATT-C3CD678AF545
payload SHA-256: d764b3450bfef490acff4ebd59466e51e68aed31e208de07b1387e91fba3c5f7
preexisting marker matches: 0
```

The sanitized payload used an existing Holded contact and the three lines from
the validated Cabinet fixture:

```json
{
  "applyContactDefaults": false,
  "contactId": "[redacted-existing-contact-id]",
  "desc": "CABINET API TEST ATTEMPT c3cd678a-f545-42d4-b865-d85f56d3e1a1",
  "date": 1785535200,
  "approveDoc": false,
  "items": [
    {"name":"[redacted]","units":1,"subtotal":2.50,"discount":0,"tax":21,"sku":"[redacted]"},
    {"name":"[redacted]","units":2,"subtotal":2.25,"discount":0,"tax":21,"sku":"[redacted]"},
    {"name":"[redacted]","units":1,"subtotal":4.75,"discount":0,"tax":21,"sku":"[redacted]"}
  ],
  "invoiceNum": "CAB-ATT-C3CD678AF545",
  "currency": "eur"
}
```

Exactly one POST was sent:

```text
HTTP status: 200
curl exit: 0
sanitized response keys: contactId, id, invoiceNum, status
returned documentId: 6a74ede5958487ce530173e3
returned operation status: 1
automatic retry: no
```

The saved POST response was not used by the recovery procedure. The first list
request returned:

```text
HTTP status: 200
exact marker matches: 1
recovered documentId: 6a74ede5958487ce530173e3
```

The independently recovered ID matched the ID in the saved POST response.

GET of the recovered ID returned HTTP `200`. Verification found:

```text
marker: matches
invoiceNum: matches
currency: matches
line count: matches
line names and order: match
line quantities: match
line tax rates: match
expected fixture gross total: 11.75
returned subtotal: 11.75
returned tax: 2.48
returned gross total: 14.23
returned paymentsPending: 14.23
financial match: false
```

The request incorrectly supplied gross unit amounts in item `subtotal`. Holded
interpreted them as net unit prices and added IVA, producing `14.23`.

The recovery procedure therefore produced:

```text
one exact marker match
and payload mismatch
-> reconciliation_required
```

No second POST or corrective mutation was executed. The recovered test purchase
remains unapproved with numeric status `0` and gross total `14.23 EUR`.

## Successful recovery experiment

A second, separately authorized attempt used corrected net unit amounts derived
from the previously verified Holded representation:

```text
publication_attempt_id: 530df579-60e9-4d07-86dc-f6e9901203fe
marker: CABINET API TEST ATTEMPT 530df579-60e9-4d07-86dc-f6e9901203fe
invoiceNum: CAB-ATT-530DF57960E9
payload SHA-256: f4936fb479a5b43e3ade27a19a628eee93df009a99dbaa79dac06d51c2f5547a
preexisting marker matches: 0
expected gross total: 11.75 EUR
```

Sanitized item amounts were:

```json
[
  {"units":1,"subtotal":2.066116,"discount":0,"tax":21},
  {"units":2,"subtotal":1.859504,"discount":0,"tax":21},
  {"units":1,"subtotal":3.925620,"discount":0,"tax":21}
]
```

Their unrounded calculated gross was `11.75000024`, which is `11.75 EUR` at
currency precision.

Exactly one POST was sent:

```text
HTTP status: 200
curl exit: 0
returned documentId: 6a74efda0f9c6caac8027342
returned operation status: 1
automatic retry: no
```

The saved POST response was withheld from the recovery procedure. The first list
request, approximately ten seconds after POST completion, returned:

```text
HTTP status: 200
exact marker matches: 1
recovered documentId: 6a74efda0f9c6caac8027342
```

The independently recovered ID matched the saved POST response. GET of that ID
returned HTTP `200` and confirmed:

```text
marker: matches
existing contact: matches
invoiceNum: matches
date: matches
currency: matches
line count: matches
line names, descriptions, and order: match
line quantities: match
line tax rates: match
net unit values: numerically equivalent
returned subtotal: 9.72
returned tax: 2.03
returned gross total: 11.75
expected gross total: 11.75
numeric document status: 0
paymentsPending: 11.75
complete accepted baseline match: true
```

The recovery procedure therefore produced:

```text
one exact marker match
and complete payload match
-> created_and_recovered
```

No second POST, PUT, DELETE, approval, payment, attachment, or refund operation
was executed.

## Safety constraints for the mutation phase

- Exactly one new POST is allowed after explicit approval of its payload.
- The document must be visibly marked `CABINET API TEST`.
- No automatic POST retry is allowed.
- No DELETE or `purchaserefund` is allowed.
- No supplier, product, contact, or other entity is created separately.
- No approval or payment operation is allowed.
- Recovery uses GET requests only.
- A zero-match or multi-match outcome stops for manual review.

## Remaining questions

1. Is a new purchase visible sooner than the observed approximately ten-second
   first recovery check, and can visibility ever be delayed longer?
2. Can tags or custom fields carry a cleaner stable attempt marker?
3. Does Holded reject or allow a second purchase with the same supplier invoice
   number?
4. Is any undocumented idempotency header supported and contractually stable?
5. How should list polling be bounded when no rate-limit headers are returned?
6. Can approved or paid documents still be correlated by the same marker?

## Current decision boundary

Cabinet Backend must not automatically retry an ambiguous create request.

Runtime evidence confirms that an exact unique `desc` marker can recover one
created purchase through list and GET without repeating POST. It also confirms
that marker recovery must be followed by complete payload verification: one
experiment correctly produced `reconciliation_required`, while the corrected
experiment produced `created_and_recovered`.

The evidence is sufficient to formulate a stable marker-based recovery rule for
the tested unapproved purchase-create flow. It does not establish native Holded
idempotency and must never authorize a repeated POST after zero matches.
