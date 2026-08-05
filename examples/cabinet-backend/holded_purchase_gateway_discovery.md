# Holded purchase gateway discovery for Cabinet Backend

## Status

Factual reconnaissance baseline and verification plan for a dedicated Cabinet
Backend integration with Holded purchase documents.

This document does not define the final Holded gateway contract and does not
claim support for operations that have not been verified against the real Holded
purchase API.

---

## Confirmed findings from the existing PresuPro integration

The current PresuPro integration cannot be reused as the Cabinet purchase
integration.

### Existing PresuPro behavior

- PresuPro exposes no Holded MCP tools.
- Holded is called through the PresuPro HTTP endpoint:

  ```text
  POST /estimates/{estimate_id}/convert
  ```

- The existing adapter supports only:

  ```text
  estimate
  invoice
  proform
  ```

- The adapter does not support:

  ```text
  purchase
  purchaserefund
  ```

- The implementation creates Holded records through `POST`.
- Update, delete, correction, and reconciliation operations are not implemented.
- PresuPro uses the Holded API v2 routes for invoices, estimates, and proformas.
- After successful creation, PresuPro stores an `InvoiceRef` and blocks the
  estimate.
- The existing integration tests cover the implemented PresuPro layer, not the
  Cabinet purchase workflow.
- No real Holded purchase operation has been executed during this discovery.

### Reusable parts

The PresuPro adapter may be used only as a technical reference for:

- authentication;
- HTTP client setup;
- error mapping;
- request logging;
- retry boundaries;
- response parsing patterns.

Its document semantics must not be reused for Cabinet purchases without separate
verification.

---

## Required Cabinet integration boundary

Cabinet Backend requires a dedicated Holded gateway for supplier purchase
documents.

The gateway is owned by Cabinet Backend and is independent from PresuPro's
estimate conversion workflow.

### Candidate gateway capabilities

The following operations are candidates only and require verification before
becoming normative:

```text
create_purchase
get_purchase
update_purchase
create_purchase_refund
```

The following Backend responsibilities are already required regardless of the
final Holded API shape:

```text
record_publication
link_publication_to_invoice_revision
detect_revision_mismatch
mark_reconciliation_required
preserve_publication_history
```

---

## Safe baseline before runtime verification

Until the real Holded purchase API is verified, Cabinet Backend follows these
rules:

1. A Holded publication is linked to one exact immutable Invoice Card revision.
2. Backend stores the Holded document identifier returned by successful
   publication.
3. A later Invoice Card revision does not silently overwrite the previously
   published Holded document.
4. Backend detects when the current accepted Invoice Card revision differs from
   the published revision.
5. Such a mismatch produces:

   ```text
   holded_reconciliation_required = true
   ```

6. No automatic update, refund, deletion, or second purchase is performed until
   the applicable Holded operation is known and explicitly accepted.
7. PresuPro does not own this reconciliation decision.
8. Failure to publish to Holded does not modify or invalidate the accepted
   Invoice Card revision.

---

## Minimum publication record

Cabinet Backend must be able to preserve at least:

```text
invoice_id
invoice_revision_hash
holded_document_id
holded_document_type
published_at
publication_status
request_fingerprint
response_reference
```

Optional operational evidence may include:

```text
actor
attempt_number
error_code
error_message
last_checked_at
```

The final storage model belongs to the implementation specification.

---

## Runtime discovery required

The following checks must be performed against a real or isolated Holded test
account before accepting the final gateway contract.

### Authentication and environment

1. Confirm the authentication mechanism for purchase-document endpoints.
2. Confirm API base URL and version.
3. Confirm whether a sandbox or isolated test organization is available.
4. Confirm rate limits and retry guidance.
5. Confirm idempotency support or the absence of it.

### Purchase creation

1. Identify the exact endpoint for creating a supplier purchase.
2. Capture the minimal valid request.
3. Capture the returned document identifier.
4. Confirm supported fields for:
   - supplier;
   - supplier invoice number;
   - date;
   - due date;
   - currency;
   - tax;
   - lines;
   - expense accounts;
   - attachments;
   - notes;
   - custom fields.
5. Confirm whether duplicate supplier invoice numbers are accepted.
6. Confirm whether the API exposes draft, approved, paid, or posted states.

### Purchase retrieval

1. Identify the exact endpoint for reading a purchase.
2. Confirm whether the response exposes current accounting status.
3. Confirm whether the response exposes modification timestamps or versions.
4. Confirm whether linked attachments can be retrieved or enumerated.

### Purchase update

1. Confirm whether existing purchases can be updated.
2. Test updates separately for:
   - description or notes;
   - supplier invoice number;
   - date;
   - supplier;
   - lines;
   - tax;
   - total amount.
3. Confirm which states prohibit update.
4. Confirm whether update rewrites, reverses, or regenerates accounting entries.
5. Confirm whether concurrent update protection exists.

### Purchase correction or refund

1. Identify whether Holded supports a supplier purchase correction or refund API.
2. Confirm the exact document type and endpoint.
3. Confirm whether the correction is linked to the original purchase.
4. Confirm whether partial correction is supported.
5. Confirm required signs, amounts, taxes, and references.
6. Confirm resulting accounting behavior.

### Deletion and cancellation

1. Confirm whether a purchase can be deleted or cancelled.
2. Confirm state restrictions.
3. Confirm whether deletion removes accounting evidence or creates a reversal.
4. Cabinet Backend must not use deletion automatically even if the API permits it.

### Attachments

1. Confirm whether invoice source files can be attached during creation.
2. Confirm whether files can be attached later.
3. Confirm supported media types and size limits.
4. Confirm whether attachment hashes or identifiers are exposed.
5. Confirm whether attachments survive purchase update or correction.

### Error and retry behavior

1. Capture validation errors.
2. Capture authentication and authorization failures.
3. Capture rate-limit behavior.
4. Capture duplicate or conflict behavior.
5. Capture timeout behavior.
6. Verify whether retrying the same request can create duplicate purchases.

---

## Evidence to record

Each runtime experiment must record:

```text
experiment_id
environment
request method and path
sanitized request body
HTTP status
sanitized response body
created Holded identifiers
visible UI result
accounting result
repeat-request result
cleanup result
observed_at
```

Secrets, API keys, supplier personal data, and production accounting data must not
be committed to the repository.

---

## Decision outcomes expected after discovery

The discovery should allow Cabinet Backend to decide:

1. whether `create_purchase` is supported;
2. whether publications can be made technically idempotent;
3. whether a published purchase may be updated safely;
4. which field changes require reconciliation;
5. whether `purchaserefund` or an equivalent correction operation exists;
6. whether attachments can be managed through the API;
7. whether reconciliation remains manual or can be partly automated;
8. which Holded states must block mutation.

---

## Open questions

1. What is the authoritative Holded purchase API version and endpoint family?
2. Is supplier purchase creation available to the current Holded plan and API
   credentials?
3. Can an existing purchase be updated after accounting approval or payment?
4. Is there an API operation equivalent to a purchase rectification?
5. How does Holded represent the relationship between a correction and its source
   purchase?
6. What fields are safe to update without accounting consequences?
7. Does Holded provide an idempotency key, external reference, or searchable
   custom field suitable for duplicate prevention?
8. Can source PDFs or images be attached and verified through the API?

---

## Consequence

Cabinet Backend requires its own Holded purchase gateway.

The existing PresuPro adapter is a useful implementation reference, but it does
not define purchase semantics and does not solve invoice revision reconciliation.

No automatic correction behavior may be accepted until the real purchase API has
been verified.
