# State 1 repair — Cabinet Web persistence runtime records

## Status

Accepted runtime-record closure for the PostgreSQL/VPS durability decision A17. These records add storage shape only where the existing product models deliberately exclude reusable secrets, recovery-journal fields, current selectors, or local-receipt binding evidence.

The mature local `cabinet-backend` is used only as an E2E-tested structural precedent for `persistence_backend/v3`, `postgres_sync_v1`, verifier-only credential storage, transaction-owned repository methods, and recoverable byte-publication journals. Server ownership and business semantics remain those of `cabinet-web-backend` A08/A09/A10/A11/A17.

Plaintext bearer material remains one-time output/input data and is never a table field. Every record below is a mechanical persistence envelope and does not move authorization, idempotency equivalence, Card lifecycle, source availability, transfer reconciliation, Registry monotonicity, release eligibility, or restore policy into PostgreSQL adapters.

## Model M108 — AccessCredentialRecord

Fields: `credential_id: str`, `subject_kind: CredentialSubjectKind`, `subject_id: str`, `channel: str`, `secret_hash: str`, `status: str`, `issued_at: datetime`, `rotated_from_credential_id: str | None`, `revoked_at: datetime | None`, `last_authenticated_at: datetime | None`.

Stores one credential verifier without the reusable bearer secret. `subject_kind` separates human/plugin principals from local-node credentials without changing M02/M17 identity.

### Identity

entity

### Identity evidence

The stable `credential_id` names one issued verifier through authentication, rotation history, and revocation. Rotation creates a new credential record; equal verifier or lifecycle fields never make two credential IDs interchangeable.

## Model M109 — CapabilityGrantRecord

Fields: `grant_id: str`, `target_principal_id: str`, `channel: str`, `capability: str`, `entity_scope: EntityScope | None`, `scope_key: str`, `created_at: datetime`.

Stores one exact target-principal/channel/capability/scope grant. `scope_key` is a deterministic non-null storage key for exact uniqueness; it does not broaden or replace the typed `EntityScope` authority.

### Identity

entity

### Identity evidence

The stable `grant_id` identifies one issued authorization fact. Exact target, channel, capability, and scope determine idempotent equivalence, but a different grant ID remains distinct evidence.

## Model M110 — AuthenticationThrottleState

Fields: `abuse_context_hash: str`, `credential_id: str | None`, `consecutive_failures: int`, `delay_until: datetime | None`, `blocked_until: datetime | None`, `updated_at: datetime`.

Stores bounded secret-free authentication-abuse state.

### Identity

entity

### Identity evidence

The stable `abuse_context_hash` identifies one bounded failure context across attempts without persisting the attempted bearer secret. Counter and timing changes preserve that context identity.

## Model M111 — SecurityAuditRecord

Fields: `evidence_id: str`, `event_type: str`, `subject_kind: str | None`, `subject_id: str | None`, `credential_id: str | None`, `channel: str | None`, `operation: str | None`, `result: str`, `reason_code: str | None`, `occurred_at: datetime`.

Append-only secret-free authentication, authorization, enrollment, rotation, revocation, throttling, and refusal evidence.

### Identity

entity

### Identity evidence

Every `evidence_id` names one immutable security event. Equal projected fields at the same time do not make independently issued audit events interchangeable.

## Model M112 — SourceUploadHandoffRecord

Fields: `handoff_id: str`, `card_id: str`, `source_id: str`, `expected_revision: CardRevisionReference`, `principal_id: str`, `actor: ActorReference`, `secret_verifier: str`, `status: str`, `issued_at: datetime`, `expires_at: datetime`, `consumed_at: datetime | None`, `revoked_at: datetime | None`.

Durable upload-handoff row containing the public M15 facts plus the protected verifier; the returned `SourceUploadHandoff` remains verifier-free.

### Identity

entity

### Identity evidence

The stable `handoff_id` preserves one single-use handoff identity through issued, consumed, expired, or revoked state. The reusable bearer secret is not part of persistence identity.

## Model M113 — SourceBytePublication

Fields: `publication_id: str`, `card_id: str`, `source_id: str`, `content_hash: str`, `size_bytes: int`, `staging_reference: str`, `final_reference: str`, `state: str`, `created_at: datetime`, `updated_at: datetime`, `failure_code: str | None`.

PostgreSQL recovery journal for one verified candidate publication. Accepted lifecycle is `staged -> metadata_committed -> published` with `failed` as recoverable non-available evidence. Only committed metadata plus reopened verified final bytes may be reported available.

### Identity

entity

### Identity evidence

The stable `publication_id` identifies one publication attempt across staging, metadata commit, final publication, and recovery. A retry requiring another logical publication receives another identity.

## Model M114 — InvoiceWorkingSetRecord

Fields: `working_set_id: str`, `invoice_id: str`, `revision: CardRevisionReference`, `manifest_id: str`, `manifest_hash: str`, `required_sources: tuple[SourceContentReference, ...]`, `status: str`, `created_at: datetime`, `released_at: datetime | None`.

Persists the exact confirmed revision, manifest, and source membership consumed by discovery and explicit safe release.

### Identity

entity

### Identity evidence

The stable `working_set_id` names one exact immutable Invoice work selection. A changed revision, manifest, or source membership creates a different working set rather than rewriting this identity.

## Model M115 — InvoiceTransferReceiptRecord

Fields: `issuance_id: str`, `receipt: InvoiceTransferReceipt`, `recorded_at: datetime`.

Binds the reciprocal local `InvoiceTransferReceipt` to the Web-side `issuance_id` without changing the wire type.

### Identity

entity

### Identity evidence

The Web-side `issuance_id` is the stable identity of the persisted receipt binding: at most one exact reciprocal receipt may acknowledge that issuance. A receipt for another issuance is not interchangeable even if payload facts match.

## Model M116 — LocalBackendConnectionObservationRecord

Fields: `observation_id: str`, `observation: LocalBackendConnectionObservation`.

Gives durable identity to one persisted compatibility/availability observation while leaving the reciprocal observation value unchanged.

### Identity

entity

### Identity evidence

The stable `observation_id` identifies one issued observation event. Equal observed values at different observation events remain distinct evidence.

## Model M117 — RegistryCataloguePublicationRecord

Fields: `publication_id: str`, `catalogue_id: str`, `content_hash: str`, `source_node_id: str`, `target_node_id: str`, `idempotency_key: str`, `status: str`, `created_at: datetime`, `acknowledged_at: datetime | None`, `safe_error_code: str | None`.

Preserves source-node idempotency and acknowledgement state for one incoming Registry catalogue publication.

### Identity

entity

### Identity evidence

The stable `publication_id` identifies one logical catalogue publication through reservation, acknowledgement, or bounded failure. Idempotent replay reuses this logical publication rather than creating an unrelated identity.

## Model M118 — RegistryCatalogueCurrentSelector

Fields: `node_id: str`, `catalogue_id: str`, `content_hash: str`, `selected_at: datetime`.

Explicit PostgreSQL current-selector row required to atomically point to one complete accepted Registry replica.

### Identity

entity

### Identity evidence

The stable `node_id` identifies one current-selector slot for that Registry source/replica boundary. Moving the selector changes its referenced catalogue while preserving the selector identity.

## Model M119 — BackupRestoreDrillRecord

Fields: `drill_id: str`, `backup_id: str`, `status: str`, `verified_card_revisions: int`, `verified_source_hashes: int`, `started_at: datetime`, `completed_at: datetime | None`, `safe_error_code: str | None`.

Durable restore-verification evidence required by readiness and recovery policy.

### Identity

entity

### Identity evidence

The stable `drill_id` identifies one isolated restore verification execution from start through its terminal report. Re-running verification produces a separate drill identity.

## Model M120 — VpsReleaseEvidence

Fields: `evidence_id: str`, `working_set_id: str`, `manifest_id: str`, `invoice_revision: CardRevisionReference`, `required_source_hashes: tuple[str, ...]`, `receipt_synchronization_id: str`, `durable_evidence_id: str`, `released_source_ids: tuple[str, ...]`, `status: str`, `released_at: datetime`.

Preserves the exact working set, manifest, revision, local durable-evidence binding, released source identities, status, and release time required by A10.

### Identity

entity

### Identity evidence

The stable `evidence_id` names one immutable release decision/effect record. Equal released memberships or timestamps do not merge independent release evidence.
