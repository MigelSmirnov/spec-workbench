# State 2 — Cabinet dependency vulnerability and update policy

## Accepted decision A68 — deployed dependency inventory and vulnerability response

Cabinet has several deployed runtime surfaces with externally maintained dependencies. This decision establishes the minimum release-blocking and remediation policy for those surfaces without creating a separate security organization.

### Normative rules

1. Every deployed Cabinet surface has one explicit dependency owner. In the baseline, that owner is the engineer/deployment owner responsible for releasing that surface.
2. Each deployed surface must have a reproducible dependency inventory derived from its accepted lockfile, package manifest, container image manifest, or equivalent deployment artifact.
3. The applicable surfaces include at least VPS Cabinet, Local Cabinet Backend, agent/MCP runtimes that are deployed as Cabinet components, and dedicated integration/gateway runtimes.
4. The baseline vulnerability evidence sources are GitHub Advisory Database/Dependabot-compatible advisories plus authoritative ecosystem or vendor advisories when applicable.
5. A newly introduced dependency with a known `critical` vulnerability blocks release or merge.
6. A newly introduced dependency with a known `high` vulnerability blocks release or merge.
7. Newly introduced `moderate` and `low` vulnerabilities produce visible review findings but do not automatically block release unless a separate product/integration rule identifies concrete exploitability requiring a stronger response.
8. For already deployed dependencies, a known `critical` vulnerability must be fixed, removed, upgraded, or otherwise effectively mitigated within 72 hours of confirmed applicability.
9. For already deployed dependencies, a known `high` vulnerability must be fixed, removed, upgraded, or otherwise effectively mitigated within 7 days of confirmed applicability.
10. For already deployed dependencies, a known `moderate` vulnerability must be resolved within 30 days unless documented as not applicable to the deployed use.
11. `Low` vulnerabilities are handled through normal maintenance unless exploitability or exposure changes their effective risk.
12. When no safe fix is immediately available, a time-bounded exception may be accepted only if it records the dependency/advisory, affected deployment, applicability rationale, containment, rollback or upgrade plan, approver, and expiry date.
13. The product/deployment owner may approve such an exception in the baseline. A separate security committee is not required.
14. One exception may last no more than 30 days. Expiry does not silently renew the exception; continuing exposure requires a new explicit review and decision.
15. Release tooling may enforce these rules through dependency-review or equivalent supply-chain checks, but the tool does not own the policy and must not silently downgrade a blocking severity.
16. Dependency findings and accepted exceptions must be auditable without storing package-registry credentials or other reusable secrets in ordinary logs or exported business data.

### Formal invariants

```text
new_dependency_vulnerability in {critical, high}
-> release_blocked

confirmed_deployed_critical
-> remediation_or_effective_mitigation_within_72h

confirmed_deployed_high
-> remediation_or_effective_mitigation_within_7d

confirmed_deployed_moderate
-> remediation_within_30d_or_documented_not_applicable

exception_duration > 30_days
-> forbidden

exception_expired
-/> automatic_renewal
```

### Required tests

1. Dependency review rejects a proposed release that introduces a known critical vulnerability.
2. Dependency review rejects a proposed release that introduces a known high vulnerability.
3. Moderate and low findings remain visible even when they do not automatically block release.
4. Each deployable Cabinet surface can produce or identify its reproducible dependency inventory.
5. A critical deployed finding cannot remain in an unmitigated accepted state beyond 72 hours without violating policy.
6. A high deployed finding cannot remain in an unmitigated accepted state beyond 7 days without violating policy.
7. An exception missing affected deployment, containment, rollback/upgrade plan, approver, or expiry is rejected.
8. An exception with an expiry later than 30 days from approval is rejected.
9. An expired exception is not treated as active unless a new explicit exception decision is recorded.

### Consequence

OQ-011 is resolved. Cabinet has an explicit dependency inventory owner, release-blocking threshold, remediation window, and time-bounded exception process for each deployed surface.
