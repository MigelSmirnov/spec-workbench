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
| `plan_actual` | `plan_actual_persistence` | `load_match_decisions` returns what exists (completeness in `calculate_plan_actual`); `save_match_decision` → `insert_match_decision` + `update_match_status` + `list_matches_for_line` (single active confirmation in `record_match_decision`) | done |
| `durable_archive` | `durable_archive_persistence` | `save_publication` → `insert_publication`; `mark_publication_*` → `update_publication_state` + `load_publication` (transitions in `attach_local_source` / `recover_pending_publications`); `save_transfer_acceptance` / `save_source_attachment` → per-model appends in the one open transaction; `StoredInvoiceCard` head gets `load_invoice_card` / `upsert_invoice_card`; revision succession gets `update_card_revision_succession` | done |

`PostgresAccessControlBackend` was not a repository: it owned credential
hashing, throttling, and atomic audit. It is split the same way, with one
more piece: `access_control_persistence` (`PostgresAccessControlRepository`,
storage), `credential_security` (`credential_security_backend/v2`, the
mechanism), and `LocalAccessControlService` in `access_control` — a `policy`
implementation of `AccessControlBackend` that owns no executable boundary and
is generated as an ordinary behavioral module.

## Backend version

`persistence_backend/v3` (SPEC_STANDARD §6.3) closes the three tooling items
this repair left open: `engine: postgres` with emitter `postgres_sync_v1`,
`transaction: owned` with `begin`/`commit`/`rollback` fixed by the version,
the `lock` method kind, plus `json_model`/`json_value` storage and the
`argument_set`/`optional_argument` binds. Each `<x>_persistence` module owns
`create_<x>_schema(database_url: str) -> None` as its schema function. The
IR is authored in `70_persistence_closure.json` and projected verbatim into
`rules.persistence_backend`.

## Open items
- `LocalFilesystemSourceByteStore` now lives in `source_byte_store` under
  `rules.source_byte_store_backend` (§6.5); `HttpxVpsSynchronizationTransport`
  stays in `synchronization` until a VPS transport backend exists;
- `RegistryProjectSnapshot` is referenced by `WorkObject.registry_snapshot_id`
  but is not a persisted model; the Registry-derived projection has no durable
  home yet. This is a State 1/2 gap, not a persistence-boundary decision;
- `SynchronizationService.get_sync_status` composes its observation from
  `list_synchronizations_for_invoice`; the `replica` field stays None because
  no writer of `InvoiceWorkingReplica` exists, and `SynchronizationService.get_working_set_membership`
  has no storage method at all: no persisted model carries `working_set_id`, and
  the fresh working set is an open product question (`open_questions.md`, VPS
  working-set questions). Both stay irregular until that decision is taken.

These are tooling and standard-version decisions and do not change the
ownership recorded here.
