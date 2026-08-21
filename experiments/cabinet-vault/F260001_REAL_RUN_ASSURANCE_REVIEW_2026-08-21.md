# F260001 real-run assurance review — 2026-08-21

## Conclusion

The real F260001 execution is a **functional PASS**, but it is **not a complete real-run proof of all host guarantees**.

A successful operation and a proven security/authority property are recorded separately below. CI/contract evidence may support a property, but it is not relabelled as evidence observed in the private real-data run.

## Evidence classes

- **REAL_RUN** — observed in the private F260001 execution/report.
- **PINNED_CODE** — follows from the exact implementation commit used by the run.
- **CI_PROBE** — executed negative/positive bridge proof using real PostgreSQL/vault providers and synthetic input.
- **SEPARATE_GRAPH_TEST** — evidence from the older graph-host path; not exercised by F260001.

## Property review

| Property | Status | Evidence | Finding |
| --- | --- | --- | --- |
| Exact Web Card accepted and unchanged | PASS | REAL_RUN | Receipt/current hash match the pinned Card hash; Card unchanged=true. |
| Real PDF attached under `source-f260001` | PASS | REAL_RUN | Attachment=`attached`, parser media=`application/pdf`, local SHA matches supplied bytes. |
| Durable acceptance/attachment audit exists | PASS, existence only | REAL_RUN | The runner checked durable audit event type + invoice subject and reported both booleans true. |
| Detailed real-run authorization decision attestation | PARTIAL | PINNED_CODE + REAL_RUN existence | Durable executor audits contain principal/capability/interaction/effects by implementation, but the real safe report did not retain event IDs/digests or those fields and did not inspect the real run's `AuthorityKernel.audit_evidence`. |
| Grant configuration is exact, non-empty and non-wildcard | PASS | PINNED_CODE | Bridge constructs two explicit grants, each scoped exactly to `invoice:invoice-f260001`, with exact capability/effect/disclosure sets. |
| Wrong invoice scope is actually rejected | PASS | CI_PROBE | BRIDGE-004/005 execute negative cases and prove exact-scope denial. The successful real run itself contains no negative scope attempt. |
| Credential classes cannot cross boundaries | PASS | CI_PROBE | BRIDGE-003 proves `local_agent` cannot invoke synchronization and vice versa. The successful real run contains only valid credentials. |
| Local-box durable state access occurs only after authenticate/authorize | PASS for effectful request path | PINNED_CODE | `AuthorityKernel.invoke()` performs authenticate then authorize then operation; invoice record loading is inside the authorized attach operation. |
| No source-byte read/parser access before authorization | **FAIL** | PINNED_CODE | The runner reads PDF bytes before bridge invocation, and `CabinetWebSourceAttachAdapter` parser-identifies bytes before `AuthorityKernel.invoke()`. This property is not merely unproven; the current path does not satisfy it. |
| Startup recovery completes before readiness | PASS | CI_PROBE + PINNED_CODE | BRIDGE-010 proves recovery-before-ready. Startup recovery may read local durable state before a request; this is host lifecycle work, not caller authorization. |
| Declared `local_cli_stdio` transport was exercised by the real canary | **NO** | REAL_RUN code path | The real runner imports `TrustedLocalCapabilityBridge` and calls methods in-process instead of spawning the CLI/stdio entrypoint. |
| Agent is confined to public bridge surface in the real run | **UNVERIFIED / not demonstrated** | REAL_RUN code path | The runner accesses private bridge fields (`_records`, `_attach_adapter`) for verification. It performs no direct writes, but process/transport isolation is not proven. |
| Credentials/grants are independently host-owned relative to the canary runner | **PARTIAL** | PINNED_CODE | Grants are fixed inside the bridge and cannot come from request payloads, but the real runner constructs bridge environment and can generate credential IDs/materials when absent. A separate host process was not the credential owner in this run. |
| Generic arbitrary capability/module/function selection is absent | PASS | CI_PROBE | BRIDGE-009 proves the bridge surface is closed. |
| `InvoiceRefSet` remains opaque | NOT APPLICABLE TO F260001 RUN | SEPARATE_GRAPH_TEST | F260001 does not use `CabinetGraphHost` or `InvoiceRefSet`. Separate tests prove graph preflight without DB access and reject opaque `InvoiceRefSet` as public output; the real invoice canary proves nothing about it. |

## Audit evidence that actually remained

The private safe report retained:

```text
acceptance audit present: true
attachment audit present: true
```

The runner obtains these booleans by reading durable audit rows and matching event type plus `invoice-f260001` subject. It does **not** persist in the public evidence the exact real-run audit event IDs/digests, principal ID/class, capability, interaction ID, declared effects, result timestamp, or a durable authorization-decision event.

Therefore `audit exists` is proven, while `the public evidence independently attests every authorization property of this exact run` is not.

## CI assurance evidence

Bridge CI run `32529515458` at implementation commit `bc872b605c3e4b3774749cdf1711eeeb35399eaf` executed BRIDGE-001..011 using real PostgreSQL/vault providers. In particular it proves negative credential-class and exact-scope denial, closed surface, recovery-before-ready, and durable effect audit presence.

This is strong evidence about the pinned implementation, but it remains a different evidence class from the private real-data run.

## Required assurance closure

Do not call all guarantees proven by the F260001 real run until an assurance run does all of the following:

1. runs the agent/canary and bridge as separate processes and invokes only the actual local stdio/IPC surface;
2. keeps host credentials/grants outside the agent process and request environment;
3. if the intended invariant is authorization-before-source-access, moves PDF byte acquisition/parser identification behind authorization (or authorizes an opaque source handle before host reading);
4. performs real negative attempts for wrong credential class, wrong invoice scope and caller-supplied authority fields and proves no protected local-box access/effect;
5. emits a bounded real-run audit attestation containing non-secret event identifiers/digests and the exact principal/capability/scope/effects/result/interaction fields needed to verify the decision;
6. treats `InvoiceRefSet` opacity as a separate graph-host assurance property unless the production path actually uses that type.

## Correct classification

```text
real F260001 functional execution: PASS
pinned bridge assurance CI: PASS
all guarantees proven by this exact real-data run: NO
real-run assurance closure: PARTIAL
```
