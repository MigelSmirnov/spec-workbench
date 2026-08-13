# State 7 repair — Flow 4 deterministic plan/actual generation notes

## `calculate_plan_actual`

calculate_plan_actual: [RULE_REFERENCE] Use the accepted plan/actual arithmetic and result semantics from State 2; do not choose an alternate variance sign, planned/actual amount basis, aggregation grain, remaining convention, or unmatched contribution.

calculate_plan_actual: [BEHAVIOR] Build one deterministic result for each analysed Estimate Item: planned quantity is the pinned Estimate Item quantity; actual quantity is the sum of confirmed matched Invoice Line quantities; quantity variance is actual minus planned; remaining quantity is planned minus actual and may be negative.

calculate_plan_actual: [BEHAVIOR] Planned item amount is the pinned Estimate Item total and actual item amount is the sum of confirmed matched Invoice Line totals; amount variance is actual minus planned. Do not re-run PresuPro arithmetic or reconstruct Invoice Card totals.

calculate_plan_actual: [BEHAVIOR] Keep unmatched invoice lines explicit. Their amounts contribute to the unmatched/project actual bucket only and must never create a placeholder Estimate Item or silently attach to a similar item.

calculate_plan_actual: [VALIDATION_ERROR] Raise PlanActualPreconditionError when units are not semantically identical and no exact accepted conversion assumption is pinned. Never invent automatic unit conversion.

calculate_plan_actual: [VALIDATION_ERROR] Raise PlanActualPreconditionError when planned and actual money do not share compatible currency and monetary/tax basis and no exact accepted conversion/basis assumption is pinned. Never invent exchange-rate or net/gross normalization.

calculate_plan_actual: [RETURN_SHAPE] A successful PlanActualAnalysis must contain the mandatory per-item and project calculation fields accepted by State 1/2. Do not return an empty, provenance-only, warning-only, zero-filled, or TODO-shaped analysis as success.

calculate_plan_actual: [DETERMINISM_OR_ORDERING] Identical pinned invoice revisions, project context, EstimateSnapshot, confirmed match IDs and accepted assumption IDs must produce equal semantic calculation fields; runtime timestamps, cache IDs and execution order must not alter business values.

calculate_plan_actual: [BEHAVIOR] Do not synthesize forecast output when the request contains no separately accepted forecast assumption identity.

## `refresh_estimate_snapshot`

No change to snapshot semantics: identical canonical content remains idempotent; changed content creates another immutable EstimateSnapshot; no PresuPro lineage is inferred.
