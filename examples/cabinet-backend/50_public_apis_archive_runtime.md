# State 5 repair — durable archive runtime API

## Public boundary

Cross-module consumers receive one explicit DurableArchiveService instance. The service exposes the seven existing accepted archive capabilities plus recover_pending_publications.

The existing operations preserve their accepted inputs, outputs, errors, and business meaning. They become methods only to make the required runtime dependencies explicit and cohesive.

recover_pending_publications is consumed only by bootstrap and has no HTTP or MCP exposure. Successful return means every recoverable committed publication was finalized or safely classified without making unverifiable bytes available. Unresolved recovery failure prevents startup.

## Mechanism ports

ArchiveUnitOfWork is consumed only by durable_archive. It provides transaction begin/commit/rollback, invoice locking, accepted-evidence reads, archive-transition persistence, and ArchiveBytePublication recovery transitions.

SourceByteStore is consumed only by durable_archive. It provides candidate staging, reopen/hash verification, atomic same-filesystem publication, and safe removal of an identified uncommitted candidate.

Neither port returns generic mappings or owns archive policy.

## Concrete implementations

PostgresArchiveUnitOfWork implements ArchiveUnitOfWork. LocalFilesystemSourceByteStore implements SourceByteStore. DurableArchiveService composes both.

Construction inputs come only from bootstrap. Business callers cannot provide database URLs, filesystem roots, staging paths, or final paths.

## Consumer rule

synchronization, plan_actual, holded_publication, retention_release, api, and api_irregular may use only DurableArchiveService. They must not import either mechanism port or its concrete implementation.
