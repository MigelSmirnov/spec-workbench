# Cabinet Backend — Stage 7.1 Flow 6 semantic review

Flow: `flow:release_vps_working_copy`

Status: **semantic_closed**

## Reconstructed accepted behavior

The accepted behavior is:

```text
manual actor intent + exact project/working-set target
        ↓
evaluate_vps_release
        ↓
resolve exact affected working set
        ↓
obtain synchronization/replica observations
+ authoritative local durable verification for every required invoice/source obligation
        ├─ any required obligation missing/unverified/inconsistent/uncovered → VpsReleaseBlockedError
        └─ complete positive coverage → allowed VpsReleaseEvaluation
               ↓
request_manual_vps_release
        ↓
re-check exact target/membership + still-applicable complete evidence
        ├─ stale/mismatch/changed membership/new ineligibility → VpsReleaseBlockedError
        └─ record idempotent authorization decision
               ↓
          later physical adapter may execute exact authorized release
```

Registry status alone is never release authority, and neither domain operation physically deletes VPS working data.

## Finding that required repair

Before repair, compressed State 5/7 semantics allowed a materially unsafe alternative: a positive subset of durable evidence could plausibly authorize a larger working set. For `{invoice_A, invoice_B}`, proof for invoice_A alone could therefore appear sufficient even when invoice_B still lacked a required local source replica.

The repair is recorded in:

- `30_modules_flow6_semantic_repair.md`;
- `50_public_apis_flow6_semantic_repair.md`;
- `80_notes_flow6_semantic_repair.md`.

No new DTO/signature was required because `VpsReleaseEvaluation` already carries multiple durable evidence records.

## Re-run scenarios

### V1 — durable-local proof is mandatory

**PASS.** Missing, unverified, inconsistent, stale, or uncovered required durable evidence raises `VpsReleaseBlockedError`; no authorization is recorded.

### V2 — Registry status alone cannot allow release

**PASS.** Registry archived/complete-like state cannot fill an evidence gap and supplies no deletion authority.

### V3 — allowed evaluation performs no physical deletion

**PASS.** Allowed evaluation requires exhaustive coverage of the exact affected working set and remains a policy/evidence artifact only; physical release belongs to a later adapter.

### V4 — stale evaluation cannot authorize release

**PASS.** `request_manual_vps_release` must re-check exact target identity/membership and still-valid complete evidence. Changed membership or stale/mismatched evidence blocks authorization.

### V5 — repeated equivalent manual decision is idempotent

**PASS.** Repeating the same exact still-valid evaluation/target preserves or returns the existing equivalent decision and creates no duplicate release obligation.

## Adversarial ambiguity rerun

The previous alternative `any positive durable proof -> allow entire working set` now directly violates the exhaustive coverage obligation in State 3/5/7 repairs.

Remaining implementation variation is internal only: evidence lookup/order, persistence layout, and physical adapter mechanics may vary while observable allow/block semantics remain fixed.

Result: **PASS_INTERNAL_VARIATION**.

## Placeholder resistance rerun

A placeholder implementation based on `any(...)`, non-empty evidence, Registry status, or synchronization success alone cannot satisfy the repaired operation semantics. An allowed evaluation must demonstrate complete exact-set coverage.

Result: **PASS**.

## Flow 6 gate

`semantic_closed`: **yes**

The V1–V5 scenarios may now be materialized as runtime acceptance tests without inventing new product behavior.
