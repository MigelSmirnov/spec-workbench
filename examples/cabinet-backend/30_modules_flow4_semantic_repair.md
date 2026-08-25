# State 3 repair — Flow 4 plan_actual responsibility

## Status

Bounded State 3 repair propagating the accepted State 2 calculation semantics.

## `module:plan_actual` additional owned responsibility

`module:plan_actual` owns deterministic derivation of the accepted PlanActualAnalysis from pinned immutable evidence.

It must:

1. resolve the exact EstimateSnapshot, invoice revisions, confirmed match decisions and accepted assumption identities supplied by the request;
2. reject missing, stale, unconfirmed, incompatible or incomparable evidence rather than substituting current mutable source data;
3. calculate per-Estimate-Item planned/actual quantities and amounts using the accepted State 2 formulas;
4. aggregate several confirmed invoice lines matched to one Estimate Item by summation;
5. keep unmatched invoice lines explicit and aggregate their actual amount only into the unmatched/project buckets;
6. enforce unit, currency and monetary-basis comparability before a successful calculation;
7. never perform implicit unit, currency or tax-basis conversion;
8. produce the mandatory non-placeholder PlanActualAnalysis result shape;
9. preserve semantic reproducibility for identical pinned evidence and assumptions;
10. avoid synthesizing forecast output when no accepted forecast assumption is pinned.

## Must not own

This repair does not give `module:plan_actual` authority to:

- modify PresuPro estimates or their snapshots;
- rewrite Invoice Card lines or totals;
- invent semantic matches;
- infer project completion from Registry status;
- invent unit/currency/tax conversion rules;
- infer PresuPro lineage.

The module still owns only confirmed match validation, accepted calculation policy, and derived analytical evidence.
