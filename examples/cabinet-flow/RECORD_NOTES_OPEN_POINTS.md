# Record-owning notes — open design points

These gaps were exposed while wiring State 7 notes to the closed `OperationalUnitOfWork` port. They are recorded rather than filled with invented records, fields, or operations.


## owner_authority

- `request_approval` — needs fields for flow version, mapped elements, file previews, owner statement, and request time. Required because the note requires the complete approval preview to remain bound, but EffectApproval has no carrier for these facts.


## semantic_vocabulary

- `retire_entry` — needs durable retirement actor, instant, and reason fields. Required because the note requires exact replay of the first retirement, but SemanticAxis, SemanticTerm, and SemanticRelation persist only status for retirement.

## slot_registry

- `submit_implementation` — needs a named durable carrier for implementation code bytes. Required because Implementation stores only code_ref, while the note requires storing and later resolving verified executable bytes.

## trace_journal

- `slot_evidence` — needs an `OperationalUnitOfWork` list operation keyed by `contract_version_ref`. Required because the note must select every concluded function attempt for the exact contract version, while the port exposes no list by that field; the existing load-by-id and lists by executed/grant/run reference cannot provide that bounded set.


## value_store

- `put_value` — needs a durable retention-reference record and durable content bytes. Required because the note appends retention independently of immutable StoredValue metadata, but no retention record exists and content bytes have no named carrier.
- `expire_values` — needs retention-reference access and a delete operation for eligible value bytes. Required because the note evaluates every live retention reference and removes bytes, but the record and delete operation do not exist.
