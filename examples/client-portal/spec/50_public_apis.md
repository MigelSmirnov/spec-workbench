# State 5 — Public module APIs

## Status

**Authoring pass State 5. Public operations are derived from `40_flows.md`.
This state fixes ownership, callers, typed inputs/outputs, effects, invariant
coverage, and rejection forms. Exact Python signatures and private helpers are
deferred to State 6.**

State 5 consolidates the former `staff_auth` and `email_challenges` candidates
into one deep `staff_identity` module. Their split created a public dependency
cycle around account creation, verification, email change, and password reset;
the merged module hides that sequencing while `email_delivery_gateway` remains
a delivery-only adapter.

## API selection rules

- `imports.internal` exports only symbols required by another module.
- Framework route handlers are not internal APIs. `api` exports only
  `create_app`.
- Public operations receive trusted actor/access contexts produced by identity
  and guard modules; they never accept role, capability, actor ID, Registry
  context, or `file_ref` as caller authority.
- Mutation outputs are concrete entities/aggregates. `None`, boolean success,
  empty models, and universal `Result` wrappers are not accepted outputs.
- Business rejections are named below. State 6 will declare exact exception
  classes; there is no generic `ApiError` domain model.
- `PortalStore` is the single concrete persistence facade supported by the
  current Factory profile. Only the class symbol is imported; raw sessions,
  ORM classes, and generic CRUD functions are never exported.

## Stable rejection families

These names describe distinct observable failures without fixing HTTP status
codes yet:

| Failure | Owner | Meaning |
| --- | --- | --- |
| `AuthenticationRejected` | identity module + authorization policy | existence-hiding invalid/unusable credential or session |
| `AuthorizationRejected` | `authorization_guard` | principal lacks active scope/capability; inaccessible project is not disclosed |
| `RegistryBoundaryError` | `registry_gateway` | carries one RegistryFailureKind from R6 |
| `ArchivedProjectRejected` | `authorization_guard` | accessible project is archived and mutation is forbidden |
| `ChallengeRejected` / `ChallengeRateLimited` | `staff_identity` | invalid lifecycle/purpose/replay or R10 issuing limit |
| `IdentityInputRejected` | `staff_identity` | email/password violates closed R16 policy |
| `DomainValidationRejected` | owning domain module | named field/rule violation, never arbitrary prose |
| `DomainConflict` | owning domain module | uniqueness, stale state, active-version, or conflicting replay |
| `BinaryAccessRejected` | expense/photo owner | object not in authorized project or not client-visible |
| `BinaryStorageError` | `binary_storage` | unsafe/missing/oversize/unreadable source object |
| `EmailDeliveryError` | `email_delivery_gateway` | provider/timeout failure; never invalidates challenge |
| `PersistenceError` | `portal_store` | translated database failure; never exposed as success |

State 6 must refine `DomainValidationRejected` and `DomainConflict` into
module-owned exception classes/codes wherever callers need different handling.
They are headings here, not permission for a free-form error container.

## Public operations by module

### `credential_security`

| Operation | Callers | Input → output | Effect / enforced policy | Rejections |
| --- | --- | --- | --- | --- |
| `hash_password` | `staff_identity` | R16-accepted plaintext password → password hash | Applies configured scheme; never logs/retains plaintext | hashing failure |
| `verify_password` | `staff_identity` | plaintext + stored hash → bool | Constant-time supported-scheme verification | malformed/unsupported hash is false plus operational evidence, never account disclosure |
| `issue_verification_secret` | staff/viewer/service identity modules | record UUID + entropy bytes → IssuedSecret | Encodes selector + random secret; plaintext returned once, hash persists elsewhere | entropy source failure |
| `parse_verification_secret` | staff/viewer/service identity modules | opaque token → PresentedSecret | Extracts UUID selector and random secret; selector is never proof | malformed token becomes AuthenticationRejected/ChallengeRejected |
| `verify_secret` | staff/viewer/service identity modules | plaintext + stored hash → bool | Constant-time verification; no lifecycle decision | malformed hash/secret returns false |

Primary invariant: INV-003. No API/router calls this module directly.

### `staff_identity`

| Operation | Callers | Input → output | Effect / enforced policy | Rejections |
| --- | --- | --- | --- | --- |
| `create_staff_account` | `api` after access-management guard | admin context + email + initial password + StaffRole → StaffAccount | Creates pending account, verification challenge/delivery record and audit atomically; delivery attempted after commit | email conflict, invalid role/password, persistence; delivery failure is telemetry |
| `authenticate_staff` | `api` | email + password → StaffSessionGrant | Verifies active/verified account, creates hashed session and login audit | AuthenticationRejected |
| `resolve_staff_session` | `api`, `authorization_guard` | session plaintext → StaffActorContext | Resolves unexpired/unrevoked session and current account | AuthenticationRejected |
| `sign_out_staff` | `api` | StaffActorContext → StaffSession | Revokes current session and audits | already-invalid session uses AuthenticationRejected |
| `revoke_staff_sessions` | `api` after proper authorization | StaffActorContext + target staff ID → list[StaffSession] | Revokes all target sessions atomically and audits | not found in authorized area, persistence |
| `change_staff_status` | `api` after access-management guard | admin context + staff ID + StaffStatus → StaffAccount | Enforces R3/R11; suspension/disable revokes sessions/challenges; notice after commit | invalid transition, target not found |
| `change_staff_password` | `api` | StaffActorContext + current/new password → StaffAccount | Verifies current secret, replaces hash, audits, sends notice after commit | AuthenticationRejected, invalid password |
| `assign_staff_project` | `api` after access-management guard | admin context + operator ID + project ID → StaffProjectAssignment | Registry active validation precedes atomic unique assignment/audit | RegistryBoundaryError, role mismatch, DomainConflict |
| `revoke_staff_project_assignment` | `api` after access-management guard | admin context + assignment ID → StaffProjectAssignment | Revokes immediately and audits | not found, already revoked |
| `issue_email_verification` | `api` after access-management guard | admin context + staff ID → ChallengeIssueView | R10 issue/revoke/rate-limit, delivery request and audit; no token/hash output | ChallengeRateLimited, invalid account state |
| `confirm_email_verification` | `api` | token plaintext → StaffAccount | Consumes once; verifies email and activates pending account atomically | ChallengeRejected |
| `request_email_change` | `api` | StaffActorContext + new email → ChallengeIssueView | Rechecks uniqueness, replaces outstanding change, requests delivery; no token/hash output | email conflict, ChallengeRateLimited |
| `confirm_email_change` | `api` | token plaintext → StaffAccount | Consumes once, changes login email, audits; old-address notice after commit | ChallengeRejected, email conflict |
| `request_password_reset` | `api` | email → None | Existence-hiding acceptance; eligible account gets token/delivery, all callers see same success | only infrastructure failure may escape; policy remains awaiting confirmation |
| `complete_password_reset` | `api` | token plaintext + new password → StaffAccount | Consumes token, changes hash, revokes sessions/other tokens, audits, then notice | ChallengeRejected, invalid password |
| `perform_recovery_override` | `api` after administrator/deployment authorization | admin context + target + replacement email → StaffAccount | Exceptional enhanced-audit path; never primary email change | authorization, conflict, invalid target state |

Primary invariants: INV-010–INV-019; supports INV-003/004 through security and
failure policy. Notification helper sequencing remains private.

### `viewer_access`

| Operation | Callers | Input → output | Effect / policy | Rejections |
| --- | --- | --- | --- | --- |
| `create_viewer` | `api` after access-management guard | staff context + display name → ClientViewer | Creates active viewer and audit | invalid name, persistence |
| `revoke_viewer` | same | staff context + viewer ID → ClientViewer | Terminal revoke; invalidates credential/sessions, audits | not found/already revoked |
| `issue_viewer_access` | same | staff context + viewer ID → ViewerCredentialIssue | Atomically revokes previous credential, issues once, audits | inactive/not found viewer |
| `revoke_viewer_access` | same | staff context + credential ID → ViewerAccessCredential | Revokes credential and viewer sessions, audits | not found/already revoked |
| `enter_viewer_access` | `api` | capability secret → ViewerSessionGrant | Verifies active viewer/current credential; persists hashed session | AuthenticationRejected |
| `resolve_viewer_session` | `api`, guard, derived views | session plaintext → ViewerActorContext | Resolves current active viewer session | AuthenticationRejected |
| `grant_viewer_project` | `api` after access-management guard | staff context + viewer ID + project ID → ProjectViewerGrant | Registry validation before unique grant/audit transaction | RegistryBoundaryError, conflict/inactive viewer |
| `revoke_viewer_project` | same | staff context + grant ID → ProjectViewerGrant | Revokes one project only and audits | not found/already revoked |
| `list_viewer_project_grants` | `derived_views` | ViewerActorContext → list[ProjectViewerGrant] | Returns active grants only; no Registry context | AuthenticationRejected |

### `service_identity`

| Operation | Callers | Input → output | Effect / policy | Rejections |
| --- | --- | --- | --- | --- |
| `create_service_principal` | `api` after access-management guard | admin context + name + source type + scope mode → ServicePrincipal | Creates named principal and audits | invalid closed choice/conflict |
| `change_service_principal_status` | same | admin context + principal ID + PrincipalStatus → ServicePrincipal | Applies R3/R11 and audits | invalid transition/not found |
| `issue_service_credential` | same | admin context + principal ID + optional expiry → ServiceCredentialIssue | Allocates monotonic key version, one-time secret, audit | inactive/not found principal |
| `revoke_service_credential` | same | admin context + credential ID → ServiceCredential | Revokes only that key and audits | not found/already revoked |
| `grant_producer_project` / `revoke_producer_project` | same | admin context + principal/project or grant ID → ProducerProjectGrant | Registry validation on grant; unique/revocable scope and audit | RegistryBoundaryError, conflict/not found |
| `authenticate_service_principal` | `api` snapshot boundary | credential plaintext → ServiceActorContext | Resolves active principal, key version, source/scope | AuthenticationRejected |
| `authorize_producer_scope` | `snapshot_import`, guard | ServiceActorContext + project ID → bool | Applies R12; never validates snapshot content | AuthorizationRejected |

### `authorization_guard`

| Operation | Callers | Input → output | Policy | Rejections |
| --- | --- | --- | --- | --- |
| `conceal_authentication_failure` | identity modules | private failure cause → AuthenticationRejected | Erases existence-sensitive distinctions without logging secrets | none |
| `authorize_staff_project_read` | `api`, derived views | StaffActorContext + project ID + read Capability → AuthorizedProjectContext | Full R4 with assignment/single-area admin and Registry readable state | AuthenticationRejected, AuthorizationRejected, RegistryBoundaryError |
| `authorize_viewer_project_read` | `api`, derived views | ViewerActorContext + project ID + read Capability → AuthorizedProjectContext | Full R4; active viewer grant; archived read allowed | same |
| `authorize_staff_project_mutation` | mutation entry points | StaffActorContext + project ID + manage/activate Capability → AuthorizedProjectContext | Full R4; Registry must be active | same + ArchivedProjectRejected |
| `authorize_access_management` | access-management routes | StaffActorContext → StaffActorContext | Requires active administrator and R2 access.manage | AuthenticationRejected, AuthorizationRejected |
| `authorize_snapshot_import` | `snapshot_import` | ServiceActorContext + project ID → AuthorizedProjectContext | R2/R12 plus matching active Registry validation | AuthorizationRejected, RegistryBoundaryError, ArchivedProjectRejected |

These operations own INV-001/002/004–007 and PLAT-REG-003. There is no
generic actor-union API because the current Factory profile does not
materialize that representation.

### Integration gateways

| Module.operation | Callers | Input → output | Boundary guarantee | Rejections |
| --- | --- | --- | --- | --- |
| `registry_gateway.list_active_projects` | staff selection use cases | none → list[ProjectReference] | Typed decode; deterministic R15 UUID order, no pagination claim | RegistryBoundaryError |
| `registry_gateway.validate_project_reference` | guard and linked creates | project ID → ProjectValidationResult | R6 translation and UUID equality | RegistryBoundaryError |
| `registry_gateway.get_project_context` | guard/derived views | project ID → ProjectContext | Live typed context for active or archived | RegistryBoundaryError |
| `email_delivery_gateway.deliver_email_message` | `staff_identity` | EmailDeliveryRequest → EmailDeliveryRecord | Delivery telemetry only; consumes plaintext immediately | EmailDeliveryError |
| `binary_storage.read_binary` | expense/photo owners after eligibility | AuthorizedBinaryReference → BinaryPayload | R14 safe opaque read and size bound | BinaryStorageError |

### `snapshot_import`

| Operation | Callers | Input → output | Effect / policy | Rejections |
| --- | --- | --- | --- | --- |
| `import_snapshot` | `api` producer route | ServiceActorContext + SnapshotPublication → SnapshotImportRecord | Owns scope/Registry/content order, fingerprint, append/replay/conflict record and audit | Authentication/authorization/Registry infrastructure failures; business rejection is typed in SnapshotImportRecord |
| `get_snapshot_import_result` | `api` producer route | ServiceActorContext + import ID → SnapshotImportRecord | Requires read-import capability and same principal/scope | AuthorizationRejected, not found without cross-principal disclosure |

### `budget_management`

| Operation | Callers | Input → output | Effect / policy | Rejections |
| --- | --- | --- | --- | --- |
| `ensure_manual_budget` | `api` | AuthorizedProjectContext → BudgetVersionDetail | Creates at most one manual version or returns existing; creation audits | wrong capability/state, conflict |
| `upsert_manual_section_plan` | `api` | authorized context + optional section ID + name/order/amounts → BudgetVersionDetail | Creates/updates only manual plan; validates EUR; audits | invalid amount/section, imported/archived mutation |
| `get_budget_version` | `api`, snapshot review | authorized read context + version ID → BudgetVersionDetail | Typed historical read scoped to project | not found/inaccessible |
| `activate_budget_version` | `api` | authorized activate context + version ID → BudgetActivationResult | Atomic source-key linking, plan creation, switch, unresolved count, audit | inactive/foreign version, concurrency conflict |
| `validate_project_section` | expense/tracking/photo modules | project ID + section ID → PortalSection | Confirms stable same-project identity; no mutation | not found/cross-project |

Plan deletion is intentionally absent: referenced PortalSections cannot be
deleted, and product semantics for removing an unreferenced manual plan have
not been approved.

### `expense_intake` and `expense_management`

| Operation | Callers | Input → output | Effect / policy | Rejections |
| --- | --- | --- | --- | --- |
| `create_expense_from_recognition` | `api` OCR route | authorized manage context + ConfirmedRecognitionPublication + list[AllocationInstruction] → ExpenseAggregate | Projects to ExpenseIntake, canonical fingerprint, atomic aggregate/audit; equal replay returns replayed aggregate | unsupported contract/status/currency, allocation mismatch, DomainConflict |
| `correct_expense` | `api` | authorized context + expense ID + corrected facts + complete allocations → ExpenseAggregate | Atomic amount/facts/allocation replacement and audit | not found, allocation/currency/concurrency rejection |
| `set_expense_inclusion` | `api` | authorized context + expense ID + bool → ExpenseAggregate | Updates inclusion without deletion and audits; returns complete aggregate for safe projection | not found/concurrency |
| `replace_expense_allocations` | `api` | authorized context + expense ID + instructions → ExpenseAggregate | Exact explicit sum, same-project sections, audit | mismatch/cross-project/concurrency |
| `update_expense_document` | `api` | authorized context + document ID + description/visibility → ExpenseDocument | Updates metadata only and audits | not found/concurrency |
| `read_expense_document` | `api` binary route | AuthorizedProjectContext + document ID → BinaryPayload | Builds AuthorizedBinaryReference only after scoped visibility, then delegates storage read | BinaryAccessRejected, BinaryStorageError |

`accept_expense_intake` becomes private inside `expense_intake`; exposing it
would let callers bypass OCR boundary validation/fingerprinting.

### `project_tracking`

| Operation | Callers | Input → output | Effect / policy | Rejections |
| --- | --- | --- | --- | --- |
| `set_section_progress` | `api` | authorized context + section ID + percent → SectionProgress | Manual 0–100 update, same-project validation, audit | invalid range/section/concurrency |
| `register_work_payment` | `api` | authorized context + payment fields → WorkPayment | EUR validation, payment-ID idempotency, audit on new registration | conflicting replay/invalid amount |
| `list_project_progress` | `derived_views` | authorized read context → list[SectionProgress] | Typed project-scoped records | persistence |
| `list_project_payments` | `derived_views` | authorized read context → list[WorkPayment] | Typed project-scoped records | persistence |

### `photo_management`

| Operation | Callers | Input → output | Effect / policy | Rejections |
| --- | --- | --- | --- | --- |
| `publish_progress_photo` | `api` intake route | authorized context + PhotoPublication → PhotoMutationResult | Intake-ID idempotency, same-project section, audit; no file_ref output | conflicting replay/section mismatch |
| `update_progress_photo` | `api` | authorized context + photo ID + caption/section/visibility → PhotoMutationResult | Metadata-only update; never progress/finance, audit; no file_ref output | not found/section/concurrency |
| `list_progress_photos` | `derived_views` | authorized read context → list[ProgressPhoto] | Visible/scoped records in deterministic order | persistence |
| `read_progress_photo` | `api` binary route | authorized read context + photo ID → BinaryPayload | Requires visible same-project photo, then delegates storage read | BinaryAccessRejected, BinaryStorageError |

### `financial_policy`

Pure cross-module operations, all deterministic candidates:

| Operation | Input → output | Callers | Enforces |
| --- | --- | --- | --- |
| `validate_eur_amount` | currency + Decimal → Decimal | snapshot/expense/budget/payment modules | EUR, non-negative/positive mode, 2 digits |
| `calculate_completed_work` | planned work + percent → Decimal | derived views | R9 per-section rounding |
| `calculate_overall_progress` | list[ProgressSectionView] → Decimal or None | derived views | weighted formula/unavailable denominator |
| `calculate_material_balance` | planned + actual → Decimal | derived views | negative overspend preserved |
| `calculate_work_balance` | completed + payments → WorkBalanceResult | derived views | R9 sign/label semantics |

Invalid amounts raise a specific financial validation rejection; these
functions perform no I/O and return no fallback.

### `derived_views`

| Operation | Callers | Input → output | Guarantee | Rejections |
| --- | --- | --- | --- | --- |
| `list_viewer_projects` | `api` | ViewerActorContext → list[ProjectListItem] | Active grants + live Registry context; fail-closed whole list; R15 name/UUID order | AuthenticationRejected, RegistryBoundaryError |
| `build_project_overview` | `api` | AuthorizedProjectContext → ProjectOverview | Concrete availability states, deterministic projections/formulas | persistence/Registry failure; no fabricated zero |
| `build_budget_view` | `api`, budget activation | authorized context + version selector → BudgetView | Stable section order and derived totals | not configured/not found |
| `build_expense_view` | `api` | authorized context → ExpenseSummaryView | Included/excluded/other totals and stable order | persistence |
| `build_progress_view` | `api` | authorized context → ProgressView | R9 formulas and explicit None denominator | not configured/persistence |
| `build_payment_view` | `api` | authorized context → PaymentSummaryView | Total/balance/label and stable payment order | persistence |

Photo projection is part of ProjectOverview; a separate client gallery route
may call `photo_management.list_progress_photos` and project to `PhotoView`
inside `derived_views` during State 6 if the route is retained.

### `audit_writer`

| Operation | Callers | Input → output | Effect | Rejections |
| --- | --- | --- | --- | --- |
| `append_audit` | all significant mutation owners | AuditIntent → AuditRecord | Supplies ID/time, validates R13/provenance, appends exactly once inside caller transaction | invalid closed choice, PersistenceError |

Separate success/rejection functions are removed; AuditIntent already encodes
the closed result choice. The operation never commits independently when it is
part of a successful business mutation.

### `portal_store`

Public exports are concrete `PortalStore` and `PortalTransaction` classes. Their domain-specific methods
are used only by owning modules and will receive exact contracts in State 6.
The accepted surface is:

```text
identity loads:       load staff/viewer/service by normalized identity or hash
scope loads:          load active assignment/grant/scope records
aggregate loads:      load budget, expense, tracking, photo, audit/import facts
atomic commits:       commit one owning use-case mutation plus AuditRecord
append-only commits:  append snapshot/import/audit records without update/delete
read projections:     typed project-scoped record collections
```

Rejected public shapes: `save(data)`, `get(id) -> object`, generic CRUD,
caller-owned SQLAlchemy session, raw rows, arbitrary query predicates, or a
transaction context exposed to `api`. State 6 must name every class method;
any method not required by an accepted operation above remains private.

### `api`

`create_app` is the sole internal export. Route handlers:

- decode HTTP inputs into declared models/primitives;
- resolve credentials through the appropriate identity module;
- obtain trusted authorization contexts from the guard;
- call exactly one owning use case or read builder;
- translate named failures to stable HTTP responses;
- stream BinaryPayload for the two binary resource routes.

They do not appear in `imports.internal` and own no policy, transaction,
formula, storage read, Registry interpretation, or audit call.

## Stable `imports.internal` draft

```text
models                 → all declared model/enum/catalog symbols
credential_security    → hash_password, verify_password,
                         issue_verification_secret, parse_verification_secret,
                         verify_secret
staff_identity         → accepted staff account/session/challenge/assignment
                         operations above
viewer_access          → accepted viewer/session/credential/grant operations
service_identity       → accepted principal/credential/scope operations
authorization_guard    → conceal_authentication_failure and five typed guards
registry_gateway       → list_active_projects,
                         validate_project_reference, get_project_context
email_delivery_gateway → deliver_email_message
binary_storage         → read_binary
snapshot_import        → import_snapshot, get_snapshot_import_result
budget_management      → ensure_manual_budget, upsert_manual_section_plan,
                         get_budget_version, activate_budget_version,
                         validate_project_section
expense_intake         → create_expense_from_recognition
expense_management     → correct_expense, set_expense_inclusion,
                         replace_expense_allocations, update_expense_document,
                         read_expense_document
project_tracking       → set_section_progress, register_work_payment,
                         list_project_progress, list_project_payments
photo_management       → publish_progress_photo, update_progress_photo,
                         list_progress_photos, read_progress_photo
financial_policy       → five pure financial operations
derived_views          → six concrete read builders
audit_writer           → append_audit
portal_store           → PortalStore, PortalTransaction
api                    → create_app
```

## Preliminary adapter requirements

- HTTP request models → exact operation inputs; never role/capability/context.
- ConfirmedRecognitionPublication + operator allocation fields →
  `create_expense_from_recognition`; no `dict` payload.
- EmailDeliveryRequest is consumed once by the email provider adapter.
- AuthorizedBinaryReference is the only adapter input containing `file_ref`.
- Registry gateway alone converts HTTP response/error shapes into typed models
  or RegistryBoundaryError.
- PortalStore alone converts ORM/database shapes and conflicts.

## Placeholder-resistance review

- Removing any accepted operation would force a caller to duplicate owned
  policy or access private persistence/integration details.
- Candidate pass-through operations were removed or privatized:
  `accept_expense_intake`, binary `describe`, separate audit success/rejection,
  framework handlers, and generic store CRUD.
- Every return is a concrete model, typed list, Decimal/boolean predicate, or
  explicit no-content command. No empty generic result can represent success.
- Every mutation names its authorization context, state effect, audit
  boundary, and rejection owner.
- Identity-specific guard operations avoid an unsupported union/optional
  envelope.

## State 5 readiness assessment

Every public operation has one owner, known callers, typed inputs/outputs,
observable effects, invariant/policy coverage, and named failures. Public
surfaces are smaller than module internals, the API remains thin, and the
persistence facade cannot become generic CRUD. The design is ready for State 6
exact contracts and private-function discovery, subject to re-confirming the
previously proposed session/reset/config values before State 8 assembly.
