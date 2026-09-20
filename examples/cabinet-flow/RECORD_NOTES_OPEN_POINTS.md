# Record-owning notes — open design points

These gaps were exposed while wiring State 7 notes to the closed `OperationalUnitOfWork` port. They are recorded rather than filled with invented records, fields, or operations.


## owner_authority

- `request_approval` — needs fields for flow version, mapped elements, file previews, owner statement, and request time. Required because the note requires the complete approval preview to remain bound, but EffectApproval has no carrier for these facts.


## semantic_vocabulary

- `seed_vocabulary` — needs an unfiltered empty-registry probe and the installation-seed actor/time. Required because the note requires installation only when the governed registry is empty, while the port exposes only filtered lists; State 1 revisions require issued_at and accepted_by.
- `find_duplicate_revision` — needs content-keyed revision lookup without a stable entry id. Required because the note requires a registry-wide exact-content duplicate search, while the port lists revisions only by axis_id, term_id, or relation_id.
- `retire_entry` — needs durable retirement actor, instant, and reason fields. Required because the note requires exact replay of the first retirement, but SemanticAxis, SemanticTerm, and SemanticRelation persist only status for retirement.

## slot_registry

- `submit_implementation` — needs a named durable carrier for implementation code bytes. Required because Implementation stores only code_ref, while the note requires storing and later resolving verified executable bytes.

## trace_journal

- `record_node_execution` — needs the slot/contract evidence fields and the node-execution identity recipe. Required because the note requires slot-scoped evidence and idempotent attempt identity, but NodeExecution lacks the slot/contract fields and no identity recipe is stated.

## trial_corpus

- `capture_trial_case` — needs a durable origin reference on TrialCase. Required because the note requires captured_from_run, but TrialCase has no origin field.
- `withdraw_trial_case` — needs a lookup proving whether the case contributed to an admitted verdict. Required because the note requires this owner-only guard, but no port operation links a TrialCase to admitted evidence.

## value_store

- `put_value` — needs a durable retention-reference record and durable content bytes. Required because the note appends retention independently of immutable StoredValue metadata, but no retention record exists and content bytes have no named carrier.
- `expire_values` — needs retention-reference access and a delete operation for eligible value bytes. Required because the note evaluates every live retention reference and removes bytes, but the record and delete operation do not exist.
