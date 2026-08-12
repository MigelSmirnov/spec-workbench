# State 3 repair — Flow 1 synchronization orchestration ownership

## Status

Accepted bounded State 3 repair discovered by Stage 7.1 semantic E2E review of `flow:synchronize_invoice_to_local_archive`.

This document refines `30_modules.md`. It introduces no new product behavior and does not transfer archive policy into `module:synchronization`.

## Finding being repaired

The base State 3 responsibility split correctly says that `module:synchronization` owns transport and that `module:durable_archive` alone owns durable acceptance. However, it did not explicitly assign ownership of the cross-module sequencing required after a successful delivered transfer.

Without that sequencing obligation, a generated `synchronize_invoice_work` could truthfully return a delivered transport outcome with no archive acceptance attempt, leaving `SynchronizationOutcome.receipt` and `SynchronizationOutcome.durable_acceptance` empty forever while still respecting the rule that delivery is not acceptance.

That behavior contradicts the accepted State 4 end-to-end flow.

## Refinement to `module:synchronization`

### Owns — additional orchestration responsibility

For `flow:synchronize_invoice_to_local_archive`, `module:synchronization` owns the application-level sequencing that carries one exact delivered transfer package across the existing `module:durable_archive` public boundary.

After transport has produced an exact **delivered** manifest/card/source package, synchronization MUST:

1. present that exact package to `capability:durable_archive.accept_transfer_manifest`;
2. preserve the returned `InvoiceTransferReceipt` in the public synchronization outcome;
3. when the receipt is `accepted` or `already_accepted`, obtain authoritative local proof through `capability:durable_archive.verify_durable_acceptance` for the same exact invoice revision/evidence identity;
4. preserve that verification in `SynchronizationOutcome.durable_acceptance`;
5. never synthesize a positive durable proof from delivery, receipt presence, or transport evidence.

A transport branch that is authentication-failed, incompatible, unavailable, failed, or unresolved/ambiguous does not manufacture an archive acceptance attempt merely to fill result fields. Its transport state remains explicit and reconcilable.

A delivered package may terminate without positive durable acceptance only because `durable_archive` returned a classified non-accepted result or authoritative verification remained non-positive/not-verifiable. It may not terminate merely because synchronization omitted the archive boundary call.

### Must not own — unchanged policy boundary

This orchestration responsibility does **not** allow `module:synchronization` to decide:

- Card validity;
- source integrity;
- duplicate handling;
- quarantine policy;
- atomic archive visibility;
- whether an import is `accepted` or `already_accepted`;
- whether durable-local evidence is sufficient for positive verification.

Those decisions remain exclusively owned by `module:durable_archive`.

## Dependency refinement

For this flow the conceptual dependency is explicitly:

```text
synchronize_invoice_work
    -> durable_archive.accept_transfer_manifest
    -> durable_archive.verify_durable_acceptance
```

The arrows are orchestration dependencies, not policy ownership transfer.

## Ownership invariant

`module:synchronization` owns **whether the accepted archive boundary is invoked at the required point in the flow**.

`module:durable_archive` owns **what the archive decision and durable proof are**.

Therefore both of these are forbidden:

- treating `delivered` as `accepted`;
- treating successful delivery as a terminal completion while silently skipping the required archive acceptance boundary.

## Propagation

This refinement must be reflected in:

- State 5 semantics of `public_op:synchronization.synchronize_invoice_work`;
- State 7 generation notes for `synchronize_invoice_work`;
- Stage 7.1 Flow 1 semantic review.

No State 6 contract change is required because `SynchronizationOutcome` already carries `receipt` and `durable_acceptance` separately.
