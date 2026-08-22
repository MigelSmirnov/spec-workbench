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
