# State 1 repair — Cabinet Web persistence runtime records

## Status

Candidate runtime-record closure for the accepted PostgreSQL/VPS durability decision A17. These records add storage shape only where the existing product models deliberately exclude reusable secrets, recovery-journal fields, current selectors, or local-receipt binding evidence.

The mature local `cabinet-backend` is used only as an E2E-tested structural precedent for `persistence_backend/v3`, `postgres_sync_v1`, verifier-only credential storage, transaction-owned repository methods, and recoverable byte-publication journals. Server ownership and business semantics remain those of `cabinet-web-backend` A08/A09/A10/A11/A17.

## Access-control storage records

`AccessCredentialRecord` stores one credential verifier without the reusable bearer secret: `credential_id`, `subject_kind`, `subject_id`, `channel`, `secret_hash`, lifecycle timestamps/status, rotation predecessor, and last-authenticated time. `subject_kind` separates human/plugin principals from local-node credentials without changing M02/M17 identity.

`CapabilityGrantRecord` stores one exact target-principal/channel/capability/scope grant. `scope_key` is a deterministic non-null storage key for exact uniqueness; it does not broaden or replace the typed `EntityScope` authority.

`AuthenticationThrottleState` stores bounded secret-free abuse state. `SecurityAuditRecord` is append-only secret-free authentication/authorization/enrollment/rotation/revocation evidence.

Plaintext bearer material remains one-time output/input data and is never a table field.

## Source-custody recovery records

`SourceUploadHandoffRecord` is the durable handoff row containing the public M15 facts plus `secret_hash`; the returned `SourceUploadHandoff` remains verifier-free.

`SourceBytePublication` is the PostgreSQL recovery journal for one verified candidate publication: publication/card/source identity, content hash/size, opaque staging/final references, state, timestamps, and bounded failure code. Its accepted lifecycle is `staged -> metadata_committed -> published` with `failed` as a recoverable terminal/non-available state. Only committed metadata plus reopened verified final bytes may be reported available.

## Synchronization and Registry storage records

`InvoiceWorkingSetRecord` persists the exact confirmed revision/manifest/source membership consumed by discovery and release. `InvoiceTransferReceiptRecord` binds the reciprocal local `InvoiceTransferReceipt` to the Web-side `issuance_id` without changing the wire type. `LocalBackendConnectionObservationRecord` gives immutable identity to one persisted compatibility observation.

`RegistryCataloguePublicationRecord` preserves source-node idempotency and acknowledgement state for one incoming catalogue publication. `RegistryCatalogueCurrentSelector` is the explicit PostgreSQL current-selector row required to atomically point to one complete accepted replica.

## Recovery and release evidence

`BackupRestoreDrillRecord` is the durable form of the restore-verification report required by readiness/recovery policy. `VpsReleaseEvidence` preserves the exact working set, manifest, revision, local durable-evidence binding, released source identities, status, and release time required by A10.

## Boundary rule

These records are mechanical persistence envelopes. They do not move authorization, idempotency equivalence, Card lifecycle, source availability, transfer reconciliation, Registry monotonicity, release eligibility, or restore policy into PostgreSQL adapters.
