# State 7 repair — synchronization runtime notes

## SynchronizationService

- Constructor [DEPENDENCY_BOUNDARY]: retain the exact supplied repository,
  transport, and archive; never construct or discover alternates.
- synchronize_invoice_work [ORCHESTRATION]: durably reserve and mark issued
  before transport, persist every conclusive or unknown outcome, and send an
  exact delivered package through archive acceptance and required verification.
- synchronize_invoice_work [FALLBACK]: classify timeout, connection loss, or
  response loss after issuance as `unknown_outcome`; never repeat the logical
  transfer automatically.
- get_sync_status [BEHAVIOR]: return only PostgreSQL-authoritative evidence and
  preserve absent, unknown, stale, and unavailable states explicitly.
- reconcile_transfer_outcome [FORBIDDEN_ACTION]: use only read-only remote
  reconciliation for a persisted unknown attempt; never issue another transfer.
- publish_registry_catalogue [ORCHESTRATION]: bind catalogue id, ordered content
  hash, endpoints, and idempotency key before publication and preserve exact
  acknowledgement evidence.
- observe_vps_connection [BEHAVIOR]: report typed current evidence without
  changing synchronization or archive state.

## PostgreSQL repository

- Transaction methods [DEPENDENCY_BOUNDARY]: use one transaction and exact row
  or uniqueness lock for each lifecycle transition.
- Insert/update/lookup methods [PROVENANCE]: plain append of attempt and
  publication rows, plain update of their lifecycle fields, exact lookups by
  idempotency binding. Reuse, issuance authority, and transition validity are
  decided by the service from the reloaded locked row
  (`30_modules_persistence_boundary.md`).
- Transaction methods [FALLBACK]: commit one valid typed transition or rollback
  idempotently while preserving the original failure.
- Read and observation methods [PROVENANCE]: return exact persisted evidence or
  absence and append immutable catalogue/connection observations without
  fabricating defaults.
- Constructor [SECURITY_BOUNDARY]: treat the database URL as secret.

## HTTPS transport

- Constructor [VALIDATION_ERROR]: require HTTPS without embedded credentials or
  fragments, a non-empty dedicated credential, and positive finite bounds.
- Mutation operations [FORBIDDEN_ACTION]: disable transport retries and replaying
  redirects; one service-authorized invocation issues at most one mutation.
- Read operations [BEHAVIOR]: perform bounded exact-status or connection reads.
- All operations [SECURITY_BOUNDARY]: verify TLS, bound bytes before parsing,
  redact authorization material, and return secret-free typed evidence.

## Bootstrap

- create_local_app [CONFIG_REFERENCE]: read the VPS URL and node credential only
  from the environment names declared by `config.synchronization_runtime`.
- create_local_app [ORCHESTRATION]: reuse the Cabinet database and exact archive,
  construct repository, transport, and service, and bind them before FastAPI.
- create_local_app [VALIDATION_ERROR]: fail closed; no disabled, anonymous,
  in-memory, or service-locator fallback is permitted.
