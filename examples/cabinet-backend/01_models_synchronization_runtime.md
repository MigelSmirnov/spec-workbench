# State 1 repair — synchronization runtime evidence

## VpsInvoiceTransferPackage

Immutable typed package returned by the authenticated VPS transport:

- `synchronization: InvoiceSynchronization`;
- `manifest: InvoiceTransferManifest`;
- `card_revision: StoredInvoiceCardRevision`;
- `source_replicas: tuple[SourceBinaryReplica, ...]`.

The package is untrusted transport evidence until `durable_archive` classifies it.

## VpsTransferReconciliationEvidence

Immutable read-only observation for one exact transfer:

- `synchronization_id: str`;
- `idempotency_key: str`;
- `manifest_hash: str`;
- `observed_status: str`;
- `receipt: InvoiceTransferReceipt | None`;
- `observed_at: datetime`;
- `safe_error_code: str | None`.

It records remote knowledge and cannot establish local durable acceptance.

## RegistryCatalogueDelivery

Immutable catalogue payload containing `catalogue_id`, exact ordered
`RegistryProjectSnapshot` values, source and target node ids, idempotency key,
and creation time.

## VpsCatalogueAcknowledgement

Immutable typed acknowledgement containing publication/catalogue identity,
status, acknowledgement time, and optional safe error code.

## VpsConnectionObservation

Immutable read-only observation containing availability, authentication result,
remote contract version, observation time, and optional safe error code. It
contains no credential or reusable authorization material.

Persistence classification: observations are appended durably by the
synchronization service and therefore are persisted evidence:
`persistence.VpsConnectionObservation.class = "issued"`, one immutable row per
observation identified by `observed_at`; never updated or deleted
(`30_modules_persistence_boundary.md`).

## Runtime interfaces

`VpsSynchronizationTransport` is the narrow authenticated HTTPS mechanism port.
`SynchronizationRepository` is the narrow PostgreSQL state and evidence port.
Neither interface owns archive acceptance, Registry catalogue content, or
retention policy.
