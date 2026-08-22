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
