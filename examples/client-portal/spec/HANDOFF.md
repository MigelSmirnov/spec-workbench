# Handoff — Client Portal spec-authoring pass

Session of 2026-07-19, continued through State 7.
Continue with `skills/spec-authoring/SKILL.md` methodology; read this
directory in numerical order first, plus
`skills/spec-authoring/references/platform_registry_contract.md` (mandatory:
product is Registry-linked).

## Completed

- **State 0** — `00_product.md`. All 9 baseline open questions closed
  (mapping table inside). ТЗ baseline `../01…09` stays frozen input.
- **State 1** — `10_models.md`. Full model set, accepted by the product
  owner including the email revision.
- **State 2** — `20_rules.md` + `invariant_ledger.json` (~50 invariants;
  `owner_function`/`landing` remain null until States 5–7). JSON syntax
  validated.
- **State 3** — `30_modules.md`. Semantic ownership, candidate public
  capabilities, dependency direction, generation order/paths, persistence
  boundary, credential-security and financial-policy ownership, audit
  transaction policy, and binary-storage boundary recorded.
- **State 4** — `40_flows.md`. Nine end-to-end flow groups cover staff auth
  and guarded mutation, email challenges, viewer access, snapshot import,
  budget activation, OCR expense intake/correction, binary delivery, derived
  overview, and audit success/rejection paths.
- **State 5** — `50_public_apis.md`. Stable cross-module APIs, callers,
  typed inputs/outputs, effects, invariant coverage, rejection families,
  imports draft, and preliminary adapters recorded.
- **State 6** — `60_contracts.md`. Exact public/private signatures,
  module-owned exception classes, concrete PortalStore/PortalTransaction,
  typed dependency edges, module ownership, and function ordering recorded.
- **State 7** — `70_notes_properties.md`. Assembly-ready classified notes
  cover all 318 exact contracts; pure properties and determinism decisions are
  recorded; every invariant has one exact owner and primary landing in
  `invariant_ledger.json`.
- **State 8** — `../global_spec.json` + `80_assembly.md`. Assembly is complete;
  strict Workbench semantic lint and the shared strict type resolver are clean.
  Factory resolver migration is complete and canonical validation now returns
  `PASS`, exit 0, zero findings. State 9 may start.

## Key decisions (all 2026-07-18, product owner unless marked State 3 design)

1. Product owner is a sole-trader (autónomo); few parallel projects;
   operating simplicity is a first-class constraint.
2. Full IAM, three principal types, never merged: `StaffAccount`
   (email+password, verified email, sessions, reset), `ClientViewer`
   (capability link, multi-project `ProjectViewerGrant`s, read-only, no
   password/registration), `ServicePrincipal` (producer, rotating revocable
   credentials, import-only capabilities, project scope).
3. **Email Delivery Gateway is a mandatory external boundary.** Challenges
   are purpose-bound, single-use, TTL, rate-limited, verification-form
   storage; gateway is delivery-only and never trusted for validity; admin
   recovery is an exceptional heavily-audited flow.
4. Snapshot import port is push: publication contract owned by the portal;
   PresuPro implements the producer later. Immutable append-only snapshots
   `(project, estimate_id, estimate_version)`; same content = idempotent,
   different = integrity conflict; import ≠ activation (human-only); ≤1
   active BudgetVersion per project; manual budget is first-class; section
   mapping only via stable `source_key`, name-matching forbidden.
5. Backend + JSON API only; EUR-only gross (IVA included) money,
   ROUND_HALF_UP 2dp; expense creation only via OCR intake.
6. Union encoding: current Factory does not materialize
   `kind: discriminated_union`; all current exactly-one concepts use an enum
   discriminant + conditional field + local validator and are marked
   `[closed-choice]` in `10_models.md`.
7. **State 3 design:** `portal_store` is a concrete typed persistence facade
   for the current target, never generic CRUD/raw ORM. Domain owners select
   transaction scope; Registry/email I/O occurs outside DB transactions;
   required audit commits atomically with successful mutations.
8. **State 3 design:** `binary_storage` is an opaque read boundary behind
   `file_ref`. Domain modules authorize access first; the adapter then safely
   resolves/reads the object. `file_ref` is never a client authority, raw
   path, or trusted URL.
9. **State 4 design:** application resources/commands use JSON; authorized
   document/photo bytes use one authenticated portal streaming response.
   Signed/provider URLs are outside the current architecture. A required
   deployment `binary_max_read_bytes` bounds reads.
10. **State 4 backward correction:** StaffProjectAssignment makes operator
    project scope explicit. Current administrators cover the documented
    single administrative area; adding a second area still requires an area
    model. INV-017 and assignment audit/revocation rules were added.
11. **State 4 backward correction:** OCR expense replay compares canonical
    `intake_fingerprint`; equal content returns existing records, conflicting
    content changes nothing. ExpenseIntake now carries the missing opaque
    `file_ref` needed to create ExpenseDocument.
12. **State 5 consolidation:** former `staff_auth` + `email_challenges` are
    one deep `staff_identity` module, removing the lifecycle dependency cycle
    while keeping email provider delivery in its gateway.
13. **State 5 backward correction:** OCR boundary now has typed
    ConfirmedRecognitionPublication/NormalizedRecognitionItem and explicit
    AllocationInstruction; binary reads return BinaryPayload through owning
    expense/photo use cases.
14. **State 5 rule, clarified in State 7:** R15 fixes deterministic
    project-list ordering; Registry gateway output sorts by UUID, viewer
    presentation by `display_name.casefold()` then UUID without changing the
    displayed name. Pagination remains absent for the accepted few-project
    profile.
15. **State 5 rule:** R16 closes staff identity inputs: normalized email is
    trimmed, syntax-validated and Unicode-casefolded without provider tricks;
    passwords are 12–128 code points, no control characters, and are hashed
    exactly as supplied without trimming/normalization.
16. **State 6 transaction correction:** semantic modules use concrete typed
    PortalTransaction; raw SQLAlchemy sessions and generic callbacks never
    cross boundaries. `audit_writer.append_audit` inserts into the same typed
    transaction as the business mutation.
17. **State 6 security correction:** persisted entities containing password/
    token/secret hashes or `file_ref` are never HTTP responses. Dedicated safe
    administration/mutation DTOs and exact top-level endpoint contracts own the
    allow-list projection.
18. **State 6 guard design:** actor-specific public guards delegate to one
    `_authorize_project_operation(ProjectAuthorizationRequest)` using the
    supported closed-choice encoding, giving R4 a single enforcement owner.
19. **State 6 security correction:** R17 token envelopes use record UUID only
    as a selector plus a random secret verified against the salted hash.
    Verification hashes are never deterministic database lookup keys.
20. **State 7 landing decision:** cross-table uniqueness and append-only/
    referential commit invariants use `PortalTransaction.commit` as their one
    technical owner; semantic modules still own the commands and required
    audit effects.
21. **State 7 projection decision:** every top-level endpoint function has an exact thin
    orchestration note, and safe projection helpers have allow-list notes plus
    pure equality properties. Hashes and `file_ref` cannot reach JSON DTOs.

22. **API boundary correction:** State 3 now maps `api` to `api/router`; State 5 owns an exact unversioned REST catalog; State 6/7 use top-level `*_endpoint` contracts/notes. The accidental `PortalApi` class and `api/runtime` path were removed without changing domain use cases.

## Product-owner confirmation received

Confirmed on 2026-07-19:

1. Fixed-expiry sessions, no sliding renewal.
2. Self-service password-reset requests allowed (existence-hiding).
3. Config defaults: staff session 12h, viewer session 30d, verification
   72h, email change 24h, reset 60min, 5 challenges/hour/account, argon2id.

These values are now authorized for State 8 assembly.

## Next: State 9 — official no-copy Factory compatibility route

State 9 must start from the accepted authoring commit with a clean Workbench
checkout. Before export, `git status --porcelain` must be empty; otherwise the
handoff records `source.dirty=true` and `tools/verify_workbench_handoff.py`
rejects the lineage proof. Do not use `--allow-dirty-source` for State 9
evidence.

1. From Workbench, export through the official boundary without a dirty-source
   override:

   ```bash
   python tools/export_to_factory.py \
     --case client-portal \
     --project client_portal_sandbox
   ```

2. From Factory, verify the handoff before Route B:

   ```bash
   python tools/verify_workbench_handoff.py \
     --project client_portal_sandbox \
     --workbench-root ../spec-workbench
   ```

3. Only after that verification passes, use the `opc_4` accepted-spec route in
   no-copy mode:

   ```bash
   PROJECT_NAME=client_portal_sandbox \
     bash factory_control/run_route_b_predeploy.sh --all --dry-run-deploy
   ```

   `--dry-run-deploy` still exercises models-first generation, selected drafts,
   assembler/build gates, linker, semantic predeploy selection, and deploy
   manifest planning, but it must not copy generated files into product source.

4. Inspect the generated model shapes, selected-draft reports, assembler
   manifest, static-gate reports, linker report, and dry-run deploy manifest.
   Stop and classify the first unexpected `WARN` or `BLOCK`; do not patch a
   Factory gate or generated artifact during the probe.

An exploratory 2026-07-19 direct-helper attempt used a dirty-source handoff and
is explicitly discarded: it performed no deploy, its Factory project/artifacts
were deleted, and it is not State 9 evidence.

If the official route exposes a missing product decision, repair its earliest
design state instead of inventing it inside JSON. If it exposes a toolchain
contradiction, record the blocker without changing product semantics.

## Still open (recorded, non-blocking for State 4 except where noted)

- Staff MFA.
- Admin-area boundaries (dormant, single area).
- PresuPro→Portal transport binding.
- List pagination beyond the current few-project profile.
- Expense-correction history beyond audit.
- `SnapshotImportRecord` retention.
- External-storage deletion/retention policy.
