# Record-owning notes — open design points

These gaps were exposed while wiring State 7 notes to the closed `OperationalUnitOfWork` port. They are recorded rather than filled with invented records, fields, or operations.

## operation_bindings

- `accept_binding_version` — needs a durable binding-version acceptance record. Required because the note requires immutable acceptance evidence, but no acceptance record model or port operation exists.
- `sweep_manifest_drift` — needs durable suspension/reissue evidence. Required because the drift sweep requires suspension and automatic-reissue records, but no such record model or insert operation exists.
- `retire_binding` — needs durable retirement actor, instant, and reason fields. Required because the note requires replay of the first retirement, but OperationBinding has no fields for those facts.
