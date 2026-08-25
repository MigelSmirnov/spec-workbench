# State 5 repair — `calculate_plan_actual` deterministic semantics

## Status

Bounded State 5 repair propagating the accepted State 2 plan/actual decision without changing the public operation name or State 6 callable signature.

## `public_op:plan_actual.calculate_plan_actual`

### Refined inputs

The operation consumes only the exact pinned identities in `PlanActualRequest`: accepted invoice revisions, exact project identity/context, one immutable EstimateSnapshot, confirmed match IDs, and accepted assumption IDs.

### Refined outputs

A successful result is a non-placeholder `PlanActualAnalysis` containing:

- one deterministic item result per analysed Estimate Item;
- explicit unmatched invoice-line identities;
- project planned amount;
- matched actual amount;
- unmatched actual amount;
- total project actual amount;
- project amount variance;
- exact evidence/match/assumption identities and deterministic warnings.

Per-item values follow the accepted formulas:

```text
planned_quantity = EstimateItemSnapshot.quantity
actual_quantity = sum(matched InvoiceLine.quantity)
quantity_variance = actual_quantity - planned_quantity
remaining_quantity = planned_quantity - actual_quantity

planned_amount = EstimateItemSnapshot.total
actual_amount = sum(matched InvoiceLine.total)
amount_variance = actual_amount - planned_amount
```

Project values follow:

```text
project_planned_amount = sum(analysed EstimateItemSnapshot.total)
matched_actual_amount = sum(confirmed-matched InvoiceLine.total)
unmatched_actual_amount = sum(explicit-unmatched InvoiceLine.total)
project_actual_amount = matched_actual_amount + unmatched_actual_amount
project_amount_variance = project_actual_amount - project_planned_amount
```

### Refined enforcement

The operation must enforce:

- confirmed matches only;
- one invoice line contributes to at most one active confirmed match;
- several invoice lines may aggregate into one Estimate Item;
- unmatched lines never populate or create an Estimate Item;
- direct quantity comparison only for semantically identical units, unless exact accepted conversion evidence is pinned;
- direct monetary comparison only for compatible currency and monetary/tax basis, unless exact accepted conversion/basis evidence is pinned;
- no implicit unit, currency, tax-basis, estimate-arithmetic or forecast assumptions;
- identical pinned semantic inputs produce equal semantic calculation fields.

### Errors

`PlanActualPreconditionError` is raised when required pinned evidence is missing, stale, unconfirmed, incompatible, unresolved or incomparable, including unit, currency or monetary-basis mismatch without exact accepted conversion evidence.

The operation must not downgrade those conditions into zero values, placeholder items, provenance-only success, or guessed conversions.

### State impact

The result is derived analytical evidence only. Invoice Card, Registry, EstimateSnapshot and confirmed match source records remain unchanged.
