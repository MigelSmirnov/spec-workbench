# Stage 8.1 — runtime boundary review

Date: 2026-08-25

Status: **REOPENED — INVOICE NOTES AMBIGUITY**

## Result

The earlier PASS is no longer authoritative. Manual reading of the
`invoice_workspace` generation packet showed that presence of classified
`MUST` notes had been mistaken for semantic closure. The slice is reopened
until its State 2–6 inputs and manually authored State 7 notes specify exact
ordering, dependency calls, transaction boundaries, result fields, and error
outcomes without invented model fields.

The Cabinet Web Backend runtime boundary is implementation-ready for the accepted VPS architecture. The earlier Stage 8.1 ambiguities were returned to their owning design states, lowered, assembled, and re-reviewed rather than waived.

PostgreSQL remains the authoritative Cabinet Web metadata store and the protected local VPS filesystem remains the authority for original source bytes. The local `cabinet_backend` remains a separate intermittent synchronization peer and is not required for ordinary Cabinet Web reads or mutations.

Final deterministic evidence:

- `persistence_backend/v3` is closed for **25 PostgreSQL tables**;
- `PostgresCabinetUnitOfWork` has **80 deterministic `postgres_sync_v1` methods**;
- one `CabinetUnitOfWorkFactory` opens a fresh UoW per application operation;
- the protected filesystem `source_byte_store_backend` is closed;
- the recoverable source-byte publication journal is durable in PostgreSQL;
- transfer issuance/receipt/conflict, Registry replica/current-selector, security, restore-drill, and release evidence all have explicit durable projections;
- `bootstrap.create_cabinet_web_app` is the sole composition root and owns protected configuration reads, migrations/connectivity checks, startup recovery, adapter/service construction, and the final `create_app` handoff;
- State 7 notes are propagated into the assembled specification before module review;
- complete Workbench assembly is **8/8 ready with 0 errors**.

The mature local `cabinet-backend` was used only as an E2E-tested structural precedent for shared Factory mechanisms such as `persistence_backend/v3`, `postgres_sync_v1`, verifier-only credential storage, transaction ownership, and recoverable byte publication. No local-backend product ownership or Holded behavior was transferred into the server application.

## Resolution of prior findings

### Finding 1 — durable backend lowering

**Resolved.** Every accepted server durable state family now has an explicit PostgreSQL projection or is intentionally embedded in the immutable canonical Card revision aggregate. Table names are closed under `config.persistence`; persistence adapters do not read deployment configuration or invent business policy.

### Finding 2 — typed repository and UoW surface

**Resolved.** Stateful application services depend on the external `CabinetUnitOfWorkFactory`; each operation receives a fresh transaction-scoped UoW. The deterministic repository surface covers Card revisions/current heads, effects, principals/nodes/credentials/grants/throttle/audit, source handoffs/custody/publication, working sets/manifests/issuance/receipts/conflicts, Registry publication/replica/current selection, restore drills, and VPS release evidence.

### Finding 3 — cross-resource atomicity and recovery

**Resolved.** One application operation owns one PostgreSQL transaction. Card/effect, Invoice producer, transfer, Registry, security, and release transitions can share that transaction. Source-byte custody uses the accepted staged/verified/metadata-committed/atomic-publish protocol with durable recovery journal evidence; startup recovery finalizes or fails pending publications without reporting unavailable bytes as present.

### Finding 4 — runtime composition

**Resolved.** `bootstrap` is now a first-class assembled module with the exact `create_cabinet_web_app() -> FastAPI` contract and a State 7 orchestration constraint. It is the only boundary allowed to read protected deployment configuration and construct the concrete PostgreSQL/filesystem/runtime graph.

### Factory emitter ownership re-review

**Resolved.** `PostgresCabinetUnitOfWorkFactory` is owned by `bootstrap`, which
already owns protected configuration and construction of the operation-scoped
PostgreSQL adapter. The deterministic `cabinet_persistence` emitter target owns
only `create_cabinet_schema` and `PostgresCabinetUnitOfWork`, so regeneration
cannot erase composition-root callables. Structural review reports zero
findings for both changed slices. `cabinet_persistence` remains `PASS` and
`bootstrap` remains `PASS_INTERNAL_VARIATION` because only private construction
details vary.

### Imported contract type-surface re-review

**Resolved.** Factory Spec Inspector exposed 78 missing model edges in the
direct runtime import surfaces of `invoice_workspace`, `project_workspace`,
`invoice_exchange`, `chatgpt_interaction`, `web_gateway`, and `sync_gateway`.
Every added edge points to the unique `models` owner and is required by the
signature of an already accepted imported callable; no callable dependency,
ownership boundary, or business behavior changed. Rebuilt structural reviews
for all six affected slices report zero findings. Their current hashes are
recorded in `81_module_review_status.json`.

### Deterministic model ownership re-review

**Resolved.** The 13 persistence/runtime records introduced by the closed model
closure are now projected into both `module_functions.models` and
`imports.internal.models`. This assigns their unique generation owner and
exports the complete deterministic model surface without changing any model
shape. The rebuilt `models` slice reports zero findings and remains `PASS`.

## Stage 8.1 semantic re-review

All **18 assembled modules** were rebuilt from the final specification. Every structural module review reports **0 blocks and 0 review findings**. Deterministic modules (`models`, `cabinet_persistence`, `source_byte_store`, `api`) are `PASS`; behavioral modules are `PASS_INTERNAL_VARIATION` where their observable behavior is closed but internal algorithms/construction details may vary.

The exact current slice SHA-256 values and per-module results are recorded in `81_module_review_status.json`. That ledger is the Stage 9 lineage gate and must become stale if any assembled module slice changes.

## Stage 9 handoff condition

Stage 8.1 is closed. Factory admission may proceed only against the clean committed source and must independently re-check assembly, current slice hashes, persistence closure, closure-completeness fuses, target identity, Factory compatibility, and the remaining Stage 9 checks.
