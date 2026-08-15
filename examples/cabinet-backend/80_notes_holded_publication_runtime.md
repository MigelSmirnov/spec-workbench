# State 7 repair — Holded publication runtime notes

- Service constructor [DEPENDENCY_BOUNDARY]: retain the exact repository, archive,
  and gateway; never construct adapters or discover alternate services.
- request [ORCHESTRATION]: lock the exact revision, resolve archive truth, reuse an
  equivalent logical publication or commit one before the sole gateway create.
- request [BEHAVIOR]: persist every verified, pending, ambiguous, mismatch, or
  reconciliation-required transition; a technical response is never success.
- reconcile [FORBIDDEN_ACTION]: reload exact state and use read-only gateway lookup;
  never repeat create or change the bound revision.
- status [BEHAVIOR]: return exact committed publication or raise
  HoldedPublicationNotFoundError; never fabricate pending or success.
- Repository transaction methods [DEPENDENCY_BOUNDARY]: use one PostgreSQL
  transaction, commit once, and rollback idempotently.
- Repository locks [BEHAVIOR]: serialize exact publication and invoice-revision
  decisions before reading active state.
- Repository reads/writes [PROVENANCE]: return exact evidence or absence, append
  valid transitions, and reject skipped/stale/conflicting lifecycle changes.
- PostgreSQL constructor [SECURITY_BOUNDARY]: validate connectivity, treat the URL
  as secret, and read no environment variables.
- Bootstrap [ORCHESTRATION]: reuse database, archive, and gateway to construct and
  inject one service; fail closed without an in-memory or nullable fallback.
