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
