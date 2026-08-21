# Cabinet_web compatibility audit

## Result

The verified Cabinet local box is **not yet cleared for a real Cabinet_web data canary**.

This does not invalidate the isolated box evidence. The generic host, content-validation lowering, capability readiness, and the narrow `attach_expected_missing_source` runtime remain PASS. The new block is at the boundary between the current `Cabinet_web` contract and the local box.

Reviewed upstream state:

```text
repository: MigelSmirnov/Cabinet_web
ref: main
commit: 63f1752dc09be93156c6e7bf45f3c80e6c7f8387
```

Machine record:

```text
experiments/cabinet-vault/cabinet_web_interop_audit_v0.yaml
```

## Responsibility alignment

The two systems already describe a compatible high-level ownership split.

`Cabinet_web` owns:

```text
Invoice Card facts and versioned Card contracts
working draft/confirmation operations
GitHub repository Card history
conversation/Web-facing workspace behavior
```

The local box owns:

```text
durable local archive replicas
local source bytes and publication recovery
local authority/effect enforcement
append-only operational audit
integration/processing evidence
```

The local box must not become the owner of confirmed Card facts, and `Cabinet_web` must not import the backend database/runtime as its domain model.

## Blocking finding 1 — source identity contract drift

`docs/01-storage/INVOICE_CARD_FORMAT.md` presents the Version 1 source as:

```json
{
  "source_id": "source-001",
  "kind": "photo",
  "file_ref": null,
  "file_status": "not_stored",
  "note": "Original received in conversation"
}
```

The same example uses `payment.transactions[].evidence.source_ref = "source-001"`.

However, the executable contract does not permit that identity:

```text
schemas/invoice-card-v1.schema.json
  source.additionalProperties = false
  source has no source_id

tools/invoice_validation.py
  SOURCE_FIELDS = kind, file_ref, file_status, note

tools/invoice_evidence_service.py
  invoice_attach_source requires those four fields only

tests/fixtures/invoices/obramat-cash/card.json
  payment evidence references source-001
  source itself has no source_id
```

Therefore a backend adapter must **not** invent `source_id` to make the models line up. The Card-contract owner must first make one explicit accepted decision and propagate it through the executable schema/validator/tool fixtures.

## Blocking finding 2 — no accepted Web-to-box synchronization contract

The accepted Cabinet_web architecture explicitly leaves a remote synchronization adapter as an extension point after an accepted integration decision.

The workflow says that confirmed Card JSON is committed to GitHub and then synchronized locally, but there is no machine contract for:

```text
exact confirmed Card revision
canonical content hash
source Git commit identity
expected source set
idempotency identity
local acceptance receipt
reconciliation after retries or revision changes
```

Until this exists, the local box cannot know from declared rules which Cabinet_web revision it is accepting and how that acceptance is acknowledged.

## Blocking finding 3 — source kind is not exact media identity

Cabinet_web source facts currently expose:

```text
kind = photo | pdf | message | scan | other
```

The verified box parser boundary requires one exact accepted content type:

```text
image/jpeg
image/png
application/pdf
```

`photo` cannot deterministically mean JPEG or PNG. Filename extension and caller-declared MIME are also insufficient by the box's accepted validation rules.

The integration must therefore define a bounded parser-backed content-type relation rather than a hidden `photo -> JPEG` mapping.

## Blocking finding 4 — no expected binary hash in Invoice Card V1

The current Cabinet_web source object contains no expected SHA-256. That is not automatically wrong: accepted backend semantics permit locally calculated hash evidence when the Card did not declare an expected hash, without rewriting the immutable Card.

But the current promoted runtime evidence is not yet a Cabinet_web interop proof for this exact no-expected-hash path. A real interop gate needs an executed case that proves:

```text
confirmed Card with source identity but no expected binary hash
-> local bounded validation
-> local calculated hash becomes storage evidence
-> confirmed Card bytes/content hash remain unchanged
-> replay/conflict/recovery still hold
```

## Non-blocking lifecycle split

The two `attach` operations should not be collapsed.

`Cabinet_web.invoice_attach_source` currently edits truthful source metadata on a **draft** Card with optimistic concurrency/idempotency.

The local box `invoice.source.attach` attaches verified durable bytes to an **accepted confirmed** Card revision without rewriting that Card.

These are different lifecycle operations. Synchronization should connect them.

## Canary rule

Current gate:

```text
isolated box runtime                PASS
Cabinet_web interoperability        BLOCK
real Cabinet_web data canary        FORBIDDEN FOR NOW
```

Blocking findings:

```text
CW-SOURCE-ID-001
CW-SYNC-001
CW-MEDIA-001
CW-HASH-001
```

The next design decision belongs at the earliest owner: Cabinet_web source identity. The backend must not silently resolve it.
