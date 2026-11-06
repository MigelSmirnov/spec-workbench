# State 4 — Client Portal reviewed flows

## Status

Migrated on 2026-11-06 from the former `spec/40_flows.md` (authoring pass of
2026-07-18/19, flows F1–F9, `SOURCE.md`) and the accepted Factory spec
`projects/client_portal_sandbox/specs/base/global_spec.json` (sha256
`459ac96c4b8febc629c81178c9d0a84ee072d1662dc52f44d74fb0993cb3c2c7`): its
routes (`rules.http_router_backend`), its guard order
(`rules.project_guard_sequence`) and the notes of the operations each flow
names. The flows are those of `40_flow_plan.json`, walked against the State 3
ownership of `30_modules.md`. They name who triggers, what crosses each
boundary, who decides next and who produces each result and each failure.
They do not freeze State 5 public operations or State 6 signatures.

Where the former text and the accepted spec disagree, the accepted spec is
kept (owner 2026-11-06: current service behaviour accepted; technical
decisions delegated); every such case is listed in "Changes against the former
text" at the end.

## Conventions every flow follows

- **Entry.** Every HTTP request first passes the transport guard of A25 (one
  middleware installed by the runtime): trusted host, body bound, viewer-entry
  rate limit, viewer sign-out origin, security and `no-store` headers, one
  redacted log line. A refusal there reaches no route. Staff, administrator and
  producer routes are the route table of `rules.http_router_backend`; viewer
  routes are the browser boundary of R0-09. A route handler extracts the
  credential and the declared request body, calls exactly one owning use case
  and returns its result or a safe projection of it; it decides nothing,
  retries nothing and writes no audit.
- **Trusted context.** No request field is trusted as an actor, role,
  capability or project context. Identity operations resolve a session or a
  bearer credential into an actor context; the authorization guard turns an
  actor context and a `project_id` into an `AuthorizedProjectContext` by the
  order `valid_session`, `active_principal`, `project_access`,
  `required_capability`, `registry_lifecycle`, first failure winning and
  concealed. Project-scoped use cases receive that context, never an
  unchecked `project_id`; access management and the snapshot import take a
  `project_id` and authorize it themselves, as their flows say.
- **Transactions and network.** The use case that owns an operation opens its
  portal transaction, closes it exactly once and guards it as A22 requires.
  An authorization check that opens its own transaction closes it before the
  caller opens one. Registry calls happen outside any open portal transaction.
- **Audit.** A significant success and its audit record commit in one
  transaction (A13, A23). Replay of an idempotent operation writes no second
  creation audit; the snapshot import is the exception, because each of its
  classified attempts, a replay included, is its own import result with its
  own `snapshot.import` audit (R0-25, A13).
- **Failure translation.** A use case raises one declared failure; the route
  table's `error_policy` maps it once to a status with an empty body
  (authentication 401, authorization 403, not found and concealed binary 404,
  archived project and conflicts 409, input 422, challenge 400 and 429,
  Registry 502, persistence and storage 500). No failure becomes a success,
  an empty list or a zero, with two exceptions: the viewer's project list
  leaves out a project whose context cannot be obtained
  (`flow:viewer_reads_projects`), and the project overview answers a failed
  part as `temporarily_unavailable` with no value
  (`flow:build_project_overview`).
- **Archived projects.** Reads of an archived project succeed; every mutation
  of its records (except the empty manual budget of R0-24) and every new
  grant or assignment for it is refused;
  revocation of existing access does not consult the Registry (R0-24).

## `flow:start_service_and_answer_health`

### Trigger

The deployment process starts the service, and later a monitor or proxy asks
for liveness or readiness (R0-10, R0-11).

### Boundary

`module:runtime_settings` owns reading the environment, once: the closed table
`config.runtime_environment_variables`, defaults, normalization and the
startup checks (A30), into `RuntimeSettings`. `module:runtime` owns the
running application: one `PortalStore`, the inner application of `module:api`
mounted with the transport guard of `module:transport_guard`, and the two
health answers. `module:portal_store` owns the database connection and
creates every repository schema when a transaction begins. Crossing models:
`RuntimeSettings` from settings to runtime and guard; `HealthStatus` out.

### Steps

1. `capability:runtime_settings.load_runtime_settings` reads and validates the
   environment variables of A30; a missing, malformed or inconsistent one (a
   wildcard host or origin, binary bounds out of order) stops the start
   before any request is served. The Registry endpoint is not one of them:
   the service starts without it (A6).
2. `capability:runtime.create_runtime_app` builds one `PortalStore` from the
   settings, builds the inner application with
   `capability:api.create_app`, installs
   `capability:transport_guard.install_transport_guards` with the settings and
   mounts the inner application under `/api` and at the root.
3. Liveness answers `ok` without reading anything. Readiness opens one
   `module:portal_store` transaction and rolls it back; it changes no product
   state.
4. Every `module:portal_store` transaction — readiness and every use case —
   begins by creating any missing table on its new connection, one schema
   function per repository: `capability:audit_repository.create_audit_schema`,
   `capability:project_tracking_repository.create_project_tracking_schema`,
   `capability:project_section_repository.create_project_section_schema`,
   `capability:budget_repository.create_budget_schema`,
   `capability:snapshot_import_repository.create_snapshot_import_schema`,
   `capability:expense_repository.create_expense_schema`,
   `capability:progress_photo_repository.create_progress_photo_schema`,
   `capability:email_delivery_repository.create_email_delivery_schema`,
   `capability:staff_access_repository.create_staff_access_schema`,
   `capability:viewer_access_repository.create_client_access_schema` and
   `capability:service_identity_repository.create_producer_identity_schema`
   (accepted note `PortalStore.begin`). Each creation is idempotent and
   commits nothing itself; a failure closes the new connection and is the
   storage failure.

### Outcomes

- A running service bound to its trusted hosts and origins. Produced by
  `module:runtime`.
- `HealthStatus` `ok` for liveness and for readiness when the database opens.
  Produced by `module:runtime`.

### Errors

- Invalid configuration: `module:runtime_settings` refuses the start; nothing
  is served.
- A database that cannot be opened: readiness fails with the storage failure
  of `module:portal_store`; the answer discloses no path, credential, schema,
  dependency version, configuration or exception (R0-11).

## `flow:bootstrap_first_administrator`

### Trigger

The host operator runs the local administrative command on an empty
deployment (R0-07, A29).

### Boundary

`module:staff_bootstrap_cli` owns the terminal: it reads the email and the
password twice without echo and maps each outcome to its exit code.
`module:staff_bootstrap` owns the operation: input rules through the staff
identity input boundary, the password hash, the account and its audit.
`module:staff_bootstrap_store` owns its own connection and the exclusive
write transaction. `module:credential_security` hashes the password.
`module:runtime_settings` resolves the database location.
No HTTP route reaches this flow.

### Steps

1. `capability:staff_bootstrap_cli.run_bootstrap_cli` reads the email and the
   password twice; a mismatch ends the command with exit code 1 before any
   store exists.
2. It resolves the database through
   `capability:runtime_settings.load_runtime_settings` and builds the
   bootstrap store.
3. `capability:staff_bootstrap.bootstrap_first_administrator` normalizes and
   validates the email and password, hashes the password with
   `capability:credential_security.hash_password`, and builds one active,
   verified administrator with no creator and its `staff.create` audit with
   the system actor.
4. `module:staff_bootstrap_store` opens its own connection, ensures the staff
   access and audit tables exist with
   `capability:staff_access_repository.create_staff_access_schema` and
   `capability:audit_repository.create_audit_schema`, begins a write
   transaction no concurrent attempt can interleave, checks that the staff table is empty, inserts the account and the audit
   and commits once; concurrent attempts create exactly one account.

### Outcomes

- One active verified administrator and one `staff.create` audit; exit code 0.
  Produced by `module:staff_bootstrap` and `module:staff_bootstrap_store`.

### Errors

- Confirmation mismatch: exit code 1, by `module:staff_bootstrap_cli`.
- Rejected email or password: exit code 2; nothing is written.
- Any staff account already exists: `BootstrapAlreadyCompleted`, exit code 3;
  neither write persists.
- The password is never printed, logged, audited, returned or read from
  arguments, environment or a file (`rules.staff_bootstrap_policy`).

## `flow:staff_session_lifecycle`

### Trigger

A staff member logs in with email and password, then uses the session, changes
the password or signs out; an administrator revokes a member's sessions.

### Boundary

`module:api` extracts the bearer session token and the request bodies.
`module:staff_identity` owns accounts, sessions, login, password change and
sign-out (A3, A16). `module:credential_security` owns hashing, secret issue
and verification (A17). `module:authorization_guard` owns the concealed
authentication failure and the access-management check (A1, A11).
`module:audit_writer` validates and appends each audit.

### Steps

1. `capability:staff_identity.authenticate_staff` normalizes the email,
   accepts only an active account with a verified email and a matching
   password (`capability:credential_security.verify_password`), issues a
   session secret for a fresh session id
   (`capability:credential_security.issue_verification_secret`), stores only
   its hash with a fixed expiry of `config` staff session TTL, and appends
   `staff.login` through `capability:audit_writer.append_audit` in the same
   transaction.
2. A malformed email is refused with `IdentityInputRejected` before any
   lookup and appends no audit. On every other rejection it appends
   `staff.login_failed` and raises the error of
   `capability:authorization_guard.conceal_authentication_failure`; the answer
   never says which check failed.
3. Each later staff request presents the token as a bearer header;
   `capability:staff_identity.resolve_staff_session` parses the selector,
   verifies the secret part (`capability:credential_security.parse_verification_secret`,
   `capability:credential_security.verify_secret`), the expiry, the
   revocation, the active account and its verified email, and returns the
   `StaffActorContext`.
4. `capability:staff_identity.change_staff_password` verifies the current
   password and stores the new hash; it writes no audit record (State 1: no
   catalog action exists for it).
5. `capability:staff_identity.sign_out_staff` revokes the presented session.
6. An administrator, checked by
   `capability:authorization_guard.authorize_access_management`, calls
   `capability:staff_identity.revoke_staff_sessions` for one account; every
   active session of it is revoked and `staff.sessions_revoke` is audited.

### Outcomes

- `StaffSessionGrant` with the plaintext token once; never logged or
  recoverable. Produced by `module:staff_identity`.
- `StaffActorContext` for every later request; the updated account view after
  a password change; the revoked session or the revocation result. Produced by
  `module:staff_identity`.

### Errors

- Malformed login email: `IdentityInputRejected` (422), no audit.
- Unknown email, wrong password, unverified, pending, suspended or disabled
  account, malformed, expired or revoked token: one concealed authentication
  failure (401).
- A non-administrator revoking sessions: authorization failure (403).
- A storage failure rolls back the whole operation, audit included (500).

## `flow:deferred_staff_challenges`

### Trigger

A caller uses an email-challenge route: an administrator issues an email
verification, a staff member requests an email change, anyone confirms a
verification or change, requests or completes a password reset.

### Boundary

`module:staff_challenges` owns these operations. In the accepted service they
are deferred (R0-23, Q19): no challenge repository exists, so they read,
write, audit and deliver nothing, and `module:email_delivery_gateway` is
called by none of them. The A10 policy stays the design they follow once
built.

### Steps

1. `capability:staff_challenges.issue_email_verification`,
   `capability:staff_challenges.request_email_change`,
   `capability:staff_challenges.confirm_email_verification`,
   `capability:staff_challenges.confirm_email_change` and
   `capability:staff_challenges.complete_password_reset` reject before
   parsing any token through the concealed authentication failure.
2. `capability:staff_challenges.request_password_reset` normalizes the
   address, answers identically for every value — malformed, unknown or known —
   and does nothing else.
3. The delivery the A10 design hands a challenge to once it is built,
   `capability:email_delivery_gateway.deliver_email_message`, exists in the
   accepted service and is imported by `module:staff_challenges`, but no step
   of this flow calls it: no challenge is issued, so nothing is delivered
   (R0-23, Q19).

### Outcomes

- Password-reset request: accepted (202) with no body and no effect. Produced
  by `module:staff_challenges`.
- Nothing is stored or sent; no email is verified by these routes. Staff
  onboarding uses the administrator activation of
  `flow:administer_staff_accounts` instead (R0-19).

### Errors

- Every other challenge route: the concealed authentication failure (401).

## `flow:administer_staff_accounts`

### Trigger

An administrator creates a staff account, changes its status, assigns it to a
project or revokes an assignment, performs the recovery override, or lists the
active Registry projects to choose from (R0-08, R0-14, R0-19, R0-20).

### Boundary

`module:authorization_guard` decides access management from the persisted
role of the session's account. `module:staff_identity` owns accounts, status
transitions with their cascades, assignments and the recovery override.
`module:registry_gateway` validates project references and lists active
projects. `module:credential_security` hashes the initial password.
`module:audit_writer` appends each audit.

### Steps

1. Every operation starts with
   `capability:authorization_guard.authorize_access_management`, completed
   before its own transaction opens.
2. `capability:staff_identity.create_staff_account` normalizes the email,
   refuses an existing normalized email, hashes the submitted initial password
   (`capability:credential_security.hash_password`), inserts the account as
   `pending_verification` and appends `staff.create`.
3. `capability:staff_identity.change_staff_status` applies only the
   transitions of `rules.status_transitions`; activation of a pending account
   sets `email_verified_at`; suspension or disabling revokes the account's
   sessions; the audit is `staff.reinstate`, `staff.suspend` or
   `staff.disable`.
4. `capability:registry_gateway.list_active_projects` returns the active
   Registry projects ordered by `project_id`, after the access-management
   check passed.
5. `capability:staff_identity.assign_staff_project` validates the project with
   `capability:registry_gateway.validate_project_reference` before its
   transaction — unknown is not found, not active is refused as archived —
   refuses a duplicate active assignment and appends `staff_assignment.create`.
6. `capability:staff_identity.revoke_staff_project_assignment` revokes the
   addressed active assignment without consulting the Registry and appends
   `staff_assignment.revoke`; the next guard check observes it.
7. `capability:staff_identity.perform_recovery_override` replaces the login
   email with the given normalized address, marks it verified and appends
   `staff.recovery_override` atomically.

### Outcomes

- `StaffAccountView` without the password hash for creation, status change and
  recovery override; the assignment record for assign and revoke; the list of
  `ProjectReference` for discovery. Produced by `module:staff_identity` and
  `module:registry_gateway`.

### Errors

- Not an administrator: 403, before any Registry call or write.
- Duplicate email, invalid email or password, transition not in the table:
  input rejection (422), nothing written.
- Unknown project or assignment: not found (404); archived project for a new
  assignment: 409; Registry failure: 502.
- A second assignment for a pair: while the first is active, refused by the
  operation's own check before any write (authorization rejection, 403);
  after its revocation, refused by State 1's one-record-per-pair rule
  (persistence conflict, 500).

## `flow:administer_viewer_access`

### Trigger

An administrator creates a client viewer, issues or revokes its access link,
grants or revokes one project, or revokes the viewer (R0-14).

### Boundary

`module:viewer_access` owns viewers, credentials, grants and the revocation
cascades of `rules.revocation_cascades`. `module:authorization_guard` decides
access management. `module:registry_gateway` validates the project of a new
grant. `module:credential_security` issues the link secret.
`module:audit_writer` appends each audit.

### Steps

1. Every operation starts with
   `capability:authorization_guard.authorize_access_management`.
2. `capability:viewer_access.create_viewer` creates an active viewer and
   appends `viewer.create`.
3. `capability:viewer_access.issue_viewer_access` revokes every earlier
   credential of the viewer and its active sessions, stores the hash of one
   new secret (`capability:credential_security.issue_verification_secret`) and
   appends `viewer.credential_issue`; the plaintext link secret is in this
   answer only.
4. `capability:viewer_access.revoke_viewer_access` revokes one credential and
   the viewer's sessions and appends `viewer.credential_revoke`.
5. `capability:viewer_access.grant_viewer_project` requires the project known
   and active (`capability:registry_gateway.validate_project_reference`,
   before the transaction; the operation itself reads the answer's `exists`
   and `is_active` as A5 says and refuses an unknown or inactive project by
   raising the Registry boundary error, unlike a staff assignment; the
   gateway raises nothing for such an answer), an active viewer and no active grant for the pair,
   and appends `grant.create`.
6. `capability:viewer_access.revoke_viewer_project` revokes the addressed
   active grant without consulting the Registry and appends `grant.revoke`;
   only that project closes.
7. `capability:viewer_access.revoke_viewer` revokes the viewer with its
   sessions and credentials and appends `viewer.revoke`; all its projects
   close.

### Outcomes

- `ClientViewer`, `ViewerCredentialIssue` (secret once), the revoked
  credential, `ProjectViewerGrant`. Produced by `module:viewer_access`.

### Errors

- Not an administrator: 403.
- Unknown or inactive viewer, unknown credential or grant: not found (404).
- A second grant for a pair: while the first is active, refused by the
  operation's own check before any write (403); after its revocation,
  refused by State 1's one-record-per-pair rule (persistence conflict, 500).
- Project not known or not active for a new grant: Registry boundary
  failure (502).

## `flow:viewer_entry_and_session`

### Trigger

A client opens the access link in the browser, later restores the session or
signs out (R0-09).

### Boundary

`module:api_irregular` owns the viewer browser boundary: the entry body, the
host-only cookie, its reading and clearing; a viewer bearer header is refused.
`module:viewer_access` owns entry, session resolution, description and
sign-out. `module:credential_security` verifies the link secret and issues the
session secret. `module:transport_guard` has already rate-limited entry per
client address; it checks the origin of sign-out only.

### Steps

1. `capability:api_irregular.viewer_enter_endpoint` reads only
   `capability_secret` from the JSON body and calls
   `capability:viewer_access.enter_viewer_access`.
2. `module:viewer_access` parses the selector, verifies the secret part
   against the stored hash of an active credential of an active viewer
   (`capability:credential_security.parse_verification_secret`,
   `capability:credential_security.verify_secret`), and creates a session with
   a fresh id and a fixed expiry of `config.viewer_session_ttl_days`
   (`capability:credential_security.issue_verification_secret`). Entry is not
   an audited action.
3. The endpoint sets the session cookie and answers the secret-free session
   view.
4. `capability:api_irregular.viewer_restore_session_endpoint` reads the
   cookie, resolves it through `capability:viewer_access.resolve_viewer_session`
   and answers `capability:viewer_access.describe_viewer_session`.
5. `capability:api_irregular.viewer_logout_endpoint` resolves the session,
   calls `capability:viewer_access.sign_out_viewer`, which revokes it, and
   clears the cookie.

### Outcomes

- A viewer session cookie and `ViewerSessionView`; no viewer credential is
  readable by page script. Produced by `module:api_irregular` from the session
  of `module:viewer_access`.
- After logout the cookie is cleared and the session is revoked.

### Errors

- Unknown selector, wrong secret, revoked credential or viewer, expired or
  revoked session, missing cookie, a bearer header: one concealed
  authentication failure (401).
- Too many entry attempts: refused by the transport guard before verification.

## `flow:viewer_reads_projects`

### Trigger

A viewer with a session lists the granted projects, opens one, or downloads a
visible document or photo of it.

### Boundary

`module:api_irregular` resolves the cookie session and owns the viewer routes.
`module:authorization_guard` authorizes the viewer read per project.
`module:derived_views` owns the project list and the overview.
`module:viewer_access` gives the viewer's active grants.
`module:registry_gateway` gives live project context. `module:expense_management`
and `module:photo_management` own binary eligibility; `module:binary_storage`
reads the bytes.

### Steps

1. `capability:api_irregular.list_viewer_projects_endpoint` calls
   `capability:derived_views.list_viewer_projects`, which reads the viewer's
   active grants (`capability:viewer_access.list_viewer_project_grants`) and
   fetches each project's context
   (`capability:registry_gateway.get_project_context`). A grant whose context
   cannot be obtained is left out; the rest are ordered by the portal's own
   order (A15). Archived projects stay listed.
2. `capability:api_irregular.viewer_project_overview_endpoint` authorizes the
   project with `capability:authorization_guard.authorize_viewer_project_read`
   and answers `capability:derived_views.build_project_overview`
   (`flow:build_project_overview`).
3. `capability:api_irregular.viewer_read_expense_document_endpoint` and
   `capability:api_irregular.viewer_read_progress_photo_endpoint` authorize
   the project the same way and call
   `capability:expense_management.read_expense_document` or
   `capability:photo_management.read_progress_photo`; the owning module
   requires a client-visible record of that project and hands an authorized
   reference to `capability:binary_storage.read_binary`.
4. The endpoint answers the exact bytes with the recognized media type and
   the derived download name (A14, R0-12).

### Outcomes

- `list[ProjectListItem]`, `ProjectOverview`, or the exact bytes of one
  binary. Produced by `module:derived_views`, `module:binary_storage`.

### Errors

- Session failures: 401. A project without an active grant is not found
  (404), never "forbidden".
- Binary reads answer as in `flow:staff_reads_protected_binary`: a document
  refusal is one concealed not-found answer (404); a photo refusal is one
  validation refusal (422) and its undeliverable content a
  storage-unavailable failure (500) (State 0 R0-12).
- Registry failure while authorizing one project: 502.

## `flow:administer_service_principals`

### Trigger

An administrator creates a service principal, changes its status, issues or
revokes a credential, or grants or revokes a producer project.

### Boundary

`module:service_identity` owns principals, credentials, producer grants and
their cascades (A12). `module:authorization_guard` decides access management.
`module:registry_gateway` validates the project of a new producer grant.
`module:credential_security` issues the credential secret.
`module:audit_writer` appends each audit.

### Steps

1. Every operation starts with
   `capability:authorization_guard.authorize_access_management`.
2. `capability:service_identity.create_service_principal` creates an active
   principal with its source type and scope mode and appends
   `principal.create`.
3. `capability:service_identity.change_service_principal_status` disables or
   enables it; disabling revokes its credentials.
4. `capability:service_identity.issue_service_credential` stores the hash of a
   new secret with the next key version and an optional expiry
   (`capability:credential_security.issue_verification_secret`) and appends
   `principal.credential_issue`; the plaintext is in this answer only (Q10).
5. `capability:service_identity.revoke_service_credential` revokes one
   credential.
6. `capability:service_identity.grant_producer_project` requires the project
   known and active (`capability:registry_gateway.validate_project_reference`)
   and appends `producer_grant.create`;
   `capability:service_identity.revoke_producer_project` revokes without
   consulting the Registry and appends `producer_grant.revoke`.

### Outcomes

- `ServicePrincipal`, `ServiceCredentialIssue` (secret once), the revoked
  credential, `ProducerProjectGrant`. Produced by `module:service_identity`.

### Errors

- Not an administrator: 403. Unknown principal, credential or grant: 404.
  Archived project for a new grant: 409. Registry failure: 502.

## `flow:import_estimate_snapshot`

### Trigger

An authorized producer publishes an approved estimate snapshot, or reads the
result of an earlier import by its `import_id` (R0-04, R0-21, R0-25).

### Boundary

`module:api` extracts the bearer credential and runs the route's checks in
the order of `rules.http_router_backend`. `module:service_identity`
authenticates the principal and answers its producer scope (A12).
`module:authorization_guard` authorizes the import against the persisted
principal, its grant and the Registry lifecycle. `module:snapshot_import` owns
validation, fingerprint, replay classification, the import record and its
audit (A7, A8). `module:financial_policy` validates amounts.

### Steps

1. `capability:service_identity.authenticate_service_principal` parses the
   bearer secret before any transaction, verifies the secret part, expiry,
   revocation and the active principal, and returns `ServiceActorContext` with
   its key version.
2. The route calls `capability:service_identity.authorize_producer_scope`
   (its answer is not used; a Registry or storage failure in it propagates),
   then `capability:authorization_guard.authorize_snapshot_import`, which
   checks the active principal, the producer's grant for a
   `granted_projects` scope, the import capability and the active Registry
   project. A refusal there is raised to the producer and records nothing
   (R0-25, Q20).
3. `capability:snapshot_import.import_snapshot` computes one fingerprint and
   time per attempt and repeats
   `capability:authorization_guard.authorize_snapshot_import` before its
   transaction; only if access changed since step 2 does it classify an
   archived, unknown or scope-denied rejection instead of raising.
4. In one transaction it validates the contract version, EUR currency,
   complete content and section amounts
   (`capability:financial_policy.validate_eur_amount`), then classifies by the
   identity `project_id + estimate_id + estimate_version`: new — insert the
   snapshot, `accepted`; equal fingerprint — `idempotent_replay` naming the
   existing snapshot; different fingerprint — `integrity_conflict`, no
   snapshot written.
5. Every classified attempt inserts one fresh import record with a fresh
   `import_id` and one `snapshot.import` audit, committed together.
6. `capability:snapshot_import.get_snapshot_import_result` returns a record
   only to the principal that made it.

### Outcomes

- `SnapshotImportRecord` with `import_id`, outcome, reason and snapshot id.
  Produced by `module:snapshot_import`. No budget version, section or plan is
  created and nothing is activated (Q11).

### Errors

- Authentication failure: 401, nothing recorded.
- Access refusals of step 2: unknown or ungranted project 404, refused
  capability 403, archived project 409, Registry failure 502; nothing
  recorded (Q20).
- Content rejections, replays and conflicts are recorded and audited
  results, not errors; only a `rejected` record carries a `reject_reason`
  (M20), and a conflict's audit carries `integrity_conflict` as its reason
  code (A13).
- A record of another principal or an unknown `import_id`: not found (404).
- A storage failure rolls back snapshot, record and audit together (500).

## `flow:maintain_and_activate_budget`

### Trigger

An operator or administrator with mutation rights on the project creates the
manual budget, edits a section plan, reads a budget version, or activates a
version.

### Boundary

`module:authorization_guard` authorizes the staff mutation or read with the
capability the route names. `module:budget_management` owns versions,
sections, plans and activation (A18). `module:financial_policy` validates
amounts. `module:audit_writer` appends each audit.

### Steps

1. The route authorizes with
   `capability:authorization_guard.authorize_staff_project_mutation` (or
   `capability:authorization_guard.authorize_staff_project_read` for a read).
2. `capability:budget_management.ensure_manual_budget` returns the one manual
   version or creates it inactive with no plans and appends
   `budget.manual_version_create`.
3. `capability:budget_management.upsert_manual_section_plan` validates both
   amounts (`capability:financial_policy.validate_eur_amount`) and an active
   project before the transaction, creates or renames the stable section or
   reuses a given one of the project
   (`capability:budget_management.validate_project_section`), keeps an existing
   plan id, and appends `budget.section_plan_edit`.
4. `capability:budget_management.get_budget_version` returns one version of the
   project with its ordered plans.
5. `capability:budget_management.activate_budget_version` requires the
   activation capability, refuses while any existing allocation would lose its
   section, deactivates the prior active version, activates the requested one
   and appends `snapshot.activate`, all in one transaction.

### Outcomes

- `BudgetVersionDetail` and `BudgetActivationResult`; at most one active
  version per project. Produced by `module:budget_management`.

### Errors

- Guard failures: 401, 403, 404, archived 409.
- Invalid amounts or names: 422. The route's guard checks the activation
  capability (`portal.estimate_snapshot.activate`, 403 without it);
  `activate_budget_version` also refuses a context authorized for another
  capability as its input rejection (422), which the route never passes
  (Factory code `api/router.py` `activate_budget_version_endpoint`,
  `domain/budget_management.py`).
- Allocations that would lose their section: conflict (409), nothing changed.

## `flow:expense_intake_and_management`

### Trigger

Staff submits a confirmed recognition result with its allocation, then
corrects the expense, includes or excludes it, replaces its allocations, or
edits its document's description and visibility (R0-05, R0-17, R0-18).

### Boundary

`module:authorization_guard` authorizes the staff mutation.
`module:expense_intake` owns the OCR contract, creation and replay (A7, A8).
`module:expense_management` owns corrections, inclusion, allocations and
documents (A19). Each of them resolves sections of the project itself,
through `module:portal_store`'s section repository (Factory code
`application/expense_intake.py`, `domain/expense_management.py`).
`module:financial_policy` validates money.

### Steps

1. The route authorizes with
   `capability:authorization_guard.authorize_staff_project_mutation`.
2. `capability:expense_intake.create_expense_from_recognition` accepts only a
   confirmed complete result of a supported contract version, validates the
   total (`capability:financial_policy.validate_eur_amount`) and the explicit
   allocations — shape, exact sum, no proportional split, then every section
   of the project, read through `module:portal_store`'s section repository in
   a read-only transaction it closes first — then in one transaction looks up the
   `recognized_document_id`: absent — insert the expense, its allocations and
   one client-visible document and append `expense.create`; same fingerprint —
   return the existing expense as replay; different — conflict.
3. `capability:expense_management.correct_expense`,
   `capability:expense_management.set_expense_inclusion` and
   `capability:expense_management.replace_expense_allocations` revalidate
   money (`capability:financial_policy.validate_eur_amount`) and sections
   inside one transaction and append `expense.correct`, `expense.include` or
   `expense.exclude`, `expense.allocate`.
4. `capability:expense_management.update_expense_document` changes only the
   description and visibility and appends `document.update`.

### Outcomes

- `ExpenseOperationOutcome` (aggregate with `replayed`) or the updated
  `ExpenseDocument`. Produced by `module:expense_intake` and
  `module:expense_management`.

### Errors

- Guard failures as in every staff mutation.
- Unsupported, unconfirmed or incomplete input, wrong currency, invalid
  allocation: 422, nothing written.
- Same recognized document with different content: conflict (409).

## `flow:track_progress_payments_and_photos`

### Trigger

Staff sets a section's completion, registers a work payment, publishes a
progress photo or changes its caption, section or visibility, or lists
progress, payments and photos.

### Boundary

`module:authorization_guard` authorizes. `module:project_tracking` owns
progress and payments (A20). `module:photo_management` owns photos and their
replay. `module:project_tracking` validates its section through
`module:budget_management` (`capability:budget_management.validate_project_section`);
`module:photo_management` resolves an optional section through
`module:portal_store`'s section repository (Factory code
`domain/photo_management.py`). `module:financial_policy`
validates payment amounts.

### Steps

1. Mutations authorize with
   `capability:authorization_guard.authorize_staff_project_mutation`, lists
   with `capability:authorization_guard.authorize_staff_project_read`.
2. `capability:project_tracking.set_section_progress` validates the section of
   the project (`capability:budget_management.validate_project_section`) and
   an integer 0–100, upserts the value and appends `progress.update`.
3. `capability:project_tracking.register_work_payment` validates the amount
   (`capability:financial_policy.validate_eur_amount`); a new `payment_id`
   inserts the payment and appends `payment.register`; equal content returns
   the existing payment without audit; different content is a conflict.
4. `capability:photo_management.publish_progress_photo` requires the
   publication's project to be the authorized one, resolves an optional
   section, and replays by `intake_id`; a new photo gets a fresh id, keeps its
   `file_ref` and given visibility, and appends `photo.publish`.
5. `capability:photo_management.update_progress_photo` changes caption,
   section and visibility only and appends `photo.update`.
6. `capability:project_tracking.list_project_progress`,
   `capability:project_tracking.list_project_payments` and
   `capability:photo_management.list_progress_photos` read the project's
   records.

### Outcomes

- `SectionProgress`, `WorkPayment`, `PhotoMutationResult`, and the lists.
  Produced by `module:project_tracking` and `module:photo_management`.
  Photographs never change progress or money.

### Errors

- Guard failures; invalid section, range, amount or project: 422; replay with
  different content: 409.

## `flow:build_project_overview`

### Trigger

A staff member or a viewer, already authorized for the project, asks for its
overview (`flow:viewer_reads_projects` step 2, or the staff overview route).

### Boundary

`module:derived_views` owns the overview and its views, their orders and the
explicit availability of each part (A15, A21, A27). `module:financial_policy`
owns every formula (A9). `module:registry_gateway` gives live context.
`module:authorization_guard` has authorized the read before the overview is
built.

### Steps

1. The staff route authorizes with
   `capability:authorization_guard.authorize_staff_project_read`.
2. `capability:derived_views.build_project_overview` fetches the live project
   context (`capability:registry_gateway.get_project_context`) and composes
   `capability:derived_views.build_budget_view`,
   `capability:derived_views.build_expense_view`,
   `capability:derived_views.build_progress_view` and
   `capability:derived_views.build_payment_view` with the visible photos.
3. The views compute material balance, completed work, cost-weighted overall
   progress and work balance with
   `capability:financial_policy.calculate_material_balance`,
   `capability:financial_policy.calculate_completed_work`,
   `capability:financial_policy.calculate_overall_progress` and
   `capability:financial_policy.calculate_work_balance`; only confirmed
   included expenses count.
4. Each of the six parts gets its own availability: no active budget is
   `not_configured`; a failed part is `temporarily_unavailable` with no value;
   the project part carries the context or its unavailability.

### Outcomes

- `ProjectOverview` with six availability and value pairs, deterministic for
  the same records. Produced by `module:derived_views`. No total is stored.

### Errors

- Authorization failures before any read. A part that cannot be read is
  marked unavailable, never zero or empty.

## `flow:staff_reads_protected_binary`

### Trigger

Staff downloads a document or a photo of a project it may read.

### Boundary

`module:authorization_guard` authorizes the staff read.
`module:expense_management` and `module:photo_management` decide eligibility
and reveal `file_ref` only to `module:binary_storage`, which resolves it under
the local root, bounds the read and recognizes the media type (A14).
`module:api` answers the bytes.

### Steps

1. The route authorizes with
   `capability:authorization_guard.authorize_staff_project_read`.
2. `capability:expense_management.read_expense_document` or
   `capability:photo_management.read_progress_photo` reads the record of the
   project, closes its transaction and calls
   `capability:binary_storage.read_binary` with the authorized reference.
3. `module:api` answers the exact bytes with the recognized media type and the
   download name derived from the kind and id.

### Outcomes

- The exact stored bytes. Produced by `module:binary_storage`.

### Errors

- Document: missing record, other project, hidden, missing object, oversize
  or unlisted media type: one concealed not-found answer (404). Photo:
  missing record, other project or hidden: one validation refusal (422);
  stored content that cannot be delivered (missing object, oversize,
  unlisted type): storage-unavailable failure (500), as State 0 R0-12
  says. Nothing is written.

## Changes against the former text

Each is the accepted Factory spec, kept under the owner decision of
2026-11-06 (current service behaviour accepted; technical decisions
delegated):

- **Email challenges (former F2) are deferred** (R0-23): the routes exist and
  change nothing; onboarding is the administrator activation (R0-19).
- **Viewer list (former F3)** leaves out a project whose context cannot be
  obtained instead of failing the whole list (Factory `00ac72f18d9c`).
- **Viewer session** travels in a host-only cookie read by `api_irregular`
  (R0-09); producers and staff use bearer headers read by `api`.
- **Snapshot import (former F4)**: the route refuses an access failure before
  the import and records nothing (Q20); every classified rejection is
  recorded and audited in the one import transaction, and every classified
  attempt gets a fresh `import_id` (R0-25).
- **Activation (former F5)** refuses while any allocation would lose its
  section, instead of activating and reporting a count; no operation turns a
  snapshot into a candidate version (Q11, deferred).
- **Project overview (former F8)** gives each part its own availability and
  carries the project part's availability (Factory `d2c4511ea119`).
- **Added flows**: service start and health (R0-10, R0-11), first
  administrator (R0-07), staff and service-principal administration and
  project discovery (R0-08, R0-14), progress, payments and photos, staff binary
  reads.
- **Schema creation named in the flows that run it** (added with State 5 on
  2026-11-06): every `portal_store` transaction and the bootstrap store create
  any missing table through the repositories' schema functions (accepted notes
  `PortalStore.begin`, `SqliteStaffBootstrapStore.create_if_empty`); the
  email gateway exists uncalled while challenges are deferred. The behaviour
  is unchanged; the flows now name the capabilities State 5 owns.

## Deferred features (not designed here)

Q11 candidate budget version from a snapshot, Q12 upload service (the
read-only boundary of R0-13 is a constraint), Q13 listing of a viewer's codes,
Q14 replay-safe client onboarding, Q16 estimate box, Q19 email challenges and
notices.
