# State 7 repair — plan/actual runtime notes

- PlanActualService constructor [DEPENDENCY_BOUNDARY]: retain the exact supplied
  repository, archive, and Registry services; never construct or discover them.
- refresh_estimate_snapshot [ORCHESTRATION]: lock stable PresuPro identity,
  canonicalize/hash accepted content, reuse an exact snapshot or append one new
  immutable snapshot in one transaction.
- propose_invoice_line_matches [BEHAVIOR]: resolve the exact archived revision and
  snapshot, return stable ordered non-authoritative proposals, and perform no
  confirmation transition.
- record_match_decision [BEHAVIOR]: lock the exact invoice line, preserve history,
  and enforce at most one active confirmed match before commit.
- get_unmatched_items [DETERMINISM_OR_ORDERING]: compute exact unmatched identities
  from pinned evidence and active confirmed decisions in stable ID order.
- calculate_plan_actual [ORCHESTRATION]: load exact snapshot and match decisions,
  resolve invoice revisions through archive and project context through Registry,
  then apply accepted formulas; direct persistence reads outside the service are forbidden.
- Repository transaction methods [DEPENDENCY_BOUNDARY]: use one PostgreSQL
  transaction per transition, commit once, and rollback idempotently.
- Repository reads [BEHAVIOR]: return exact persisted evidence or absence and never
  fabricate current snapshots, matches, or unmatched state.
- Repository writes [PROVENANCE]: append immutable snapshots/proposals/history and
  reject skipped, stale, or conflicting match transitions.
- PostgresPlanActualRepository constructor [SECURITY_BOUNDARY]: validate the
  supplied database connection, treat the URL as secret, and read no environment.
- Bootstrap create_local_app [ORCHESTRATION]: reuse the Cabinet database and exact
  archive/Registry services to construct and inject PlanActualService.
- Bootstrap create_local_app [VALIDATION_ERROR]: fail closed; no in-memory or
  nullable fallback is permitted.
