# State 2 gap — plan/actual calculation semantics

## Status

**UNRESOLVED — blocks Stage 7.1 Flow 4 semantic closure.**

This file records a gap discovered by Stage 7.1. It is not an accepted decision and does not change product behavior.

The existing product/rules already accept immutable EstimateSnapshots, confirmed-match authority, explicit unmatched invoice lines, source immutability, pinned evidence, and refusal when comparison preconditions fail. They do **not** yet define enough calculation semantics to make two implementations produce the same observable business analysis.

## Decisions still required

Before `flow:calculate_plan_actual` can be semantic-closed, State 2 must accept an exact answer for each of the following:

1. **Analysis grain** — whether the canonical result is organized by Estimate Item, invoice line, project total, zone, or a declared combination.
2. **Planned quantity/value source** — which exact EstimateSnapshot fields are canonical inputs to planned quantity and planned monetary value.
3. **Actual quantity/value source** — which exact accepted Invoice Card line fields are canonical inputs to actual quantity and actual monetary value.
4. **Aggregation** — how several invoice lines confirmed against one estimate item are combined.
5. **Variance convention** — exact sign and meaning of quantity and monetary variance.
6. **Remaining convention** — exact formula and behavior when actual exceeds plan.
7. **Unit comparability** — which units compare directly and whether any conversion is accepted.
8. **Conversion assumptions** — if conversions are accepted, their typed evidence, ownership, precision and pinning semantics.
9. **Unmatched contribution** — which coverage/count/value metrics include unmatched invoice lines while keeping them explicitly unmatched.
10. **Minimum result shape** — mandatory fields that every successful `PlanActualAnalysis` must contain so an empty/provenance-only result cannot satisfy the specification.
11. **Reproducibility equality** — which semantic result fields must be equal for repeated calculations over identical pinned evidence and assumptions.
12. **Forecast boundary** — whether forecast outputs are in the baseline calculation or optional only when separately accepted forecast assumptions are supplied.

## Already accepted constraints that the resolution must preserve

Any future accepted decision must preserve:

- only confirmed `InvoiceLineEstimateMatch` decisions may contribute as matches;
- one invoice line has at most one active confirmed estimate-item match in the baseline;
- one estimate item may have many matched invoice lines;
- splitting one invoice line across several estimate items remains unsupported;
- unmatched lines remain explicit facts and must not create placeholder estimate items;
- EstimateSnapshots and accepted Invoice Card revisions remain immutable;
- existing matches stay pinned to their exact EstimateSnapshot;
- a newer snapshot does not inherit older matches automatically;
- missing, stale, incompatible, unresolved or incomparable pinned evidence must fail rather than be guessed;
- PresuPro lineage must not be inferred from project identity, content similarity or timestamps.

## Non-decisions

The following must **not** be silently chosen merely because they are common conventions:

```text
variance = actual - planned
variance = planned - actual
planned amount = estimate subtotal
planned amount = estimate total including tax
actual amount = invoice subtotal
actual amount = invoice total including tax
remaining quantity = max(planned - actual, 0)
remaining quantity = planned - actual
```

Any of these may be reasonable, but selecting one is product semantics and therefore requires an explicit accepted State 2 decision.

## Propagation after acceptance

Once the calculation decision is accepted:

```text
State 2 calculation rules
  -> State 1 PlanActualAnalysis / supporting value models
  -> State 3 plan_actual responsibility details
  -> State 4 Flow 4 graph
  -> State 5 calculate_plan_actual semantics
  -> State 6 request/result closure and properties
  -> State 7 notes
  -> Stage 7.1 re-review
  -> tests/semantic runtime oracle
```

Do not create the runtime oracle before this chain is closed; otherwise the test itself would invent the missing business decision.
