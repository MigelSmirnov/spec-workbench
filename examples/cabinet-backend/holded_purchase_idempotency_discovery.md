# Holded purchase create idempotency discovery

## Status

Partial factual discovery and controlled runtime-test plan.

The official contract and read-only list behavior have been inspected. No POST,
PUT, DELETE, attachment, payment, approval, or `purchaserefund` request was
executed during this phase.

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
API family: Holded invoicing v1
credential source: HOLDED_V1_API_KEY from /home/smirnov/jestor_VBC/.env
credential value: not recorded
transport: HTTPS
```

Neither the API key nor authorization headers were printed or stored in this
repository.

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
7. The current test document proves list visibility after successful creation,
   but does not measure immediate visibility or eventual-consistency delay.

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

## Controlled mutation experiment required

One new isolated test purchase is required to verify recovery. It must be marked
`CABINET API TEST` and use a unique attempt marker.

Proposed sequence:

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

1. Does a unique marker in `desc` survive create and appear immediately in list?
2. How many list requests, if any, are needed before a new purchase is visible?
3. Can tags or custom fields carry a cleaner stable attempt marker?
4. Does Holded reject or allow a second purchase with the same supplier invoice
   number?
5. Is any undocumented idempotency header supported and contractually stable?
6. How should list polling be bounded when no rate-limit headers are returned?
7. Can approved or paid documents still be correlated by the same marker?

## Current decision boundary

Cabinet Backend must not automatically retry an ambiguous create request.

Read-only evidence supports a candidate marker-and-list recovery design, but one
controlled create experiment is still required before that design becomes a
normative duplicate-prevention rule.
