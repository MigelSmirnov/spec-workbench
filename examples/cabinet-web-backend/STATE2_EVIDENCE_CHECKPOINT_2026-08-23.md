# Cabinet Web Backend — State 2 evidence checkpoint

Date: 2026-08-23

## Evidence pins

| Evidence | SHA-256 | Classification |
| --- | --- | --- |
| `CURRENT_CABINET_BEHAVIOR_EVIDENCE_2026-08-23.md` | `2e0dc0761f9bc032b93d538eb27274179949d54dc43d20de0162311566caf883` | implemented Cabinet behavior probe |
| `VPS_RUNTIME_DISCOVERY_2026-08-22.md` | `0ca3d93285da9f85207ccb86d20213dfefc6f1206cfd27c97f561738e829f023` | observed runtime/topology probe |
| `CABINET_BACKEND_SYNC_BOUNDARY_2026-08-23.md` | `c0c1477fe3d7adfac4b08ef140b22921adb0156b87553a3e422ad4c6cd04022e` | accepted external-spec snapshot |

Cabinet_web behavior is pinned to repository commit
`d3fac8e5d2b85c12904cba24060717b84e2757c2`. Its own `make check` passed 85
tests during the controlled review.

The local Backend boundary is pinned to accepted base-spec SHA-256
`48ff46297b4b0bd134063c898a11a38df74f33c51e193fd303b1b523b3414a6e`.
No `cabinet_backend` worktree or artifact was changed.

## Legacy finding classification

| Finding | Classification | Normative owner |
| --- | --- | --- |
| Existing type-specific Card validation, revisions, duplicate results, and idempotency | derivable/current accepted behavior | A01, A02, A04 |
| Conversation is the primary write interaction but deployed MCP is read-only | placement | A02, A03, A16 |
| Chat attachment bytes do not automatically reach existing repository writes | placement | A05, A06 |
| Static Web deployment has no server API | placement | A07 and later module/deploy design |
| Existing optimistic concurrency and atomic Card writes | derivable behavior to preserve; implementation lowering remains backend-owned | A01, A04 |
| Local-initiated synchronization, Invoice-only pull, Registry publication, exact receipts | external accepted product contract | A08, A09 |
| Pending-work discovery wire contract not present in reviewed local transport | unresolved external wire detail, deliberately deferred from State 2 | State 4 flow and State 6 contract evidence; no generic endpoint authorized |
| Deployed Cabinet release differs from repository main | operational lineage obligation | Stage 9 admission/deploy evidence |

## External-contract refresh obligation

State 2 accepts synchronization semantics, identities, allowed transitions, and
failure policy. It does not claim that the current local Backend exposes the
final wire operations.

Before State 6 freezes reciprocal contracts and before Stage 9 admission:

1. refresh Factory state for `cabinet_backend` without touching its worktree;
2. pin the then-current accepted spec and terminal OTK result when available;
3. verify exact reciprocal fields, enums, capability names, and version
   negotiation;
4. create the content-addressed `70_external_contract_evidence.json` bindings;
5. treat any incompatible accepted change as a return to the earliest affected
   Cabinet Web design state.

This refresh obligation blocks contract/admission closure, not State 3 module
responsibility design. No external field name or endpoint is invented in the
interim.

## Checkpoint result

```text
legacy findings classified       PASS
runtime evidence pinned          PASS
State 2 normative owners         PASS
unresolved product policy        0
external wire refresh required   YES — before State 6/Stage 9
cabinet_backend modified         NO
```

