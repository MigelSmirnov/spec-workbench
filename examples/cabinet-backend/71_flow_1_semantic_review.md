# Cabinet Backend — Stage 7.1 Flow 1 semantic review

Flow: `flow:synchronize_invoice_to_local_archive`

Status: **semantic_closed**

This review applies the protocol in `skills/spec-authoring/STAGE_7_1_SEMANTIC_HANDOFF.md` to the first Cabinet handoff flow. The initial ambiguity was recorded before repair and then re-reviewed after bounded State 3, State 5, and State 7 corrections.

## Reviewed semantic slice

- `00_product.md`
- `01_models.md`
- `01_models_contract_support.md`
- relevant synchronization/archive State 2 rules
- `30_modules.md`
- `30_modules_flow1_semantic_repair.md`
- `40_flows.md`
- `50_public_apis.md`
- `50_public_apis_flow1_semantic_repair.md`
- `60_contract_plan.json`
- `60_contracts.json`
- `60_data_closure.json`
- `60_exception_taxonomy.json`
- `80_notes.md`
- `80_notes_flow1_semantic_repair.md`
- `71_semantic_e2e_handoff.md`

## Reconstructed accepted behavior

The accepted business flow distinguishes three materially different facts:

```text
transport delivery
    ↓ does not imply
archive acceptance receipt
    ↓ when accepted/already accepted
local durable verification
```

`module:synchronization` owns authenticated transfer, transfer identity, delivery state, reconciliation, and the application-level sequencing that crosses the accepted archive boundary after an exact delivered package exists.

`module:durable_archive` alone owns the archive acceptance classification and authoritative durable-local proof.

The State 1 support model preserves the distinction through `SynchronizationOutcome`:

- `synchronization: InvoiceSynchronization`;
- `receipt: InvoiceTransferReceipt | None`;
- `durable_acceptance: DurableAcceptanceVerification | None`.

No contract or result-model change was required.

## Initial Stage 7.1 finding

The original slice permitted two materially different implementations:

### Interpretation A — transport-only completion

`synchronize_invoice_work` could record a delivered transport result and return:

```text
SynchronizationOutcome(
  synchronization=<delivered>,
  receipt=None,
  durable_acceptance=None,
)
```

without ever presenting the delivered package to `durable_archive`.

### Interpretation B — complete local-custody synchronization

`synchronize_invoice_work` could perform the accepted State 4 sequence by presenting the exact delivered package to `accept_transfer_manifest` and, for accepted/already-accepted receipts, obtaining authoritative proof through `verify_durable_acceptance`.

Both interpretations respected the negative rule that delivery is not acceptance, but only Interpretation B fulfilled the end-to-end business promise. The original slice was therefore `AMBIGUITY` with a flow-level placeholder risk.

## Repair

The earliest affected owner was State 3 synchronization orchestration ownership, propagated to State 5 and State 7.

The repair establishes:

1. For an exact **delivered** package, `synchronize_invoice_work` MUST present the exact manifest/Card/source evidence to `durable_archive.accept_transfer_manifest`.
2. The returned `InvoiceTransferReceipt` MUST be preserved in `SynchronizationOutcome.receipt`.
3. For `accepted` or `already_accepted`, `synchronize_invoice_work` MUST obtain authoritative proof from `durable_archive.verify_durable_acceptance` for the same exact invoice revision/evidence identity.
4. Positive `SynchronizationOutcome.durable_acceptance` may come only from that authoritative archive verification.
5. Authentication failure, incompatibility, transport failure, remote unavailability, and unresolved/ambiguous delivery may return without archive evidence because no exact delivered package exists for acceptance.
6. A delivered package may lack positive durable acceptance only because the archive returned a classified non-accepted result or authoritative verification is negative/not-verifiable — never because synchronization silently skipped the archive boundary.
7. Archive validation, duplicate, integrity, quarantine, atomicity, and proof-sufficiency decisions remain exclusively owned by `durable_archive`.

Repair artifacts:

- `30_modules_flow1_semantic_repair.md`;
- `50_public_apis_flow1_semantic_repair.md`;
- `80_notes_flow1_semantic_repair.md`.

## Adversarial ambiguity re-check

> Construct the strongest materially different alternative observable semantics that still satisfies the repaired complete specification slice.

### Attempted alternative — delivered transport terminates without archive call

This is no longer conforming. The State 3 repair makes synchronization own the required cross-module sequencing, the State 5 repair requires the delivered branch to invoke archive acceptance, and the State 7 repair explicitly forbids a delivered result with `receipt=None` when the archive boundary was reachable and no archive call was attempted.

### Attempted alternative — accepted receipt returned without durable verification

This is no longer conforming. The repaired State 5/7 semantics require `verify_durable_acceptance` after `accepted` or `already_accepted` and prohibit manufacturing positive proof from receipt or transport evidence.

### Remaining implementation freedom

Implementations may differ internally in transport mechanism, persistence sequencing inside the owning modules, logging, retries permitted by accepted transport rules, and local helper decomposition. Those differences do not change the observable business semantics.

Classification: **PASS_INTERNAL_VARIATION**.

## Semantic pseudotest re-check

### S1 — successful transfer does not skip durable verification

**PASS.** Delivered exact evidence must reach `accept_transfer_manifest`; accepted/already-accepted receipt must then reach `verify_durable_acceptance`; transport evidence cannot substitute for proof.

### S2 — ambiguous transport outcome remains reconcilable

**PASS.** The original synchronization rules and notes preserve unresolved/ambiguous delivery as an explicit reconcilable synchronization state. The repair does not force a fabricated archive call when no exact delivered package exists.

### S3 — rejected archive evidence is not partially accepted

**PASS.** `durable_archive.accept_transfer_manifest` remains the sole acceptance owner and its existing notes require unsupported, integrity-invalid, conflicting, duplicate-review, incomplete, and quarantine-required evidence to remain classified non-accepted outcomes without partially exposing an accepted manifest set.

### S4 — repeated equivalent acceptance is idempotent

**PASS.** The archive acceptance notes require repeated equivalent acceptance not to create a second logical durable acceptance, while synchronization preserves the resulting receipt/proof instead of inventing another acceptance.

## Placeholder-resistance re-check

Status: **PASS** for Flow 1.

A transport-only semantic skeleton can no longer satisfy the repaired slice on the delivered branch. A conforming implementation must cross the archive acceptance boundary and, on accepted/already-accepted outcomes, the authoritative verification boundary.

The following trivial behaviors are therefore non-conforming for a delivered package:

- always returning `receipt=None`;
- always returning `durable_acceptance=None` after an accepted/already-accepted receipt;
- treating delivery as positive durable proof;
- blindly forwarding a transport outcome without the required archive sequencing.

The individual archive callables retain their existing non-placeholder behavioral constraints.

## Final review record

```text
flow: flow:synchronize_invoice_to_local_archive
status: semantic_closed
material_alternative_found: no
placeholder_implementation_found: no
scenario_gaps: []
findings:
  - owner: upstream_business
    scope: synchronization orchestration ownership at State 3/5, propagated to State 7 notes
    original_status: AMBIGUITY
    resolution: delivered exact package must cross durable_archive acceptance; accepted/already-accepted receipt must cross authoritative durable verification
    recheck: PASS_INTERNAL_VARIATION
```

## Flow 1 gate

`semantic_closed`: **yes**

The semantic scenarios S1–S4 are now eligible to be materialized as implementation-independent runtime acceptance tests during the Stage 7.1 test-artifact work. Those tests must preserve these accepted semantics and must not later be rewritten merely to match generated code.
