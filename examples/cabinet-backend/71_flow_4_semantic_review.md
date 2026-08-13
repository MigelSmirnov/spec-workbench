# Cabinet Backend — Stage 7.1 Flow 4 semantic review

Flow: `flow:calculate_plan_actual`

Status: **AMBIGUITY — upstream business/rule repair required**

This review applies `skills/spec-authoring/STAGE_7_1_SEMANTIC_HANDOFF.md` to Flow 4. The finding is recorded before any attempted repair.

## Reconstructed accepted behavior

The accepted slice currently establishes:

```text
exact accepted invoice revisions
+ exact Registry/WorkObject context
+ exact immutable EstimateSnapshot
+ confirmed match decisions only
+ explicit accepted assumptions
        ↓
calculate_plan_actual
        ↓
validate evidence identity, assignment, matches, and comparability
        ├─ failed precondition -> PlanActualPreconditionError
        └─ valid -> reproducible PlanActualAnalysis
```

It also establishes that:

- source Invoice Card, Registry, and PresuPro records are immutable inputs;
- similarity cannot become a confirmed estimate match;
- unmatched invoice lines remain explicit analytical facts;
- missing/incompatible/unresolved pinned evidence must not be guessed;
- identical PresuPro content is snapshot-idempotent;
- a changed PresuPro content state creates another immutable EstimateSnapshot.

## Adversarial ambiguity question

> Construct the strongest materially different alternative observable semantics that still satisfies the complete specification slice.

### Interpretation A — quantity-first matched-item analysis

For each confirmed invoice-line/estimate-item match, calculate actual purchased quantity from matched invoice lines, compare it to the Estimate Item planned quantity, derive remaining quantity and a quantity variance, and separately aggregate monetary actuals. Unmatched lines remain explicit and do not affect matched-item planned quantity.

### Interpretation B — monetary-first estimate-total analysis

Aggregate accepted matched invoice monetary totals against Estimate Snapshot monetary totals, expose amount variance as the principal plan/actual result, and leave quantity/remaining values absent or only warning-level when the implementation does not choose to calculate them.

Both interpretations can preserve pinned evidence, confirmed matches, unmatched facts, source immutability, and reproducibility. They nevertheless produce materially different observable analysis for the same accepted inputs.

Further materially different choices remain open in the current slice:

- whether `variance` is `actual - planned` or `planned - actual`;
- whether planned monetary value uses estimate subtotal, post-discount value, tax-inclusive total, margin/waste-adjusted value, or another accepted PresuPro amount;
- whether actual monetary value uses Invoice Card line subtotal, tax-inclusive amount, allocated document total, or another amount;
- how many invoice lines matched to one estimate item are aggregated;
- which unit conversions, if any, are accepted and how an explicit conversion assumption is represented;
- what mandatory fields make `PlanActualAnalysis` non-empty and observable;
- whether unmatched facts contribute only coverage/warnings or also an explicit unmatched actual amount;
- what exact semantic equality is required for repeated calculations over identical pinned inputs.

## Material difference

The same pinned invoice revisions, project context, EstimateSnapshot and confirmed match set can yield different planned values, actual values, variance signs, remaining quantities and coverage totals while still satisfying the current State 4/5/7 prose.

This is not implementation freedom. These values are user-visible business analysis.

## Placeholder resistance

Status: **PLACEHOLDER_RISK**.

`PlanActualAnalysis` is currently described as a calculated view that *may contain* planned amount, actual amount, average actual price, remaining quantity, variance, unmatched coverage, warnings and forecasts. The compressed public API requires a reproducible result and explicit unmatched facts, but it does not define a minimum mandatory calculated result shape.

Therefore a semantically hollow implementation can plausibly return a provenance-only or warning-only `PlanActualAnalysis` while avoiding source mutation and still appear consistent with the existing contract prose.

## Scenario review

### P1 — equal pinned evidence produces reproducible analysis

**Not fully derivable.** Input pinning is explicit, but the semantic value set whose equality must be reproducible is not closed.

### P2 — unmatched facts remain explicit

**PASS for preservation**, but the exact analytical contribution/coverage semantics of unmatched facts remain unspecified.

### P3 — incomparable units block calculation

**PASS for refusal** because `PlanActualPreconditionError` is required when accepted comparability preconditions fail. However, the accepted set of comparable units/conversions is not defined strongly enough to determine all positive branches.

### P4 — invalid PresuPro observation never creates partial snapshot

**PASS.** Snapshot rejection/idempotency semantics are already sufficiently constrained by A40/A43 and State 5/7.

## Finding record

```text
flow: flow:calculate_plan_actual
status: AMBIGUITY
material_alternative_found: yes
placeholder_implementation_found: yes
scenario_gaps:
  - P1 lacks a closed mandatory semantic result set and calculation definitions.
  - P2 preserves unmatched facts but does not close their analytical contribution.
  - P3 closes refusal for incomparable evidence but not the positive comparability/conversion policy.
findings:
  - owner: upstream_business
    scope: State 2 plan/actual calculation semantics and State 1 PlanActualAnalysis shape
    interpretation_A: quantity-first matched-item calculation
    interpretation_B: monetary-first aggregate calculation
    required_resolution: accept exact calculation vocabulary, formulas/sign conventions, aggregation scope, unmatched contribution, unit-conversion policy, and minimum result fields before propagating to model/API/notes
```

## Earliest repair owner

The earliest repair owner is **State 2 rules/business semantics**. State 1 must then be refined so `PlanActualAnalysis` has a mandatory non-placeholder shape, followed by propagation through State 3–7.

Do not repair this only in State 7 Notes and do not invent formulas from generic accounting conventions.

## Flow 4 gate

`semantic_closed`: **no**

A runtime acceptance oracle must not be materialized yet because doing so would encode one unaccepted calculation interpretation as product truth.
