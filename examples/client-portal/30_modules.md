# State 3 — Client Portal module responsibilities

## Status

Migrated on 2026-11-06 from the former `spec/30_modules.md` (authoring pass of
2026-07-18/19, `SOURCE.md`) and the accepted Factory spec
`projects/client_portal_sandbox/specs/base/global_spec.json` (sha256
`459ac96c4b8febc629c81178c9d0a84ee072d1662dc52f44d74fb0993cb3c2c7`, Factory
`6011ac93b143`). Builds on `00_product.md`, `01_models.md` and the accepted
State 2 decisions A1–A32 of `02_rules.md`.

The former text named 20 modules. The accepted spec runs 39: the same 20 and
19 the Factory added between 2026-07-22 and 2026-08-17 — eleven narrow SQLite
repositories, `staff_bootstrap_store`, `staff_bootstrap`, `staff_challenges`,
`api_irregular`, `transport_guard`, `runtime_settings`, `runtime` and
`staff_bootstrap_cli`. Each added module cites the Factory commit that added
it; that commit's body is its rationale. Where the former text and the
accepted spec disagree, the accepted spec is kept (owner 2026-11-06: current
service behaviour accepted; technical decisions delegated); every such case is
listed in "Changes against the former text" below.

On 2026-11-07 the owner removed the staff email challenges (`00_product.md`
R0-23). Three modules leave with them: `staff_challenges` (added by the
Factory), the repository `email_delivery_repository` (one of the eleven) and
`email_delivery_gateway` (one of the former 20). On 2026-11-07 the
coordinator added `system_clock`, the one reader of the host clocks (A28,
SPEC_STANDARD §6.9 version 5), which the accepted spec does not have. The case
runs 37 modules: 19 of the former text, 17 added by the Factory, ten of them
repositories, and `system_clock`. On 2026-11-08 the owner had the
specification rebuilt by SPEC_STANDARD, starting with its data; the values
generated code reads moved into `data_provider`, the deterministic
provider module of SPEC_STANDARD 6.10. The case runs 38 modules.

A module owns one hidden mechanism and has one reason to change; its public
surface is smaller than what it hides. Each accepted decision has one primary
owner, the module that holds the decision's central mechanism, and consumers,
except the two decisions recorded `cross_cutting` (A22, A26, below).
A consumer owns exactly the rules and parts of a decision its own section
names; the primary owner owns every other rule of the decision. The table is
the one mapping; `30_trace.json` records the same:

| decision | primary owner | consumers |
|---|---|---|
| A1 | `authorization_guard` | `models`, `staff_identity`, `viewer_access`, `service_identity` |
| A2 | `authorization_guard` | `models`, `staff_identity`, `service_identity`, `data_provider` |
| A3 | `staff_identity` | `viewer_access`, `service_identity`, `budget_management`, `staff_access_repository`, `data_provider` |
| A4 | `authorization_guard` | `registry_gateway`, `api`, `api_irregular` |
| A5 | `authorization_guard` | `registry_gateway`, `staff_identity`, `viewer_access`, `service_identity`, `derived_views` |
| A6 | `registry_gateway` | `authorization_guard`, `derived_views`, `data_provider` |
| A7 | `snapshot_import` | `expense_intake`, `data_provider` |
| A8 | `snapshot_import` | `expense_intake`, `project_tracking`, `photo_management`, `progress_photo_repository` |
| A9 | `financial_policy` | `expense_intake`, `expense_management`, `snapshot_import`, `budget_management`, `project_tracking`, `derived_views`, `data_provider` |
| A10 | `staff_identity` | — |
| A11 | `authorization_guard` | `staff_identity`, `viewer_access`, `service_identity` |
| A12 | `service_identity` | `authorization_guard`, `snapshot_import` |
| A13 | `audit_writer` | `audit_repository`, `staff_identity`, `viewer_access`, `service_identity`, `snapshot_import`, `budget_management`, `expense_intake`, `expense_management`, `project_tracking`, `photo_management`, `staff_bootstrap`, `data_provider` |
| A14 | `binary_storage` | `expense_management`, `photo_management`, `api`, `api_irregular`, `runtime_settings`, `transport_guard` |
| A15 | `derived_views` | `registry_gateway` |
| A16 | `staff_identity` | `staff_access_repository`, `staff_bootstrap`, `data_provider` |
| A17 | `credential_security` | `staff_identity`, `viewer_access`, `service_identity` |
| A18 | `budget_management` | `snapshot_import`, `derived_views`, `budget_repository`, `snapshot_import_repository`, `project_section_repository`, `data_provider` |
| A19 | `expense_management` | `expense_intake`, `derived_views`, `budget_management` |
| A20 | `project_tracking` | `photo_management`, `data_provider` |
| A21 | `derived_views` | `financial_policy`, `audit_writer`, `audit_repository`, `snapshot_import_repository` |
| A22 | cross-cutting | every module that opens a transaction (listed in `30_trace.json`) |
| A23 | `audit_writer` | the A13 consumers |
| A24 | `models` | every runtime module |
| A25 | `transport_guard` | `api`, `api_irregular`, `runtime`, `runtime_settings`, `data_provider` |
| A26 | cross-cutting | `registry_gateway`, `snapshot_import`, `authorization_guard` |
| A27 | `derived_views` | — |
| A28 | `system_clock` | every module that reads the time (listed in `30_trace.json`) |
| A29 | `staff_bootstrap` | `staff_bootstrap_store`, `staff_bootstrap_cli`, `staff_identity`, `credential_security`, `data_provider` |
| A30 | `runtime_settings` | `registry_gateway`, `staff_identity`, `viewer_access`, `credential_security`, `binary_storage`, the ten repositories, `staff_bootstrap_store`, `data_provider` |
| A31 | evidence record | — |
| A32 | deployment process | — |

A22 (transaction guard) and A26 (exception payloads) are one rule applied the
same way by many modules, each to its own transactions and exceptions; no
module holds a mechanism the others call, so they are recorded
`cross_cutting` in `30_trace.json`. A28 (clock) was recorded so until
2026-11-07; its source is now `system_clock`, and each consumer applies the
one-instant rule to its own timestamps. A31, the security review of
States 0–2, is an evidence record checked by `design_lint --state 2`. A32, the
dependency pins and their check, is a deployment process.

## Dependency direction

The portal is one process. The order is the accepted `module_order`; a module
may know only modules on earlier lines, never one on a later line:

```text
models
data_provider
system_clock
credential_security, financial_policy
audit_repository, project_tracking_repository, project_section_repository,
  budget_repository, snapshot_import_repository, expense_repository,
  progress_photo_repository, staff_access_repository, viewer_access_repository,
  service_identity_repository
portal_store
staff_bootstrap_store
registry_gateway, binary_storage
audit_writer
authorization_guard
staff_identity
staff_bootstrap
viewer_access, service_identity
snapshot_import, budget_management
expense_management
expense_intake
project_tracking, photo_management
derived_views
api_irregular
api
transport_guard, runtime_settings
runtime
staff_bootstrap_cli
```

Each module's `Knows` section names exactly the modules it imports (the
accepted `imports.module_internal`, plus the one edge `api` → `api_irregular`
of the running code). Lines of the list are layers, not an
assertion that every module imports every earlier one.

## Facts several modules touch, and their one owner

- **Persistence.** Only the repositories, `portal_store` and
  `staff_bootstrap_store` touch the database. Each repository implements one
  `kind: interface` port of State 1 on a caller-owned `sqlite3.Connection`
  and never opens, commits, rolls back or closes it. `portal_store` opens the
  connection, owns the transaction and hands the repositories out through
  `PortalTransaction` (`tx.expenses()`, `tx.audit()` …); use cases reach
  persistence only through it. `staff_bootstrap_store` is the one other
  connection owner, for the bootstrap command only (A29). Physical storage is
  SQLite and a local binary root (R0-10). Table names are `config.persistence`
  (A30); the table and column layout is the persistence closure's.
- **Transactions.** The use case that owns an operation opens its transaction
  through `portal_store`, closes it exactly once and guards it as A22 requires.
  Registry network I/O happens outside any open portal transaction;
  an authorization check that opens its own transaction completes before the
  caller opens one, never inside it.
- **Audit.** The use case that owns a significant action builds its
  `AuditIntent` (action, result, reason, `entity_id` per A23) and passes it to
  `audit_writer`, which validates it and appends it in the caller's
  transaction. The two rejected records of A13 (`snapshot.import`,
  `staff.login_failed`) are appended and committed in the refused
  operation's own transaction; every other refusal writes none. The
  catalogue and the reason policy are A13's.
- **Binary content.** A client names a document or photo by its portal id,
  never by `file_ref` (A14). `expense_management` and `photo_management`
  re-check access and visibility and hand an `AuthorizedBinaryReference` to
  `binary_storage`, which alone resolves `file_ref` under the local binary
  root, recognises the media type from the content signature and returns
  `BinaryPayload`. The HTTP modules send its exact bytes. The concealment of
  R0-12 is owned by the module that owns the read: `expense_management`
  answers every refused document read with its one rejection, and
  `photo_management` answers an unknown, cross-project or hidden photo with
  its one validation refusal while a `binary_storage` failure passes
  through. The portal writes no binary content (R0-13, Q12).
- **Transport.** Host, origin, body-size, rate-limit, security-header and log
  rules of A25 run once, in `transport_guard`, before any route handler. The
  viewer browser credential is the host-only cookie read only by
  `api_irregular`; service principals and staff present bearer headers read
  only by `api`.
- **Data.** Every policy value generated code reads — a threshold, a name, a path, a closed set or a table over a State 1 enumeration — is a typed constant of `data_provider`, imported by name; no other module holds or repeats it (SPEC_STANDARD 6.10, 15.4; 2026-11-08).
- **Time.** Only `system_clock` reads the host clocks (A28). An operation
  that needs the current instant takes one wall reading from it and reuses
  it; the transport guard takes the elapsed reading for the viewer-entry
  window from it. No other module reads a host clock.
- **Configuration.** Environment values are read once, by `runtime_settings`,
  into `RuntimeSettings`; other modules read `config.*` constants or the
  settings they are handed, never the environment, with two exceptions
  kept from the running service: `registry_gateway` reads
  `REGISTRY_BASE_URL` at each Registry call (A6, A30) and `binary_storage`
  reads `BINARY_STORAGE_ROOT` and `BINARY_MAX_READ_BYTES` at each binary
  read, each refusing that call when its value is missing or unusable
  (Factory code `adapters/registry_gateway.py` `_registry_url`,
  `adapters/binary_storage.py`; owner 2026-11-06: current service
  behaviour accepted; technical decisions delegated).

## Changes against the former text

Each is the accepted Factory spec, kept under the owner decision of
2026-11-06 (current service behaviour accepted; technical decisions
delegated):

- **19 added modules** (above), each with its Factory commit in its section.
- **Narrow ports instead of one facade.** The former text kept
  `portal_store` as one typed facade "if the target Factory proves complete
  `kind: interface` materialization"; it did (Factory `af686d7364d2` …
  `62c73965adb8`, `ced617bd55c9` … `88c1dbbcc3a6`). Persistence is sqlite3,
  not SQLAlchemy (Factory `d1280708714f`).
- **No email challenges, no email modules** (owner 2026-11-07,
  `00_product.md` R0-23). The accepted spec split the challenges into
  `staff_challenges` (Factory `f12197b46a82`) and kept them inert while
  `StaffChallengeRepository` was deferred; the former `staff_identity`
  capability `send_staff_security_notice` had no sending function. The owner
  removed the feature: `staff_challenges`, `email_delivery_gateway`,
  `email_delivery_repository`, `send_staff_security_notice` and every
  challenge and delivery model leave the design. No module sends email.
- **Renamed or reshaped capabilities**, as accepted: `authorize_project_read`
  is `authorize_staff_project_read` and `authorize_viewer_project_read`;
  `authorize_project_mutation` is `authorize_staff_project_mutation`;
  `append_success_audit` and `append_rejection_audit` are one
  `append_audit`; `edit_manual_section_plans`, `review_budget_version` and
  `get_active_budget` are `upsert_manual_section_plan`, `get_budget_version`
  and `validate_project_section` (the active budget is read through the
  views); `list_viewer_project_ids` is `list_viewer_project_grants`, with
  `resolve_viewer_session`, `describe_viewer_session` and `sign_out_viewer`
  added (Factory `35a0a09ccbb1`); `staff_identity` gains
  `create_staff_account` and `resolve_staff_session`.
- **Binary answers are exact bytes**, not a stream with the declared media
  type (A14, Factory `babd5e5262d9`).
- **Module paths**: `staff_identity`, `viewer_access`, `service_identity` and
  `snapshot_import` are `application/*`, not `domain/*` (Factory
  `4bdaa008e1d7`).

## `models`

### Owns

The State 1 records M01–M46 (M38–M46 the row models of the data provider's
tables, with their enumerations `CapabilitySet`, `ImportAuditReason`,
`TransportGuardRefusal` and `BootstrapCommandOutcome`), their projections and answers, the request
models, the repository interfaces and the runtime models, as plain frozen typed
data with their closed enumerations (A24). No behaviour beyond the local
validators of their closed choices (State 1 modeling conventions).

### Knows

Nothing.

### Must not own

Repository lookup, runtime configuration, Registry or storage I/O,
authorization, cross-record uniqueness or any lifecycle transition.

### Depth assessment

- kind: deep
- hidden mechanism: type validity of the portal's shared vocabulary; a rule
  placed here would have no single owner

## `data_provider`

### Owns

The typed constants of `70_data_provider_closure.json`, the one home of each
value generated code reads (SPEC_STANDARD 6.10 version 2, 15.3.1): the money
values and work-balance signs (A9), the Registry variable, paths and timeout
(A6, A30), the session lifetimes and credential entropy (A30), the audit
significance (A13), the capability sets (A2), the staff and principal
transitions (A3), the password bounds (A16), the supported contract versions
(A7), the import audit table (A18), the completion bound (A20), the transport
values (A25) and the bootstrap exit codes (A29). Emitted deterministically
(`python_constant_data_v1`); 2026-11-08.

### Knows

`models`, for the row models and enumerations of its tables.

### Must not own

Behaviour, selection, validation, defaults, runtime configuration, or any
value a deterministic backend reads from its own IR.

### Hides

The values from every generator's prompt: a generated consumer is given the
name and type of a constant and imports it, so the running code reads the
value while the generator never sees it (SPEC_STANDARD 15.9).

### Depth assessment

- kind: deep
- hidden mechanism: the one home of every policy value; a value moves here
  once and every reader imports it

### Candidate public capabilities

```text
API_PREFIX
AUDIT_ACTION_SIGNIFICANCE
BOOTSTRAP_EXIT_CODES
CAPABILITY_SET_MEMBERS
COMPLETION_PERCENT_MAX
CREDENTIAL_SECRET_BYTES
HEALTH_LIVE_PATH
HEALTH_OK_STATUS
HEALTH_READY_PATH
IMPORT_OUTCOME_AUDIT
MONEY_CURRENCY
MONEY_FRACTION_DIGITS
MONEY_ROUNDING
NO_STORE_CACHE_CONTROL
NO_STORE_PATHS
PASSWORD_MAX_CODEPOINTS
PASSWORD_MIN_CODEPOINTS
PRINCIPAL_STATUS_TRANSITIONS
REGISTRY_BASE_URL_VARIABLE
REGISTRY_CONTEXT_SEGMENT
REGISTRY_PROJECTS_PATH
REGISTRY_TIMEOUT_SECONDS
REGISTRY_VALIDATE_SEGMENT
SECURITY_HEADERS
STAFF_SESSION_TTL_HOURS
STAFF_STATUS_TRANSITIONS
SUPPORTED_OCR_CONTRACT_VERSIONS
SUPPORTED_SNAPSHOT_CONTRACT_VERSIONS
TRANSPORT_GUARD_STATUSES
TRANSPORT_LOG_LABELS
VIEWER_ENTRY_PATH
VIEWER_LOGOUT_PATH
VIEWER_SESSION_TTL_DAYS
WORK_BALANCE_LABEL_SIGNS
```

## `system_clock`

### Owns

The source of time of A28: the only reader of the host wall clock and of the
host elapsed clock. One wall reading per call, the current UTC time as an
offset-naive datetime, and one elapsed reading per call, a monotonic count of
seconds as a float. The backend is `rules.system_clock_backend` (SPEC_STANDARD
§6.9 version 5) under `rules.time_source_policy`; coordinator 2026-11-07
(the accepted spec 459ac96c has no such module, `SOURCE.md`).

### Knows

Nothing.

### Must not own

When an operation reads the time, how many readings it takes, which instant
it reuses, any comparison, TTL arithmetic, storage or ordering of a reading,
and the rate-limit window.

### Hides

Which host primitives give the two readings and how the wall reading is made
offset-naive UTC.

### Depth assessment

- kind: deep
- hidden mechanism: the host clocks behind one wall and one elapsed reading

### Candidate public capabilities

```text
utc_now
monotonic_seconds
```

## `credential_security`

### Owns

A17 and the cryptographic part of A16 and A30: password hashing with
Argon2id at the library defaults (R0-06, Factory `39934597ae17`), issue of a
verification secret with the configured entropy, parsing of the
verification-secret envelope, constant-time verification, and redaction-safe
failure. The backend is `rules.credential_security_backend` (Factory
`8387e0a3d7fe`).

### Knows

`models`.

### Must not own

Account, token or session lifecycle, persistence, authorization, delivery,
HTTP credential extraction, or logging of a plaintext. An issuing module
receives the plaintext only for its immediate answer or delivery and persists
only the verification form.

### Hides

The hash library, salt and parameter encoding, random-byte generation and the
comparison.

### Depth assessment

- kind: deep
- hidden mechanism: the password hash and the verification-secret envelope

### Candidate public capabilities

```text
hash_password
verify_password
issue_verification_secret
parse_verification_secret
verify_secret
```

## `financial_policy`

### Owns

A9 and the arithmetic of A21: amount validation in the portal currency and
its quantization (the money constants of `data_provider`), section completed work, weighted overall
progress, remaining material without clamping, work balance and its label,
and the unavailable result where an input is missing.

### Knows

`models`, `data_provider`.

### Must not own

Record loading, persistence, presentation, currency conversion or a fallback
value.

### Hides

Decimal quantization and the order of each formula; it does no I/O and holds
no state.

### Depth assessment

- kind: deep
- hidden mechanism: the money and progress formulas of A9 over exact decimals

### Candidate public capabilities

```text
FinancialValidationError
validate_eur_amount
calculate_completed_work
calculate_overall_progress
calculate_material_balance
calculate_work_balance
```

## `audit_repository`

### Owns

The SQLite implementation of the `AuditRepository` port (the port itself is a `models` interface) on the caller's SQLite connection: append and read
of AuditRecord rows, and the append-only part of A21 for audit rows. Like every
repository it asserts open state and translates driver failures only through
the caller's `AuditRepositoryContext`, which the connection owner implements
(`PortalTransaction`, `SqliteStaffBootstrapStore`). Factory `5677993e5113`.

### Knows

`models`.

### Must not own

A connection, a commit or rollback, the audit catalogue, or any application
service.

### Hides

SQL, row shape and canonical serialization of audit rows.

### Depth assessment

- kind: deep
- hidden mechanism: the append-only audit table on a borrowed connection

### Candidate public capabilities

```text
create_audit_schema
SqliteAuditRepository
```

## `project_tracking_repository`

### Owns

The SQLite implementation of the `ProjectTrackingRepository` port (the port itself is a `models` interface): SectionProgress and WorkPayment rows.
Factory `ac279dd8cdba`.

### Knows

`models`.

### Must not own

A connection, a transaction, the payment replay decision or any formula.

### Hides

SQL, row shape and serialization of progress and payment rows.

### Depth assessment

- kind: deep
- hidden mechanism: the progress and payment tables on a borrowed connection

### Candidate public capabilities

```text
create_project_tracking_schema
SqliteProjectTrackingRepository
```

## `project_section_repository`

### Owns

The SQLite implementation of the `ProjectSectionRepository` port (the port itself is a `models` interface): PortalSection rows and their source-key
lookup, and the A18 rule that a referenced section is never deleted at the
storage level. Factory `a6d7b759519a`.

### Knows

`models`.

### Must not own

Section linking, budget activation or any transaction.

### Hides

SQL, row shape and serialization of section rows.

### Depth assessment

- kind: deep
- hidden mechanism: the portal-section table on a borrowed connection

### Candidate public capabilities

```text
create_project_section_schema
SqliteProjectSectionRepository
```

## `budget_repository`

### Owns

The SQLite implementation of the `BudgetRepository` port (the port itself is a `models` interface): BudgetVersion and SectionPlan rows, and the
storage form of A18's single-active and single-manual rules. Factory
`37b1f529eb16`.

### Knows

`models`.

### Must not own

Activation sequencing, plan mutability or any transaction.

### Hides

SQL, row shape and serialization of budget rows.

### Depth assessment

- kind: deep
- hidden mechanism: the budget-version and section-plan tables on a borrowed
  connection

### Candidate public capabilities

```text
create_budget_schema
SqliteBudgetRepository
```

## `snapshot_import_repository`

### Owns

The SQLite implementation of the `SnapshotImportRepository` port (the port itself is a `models` interface): ApprovedEstimateSnapshot and
SnapshotImportRecord rows, append-only (A18, A21). Factory `f8c5cb9a8142`.

### Knows

`models`.

### Must not own

Fingerprints, replay classification or any transaction.

### Hides

SQL, row shape and serialization of snapshot and import rows.

### Depth assessment

- kind: deep
- hidden mechanism: the append-only snapshot and import tables on a borrowed
  connection

### Candidate public capabilities

```text
create_snapshot_import_schema
SqliteSnapshotImportRepository
```

## `expense_repository`

### Owns

The SQLite implementation of the `ExpenseRepository` port (the port itself is a `models` interface): Expense, ExpenseAllocation and ExpenseDocument
rows read and written as one aggregate. Factory `0baceacca950`.

### Knows

`models`.

### Must not own

The allocation-sum rule, replay classification or any transaction.

### Hides

SQL, the three row shapes and their serialization.

### Depth assessment

- kind: deep
- hidden mechanism: the expense aggregate tables on a borrowed connection

### Candidate public capabilities

```text
create_expense_schema
SqliteExpenseRepository
```

## `progress_photo_repository`

### Owns

The SQLite implementation of the `ProgressPhotoRepository` port (the port itself is a `models` interface): ProgressPhoto rows and the lookup by
`intake_id` that A8's photo row uses. Factory `7eb7ebccc53d`.

### Knows

`models`.

### Must not own

Publication, visibility policy or any transaction.

### Hides

SQL, row shape and serialization of photo rows.

### Depth assessment

- kind: deep
- hidden mechanism: the progress-photo table on a borrowed connection

### Candidate public capabilities

```text
create_progress_photo_schema
SqliteProgressPhotoRepository
```

## `staff_access_repository`

### Owns

The SQLite implementation of the `StaffAccessRepository` port (the port itself is a `models` interface): staff accounts, staff sessions and
assignments, with the storage form of A16 (exact match on the normalized
email) and of the assignment uniqueness of A3. Factory `fd7905625fe7`.

### Knows

`models`.

### Must not own

Normalization, hashing, transitions or any transaction.

### Hides

SQL, row shapes and serialization of staff rows.

### Depth assessment

- kind: deep
- hidden mechanism: the staff identity tables on a borrowed connection

### Candidate public capabilities

```text
create_staff_access_schema
SqliteStaffAccessRepository
```

## `viewer_access_repository`

### Owns

The SQLite implementation of the `ViewerAccessRepository` port (the port itself is a `models` interface): client viewers, access credentials,
viewer sessions and project grants, with grant uniqueness. Factory
`62c73965adb8`.

### Knows

`models`.

### Must not own

Credential issue, revocation cascades or any transaction. It holds no
contact data (`ClientViewer` has none).

### Hides

SQL, row shapes and serialization of viewer rows.

### Depth assessment

- kind: deep
- hidden mechanism: the viewer access tables on a borrowed connection

### Candidate public capabilities

```text
create_client_access_schema
SqliteViewerAccessRepository
```

## `service_identity_repository`

### Owns

The SQLite implementation of the `ServiceIdentityRepository` port (the port itself is a `models` interface): service principals, service
credentials with their key versions, and producer grants. Factory
`88c1dbbcc3a6`.

### Knows

`models`.

### Must not own

Key-version allocation, scope decisions or any transaction.

### Hides

SQL, row shapes and serialization of producer identity rows.

### Depth assessment

- kind: deep
- hidden mechanism: the producer identity tables on a borrowed connection

### Candidate public capabilities

```text
create_producer_identity_schema
SqliteServiceIdentityRepository
```

## `portal_store`

### Owns

The portal's database connections (a new one per transaction) and its transactions: open, commit,
rollback and close, schema creation through the repositories, the
`PortalTransaction` that hands out one repository per port, and translation of
every storage failure to `PersistenceError` without SQL or driver detail;
`PortalTransaction` is the `AuditRepositoryContext` of the repositories it
hands out. `rules.persistence_backend` (Factory `d1280708714f`).

### Knows

`models` and the ten repositories.

### Must not own

Business validation, authorization, formulas, network calls, audit catalogue
selection, or an automatic retry. It imports no application or domain module.

### Hides

The SQLite connection, its isolation and the wiring of repositories to one
connection.

### Depth assessment

- kind: deep
- hidden mechanism: one connection and one transaction shared by the
  repositories of an operation

### Candidate public capabilities

```text
PersistenceError
PortalStore
PortalTransaction
```

## `staff_bootstrap_store`

### Owns

The persistence of the first-administrator bootstrap (A29): its own
connection, an exclusive write transaction, the emptiness check of the staff
table and the two inserts (account and its `staff.create` audit), committed
once or not at all. Factory `6011ac93b143`.

### Knows

`models`, `staff_access_repository`, `audit_repository`, `portal_store` (for
its error type only).

### Must not own

`PortalStore` or `PortalTransaction` use, any application service, or any
operation other than the bootstrap.

### Hides

The exclusive transaction that makes concurrent attempts create exactly one
account, and the reuse of the staff and audit row shapes.

### Depth assessment

- kind: deep
- hidden mechanism: create-if-empty in one exclusive write transaction

### Candidate public capabilities

```text
SqliteStaffBootstrapStore
```

## `registry_gateway`

### Owns

A6 and the Registry part of A5 and A15: HTTP calls to the Registry for the
active project list, project validation and project context at the
configured endpoint, paths and timeout (A30; the data-provider constants),
decoding, UUID identity matching, keeping only active projects while decoding
the list, and translation of every failure to `RegistryFailureKind` carried in
the `kind` field of `RegistryBoundaryError` (A26).

### Knows

`models`, `data_provider`.

### Must not own

Portal authorization, grants, caching as authority, Registry storage access or
a portal copy of Registry data.

### Hides

URLs, the HTTP client, status and body parsing and transport exceptions.

### Depth assessment

- kind: deep
- hidden mechanism: the Registry HTTP contract and its failure translation

### Candidate public capabilities

```text
RegistryBoundaryError
list_active_projects
validate_project_reference
get_project_context
```

## `binary_storage`

### Owns

A14's storage part: resolution of an authorized opaque `file_ref` under the
local binary root (R0-10), the read bound, recognition of the media type from
the leading signature bytes against the closed list per object kind, the
download name, and translation of a missing or unreadable object to
`BinaryStorageError`. `rules.binary_storage_backend` (Factory
`8387e0a3d7fe`). Read only: it writes no binary content (R0-13, Q12).

### Knows

`models`.

### Must not own

Actor, project or visibility authorization, retention, OCR, image
interpretation or fetching an arbitrary URL.

### Hides

Paths, the storage root and the signature table.

### Depth assessment

- kind: deep
- hidden mechanism: safe read of an opaque reference and content-signature
  recognition

### Candidate public capabilities

```text
BinaryStorageError
read_binary
```

## `audit_writer`

### Owns

A13 and A23: validation of an `AuditIntent` against the closed catalogue, the
significant-mutation actions and the result and reason policy, and the append
of exactly one AuditRecord per occurrence, including the rejected records
A13 names and service key-version provenance. The one record not written
through it is the bootstrap's `staff.create`: `staff_bootstrap` builds that
record itself, its `occurred_at` the bootstrap's one instant (A28), and
`staff_bootstrap_store` inserts it (A29; Factory code
`application/staff_bootstrap.py` 21, 39).

### Knows

`models`, `data_provider`, `system_clock`.

### Must not own

Business transaction success, action-specific details, authorization or
mutable audit history.

### Hides

Record construction and the catalogue checks.

### Depth assessment

- kind: deep
- hidden mechanism: the closed audit catalogue and its record construction

### Candidate public capabilities

```text
append_audit
```

## `authorization_guard`

### Owns

A1, A2, A4, A11 and the guard part of A5 and A12: one decision per operation —
session validity, active principal, project scope (assignment, viewer grant
or producer grant), required capability and Registry lifecycle — in the
declared order, with existence-hiding first failure. It reads the persisted
role and binds a session to its identity (Factory `efd08476a436`). "Immediate"
revocation (A11) is this module's: every request authenticated after it
observes it.

### Knows

`models`, `data_provider`, `system_clock`, `registry_gateway`, `portal_store`.

### Must not own

Session or credential issue, Registry transport, domain mutation, HTTP
status formatting or persistence of business facts.

### Hides

The guard sequence across principal kinds and the Registry check.

### Depth assessment

- kind: deep
- hidden mechanism: the ordered authorization sequence of A4

### Candidate public capabilities

```text
AuthenticationRejected
AuthorizationRejected
ArchivedProjectRejected
ScopedNotFoundError
conceal_authentication_failure
authorize_staff_project_read
authorize_viewer_project_read
authorize_staff_project_mutation
authorize_access_management
authorize_snapshot_import
```

## `staff_identity`

### Owns

A16 and the staff rows of A3 and A11: staff account creation by an
administrator, login and staff session issue, resolution and sign-out,
session revocation, status transitions with their cascade (sessions
revoked), password change, project assignment and its revocation, and the
administrative recovery override, the one replacement of a login email (A10,
Factory `3080ef0dbe73`). Session TTL is A30's.

### Knows

`models`, `data_provider`, `system_clock`, `credential_security`, `authorization_guard`,
`registry_gateway`, `audit_writer`, `portal_store`.

### Must not own

Sending email or any other message (the portal sends none, A10), project
authorization, viewer or service credentials, HTTP cookies or headers, or role-capability tables. It
sends no notice.

### Hides

Email normalization, password policy, existence-hiding login and the atomic
account, session and assignment sequencing.

### Depth assessment

- kind: deep
- hidden mechanism: the staff account and session lifecycle

### Candidate public capabilities

```text
IdentityInputRejected
create_staff_account
authenticate_staff
resolve_staff_session
sign_out_staff
revoke_staff_sessions
change_staff_status
change_staff_password
assign_staff_project
revoke_staff_project_assignment
perform_recovery_override
```

## `staff_bootstrap`

### Owns

A29: the first-administrator operation — normalize and validate the input
through `staff_identity`'s input boundary, hash the password through
`credential_security`, build the administrator account and its audit, and ask
`StaffBootstrapPort` to create it only on an empty staff table; refuse with
`BootstrapAlreadyCompletedError` otherwise. Factory `6011ac93b143` (R0-07).

### Knows

`models`, `system_clock`, `credential_security`, `staff_identity`.

### Must not own

`PortalStore`, `PortalTransaction`, any repository or the port's
implementation; it is not reachable from the HTTP router.

### Hides

Account and audit construction for the bootstrap and the disclosure rules of
the password.

### Depth assessment

- kind: deep
- hidden mechanism: the one-time first-administrator creation

### Candidate public capabilities

```text
bootstrap_first_administrator
BootstrapAlreadyCompletedError
```

## `viewer_access`

### Owns

The viewer rows of A3 and A11: ClientViewer creation and revocation,
ViewerAccessCredential issue (revoking every prior credential) and
revocation, viewer entry and session resolution, description and sign-out
(Factory `35a0a09ccbb1`), and project grants. Viewer session TTL is A30's.

### Knows

`models`, `data_provider`, `system_clock`, `credential_security`, `authorization_guard`,
`registry_gateway`, `audit_writer`, `portal_store`.

### Must not own

Registry context, capability evaluation, project data reads, cookies or
links, and any contact data of a viewer.

### Hides

Capability secret issue and verification and atomic credential replacement.

### Depth assessment

- kind: deep
- hidden mechanism: the viewer credential and session lifecycle

### Candidate public capabilities

```text
create_viewer
revoke_viewer
issue_viewer_access
revoke_viewer_access
enter_viewer_access
resolve_viewer_session
describe_viewer_session
sign_out_viewer
grant_viewer_project
revoke_viewer_project
list_viewer_project_grants
```

## `service_identity`

### Owns

A12 and the producer rows of A3 and A11: ServicePrincipal lifecycle,
ServiceCredential issue with monotonic key versions, rotation overlap and
revocation, producer grants, bearer authentication and producer scope.

### Knows

`models`, `data_provider`, `system_clock`, `credential_security`, `authorization_guard`,
`registry_gateway`, `audit_writer`, `portal_store`.

### Must not own

Snapshot validation or import, activation, Registry HTTP, or staff and viewer
authentication.

### Hides

Secret verification, key-version allocation and credential usability.

### Depth assessment

- kind: deep
- hidden mechanism: producer credentials with key versions and scope

### Candidate public capabilities

```text
create_service_principal
change_service_principal_status
issue_service_credential
revoke_service_credential
grant_producer_project
revoke_producer_project
authenticate_service_principal
authorize_producer_scope
```

## `snapshot_import`

### Owns

A7 for snapshots, the snapshot row and every row no consumer names of A8,
and the import part of A18: canonical snapshot validation and fingerprint,
supported contract and currency, section validation, replay and integrity
conflict classification, append-only acceptance with its import record and
audit, rejections classified by field in the `reason` field of
`SnapshotContentRejected` (A26, Factory `a12937fd79b6`), and the readable
import result.

### Knows

`models`, `data_provider`, `system_clock`, `authorization_guard`, `financial_policy`,
`audit_writer`, `portal_store`.

### Must not own

Activation, section linking, budget plans, producer credentials or Registry
transport.

### Hides

Canonicalization, the fingerprint and the atomic append.

### Depth assessment

- kind: deep
- hidden mechanism: canonical snapshot fingerprint and replay classification

### Candidate public capabilities

```text
SnapshotContentRejected
import_snapshot
get_snapshot_import_result
```

## `budget_management`

### Owns

A18 and the budget rows of A3: the manual budget and its section plans,
PortalSection identity and source-key linking, activation of an imported
version with the atomic switch of the active version, and the count of
expense allocations left without a current section after a switch.

### Knows

`models`, `system_clock`, `financial_policy`, `audit_writer`, `portal_store`.

### Must not own

Snapshot import, expense mutation, derived totals, Registry HTTP or deletion
of referenced sections.

### Hides

Section linking, activation sequencing and coexistence of versions.

### Depth assessment

- kind: deep
- hidden mechanism: budget-version activation with stable section identity

### Candidate public capabilities

```text
BudgetValidationError
BudgetConflictError
ensure_manual_budget
upsert_manual_section_plan
get_budget_version
activate_budget_version
validate_project_section
```

## `expense_management`

### Owns

A19 after creation: correction, inclusion and exclusion, explicit allocation
replacement with the exact-sum rule, atomic amount-plus-allocation
correction, document description and visibility, same-project targets, and
the access and visibility re-check before a document's content is read (A14).

### Knows

`models`, `data_provider`, `system_clock`, `financial_policy`, `binary_storage`,
`audit_writer`, `portal_store`.

### Must not own

OCR, automatic proportional allocation, budget plans or derived totals.

### Hides

Allocation replacement sequencing and conflict handling.

### Depth assessment

- kind: deep
- hidden mechanism: the expense aggregate's allocation-sum invariant

### Candidate public capabilities

```text
ExpenseValidationError
ExpenseConflictError
BinaryAccessRejected
correct_expense
set_expense_inclusion
replace_expense_allocations
update_expense_document
read_expense_document
```

## `expense_intake`

### Owns

The Expense row of A8 and A7 for recognition: projection of the confirmed
recognition request of an authenticated staff member into `ExpenseIntake`
(R0-17), supported-version enforcement, rejection of provider and raw fields,
canonical intake fingerprint and replay classification, initial allocation and
document consistency, and atomic creation of the aggregate with its audit.

### Knows

`models`, `data_provider`, `system_clock`, `financial_policy`, `audit_writer`, `portal_store`,
`expense_management`.

### Must not own

OCR, provider confidence, manual expense creation, budget management or
later correction.

### Hides

The projection of the recognition contract and the fingerprint.

### Depth assessment

- kind: deep
- hidden mechanism: canonical intake fingerprint and replay classification

### Candidate public capabilities

```text
create_expense_from_recognition
```

## `project_tracking`

### Owns

A20 and the WorkPayment row of A8: manual section progress in [0, 100],
payment registration idempotent by `payment_id`, section and project checks,
and the progress and payment lists.

### Knows

`models`, `data_provider`, `system_clock`, `financial_policy`, `budget_management`,
`audit_writer`, `portal_store`.

### Must not own

Progress formulas, progress from photos, budget editing or accounting.

### Hides

Range validation and payment replay classification.

### Depth assessment

- kind: deep
- hidden mechanism: manual progress and idempotent payment records

### Candidate public capabilities

```text
TrackingValidationError
TrackingConflictError
set_section_progress
register_work_payment
list_project_progress
list_project_payments
```

## `photo_management`

### Owns

The ProgressPhoto row of A8: idempotent publication by `intake_id`, caption,
section and visibility changes, same-project sections, the order of the
staff photo list it returns (accepted `list_progress_photos`; the overview
gallery's order of A27 is `derived_views`') and the access and visibility re-check before a photo's content is read
(A14). A photo never sets progress (A20).

### Knows

`models`, `system_clock`, `binary_storage`, `audit_writer`, `portal_store`.

### Must not own

Telegram intake, binary writing, financial or progress mutation.

### Hides

Replay classification and photo ordering.

### Depth assessment

- kind: deep
- hidden mechanism: idempotent photo publication and visibility

### Candidate public capabilities

```text
PhotoValidationError
PhotoConflictError
publish_progress_photo
update_progress_photo
list_progress_photos
read_progress_photo
```

## `derived_views`

### Owns

A15, A21 (derivation), A27 and the view part of A5: the viewer project list,
the project overview with its project and availability (Factory
`d2c4511ea119`), budget, expense, progress and payment views with their
orderings, and explicit unavailable values. Inaccessible viewer projects are
left out (Factory `00ac72f18d9c`).

### Knows

`models`, `viewer_access`, `registry_gateway`, `financial_policy`,
`portal_store`, `authorization_guard`.

### Must not own

Authorization policy, persistence writes, fallback zeros, corrections or a
stored Registry copy.

### Hides

Read composition, projection, ordering and formula sequencing.

### Depth assessment

- kind: deep
- hidden mechanism: read-time projection of owning records into views

### Candidate public capabilities

```text
list_viewer_projects
build_project_overview
build_budget_view
build_expense_view
build_progress_view
build_payment_view
```

## `api_irregular`

### Owns

The viewer browser boundary (R0-09): viewer entry from the JSON body, cookie
issue, extraction and clearing per `rules.viewer_cookie_transport_backend`,
session restore and logout, the viewer project list and overview, and the
viewer's document and photo answers as exact bytes with the disposition of
A14. A viewer bearer header is refused. Factory `f42548473a1a`,
`61dfb1b7d468`, `d9b892e39997`.

### Knows

`models`, `viewer_access`, `authorization_guard`, `derived_views`,
`expense_management`, `photo_management`.

### Must not own

Authorization decisions, visibility policy, storage reads or any persistence.

### Hides

Cookie encoding and the binary response construction.

### Depth assessment

- kind: facade
- delegates to: `viewer_access`, `authorization_guard`, `derived_views`,
  `expense_management`, `photo_management`

### Candidate public capabilities

```text
viewer_enter_endpoint
viewer_restore_session_endpoint
viewer_logout_endpoint
list_viewer_projects_endpoint
viewer_project_overview_endpoint
viewer_read_expense_document_endpoint
viewer_read_progress_photo_endpoint
```

## `api`

### Owns

The staff, administrator and producer HTTP JSON routes of
`rules.http_router_backend` (Factory `300bd11d2660`): request-body decoding
into the request models of `models`, bearer extraction, one owning use case per route, safe projections, and the
translation of declared failures by its `error_policy`. Routes for
password change, recovery override, progress, payments, photos, budget
version and the administrator project list are the accepted ones (Factory
`3080ef0dbe73`, `fae77f993e03`).

### Knows

`models`, `staff_identity`, `viewer_access`, `service_identity`,
`authorization_guard`, `snapshot_import`, `budget_management`,
`expense_intake`, `expense_management`, `project_tracking`,
`photo_management`, `derived_views`, `portal_store`,
`financial_policy`, `registry_gateway`, `api_irregular` (the running router
mounts the seven viewer endpoints, Factory code `api/router.py` 22; the
accepted `imports.module_internal` lacks this edge, see `SOURCE.md`).

### Must not own

Role or capability decisions, Registry policy, transactions, formulas, file
reference safety, queries or a business rule. Client-supplied project
context, roles and capabilities are never forwarded as authority.

### Hides

Framework request and response mechanics.

### Depth assessment

- kind: facade
- delegates to: `staff_identity`, `viewer_access`,
  `service_identity`, `authorization_guard`, `snapshot_import`,
  `budget_management`, `expense_intake`, `expense_management`,
  `project_tracking`, `photo_management`, `derived_views`

### Candidate public capabilities

```text
create_app
```

## `transport_guard`

### Owns

A25 at the request boundary: one middleware that reads each path without
the `/api` prefix (stripped by the deployment proxy, A25; a path still
carrying it is read the same way), admits only trusted hosts, checks the origin of viewer sign-out, bounds the
body, rate-limits viewer entry per client address and route, sets the
security and `no-store` headers and writes one redacted log line. Factory
`babd5e5262d9`, `dc351917d376`, `51d19fdf035e`.

### Knows

`models`, `data_provider`, `system_clock`.

### Must not own

Authentication, authorization, routing or any business rule.

### Hides

Path canonicalization, origin normalization, the rate-limit buckets and the
log format.

### Depth assessment

- kind: deep
- hidden mechanism: the ordered transport checks of A25 in one middleware

### Candidate public capabilities

```text
install_transport_guards
```

## `runtime_settings`

### Owns

A30's environment part: load, normalize, default and validate the closed
table `config.runtime_environment_variables` into `RuntimeSettings` once at
start, including the startup consistency of the binary bounds (A14). Factory
`38626cc7be12`.

### Knows

`models`.

### Must not own

A default for a value nobody chose, or any check that uses a setting.

### Hides

Environment reading and per-environment defaults.

### Depth assessment

- kind: deep
- hidden mechanism: the closed environment table and its validation

### Candidate public capabilities

```text
load_runtime_settings
```

## `runtime`

### Owns

The running application (R0-10, R0-11): one `PortalStore` from the settings,
the inner `api` application, the transport guard, and the public liveness and
readiness answers that change nothing. Factory `38626cc7be12`,
`21658368525f`, `e8a6189534a7`.

### Knows

`models`, `data_provider`, `portal_store`, `api`, `transport_guard`, `runtime_settings`.

### Must not own

Routes other than health, business rules or a second store.

### Hides

Application composition and the bounded readiness check.

### Depth assessment

- kind: facade
- delegates to: `api`, `transport_guard`, `runtime_settings`, `portal_store`

### Candidate public capabilities

```text
create_runtime_app
```

## `staff_bootstrap_cli`

### Owns

The local command of A29 and R0-07: read the email from the terminal and the
password twice without echo, refuse a mismatch before any store exists,
resolve the database through `runtime_settings`, call the bootstrap, and map
each outcome to its closed exit code. The only entry point that reaches the
bootstrap. Factory `6011ac93b143`.

### Knows

`models`, `data_provider`, `runtime_settings`, `staff_bootstrap`, `staff_bootstrap_store`,
`staff_identity`.

### Must not own

An HTTP route, a password from arguments, environment or file, or any output
of a credential.

### Hides

Terminal input and exit-code mapping.

### Depth assessment

- kind: facade
- delegates to: `staff_bootstrap`, `staff_bootstrap_store`,
  `runtime_settings`

### Candidate public capabilities

```text
run_bootstrap_cli
```
