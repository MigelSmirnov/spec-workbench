# State 5 — Client Portal public module operations

## Status

Migrated on 2026-11-06 from the former `spec/50_public_apis.md` (authoring
pass of 2026-07-18/19, `SOURCE.md`) and the accepted Factory spec
`projects/client_portal_sandbox/specs/base/global_spec.json` (sha256
`459ac96c4b8febc629c81178c9d0a84ee072d1662dc52f44d74fb0993cb3c2c7`, Factory
`6011ac93b143`): its `module_functions`, `imports.module_internal`, the
contracts and notes of each operation and the route table
`rules.http_router_backend`. Builds on States 0–4: `00_product.md`,
`01_models.md`, `02_rules.md` (A1–A32), `30_modules.md` and `40_flows.md`.

One public operation per State 3 capability (108), each proven by the State 4
flows `50_api_plan.json` names. An operation is what another module, the
HTTP route table or the host may call; everything else a module does is
hidden. Inputs and outputs name State 1 models; exact Python signatures are
State 6's, and the accepted contracts are their evidence. Callers are the
modules that import the operation in the accepted `imports.module_internal`,
or the boundary that reaches it when no module does. `50_exposure_plan.json`
says which operations an HTTP route exposes.

Where the former text and the accepted spec disagree, the accepted spec is
kept (owner 2026-11-06: current service behaviour accepted; technical
decisions delegated); every such case is listed in "Changes against the former
text" at the end.

## Conventions every operation follows

- **Trusted context.** No operation accepts a role, capability, actor id or
  Registry context from its caller as authority. Identity operations turn a
  presented credential into a `StaffActorContext`, `ViewerActorContext` or
  `ServiceActorContext`; `module:authorization_guard` turns an actor context
  and a `project_id` into an `AuthorizedProjectContext` (A4). A project-scoped
  use case receives that context, never an unchecked `project_id`, and
  re-reads the persisted principal where its own notes say so.
- **Store.** A use case receives the one `PortalStore` and opens its own
  `PortalTransaction` through it; it reaches a table only through the narrow
  port the transaction hands out (`tx.staff_access()`, `tx.expenses()` …).
  `PortalStore`, `PortalTransaction`, the eleven `Sqlite*Repository` classes
  and `SqliteStaffBootstrapStore` are exported classes, not operations: their
  methods are State 6 contracts and the persistence closure's.
- **Transactions.** The operation that opens a transaction closes it exactly
  once under the transaction guard of A22: an explicit open flag, rollback
  only while it is open, the original failure re-raised unchanged. A guard
  check that opens its own transaction closes it before its caller opens one.
  Registry and email network calls happen with no portal transaction open.
- **Audit.** A significant success and its audit record commit in one
  transaction through `audit_writer.append_audit` (A13, A23); an idempotent
  replay writes no second creation audit. The audited action, result, reason
  and `entity_id` are the operation's to build.
- **Time.** Every timestamp an operation writes is the persisted UTC time of
  A28, taken when the change is made.
- **Refusal.** An operation returns its output or raises one declared
  exception; a refusal is decided before the first write, so it writes
  nothing, except where its Errors say the rejection is itself recorded.
  Exceptions carry data in fields, not messages (A26). The route table maps
  each once to a status with an empty body:

  | exception | owner | status |
  |---|---|---|
  | `AuthenticationRejected` | `authorization_guard` | 401 |
  | `AuthorizationRejected` | `authorization_guard` | 403 |
  | `ScopedNotFoundError` | `authorization_guard` | 404 |
  | `BinaryAccessRejected` | `expense_management` | 404 |
  | `ArchivedProjectRejected` | `authorization_guard` | 409 |
  | `IdentityInputRejected` | `staff_identity` | 422 |
  | `BudgetValidationError`, `ExpenseValidationError`, `PhotoValidationError`, `TrackingValidationError`, `FinancialValidationError` | owning module | 422 |
  | `BudgetConflictError`, `ExpenseConflictError`, `PhotoConflictError`, `TrackingConflictError` | owning module | 409 |
  | `ChallengeRejected` | `staff_challenges` | 400 |
  | `ChallengeRateLimited` | `staff_challenges` | 429 |
  | `RegistryBoundaryError` | `registry_gateway` | 502 |
  | `EmailDeliveryError` | `email_delivery_gateway` | 502 |
  | `PersistenceError` | `portal_store` | 500 |
  | `BinaryStorageError` | `binary_storage` | 500 |

  Any other failure is 500. No failure becomes a success, an empty list or a
  zero.
- **Concealment.** An unknown, revoked or expired credential or session and a
  non-active principal are one `AuthenticationRejected`; an inaccessible
  project or record is `ScopedNotFoundError` or `AuthorizationRejected` as the
  operation says, never a disclosure of what exists (A4, A11).
- **Archived projects.** Reads of an archived project succeed; every mutation
  of its records and every new grant or assignment for it is
  `ArchivedProjectRejected`; revocation consults no Registry (R0-24).
- **Order.** Every list in an output is in the order A15 or A27 names for it.

## `public_op:credential_security.hash_password`

### Owner

`module:credential_security`. Hash an accepted plaintext password with the configured scheme, never keeping the plaintext.

### Callers

`module:staff_bootstrap`, `module:staff_challenges`, `module:staff_identity`, `module:viewer_access`.

### Inputs

The exact plaintext password, already accepted by the A16 input policy of its
caller.

### Outputs

The password hash string of `rules.credential_security_backend` (Argon2id).

### Observable effect

None.

### Enforces

A17 and `rules.credential_security_backend`: the exact plaintext is hashed,
never normalized, logged or persisted.

### Errors

A failure of the hashing backend propagates; no fallback hash is returned.

### State impact

Pure; no store access.

## `public_op:credential_security.verify_password`

### Owner

`module:credential_security`. Compare a presented password with a stored hash.

### Callers

`module:staff_identity`, `module:viewer_access`.

### Inputs

The exact presented password and the stored password hash.

### Outputs

The comparison result, true only for a match.

### Observable effect

None.

### Enforces

A17: verification by `rules.credential_security_backend`; the result says
nothing about why a comparison failed.

### Errors

None of its own: a malformed or unsupported hash compares false.

### State impact

Pure; no store access.

## `public_op:credential_security.issue_verification_secret`

### Owner

`module:credential_security`. Mint a one-time verification secret for one record, returning its plaintext once.

### Callers

`module:service_identity`, `module:staff_challenges`, `module:staff_identity`, `module:viewer_access`.

### Inputs

The UUID of the record the secret will belong to and the entropy in bytes.

### Outputs

`IssuedSecret`: the envelope token (selector and secret) in plaintext and the
verification hash its caller persists.

### Observable effect

None.

### Enforces

A17: the envelope of `rules.verification_envelope_policy` and
`rules.credential_security_backend`; the plaintext exists only in the
returned value.

### Errors

A failure of the entropy source or hashing backend propagates.

### State impact

Pure; no store access.

## `public_op:credential_security.parse_verification_secret`

### Owner

`module:credential_security`. Decode a presented envelope token into its selector and secret.

### Callers

`module:service_identity`, `module:staff_challenges`, `module:staff_identity`, `module:viewer_access`.

### Inputs

The opaque presented token.

### Outputs

`PresentedSecret`: the selector UUID and the secret.

### Observable effect

None.

### Enforces

A17: only envelopes the backend accepts decode; the selector names a record
and is never proof of anything.

### Errors

A malformed envelope is rejected; each caller turns that rejection into its
own concealed failure (`AuthenticationRejected`).

### State impact

Pure; no store access.

## `public_op:credential_security.verify_secret`

### Owner

`module:credential_security`. Compare a presented secret with a stored verification hash.

### Callers

`module:service_identity`, `module:staff_challenges`, `module:staff_identity`, `module:viewer_access`.

### Inputs

The presented secret and the stored verification hash.

### Outputs

The comparison result, true only for a match.

### Observable effect

None.

### Enforces

A17: constant-time verification by the backend; it reads no storage and logs
neither value, and decides nothing about the record's lifecycle.

### Errors

None of its own: a malformed hash or secret compares false.

### State impact

Pure; no store access.

## `public_op:financial_policy.validate_eur_amount`

### Owner

`module:financial_policy`. Accept one EUR amount under the money policy and return it quantized.

### Callers

`module:budget_management`, `module:expense_intake`, `module:expense_management`, `module:project_tracking`, `module:snapshot_import`.

### Inputs

A currency code, a `Decimal` amount and whether the amount must be strictly
positive (default: non-negative).

### Outputs

The amount quantized to two digits, ROUND_HALF_UP.

### Observable effect

None.

### Enforces

A9 and `rules.money_policy`: EUR only, no conversion, the sign rule the caller
names.

### Errors

`FinancialValidationError` for another currency or a forbidden sign.

### State impact

Pure.

## `public_op:financial_policy.calculate_completed_work`

### Owner

`module:financial_policy`. Compute the completed-work amount of one section from its planned work and completion percent.

### Callers

`module:derived_views`.

### Inputs

The section's planned work amount and its completion percent (0–100).

### Outputs

The completed-work amount, rounded per section as `rules.money_policy` says.

### Observable effect

None.

### Enforces

A9: decimal arithmetic only, never float.

### Errors

None for inputs its callers have validated.

### State impact

Pure.

## `public_op:financial_policy.calculate_overall_progress`

### Owner

`module:financial_policy`. Compute the weighted overall progress of a project's sections, or report that it has none.

### Callers

`module:derived_views`.

### Inputs

The `ProgressSectionView` list of one project.

### Outputs

The weighted R9 progress over sections with positive planned work and a
reported percent, or `None` when that denominator is zero.

### Observable effect

None.

### Enforces

A9: a section without a reported percent counts in neither numerator nor
denominator and is never read as zero; no arithmetic mean; no fabricated zero.

### Errors

None.

### State impact

Pure.

## `public_op:financial_policy.calculate_material_balance`

### Owner

`module:financial_policy`. Compute planned minus actual material spend.

### Callers

`module:derived_views`.

### Inputs

Planned and actual material amounts.

### Outputs

Their quantized difference; a negative overspend is kept, never clamped.

### Observable effect

None.

### Enforces

A9.

### Errors

None.

### State impact

Pure.

## `public_op:financial_policy.calculate_work_balance`

### Owner

`module:financial_policy`. Compute completed work minus payments and its closed label.

### Callers

`module:derived_views`.

### Inputs

The completed-work total and the payments total of one project.

### Outputs

`WorkBalanceResult`: the quantized difference and the `WorkBalanceLabel`
derived from its sign.

### Observable effect

None.

### Enforces

A9 and `rules.money_policy`.

### Errors

None.

### State impact

Pure.

## `public_op:audit_repository.create_audit_schema`

### Owner

`module:audit_repository`. Create the append-only audit table on a connection its owner holds, if missing.

### Callers

`module:portal_store`, `module:staff_bootstrap_store`.

### Inputs

An open SQLite connection owned by the caller.

### Outputs

None: the table named by `config.persistence.audit_table_name` exists, one
column per `AuditRecord` field, `audit_id` the primary key.

### Observable effect

None beyond the table.

### Enforces

A21 (audit rows are append-only) and A30 (table names are
`config.persistence`). Idempotent; no runtime value is interpolated into SQL.

### Errors

A driver failure propagates to the connection owner, which translates it.

### State impact

Creates the table when absent; never commits, rolls back, closes, drops or
alters.

## `public_op:project_tracking_repository.create_project_tracking_schema`

### Owner

`module:project_tracking_repository`. Create the section-progress and work-payment tables on the caller's connection, if missing.

### Callers

`module:portal_store`.

### Inputs

An open SQLite connection owned by the caller.

### Outputs

None: the tables `config.persistence.section_progress_table_name` (key
`project_id`, `section_id`) and `config.persistence.work_payment_table_name`
(key `payment_id`) exist, one column per field of `SectionProgress` and
`WorkPayment`.

### Observable effect

None beyond the tables.

### Enforces

A20, A8 (payment replay identity), A30. Idempotent.

### Errors

A driver failure propagates to the connection owner.

### State impact

Creates the tables when absent; never commits, rolls back or closes.

## `public_op:project_section_repository.create_project_section_schema`

### Owner

`module:project_section_repository`. Create the portal-section table on the caller's connection, if missing.

### Callers

`module:portal_store`.

### Inputs

An open SQLite connection owned by the caller.

### Outputs

None: the table `config.persistence.project_section_table_name` exists, one
column per `PortalSection` field, `section_id` the key, (`project_id`,
`source_key`) unique when `source_key` is present.

### Observable effect

None beyond the table.

### Enforces

A18 (stable section identity), A30. Idempotent.

### Errors

A driver failure propagates to the connection owner.

### State impact

Creates the table when absent; never commits, rolls back or closes.

## `public_op:budget_repository.create_budget_schema`

### Owner

`module:budget_repository`. Create the budget-version and section-plan tables on the caller's connection, if missing.

### Callers

`module:portal_store`.

### Inputs

An open SQLite connection owned by the caller.

### Outputs

None: the tables `config.persistence.budget_version_table_name` and
`config.persistence.section_plan_table_name` exist, one column per field of
`BudgetVersion` and `SectionPlan`, (`version_id`, `section_id`) unique.

### Observable effect

None beyond the tables.

### Enforces

A18: at most one manual and at most one active version per project, by unique
partial indexes. A30. Idempotent.

### Errors

A driver failure propagates to the connection owner.

### State impact

Creates the tables when absent; never commits, rolls back or closes.

## `public_op:snapshot_import_repository.create_snapshot_import_schema`

### Owner

`module:snapshot_import_repository`. Create the approved-snapshot and import-record tables on the caller's connection, if missing.

### Callers

`module:portal_store`.

### Inputs

An open SQLite connection owned by the caller.

### Outputs

None: the tables `config.persistence.approved_snapshot_table_name` and
`config.persistence.snapshot_import_table_name` exist, projecting every field
of `ApprovedEstimateSnapshot` and `SnapshotImportRecord`; (`project_id`,
`estimate_id`, `estimate_version`) unique; snapshot sections in one
deterministic JSON text column.

### Observable effect

None beyond the tables.

### Enforces

A7, A8, A21 (snapshots and import records are append-only), A30. Idempotent.

### Errors

A driver failure propagates to the connection owner.

### State impact

Creates the tables when absent; never commits, rolls back or closes.

## `public_op:expense_repository.create_expense_schema`

### Owner

`module:expense_repository`. Create the expense, allocation and document tables on the caller's connection, if missing.

### Callers

`module:portal_store`.

### Inputs

An open SQLite connection owned by the caller.

### Outputs

None: the tables `config.persistence.expense_table_name`,
`config.persistence.expense_allocation_table_name` and
`config.persistence.expense_document_table_name` exist, projecting every
field of `Expense`, `ExpenseAllocation` and `ExpenseDocument`;
`recognized_document_id` unique; every allocation and document carries its
`expense_id`; at most one document per expense.

### Observable effect

None beyond the tables.

### Enforces

A19, A8 (recognized-document replay identity), A30. Idempotent.

### Errors

A driver failure propagates to the connection owner.

### State impact

Creates the tables when absent; never commits, rolls back or closes.

## `public_op:progress_photo_repository.create_progress_photo_schema`

### Owner

`module:progress_photo_repository`. Create the progress-photo table on the caller's connection, if missing.

### Callers

`module:portal_store`.

### Inputs

An open SQLite connection owned by the caller.

### Outputs

None: the table `config.persistence.progress_photo_table_name` exists, one
column per `ProgressPhoto` field, `photo_id` the key and `intake_id` unique.

### Observable effect

None beyond the table.

### Enforces

A8 (`rules.idempotency_identities.progress_photo`: `intake_id` is the one
replay identity), A30. Idempotent.

### Errors

A driver failure propagates to the connection owner.

### State impact

Creates the table when absent; never drops, alters, commits, rolls back or
closes.

## `public_op:email_delivery_repository.create_email_delivery_schema`

### Owner

`module:email_delivery_repository`. Create the email-delivery table on the caller's connection, if missing.

### Callers

`module:portal_store`.

### Inputs

An open SQLite connection owned by the caller.

### Outputs

None: the table `config.persistence.email_delivery_table_name` exists, one
column per `EmailDeliveryRecord` field, `delivery_id` the key.

### Observable effect

None beyond the table.

### Enforces

A10 (delivery telemetry), A30. Idempotent.

### Errors

A driver failure propagates to the connection owner.

### State impact

Creates the table when absent; never drops, alters, commits, rolls back or
closes.

## `public_op:staff_access_repository.create_staff_access_schema`

### Owner

`module:staff_access_repository`. Create the staff account, session and assignment tables on the caller's connection, if missing.

### Callers

`module:portal_store`, `module:staff_bootstrap_store`.

### Inputs

An open SQLite connection owned by the caller.

### Outputs

None: the tables `config.persistence.staff_account_table_name`,
`config.persistence.staff_session_table_name` and
`config.persistence.staff_assignment_table_name` exist, keyed by `staff_id`,
`session_id` and `assignment_id`; the account email is unique and
(`staff_id`, `project_id`) of an assignment is unique.

### Observable effect

None beyond the tables.

### Enforces

A16 (the stored email is the normalized identity), A3, A30. Idempotent.

### Errors

A driver failure propagates to the connection owner.

### State impact

Creates the tables when absent; never drops, alters, commits, rolls back or
closes.

## `public_op:viewer_access_repository.create_client_access_schema`

### Owner

`module:viewer_access_repository`. Create the viewer, credential, session and grant tables on the caller's connection, if missing.

### Callers

`module:portal_store`.

### Inputs

An open SQLite connection owned by the caller.

### Outputs

None: the tables `config.persistence.viewer_table_name`,
`config.persistence.viewer_credential_table_name`,
`config.persistence.viewer_session_table_name` and
`config.persistence.viewer_grant_table_name` exist, keyed by `viewer_id`,
`credential_id`, `session_id` and `grant_id`; (`viewer_id`, `project_id`) of a
grant is unique.

### Observable effect

None beyond the tables.

### Enforces

A3, A11, A30. Idempotent.

### Errors

A driver failure propagates to the connection owner.

### State impact

Creates the tables when absent; never drops, alters, commits, rolls back or
closes.

## `public_op:service_identity_repository.create_producer_identity_schema`

### Owner

`module:service_identity_repository`. Create the service principal, credential and producer-grant tables on the caller's connection, if missing.

### Callers

`module:portal_store`.

### Inputs

An open SQLite connection owned by the caller.

### Outputs

None: the tables `config.persistence.service_principal_table_name`,
`config.persistence.service_credential_table_name` and
`config.persistence.producer_grant_table_name` exist, keyed by
`service_principal_id`, `credential_id` and `grant_id`; (`service_principal_id`,
`project_id`) of a grant and (`service_principal_id`, `key_version`) of a
credential are unique.

### Observable effect

None beyond the tables.

### Enforces

A12, A3, A30. Idempotent.

### Errors

A driver failure propagates to the connection owner.

### State impact

Creates the tables when absent; never drops, alters or repopulates.

## `public_op:registry_gateway.list_active_projects`

### Owner

`module:registry_gateway`. Return the Registry's active projects for administrator project discovery.

### Callers

`module:api`.

### Inputs

None.

### Outputs

The typed active `ProjectReference` list, by `project_id` ascending
(`rules.project_list_ordering`), whatever the upstream order.

### Observable effect

One Registry request to `config.registry_request_paths.active_projects` with
no query parameters, under `config.registry_timeout_seconds`.

### Enforces

A6, A15, R0-08; A30 for the endpoint, read from the environment variable
`config.registry_endpoint_env_name`. Active-only selection happens while
decoding, never as an upstream filter (A30, State 2).

### Errors

`RegistryBoundaryError` with its `RegistryFailureKind` for timeout, transport,
HTTP, schema or identity failure (`rules.registry_failure_translation`).

### State impact

None in the portal.

## `public_op:registry_gateway.validate_project_reference`

### Owner

`module:registry_gateway`. Ask the Registry whether a project exists and in which lifecycle state.

### Callers

`module:authorization_guard`, `module:service_identity`, `module:staff_identity`, `module:viewer_access`.

### Inputs

A `project_id`.

### Outputs

`ProjectValidationResult` decoded from the response, whose identity is the
requested one.

### Observable effect

One Registry request to `config.registry_request_paths.project_validate`.

### Enforces

A6, A5: the portal never creates a `project_id` and never reads Registry
storage; the lifecycle decision is its caller's (`rules.registry_status_policy`).

### Errors

`RegistryBoundaryError` for timeout, transport, HTTP, schema or identity
failure.

### State impact

None in the portal.

## `public_op:registry_gateway.get_project_context`

### Owner

`module:registry_gateway`. Fetch the live Registry context of one project for a read.

### Callers

`module:derived_views`.

### Inputs

A `project_id`.

### Outputs

The live `ProjectContext` whose `project.project_id` is the requested one;
never `None`. Active and archived projects are both accepted.

### Observable effect

One Registry request to `config.registry_request_paths.project_context`.

### Enforces

A6, A15: the context is shown, never persisted or treated as portal-owned
truth.

### Errors

`RegistryBoundaryError` for timeout, transport, HTTP, schema or identity
failure.

### State impact

None in the portal.

## `public_op:email_delivery_gateway.deliver_email_message`

### Owner

`module:email_delivery_gateway`. Send one email message through the provider and record the attempt and its outcome.

### Callers

`module:staff_challenges`.

### Inputs

The `PortalStore` and one `EmailDeliveryRequest`.

### Outputs

The persisted `EmailDeliveryRecord` of the accepted outcome.

### Observable effect

One provider call, made with no portal transaction open. While challenges are
deferred no current operation calls it (R0-23, Q19).

### Enforces

A10 and R0-03: delivery is telemetry; it never marks a challenge valid,
consumed or verified. A22: one transaction inserts and commits the pending
record before the call, one further transaction writes the outcome.

### Errors

`EmailDeliveryError` for a provider failure, after the failed outcome is
recorded; a persistence failure propagates unchanged.

### State impact

Writes one `EmailDeliveryRecord` (pending, then accepted or failed).

## `public_op:binary_storage.read_binary`

### Owner

`module:binary_storage`. Read the exact bytes of one authorized document or photo from the local binary root.

### Callers

`module:expense_management`, `module:photo_management`.

### Inputs

An `AuthorizedBinaryReference`, built only by the owner of the record after
its access and visibility checks.

### Outputs

`BinaryPayload`: the exact bytes, the media type recognised from the content
signature, the size and the always-present download name; no storage locator
or credential.

### Observable effect

None.

### Enforces

A14, R0-12, R0-13: `rules.binary_storage_backend` and
`rules.binary_delivery_policy`; `file_ref` is resolved only here and only
under the root; the portal writes no binary content.

### Errors

`BinaryStorageError` for an unsafe, missing, oversize, unreadable or
unrecognised object.

### State impact

Read-only.

## `public_op:audit_writer.append_audit`

### Owner

`module:audit_writer`. Validate one audit intent and append it in the caller's open unit of work.

### Callers

`module:budget_management`, `module:expense_intake`, `module:expense_management`, `module:photo_management`, `module:project_tracking`, `module:service_identity`, `module:snapshot_import`, `module:staff_challenges`, `module:staff_identity`, `module:viewer_access`.

### Inputs

The caller's `AuditRepository` port and one `AuditIntent`.

### Outputs

The appended `AuditRecord`.

### Observable effect

None outside the caller's transaction.

### Enforces

A13 (closed catalogue `rules.audit_action_catalog`, reason policy
`rules.audit_result_reason_policy`), A23 (`entity_id`), A21 (append-only):
exactly one insert; a service actor keeps its `key_version`; no secret or
`file_ref` enters the details.

### Errors

A closed-choice violation of the intent is rejected; a persistence failure
propagates untranslated.

### State impact

Appends one `AuditRecord`; never commits or rolls back.

## `public_op:authorization_guard.conceal_authentication_failure`

### Owner

`module:authorization_guard`. Produce the one concealed authentication failure every identity module raises.

### Callers

`module:api`, `module:service_identity`, `module:staff_challenges`, `module:staff_identity`, `module:viewer_access`.

### Inputs

None.

### Outputs

A fresh `AuthenticationRejected` with no fields.

### Observable effect

None.

### Enforces

A4, A11, A26: no account, principal, project, selector or failure detail
survives.

### Errors

None.

### State impact

Pure.

## `public_op:authorization_guard.authorize_staff_project_read`

### Owner

`module:authorization_guard`. Decide whether a staff member may read one project.

### Callers

`module:api`.

### Inputs

The `PortalStore`, a `StaffActorContext`, the `project_id` and the read
`Capability` of the route.

### Outputs

`AuthorizedProjectContext` with the persisted actor, the capability, the
project and its accepted Registry status (active or archived).

### Observable effect

One Registry validation, after its own transaction closed.

### Enforces

A4: `rules.project_guard_sequence` in order — `valid_session`,
`active_principal`, `project_access`, `required_capability`,
`registry_lifecycle` — first failure winning; session, account and
assignment are read from persistence in one transaction; an administrator
passes the single-area scope, an operator needs an active assignment (A1,
A2, A5).

### Errors

`AuthenticationRejected` for an unknown, revoked or expired session or a
non-active account; `ScopedNotFoundError` for an operator without an active
assignment or a project the Registry does not know; `AuthorizationRejected`
for a role outside the scope rule or without the capability;
`RegistryBoundaryError`.

### State impact

Read-only.

## `public_op:authorization_guard.authorize_viewer_project_read`

### Owner

`module:authorization_guard`. Decide whether a client viewer may read one project.

### Callers

`module:api`, `module:api_irregular`.

### Inputs

The `PortalStore`, a `ViewerActorContext`, the `project_id` and the read
`Capability`.

### Outputs

`AuthorizedProjectContext` for the persisted viewer.

### Observable effect

One Registry validation, after its own transaction closed.

### Enforces

A4 as for staff reads; project access is an active `ProjectViewerGrant` read
from persistence; archived projects are readable (A5).

### Errors

`AuthenticationRejected`; `ScopedNotFoundError` for a missing or revoked
grant, indistinguishably, or a project the Registry does not know;
`AuthorizationRejected` without the capability; `RegistryBoundaryError`.

### State impact

Read-only.

## `public_op:authorization_guard.authorize_staff_project_mutation`

### Owner

`module:authorization_guard`. Decide whether a staff member may change one project's records.

### Callers

`module:api`.

### Inputs

The `PortalStore`, a `StaffActorContext`, the `project_id` and the manage or
activate `Capability` of the route.

### Outputs

`AuthorizedProjectContext` of an active project.

### Observable effect

One Registry validation, after its own transaction closed.

### Enforces

A4 and A5: the read sequence, and the Registry lifecycle must be active.

### Errors

As `authorize_staff_project_read`, and `ArchivedProjectRejected` for an
archived project.

### State impact

Read-only.

## `public_op:authorization_guard.authorize_access_management`

### Owner

`module:authorization_guard`. Decide whether a staff member may manage staff, viewer and producer access.

### Callers

`module:api`, `module:service_identity`, `module:staff_challenges`, `module:staff_identity`, `module:viewer_access`.

### Inputs

The `PortalStore` and a `StaffActorContext`.

### Outputs

The `StaffActorContext` carrying the identity and role read from persistence.

### Observable effect

None.

### Enforces

A1, A2, R0-14: the session is valid (present, not revoked, not expired), the
account active, and `portal.access.manage` comes from the stored role through
`rules.principal_capability_sets` (administrators only); one transaction,
rolled back once after the last read (A22).

### Errors

`AuthenticationRejected` for an invalid session or non-active account;
`AuthorizationRejected` for an operator.

### State impact

Read-only.

## `public_op:authorization_guard.authorize_snapshot_import`

### Owner

`module:authorization_guard`. Decide whether a service principal may publish a snapshot for one project.

### Callers

`module:api`, `module:snapshot_import`.

### Inputs

The `PortalStore`, a `ServiceActorContext` and the `project_id`.

### Outputs

`AuthorizedProjectContext` of an active project for the persisted principal
and its `key_version`.

### Observable effect

One Registry validation, after its own transaction closed.

### Enforces

A12 producer scope before any content validation, then the A4 sequence with
the service principal's bearer credential standing in for a session: the
stored principal must be active and, for a granted-projects scope, hold an
active grant for the project.

### Errors

`AuthenticationRejected` for an absent or non-active principal;
`ScopedNotFoundError` without the grant or for a project the Registry does
not know; `AuthorizationRejected` without the capability;
`ArchivedProjectRejected`; `RegistryBoundaryError`.

### State impact

Read-only.

## `public_op:staff_identity.authenticate_staff`

### Owner

`module:staff_identity`. Sign a staff member in with email and password and issue a session.

### Callers

`module:api`.

### Inputs

The `PortalStore`, the presented email and password (request body
`StaffLoginRequest`).

### Outputs

`StaffSessionGrant`: session id, staff id, role, the session token in
plaintext (returned once) and `expires_at`.

### Observable effect

None beyond the session and the audit.

### Enforces

A16 (normalized email), A17 (the session secret is issued for the new
`session_id`; only its hash is stored), R0-06 (fixed expiry of
`config.staff_session_ttl_hours`, twelve hours), A13: exactly one audit on
every outcome — `staff.login` success or `staff.login_failed` rejected with
no reason code, actor and entity empty when no account matched. Only an
active, verified account with a matching password signs in.

### Errors

`IdentityInputRejected` for an address that does not normalize under A16,
before any read or audit; it says nothing about any account.
`AuthenticationRejected` for every other failed check, without saying which;
the rejection audit is committed before it is raised.

### State impact

Writes one `StaffSession` and one `AuditRecord` per success; one
`AuditRecord` per rejection.

## `public_op:staff_identity.resolve_staff_session`

### Owner

`module:staff_identity`. Turn a presented staff bearer token into the trusted staff actor context.

### Callers

`module:api`.

### Inputs

The `PortalStore` and the bearer token.

### Outputs

Exactly one `StaffActorContext` (session id, staff id, role) from the
persisted session and account; never `None`.

### Observable effect

None.

### Enforces

A17: the parsed secret, not the envelope, is verified against the stored
hash; A4 `valid_session` and `active_principal`: the session exists, is not
revoked or expired, and its account is active with a verified email. One read
transaction, rolled back after the two reads (A22).

### Errors

`AuthenticationRejected` for every authentication outcome, an unparsable
token included; a persistence failure stays visible.

### State impact

Read-only.

## `public_op:staff_identity.sign_out_staff`

### Owner

`module:staff_identity`. End the staff session the actor is acting through.

### Callers

`module:api`.

### Inputs

The `PortalStore` and the `StaffActorContext`.

### Outputs

The revoked `StaffSession`.

### Observable effect

None beyond the revocation and the audit.

### Enforces

A11, A24 (a replacement session carries `revoked_at`), A13 (`staff.logout`).

### Errors

`AuthenticationRejected` for a missing, already revoked or expired session;
never a successful sign-out.

### State impact

Updates one `StaffSession`; appends one `AuditRecord`.

## `public_op:staff_identity.revoke_staff_sessions`

### Owner

`module:staff_identity`. Revoke every live session of one staff account on an administrator's request.

### Callers

`module:api`.

### Inputs

The `PortalStore`, the administrator's `StaffActorContext` and the target
`staff_id`.

### Outputs

`SessionRevocationResult`: the staff id, the number of sessions revoked and
the one `revoked_at` the operation captured, also when none was live.

### Observable effect

None beyond the revocations and the audit.

### Enforces

R0-14 (access management checked before the transaction opens), A11, A24,
A13 (`staff.sessions_revoke`).

### Errors

`AuthenticationRejected`, `AuthorizationRejected` from the access-management
check.

### State impact

Updates each live `StaffSession` of the account; appends one `AuditRecord`.

## `public_op:staff_identity.change_staff_status`

### Owner

`module:staff_identity`. Suspend, disable, reinstate or activate one staff account.

### Callers

`module:api`.

### Inputs

The `PortalStore`, the administrator's `StaffActorContext`, the `staff_id`
and the new `StaffStatus`.

### Outputs

The hash-free `StaffAccountView` of the changed account.

### Observable effect

None beyond the change and the audit.

### Enforces

A3 (`rules.status_transitions`) from the persisted status; A11
(`rules.revocation_cascades`): suspension and disabling revoke every live
session at the same timestamp; challenges have no storage while deferred
(R0-23). R0-19: activation from `pending_verification` records
`email_verified_at`; reinstatement from `suspended` keeps it. A13: one
`staff.suspend`, `staff.disable` or `staff.reinstate`.

### Errors

Access-management failures; `IdentityInputRejected` for a transition the table
does not list; `ScopedNotFoundError` for an unknown account.

### State impact

Updates one `StaffAccount` and the revoked sessions; appends one
`AuditRecord`.

## `public_op:staff_identity.change_staff_password`

### Owner

`module:staff_identity`. Replace the acting staff member's own password.

### Callers

`module:api`.

### Inputs

The `PortalStore`, the `StaffActorContext`, the current and the new password.

### Outputs

The hash-free `StaffAccountView`.

### Observable effect

None.

### Enforces

A16 for the new password, A17 for the hash; every other live session of the
account is revoked, the actor's own is kept. `rules.audit_action_catalog`
has no action for a password change, so none is appended. Neither plaintext
is persisted or audited.

### Errors

`AuthenticationRejected` for a wrong current password;
`IdentityInputRejected` for a new password outside A16.

### State impact

Updates the `StaffAccount` hash and the other live sessions.

## `public_op:staff_identity.create_staff_account`

### Owner

`module:staff_identity`. Create a staff account with an initial password on an administrator's request.

### Callers

`module:api`.

### Inputs

The `PortalStore`, the administrator's `StaffActorContext`, the email, the
initial password and the `StaffRole`.

### Outputs

The hash-free `StaffAccountView` of the new account, `pending_verification`
with no verified email.

### Observable effect

None: the administrator hands the password over outside the portal and
activates the account (R0-19); no message is sent (R0-23).

### Enforces

R0-14, A16 (normalized unique email), A17 (only the hash of the exact
password is stored), A13 (`staff.create` in the same transaction).

### Errors

Access-management failures; `IdentityInputRejected` for an invalid or taken
email or a password outside A16, before any insert.

### State impact

Writes one `StaffAccount` and one `AuditRecord`.

## `public_op:staff_identity.assign_staff_project`

### Owner

`module:staff_identity`. Give one operator access to one Registry project.

### Callers

`module:api`.

### Inputs

The `PortalStore`, the administrator's `StaffActorContext`, the operator's
`staff_id` and the `project_id`.

### Outputs

The new active `StaffProjectAssignment`.

### Observable effect

One Registry validation before the transaction opens.

### Enforces

R0-14, A5 and R0-24 (no new access to an unknown or archived project), A13
(`staff_assignment.create` with the project).

### Errors

Access-management failures; `ScopedNotFoundError` for a project the Registry
does not know or an unknown operator; `ArchivedProjectRejected` for an
inactive project; `AuthorizationRejected` for an existing active assignment;
`RegistryBoundaryError`.

### State impact

Writes one `StaffProjectAssignment` and one `AuditRecord`.

## `public_op:staff_identity.revoke_staff_project_assignment`

### Owner

`module:staff_identity`. Revoke one operator's project assignment.

### Callers

`module:api`.

### Inputs

The `PortalStore`, the administrator's `StaffActorContext` and the
`assignment_id`.

### Outputs

The revoked `StaffProjectAssignment`.

### Observable effect

None; the next guard check sees the revocation.

### Enforces

R0-14, R0-24 (no Registry call), A24, A13 (`staff_assignment.revoke`).

### Errors

Access-management failures; `ScopedNotFoundError` for an unknown or already
revoked assignment, indistinguishably.

### State impact

Updates one `StaffProjectAssignment`; appends one `AuditRecord`.

## `public_op:staff_identity.perform_recovery_override`

### Owner

`module:staff_identity`. Replace a staff member's login email by administrator recovery.

### Callers

`module:api`.

### Inputs

The `PortalStore`, the administrator's `StaffActorContext`, the `staff_id`
and the replacement email.

### Outputs

The hash-free `StaffAccountView` with the replacement email, verified.

### Observable effect

None.

### Enforces

R0-20 (administrator-only, not the ordinary email change), A16 for the
replacement, A13 (enhanced `staff.recovery_override` audit in the same
transaction).

### Errors

Access-management failures; `IdentityInputRejected` for the replacement email;
`ScopedNotFoundError` for an unknown account.

### State impact

Updates one `StaffAccount`; appends one `AuditRecord`.

## `public_op:staff_bootstrap.bootstrap_first_administrator`

### Owner

`module:staff_bootstrap`. Create the first active, verified administrator of an empty deployment.

### Callers

`module:staff_bootstrap_cli`.

### Inputs

The `StaffBootstrapPort` (the bootstrap store), the email and the initial
password.

### Outputs

The hash-free `StaffAccountView` of the new administrator.

### Observable effect

None.

### Enforces

R0-07 and A29 (`rules.staff_bootstrap_policy`): the A16 input rules through
the staff identity input boundary, the A17 hash, an account with no creator
and its `staff.create` audit with the system actor, handed to the port in one
call; no transaction, query or authorization of its own. The password or its
hash reaches no sink the policy forbids.

### Errors

`IdentityInputRejected` for the email or password;
`BootstrapAlreadyCompleted` when any staff account exists, with nothing
written; a storage failure propagates unchanged.

### State impact

Through the port: one `StaffAccount` and one `AuditRecord`, both or neither.

## `public_op:staff_challenges.issue_email_verification`

### Owner

`module:staff_challenges`. Refuse, while challenges are deferred, an administrator's request for an email-verification challenge.

### Callers

`module:api`.

### Inputs

The `PortalStore`, the administrator's `StaffActorContext` and the
`staff_id`.

### Outputs

None while deferred: no `ChallengeIssueView` is fabricated.

### Observable effect

None.

### Enforces

R0-23 and Q19: the operation is inert until a challenge repository exists;
the A10 policy is the design it follows once built.

### Errors

`AuthenticationRejected`, before authorization or any input check.

### State impact

None: no transaction, read, write, audit or delivery.

## `public_op:staff_challenges.confirm_email_verification`

### Owner

`module:staff_challenges`. Refuse, while challenges are deferred, a presented email-verification token.

### Callers

`module:api`.

### Inputs

The `PortalStore` and the token.

### Outputs

None while deferred.

### Observable effect

None.

### Enforces

R0-23, Q19; no email is verified by this route (R0-19).

### Errors

`AuthenticationRejected`, before the token is parsed.

### State impact

None.

## `public_op:staff_challenges.request_email_change`

### Owner

`module:staff_challenges`. Refuse, while challenges are deferred, a staff member's request to change their email.

### Callers

`module:api`.

### Inputs

The `PortalStore`, the `StaffActorContext` and the new email.

### Outputs

None while deferred.

### Observable effect

None.

### Enforces

R0-23, Q19.

### Errors

`AuthenticationRejected`, before authorization or normalization.

### State impact

None.

## `public_op:staff_challenges.confirm_email_change`

### Owner

`module:staff_challenges`. Refuse, while challenges are deferred, a presented email-change token.

### Callers

`module:api`.

### Inputs

The `PortalStore` and the token.

### Outputs

None while deferred.

### Observable effect

None.

### Enforces

R0-23, Q19.

### Errors

`AuthenticationRejected`, before the token is parsed.

### State impact

None.

## `public_op:staff_challenges.request_password_reset`

### Owner

`module:staff_challenges`. Accept a password-reset request with one identical answer for every address.

### Callers

`module:api`.

### Inputs

The `PortalStore` and the presented email.

### Outputs

None, on every path (202 with no body).

### Observable effect

None while deferred: no challenge is issued and nothing is sent.

### Enforces

R0-06 and R0-15 (an unauthenticated surface that discloses no existence):
the address is normalized and a rejected normalization is swallowed, so a
malformed, unknown and known address are answered alike. R0-23.

### Errors

None for any presented value.

### State impact

None.

## `public_op:staff_challenges.complete_password_reset`

### Owner

`module:staff_challenges`. Refuse, while challenges are deferred, a password-reset completion.

### Callers

`module:api`.

### Inputs

The `PortalStore`, the token and the new password.

### Outputs

None while deferred.

### Observable effect

None.

### Enforces

R0-23, Q19: no password is hashed or changed.

### Errors

`AuthenticationRejected`, before the token or the password is examined.

### State impact

None.

## `public_op:viewer_access.create_viewer`

### Owner

`module:viewer_access`. Create a client viewer with a portal-owned display name.

### Callers

`module:api`.

### Inputs

The `PortalStore`, the administrator's `StaffActorContext` and the display
name.

### Outputs

The new active `ClientViewer` (the route answers its safe view).

### Observable effect

None.

### Enforces

R0-14 (access management), M02: the display name is the portal's, independent
of any Registry customer reference, and the viewer holds no contact data; A13
(`viewer.create` in the same transaction).

### Errors

Access-management failures; a display name the model rejects.

### State impact

Writes one `ClientViewer` and one `AuditRecord`.

## `public_op:viewer_access.revoke_viewer`

### Owner

`module:viewer_access`. Revoke a client viewer for good, with its credentials and sessions.

### Callers

`module:api`.

### Inputs

The `PortalStore`, the administrator's `StaffActorContext` and the
`viewer_id`.

### Outputs

The revoked `ClientViewer`.

### Observable effect

None.

### Enforces

R0-14, A3 (terminal), A11 (`rules.revocation_cascades`: credentials and
sessions revoked in the same transaction), R0-24 (no Registry call), A24,
A13 (`viewer.revoke`).

### Errors

Access-management failures; `ScopedNotFoundError` for an unknown or already
revoked viewer.

### State impact

Updates the viewer, its credentials and sessions; appends one `AuditRecord`.

## `public_op:viewer_access.issue_viewer_access`

### Owner

`module:viewer_access`. Issue a new access code for a viewer, revoking every earlier one.

### Callers

`module:api`.

### Inputs

The `PortalStore`, the administrator's `StaffActorContext` and the
`viewer_id`.

### Outputs

`ViewerCredentialIssue`: the new `ViewerAccessCredential` and the secret in
plaintext, returned once.

### Observable effect

None: the owner passes the code to the client outside the portal.

### Enforces

M02 and A11: every non-revoked prior credential and every live session of the
viewer is revoked in the same transaction — the behaviour the owner's
observation Q13 is about, which stays the owner's; A17 (only the hash is
stored), A13 (`viewer.credential_issue`).

### Errors

Access-management failures; `ScopedNotFoundError` for an unknown or
non-active viewer.

### State impact

Writes one credential, updates the prior credentials and live sessions;
appends one `AuditRecord`.

## `public_op:viewer_access.revoke_viewer_access`

### Owner

`module:viewer_access`. Revoke one viewer access code and the viewer's sessions.

### Callers

`module:api`.

### Inputs

The `PortalStore`, the administrator's `StaffActorContext` and the
`credential_id`.

### Outputs

The revoked `ViewerAccessCredential` (the route answers 204).

### Observable effect

None.

### Enforces

A11, R0-24, A24, A13 (`viewer.credential_revoke`).

### Errors

Access-management failures; `ScopedNotFoundError` for an unknown or already
revoked credential.

### State impact

Updates the credential and every session of its viewer; appends one
`AuditRecord`.

## `public_op:viewer_access.enter_viewer_access`

### Owner

`module:viewer_access`. Exchange a viewer access code for a viewer session.

### Callers

`module:api`, `module:api_irregular`.

### Inputs

The `PortalStore` and the presented access code.

### Outputs

`ViewerSessionGrant`: session id, viewer id, the session token (returned
once, carried only in the cookie of R0-09) and `expires_at`.

### Observable effect

None.

### Enforces

A17: the parsed selector locates the credential and its secret is verified
against the stored hash; the viewer must be active and the credential
usable; the session secret is issued for a fresh `session_id`; expiry is
`config.viewer_session_ttl_days` after one captured time (R0-06).

### Errors

`AuthenticationRejected` for an unknown selector, a wrong secret, a revoked
credential or viewer, without saying which.

### State impact

Writes one `ViewerSession`.

## `public_op:viewer_access.resolve_viewer_session`

### Owner

`module:viewer_access`. Turn a presented viewer session token into the trusted viewer actor context.

### Callers

`module:api`, `module:api_irregular`.

### Inputs

The `PortalStore` and the session token from the viewer cookie.

### Outputs

Exactly one `ViewerActorContext` (session id, viewer id); never `None`.

### Observable effect

None.

### Enforces

A17, A4 `valid_session` and `active_principal`: hash, expiry, revocation,
viewer status and credential usability.

### Errors

`AuthenticationRejected` only for a genuine authentication outcome; a
persistence or programming failure stays visible.

### State impact

Read-only.

## `public_op:viewer_access.describe_viewer_session`

### Owner

`module:viewer_access`. Describe the viewer's current session for a browser that restores it.

### Callers

`module:api`, `module:api_irregular`.

### Inputs

The `PortalStore` and the `ViewerActorContext`.

### Outputs

`ViewerSessionView`: session id, viewer id and `expires_at`; no token or hash.

### Observable effect

None.

### Enforces

R0-09: the session still exists, belongs to the viewer and is neither revoked
nor expired at one captured time; one read transaction closed by one
rollback.

### Errors

`AuthenticationRejected` for any authentication outcome; persistence failures
stay visible.

### State impact

Read-only.

## `public_op:viewer_access.sign_out_viewer`

### Owner

`module:viewer_access`. End the viewer session the browser presents.

### Callers

`module:api`, `module:api_irregular`.

### Inputs

The `PortalStore` and the `ViewerActorContext`.

### Outputs

None (204); the persisted session is not returned.

### Observable effect

None beyond the revocation.

### Enforces

R0-09: only the session the context names, owned by its viewer, is revoked;
the viewer's other sessions stay. A24. `rules.audit_action_catalog` has no
viewer logout action, so none is appended.

### Errors

`AuthenticationRejected` for a missing, revoked or mismatched session; never a
successful sign-out.

### State impact

Updates one `ViewerSession`.

## `public_op:viewer_access.grant_viewer_project`

### Owner

`module:viewer_access`. Let one viewer see one active Registry project.

### Callers

`module:api`.

### Inputs

The `PortalStore`, the administrator's `StaffActorContext`, the `viewer_id`
and the `project_id`.

### Outputs

The new active `ProjectViewerGrant`.

### Observable effect

One Registry validation before the transaction opens.

### Enforces

R0-14, A5 and R0-24 (only an existing active project receives a new grant),
A13 (`grant.create`).

### Errors

Access-management failures; `RegistryBoundaryError` carrying the validation's
failure kind for a project the Registry does not know or does not report
active, and for a failed Registry call; `ScopedNotFoundError` for an unknown
or non-active viewer; `AuthorizationRejected` for an existing active grant.

### State impact

Writes one `ProjectViewerGrant` and one `AuditRecord`.

## `public_op:viewer_access.revoke_viewer_project`

### Owner

`module:viewer_access`. Withdraw one viewer's access to one project.

### Callers

`module:api`.

### Inputs

The `PortalStore`, the administrator's `StaffActorContext` and the
`grant_id`.

### Outputs

The revoked `ProjectViewerGrant`.

### Observable effect

None; the next guard check sees the revocation.

### Enforces

R0-24 (no Registry call), A24, A13 (`grant.revoke`); no other grant changes.

### Errors

Access-management failures; `ScopedNotFoundError` for an unknown or already
revoked grant.

### State impact

Updates one `ProjectViewerGrant`; appends one `AuditRecord`.

## `public_op:viewer_access.list_viewer_project_grants`

### Owner

`module:viewer_access`. List the active project grants of the acting viewer.

### Callers

`module:api`, `module:derived_views`.

### Inputs

The `PortalStore` and the `ViewerActorContext`.

### Outputs

Every active `ProjectViewerGrant` of that viewer and no other; possibly empty.

### Observable effect

None.

### Enforces

A4: the viewer comes from the trusted context, never from request data; no
Registry context is read here.

### Errors

A persistence failure propagates.

### State impact

Read-only.

## `public_op:service_identity.create_service_principal`

### Owner

`module:service_identity`. Register a named producer service principal.

### Callers

`module:api`.

### Inputs

The `PortalStore`, the administrator's `StaffActorContext`, the name, the
`ProducerSourceType` and the `ProducerScopeMode`.

### Outputs

The new active `ServicePrincipal` (the route answers its safe view).

### Observable effect

None.

### Enforces

R0-14, A12 (closed source type and scope mode), A13 (`principal.create`).

### Errors

Access-management failures.

### State impact

Writes one `ServicePrincipal` and one `AuditRecord`.

## `public_op:service_identity.change_service_principal_status`

### Owner

`module:service_identity`. Disable or re-enable one service principal.

### Callers

`module:api`.

### Inputs

The `PortalStore`, the administrator's `StaffActorContext`, the principal id
and the new `PrincipalStatus`.

### Outputs

The `ServicePrincipal` in its new status (the route answers its safe view).

### Observable effect

None.

### Enforces

A3 (`rules.status_transitions`), A11 (`rules.revocation_cascades`), A24, A13
(`principal.disable` or `principal.enable`). A request for the status the
principal already holds changes nothing and appends no audit.

### Errors

Access-management failures; `ScopedNotFoundError` for an unknown principal;
`AuthorizationRejected` for a transition the table does not list.

### State impact

Updates the principal and what its cascade names; appends one `AuditRecord`
per change.

## `public_op:service_identity.issue_service_credential`

### Owner

`module:service_identity`. Issue a new bearer credential for an active service principal.

### Callers

`module:api`.

### Inputs

The `PortalStore`, the administrator's `StaffActorContext`, the principal id
and an optional `expires_at`.

### Outputs

`ServiceCredentialIssue`: the new `ServiceCredential` with the next
`key_version` and the secret in plaintext, returned once.

### Observable effect

None.

### Enforces

A12, A17 (secret issued for the fresh `credential_id`; only the hash
stored); earlier credentials stay valid until revoked; A13
(`principal.credential_issue` with the key version).

### Errors

Access-management failures; `ScopedNotFoundError` for an unknown principal;
`AuthorizationRejected` for a non-active one, with nothing generated.

### State impact

Writes one `ServiceCredential` and one `AuditRecord`.

## `public_op:service_identity.revoke_service_credential`

### Owner

`module:service_identity`. Revoke one service credential, leaving the principal's other credentials.

### Callers

`module:api`.

### Inputs

The `PortalStore`, the administrator's `StaffActorContext` and the
`credential_id`.

### Outputs

The revoked `ServiceCredential` (the route answers 204).

### Observable effect

None.

### Enforces

A11, A24, A13 (`principal.credential_revoke` with the key version).

### Errors

Access-management failures; `ScopedNotFoundError` for an unknown or already
revoked credential, indistinguishably.

### State impact

Updates one `ServiceCredential`; appends one `AuditRecord`.

## `public_op:service_identity.grant_producer_project`

### Owner

`module:service_identity`. Let one service principal publish for one active Registry project.

### Callers

`module:api`.

### Inputs

The `PortalStore`, the administrator's `StaffActorContext`, the principal id
and the `project_id`.

### Outputs

The new active `ProducerProjectGrant`.

### Observable effect

One Registry validation before the transaction opens.

### Enforces

R0-14, A12, A5 and R0-24, A13 (`producer_grant.create` with the project).

### Errors

Access-management failures; `ScopedNotFoundError` for a project the Registry
does not know or an unknown principal; `ArchivedProjectRejected` for an
inactive project; `AuthorizationRejected` for an existing active grant;
`RegistryBoundaryError`.

### State impact

Writes one `ProducerProjectGrant` and one `AuditRecord`.

## `public_op:service_identity.revoke_producer_project`

### Owner

`module:service_identity`. Withdraw one producer grant.

### Callers

`module:api`.

### Inputs

The `PortalStore`, the administrator's `StaffActorContext` and the
`grant_id`.

### Outputs

The revoked `ProducerProjectGrant`.

### Observable effect

None.

### Enforces

R0-24 (no Registry call), A24, A13 (`producer_grant.revoke` with the
project); only an active, unrevoked grant is revocable.

### Errors

Access-management failures; `ScopedNotFoundError` for an unknown or
non-revocable grant, indistinguishably.

### State impact

Updates one `ProducerProjectGrant`; appends one `AuditRecord`.

## `public_op:service_identity.authenticate_service_principal`

### Owner

`module:service_identity`. Turn a presented producer bearer credential into the trusted service actor context.

### Callers

`module:api`.

### Inputs

The `PortalStore` and the bearer secret.

### Outputs

`ServiceActorContext`: principal id, source type, scope mode and key version
from persistence.

### Observable effect

None.

### Enforces

R0-09 (bearer only), A17 (parsed before any transaction opens; the secret
part verified), A28 for usability: the credential is not revoked or expired
and its principal is active.

### Errors

`AuthenticationRejected` for every authentication outcome, a malformed
envelope included, revealing no selector state.

### State impact

Read-only.

## `public_op:service_identity.authorize_producer_scope`

### Owner

`module:service_identity`. Decide whether a service principal's scope covers one project.

### Callers

`module:api`.

### Inputs

The `PortalStore`, the `ServiceActorContext` and the `project_id`.

### Outputs

The decision of `rules.producer_scope_policy`: for an all-projects scope,
whether the Registry reports the project active; for a granted-projects
scope, whether an active unrevoked grant exists for this principal and
project.

### Observable effect

One Registry validation for an all-projects scope.

### Enforces

A12; the scope comes from the trusted context and persisted grants only.

### Errors

Never answers false by swallowing a failure: persistence and
`RegistryBoundaryError` propagate unchanged.

### State impact

Read-only.
