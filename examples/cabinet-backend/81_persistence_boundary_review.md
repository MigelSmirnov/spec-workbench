# Cabinet Backend — persistence boundary repair review

## Scope

`30_modules_persistence_boundary.md` records the State 3 decision: a concrete
PostgreSQL repository owns storage shape only; conditional writes are service
policy; one persistence module owns exactly one repository class. This review
covers the first module moved under that decision, `retention_release`, and
the slices it changed.

## Change

- `retention_release_persistence` owns `PostgresRetentionReleaseRepository`.
- `RetentionReleaseRepository.reserve_decision(decision) -> VpsReleaseDecision`
  (interface and concrete) is replaced by the plain append
  `insert_decision(decision) -> None`; a second decision for the same target
  is a uniqueness failure.
- `RetentionReleaseService.request_manual_vps_release` now states the
  equivalence rule itself: after the lock and re-check it loads the stored
  decision for the exact target, returns it when target, evaluation
  membership, evidence identities, and result are the same, raises
  `VpsReleaseBlockedError` when a different decision exists, and otherwise
  inserts exactly one new decision.
- Bootstrap imports the concrete repository from the new module; no public
  operation, route, rule, model, or obligation changed.

## Deterministic review

`design_module_review.py --review` reports zero blocks and zero review
prompts for every changed slice:

- `models`: 87 contracts, 89 notes;
- `retention_release`: 7 contracts, 24 notes;
- `retention_release_persistence`: 8 contracts, 8 notes;
- `bootstrap`: 4 contracts, 24 notes.

Assembly reports 8/8 checks ready with zero errors and zero warnings.

## Adversarial semantic review

- `insert_decision` cannot be emitted as a no-op, an upsert, or an update: the
  note requires an append inside the active locked transaction and forbids
  replacing or updating the stored row.
- The service cannot skip the equivalence check or broaden it: the note names
  the compared facets and the two outcomes for a mismatch and a match.
- Idempotency is unchanged for callers: the public note on
  `request_manual_vps_release` already required the existing equivalent
  decision to be returned; the responsibility moved, the behavior did not.
- The persistence module cannot acquire policy: it imports only the Protocol
  and the two persisted models from `models`.

Result: `PASS_INTERNAL_VARIATION` for `retention_release` (SQL organisation
and equivalence-comparison order remain internal), `PASS` for
`retention_release_persistence`, `models`, and `bootstrap`.

## Not yet closed

Factory canonical validation still reports
`local_implementation_requires_deterministic_backend` for every concrete port,
including the new module: no `rules.persistence_backend` IR exists for
PostgreSQL yet. That is the next repair and is recorded as an open item in
`30_modules_persistence_boundary.md`.

## `holded_publication`

- `holded_publication_persistence` owns `PostgresHoldedPublicationRepository`.
- `reserve_publication(publication) -> HoldedPublication` becomes the plain
  append `insert_publication(publication) -> None` with uniqueness on
  `publication_id` and on the card revision plus idempotency key.
- `save_transition(publication) -> None` becomes `update_publication`: a
  field update of `status`, `external_document_id`, `completed_at`, and
  `safe_outcome_code` for an existing row; it never inserts or changes the
  binding fields.
- `HoldedPublicationService.request_holded_publication` states the reuse
  rule (same card revision and idempotency key), rejects a different active
  publication with `HoldedPublicationIneligibleError`, and inserts otherwise.
  Both `request_holded_publication` and `reconcile_holded_publication` now
  write a transition only from the reloaded locked status along an accepted
  transition and raise `HoldedReconciliationRequiredError` for a stale,
  skipped, or conflicting one.

Deterministic review: `models` 87/89, `holded_publication` 7 contracts /
28 notes, `holded_publication_persistence` 10/10, `bootstrap` 4/24 — zero
blocks, zero prompts. Adversarial review: `update_publication` cannot be an
upsert or a no-op; the service cannot skip the status re-read; no public
operation, rule, or model changed. Result: `PASS_INTERNAL_VARIATION` for
`holded_publication`, `PASS` for the others.

Slice hashes of modules whose notes follow the inserted service notes were
refreshed: their packets changed only in note index numbers, not in content.

## `registry_context`

- `registry_context_persistence` owns `PostgresRegistryContextRepository`.
- `merge_work_objects(work_objects)` is replaced by `list_work_objects() ->
  tuple[WorkObject, ...]` (stable `project_id` order) and the keyed
  `upsert_work_objects(work_objects)`: insert by `project_id` or update only
  `registry_snapshot_id`, `last_seen_at`, and `attention_status`; never delete
  a row or change `first_seen_at`.
- `RegistryContextService.refresh_registry_context` now states the merge
  itself: list, derive new / refreshed / unresolved objects by stable
  `project_id`, keep Cabinet-owned fields, upsert in one transaction.

Deterministic review: `models` 88/90, `registry_context` 9/30,
`registry_context_persistence` 10/10, `bootstrap` 4/24 — zero blocks, zero
prompts. Adversarial review: the upsert cannot delete or reset
`first_seen_at`; the service cannot treat absence as deletion; rules 5–11 of
the WorkObject decision are preserved. Result: `PASS_INTERNAL_VARIATION` for
`registry_context`, `PASS` for the others.

Open item recorded in `30_modules_persistence_boundary.md`:
`RegistryProjectSnapshot` is not a persisted model although
`WorkObject.registry_snapshot_id` references it. Pre-existing; not resolved
here.

## `holded_gateway`

- `holded_gateway_persistence` owns `PostgresHoldedAttemptRepository`.
- `reserve_attempt` becomes the plain append `insert_attempt` (uniqueness on
  `publication_attempt_id` and `attempt_marker`); `mark_request_issued` and
  `append_attempt_outcome` collapse into one field update `update_attempt`
  of `request_started_at`, `request_finished_at`, `outcome`, `document_id`,
  `safe_error_code`; `append_lookup_evidence` becomes the plain append
  `insert_lookup_evidence`.
- State 1 repair: `HoldedPurchaseLookupEvidence` was appended durably but not
  classified as persisted; it is now `issued` evidence keyed by
  `attempt_marker` and `observed_at` (`01_models_holded_gateway_runtime.md`,
  `60_data_closure*.json`).
- `HoldedGatewayService.create_holded_purchase` now states reservation
  equivalence (publication identity, revision hash, payload hash, marker),
  the issuance re-read before the sole POST, and the outcome update from the
  reloaded issued state; `lookup_holded_purchase` resolves the attempt by
  unique marker itself.

Deterministic review: `models` 87/89, `holded_gateway` 5/14,
`holded_gateway_persistence` 10/10, `holded_publication` 7/28, `bootstrap`
4/24 — zero blocks, zero prompts. Adversarial review: a second POST is still
impossible without an issuance record; `update_attempt` cannot change the
identity or hash fields; evidence rows cannot be deleted. Result:
`PASS_INTERNAL_VARIATION` for `holded_gateway`, `PASS` for the others.

## `synchronization`

- `synchronization_persistence` owns `PostgresSynchronizationRepository`;
  `HttpxVpsSynchronizationTransport` stays in `synchronization` until its
  own transport backend exists.
- `reserve_synchronization` → `insert_synchronization` plus
  `load_synchronization_by_idempotency`; `mark_transfer_issued` and
  `save_synchronization_outcome` → one field update `update_synchronization`
  (`status`, `started_at`, `finished_at`, `safe_error_code`);
  `reserve_catalogue_publication` → `insert_catalogue_publication` plus
  `load_catalogue_publication_by_idempotency`; `save_catalogue_acknowledgement`
  → `update_catalogue_publication`; `append_connection_observation` →
  `insert_connection_observation`.
- State 1 repair: `VpsConnectionObservation` is appended durably and is now
  classified as persisted `issued` evidence keyed by `observed_at`.
- `SynchronizationService.synchronize_invoice_work` and
  `publish_registry_catalogue` now state reuse equivalence, the issuance
  re-read before transport, and the outcome/acknowledgement update from the
  reloaded locked row. `SynchronizationOutcome` and
  `VpsCatalogueAcknowledgement` remain service/transport values; their
  persisted parts are the rows above.
- Unchanged and recorded as open: `load_sync_status` (composite observation)
  and the missing storage behind `get_working_set_membership` — no persisted
  model carries `working_set_id`, and the fresh working set is an open
  product question.

Deterministic review: `models` 88/90, `synchronization` 18/32,
`synchronization_persistence` 14/14, `retention_release` 7/24, `bootstrap`
4/24 — zero blocks, zero prompts. Adversarial review: a second transfer is
impossible without an issuance record; updates cannot change identity or
binding fields; evidence rows cannot be deleted. Result:
`PASS_INTERNAL_VARIATION` for `synchronization`, `PASS` for the others.

## `plan_actual`

- `plan_actual_persistence` owns `PostgresPlanActualRepository`.
- `load_match_decisions` becomes a plain set read in stable match-id order;
  `calculate_plan_actual` raises `PlanActualPreconditionError` when a pinned
  `match_id` is absent.
- `save_match_decision` becomes `insert_match_decision` (uniqueness on
  `match_id`), `update_match_status` (status fields of an existing match, for
  invalidation), and `list_matches_for_line`; `record_match_decision` lists
  the line's decisions under the line lock and rejects a second active
  confirmation with `PlanActualPreconditionError`.

Deterministic review: `models` 90/92, `plan_actual` 11/33,
`plan_actual_persistence` 15/15, `bootstrap` 4/24 — zero blocks, zero
prompts. Adversarial review: history cannot be deleted or replaced; the
invariant cannot be skipped because the service must list before writing;
absent pinned identities cannot silently shrink an analysis. Result:
`PASS_INTERNAL_VARIATION` for `plan_actual`, `PASS` for the others.

## `durable_archive`

- `durable_archive_persistence` owns `PostgresArchiveUnitOfWork`;
  `LocalFilesystemSourceByteStore` stays in `durable_archive` until it is
  bound to `binary_storage_backend`.
- `save_publication` → `insert_publication`; `mark_publication_published`
  and `mark_publication_failed` → `update_publication_state` plus
  `load_publication`; the `rules.archive_byte_publication` state machine is
  now stated on `attach_local_source` and `recover_pending_publications`
  (advance only from the reloaded state; never published → failed).
- `save_transfer_acceptance` → `insert_transfer_manifest`,
  `insert_card_revision`, `insert_source_replicas`, `insert_transfer_receipt`
  composed by `accept_transfer_manifest` in the one open transaction;
  `save_source_attachment` → `insert_source_binary` (uniqueness on
  `source_id` and on `invoice_id` + `content_hash`), `insert_source_replicas`,
  `insert_publication`.
- Storage gap closed: the `StoredInvoiceCard` head had no reader or writer
  and revision succession had no writer; `load_invoice_card`,
  `upsert_invoice_card`, and `update_card_revision_succession` are added and
  `accept_transfer_manifest` states when they are used.

Deterministic review: `models` 96/98, `durable_archive` 14/44,
`durable_archive_persistence` 23/23, `api` 14/22, `api_irregular` 2/5,
`bootstrap` 4/24 — zero blocks, zero prompts. Adversarial review: no
publication can reach `published` without a `metadata_committed` row and a
verified final byte; partial acceptance cannot be exposed because every
append is inside the invoice-locked transaction committed once; conflicting
bytes for one source identity cannot both commit. Result:
`PASS_INTERNAL_VARIATION` for `durable_archive`, `PASS` for the others.

## `retention_release_persistence` — deterministic backend

First module lowered through `persistence_backend/v3`: tables
`vps_release_evaluations` (key `project_id, working_set_id, evaluated_at`)
and `vps_release_decisions` (key `decision_id`, unique
`project_id, working_set_id`); rows `lock_working_set` (lock),
`save_evaluation` (insert), `load_decision` (get_unique, error on multiple),
`insert_decision` (insert); nested `actor`/`evaluation` stored as
`json_model`, evidence tuples as `json`. `create_retention_release_schema`
is the owned-transaction schema function. Factory canonical validation no
longer reports the module; the Factory emitter produces the module from this
spec without an LLM pass.

## Deterministic backend for all seven persistence modules

`70_persistence_closure.json` (status `closed`) carries the complete
`persistence_backend/v3` IR and `rules.persistence_backend` equals it: 22
tables, 7 owned-transaction repositories, 62 method rows. Every
`<x>_persistence` module is emitted by the Factory's `postgres_sync_v1`
without an LLM pass; Factory canonical validation reports only the three
ports outside persistence (`PostgresAccessControlBackend`,
`LocalFilesystemSourceByteStore`, `HttpxVpsSynchronizationTransport`).

Contract adjustments made while closing the IR (each is a storage-shape
consequence, not a policy change):

- `ArchiveUnitOfWork.load_pending_publications()` →
  `list_publications_in_states(states)`; the pending set comes from
  `rules.archive_byte_publication` in `recover_pending_publications`;
- `ArchiveUnitOfWork.load_transfer_receipt(invoice_id, hash | None)` →
  `list_transfer_receipts(invoice_id)`; selection by accepted hash in
  `verify_durable_acceptance`;
- `ArchiveUnitOfWork.load_card_revision` takes an exact `content_hash`; the
  current revision is resolved through the `StoredInvoiceCard` head;
- `ArchiveUnitOfWork.load_source_replicas(invoice_id)` →
  `list_source_replicas(source_ids)`: a replica row carries no invoice id;
- `SynchronizationRepository.load_sync_status` →
  `list_synchronizations_for_invoice`; `get_sync_status` composes;
- `PlanActualRepository.list_active_matches(project_id, snapshot)` →
  `list_matches_for_snapshot(snapshot, status)`: a match row carries no
  project id, and the active status is policy;
- State 1: `StoredInvoiceCardRevision.revision_id` — a persisted entity
  needs a scalar key; the revision reference stays the domain identity and is
  unique by `invoice_id` + `content_hash` (json-path unique index).

Keys inside nested references (`card_revision`, `invoice_revision`,
`revision`) are addressed with v3 `path` terms; nested values are stored as
`json_model`, evidence tuples as `json`, scalar tuples and canonical cards as
`json_value`.

Adversarial review of the emitted modules: every method runs only on the
active owned transaction and raises without one; locks are advisory
transaction-scoped over `(scope, keys)`, so a lock before the first insert
of a key is honoured; `update_*` rows never touch identity or binding
columns; `upsert_*` rows never touch `first_received_at`/`first_seen_at`;
no method deletes. Result: `PASS` for all seven persistence modules.

## `source_byte_store` — deterministic backend

`LocalFilesystemSourceByteStore` moved out of `durable_archive` into
`source_byte_store` and is emitted from `rules.source_byte_store_backend`
(SPEC_STANDARD §6.5), whose `layout` restates decision A70: staging written
exclusively and verified by reopen, final reference
`final/<hash[:2]>/<hash>`, same-filesystem rename, existing final reused only
after exact verification and never overwritten, only staging ever removed.
`SourceByteStore.final_reference_for(expected_hash)` was added so the store
owns its layout and `attach_local_source` never composes paths. The Factory
emitter is exercised against a real filesystem, including traversal,
tampered-final, and idempotent staging removal cases. Result: `PASS`.

## `access_control` — policy, storage, mechanism

`PostgresAccessControlBackend` mixed three owners and is split:

- `access_control_persistence` — `PostgresAccessControlRepository`
  (`persistence_backend/v3`): four tables, principal and abuse-context locks,
  plain reads, appends, field updates, one keyed upsert of throttle state;
- `credential_security` — `credential_security_backend/v2`: random secret,
  `credential_id.secret` token, Argon2id verifier over
  `HMAC-SHA256(pepper, secret)`, constant-time check;
- `access_control` — `LocalAccessControlService(repository, credential_pepper)`,
  the `policy` implementation of `AccessControlBackend` (SPEC_STANDARD §5.1):
  progressive delay and temporary block from `rules.access_control`, exact
  capability match against reread state, atomic enrol/rotate/revoke, audit
  evidence in the same transaction. Its `__init__` takes only a port and a
  scalar, so it owns no executable boundary and is generated as a behavioral
  module.

Adversarial review: the service cannot bypass throttling (throttle state is
locked and upserted on every outcome); the verifier is never compared outside
`verify_service_secret`; tokens and pepper never reach storage or logs;
revocation is an update that never deletes history. Result:
`PASS_INTERNAL_VARIATION` for `access_control`, `PASS` for the two
deterministic modules.

## `VpsSynchronizationTransport` — external

Inspection of the VPS (`cabinet-dev`, 2026-08-22) found static JSON behind
nginx Basic Auth and an MCP tunnel; no synchronization HTTP API, no node
credential, no receipts or acknowledgements. A transport emitter without a
verified wire contract would be a guess, so `HttpxVpsSynchronizationTransport`
is removed and the port is `disposition: external`:
`create_local_app(vps_transport: VpsSynchronizationTransport)` receives the
implementation and fails closed on None. Factory canonical validation of the
assembled specification now reports no issues. Building the VPS sync API and
its experiment is a separate project; the transport then returns as a
deterministic backend like Holded.

## Invoice Card V1 projection and monetary basis (semantic-oracle finding)

The first oracle run showed every consumer of `canonical_card` guessing at
its shape. State 1 now projects the accepted card format (M79–M87, M01
refinement) and `canonical_card` is typed; the plan/actual basis becomes a
fact of each estimate item (`currency`, `monetary_basis`) and of the line
(`net_amount`/`gross_amount`); `CardObjectAssignmentObservation` gets
`observation_id` and storage, and `validate_card_assignment` reads the
project from it. Deterministic review: zero blocks and zero prompts on every
changed slice; both persistence modules emit with the new json_model columns.
