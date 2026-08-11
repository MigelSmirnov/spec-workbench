# State 1 repair — contract-support value models

## Status

This is a bounded State 1 repair discovered while authoring State 6 exact contracts.
It introduces no new product behavior. Every type below packages an input, outcome,
or evidence shape already required by accepted State 2 rules, reviewed State 4
flows, and State 5 public operations.

These types exist so State 6 can use real project types instead of `dict`, `Any`,
implicit tuples, or transport-shaped payloads. They do not replace the existing
entity models in `01_models.md`.

---

## Model M35 — AuthenticatedPrincipalContext

Immutable authenticated-call context. It is not a credential and contains no secret.

Fields:

- `principal_id: str`;
- `principal_kind: str` — accepted values are `user`, `agent`, or `service`;
- `credential_id: str` — stable identifier of the credential used for the call;
- `authenticated_at: datetime`;
- `interaction_id: str | None`.

The current authorization store remains authoritative for revocation and capability
checks; this value does not cache authorization truth.

---

## Model M36 — AuthorizationDecision

Immutable result of checking one exact protected operation.

Fields:

- `principal_id: str`;
- `operation: str`;
- `allowed: bool`;
- `reason_code: str | None`;
- `evidence_id: str`;
- `decided_at: datetime`.

---

## Model M37 — SynchronizationWorkSelection

Immutable selection of one exact synchronization obligation.

Fields:

- `invoice_id: str`;
- `manifest_id: str`;
- `source_node_id: str`;
- `target_node_id: str`;
- `requested_at: datetime`.

---

## Model M38 — SynchronizationOutcome

Immutable public outcome preserving transport state separately from durable
acceptance.

Fields:

- `synchronization: InvoiceSynchronization`;
- `receipt: InvoiceTransferReceipt | None`;
- `durable_acceptance: DurableAcceptanceVerification | None`.

A delivered synchronization with no durable proof remains distinguishable from an
accepted import.

---

## Model M39 — SynchronizationStatusObservation

Read-only observation used by retention/release evaluation.

Fields:

- `invoice_id: str`;
- `node_id: str`;
- `synchronization_id: str | None`;
- `replica: InvoiceWorkingReplica | None`;
- `status: str`;
- `observed_at: datetime`.

The value makes no durable-acceptance claim.

---

## Model M40 — DurableAcceptanceVerification

Authoritative read result for exact local durable acceptance.

Fields:

- `invoice_id: str`;
- `content_hash: str | None`;
- `accepted: bool`;
- `required_source_ids: tuple[str, ...]`;
- `verified_source_ids: tuple[str, ...]`;
- `evidence_id: str | None`;
- `verified_at: datetime`.

`accepted = true` is valid only when the accepted durable-local proof is complete.

---

## Model M41 — LocalSourceFile

One local source-file submission before archive acceptance.

Fields:

- `filename: str`;
- `media_type: str`;
- `content: bytes`;
- `expected_source_id: str | None`;
- `expected_content_hash: str | None`.

Filename and media type never create storage/path authority.

---

## Model M42 — SourceAttachmentItemResult

Immutable per-file attachment outcome.

Fields:

- `filename: str`;
- `source_id: str | None`;
- `content_hash: str`;
- `result: str` — accepted values are `attached`, `already_attached`, or `rejected`;
- `safe_error_code: str | None`.

---

## Model M43 — SourceStatus

Read-only source-evidence status for one accepted invoice.

Fields:

- `invoice_id: str`;
- `available_source_ids: tuple[str, ...]`;
- `missing_source_ids: tuple[str, ...]`;
- `failed_source_ids: tuple[str, ...]`;
- `complete: bool`;
- `observed_at: datetime`.

---

## Model M44 — SourceAttachmentBatchResult

Result of one local source-attachment invocation.

Fields:

- `invoice_id: str`;
- `items: tuple[SourceAttachmentItemResult, ...]`;
- `source_status: SourceStatus`.

Partial success remains explicit through the per-item results.

---

## Model M45 — RegistryProjectObservation

One project row from the accepted full Registry observation defined by A34.

Fields:

- `project_id: str`;
- `display_name: str`;
- `address: str`;
- `status: str`;
- `registry_updated_at: datetime`.

No customer or completion fields are added.

---

## Model M46 — RegistryRefreshResult

Immutable summary of one accepted full Registry refresh.

Fields:

- `projects: tuple[RegistryProjectSnapshot, ...]`;
- `work_objects: tuple[WorkObject, ...]`;
- `observed_at: datetime`.

Absence from the refresh does not imply deletion.

---

## Model M47 — PresuProEstimateObservation

One current PresuPro estimate observation presented for immutable snapshot
acceptance under A43.

Fields:

- `presupro_estimate_id: str`;
- `project_id: str`;
- `presupro_updated_at: datetime`;
- `status: str`;
- `locked: bool`;
- `canonical_content: str`;
- `observed_at: datetime`.

`canonical_content` is the deterministic serialized estimate content used for
content hashing and snapshot construction; it is not a generic application DTO.

---

## Model M48 — HoldedPurchasePayloadItem

Typed item in the currently accepted Holded purchase-create contract A51.

Fields:

- `name: str`;
- `desc: str | None`;
- `units: Decimal`;
- `subtotal: Decimal`;
- `discount: Decimal | None`;
- `tax: Decimal`;
- `sku: str | None`.

---

## Model M49 — HoldedPurchaseAttemptPayload

Typed first-publication payload accepted by A51/A52.

Fields:

- `apply_contact_defaults: bool`;
- `contact_code: str`;
- `contact_name: str`;
- `desc: str`;
- `date: str`;
- `approve_doc: bool`;
- `items: tuple[HoldedPurchasePayloadItem, ...]`;
- `invoice_num: str`;
- `currency: str`.

The `desc` field carries the stable non-financial attempt marker required by A52.

---

## Model M50 — HoldedPurchaseLookupEvidence

Immutable technical result of bounded read-only Holded recovery lookup.

Fields:

- `attempt_marker: str`;
- `match_count: int`;
- `document_id: str | None`;
- `raw_status: int | None`;
- `business_verified: bool`;
- `outcome: str` — accepted values are `verified_match`, `payload_mismatch`,
  `outcome_unknown`, or `duplicate_conflict`;
- `observed_at: datetime`.

It contains technical evidence only; `module:holded_publication` owns the logical
publication classification.

---

## Model M51 — VpsReleaseRequestContext

Immutable context of one explicit manual release evaluation.

Fields:

- `requested_by: ActorReference`;
- `requested_at: datetime`;
- `working_set_id: str | None`.

At least one of Registry `project_id` (the operation argument) or `working_set_id`
must identify the exact target before evaluation.

---

## Model M52 — VpsReleaseEvaluation

Immutable allow/block evaluation for one exact VPS working set.

Fields:

- `project_id: str`;
- `working_set_id: str`;
- `allowed: bool`;
- `durable_evidence: tuple[DurableAcceptanceVerification, ...]`;
- `sync_observations: tuple[SynchronizationStatusObservation, ...]`;
- `blocked_reason_code: str | None`;
- `evaluated_at: datetime`.

No physical deletion occurs during evaluation.

---

## Model M53 — VpsReleaseDecision

Immutable recorded manual release decision.

Fields:

- `decision_id: str`;
- `project_id: str`;
- `working_set_id: str`;
- `actor: ActorReference`;
- `evaluation: VpsReleaseEvaluation`;
- `result: str` — accepted values are `authorized`, `blocked`, `idempotent`, or
  `conflict`;
- `decided_at: datetime`.

The physical VPS adapter consumes an authorized decision but cannot broaden its
target or weaken its evidence.
