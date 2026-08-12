# Cabinet Backend — Stage 7.1 Flow 1 semantic review

Flow: `flow:synchronize_invoice_to_local_archive`

Status: **AMBIGUITY — not semantic_closed**

This review applies the protocol in `skills/spec-authoring/STAGE_7_1_SEMANTIC_HANDOFF.md` to the first Cabinet handoff flow. It records the finding before any upstream repair.

## Reviewed semantic slice

- `00_product.md`
- `01_models.md`
- `01_models_contract_support.md`
- relevant synchronization/archive State 2 rules
- `30_modules.md`
- `40_flows.md`
- `50_public_apis.md`
- `60_contract_plan.json`
- `60_contracts.json`
- `60_data_closure.json`
- `60_exception_taxonomy.json`
- `80_notes.md`
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

`module:synchronization` owns authenticated transfer, transfer identity, delivery state and reconciliation. `module:durable_archive` alone owns the acceptance decision and authoritative durable-local proof.

The State 1 support model is capable of preserving this distinction because `SynchronizationOutcome` contains:

- `synchronization: InvoiceSynchronization`;
- `receipt: InvoiceTransferReceipt | None`;
- `durable_acceptance: DurableAcceptanceVerification | None`.

Therefore this finding is not caused by a missing result type.

## Adversarial ambiguity question

> Construct the strongest materially different alternative observable semantics that still satisfies the complete specification slice.

### Interpretation A — transport-only completion

`synchronize_invoice_work` authenticates, obtains/transfers the exact work package, records a delivered `InvoiceSynchronization`, and returns:

```text
SynchronizationOutcome(
  synchronization=<delivered>,
  receipt=None,
  durable_acceptance=None,
)
```

No generated callable is required by its current State 5 operation description or State 7 notes to invoke `accept_transfer_manifest` for the delivered package or to invoke `verify_durable_acceptance` after an accepted/already-accepted receipt.

The result truthfully avoids claiming durable acceptance, so the existing delivery-versus-acceptance rule is not violated.

### Interpretation B — complete local-custody synchronization

`synchronize_invoice_work` performs the same transport work, then orchestrates the delivered exact manifest/card/source evidence through `durable_archive.accept_transfer_manifest`. For accepted or already-accepted archive outcomes it obtains authoritative proof through `durable_archive.verify_durable_acceptance`, and returns the receipt/proof in `SynchronizationOutcome`.

This interpretation realizes the complete State 4 business flow and the Stage 7.1 handoff graph.

## Material difference

Both interpretations preserve the rule that delivery is not durable acceptance, but only Interpretation B can make the trigger "synchronize invoice to local archive" reach its accepted terminal business outcome in one generated flow.

Interpretation A can terminate after successful transport with no archive acceptance attempt at all. That is materially different observable behavior, not internal implementation variation.

## Why current downstream constraints do not close the gap

Current constraints are strong about what synchronization **must not claim**:

- transport delivery must not be promoted to durable acceptance;
- ambiguous transport outcomes remain reconcilable;
- classified transport failures must not become accepted outcomes.

They are not yet strong about what the owning flow **must do after a delivered exact package**.

`accept_transfer_manifest` correctly owns archive policy, but its existence and its `Callers: module:synchronization` declaration do not by themselves force the generated synchronization callable to invoke it on the delivered branch.

Likewise, `verify_durable_acceptance` correctly owns authoritative proof, but the current synchronization notes do not require the accepted/already-accepted branch to obtain that proof before exposing durable acceptance in `SynchronizationOutcome`.

## Placeholder-resistance result

Status: **PLACEHOLDER_RISK** for the complete Flow 1 business promise.

A transport-only implementation is not a syntactic stub, but it is a semantic skeleton for the end-to-end flow: it may stop after transport and leave both archive fields empty on every delivered result while still satisfying the current synchronization-local notes.

The individual archive callables are not themselves shown to be placeholder-permitting by this finding; the gap is orchestration ownership between the transport result and those archive operations.

## Finding record

```text
flow: flow:synchronize_invoice_to_local_archive
status: AMBIGUITY
material_alternative_found: yes
placeholder_implementation_found: yes
scenario_gaps:
  - S1 is not derivable from the current generated-callable obligations because no callable is forced to hand delivered evidence to durable_archive.
  - The accepted/already-accepted branch is not forced to obtain authoritative durable verification before durable_acceptance is populated.
findings:
  - owner: upstream_business
    scope: synchronization orchestration ownership at State 3/5, propagated to State 7 notes
    interpretation_A: delivered transport may terminate with receipt=None and durable_acceptance=None without any archive acceptance attempt
    interpretation_B: delivered exact package must be handed to durable_archive; accepted/already-accepted receipt must be followed by authoritative durable verification
    required_resolution: make one existing generated callable explicitly own this cross-module sequencing while preserving durable_archive as the sole owner of the acceptance decision
```

## Earliest repair owner

The earliest affected design state is **State 3 module responsibility / State 5 public-operation semantics**, not State 1 and not the contract signature.

Recommended repair:

1. Keep `module:durable_archive` as the sole owner of acceptance policy and durable proof.
2. Make `module:synchronization` explicitly own orchestration of the delivered exact package across that existing public boundary as part of `synchronize_invoice_work`.
3. State that a delivered exact package must be presented to `accept_transfer_manifest`; transport-only termination is valid only when the transport branch itself is non-delivered/unresolved or the archive returns a classified non-accepted outcome.
4. For `accepted` / `already_accepted` receipts, require `verify_durable_acceptance` before `SynchronizationOutcome.durable_acceptance` may carry positive proof.
5. Propagate the obligation into the State 5 operation and State 7 `[ORCHESTRATION]` notes.
6. Re-run S1–S4 and the adversarial ambiguity question after repair.

This repair adds no new business behavior. It makes the already accepted State 4 sequence generation-obligatory.

## Flow 1 gate

`semantic_closed`: **no**

Do not mark Flow 1 closed until the upstream orchestration obligation is repaired and the full slice is reviewed again.