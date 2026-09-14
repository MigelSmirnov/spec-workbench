# State 1 — concrete runtime evidence model closure

The following runtime evidence shapes refine the accepted archive, Holded, and
synchronization boundaries without moving business policy into adapters.

## Model M105 — ArchivePublicationState

`kind: enum`: `staged`, `metadata_committed`, `published`, `failed`.

### Identity

value

### Identity evidence

The value is a closed classification without runtime identity; equal members are interchangeable.

---

## Model M63 — ArchiveBytePublication

Fields: `publication_id: str`, `source_id: str`, `invoice_id: str`,
`content_hash: str`, `size_bytes: int`, `staging_reference: str`,
`final_reference: str`, `state: ArchivePublicationState`, `created_at: datetime`,
`updated_at: datetime`, `failure_code: str | None`.

### Identity
entity
### Identity evidence
`publication_id` preserves one publication attempt through its bounded lifecycle.

## Model M64 — HoldedTransportResponse

Fields: `status_code: int`, `body: bytes`, `request_id: str | None`,
`received_at: datetime`.
### Identity
value
### Identity evidence
Equal bounded response facts are interchangeable technical evidence.

## Model M65 — HoldedRemotePurchaseSummary

Fields: `document_id: str`, `description: str | None`, `raw_status: int | None`.
### Identity
value
### Identity evidence
Equal typed summary facts are interchangeable observations.

## Model M66 — HoldedPurchaseListPage

Fields: `items: tuple[HoldedRemotePurchaseSummary, ...]`,
`observed_at: datetime`.
### Identity
value
### Identity evidence
Equal ordered list contents and observation time are interchangeable.

## Model M67 — HoldedRemotePurchaseItem

Fields: `name: str`, `description: str | None`, `units: Decimal`, `tax: Decimal`,
`subtotal: Decimal | None`.
### Identity
value
### Identity evidence
Equal typed line observations are interchangeable.

## Model M68 — HoldedRemotePurchaseDocument

Fields: `document_id: str`, `supplier_code: str | None`, `supplier_name: str`,
`supplier_invoice_number: str`, `document_date: int`, `currency: str`,
`description: str | None`, `items: tuple[HoldedRemotePurchaseItem, ...]`,
`gross_total: Decimal`, `raw_status: int | None`, `observed_at: datetime`.
### Identity
value
### Identity evidence
Equal exact typed GET observations are interchangeable technical evidence.

## Model M69 — VpsInvoiceTransferPackage

Fields: `synchronization: InvoiceSynchronization`,
`manifest: InvoiceTransferManifest`, `card_revision: StoredInvoiceCardRevision`,
`source_replicas: tuple[SourceBinaryReplica, ...]`,
`assignment_observation: CardObjectAssignmentObservation | None` (produced by Cabinet Web at
capture; carried unchanged, never derived here).
### Identity
value
### Identity evidence
Equal exact transfer identity and evidence are interchangeable package observations.

## Model M70 — VpsTransferReconciliationEvidence

Fields: `synchronization_id: str`, `idempotency_key: str`, `manifest_hash: str`,
`observed_status: str`, `receipt: InvoiceTransferReceipt | None`,
`observed_at: datetime`, `safe_error_code: str | None`.
### Identity
value
### Identity evidence
Equal remote status evidence for the exact transfer is interchangeable.

## Model M71 — RegistryCatalogueDelivery

Fields: `catalogue_id: str`, `projects: tuple[RegistryProjectSnapshot, ...]`,
`source_node_id: str`, `target_node_id: str`, `idempotency_key: str`,
`created_at: datetime`.
### Identity
value
### Identity evidence
Equal exact ordered catalogue and endpoint facts are interchangeable deliveries.

## Model M72 — VpsCatalogueAcknowledgement

Fields: `publication_id: str`, `catalogue_id: str`, `status: str`,
`acknowledged_at: datetime | None`, `safe_error_code: str | None`.
### Identity
value
### Identity evidence
Equal exact acknowledgement facts are interchangeable evidence.

## Model M73 — VpsConnectionObservation

Fields: `available: bool`, `authenticated: bool`,
`remote_contract_version: str | None`, `observed_at: datetime`,
`safe_error_code: str | None`.
### Identity
value
### Identity evidence
Equal bounded connection facts and observation time are interchangeable.
