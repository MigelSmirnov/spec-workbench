# State 7 repair — retention release runtime notes

- synchronization membership [BEHAVIOR]: return exact PostgreSQL-authoritative
  working-set membership in stable revision order; never infer from Registry state.
- Service constructor [DEPENDENCY_BOUNDARY]: retain the exact repository, archive,
  and synchronization services; never construct or discover alternates.
- evaluate [ORCHESTRATION]: resolve exact membership, obtain synchronization and
  durable proof for every member, persist evaluation evidence, and allow only
  exhaustive positive coverage.
- request [ORCHESTRATION]: lock the exact target, reload current membership and all
  proof, reject any stale/change/gap, and reserve one idempotent authorization.
- status [BEHAVIOR]: return exact decision or None and never claim physical deletion.
- Repository transaction/lock methods [DEPENDENCY_BOUNDARY]: use one PostgreSQL
  transaction and serialize the exact working-set lifecycle.
- Repository evidence methods [PROVENANCE]: append immutable evaluations and
  decisions, reuse only an equivalent decision, and reject conflicts.
- PostgreSQL constructor [SECURITY_BOUNDARY]: validate connectivity, protect the
  database URL, and read no environment variables.
- Bootstrap [ORCHESTRATION]: reuse database, archive, and synchronization to
  construct and inject one service; fail closed without fallback.
