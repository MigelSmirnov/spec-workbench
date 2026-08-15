# State 3 repair — plan/actual runtime boundary

`plan_actual` exposes one cohesive `PlanActualService` constructed with the exact
`PlanActualRepository`, `DurableArchiveService`, and `RegistryContextService`.
The concrete repository is `PostgresPlanActualRepository`.

The service owns immutable snapshot acceptance, non-authoritative proposals,
confirmed/rejected/invalidation decisions, unmatched reads, and deterministic
analysis. It never constructs adapters, reads environment variables, mutates
source systems, or treats a proposal as confirmation.

Bootstrap reuses the Cabinet database and already constructed archive/Registry
services to construct and inject one service before application exposure.
