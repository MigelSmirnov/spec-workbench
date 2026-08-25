# State 1 repair — Holded gateway runtime evidence

## Accepted model refinement — HoldedPurchaseLookupEvidence

The earlier support shape is refined so the gateway does not decide A51 business verification.

- remove `business_verified`;
- technical `outcome` values describe observation only: `document_observed`, `zero_matches`, `multiple_matches`, `unknown_document`, `malformed_response`, or `transport_failure`;
- add `document: HoldedRemotePurchaseDocument | None`.

`module:holded_publication` compares the typed observed document with the exact immutable Card revision and owns verified success, payload mismatch, and logical reconciliation.

## Persistence classification — HoldedPurchaseLookupEvidence

Lookup evidence is appended durably by the gateway (`append_lookup_evidence`
in State 6) and therefore is persisted evidence, not a transient value:
`persistence.HoldedPurchaseLookupEvidence.class = "issued"`. One row per
observation, identified by `attempt_marker` and `observed_at`; rows are never
updated or deleted. The earlier omission left the evidence with no durable
home (`30_modules_persistence_boundary.md`).

## Accepted boundary models

### HoldedTransportResponse

A bounded immutable observation of one Holded HTTP response.

Fields:

- `status_code: int`;
- `body: bytes`;
- `request_id: str | None`;
- `received_at: datetime`.

The body is bounded before this model is created. It is untrusted external evidence and never contains or exposes the API key.

### HoldedRemotePurchaseItem

Typed immutable line evidence returned by Holded:

- `name: str`;
- `description: str | None`;
- `units: Decimal`;
- `tax: Decimal`;
- `subtotal: Decimal | None`.

### HoldedRemotePurchaseDocument

Typed immutable GET evidence required for A51 comparison:

- `document_id: str`;
- `supplier_code: str | None`;
- `supplier_name: str`;
- `supplier_invoice_number: str`;
- `document_date: int` (the exact Holded v1 timestamp);
- `currency: str`;
- `description: str | None`;
- `items: tuple[HoldedRemotePurchaseItem, ...]`;
- `gross_total: Decimal`;
- `raw_status: int | None`;
- `observed_at: datetime`.

The gateway parses this shape but does not compare it with Card truth or interpret raw status.

### HoldedRemotePurchaseSummary

Fields:

- `document_id: str`;
- `description: str | None`;
- `raw_status: int | None`.

### HoldedPurchaseListPage

Fields:

- `items: tuple[HoldedRemotePurchaseSummary, ...]`;
- `observed_at: datetime`.

## Runtime boundaries

The generated gateway requires two explicit runtime interfaces:

- `HoldedHttpClient`, a narrow create/list/GET HTTP mechanism port;
- `HoldedAttemptRepository`, a narrow technical-attempt PostgreSQL port.

Both are local implementation obligations. `module:holded_transport` owns the
deterministically emitted `HttpxHoldedHttpClient` implementation of
`HoldedHttpClient`; `module:holded_gateway` owns
`PostgresHoldedAttemptRepository` as the implementation of
`HoldedAttemptRepository`.
Neither port is an ordinary concrete base class or an externally supplied
deployment extension.

Generic response dictionaries, unbounded JSON, generic repositories, and reusable credentials in domain models are forbidden.
