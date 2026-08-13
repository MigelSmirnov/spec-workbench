# State 1 repair — PlanActualAnalysis semantic shape

## Status

Bounded State 1 repair required by the accepted State 2 plan/actual calculation decision. It refines the existing `PlanActualAnalysis` meaning without changing source-system ownership or introducing mutable analytical state.

## `PlanActualItemResult`

Immutable value for one analysed `EstimateItemSnapshot`.

Required fields:

- `estimate_item_id: str` — exact item identity within the pinned EstimateSnapshot;
- `unit: str`;
- `planned_quantity: Decimal`;
- `actual_quantity: Decimal`;
- `quantity_variance: Decimal`;
- `remaining_quantity: Decimal`;
- `planned_amount: Decimal`;
- `actual_amount: Decimal`;
- `amount_variance: Decimal`;
- `matched_invoice_line_ids: tuple[str, ...]`.

The values are calculated only after accepted quantity and monetary comparability preconditions are satisfied. They are derived values and do not mutate either source system.

## Refined `PlanActualAnalysis`

`PlanActualAnalysis` is an immutable calculated value with the following mandatory baseline fields:

- `project_id: str`;
- `estimate_snapshot_id: str`;
- `invoice_revisions: tuple[InvoiceCardRevisionReference, ...]`;
- `match_ids: tuple[str, ...]`;
- `assumption_ids: tuple[str, ...]`;
- `items: tuple[PlanActualItemResult, ...]`;
- `unmatched_invoice_line_ids: tuple[str, ...]`;
- `project_planned_amount: Decimal`;
- `matched_actual_amount: Decimal`;
- `unmatched_actual_amount: Decimal`;
- `project_actual_amount: Decimal`;
- `project_amount_variance: Decimal`;
- `warning_codes: tuple[str, ...]`.

Optional forecast fields may exist only when separately accepted forecast assumptions are pinned by `assumption_ids`; the baseline analysis does not require or synthesize forecast values.

## Semantic invariants

For every item result:

```text
quantity_variance = actual_quantity - planned_quantity
remaining_quantity = planned_quantity - actual_quantity
amount_variance = actual_amount - planned_amount
```

For project totals:

```text
project_actual_amount = matched_actual_amount + unmatched_actual_amount
project_amount_variance = project_actual_amount - project_planned_amount
```

`items` is not a placeholder collection. A successful analysis represents every analysed Estimate Item from the pinned snapshot that belongs to the requested analysis scope.

`unmatched_invoice_line_ids` contains accepted analysed invoice lines that have no confirmed active match. Those lines are not attached to synthetic Estimate Items.

## Identity and reproducibility

The analysis remains a value object. Equal pinned evidence and accepted assumptions must produce equal semantic calculation fields. Execution timestamps, cache identifiers, or storage metadata do not create a different business analysis.

## Source ownership

- PresuPro remains authoritative for Estimate Item source facts and accepted snapshot content.
- Invoice Card remains authoritative for accepted invoice-line facts.
- Cabinet Backend owns confirmed match decisions and the derived analysis result.
- Calculation never rewrites any source record.
