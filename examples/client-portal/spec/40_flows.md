# State 4 — Key system flows

## Status

**Authoring pass State 4. Builds on States 0–3 and includes backward
corrections made while walking the flows: `StaffProjectAssignment`, transient
authentication/authorization contexts, concrete client read DTOs, and the R14
authenticated binary-stream policy. This document fixes sequencing and error
ownership, not Python signatures or the complete HTTP route catalog.**

## Flow conventions

- The API accepts credentials and request fields, but never constructs a
  trusted actor, role, capability, project context, or service key version
  from request claims. Identity modules produce trusted contexts.
- `authorization_guard` runs the complete R4 sequence. Domain use cases
  receive `AuthorizedProjectContext`, not an unchecked `project_id` plus role.
- Registry validation/context calls and email delivery calls occur before or
  after portal transactions, never while a portal database transaction is
  open.
- A successful significant mutation and its AuditRecord commit atomically.
  A rejected significant mutation writes its rejection audit in a separate
  short transaction after the rejection is known.
- API translation is last. A transport handler does not retry a use case,
  reinterpret a Registry result, manufacture an empty view, or write audit.
- The portal has no standalone project mode. Every project-scoped record uses
  a Registry-owned UUID; failed linked work never falls back to standalone.

## F1. Staff login and guarded project mutation

### F1a. Staff login

```text
email + password
→ API credential boundary
→ staff_identity + credential_security
→ StaffAccount/StaffSession persistence + audit
→ StaffSessionGrant returned once
```

1. `api` accepts normalized-login input over the authentication route and
   passes it to `staff_identity`; it does not query StaffAccount directly.
2. `staff_identity` loads by normalized email and uses
   `credential_security.verify_password`. Missing account, wrong password,
   unverified email, non-active status, and malformed credentials converge on
   the existence-hiding authentication failure owned by
   `authorization_guard.conceal_authentication_failure`.
3. On success, `credential_security` issues session plaintext plus its
   verification form. `staff_identity` creates StaffSession with the proposed
   fixed expiry; only the hash is persisted.
4. StaffSession and one `staff.login` AuditRecord commit atomically.
5. The observable success is StaffSessionGrant. Plaintext token appears once
   in that response and is never logged or reconstructed later.
6. A failed attempt creates one `staff.login_failed` rejection audit without
   storing password/email secrets. The public failure remains identical for
   missing and unusable accounts.

Failure owners: `staff_identity` owns credential/account conditions;
`credential_security` owns hash failures; `portal_store` translates database
failure; `api` only maps the stable public authentication failure.

### F1b. Project mutation

```text
session token + project command
→ staff_identity resolves session/account
→ authorization_guard executes R4
→ Registry validate (no portal transaction)
→ owning domain mutation + audit in one transaction
→ concrete updated entity/result
```

1. The session token resolves to an active StaffSession and active verified
   StaffAccount. Request role/capability fields, if present, are ignored or
   rejected as non-authoritative.
2. `authorization_guard` checks active StaffProjectAssignment for an operator
   (or the current single-area administrator scope), the R2 capability for the
   persisted role, and Registry lifecycle in R4 order.
3. `registry_gateway.validate_project_reference` must return the same UUID and
   `exists=true`. A mutation additionally requires `is_active=true`.
4. Only after Registry I/O completes does the owning module open a portal
   transaction, reload mutation preconditions that may have changed, apply the
   domain operation, append the R13 audit, and commit.
5. Assignment/session/account revocation detected on the transactional reload
   aborts the mutation even if the earlier guard passed.
6. Registry missing/archived/unavailable/schema/identity failures are
   translated once by `registry_gateway`; no stale context or client fields
   substitute for the failed validation.

Observable failures distinguish malformed command and Registry operational
failure where safe, but never reveal an inaccessible project. No domain state
is committed on any failure.

## F2. Email verification, email change, and password reset

### Shared issuance sequence

```text
authorized/self-service trigger
→ staff_identity policy/rate limit
→ challenge + EmailDeliveryRecord commit
→ email_delivery_gateway (after commit)
→ delivery telemetry update
```

1. `staff_identity` selects the purpose, checks R10 and the configured
   per-account rate limit, and issues plaintext/hash through
   `credential_security`.
2. In one transaction it revokes outstanding same-purpose records, persists
   the new challenge/reset/change record with only the hash, creates a pending
   EmailDeliveryRecord, and writes the action audit.
3. After commit it passes the plaintext only to `email_delivery_gateway` for
   immediate delivery. The gateway updates delivery telemetry in a separate
   transaction.
4. Accepted, failed, or timed-out delivery never consumes/revokes the
   challenge and never verifies an address. Staff may explicitly re-issue;
   there is no hidden automatic creation of multiple valid challenges.
5. Self-service password reset returns the same public acceptance for unknown,
   unverified, and eligible email addresses; only the eligible case creates a
   token and delivery.

### Consumption sequence

1. The API passes purpose-specific token plaintext to `staff_identity`.
2. The module loads only the matching purpose record, verifies through
   `credential_security`, and rejects expired/used/revoked/cross-purpose use.
3. Email verification atomically consumes the challenge, sets
   `email_verified_at`, transitions pending account to active, and audits.
4. Email change rechecks normalized-email uniqueness, consumes the change,
   replaces the login email, audits, commits, then requests a notice to the
   previous address. Notice failure does not roll back the completed change.
5. Password reset consumes the token, replaces the password hash, revokes all
   sessions and other reset tokens, creates the success audit, and commits;
   the password-changed notice is attempted after commit.
6. Replay produces an explicit invalid/consumed failure and no second account
   mutation.

The unconfirmed TTL values and self-service policy remain config/product
proposals; the flow depends only on finite TTL, single use, and
existence-hiding if self-service stays enabled.

## F3. Viewer entry, project list, archived read, and revocation

### Capability-link entry

1. The API passes link secret to `viewer_access`; it never accepts viewer ID
   as proof.
2. `viewer_access` verifies the one non-revoked credential, active viewer, and
   expiry/revocation state. It issues ViewerSession plaintext/hash through
   `credential_security`.
3. ViewerSession commits atomically; success returns ViewerSessionGrant once.
   Invalid/revoked links use the common existence-hiding auth failure. Viewer
   entry is not silently added to the closed R13 catalog; credential/grant
   management and revocation remain audited actions.

### Project list and read

1. ViewerSession resolves to one active ClientViewer.
2. `viewer_access` loads active ProjectViewerGrant records; URL/project IDs
   supplied outside those grants do not expand the set.
3. For each grant, `registry_gateway.get_project_context` obtains live typed
   context. The portal does not use `/projects/active` to remove archived
   granted projects: archived projects remain readable by product rule.
4. `derived_views` produces ProjectListItem objects from grant plus context
   and applies the portal-owned R15 `display_name.casefold()`/UUID order
   without changing the displayed name. Registry is
   never treated as the source of that order.
5. Opening a project repeats `authorize_project_read`; archived context is
   accepted for reads. It then builds ProjectOverview.

If Registry is temporarily unavailable for a list item, the portal does not
fabricate its display name/address. The list operation either reports the
dependency failure or, if a partial-list product policy is later approved,
must gain an explicit per-item failure model first. This pass chooses
fail-closed whole-list behavior because no partial-result model exists.

### Revocation

Revoking one ProjectViewerGrant commits grant state and audit atomically. The
next guard rejects only that project. Revoking the viewer or link invalidates
all viewer sessions immediately while retaining grant/history records.

## F4. Producer snapshot import

```text
service credential + SnapshotPublication
→ service_identity authentication/scope
→ Registry validate
→ snapshot content/fingerprint decision
→ snapshot/import record/audit transaction
→ SnapshotImportRecord
```

1. `service_identity` resolves credential hash to ServiceActorContext and
   rejects disabled principal, expired/revoked credential, or wrong source
   type without exposing credential details.
2. `snapshot_import` asks `service_identity` for producer scope before content
   validation. Scope denial produces a rejected SnapshotImportRecord and
   rejection audit; no snapshot is stored.
3. `registry_gateway.validate_project_reference` runs outside a portal
   transaction and requires matching active UUID. Missing/archived/failure
   maps to the appropriate import rejection/boundary failure; it never becomes
   a standalone import.
4. `snapshot_import` validates contract version, complete/unique sections,
   EUR amounts through `financial_policy`, and computes the canonical content
   fingerprint.
5. Inside one transaction it checks the identity tuple:
   - absent: append ApprovedEstimateSnapshot, accepted SnapshotImportRecord,
     and success AuditRecord;
   - same fingerprint: append idempotent-replay SnapshotImportRecord and
     audit, return existing snapshot ID;
   - different fingerprint: append integrity-conflict SnapshotImportRecord
     and rejection audit, store no snapshot mutation.
6. Database uniqueness races are re-read and classified by the same identity/
   fingerprint rule, never exposed as a generic success.
7. Import never calls budget activation and the producer context cannot carry
   `estimate_snapshot.activate`.

Every outcome preserves principal ID, key version, estimate identity,
contract version, fingerprint, and occurred time through typed records.

## F5. Human budget activation and section mapping

1. Staff session passes `authorize_project_mutation` with
   `estimate_snapshot.activate`; Registry active validation completes before
   the transaction.
2. `budget_management` loads the target inactive imported BudgetVersion,
   immutable snapshot sections, current PortalSections, active version, and
   allocations/progress references relevant to the switch.
3. For every snapshot section, equal non-null `source_key` reuses the existing
   PortalSection. An unmatched key creates a new PortalSection. Display name
   never participates in identity matching.
4. The module creates immutable imported SectionPlans, identifies previous
   section references absent from the new active version, and derives the
   unresolved allocation set; it does not rewrite allocations automatically.
5. Target activation, previous-version deactivation, plans/sections, and one
   `snapshot.activate` AuditRecord commit atomically. A concurrent activation
   conflict aborts and returns an explicit conflict; ≤1 active remains true.
6. Success returns the active BudgetVersion/BudgetView plus unresolved count.
   It never deletes manual budget, expenses, payments, photos, sections, or
   history.

## F6. OCR expense intake, replay, and correction

### Create/replay

1. `expense_intake` receives the external confirmed normalized payload plus
   operator project/allocation choices. The API does not allow a manual
   expense-create substitute.
2. The adapter requires supported contract version, confirmed status,
   complete normalized items, stable recognized_document_id and document
   reference; it discards confidence/provider/raw response fields.
3. Staff authorization and Registry active validation finish before the
   transaction. `financial_policy` validates EUR/two-digit total and amounts;
   `budget_management` validates section IDs belong to the project;
   `expense_management` checks positive explicit allocations and exact sum.
4. If recognized_document_id is new, Expense, all ExpenseAllocations, exactly
   one ExpenseDocument, and `expense.create` audit commit atomically.
5. `expense_intake` computes the canonical `intake_fingerprint`. If the ID
   already exists with the same fingerprint, the flow returns the existing
   Expense/Document without inserting or double-auditing a create. A different
   fingerprint is an integrity conflict and changes nothing.

### Amount/allocation correction

1. Authorized staff supplies corrected amount and a complete replacement
   allocation set; automatic proportional generation is unavailable.
2. `expense_management` validates same-project targets and exact sum before
   mutation.
3. Expense amount, all replacement allocations, timestamps/provenance, and
   one correction/allocation AuditRecord commit atomically. Any invalid target,
   sum, or concurrency conflict rolls back the entire change.
4. Include/exclude changes retain the Expense and document; derived totals
   change only because `derived_views` filters confirmed `included=true`
   records.

## F7. Authorized document/photo binary access

This flow resolves the State 3 transport choice: the portal streams bytes;
there is no signed/provider URL.

```text
session + document_id/photo_id
→ authorization_guard
→ expense_management/photo_management eligibility
→ binary_storage read by hidden file_ref
→ BinaryPayload
→ API binary stream
```

1. The client addresses a portal-owned object ID, never `file_ref`.
2. The guard rechecks active session/principal/grant-or-assignment and project
   read capability. Archived projects remain readable.
3. The owning module loads the record scoped to the authorized project and
   requires client-visible eligibility. Only it may reveal `file_ref`
   internally to `binary_storage`.
4. `binary_storage` rejects unsafe/unknown references, absent objects, invalid
   metadata, and content above `binary_max_read_bytes`; it never fetches an
   arbitrary URL. Success returns BinaryPayload with exact length.
5. `api` emits the bytes/media type/download name. It does not serialize
   content into ordinary JSON and never exposes the hidden reference.
6. Storage/read failure changes no business record and never becomes empty
   bytes. Hiding a document/photo immediately blocks later reads but does not
   delete the source object.

## F8. Deterministic project overview

1. Viewer or staff passes `authorize_project_read`; live ProjectContext is
   fetched from Registry. Archived is readable; missing/inaccessible fails.
2. `portal_store` supplies typed active budget/plans, expenses/allocations/
   documents, progress, payments, and visible photos scoped by project.
3. `financial_policy` computes all R9 values and explicit unavailable results.
   `derived_views` projects the concrete DTOs added to `10_models.md` and
   applies their deterministic tie-break orders.
4. No active budget yields `budget_availability=not_configured`; dependent
   progress is likewise not configured. Confirmed empty expense/payment/photo
   sets remain `available` with empty lists and exact zero totals.
5. A Registry failure fails the entire overview because live project context
   is mandatory. A failure in portal-owned reads produces
   `temporarily_unavailable` only for a component when the failure boundary is
   isolated and known; it never inserts zero/empty data as a fallback.
6. The same accepted records and context produce the same financial/progress
   values and ordering. No total is persisted or edited.

Observable success is ProjectOverview, never a generic dictionary.

## F9. Audit success and rejection paths

- The owning use case selects one closed R13 action and supplies actor,
  project, entity, result, and reason evidence to `audit_writer`.
- Successful significant mutations include AuditRecord in their business
  transaction. Audit construction/persistence failure rolls back success.
- A rejection known before a business transaction writes one rejected audit
  in a new short transaction. Failure to persist that audit is surfaced to
  operational error handling and never converted to an unaudited success.
- Authentication failures are audited without plaintext credentials or
  account-existence disclosure. Service actions include key_version.
- Idempotent replay is not a second business creation; snapshot replay has its
  own SnapshotImportRecord/audit outcome, while expense/payment/photo replay
  returns existing state and must not fabricate a second create action.
- AuditRecord and SnapshotImportRecord are append-only; corrections reference
  new business actions rather than editing history.

## Adapter and boundary inventory exposed by flows

- API credential/request decoding → typed identity/domain inputs.
- `registry_gateway` HTTP decoder/error translator → ProjectReference,
  ProjectValidationResult, ProjectContext, RegistryFailureKind.
- `email_delivery_gateway` provider translator → EmailDeliveryRecord outcome.
- OCR wire adapter → ExpenseIntake; forbidden source fields terminate there.
- `binary_storage` opaque reference resolver → BinaryPayload.
- `portal_store` ORM/database translator → typed aggregates and conflicts.

No adapter performs authorization, formulas, lifecycle decisions, audit
selection, or fallback fabrication.

## Backward corrections

Applied before accepting State 4:

- State 0: JSON application API plus one authenticated binary-stream response;
  no exposed file reference/provider URL.
- State 1: StaffProjectAssignment, trusted authentication/authorization
  contexts, concrete ProjectOverview component DTOs, BinaryPayload, OCR
  `file_ref`, and persisted `intake_fingerprint`.
- State 2: INV-017, staff-assignment revocation/audit entries, and R14 binary
  delivery policy with required deployment size limit; R8/INV-030 now define
  identical versus conflicting expense replay.
- State 3: staff assignment ownership and the selected streaming boundary.

## Placeholder-resistance review

- Every flow ends in a named entity/DTO or explicit failure; none promises a
  generic result.
- Network I/O and database transactions are separated explicitly.
- API handlers cannot complete a flow by forwarding input or returning empty
  data; each observable result has a producing module.
- Registry failures never become standalone/client-supplied context.
- Binary access cannot succeed from `file_ref` possession.
- Derived views cannot replace unavailable values with zero or unordered
  generic lists.
- Audit cannot be appended as best-effort after a successful commit.

## State 4 readiness assessment

Major identity, Registry, snapshot, budget, expense, binary, view, and audit
flows now expose their model crossings, decision owners, transaction
boundaries, failure translators, and observable results. The OCR replay gap
was repaired in State 1/2. State 4 is ready; State 5 may define the narrow
public module APIs without inventing new domain behavior.
