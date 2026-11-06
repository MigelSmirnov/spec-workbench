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
