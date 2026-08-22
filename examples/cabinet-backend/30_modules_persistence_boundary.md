# State 3 repair — persistence boundary ownership

## Decision

A concrete PostgreSQL repository is a storage mechanism, not a policy owner.
Stage 9 admission and Factory `validate_generation_closure` reject every local
port implementation that is not emitted from a closed deterministic backend,
and `persistence_backend` lowers only storage shape: tables, columns, keys,
uniqueness, reads, appends, and field updates on an open transaction.

Two kinds of decisions were therefore sitting in the wrong design state:

1. **Conditional writes** (`reserve_*`, `mark_*_issued`, `save_transition`,
   `merge_work_objects`, guarded `save_*`): "reuse only an equivalent record,
   otherwise reject" and "permit only this state transition" are idempotency
   and lifecycle policy. They belong to the owning `*Service`, which already
   holds the lock for the exact target. The repository exposes the plain read
   and the plain append or update that the service composes.
2. **Generation-unit mixing**: one module owned a behavioral service and a
   deterministic repository. A persistence module must own exactly one
   repository class so that it can be emitted without an LLM pass.

## Structure

Every runtime module `<x>` that owns `Postgres<X>Repository` (or unit of work)
is split into:

- `<x>` — unchanged public operations, `<X>Service`, errors, and all policy;
- `<x>_persistence` — exactly one concrete repository class implementing the
  `<X>Repository` Protocol declared in `models`.

Transaction ownership (`begin`, `commit`, `rollback`) and exact-target locking
(`lock_*`) stay on the repository contract: the services already depend on
them and they are engine mechanism, not product policy. Their deterministic
lowering is a backend-version concern and is recorded as an open item below.

Bootstrap constructs the concrete repository from `<x>_persistence` and
injects it into the service exactly as before.

## Per-module status

| Runtime module | Persistence module | Policy moved to service | Status |
|---|---|---|---|
| `retention_release` | `retention_release_persistence` | `reserve_decision` → `insert_decision` + equivalence check in `request_manual_vps_release` | done |
| `holded_publication` | `holded_publication_persistence` | `reserve_publication` → `insert_publication`, `save_transition` → `update_publication`; equivalence and transition validity in `HoldedPublicationService` | done |
| `registry_context` | `registry_context_persistence` | `merge_work_objects` → `list_work_objects` + keyed `upsert_work_objects`; merge derived in `refresh_registry_context` | done |
| `holded_gateway` | `holded_gateway_persistence` | `reserve_attempt` → `insert_attempt`; `mark_request_issued` + `append_attempt_outcome` → `update_attempt`; `append_lookup_evidence` → `insert_lookup_evidence`; `HoldedPurchaseLookupEvidence` classified as persisted `issued` evidence | done |
| `synchronization` | `synchronization_persistence` | `reserve_synchronization` → `insert_synchronization` + `load_synchronization_by_idempotency`; `mark_transfer_issued` + `save_synchronization_outcome` → `update_synchronization`; `reserve_catalogue_publication` → `insert_catalogue_publication` + `load_catalogue_publication_by_idempotency`; `save_catalogue_acknowledgement` → `update_catalogue_publication`; `VpsConnectionObservation` classified as persisted `issued` evidence | done (see open items) |
| `plan_actual` | `plan_actual_persistence` | `load_match_decisions` pinned-absence failure, `save_match_decision` active-conflict | pending |
| `durable_archive` | `durable_archive_persistence` | `save_publication`, `mark_publication_published`, `mark_publication_failed`; multi-model writes become aggregates | pending |

`PostgresAccessControlBackend` is not a repository: it owns credential
hashing, throttling, and atomic audit. It is handled by a credential-security
backend, not by this repair.

## Open items for the backend version

- lowering of repository-owned `begin`/`commit`/`rollback` and `lock_*`;
- `schema_function` ownership for a repository constructed from
  `database_url` rather than an open connection;
- `engine: postgres` in `rules.persistence_backend`;
- `RegistryProjectSnapshot` is referenced by `WorkObject.registry_snapshot_id`
  but is not a persisted model; the Registry-derived projection has no durable
  home yet. This is a State 1/2 gap, not a persistence-boundary decision;
- `SynchronizationRepository.load_sync_status` returns the composite
  `SynchronizationStatusObservation` and `SynchronizationService.get_working_set_membership`
  has no storage method at all: no persisted model carries `working_set_id`, and
  the fresh working set is an open product question (`open_questions.md`, VPS
  working-set questions). Both stay irregular until that decision is taken.

These are tooling and standard-version decisions and do not change the
ownership recorded here.
