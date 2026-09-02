# State 2 repair — plan/actual runtime lowering

## Accepted decision A73 — PostgreSQL plan/actual state boundary

The first implementation uses the shared Cabinet PostgreSQL deployment.

### Normative rules

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

### Formal invariants

```text
count(active_confirmed_match per invoice_line) <= 1
estimate_snapshot = immutable
proposal -/> calculation_input
rejected_decision -> auditable_forever
```

### Required tests

1. Concurrent confirmations of one invoice line yield exactly one active match.
2. Identical snapshot content is idempotent.
3. Proposals never change analysis results.
4. Unmatched computation is reproducible in stable identifier order for pinned
   inputs.
5. Bootstrap fails closed without PostgreSQL.

### Consequence

Plan/actual analysis reads only pinned immutable evidence and single active
decisions, so the same inputs reproduce the same analysis across processes and
restarts.
