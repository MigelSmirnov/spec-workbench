# State 4 refinement — publish Registry catalogue to Cabinet Web

## Trigger

A verified full Registry project observation has produced a new immutable compact
catalogue, or an exact earlier catalogue requires idempotent redelivery.

## Steps

1. `module:registry_context` produces the accepted compact ordered projection
   from the full Registry observation.
2. `module:synchronization` binds the exact catalogue identity, canonical
   content hash, count and target Cabinet Web node to a durable publication
   attempt.
3. The authenticated VPS transport sends one
   `RegistryCatalogueDelivery` without adding, filtering or changing Registry
   facts.
4. Cabinet Web validates the entire V1 envelope before persistence.
5. Cabinet Web atomically stores the accepted snapshot and returns an
   acknowledgement containing catalogue identity, content hash and typed
   acceptance outcome.
6. Backend persists the acknowledgement. Unknown transport outcome is reconciled
   by exact catalogue identity; it does not authorize creation of a different
   delivery.
7. Cabinet Web rebuilds its project view by joining Web-owned Project Card links
   to Registry `project_id`. Unlinked Cards remain visible for manual matching.

## Outcomes

- `accepted`;
- `already_accepted`;
- `rejected_contract`;
- `catalogue_identity_conflict`;
- explicit unavailable or unknown transport outcome.

No outcome transfers Web-owned statistics to Backend or mutates Registry.
