# State 2 repair — Flow 6 ownership: VPS working-set release belongs to Cabinet Web

## Accepted decision A76 — Flow 6 crosses the Cabinet Web boundary (2026-08-23)

A75 (durable release authorization boundary) is withdrawn. It placed the VPS
working-set composition and the release allow/block policy inside the local
`cabinet_backend`, which is the wrong owner.

### Normative rules

1. Cabinet Web owns the VPS working-set composition and the release
   allow/block policy; `cabinet_backend` never defines the working set,
   decides a release, or deletes data on the VPS.
2. `cabinet_backend` stores and exposes only its own durable-acceptance
   evidence through `durable_archive.verify_durable_acceptance` and
   `durable_archive.get_transfer_receipt`.
3. The two sides link by manifest, issuance, and receipt identity plus the
   exact Card and source hashes; the reciprocal wire fields are frozen jointly
   before Cabinet Web State 6.
4. The removals listed under the consequence are part of this decision.

### Formal invariants

```text
working_set_composition_owner = cabinet_web
local_release_policy = removed
durable_acceptance_evidence_owner = cabinet_backend
```

### Required tests

1. No local module persists a working-set membership model.
   [witness: verification:semantic_flow6_synchronization]
2. verify_durable_acceptance and get_transfer_receipt answer the reciprocal
   verification for exact manifest, Card, and source identities.
3. No local operation can produce a VPS release decision.

### Ownership

- The canonical owner of the VPS working-set composition and of release policy
  is Cabinet Web (`examples/cabinet-web-backend`): M27
  `InvoiceWorkingSetMembership` is an immutable observation computed from the
  available Card revisions and source custody, without a lifecycle of its own;
  a snapshot is pinned together with issuance/release evidence when needed
  (`01_models_sync.md`, A10 in `02_rules_sync_operations.md`,
  `flow:release_verified_vps_working_set` in `40_flows.md`).
- `cabinet_backend` stores only its own evidence of exact local acceptance of a
  manifest / Card revision / source hash and exposes it for verification:
  `durable_archive.verify_durable_acceptance` and
  `durable_archive.get_transfer_receipt`. It does not define the working set,
  does not decide a VPS release, and does not execute deletion on the VPS.
- The two sides are linked by manifest / issuance / receipt identity and by the
  exact Card and source hashes; the exact wire fields of the reciprocal
  verification operation are frozen jointly before State 6 of Cabinet Web
  (`STATE2_EVIDENCE_CHECKPOINT_2026-08-23.md`). No endpoint is invented here.

### Consequence

Removed from `cabinet_backend`: `module:retention_release`,
`module:retention_release_persistence`, models M52 `VpsReleaseEvaluation`,
M53 `VpsReleaseDecision`, M76 `VpsWorkingSetMembership`, port
`RetentionReleaseRepository`, `synchronization.get_working_set_membership`,
rules `retention_release.*`, routes `/vps-release/*`, and
`flow:release_vps_working_copy` together with its semantic tests (they move to
Cabinet Web with the flow). The remaining durable-acceptance surface is unchanged.

### Stop condition

An OTK that demands a locally persisted membership model is a sign of a
wrongly assigned Flow 6 owner, not of a missing product decision.
