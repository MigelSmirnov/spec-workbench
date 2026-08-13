# Cabinet Backend — Stage 7.1 Flow 6 semantic review

Flow: `flow:release_vps_working_copy`

Status: **AMBIGUITY — repair required**

## Reconstructed accepted behavior

The accepted State 4 / handoff behavior is:

```text
manual actor intent + exact project/working-set target
        ↓
evaluate_vps_release
        ↓
resolve exact affected working set
        ↓
obtain synchronization/replica observations
+ authoritative local durable verification for every required invoice/source obligation
        ├─ any required obligation missing/unverified/inconsistent → VpsReleaseBlockedError
        └─ complete positive coverage → allowed VpsReleaseEvaluation
               ↓
request_manual_vps_release
        ↓
re-check exact target + still-applicable evidence
        ├─ stale/mismatched/newly ineligible → VpsReleaseBlockedError
        └─ record idempotent authorization decision
```

Registry status alone is never release authority, and neither domain operation physically deletes VPS working data.

## Adversarial ambiguity

### Interpretation A — complete working-set proof

`evaluate_vps_release` resolves every required release obligation in the exact working set and requires authoritative positive durable-local verification for each one. If one required invoice/source replica is absent, unverified, inconsistent, or not covered by the evidence set, evaluation is blocked.

### Interpretation B — any positive proof is sufficient

`evaluate_vps_release` receives a tuple of durable evidence and allows release whenever at least one positive `DurableAcceptanceVerification` exists, while other working-set members are missing from the evidence set. The current State 5/7 wording requires durable-local proof but does not explicitly require exhaustive proof coverage of every required member.

## Material difference

For working set `{invoice_A, invoice_B}` where `invoice_A` is durably verified and `invoice_B` still lacks one required local source replica, Interpretation A blocks release. Interpretation B authorizes deletion of the whole VPS working set and can remove the last intact copy for invoice_B. This is materially different observable retention behavior.

## Placeholder resistance

Status: **PLACEHOLDER_RISK** for `evaluate_vps_release`.

An implementation that checks `any(v.accepted for v in durable_evidence)` can appear to satisfy the compressed durable-proof requirement while failing the accepted complete-working-set safety condition.

## Scenario review before repair

- V1 missing all durable proof: PASS.
- V2 Registry status alone cannot authorize release: PASS.
- V3 allowed evaluation performs no physical deletion: PASS for effect separation, but complete proof coverage is not generation-obligatory.
- V4 stale evaluation cannot authorize release: PASS at the public-operation level.
- V5 repeated equivalent decision is idempotent: PASS.

## Finding

```text
flow: flow:release_vps_working_copy
status: AMBIGUITY
material_alternative_found: yes
placeholder_implementation_found: yes
findings:
  - owner: structure
    scope: State 3/5 retention-release proof completeness propagated to State 7
    interpretation_A: every required working-set member/replica obligation must have authoritative positive local durable evidence
    interpretation_B: one or a subset of positive proofs can authorize the entire exact working set
    required_resolution: require exhaustive evidence coverage for the resolved affected working set and block on any missing, unverified, inconsistent, or uncovered required obligation
```

## Earliest repair owner

State 4 is already explicit that every required local source replica for the target working set must be present and verified. State 1/contract support already allows multiple durable evidence records in `VpsReleaseEvaluation`. Repair State 3/5 semantics and propagate to State 7 Notes; no signature change is required.

`semantic_closed`: **no**, pending repair and rerun.
