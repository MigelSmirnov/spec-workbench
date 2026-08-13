# State 2 decision — plan/actual calculation semantics

## Status

**ACCEPTED — closes the Stage 7.1 Flow 4 semantic gap.**

This decision defines the baseline deterministic meaning of Cabinet Backend plan-versus-actual analysis. It preserves the already accepted rules for immutable EstimateSnapshots, confirmed-match authority, explicit unmatched facts, pinned evidence, and source immutability.

## Canonical analysis grain

The baseline analysis is organized by exact `EstimateItemSnapshot` identity, with explicit project-level totals and a separate unmatched-actual bucket.

One estimate item may aggregate several confirmed invoice lines. One invoice line may contribute to at most one active confirmed estimate-item match. Splitting one invoice line across several estimate items remains unsupported.

## Planned values

For each analysed Estimate Item:

```text
planned_quantity = EstimateItemSnapshot.quantity
planned_amount = EstimateItemSnapshot.total
```

`EstimateItemSnapshot.total` is consumed as the accepted PresuPro result for that immutable snapshot. Cabinet Backend must not independently reapply PresuPro waste, margin, discount, IVA, or other estimate arithmetic in order to derive another planned value.

## Actual values

For every confirmed Invoice Line matched to the Estimate Item:

```text
actual_quantity = sum(matched InvoiceLine.quantity)
actual_amount = sum(matched InvoiceLine.total)
```

The accepted Invoice Card line total is consumed as source truth. Cabinet Backend must not replace it with a newly reconstructed `quantity * unit_price` value when calculating plan-versus-actual.

Several confirmed invoice lines matched to one Estimate Item are aggregated by summation over the exact pinned matched lines.

## Variance and remaining conventions

For comparable quantities:

```text
quantity_variance = actual_quantity - planned_quantity
remaining_quantity = planned_quantity - actual_quantity
```

For comparable monetary values:

```text
amount_variance = actual_amount - planned_amount
```

A positive monetary variance means actual spend exceeds plan. A negative monetary variance means actual spend is below plan.

`remaining_quantity` is not clamped to zero. A negative result preserves the amount by which actual quantity exceeded planned quantity.

## Quantity comparability

Quantity comparison is allowed when the analysed Estimate Item unit and every contributing matched Invoice Line unit are semantically identical under the accepted unit vocabulary.

Different units are not converted automatically.

A different-unit comparison is allowed only when the request pins an explicit, already accepted conversion assumption/evidence that deterministically converts every contributing quantity into the Estimate Item unit. Conversion evidence must be part of the pinned assumption identity set used for reproducibility.

Without such accepted conversion evidence, the operation raises `PlanActualPreconditionError` rather than guessing a conversion. No implicit `kg <-> t`, `m <-> cm`, package-to-piece, or other unit conversion is accepted by default.

## Monetary comparability

Direct monetary comparison requires the planned and actual values to share the same currency and the same accepted monetary/tax basis.

The baseline does not infer or normalize a mismatch between net and gross/tax-inclusive bases. When the pinned evidence does not establish compatible currency and monetary basis, `calculate_plan_actual` raises `PlanActualPreconditionError` unless an explicit accepted conversion/basis assumption is pinned in the request.

No currency exchange or tax-basis conversion is implicit.

## Unmatched invoice lines

An accepted invoice line without a confirmed Estimate Item match remains explicitly unmatched.

It contributes:

```text
unmatched_actual_amount = sum(unmatched InvoiceLine.total)
```

when those line amounts share the accepted project monetary basis/currency required for aggregation.

Unmatched lines do **not** increase the actual quantity or actual amount of any Estimate Item and must not cause creation of a placeholder Estimate Item.

Project actual spend is:

```text
project_actual_amount = matched_actual_amount + unmatched_actual_amount
```

where all included amounts satisfy the same monetary comparability rules.

## Minimum successful result

Every successful `PlanActualAnalysis` must contain enough information to reproduce and inspect the calculation. At minimum it exposes:

- exact analysed `project_id`;
- exact `estimate_snapshot_id`;
- exact pinned invoice revision identities;
- exact confirmed match identities consumed;
- exact accepted assumption identities consumed;
- one item result for each analysed Estimate Item containing its item identity, planned quantity, actual quantity, quantity variance, remaining quantity, planned amount, actual amount, and amount variance when those dimensions are applicable and comparable;
- explicit unmatched invoice-line identities and `unmatched_actual_amount`;
- project `planned_amount`, `matched_actual_amount`, `unmatched_actual_amount`, `project_actual_amount`, and `amount_variance`;
- explicit warnings that do not invalidate the calculation.

A provenance-only, warning-only, empty, or placeholder analysis is not a successful result.

If a required baseline quantity or monetary comparison cannot be constructed from the pinned evidence under the comparability rules above, the operation raises `PlanActualPreconditionError` rather than returning a partially invented successful analysis.

## Project monetary totals

Project totals are computed from the exact analysed EstimateSnapshot and accepted Invoice Lines:

```text
project_planned_amount = sum(EstimateItemSnapshot.total for analysed items)
matched_actual_amount = sum(InvoiceLine.total for confirmed matched lines)
unmatched_actual_amount = sum(InvoiceLine.total for explicit unmatched lines)
project_actual_amount = matched_actual_amount + unmatched_actual_amount
project_amount_variance = project_actual_amount - project_planned_amount
```

The same monetary currency/basis preconditions apply to every summed value.

## Reproducibility

For identical pinned invoice revisions, project identity/context, EstimateSnapshot, confirmed match identities, and accepted assumption identities, repeated calculation must produce equal semantic calculation fields:

- per-item planned/actual quantities and amounts;
- per-item variances and remaining quantity;
- unmatched invoice-line identity set and unmatched actual amount;
- project planned, matched actual, unmatched actual, total actual, and amount variance;
- deterministic warning codes derived solely from those pinned inputs.

Runtime timestamps, persistence IDs, cache metadata, or execution ordering are not part of semantic equality unless separately accepted as domain evidence.

## Forecast boundary

Forecast values are not required for the baseline plan-versus-actual result. They may be included only when the request pins separately accepted forecast assumptions. Absence of forecast assumptions must not cause Cabinet Backend to invent a forecast.

## Preserved invariants

- only confirmed `InvoiceLineEstimateMatch` decisions may contribute as matches;
- similarity evidence alone never contributes as a match;
- one invoice line has at most one active confirmed Estimate Item match;
- one Estimate Item may aggregate many confirmed invoice lines;
- unmatched lines remain explicit and never create placeholder estimate items;
- EstimateSnapshots and accepted Invoice Card revisions remain immutable;
- matches remain pinned to their exact EstimateSnapshot;
- newer EstimateSnapshots do not inherit matches automatically;
- missing, stale, incompatible, unresolved, or incomparable pinned evidence fails with `PlanActualPreconditionError` rather than being guessed;
- PresuPro lineage is never inferred from project identity, content similarity, timestamps, or naming.

## Required tests

1. Two identical pinned requests produce semantically equal calculation fields.
2. Planned quantity comes from the exact Estimate Item quantity and planned amount from its accepted total.
3. Two matched invoice lines for one Estimate Item are summed into that item's actual quantity and amount.
4. `amount_variance = actual_amount - planned_amount`; positive means overspend.
5. `remaining_quantity = planned_quantity - actual_quantity` and remains negative when actual exceeds plan.
6. Different units without accepted conversion evidence raise `PlanActualPreconditionError`.
7. An explicit pinned conversion assumption may enable a deterministic different-unit comparison.
8. Currency or monetary-basis mismatch without accepted conversion/basis evidence raises `PlanActualPreconditionError`.
9. Unmatched lines remain explicit, contribute to project actual spend, and do not mutate any Estimate Item actual.
10. A successful analysis cannot be empty or provenance-only.
11. Source Invoice Card, EstimateSnapshot, Registry context, and confirmed match records remain unchanged by calculation.
12. No forecast is invented when no accepted forecast assumptions are pinned.
