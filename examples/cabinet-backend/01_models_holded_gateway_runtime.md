# State 1 repair — Holded gateway runtime evidence

## Accepted boundary models

### HoldedTransportResponse

A bounded immutable observation of one Holded HTTP response.

Fields:

- `status_code: int`;
- `body: bytes`;
- `request_id: str | None`;
- `received_at: datetime`.

The body is bounded by deployment policy before this model is created. It is external evidence, not trusted business truth, and must never contain or expose the API key.

### HoldedPurchaseListPage

A typed immutable page used only for read-only marker recovery.

Fields:

- `items: tuple[HoldedRemotePurchaseSummary, ...]`;
- `next_page: int | None`;
- `observed_at: datetime`.

### HoldedRemotePurchaseSummary

Fields:

- `document_id: str`;
- `description: str | None`;
- `raw_status: int | None`.

These models do not interpret numeric Holded status or decide Cabinet publication success.

## Runtime boundaries

The generated gateway requires:

- a narrow HTTP mechanism port for create, list, and GET;
- a narrow technical-attempt repository for durable pre-mutation reservation and append-only outcomes;
- a cohesive gateway service that owns protocol sequencing, parsing, redaction, and safe error classification.

Generic response dictionaries, unbounded JSON, generic repositories, and reusable credentials in domain models are forbidden.
