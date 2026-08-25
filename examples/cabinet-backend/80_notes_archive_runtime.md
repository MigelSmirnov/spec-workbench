# State 7 repair — durable archive runtime generation notes

## DurableArchiveService

- Constructor [DEPENDENCY_BOUNDARY]: retain the exact supplied ports; reject missing dependencies and never construct adapters or read environment variables.
- attach_local_source [ORCHESTRATION]: stage and verify each valid candidate before the invoice-scoped metadata transition; persist the journal and archive mutation under one lock, then publish according to A70.
- attach_local_source [BEHAVIOR]: report attached only after committed metadata and reopened final bytes match the expected hash and size.
- attach_local_source [FALLBACK]: before commit, rollback and remove only the current candidate; after commit, retain recoverable pending state and never fabricate availability.
- attach_local_source [DETERMINISM_OR_ORDERING]: equivalent concurrent input converges on one replica; conflicting bytes for one source identity cannot both commit.
- recover_pending_publications [BEHAVIOR]: lock and inspect every committed pending publication, verify candidate or final bytes, finalize an equivalent candidate once, and persist published or safe failed state.
- recover_pending_publications [VALIDATION_ERROR]: raise a startup-blocking error when recovery cannot establish truthful state.

All existing archive notes apply to the corresponding service methods without weakening accepted semantics.

## PostgreSQL unit of work

- Transaction methods [DEPENDENCY_BOUNDARY]: use one PostgreSQL connection and transaction per service operation; nested implicit transactions and ad-hoc connections are forbidden.
- lock_invoice [BEHAVIOR]: acquire the database lock for the exact invoice before reading mutable acceptance or source state.
- Publication transitions [BEHAVIOR]: enforce the closed lifecycle and reject stale, skipped, or conflicting transitions.
- Constructor [SECURITY_BOUNDARY]: treat the database URL as secret; never log it or include it in safe errors.

## Local filesystem byte store

- stage [PATH_OR_ARTIFACT_POLICY]: create a private candidate under the staging root, write bounded bytes, flush, reopen, and verify exact hash and size.
- verify [SECURITY_BOUNDARY]: resolve only store-created opaque references under the configured root; reject traversal, symlink escape, devices, and non-regular files.
- publish [PATH_OR_ARTIFACT_POLICY]: use same-filesystem atomic rename to the content-addressed final reference; reuse existing final content only after exact verification and never overwrite different bytes.
- remove_staging [FORBIDDEN_ACTION]: remove only the exact candidate and never final or previously published content.
- Constructor [VALIDATION_ERROR]: require an absolute private root with staging and final directories on one filesystem; fail if atomic rename cannot be guaranteed.

## Bootstrap

- create_local_app [CONFIG_REFERENCE]: read the byte-store root only from the environment variable named by config.archive_runtime.byte_store_root_env.
- create_local_app [ORCHESTRATION]: construct both adapters and the service, and complete recovery before exposing FastAPI.
- create_local_app [VALIDATION_ERROR]: fail closed on missing configuration, unusable storage, database failure, or incomplete recovery; no in-memory fallback is permitted.
