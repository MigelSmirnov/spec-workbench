# State 3 repair — retention release runtime boundary

`retention_release` exposes `RetentionReleaseService` constructed with the exact
`RetentionReleaseRepository`, `DurableArchiveService`, and
`SynchronizationService`. The concrete repository is
`PostgresRetentionReleaseRepository`.

Synchronization additionally exposes the read-only
`get_working_set_membership` capability required to resolve exact coverage.

The retention service owns evaluation, re-check, idempotent decision history, and
status. It never performs physical deletion, reads environment variables, or
accesses archive/synchronization persistence directly.
