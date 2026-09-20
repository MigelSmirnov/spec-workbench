# Record-owning notes — open design points

These gaps were exposed while wiring State 7 notes to the closed `OperationalUnitOfWork` port. They are recorded rather than filled with invented records, fields, or operations.

## operation_bindings

- `accept_binding_version` — needs a durable binding-version acceptance record. Required because the note requires immutable acceptance evidence, but no acceptance record model or port operation exists.
- `sweep_manifest_drift` — needs durable suspension/reissue evidence. Required because the drift sweep requires suspension and automatic-reissue records, but no such record model or insert operation exists.
- `retire_binding` — needs durable retirement actor, instant, and reason fields. Required because the note requires replay of the first retirement, but OperationBinding has no fields for those facts.

## owner_authority

- `authorization_for_effect` — needs an attempt identity for single-use approval consumption and an atomic active-grant absence guard. Required because the contract lacks map index/attempt identity and the port cannot guard insertion on absence of an active grant.
- `request_approval` — needs fields for flow version, mapped elements, file previews, owner statement, and request time. Required because the note requires the complete approval preview to remain bound, but EffectApproval has no carrier for these facts.
- `waiting_for_owner` — needs bounded set-filtered pagination across approvals and grants. Required because the view requires IN-set filters and one cursor across two record families, while the port offers only single-field lists.

## run_executor

- `advance_run` — needs a durable in-flight effect-attempt record. Required because the executor must persist the pre-send attempt, but no record model or port operation exists.
- `resume_runs` — needs a durable in-flight effect-attempt record. Required because recovery must reconcile the pre-send attempt, but no record model or port operation exists.

## semantic_vocabulary

- `seed_vocabulary` — needs an unfiltered empty-registry probe and the installation-seed actor/time. Required because the note requires installation only when the governed registry is empty, while the port exposes only filtered lists; State 1 revisions require issued_at and accepted_by.
- `find_duplicate_revision` — needs content-keyed revision lookup without a stable entry id. Required because the note requires a registry-wide exact-content duplicate search, while the port lists revisions only by axis_id, term_id, or relation_id.
- `retire_entry` — needs durable retirement actor, instant, and reason fields. Required because the note requires exact replay of the first retirement, but SemanticAxis, SemanticTerm, and SemanticRelation persist only status for retirement.

## slot_registry

- `submit_implementation` — needs a named durable carrier for implementation code bytes. Required because Implementation stores only code_ref, while the note requires storing and later resolving verified executable bytes.

## trace_journal

- `record_node_execution` — needs the slot/contract evidence fields and the node-execution identity recipe. Required because the note requires slot-scoped evidence and idempotent attempt identity, but NodeExecution lacks the slot/contract fields and no identity recipe is stated.
