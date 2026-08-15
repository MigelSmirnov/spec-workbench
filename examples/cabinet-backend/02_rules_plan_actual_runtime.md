# State 2 repair — plan/actual runtime lowering

## Accepted decision A73 — PostgreSQL plan/actual state boundary

The first implementation uses the shared Cabinet PostgreSQL deployment.

- `EstimateSnapshot` is immutable issued evidence keyed by stable PresuPro
  identity and canonical content hash; identical content is idempotent.
- Match proposals are immutable, non-authoritative evidence and never contribute
  to calculation.
- `InvoiceLineEstimateMatch` is the durable decision record. Only active
  `confirmed` decisions may contribute to analysis.
- One invoice line may have at most one active confirmed match. PostgreSQL
  uniqueness/locking enforces the transition across processes.
- Rejected or invalidated decisions remain auditable and are never overwritten.
- All request identities are resolved from PostgreSQL and then checked through
  the exact archive and Registry services; callers cannot supply trusted source
  objects by value.
- Unmatched lines/items are computed from exact pinned snapshot, invoice, and
  active decision state in stable identifier order.
- Bootstrap constructs one repository and `PlanActualService` and fails closed
  on database/configuration failure; no memory or service-locator fallback exists.

The repository provides mechanisms only. `plan_actual` retains proposal,
decision, comparability, and calculation policy.
