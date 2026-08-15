# State 5 repair — synchronization runtime public operations

## `public_op:synchronization.synchronize_invoice_work`

Receives one exact work selection and node identity through the cohesive service.
It durably reserves the attempt before transport, preserves explicit failure or
unknown states, and sends an exact delivered package through archive acceptance
and verification before returning.

## `public_op:synchronization.get_sync_status`

Reads the PostgreSQL-authoritative attempt/replica observation for exact invoice
and node identities. Missing, stale, unavailable, and unknown evidence remain
explicit; a default synchronized result is forbidden.

## `public_op:synchronization.reconcile_transfer_outcome`

Performs bounded read-only remote reconciliation for an exact persisted unknown
outcome and records the new observation atomically. It never issues a second
transfer and never manufactures archive acceptance.

## `public_op:synchronization.publish_registry_catalogue`

Publishes one exact ordered Registry catalogue delivery under a durable
idempotency binding and returns its persisted publication state. It does not
construct or filter Registry truth.

## `public_op:synchronization.observe_vps_connection`

Returns a typed read-only authenticated connection observation without changing
transfer, catalogue, archive, or Registry business state.
