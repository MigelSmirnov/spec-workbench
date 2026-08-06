# Cabinet Backend — Holded Purchase Create Recovery

## Status

Accepted clarification for `02_rules.md`.

This rule is based on completed runtime discovery against the Holded invoicing
v1 purchase API.

It defines recovery of an ambiguous purchase-create outcome without repeating
POST.

It does not define update, refund, deletion, attachment, approval, payment, or
revision-reconciliation behavior.

---

## Verified runtime facts

The completed discovery established:

1. Holded does not document a native idempotency key for purchase creation.
2. A unique non-financial attempt marker stored in `desc` survives purchase
   creation.
3. The marker is returned by the purchase list endpoint and by GET of the
   resulting document.
4. A purchase created exactly once can be recovered by:
   - list;
   - exact marker match;
   - GET of the recovered `documentId`;
   - full business-field verification.
5. Recovery succeeded without using the POST response.
6. No second POST was required.
7. A recovered document with a payload mismatch correctly produced
   `reconciliation_required`.
8. A recovered document with a complete payload match correctly produced
   `created_and_recovered`.
9. Zero marker matches are not evidence that the POST definitely failed.
10. Automatic retry after an ambiguous create outcome is unsafe.

---

## Accepted decision — marker-based create recovery

Every Holded purchase publication attempt has a unique stable local
`publication_attempt_id`.

Before the first POST, Cabinet Backend persists the attempt record and derives a
unique non-financial marker.

Example:

```text
CABINET API TEST ATTEMPT <publication_attempt_id>
```

Production formatting may differ, but the marker must remain unique,
deterministic for the attempt, and retrievable from Holded list and GET
representations.

---

## Publication attempt record

Before POST, Backend stores at least:

```text
publication_attempt_id
invoice_id
invoice_revision_hash
canonical_holded_payload_hash
attempt_marker
request_started_at
attempt_state
```

It may also store:

```text
request_finished_at
timeout_at
created_before
error_code
error_message
```

The attempt record must exist before network mutation begins.

---

## First POST rule

For one logical publication attempt:

```text
maximum automatic POST count = 1
```

The create request includes the unique attempt marker in a verified
non-financial field.

The current accepted field is:

```text
desc
```

The marker must not alter financial meaning.

---

## Normal successful response

When POST returns a clear successful response containing `documentId`, Backend
continues with the verification rules defined by A51.

The attempt marker remains part of publication evidence.

---

## Ambiguous create outcome

An outcome is ambiguous when Backend cannot prove whether Holded created the
purchase, for example after:

```text
connection loss
client timeout
response loss
process interruption after request delivery
```

Backend must not send a second POST automatically.

Instead it enters recovery.

---

## Recovery sequence

Recovery is read-only:

1. Load the persisted `publication_attempt_id`.
2. Load the exact attempt marker.
3. Perform bounded polling of the Holded purchase list.
4. Filter locally for the exact marker.
5. Classify the marker-match count.
6. If exactly one match exists, obtain its `documentId`.
7. GET that exact document.
8. Perform complete business-field verification against the stored publication
   attempt.
9. Bind the Holded document to the Invoice Card revision only after successful
   verification.

Recovery itself must not perform:

```text
POST
PUT
DELETE
approval
payment
attachment
refund
```

---

## Deterministic recovery outcomes

### Exactly one marker match and complete business match

```text
outcome = created_and_recovered
```

Backend records:

```text
holded_document_id
invoice_id
invoice_revision_hash
publication_attempt_id
verified_at
```

The recovered document becomes the publication record for that exact Invoice Card
revision.

### Exactly one marker match but payload mismatch

```text
outcome = reconciliation_required
holded_reconciliation_required = true
```

Backend preserves both local expected evidence and the recovered Holded
representation.

It must not correct the Holded document automatically.

### Zero marker matches within the bounded recovery window

```text
outcome = outcome_unknown
```

This state requires manual review.

Zero matches must not authorize another automatic POST.

### More than one exact marker match

```text
outcome = duplicate_conflict
holded_reconciliation_required = true
```

Backend must not choose one candidate automatically.

---

## Required business verification

A marker match alone is never sufficient.

The recovered document must be verified according to A51, including at least:

```text
supplier identity
supplier invoice number
document date
currency
line count
line order
line names
line quantities
line tax rates
gross total
```

The gross total must match within accepted currency precision.

Holded-specific intermediate rounding remains governed by A51.

---

## Marker semantics

The attempt marker is a correlation token, not a business identifier.

It must not replace:

```text
invoice_id
invoice_revision_hash
holded_document_id
supplier invoice number
```

Two legitimate invoices may share supplier, date, amount, or invoice number in
ways that are not sufficient for idempotency.

Backend must not use payload similarity without an exact marker as create
recovery proof.

---

## Bounded polling

Recovery polling must be finite.

The exact polling interval and maximum duration belong to implementation
configuration.

The normative outcomes after the bounded window are:

```text
1 verified match -> created_and_recovered
1 mismatched match -> reconciliation_required
0 matches -> outcome_unknown
>1 matches -> duplicate_conflict
```

A longer wait or manual inspection may later resolve `outcome_unknown`, but the
Backend must not turn that state into an automatic retry permission.

---

## Retry policy

Automatic create retry is prohibited for an ambiguous attempt.

A new POST may occur only after an explicit manual decision that establishes a
new logical publication attempt.

Such a new attempt must receive:

```text
new publication_attempt_id
new attempt marker
new audit record
```

The old attempt remains preserved.

---

## Audit requirements

Every publication attempt and recovery action records:

```text
publication_attempt_id
invoice_id
invoice_revision_hash
actor
attempt_marker
request_started_at
request_outcome
recovery_started_at
marker_match_count
recovered_document_id
verification_result
final_attempt_state
```

Audit evidence is append-only.

---

## Formal invariants

Single automatic create:

```text
one publication_attempt_id -> at most one automatic POST
```

Recovery correlation:

```text
recovered candidate -> exact attempt marker match
```

Successful recovery:

```text
created_and_recovered
-> exactly one marker match
-> GET succeeded
-> complete A51 verification passed
```

No retry from absence:

```text
zero marker matches != proof of failed POST
```

Mismatch handling:

```text
marker match + payload mismatch
-> reconciliation_required
```

---

## Required tests

1. Attempt state is persisted before POST.
2. Exactly one automatic POST is issued per publication attempt.
3. A successful POST-created purchase can be recovered using only list and GET.
4. Recovery does not use the saved POST response.
5. One marker match with complete payload verification produces
   `created_and_recovered`.
6. One marker match with a financial mismatch produces
   `reconciliation_required`.
7. Zero marker matches produce `outcome_unknown`.
8. Zero marker matches do not trigger another POST.
9. Multiple marker matches produce `duplicate_conflict`.
10. Marker match alone cannot produce publication success.
11. Gross mismatch prevents successful binding.
12. Recovery performs no mutation.
13. Manual retry creates a new attempt ID and marker.
14. Previous ambiguous attempts remain auditable.
15. Repeating recovery reads is idempotent.

---

## Scope limitation

This decision applies only to recovery of purchase creation.

It does not establish:

- server-side idempotency in Holded;
- PUT safety for financial fields;
- approved or paid document mutation;
- refund or rectification behavior;
- attachment behavior;
- revision reconciliation.

Those remain separate Holded concerns.

---

## Consequence

Cabinet Backend can safely recover a purchase that may already have been created
without risking an automatic duplicate POST.

The publication attempt marker provides correlation, while complete business
verification determines whether the recovered document may be accepted or must
enter reconciliation.
