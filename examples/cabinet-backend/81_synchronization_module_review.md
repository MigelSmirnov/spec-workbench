# Cabinet Backend — Stage 8.1 synchronization module review

Module: `synchronization`

Status: **PASS_INTERNAL_VARIATION**

Slice SHA-256: `f35eabfe59b3257932de48d0ee2148b57896cb06bd3bb76c6c83bc7816d92d89`

Structural review: 31 contracts, 45 notes, 0 blocks, 0 deterministic review prompts.

## Closed portion

The rebuilt packet preserves the accepted Flow 1 boundary. An exact delivered
package must cross `durable_archive.accept_transfer_manifest`; accepted or
already-accepted receipts must then cross authoritative durable verification.
Transport delivery cannot manufacture durable acceptance.

## Finding

The module responsibility owns authenticated VPS transport, durable delivery
state, unknown-outcome reconciliation, Registry catalogue delivery, and
connection observations. The lowered module exposes only
`synchronize_invoice_work` and `get_sync_status`.

No concrete VPS transport port, synchronization repository/unit-of-work,
credential/config boundary, or bootstrap composition is declared. The accepted
capabilities `publish_registry_catalogue`, `reconcile_transfer_outcome`, and
`observe_vps_connection` have no contracts or generation constraints.

Consequently, materially different observable implementations still satisfy the
packet. A generated module can fabricate an outcome from the selection, keep
attempt state only in process memory, return a default status observation, or
omit catalogue publication and reconciliation entirely without violating a
concrete runtime contract.

## Earliest repair owner

The repair begins at State 1/2 runtime evidence and deployment mechanism, then
propagates through State 3 ownership, State 5 public operations, State 6 typed
ports, State 7 notes, bootstrap composition, and `global_spec.json` last.

The proposed first-implementation lowering requires explicit owner acceptance:

- one Backend-initiated HTTPS VPS client with a dedicated synchronization node
  credential read only by bootstrap;
- one PostgreSQL synchronization repository using the existing Cabinet database;
- durable reservation before transfer, idempotency-key/manifest binding, and
  persisted unknown outcomes before read-only reconciliation;
- typed package, catalogue acknowledgement, reconciliation, and connection
  evidence with bounded responses and secret-free errors;
- fail-closed startup with no anonymous, in-memory, or service-locator fallback.

The proposed mechanism was accepted and propagated as A72.

## Repair and adversarial re-check

The assembled module now requires one exact `SynchronizationService` with a
PostgreSQL repository, authenticated outbound HTTPS transport, and the exact
composed archive service. Reservation precedes mutation; an issued request with
no conclusive response is durably `unknown_outcome`; reconciliation is read-only;
status cannot be fabricated; catalogue and connection capabilities are typed and
lowered; bootstrap fails closed without configuration.

A memory-only implementation, synthetic success/status result, repeated transfer
after ambiguity, anonymous transport, omitted catalogue capability, or alternate
archive runtime now violates explicit contracts and notes. Remaining freedom is
internal SQL layout, helper decomposition, serialization details within the typed
boundary, and retry timing for operations that do not replay mutations.

Classification: **PASS_INTERNAL_VARIATION**.

The final Stage 8.1 revalidation also adds a typed, read-only exact working-set
membership operation for retention coverage. It does not broaden synchronization
mutation authority and preserves the same classification.
