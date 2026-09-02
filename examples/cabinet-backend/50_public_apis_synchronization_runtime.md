# State 5 repair — synchronization runtime public operations

## Refined — `public_op:synchronization.synchronize_invoice_work`

Owner: `module:synchronization`.

Receives one exact work selection and node identity through the cohesive service.
It durably reserves the attempt before transport, preserves explicit failure or
unknown states, and sends an exact delivered package through archive acceptance
and verification before returning.

## Refined — `public_op:synchronization.get_sync_status`

Owner: `module:synchronization`.

Reads the PostgreSQL-authoritative attempt/replica observation for exact invoice
and node identities. Missing, stale, unavailable, and unknown evidence remain
explicit; a default synchronized result is forbidden.

## `public_op:synchronization.reconcile_transfer_outcome`

### Owner
`module:synchronization`

### Callers
Synchronization scheduler/adapter.

### Inputs
Exact `synchronization_id` of one persisted transfer outcome whose result is unknown.

### Outputs
Updated `SynchronizationOutcome` — either a classified resolved result or an explicitly still-unknown state.

### Observable effect
Performs bounded read-only remote reconciliation for the exact persisted unknown outcome and records the new observation atomically.

### Enforces
Exact attempt targeting, read-only remote evidence gathering, no second transfer, no manufactured archive acceptance, and atomic recording of the observation.

### Errors
Failure to load the exact persisted outcome or to durably record the reconciliation observation. Remote evidence that cannot be classified stays an explicit unknown state in `SynchronizationOutcome` rather than becoming implicit success.

### State impact
Mutates synchronization attempt/receipt observation state only; durable acceptance remains owned by `module:durable_archive`.

## `public_op:catalogue_publication.publish_registry_catalogue`

### Owner
`module:catalogue_publication`

### Callers
Registry refresh scheduler/adapter.

### Inputs
One exact already-produced ordered `RegistryCatalogueDelivery`.

### Outputs
Persisted `RegistryCataloguePublication` state for the delivery — accepted, rejected with an explicit reason, or the idempotently equivalent existing publication.

### Observable effect
Publishes the delivery under a durable idempotency binding and records its publication state.

### Enforces
Durable idempotency of the delivery binding, exact ordered-content identity, and separation of transport from truth: the operation never constructs or filters Registry truth.

### Errors
Failure to persist the publication binding at all. A conflicting reuse of the same idempotency binding with different content and a delivery that fails acceptance checks are recorded rejections in the returned publication state, not silent success.

### State impact
Mutates catalogue publication/replica evidence only; Registry truth and archive state remain untouched.

## `public_op:synchronization.observe_vps_connection`

### Owner
`module:synchronization`

### Callers
Synchronization scheduler/adapter.

### Inputs
None beyond the cohesive service context.

### Outputs
Typed `VpsConnectionObservation` describing one authenticated connection attempt.

### Observable effect
Performs one read-only authenticated connection observation.

### Enforces
Read-only observation: no transfer, catalogue, archive, or Registry business state changes; authentication failure is an explicit observation state.

### Errors
Failure to construct the typed observation at all. Unreachable or unauthenticated remote states are explicit values of `VpsConnectionObservation`, not exceptions.

### State impact
None on business state; at most connection-observation evidence.
