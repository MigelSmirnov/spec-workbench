# Stage 8.1 — runtime boundary review

Date: 2026-08-25

Status: **PASS — INVOICE CONFIRMATION CLOSED**

## Result

The reopened `invoice_workspace` ambiguity is resolved. Its State 2–6 inputs
and manually authored State 7 notes now specify exact authorization,
dependency calls, transaction boundaries, source custody, result-field
assignments, duplicate ordering, and error outcomes without invented model
fields. Invoice confirmation commits its canonical Card revision, transfer
manifest, and working-set record through the same caller-owned unit of work.

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

### Invoice confirmation semantic re-review

**Resolved.** The six Invoice mutations now carry actor provenance and have
explicit security, orchestration, transaction, rollback, and return-shape
requirements. Duplicate matching uses real `CardRevisionReference` fields and
declares the source path for every candidate value. Card owns canonical
revision preparation and exposes a transaction-aware commit helper, allowing
Invoice confirmation to persist the Card revision, custody evidence, transfer
manifest, and working-set record atomically without duplicating Card policy.
The rebuilt `card_workspace` and `invoice_workspace` slices report zero
findings.

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

### Capability policy construction re-review

**Resolved.** Factory generation exposed an impermissible internal variation:
`CapabilityPolicy.__init__` invented an initialization timestamp after
`datetime` entered its type context through `CabinetPrincipal`. State 3 now
forbids wall-clock access and clock-derived state for this module, State 6
names catalogue-only construction as the constructor purpose, and State 7
contains an explicit forbidden-action constraint. The assembled contract is
also marked deterministic. The rebuilt `capability_policy` slice has two
notes, zero blocks, and no remaining semantic ambiguity: representation of the
immutable catalogue may vary, but additional lifecycle state may not.

### Access-control temporal semantics re-review

**Resolved.** Factory generation exposed a previously implicit temporal
boundary: access control legitimately observes time for credential lifecycle
timestamps and abuse throttling, but the specification did not distinguish
wall-clock values from elapsed-time measurements. State 3 now assigns
timezone-aware UTC lifecycle observations and monotonic throttle intervals to
the module, while State 7 forbids naive datetimes and wall-clock-derived
elapsed intervals. The rebuilt `access_control` slice retains ten contracts
and thirteen notes with zero blocks; implementations may vary internally but
cannot mix naive timestamps, aware persistence values, and throttle timing.

### Access-control UoW surface re-review

**Resolved.** The next Factory handoff showed that behavioral requirements
named durable effects but did not project the records and exact port calls
needed to implement them, so the generator either invented repository methods
or returned security-denial stubs. State 3 now names the operation-scoped UoW
and its four access-control records. State 6 adds the bounded
`list_principals_by_kind` interface/concrete pair and deterministic PostgreSQL
query. State 7 fixes the self-identifying bearer shape and maps authentication,
authorization, enrollment, grant provisioning, resolution, rotation, and
revocation to exact UoW calls and commit-or-rollback behavior. Rebuilt slices
for `models`, `access_control`, and `cabinet_persistence` report zero blocks;
the behavioral implementation may vary only behind this closed port.
The plugin-owner resolver delegates to the transaction-owning authentication
operation and performs only an in-memory owner-kind check after it returns, so
it cannot create a re-entrant or nested UoW.

### Runtime timestamp policy re-review

**Resolved globally.** Repeated Factory generation exposed that timezone
awareness was implicit across the persistence-backed service boundary. A17 now
requires every persisted, emitted, or compared wall-clock value to be
timezone-aware UTC, forbids naive datetimes, and reserves monotonic clocks for
elapsed intervals. Each behavioral service constructor note projects that
shared rule into its module generation slice, preventing local clock-style
invention without introducing a shared transaction or clock-derived state.

### Invoice workspace implementation-completeness re-review

**Resolved.** Factory received the complete invoice rules, UoW surface, Card
workspace seams, and runtime model fields, but the generator substituted
unconditional rejection and empty-return bodies for ten owned operations. The
invoice workspace boundary now explicitly forbids fail-closed placeholders and
requires every owned callable to execute its complete specified algorithm.
This closes implementation completeness without weakening any security rule or
changing the public contract surface.

## Stage 8.1 semantic re-review

All **18 assembled modules** were rebuilt from the final specification. Every structural module review reports **0 blocks and 0 review findings**. Deterministic modules (`models`, `cabinet_persistence`, `source_byte_store`, `api`) are `PASS`; behavioral modules are `PASS_INTERNAL_VARIATION` where their observable behavior is closed but internal algorithms/construction details may vary.

The exact current slice SHA-256 values and per-module results are recorded in `81_module_review_status.json`. That ledger is the Stage 9 lineage gate and must become stale if any assembled module slice changes.

## Stage 9 handoff condition

Stage 8.1 is closed. Factory admission may proceed only against the clean committed source and must independently re-check assembly, current slice hashes, persistence closure, closure-completeness fuses, target identity, Factory compatibility, and the remaining Stage 9 checks.

## Invoice module split (2026-08-26)

`invoice_workspace` was accepted as one module because every operation was
"about Invoice". Its accepted implementation had no private helper, no
dependency shared by all functions, and 11 of 12 owned functions public; the
generator collapsed it to stubs on the largest generation packet of the case.
The State 3 cohesion test now splits it along its mechanisms:

- `invoice_catalogue` — the revision-exact read model (`load_invoice_revisions`,
  `parse_invoice_revision`) behind `search_invoices`, `get_invoice`,
  `find_invoice_duplicates`; owns `ValidationRejectedError` as the lowest
  Invoice module in dependency order.
- `invoice_validation` — declared-order rule evaluation
  (`evaluate_validation_checks`) behind `prepare_invoice_draft` and
  `validate_invoice`; duplicate reuse goes through the retained catalogue.
- `invoice_lifecycle` — the lifecycle state machine
  (`require_mutation_authorization`, `load_expected_draft`,
  `commit_invoice_successor`, `derive_transfer_records`) behind the six
  mutations; depends on `card_workspace`, the catalogue and the validator.

Every public note keeps its accepted behaviour and now names the internal
mechanism it goes through, so the depth is declared rather than assumed. The
three slices report zero blocks; `api`, `chatgpt_interaction` and `bootstrap`
consume the three modules directly, without a façade.


## Re-slice 2026-08-28: measured invoice arithmetic

`rules.invoice_workspace.validation_checks` now mirrors the live-data
contract (`LIVE_INVOICE_DATA_EVIDENCE_20260828.md`): `line_net` gains
explicit `round_half_up`, while `line_tax`, `total_net` and `total_tax`
leave the blocking set — no formula over the 109 observed lines supports
them, and the live validator does not enforce them. Slice hashes for
`models`, `invoice_validation` and `invoice_lifecycle` are recomputed;
review statuses are unchanged because no note, contract, or model shape
moved — only the declared rule data the notes already reference
generically.
