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
  A28, taken when the change is made; an audit record's `occurred_at` is
  taken by `audit_writer.append_audit` when it appends (A28).
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
  zero, except in the two reads whose Errors say so:
  `derived_views.build_project_overview` turns a part's failure into that
  part's availability, and `derived_views.list_viewer_projects` leaves out a
  project whose Registry context fails.
- **Concealment.** An unknown, revoked or expired credential or session and a
  non-active principal are one `AuthenticationRejected`; an inaccessible
  project or record is `ScopedNotFoundError` or `AuthorizationRejected` as the
  operation says, never a disclosure of what exists (A4, A11).
- **Archived projects.** Reads of an archived project succeed; every mutation
  of its records and every new staff assignment for it is
  `ArchivedProjectRejected`; a new viewer grant for it is refused with the
  `RegistryBoundaryError` its operation names; revocation consults no
  Registry (R0-24). The one write that is not refused for an archived project
  is the empty manual budget version (with its audit) that
  `ensure_manual_budget` creates, also when `list_project_progress` reads a
  project that has none.
- **Order.** Every list A15 or A27 names (the project lists and the derived
  views) is in the order they give; any other list is in the order its
  operation's Outputs state.

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

The amount quantized to two digits, ROUND_HALF_UP. An amount with more
fraction digits is rounded, never refused, and the sign rule is applied to
the rounded amount.

### Observable effect

None.

### Enforces

A9 and `rules.money_policy`: EUR only, no conversion, the sign rule the caller
names. Only finite amounts are amounts: the request models refuse a
non-finite value before any operation is called, and a non-finite value
passed directly is no declared refusal but an unclassified failure (500
under the conventions).

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
reported percent, rounded to two fraction digits as money is (A9), or `None`
when that denominator is zero.

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
`rules.audit_result_reason_policy`), A23 (`entity_id`), A21 (append-only),
A28 (`occurred_at` from its own clock read at append, not the caller's
instant): exactly one insert; a service actor keeps its `key_version`; no secret or
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
`RegistryBoundaryError`. A Registry answer whose project status is neither
`active` nor `archived` is an invalid Registry answer: no context is built
and the read ends as an unclassified failure, 500 under the conventions,
never a success or a not-found.

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
`AuthorizationRejected` without the capability; `RegistryBoundaryError`. A
project status other than `active` or `archived` ends the read as for staff
reads: an unclassified failure, 500 under the conventions.

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
active grant for the project. The authorization check of an import request
starts with the authentication of its bearer credential
(`service_identity.authenticate_service_principal`) and ends with this
guard; the credential's revocation and expiry are observed in that first
step (A11), so any request authenticated after a revocation is refused; a
revocation committed after this request's authentication is observed from
the next request on. This guard then re-reads the principal and the grant.

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
`config.staff_session_ttl_hours`, twelve hours), A13: once the address has
normalized, exactly one audit on every outcome — `staff.login` success or
`staff.login_failed` rejected with no reason code. A rejection audit names the
account the normalized address matched as both actor and entity, also when
the account is not active, not verified or the password is wrong; actor and
entity are empty only when no account matched, and the actor kind is staff
in every case. Only an active, verified
account with a matching password signs in.

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
the one `revoked_at` the operation captured, also when none was live. The
target id is not checked against the staff accounts: an id no account has
succeeds with zero sessions revoked and is audited like any other.

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
`staff.suspend` for suspension, `staff.disable` for disabling, and
`staff.reinstate` for every change to `active`, the activation of a
`pending_verification` account included.

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

The `PortalStore`, the administrator's `StaffActorContext`, the target
account's `staff_id` and the `project_id`. Any existing staff account is
accepted as the target, an administrator included; such an assignment is
stored and audited but changes no administrator's access.

### Outputs

The new active `StaffProjectAssignment`.

### Observable effect

One Registry validation before the transaction opens.

### Enforces

R0-14, A5 and R0-24 (no new access to an unknown or archived project), A13
(`staff_assignment.create` with the project).

### Errors

Access-management failures; `ScopedNotFoundError` for a project the Registry
does not know or an unknown staff account; `ArchivedProjectRejected` for an
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

R0-14 (access management), M01: the display name is the portal's, independent
of any Registry customer reference, and the viewer holds no email, profile or
Registry customer data; A13
(`viewer.create` in the same transaction).

### Errors

Access-management failures only: any text, the empty one included, is
accepted as the display name.

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
principal already holds is no transition, so A3's refusal of unlisted
transitions does not apply to it: the operation returns the principal
unchanged, writes nothing and appends no audit.

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
and an optional `expires_at`. Any expiry is accepted and stored as
supplied, a past one included, never converted (A28 keeps a supplied time); no expiry means the credential does not expire. A
credential is usable only before its expiry, so one issued with an expiry
already reached is stored but never authenticates.

### Outputs

`ServiceCredentialIssue`: the new `ServiceCredential` with the next
`key_version` and the secret in plaintext, returned once. Of two
concurrent issuances for one principal that pick the same key version, the
uniqueness of (`service_principal_id`, `key_version`) lets one commit; the
other fails as a persistence failure and writes nothing.

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

A yes-or-no answer, the decision of `rules.producer_scope_policy`: for an
all-projects scope, yes exactly when the Registry reports the project
active; for a granted-projects scope, yes exactly when an active unrevoked
grant exists for this principal and project. A project the scope does not
cover is the answer no, not an exception. The import route that calls it
does not act on the answer: the refusal comes from
`authorization_guard.authorize_snapshot_import`, called next.

### Observable effect

One Registry validation for an all-projects scope.

### Enforces

A12; the scope comes from the trusted context and persisted grants only.

### Errors

Never answers false by swallowing a failure: persistence and
`RegistryBoundaryError` propagate unchanged.

### State impact

Read-only.

## `public_op:snapshot_import.import_snapshot`

### Owner

`module:snapshot_import`. Classify and record one estimate-snapshot publication from a producer.

### Callers

`module:api`.

### Inputs

The `PortalStore`, the `ServiceActorContext` and one `SnapshotPublication`.

### Outputs

The fresh `SnapshotImportRecord` of this attempt, with its portal-assigned
`import_id` and `ImportOutcome`: `accepted`, `idempotent_replay`,
`integrity_conflict` or `rejected` with an `ImportRejectReason`.

### Observable effect

None beyond the records; the import never touches budgets, sections or plans
(A18: a snapshot becomes a candidate only by activation, and Q11 stays
deferred).

### Enforces

R0-04 and R0-25: it is reached only after the route's own
`authorize_producer_scope` and `authorize_snapshot_import` passed, so an
access refusal never reaches it and is recorded nowhere (Q20). One
fingerprint and one `occurred_at` per attempt; every classified attempt — a
content rejection (A7 contract version, A9 currency, completeness,
sections), acceptance, equal replay, differing replay, or an archived,
unknown or scope-denied project from its repeated `authorize_snapshot_import`
(called once before the transaction; only if access changed after the
route's check) — appends exactly one fresh record and one `snapshot.import`
audit in one transaction. A new
acceptance inserts one `ApprovedEstimateSnapshot` before its record; an equal
replay references the existing snapshot (A8, A21). Rejection reasons come from
the exception's field, never its message (A26).

### Errors

`AuthenticationRejected` and infrastructure failures outside the catalogue
re-raise with nothing written; every business rejection is an answered
record, not an exception.

### State impact

Appends one `SnapshotImportRecord`, at most one `ApprovedEstimateSnapshot`
and one `AuditRecord`, together or not at all.

## `public_op:snapshot_import.get_snapshot_import_result`

### Owner

`module:snapshot_import`. Return one of the acting producer's own import results.

### Callers

`module:api`.

### Inputs

The `PortalStore`, the `ServiceActorContext` and the `import_id`.

### Outputs

Exactly the immutable `SnapshotImportRecord` of that `import_id`.

### Observable effect

None.

### Enforces

R0-21: the record's `service_principal_id` must be the actor's; the producer
grant and the Registry are not re-checked.

### Errors

`ScopedNotFoundError` for an unknown id or another principal's record,
indistinguishably.

### State impact

Read-only.

## `public_op:budget_management.ensure_manual_budget`

### Owner

`module:budget_management`. Return the project's one manual budget version, creating it empty when absent.

### Callers

`module:api`, `module:project_tracking`.

### Inputs

The `PortalStore` and an `AuthorizedProjectContext`.

### Outputs

`BudgetVersionDetail`: the manual `BudgetVersion`, its plans by
`sort_order` then `section_id`, and the count of section allocations whose
section has no plan in this manual version; zero when this call creates the
version. Whether another version is active does not change the count.

### Observable effect

None.

### Enforces

A18: at most one manual version per project; a new one is `inactive` and is
never activated implicitly; A13 (`budget.manual_version_create` only when it
is created).

### Errors

A persistence failure propagates.

### State impact

Writes one `BudgetVersion` and one `AuditRecord` when none exists; otherwise
read-only.

## `public_op:budget_management.upsert_manual_section_plan`

### Owner

`module:budget_management`. Create or edit one section plan of the manual budget.

### Callers

`module:api`.

### Inputs

The `PortalStore`, an `AuthorizedProjectContext`, an optional `section_id`,
the display name, the sort order and the planned material and work amounts.
Any text is accepted as the display name, the empty one included, and any
whole number as the sort order; neither is refused.

### Outputs

The `BudgetVersionDetail` of the manual version after the change.

### Observable effect

None.

### Enforces

A9 (both amounts validated before the transaction), A18 (stable
`PortalSection` identity; imported plans never change; a missing manual
version is created as `ensure_manual_budget` does), R0-24 (active project
only), A13 (`budget.section_plan_edit`, and `budget.manual_version_create`
when created). An existing plan of the section keeps its `plan_id`.

### Errors

`FinancialValidationError` for an amount; `BudgetValidationError` for an
inactive project or a `section_id` not in this project, with nothing written.

### State impact

Writes or updates the manual version, a new `PortalSection` when
`section_id` is absent, one `SectionPlan`, and their audits, in one
transaction.

## `public_op:budget_management.get_budget_version`

### Owner

`module:budget_management`. Return one budget version of the project with its plans.

### Callers

`module:api`.

### Inputs

The `PortalStore`, an `AuthorizedProjectContext` and the `version_id`.

### Outputs

`BudgetVersionDetail` for exactly that version: plans by `sort_order` then
`section_id` and the count of section allocations whose section has no plan
in that version, active or not.

### Observable effect

None.

### Enforces

A18, A4 (project-scoped read).

### Errors

`ScopedNotFoundError` for a version of no or another project.

### State impact

Read-only.

## `public_op:budget_management.activate_budget_version`

### Owner

`module:budget_management`. Make one budget version of the project the active one.

### Callers

`module:api`.

### Inputs

The `PortalStore`, an `AuthorizedProjectContext` carrying the activate
capability, and the `version_id`.

### Outputs

`BudgetActivationResult`: the activated version, its ordered plans and the
count of section allocations whose section has no plan in the requested
version (zero, since a positive count refuses).

### Observable effect

None.

### Enforces

A18 and A1: only `portal.estimate_snapshot.activate`, never a producer; the
prior active version becomes `inactive` and the requested one `active` at one
captured time in one transaction; A13 (`snapshot.activate`). Activation is
refused while any section allocation of the project names a section the
requested version has no plan for. Activating the version that is already
active is no status transition (its status stays `active`) and is not
refused: it records a new activation time and actor for it, deactivates
nothing and is audited like any activation.

### Errors

`BudgetValidationError` for another capability, before any transaction;
`ScopedNotFoundError` for a version of no or another project;
`BudgetConflictError` while allocations would lose their section, with
nothing changed.

### State impact

Updates two `BudgetVersion` rows at most; appends one `AuditRecord`.

## `public_op:budget_management.validate_project_section`

### Owner

`module:budget_management`. Confirm that a section id belongs to a project.

### Callers

`module:api`, `module:project_tracking`.

### Inputs

The `PortalStore`, a `project_id` and a `section_id`.

### Outputs

The `PortalSection` of that project.

### Observable effect

None.

### Enforces

A18 stable section identity; another project's section is never disclosed.

### Errors

`BudgetValidationError` for a missing or cross-project section.

### State impact

Read-only.

## `public_op:expense_intake.create_expense_from_recognition`

### Owner

`module:expense_intake`. Create one expense with its document and allocations from a confirmed OCR recognition.

### Callers

`module:api`.

### Inputs

The `PortalStore`, an `AuthorizedProjectContext`, one
`ConfirmedRecognitionPublication` and the operator's `AllocationInstruction`
list.

### Outputs

`ExpenseOperationOutcome`: the `ExpenseAggregate` and whether it was a
replay (the route answers its safe projection).

### Observable effect

None.

### Enforces

R0-05 and R0-17 (expenses only from confirmed OCR intake, decided by the
authenticated operator), A7 (`rules.supported_external_contract_versions.ocr`),
A9, A19 (allocations sum exactly to the total, sections of this project),
A8 (replay by `recognized_document_id`: an equal fingerprint returns the
existing aggregate with no audit), R0-18 (the new document is client-visible),
A13 (`expense.create`).

### Errors

`ExpenseValidationError` or `FinancialValidationError` for unsupported or
incomplete input, a currency or an allocation mismatch;
`ExpenseConflictError` for a replay with a different fingerprint.

### State impact

Writes one `Expense`, one `ExpenseDocument`, its `ExpenseAllocation` rows and
one `AuditRecord`; a replay writes nothing.

## `public_op:expense_management.correct_expense`

### Owner

`module:expense_management`. Correct an expense's facts and replace all its allocations.

### Callers

`module:api`.

### Inputs

The `PortalStore`, an `AuthorizedProjectContext`, the `expense_id`, the
supplier, the document date, the total, the inclusion flag and the complete
`AllocationInstruction` list.

### Outputs

`ExpenseOperationOutcome` with the corrected aggregate, not a replay.

### Observable effect

None.

### Enforces

A9 (the total in EUR, non-negative), A19 (every section target of this
project, exact sum), A24, A13 (`expense.correct`); no intermediate state
commits. The allocation list must hold at least one instruction whatever
the total; an empty list is refused, a zero total included.

### Errors

`ExpenseConflictError` for an expense of no or another project;
`ExpenseValidationError` for an empty allocation list, a section target or
a sum; `FinancialValidationError` for the total.

### State impact

Updates the `Expense` and replaces its allocations; appends one
`AuditRecord`.

## `public_op:expense_management.set_expense_inclusion`

### Owner

`module:expense_management`. Include an expense in, or exclude it from, the project totals.

### Callers

`module:api`.

### Inputs

The `PortalStore`, an `AuthorizedProjectContext`, the `expense_id` and the
inclusion flag.

### Outputs

`ExpenseOperationOutcome` with the updated aggregate, not a replay.

### Observable effect

None.

### Enforces

A19: an excluded expense is kept, never deleted; only `included`,
`updated_at` and `updated_by` change; A13 (`expense.include` for the flag
set, `expense.exclude` for it cleared). A request for the flag the expense
already has is not a no-op and not refused: it is applied like any change,
with a new `updated_at` and the audit of the requested value.

### Errors

`ExpenseConflictError` for an expense of no or another project.

### State impact

Updates one `Expense`; appends one `AuditRecord`.

## `public_op:expense_management.replace_expense_allocations`

### Owner

`module:expense_management`. Replace all allocations of an expense with the operator's instructions.

### Callers

`module:api`.

### Inputs

The `PortalStore`, an `AuthorizedProjectContext`, the `expense_id` and the
`AllocationInstruction` list.

### Outputs

`ExpenseOperationOutcome` with the updated aggregate, not a replay.

### Observable effect

None.

### Enforces

A19: the sum equals the unchanged total; every section target belongs to this
project; A13 (`expense.allocate`).

### Errors

`ExpenseConflictError` for an expense of no or another project;
`ExpenseValidationError` for an empty list, a mismatched sum or a section
target outside the project.

### State impact

Replaces the expense's allocations; appends one `AuditRecord`.

## `public_op:expense_management.update_expense_document`

### Owner

`module:expense_management`. Change the description and client visibility of an expense document.

### Callers

`module:api`.

### Inputs

The `PortalStore`, an `AuthorizedProjectContext`, the `document_id`, an
optional description and the client-visibility flag.

### Outputs

The updated `ExpenseDocument` (the route answers its safe projection).

### Observable effect

None.

### Enforces

A14 and R0-13: metadata only, `file_ref` unchanged; A13 (`document.update`
with the document's own id). A request equal to the stored description and
visibility is not a no-op: it is applied like any update, with a new
`updated_at`, the caller as `updated_by` and its audit.

### Errors

`ExpenseConflictError` for a document of no or another project.

### State impact

Updates one `ExpenseDocument`; appends one `AuditRecord`.

## `public_op:expense_management.read_expense_document`

### Owner

`module:expense_management`. Return the exact bytes of an expense document to a reader allowed to see it.

### Callers

`module:api`, `module:api_irregular`.

### Inputs

The `PortalStore`, an `AuthorizedProjectContext` and the `document_id`.

### Outputs

`BinaryPayload` of the document (staff answer as attachment; the viewer
route by its own projection).

### Observable effect

None.

### Enforces

A14 and R0-12: the document and its expense belong to the context's project
and, for a viewer, the document is client-visible; only then is an
`AuthorizedBinaryReference` built and `binary_storage.read_binary` called,
with no transaction open.

### Errors

`BinaryAccessRejected` for a missing record, another project's or an
invisible one, and an unreadable object alike.

### State impact

Read-only.

## `public_op:project_tracking.set_section_progress`

### Owner

`module:project_tracking`. Record the manual completion percent of one section.

### Callers

`module:api`.

### Inputs

The `PortalStore`, an `AuthorizedProjectContext`, the `section_id` and the
completion percent.

### Outputs

The upserted `SectionProgress`.

### Observable effect

None.

### Enforces

A20: an integer 0–100, never clamped, set by staff and never by photographs;
the section is this project's (`budget_management.validate_project_section`,
before the transaction); A13 (`progress.update`).

### Errors

`TrackingValidationError` for a percent out of range or not an integer;
`BudgetValidationError` for a section outside the project.

### State impact

Upserts one `SectionProgress`; appends one `AuditRecord`.

## `public_op:project_tracking.register_work_payment`

### Owner

`module:project_tracking`. Register one payment for work, idempotently by its payment id.

### Callers

`module:api`.

### Inputs

The `PortalStore`, an `AuthorizedProjectContext`, the `payment_id`, the
amount, the payment date and the description.

### Outputs

The `WorkPayment`, new or the existing equal one.

### Observable effect

None: no invoice or accounting posting is created.

### Enforces

A9 (positive EUR, the validated amount stored and compared), A8
(`rules.idempotency_identities`: an equal replay returns the existing payment
with no audit), A13 (`payment.register`).

### Errors

`FinancialValidationError` for the amount; `TrackingConflictError` for a
replay of the id with other content or of another project, changing nothing.

### State impact

Writes one `WorkPayment` and one `AuditRecord` when new.

## `public_op:project_tracking.list_project_progress`

### Owner

`module:project_tracking`. List the project's recorded section progress in plan order.

### Callers

`module:api`.

### Inputs

The `PortalStore` and an `AuthorizedProjectContext`.

### Outputs

Every `SectionProgress` of the project, by the manual budget's plan
`sort_order`, `section_id` breaking ties, the progress of a section without
a manual plan after all others; empty when none is recorded.

### Observable effect

None.

### Enforces

The tracking read transaction closes before
`budget_management.ensure_manual_budget` is called for the order.

### Errors

A persistence failure propagates.

### State impact

Not a pure read: when the project has no manual budget version, this list
creates it empty with its `budget.manual_version_create` audit, exactly as
`ensure_manual_budget` does, an archived project included; otherwise
read-only.

## `public_op:project_tracking.list_project_payments`

### Owner

`module:project_tracking`. List the project's payments, newest first.

### Callers

`module:api`.

### Inputs

The `PortalStore` and an `AuthorizedProjectContext`.

### Outputs

Every `WorkPayment` of the project by `payment_date` then `payment_id`,
descending; empty when none. This staff record list does not use the
recording time; the A27 order with recording time is that of the derived
payment view (`derived_views.build_payment_view`).

### Observable effect

None.

### Enforces

A4 (project-scoped read).

### Errors

A persistence failure propagates.

### State impact

Read-only.

## `public_op:photo_management.publish_progress_photo`

### Owner

`module:photo_management`. Publish one progress photo, idempotently by its intake id.

### Callers

`module:api`.

### Inputs

The `PortalStore`, an `AuthorizedProjectContext` and one `PhotoPublication`.

### Outputs

`PhotoMutationResult`: photo id, whether it was a replay, client visibility
and `updated_at`; no `file_ref`.

### Observable effect

None: the binary already exists under the root (R0-13).

### Enforces

A8 (`rules.idempotency_identities.progress_photo`: `intake_id` is the one
replay identity; a fresh `photo_id`), A20 (no progress or financial value is
set), the optional section is this project's, A13 (`photo.publish`).

### Errors

`PhotoValidationError` for a publication of another project or a section
outside it; `PhotoConflictError` for a replay that differs or belongs to
another project.

### State impact

Writes one `ProgressPhoto` and one `AuditRecord` when new.

## `public_op:photo_management.update_progress_photo`

### Owner

`module:photo_management`. Change a photo's caption, section and client visibility.

### Callers

`module:api`.

### Inputs

The `PortalStore`, an `AuthorizedProjectContext`, the `photo_id`, an optional
caption, an optional `section_id` and the client-visibility flag.

### Outputs

`PhotoMutationResult` of the updated photo, not a replay.

### Observable effect

None.

### Enforces

A20 and A14: never `file_ref`, progress or finance; A24 (a replacement
photo); A13 (`photo.update`). Caption, section and visibility are all
replaced by the request, an absent caption or section clearing it. A request
equal to the stored values is not a no-op: it is applied like any update,
with a new `updated_at`, the caller as `updated_by` and its audit.

### Errors

`PhotoValidationError` for a photo of no or another project or a section
outside the project.

### State impact

Updates one `ProgressPhoto`; appends one `AuditRecord`.

## `public_op:photo_management.list_progress_photos`

### Owner

`module:photo_management`. List the project's photos a reader may see.

### Callers

`module:api`.

### Inputs

The `PortalStore` and an `AuthorizedProjectContext`.

### Outputs

`ProgressPhotoView` list by `photo_date` then `photo_id`, ascending; for a
viewer only client-visible photos; never `file_ref` or `intake_id`; empty
when none. This list does not use the publication time; the A27 order with
publication time is that of the overview's photo part
(`derived_views.build_project_overview`).

### Observable effect

None.

### Enforces

A14.

### Errors

A persistence failure propagates.

### State impact

Read-only.

## `public_op:photo_management.read_progress_photo`

### Owner

`module:photo_management`. Return the exact bytes of a progress photo to a reader allowed to see it.

### Callers

`module:api`, `module:api_irregular`.

### Inputs

The `PortalStore`, an `AuthorizedProjectContext` and the `photo_id`.

### Outputs

`BinaryPayload` of the photo (answered inline).

### Observable effect

None.

### Enforces

A14 and R0-12: the photo belongs to the context's project and, for a viewer,
is client-visible; the read transaction closes before
`binary_storage.read_binary` is called.

### Errors

`PhotoValidationError` for a missing, another project's or an invisible
photo; `BinaryStorageError` for an unreadable object. Unlike documents, the
accepted service does not fold these into one answer.

### State impact

Read-only.

## `public_op:derived_views.list_viewer_projects`

### Owner

`module:derived_views`. List the projects the acting viewer can open, with live Registry names.

### Callers

`module:api`, `module:api_irregular`.

### Inputs

The `PortalStore` and the `ViewerActorContext`.

### Outputs

`ProjectListItem` list (project, display name, address, Registry status,
grant) in the A15 order (`rules.project_list_ordering.viewer`: display name
case-folded, then `project_id`); empty when none.

### Observable effect

One Registry context request per active grant.

### Enforces

A15 and Factory `00ac72f18d9c`: a grant whose context cannot be read is left
out, each grant independently, instead of failing the list.

### Errors

A persistence failure propagates; Registry failures only omit items.

### State impact

Read-only.

## `public_op:derived_views.build_project_overview`

### Owner

`module:derived_views`. Build the one-page overview of a project with an availability for each part.

### Callers

`module:api`, `module:api_irregular`.

### Inputs

The `PortalStore` and an `AuthorizedProjectContext`.

### Outputs

`ProjectOverview`: six pairs — project, budget, expenses, progress, payments,
photos — each a `ViewAvailability` and a value present only when available.

### Observable effect

One Registry context request.

### Enforces

A21 (derived at read time, nothing persisted), A27 and Factory
`d2c4511ea119`: a part whose builder answers `ScopedNotFoundError` is
`not_configured`, a persistence or Registry failure `temporarily_unavailable`;
no zero is fabricated; the photo part holds client-visible photos only, for
every reader.

### Errors

The project part turns a `RegistryBoundaryError` into
`temporarily_unavailable`; any other failure of the Registry context request
propagates. Each portal part (budget, expenses, progress, payments, photos)
turns `ScopedNotFoundError` into `not_configured` and every other failure of
its builder, an unexpected one included, into `temporarily_unavailable`, so
the overview itself then still succeeds.

### State impact

Read-only.

## `public_op:derived_views.build_budget_view`

### Owner

`module:derived_views`. Derive the budget view of the active or a named version.

### Callers

`module:api`.

### Inputs

The `PortalStore`, an `AuthorizedProjectContext` and an optional
`version_id`.

### Outputs

`BudgetView`: the version, sections, planned and actual material, planned and
completed work, other expenses and the count of section allocations whose
section has no plan in the viewed version. Everything is computed against
the viewed version: the named one when `version_id` is given, active or not,
otherwise the active one; no other version is consulted. A section row of
the view never carries an unresolved mark, since its section has a plan.

### Observable effect

None.

### Enforces

A9, A19, A21: totals use included expenses only; the integrity count counts
every expense, included or not; nothing is persisted.

### Errors

`ScopedNotFoundError` when no active version exists or the named one is not
this project's.

### State impact

Read-only.

## `public_op:derived_views.build_expense_view`

### Owner

`module:derived_views`. Derive the expense summary of a project.

### Callers

`module:api`.

### Inputs

The `PortalStore` and an `AuthorizedProjectContext`.

### Outputs

`ExpenseSummaryView`: every confirmed expense, excluded ones visible,
included, excluded and other totals; no `file_ref`.

### Observable effect

None.

### Enforces

A19, A21, A27 (`rules.derived_view_ordering` for expenses and allocations).

### Errors

A persistence failure propagates.

### State impact

Read-only.

## `public_op:derived_views.build_progress_view`

### Owner

`module:derived_views`. Derive the progress view of the active budget's sections.

### Callers

`module:api`.

### Inputs

The `PortalStore` and an `AuthorizedProjectContext`.

### Outputs

`ProgressView`: sections with their percent (absent when none is recorded),
completed work per section and in total, and the weighted overall percent or
`None`.

### Observable effect

None.

### Enforces

A9 and A20 through `financial_policy`; an absent measurement is never zero.

### Errors

`ScopedNotFoundError` when the project has no active version.

### State impact

Read-only.

## `public_op:derived_views.build_payment_view`

### Owner

`module:derived_views`. Derive the payment summary and work balance of a project.

### Callers

`module:api`.

### Inputs

The `PortalStore` and an `AuthorizedProjectContext`.

### Outputs

`PaymentSummaryView`: payments in A27 order, their total and the
`WorkBalanceResult` against completed work.

### Observable effect

None.

### Enforces

A9, A21, A27.

### Errors

`ScopedNotFoundError` when the project has no active version.

### State impact

Read-only.

## `public_op:api_irregular.viewer_enter_endpoint`

### Owner

`module:api_irregular`. Answer `POST /auth/viewer/enter`: exchange a viewer access code for the viewer session cookie.

### Callers

`boundary:viewer_browser`.

### Inputs

The request and response, and the JSON body `ViewerEnterRequest` whose
`capability_secret` is the only credential input, passed untrimmed.

### Outputs

`ViewerSessionView` (200); the session token travels only in the cookie.

### Observable effect

Sets the host-only cookie `__Host-portal_viewer_session` (Secure, HttpOnly,
SameSite=strict, Path=/, no Domain) of `rules.viewer_cookie_transport_backend`.

### Enforces

R0-09 and A25 (`rules.http_transport_policy.browser_session`): the secret
never appears in a URL, query, redirect, id, metric, trace or log; the
transport guard has already applied the entry rate limit; delegates to
`viewer_access.enter_viewer_access` with the one `PortalStore` of
`app.state.portal_store`.

### Errors

`AuthenticationRejected` (401); unknown body fields are rejected by the
request model (422).

### State impact

Through `viewer_access`: one `ViewerSession`.

## `public_op:api_irregular.viewer_restore_session_endpoint`

### Owner

`module:api_irregular`. Answer `GET /auth/viewer/session`: describe the session the browser's cookie carries.

### Callers

`boundary:viewer_browser`.

### Inputs

The request, read only for the viewer cookie.

### Outputs

The secret-free `ViewerSessionView` of `viewer_access.describe_viewer_session`,
unchanged.

### Observable effect

None; `no-store` is the transport guard's (A25).

### Enforces

R0-09: the cookie is the only viewer credential; a bearer header is not one.

### Errors

`AuthenticationRejected` (401).

### State impact

Read-only.

## `public_op:api_irregular.viewer_logout_endpoint`

### Owner

`module:api_irregular`. Answer `POST /auth/viewer/logout`: end the cookie's session and clear the cookie.

### Callers

`boundary:viewer_browser`.

### Inputs

The request (viewer cookie) and the response.

### Outputs

None (204), only after the server-side revocation committed.

### Observable effect

Clears the viewer cookie with exactly the attributes it was issued with.

### Enforces

R0-09, A25 (the guard has checked the request origin against the public
origin); delegates to `viewer_access.sign_out_viewer` before clearing.

### Errors

`AuthenticationRejected` (401); a failure never reports a successful logout.

### State impact

Through `viewer_access`: one revoked `ViewerSession`.

## `public_op:api_irregular.list_viewer_projects_endpoint`

### Owner

`module:api_irregular`. Answer `GET /viewer/projects`: the projects the viewer can open.

### Callers

`boundary:viewer_browser`.

### Inputs

The request, read only for the viewer cookie.

### Outputs

The `ProjectListItem` list of `derived_views.list_viewer_projects`.

### Observable effect

None.

### Enforces

R0-09; no viewer id, grant, sort or Registry fact is taken from the request.

### Errors

`AuthenticationRejected` (401).

### State impact

Read-only.

## `public_op:api_irregular.viewer_project_overview_endpoint`

### Owner

`module:api_irregular`. Answer `GET /viewer/projects/{project_id}`: the overview of one granted project.

### Callers

`boundary:viewer_browser`.

### Inputs

The request (viewer cookie) and the path `project_id`.

### Outputs

The `ProjectOverview` of `derived_views.build_project_overview`.

### Observable effect

None.

### Enforces

R0-09, A4: resolves the session, then
`authorization_guard.authorize_viewer_project_read`; archived projects stay
readable and visibility is unchanged.

### Errors

401, 403, 404 and 502 as the guard decides.

### State impact

Read-only.

## `public_op:api_irregular.viewer_read_expense_document_endpoint`

### Owner

`module:api_irregular`. Answer `GET /viewer/projects/{project_id}/expense-documents/{document_id}/content`: a client-visible document's bytes.

### Callers

`boundary:viewer_browser`.

### Inputs

The request (viewer cookie), the path `project_id` and `document_id`.

### Outputs

The exact bytes of `expense_management.read_expense_document` with the
attachment disposition `rules.binary_delivery_policy` assigns to a document;
no JSON envelope, base64, redirect or storage location.

### Observable effect

None.

### Enforces

R0-09, R0-12, A14: viewer read authorization first; a failure is
indistinguishable from an unknown, cross-project or invisible document.

### Errors

401 or the guard's answers; `BinaryAccessRejected` (404).

### State impact

Read-only.

## `public_op:api_irregular.viewer_read_progress_photo_endpoint`

### Owner

`module:api_irregular`. Answer `GET /viewer/projects/{project_id}/photos/{photo_id}/content`: a client-visible photo's bytes.

### Callers

`boundary:viewer_browser`.

### Inputs

The request (viewer cookie), the path `project_id` and `photo_id`.

### Outputs

The exact bytes of `photo_management.read_progress_photo` with the inline
disposition `rules.binary_delivery_policy` assigns to a photo.

### Observable effect

None.

### Enforces

R0-09, R0-12, A14: viewer read authorization first; no `file_ref` leaves.

### Errors

401 or the guard's answers; the photo read's own failures
(`PhotoValidationError` 422, `BinaryStorageError` 500).

### State impact

Read-only.

## `public_op:api.create_app`

### Owner

`module:api`. Build the inner HTTP application from the route table around one store.

### Callers

`module:runtime`.

### Inputs

The one `PortalStore`.

### Outputs

The FastAPI application, with the store only as `app.state.portal_store`.

### Observable effect

None: no transaction is opened.

### Enforces

`rules.http_router_backend`: every route row bound exactly once — staff,
administrator and producer bearer routes by the table, the seven viewer-cookie
routes by `api_irregular` — binary rows answered as plain responses, and one
exception handler per `error_policy` mapping available to the module, any
other failure the policy default (500). A route handler extracts the
credential and the declared body, runs the route's `authorize` steps, calls
exactly one owning operation and returns its result or a safe projection;
it decides, retries and audits nothing.

### Errors

None at build time beyond a defect in the route table.

### State impact

None.

## `public_op:transport_guard.install_transport_guards`

### Owner

`module:transport_guard`. Install the one HTTP middleware that applies the transport policy before any route.

### Callers

`module:runtime`.

### Inputs

The application and the `RuntimeSettings`.

### Outputs

None: the middleware is registered on the application.

### Observable effect

For every request, in order: a request id with no identity in it; 400 for an
untrusted host; CORS preflight 204 for a listed origin and 403 for another;
403 for a viewer logout from another origin than the public one; 413 for a
body over `max_request_body_bytes`; 429 for viewer entries over the
monotonic-clock rate limit, before any credential is parsed; then the route,
called once. Every answer carries the security headers, `no-store` where the
policy names it, CORS headers only for a listed origin, and in production one
redacted log line. The origin check covers the one viewer mutation the viewer
session cookie authenticates, the viewer logout. Viewer entry presents an
access code rather than that cookie: it is limited by the entry rate limit,
not by origin, so an entry from another origin reaches the route.

### Enforces

A25 (`rules.http_transport_policy`), R0-09.

### Errors

Its refusals are the statuses above, each with an empty body.

### State impact

The in-memory viewer-entry attempt buckets only.

## `public_op:runtime_settings.load_runtime_settings`

### Owner

`module:runtime_settings`. Read, normalize, default and validate the deployment environment once.

### Callers

`module:runtime`, `module:staff_bootstrap_cli`.

### Inputs

None: the process environment, by the closed table
`config.runtime_environment_variables`.

### Outputs

The immutable `RuntimeSettings`.

### Observable effect

None; no raw environment value is logged.

### Enforces

A30 and R0-10; the viewer-entry rate limit comes only from its two variables;
`rules.binary_delivery_policy.size_bounds.startup_consistency` is checked and
neither bound is changed silently.

### Errors

A missing, malformed or inconsistent value (a wildcard host or origin, binary
bounds out of order) stops the start.

### State impact

None.

## `public_op:runtime.create_runtime_app`

### Owner

`module:runtime`. Compose the running service from its settings.

### Callers

`boundary:deployment_process`.

### Inputs

`RuntimeSettings` supplied by the caller.

### Outputs

The outer FastAPI application.

### Observable effect

None at import: construction happens only on this call.

### Enforces

R0-10 and R0-11: exactly one `PortalStore` from `settings.database_url`; one
inner application from `api.create_app`; liveness at `/health/live` and
readiness at `/health/ready`, each answering exactly `HealthStatus`; the
transport guard installed before mounting; the inner application mounted at
`/api` and then at `/`. It implements no transport policy itself. The
settings handed here reach only the store and the transport guard: the
inner application and the use cases receive no `RuntimeSettings`; which
knobs a deployment can change is carried to States 6–7 (`SOURCE.md`). The
inner application answers at both prefixes, so a route is reached whether
or not the proxy has stripped `/api`; behind the stripping proxy a path that
repeats the prefix (`/api/api/…`) reaches the same route, and no route
exists only under one prefix.

### Errors

A store or application construction failure propagates. Readiness opens and
closes one portal transaction; when that cannot be opened it answers 500
with no `HealthStatus` body and no internal detail, never `ok`. Liveness does
not touch the store.

### State impact

None until a request arrives; readiness opens and rolls back one transaction.

## `public_op:staff_bootstrap_cli.run_bootstrap_cli`

### Owner

`module:staff_bootstrap_cli`. Run the local first-administrator command and return its exit code.

### Callers

`boundary:host_operator_cli`.

### Inputs

None: the email and the password, twice without echo, from the terminal.

### Outputs

The exit code `rules.staff_bootstrap_policy.command_outcomes` assigns: 0
created, 1 confirmation mismatch, 2 rejected input, 3 already initialized.

### Observable effect

One message per outcome on the terminal; the password or its hash is never
echoed, printed or logged.

### Enforces

R0-07 and A29: the mismatch is refused before any store exists; the database
comes from `runtime_settings.load_runtime_settings`; the password never comes
from arguments, environment or a file.

### Errors

Each refusal is its exit code. A configuration or storage failure is none of
the four outcomes: the operation raises it and returns no exit code, and the
failure status the host process then ends with is outside the closed
contract of A29.

### State impact

Through `staff_bootstrap`: one administrator and its audit, or nothing.

## Changes against the former text

Each is the accepted Factory spec, kept under the owner decision of
2026-11-06 (current service behaviour accepted; technical decisions
delegated):

- **One operation per State 3 capability** (108) instead of per-module
  tables. Added: the eleven repository schema
  functions, `staff_bootstrap`, `staff_bootstrap_cli`, the seven
  `api_irregular` viewer endpoints, `transport_guard`, `runtime_settings`,
  `runtime`, `describe_viewer_session`, `sign_out_viewer`,
  `create_staff_account`, `resolve_staff_session`, `change_staff_password`
  and `perform_recovery_override` as routed operations (Factory
  `3080ef0dbe73`, `35a0a09ccbb1`, `38626cc7be12`, `6011ac93b143`).
- **`staff_challenges` split from `staff_identity`** (Factory
  `f12197b46a82`), and its operations inert (R0-23): the former outputs
  `ChallengeIssueView` and `StaffAccount` are never produced; the email gateway
  is uncalled. The former `create_staff_account` with a verification challenge
  is the administrator activation of R0-19.
- **Narrow ports** instead of the `PortalStore` facade surface (Factory
  `af686d7364d2` … `88c1dbbcc3a6`); `PortalStore`, `PortalTransaction` and the
  repository classes are exported classes, not operations.
- **Identity outputs are safe views**: `StaffAccountView` without the hash for
  every staff account change, `SessionRevocationResult` for session
  revocation, `ExpenseOperationOutcome` and `PhotoMutationResult` for
  mutations (Factory `9eab4d948181`, `d1280708714f`).
- **`authorize_producer_scope` is called by `api`**, not by
  `snapshot_import`; the route then calls `authorize_snapshot_import`, whose
  refusal is answered unrecorded, and `import_snapshot` repeats it once and
  records every classified rejection (R0-25, Q20).
- **Viewer reads**: `list_viewer_projects` omits a grant whose context fails
  (Factory `00ac72f18d9c`); the overview carries six availabilities (Factory
  `d2c4511ea119`).
- **Binary reads answer exact bytes** (Factory `babd5e5262d9`); a document's
  failures are one `BinaryAccessRejected`, a photo's are not.
- **Errors are the closed exception set of the route table** instead of the
  former families `DomainValidationRejected` and `DomainConflict`.
- **Route table** is `rules.http_router_backend` (56 routes, 49 table and 7
  irregular) instead of the former `rules.http_route_catalog`; administrator
  project discovery `GET /admin/projects` is added (R0-08).
