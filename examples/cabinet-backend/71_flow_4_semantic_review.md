# Cabinet Backend — Stage 7.1 Flow 4 semantic review

Flow: `flow:calculate_plan_actual`

Status: **semantic_closed**

This review applies `skills/spec-authoring/STAGE_7_1_SEMANTIC_HANDOFF.md` to Flow 4. The initial upstream business ambiguity was recorded before repair. The accepted State 2 plan/actual decision now closes the calculation semantics and has been propagated through State 1, State 3, State 5, and State 7.

## Reconstructed accepted behavior after repair

```text
exact accepted invoice revisions
+ exact Registry/WorkObject context
+ exact immutable EstimateSnapshot
+ confirmed match decisions only
+ explicit accepted assumptions
        ↓
calculate_plan_actual
        ↓
validate evidence identity, assignment, matches, unit/currency/basis comparability
        ├─ failed precondition -> PlanActualPreconditionError
        └─ valid -> deterministic non-placeholder PlanActualAnalysis
```

For every analysed Estimate Item:

```text
planned_quantity = EstimateItemSnapshot.quantity
actual_quantity = sum(confirmed-matched InvoiceLine.quantity)
quantity_variance = actual_quantity - planned_quantity
remaining_quantity = planned_quantity - actual_quantity

planned_amount = EstimateItemSnapshot.total
actual_amount = sum(confirmed-matched InvoiceLine.total)
amount_variance = actual_amount - planned_amount
```

For project totals:

```text
project_planned_amount = sum(analysed EstimateItemSnapshot.total)
matched_actual_amount = sum(confirmed-matched InvoiceLine.total)
unmatched_actual_amount = sum(explicit-unmatched InvoiceLine.total)
project_actual_amount = matched_actual_amount + unmatched_actual_amount
project_amount_variance = project_actual_amount - project_planned_amount
```

Unmatched lines never create placeholder Estimate Items and never increase the actual value of a matched item. Direct quantity comparison requires semantically identical units unless exact accepted conversion evidence is pinned. Direct money comparison requires compatible currency and monetary/tax basis unless exact accepted conversion/basis evidence is pinned. No forecast is synthesized without separately accepted forecast assumptions.

## Initial adversarial ambiguity

Before repair, two materially different interpretations remained legal:

- quantity-first matched-item analysis with remaining quantity and item variance;
- monetary-first aggregate analysis that could omit quantity/remaining semantics.

The same pinned evidence could also produce opposite variance signs, different monetary bases, different unmatched contribution, and even a provenance-only successful result.

That ambiguity was correctly classified as an upstream State 2 business gap rather than repaired only in Notes.

## Repair applied

1. State 2 now defines the exact plan/actual grain, source fields, aggregation, variance sign, remaining convention, unmatched contribution, comparability policy, project totals, semantic reproducibility, and forecast boundary.
2. State 1 now gives `PlanActualAnalysis` a mandatory non-placeholder baseline shape and introduces the derived per-item result shape.
3. State 3 assigns deterministic calculation and comparability enforcement to `module:plan_actual` without granting source-system mutation authority.
4. State 5 binds `calculate_plan_actual` to the accepted formulas and error semantics without changing its callable signature.
5. State 7 Notes prohibit alternate formulas, guessed conversions, placeholder success, or invented forecast values.

## Scenario rerun

### P1 — equal pinned evidence produces reproducible analysis

**PASS.** Semantic equality now covers the mandatory per-item quantities/amounts/variances/remaining values, unmatched identities/amount, project totals, and deterministic warning codes. Runtime timestamps/cache metadata are explicitly excluded from business equality.

### P2 — unmatched facts remain explicit

**PASS.** Unmatched invoice lines are preserved explicitly, contribute only to `unmatched_actual_amount` and project actual spend, and never create or populate a placeholder Estimate Item.

### P3 — incomparable units or monetary basis block calculation

**PASS.** Different units require exact accepted conversion evidence. Currency or monetary/tax-basis mismatch requires exact accepted conversion/basis evidence. Otherwise `PlanActualPreconditionError` is mandatory; no implicit conversion is legal.

### P4 — invalid PresuPro observation never creates partial snapshot

**PASS.** Existing A40/A43 semantics remain unchanged: identical canonical content is idempotent, changed content creates another immutable snapshot, rejected observations do not create partial snapshots, and no lineage is inferred.

## Overspend and remaining edge case

For `planned_quantity = 10` and `actual_quantity = 13`:

```text
quantity_variance = 3
remaining_quantity = -3
```

The negative remaining value is preserved rather than clamped.

For `planned_amount = 100` and `actual_amount = 125`:

```text
amount_variance = 25
```

Positive amount variance therefore means overspend.

## Placeholder resistance

**PASS.** A successful result must expose the accepted mandatory calculation fields. Empty, provenance-only, warning-only, TODO-shaped, fabricated-zero, or guessed-conversion results are not conforming successful implementations.

## Adversarial ambiguity rerun

The previous material alternatives no longer both satisfy the specification:

- reversing the variance sign violates the accepted formulas;
- clamping remaining quantity violates the accepted remaining convention;
- using reconstructed invoice values or re-running PresuPro arithmetic violates source-field rules;
- omitting unmatched spend from project actual violates project aggregation;
- attaching unmatched lines to similar Estimate Items violates confirmed-match authority;
- silently converting units/currency/tax basis violates explicit-assumption rules;
- returning a provenance-only analysis violates the mandatory result shape.

Remaining freedom concerns internal implementation only: iteration order, repository layout, caching strategy, helper decomposition, and equivalent arithmetic execution that yields the same accepted semantic values.

Adversarial result: **PASS_INTERNAL_VARIATION**.

## Finding record

```text
flow: flow:calculate_plan_actual
status: semantic_closed
material_alternative_found_after_repair: no
placeholder_implementation_found_after_repair: no
repair_owner: State 2 business semantics, propagated through State 1/3/5/7
contract_signature_changed: no
runtime_oracle_allowed: yes
```

## Flow 4 gate

`semantic_closed`: **yes**

The runtime acceptance oracle may now be materialized from these accepted semantics.
