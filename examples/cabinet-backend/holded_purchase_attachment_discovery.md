# Holded purchase attachment discovery

## Status

Complete read-only factual discovery. The attachment mutation was not executed.

The legacy Holded Invoicing v1 reference confirms that an attachment endpoint
exists, but it does not define the request body or encoding. The Cabinet Invoice
Card fixture also declares that its source binary is not stored, and no PDF or
image fixture exists in the scoped Cabinet project. These two conditions trigger
the experiment's stop rule.

```text
result: mutation_not_executed_contract_ambiguous
attachment uploads executed: 0
purchase POST/PUT/DELETE executed: 0
approval/payment/refund operations executed: 0
```

This document is factual evidence, not a normative Cabinet Backend rule.

---

## Environment

```text
observed_at: 2026-08-06T22:51:01+02:00
runtime: local Cabinet/spec-workbench environment
credential source: HOLDED_V1_API_KEY from /home/smirnov/jestor_VBC/.env
credential value: not recorded
transport: HTTPS
```

The configured credential was present and non-empty. Neither the credential nor
the authorization header was printed or stored in this repository.

## Official contract

### Legacy Invoicing v1

The archived official v1 reference documents:

```text
POST /api/invoicing/v1/documents/{docType}/{documentId}/attach
required path parameters: docType, documentId
document type for this experiment: purchase
documented success status: HTTP 200
documented response example: {"status":1,"data":"<base64 file content>"}
```

A read-only `OPTIONS` request to the exact test-document path returned HTTP
`200`, `Allow: POST`, an empty body, and no request-format metadata.

The v1 reference does **not** specify:

- a request body schema;
- whether the upload is `multipart/form-data`, base64 JSON, or another format;
- the upload field name;
- accepted MIME types or maximum size;
- whether several attachments are supported;
- an attachment list endpoint for documents;
- an attachment download endpoint for documents;
- an attachment ID, filename, media type, size, or hash in the response;
- attachment behavior after an ordinary document PUT.

The v1 index separately documents list/download operations for contact
attachments. It does not list equivalent operations for document attachments,
so the contact routes are not evidence for a purchase route.

Official v1 references:

- https://www.holded.com/es/desarrolladores/v1
- https://www.holded.com/es/desarrolladores/v1/invoice-api/documents/attach-file

### Current API v2

The current official API has a different, explicit purchase attachment
contract:

```text
POST /api/v2/purchases/{purchaseId}/attachments
request: multipart/form-data, field file (binary)
success: HTTP 201 with attachment id

GET /api/v2/purchases/{purchaseId}/attachments
GET /api/v2/purchases/{purchaseId}/attachments/{attachmentId}
```

The download response is documented as binary `application/octet-stream`.
However, v2 uses different endpoints, authorization scopes, and authentication.
It does not resolve the missing v1 request contract and was not called with the
v1 credential in this experiment.

Official v2 references:

- https://www.holded.com/es/desarrolladores/referencia-api/compras/adjuntar-un-archivo-a-una-compra
- https://www.holded.com/es/desarrolladores/referencia-api/compras/listar-adjuntos-de-compra
- https://www.holded.com/es/desarrolladores/referencia-api/compras/obtener-adjunto-de-compra

## Endpoint and method

The only authenticated runtime calls were read-only:

```text
GET /api/invoicing/v1/documents/purchase/{documentId} -> HTTP 200
OPTIONS /api/invoicing/v1/documents/purchase/{documentId}/attach -> HTTP 200
OPTIONS Allow -> POST
```

No request was sent with method POST, PUT, PATCH, or DELETE.

## Request format

No v1 request payload was constructed or sent. Inferring multipart encoding
from the v2 endpoint or from common upload conventions would not be an
unambiguous v1 contract.

The documented v1 response's base64 `data` field describes the response example;
it is not evidence that the request accepts base64.

## Test document

The supplied existing test purchase was confirmed through v1 GET:

```text
documentId: 6a74cd787765e9f84a0297d3
document type requested: purchase
description: CABINET API TEST
docNumber: 036-0008-424824
currency: eur
status: 0
approvedAt: null
draft: null
product lines: 3
subtotal: 9.7200000000000006
tax: 2.0299999999999998
total: 11.75
paymentsTotal: 0
paymentsPending: 11.75
paymentsRefunds: 0
```

The sanitized preflight snapshot SHA-256 is:

```text
ffd6d1824e220a0aa2483c268dec8f13c5ed6de4820ccf86a3e549f047fea231
```

The document GET contained no top-level key whose name matched `attach` or
`file`. It therefore did not expose a current attachment list.

## Source-file evidence

The existing Invoice Card fixture inspected was:

```text
/home/smirnov/jestor_VBC/exp_vbc/demo/code_factory/projects/Cabinet_web/tests/fixtures/invoices/obramat-cash/card.json
```

Its source declaration is:

```text
source.kind: photo
source.file_status: not_stored
source.file_ref: null
```

The fixture directory contains only `card.json`. A scoped search of the Cabinet
project and `examples/cabinet-backend` found no PDF, PNG, JPEG, WebP, or TIFF
file. Consequently these required values cannot truthfully be produced from an
existing fixture:

```text
source_filename: unavailable
source_media_type: unavailable
source_size: unavailable
source_sha256: unavailable
target_holded_document_id: 6a74cd787765e9f84a0297d3
```

No file was created, copied, or modified as a substitute.

## Upload result

Not executed. The v1 request format is undocumented and the required existing
fixture binary is absent. This is neither `attachment_verified` nor
`attachment_created_but_unverifiable`, because no attachment was created.

## Attachment identity

Unavailable because no upload occurred. The v1 contract does not promise a
stable attachment identifier or metadata sufficient to establish filename,
media type, size, or content identity.

## List/read-back result

No documented v1 purchase-document attachment list or read-back endpoint was
found. Plausible undocumented paths were not guessed against the live account.
The ordinary purchase GET exposed no attachment-related field.

The v2 list and download endpoints are documented, but they belong to a separate
API contract and were not used.

## Download/hash verification

Not applicable: no source binary was available, no upload occurred, and no
document-attachment download route is documented for v1.

## Purchase GET before/after

The preflight GET returned HTTP `200` and confirmed the intended unapproved test
purchase and its financial state. There is no post-mutation GET because the
mutation was stopped before execution. No purchase state was changed by this
discovery.

## UI verification

Not requested after the stopped mutation because there is no new attachment to
inspect. The existing same-document UI correlation from the status/PUT
discovery remains: status `0` is unapproved and the pending amount is `11.75
EUR`. This run makes no new UI claim.

## Limitations

- The investigation targets the configured legacy Invoicing v1 integration.
- The official v1 archive is incomplete about the attachment request and
  response identity.
- `OPTIONS` confirms POST is accepted but supplies no body contract.
- The scoped Invoice Card fixture represents a missing original rather than a
  stored binary.
- No runtime behavior for upload, multiple files, listing, download, hashing,
  persistence after PUT, or UI display was tested.
- The explicit v2 attachment lifecycle cannot be assumed to behave identically
  under v1.

## Remaining questions

1. Will Cabinet use v2 for purchase attachments, or is an authoritative v1
   request example/schema available from Holded support?
2. Which real, non-sensitive Invoice Card fixture includes the stored original
   and may be used for this test?
3. If v1 remains in scope, how can the uploaded file be listed and downloaded
   for same-document and SHA-256 verification?
4. Which MIME types and maximum file size apply to v1?
5. Does v1 return or expose a stable attachment ID, filename, media type, size,
   or hash?
6. Does v1 support more than one attachment on a purchase?
7. Do attachments survive metadata and financial PUT operations unchanged?
8. After an eventual upload, does the purchase remain unapproved with identical
   payment fields, product lines, subtotal, tax, and total?

No normative attachment rule can be accepted from this run. A mutation test can
resume only after both the request contract and an eligible existing source
fixture are available.
