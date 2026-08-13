# State 7 bounded repair — Flow 6 release generation obligations

These notes refine generation for Stage 7.1 Flow 6.

# retention_release

evaluate_vps_release: [ORCHESTRATION] Resolve the exact affected VPS working set and require authoritative positive local durable verification for every required invoice/source replica obligation that would lose its VPS working copy; a positive subset is never sufficient for a larger set.
evaluate_vps_release: [VALIDATION_ERROR] Raise VpsReleaseBlockedError when any required working-set obligation is missing from evidence coverage, unverified, inconsistent, stale, or otherwise not proven durable locally.
evaluate_vps_release: [RULE_REFERENCE] Registry lifecycle/status never fills a missing durable-evidence obligation and never authorizes deletion; preserve the manual-release baseline.
evaluate_vps_release: [BEHAVIOR] Return an allowed evaluation only with the exact affected-set identity/membership and complete evidence identities used for the decision, and perform no physical deletion.
request_manual_vps_release: [ORCHESTRATION] Re-check that the allowed evaluation still covers the same exact working-set identity and membership with complete still-valid durable evidence before recording authorization; do not broaden or substitute the target.
request_manual_vps_release: [VALIDATION_ERROR] Raise VpsReleaseBlockedError for stale evidence, changed membership, missing coverage, target mismatch, conflicting evidence, or any newly ineligible required obligation.
request_manual_vps_release: [BEHAVIOR] Preserve idempotency for an equivalent repeated decision over the same exact still-valid evaluation and target; record policy authorization only and never perform physical VPS deletion inside this operation.
