# State 5 repair — complete retention release operations

## `public_op:synchronization.get_working_set_membership`

Returns one exact read-only membership observation in stable invoice-revision
order. Unknown, unavailable, or stale membership is explicit and never inferred
from Registry status.

## `public_op:retention_release.evaluate_vps_release`

Through the cohesive service, resolves exact membership and requires exhaustive
positive synchronization and durable-local evidence before returning allowed.

## `public_op:retention_release.request_manual_vps_release`

Under the exact target lock, reloads membership and proof, rejects any change or
gap, then records or returns one equivalent immutable authorization decision.

## `public_op:retention_release.get_retention_status`

Returns the exact persisted release decision for one working set or no decision;
it makes no claim that physical release has completed.
