# State 5 repair — Flow 1 public synchronization semantics

## Status

Accepted bounded State 5 repair discovered by Stage 7.1 review of `flow:synchronize_invoice_to_local_archive`.

This document refines `public_op:synchronization.synchronize_invoice_work` from `50_public_apis.md`. It changes no Python signature.

## Refined public operation

### `public_op:synchronization.synchronize_invoice_work`

#### Owner

`module:synchronization`.

#### Inputs

Unchanged: one exact synchronization work selection and synchronization-node context.

#### Required orchestration semantics

The operation owns the complete application sequencing of the accepted synchronization flow while delegating archive decisions to `module:durable_archive`.

For a transport outcome that has not produced an exact delivered package, the operation returns the explicit authentication/compatibility/transport/unavailability/unresolved state and does not fabricate archive evidence.

For an exact **delivered** package, the operation MUST present the exact manifest, immutable Card revision evidence, and required source evidence to `public_op:durable_archive.accept_transfer_manifest`.

It MUST preserve that returned `InvoiceTransferReceipt` in `SynchronizationOutcome.receipt`.

If and only if the receipt classifies the package as `accepted` or `already_accepted`, the operation MUST then call `public_op:durable_archive.verify_durable_acceptance` for the same exact invoice revision/evidence identity and preserve the resulting verification in `SynchronizationOutcome.durable_acceptance`.

A positive `durable_acceptance` is valid only when the archive verification itself is positive. Delivery or receipt presence alone is never proof.

A delivered package may return without positive durable proof when the archive returns a classified non-accepted receipt or authoritative verification is negative/not-verifiable. It may not return `receipt=None` merely because the archive acceptance step was skipped.

#### Outputs

`SynchronizationOutcome` continues to preserve three independent facts:

- synchronization/transport state;
- archive acceptance receipt when a delivered package reached the archive boundary;
- authoritative durable verification when the accepted/already-accepted branch was verified.

#### Observable effect

May perform authenticated transfer attempts, record transport observations, invoke the existing archive acceptance/verification boundary at the required point, and record the resulting receipt/proof references.

The operation does not implement archive validation, duplicate, quarantine, source-integrity, or durable-proof policy itself.

#### Errors and classified outcomes

Transport and reconciliation conditions that can be classified remain synchronization outcome states.

Archive validation, duplicate, integrity, incomplete, and quarantine conditions remain the `InvoiceTransferReceipt` returned by `durable_archive`.

System failures that prevent either owner from producing trustworthy evidence remain failures rather than manufactured success.

#### State impact

Synchronization state remains owned by `module:synchronization`; durable archive state remains owned by `module:durable_archive`.

The orchestration call crosses the module boundary without transferring state ownership.

## Contract impact

None. The existing State 6 contract remains:

```python
(selection: SynchronizationWorkSelection, node: CabinetNodeIdentity) -> SynchronizationOutcome
```

The existing State 1 support model already carries the required receipt and durable-verification fields.
