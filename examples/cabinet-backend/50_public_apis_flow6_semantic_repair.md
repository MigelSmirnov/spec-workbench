# State 5 bounded repair — Flow 6 release proof completeness

This file refines `public_op:retention_release.evaluate_vps_release` and `public_op:retention_release.request_manual_vps_release` for Stage 7.1 Flow 6.

## Withdrawn — `public_op:retention_release.evaluate_vps_release`

### Refined outputs

An allowed `VpsReleaseEvaluation` identifies one exact affected working set and carries the complete authoritative durable-evidence set plus required synchronization/replica observations used to prove release eligibility.

### Refined enforcement

Before returning `allowed = true`, the operation must prove exhaustive coverage of the resolved affected working set. Every required invoice/source replica obligation that would lose its VPS working copy must have authoritative positive local durable verification. Any missing, unverified, inconsistent, stale, or uncovered required obligation blocks the evaluation with `VpsReleaseBlockedError`.

The existence of one or several positive proofs is insufficient when they do not cover the complete affected working set. Registry status never substitutes for missing coverage.

The operation performs no physical deletion.

## Withdrawn — `public_op:retention_release.request_manual_vps_release`

Before recording authorization, the operation must re-check that the supplied allowed evaluation still applies to the exact same working-set identity/membership and that its complete evidence coverage remains valid. A stale evaluation, changed target membership, missing required proof, mismatched evidence identity, or newly ineligible obligation raises `VpsReleaseBlockedError`.

Repeating an equivalent request for the same exact still-valid evaluation/target returns or preserves the existing equivalent release decision and creates no duplicate authorization obligation.
