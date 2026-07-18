# State 6 — Exact contracts and internal functions

## Status

**Authoring pass State 6. All accepted State 5 public operations now have
exact Python signatures. Private helpers are included only where they hide
policy, canonicalization, projection, or integration translation. Contracts
use builtins, declared models, module-owned classes, and explicit imports;
there is no `Any`, untyped `dict`, Callable callback, raw ORM session, or
unsupported union.**

## Type origins

```text
stdlib imports:
  from datetime import date, datetime
  from decimal import Decimal
  from uuid import UUID

third-party imports:
  from fastapi import FastAPI

internal class types:
  portal_store.PortalStore
  portal_store.PortalTransaction

all remaining capitalized types:
  declared in models, except the module-owned exception classes below
```

Every nullable form is `X | None`, which is supported field/contract syntax.
No signature uses an untagged multi-variant union.

## Exception class contracts

Exceptions carry no arbitrary payload. A distinct class is used when callers
need distinct handling.

```python
AuthenticationRejected.__init__(self) -> None
AuthorizationRejected.__init__(self) -> None
ArchivedProjectRejected.__init__(self) -> None
ChallengeRejected.__init__(self) -> None
ChallengeRateLimited.__init__(self) -> None
IdentityInputRejected.__init__(self) -> None
ScopedNotFoundError.__init__(self) -> None
RegistryBoundaryError.__init__(self, kind: RegistryFailureKind) -> None
BudgetValidationError.__init__(self) -> None
BudgetConflictError.__init__(self) -> None
ExpenseValidationError.__init__(self) -> None
ExpenseConflictError.__init__(self) -> None
TrackingValidationError.__init__(self) -> None
TrackingConflictError.__init__(self) -> None
PhotoValidationError.__init__(self) -> None
PhotoConflictError.__init__(self) -> None
FinancialValidationError.__init__(self) -> None
BinaryAccessRejected.__init__(self) -> None
BinaryStorageError.__init__(self) -> None
EmailDeliveryError.__init__(self) -> None
PersistenceError.__init__(self) -> None
```

Ownership:

- authentication/authorization exceptions — `authorization_guard`;
- challenge/identity exceptions — `staff_identity`;
- Registry/email/binary/persistence exceptions — their adapter modules;
- budget/expense/tracking/photo/financial exceptions — corresponding domain
  modules;
- `ScopedNotFoundError` — `authorization_guard`; it reveals no inaccessible
  entity kind or project.

## Exact public contracts

### `credential_security`

```python
hash_password(password: str) -> str
verify_password(password: str, password_hash: str) -> bool
issue_verification_secret(record_id: UUID, entropy_bytes: int) -> IssuedSecret
parse_verification_secret(token: str) -> PresentedSecret
verify_secret(secret: str, verification_hash: str) -> bool
```

Private:

```python
_hash_secret(secret: str) -> str
_constant_time_verify(secret: str, verification_hash: str) -> bool
_encode_secret_envelope(record_id: UUID, secret: str) -> str
```

### `staff_identity`

```python
create_staff_account(store: PortalStore, administrator: StaffActorContext, email: str, initial_password: str, role: StaffRole) -> StaffAccount
authenticate_staff(store: PortalStore, email: str, password: str) -> StaffSessionGrant
resolve_staff_session(store: PortalStore, token: str) -> StaffActorContext
sign_out_staff(store: PortalStore, actor: StaffActorContext) -> StaffSession
revoke_staff_sessions(store: PortalStore, administrator: StaffActorContext, staff_id: UUID) -> list[StaffSession]
change_staff_status(store: PortalStore, administrator: StaffActorContext, staff_id: UUID, new_status: StaffStatus) -> StaffAccount
change_staff_password(store: PortalStore, actor: StaffActorContext, current_password: str, new_password: str) -> StaffAccount
assign_staff_project(store: PortalStore, administrator: StaffActorContext, operator_id: UUID, project_id: UUID) -> StaffProjectAssignment
revoke_staff_project_assignment(store: PortalStore, administrator: StaffActorContext, assignment_id: UUID) -> StaffProjectAssignment
issue_email_verification(store: PortalStore, administrator: StaffActorContext, staff_id: UUID) -> ChallengeIssueView
confirm_email_verification(store: PortalStore, token: str) -> StaffAccount
request_email_change(store: PortalStore, actor: StaffActorContext, new_email: str) -> ChallengeIssueView
confirm_email_change(store: PortalStore, token: str) -> StaffAccount
request_password_reset(store: PortalStore, email: str) -> None
complete_password_reset(store: PortalStore, token: str, new_password: str) -> StaffAccount
perform_recovery_override(store: PortalStore, administrator: StaffActorContext, staff_id: UUID, replacement_email: str) -> StaffAccount
```

Private:

```python
_normalize_staff_email(email: str) -> str
_validate_new_password(password: str) -> None
_build_staff_session(staff: StaffAccount, issued: IssuedSecret, created_at: datetime, expires_at: datetime) -> StaffSession
_build_email_delivery_request(record: EmailDeliveryRecord, token: str | None) -> EmailDeliveryRequest
_build_challenge_issue_view(challenge_ref: UUID, expires_at: datetime, delivery: EmailDeliveryRecord) -> ChallengeIssueView
_issue_challenge(tx: PortalTransaction, staff: StaffAccount, purpose: EmailMessageKind, requested_by: UUID, issued_at: datetime) -> EmailDeliveryRequest
_consume_email_verification(tx: PortalTransaction, token: str, consumed_at: datetime) -> StaffAccount
_consume_email_change(tx: PortalTransaction, token: str, consumed_at: datetime) -> StaffAccount
_consume_password_reset(tx: PortalTransaction, token: str, new_password_hash: str, consumed_at: datetime) -> StaffAccount
_deliver_after_commit(request: EmailDeliveryRequest) -> EmailDeliveryRecord
```

The three `_consume_*` helpers are separate because their state effects differ;
a generic token consumer would hide purpose binding.

### `viewer_access`

```python
create_viewer(store: PortalStore, administrator: StaffActorContext, display_name: str) -> ClientViewer
revoke_viewer(store: PortalStore, administrator: StaffActorContext, viewer_id: UUID) -> ClientViewer
issue_viewer_access(store: PortalStore, administrator: StaffActorContext, viewer_id: UUID) -> ViewerCredentialIssue
revoke_viewer_access(store: PortalStore, administrator: StaffActorContext, credential_id: UUID) -> ViewerAccessCredential
enter_viewer_access(store: PortalStore, secret: str) -> ViewerSessionGrant
resolve_viewer_session(store: PortalStore, token: str) -> ViewerActorContext
grant_viewer_project(store: PortalStore, administrator: StaffActorContext, viewer_id: UUID, project_id: UUID) -> ProjectViewerGrant
revoke_viewer_project(store: PortalStore, administrator: StaffActorContext, grant_id: UUID) -> ProjectViewerGrant
list_viewer_project_grants(store: PortalStore, actor: ViewerActorContext) -> list[ProjectViewerGrant]
```

Private:

```python
_build_viewer_session(viewer: ClientViewer, issued: IssuedSecret, created_at: datetime, expires_at: datetime) -> ViewerSession
_revoke_viewer_sessions(tx: PortalTransaction, viewer_id: UUID, revoked_at: datetime) -> list[ViewerSession]
```

### `service_identity`

```python
create_service_principal(store: PortalStore, administrator: StaffActorContext, name: str, source_type: ProducerSourceType, scope_mode: ProducerScopeMode) -> ServicePrincipal
change_service_principal_status(store: PortalStore, administrator: StaffActorContext, principal_id: UUID, new_status: PrincipalStatus) -> ServicePrincipal
issue_service_credential(store: PortalStore, administrator: StaffActorContext, principal_id: UUID, expires_at: datetime | None = None) -> ServiceCredentialIssue
revoke_service_credential(store: PortalStore, administrator: StaffActorContext, credential_id: UUID) -> ServiceCredential
grant_producer_project(store: PortalStore, administrator: StaffActorContext, principal_id: UUID, project_id: UUID) -> ProducerProjectGrant
revoke_producer_project(store: PortalStore, administrator: StaffActorContext, grant_id: UUID) -> ProducerProjectGrant
authenticate_service_principal(store: PortalStore, secret: str) -> ServiceActorContext
authorize_producer_scope(store: PortalStore, actor: ServiceActorContext, project_id: UUID) -> bool
```

Private:

```python
_next_key_version(tx: PortalTransaction, principal_id: UUID) -> int
_credential_is_usable(credential: ServiceCredential, principal: ServicePrincipal, checked_at: datetime) -> bool
```

### `authorization_guard`

```python
conceal_authentication_failure() -> AuthenticationRejected
authorize_staff_project_read(store: PortalStore, actor: StaffActorContext, project_id: UUID, capability: Capability) -> AuthorizedProjectContext
authorize_viewer_project_read(store: PortalStore, actor: ViewerActorContext, project_id: UUID, capability: Capability) -> AuthorizedProjectContext
authorize_staff_project_mutation(store: PortalStore, actor: StaffActorContext, project_id: UUID, capability: Capability) -> AuthorizedProjectContext
authorize_access_management(store: PortalStore, actor: StaffActorContext) -> StaffActorContext
authorize_snapshot_import(store: PortalStore, actor: ServiceActorContext, project_id: UUID) -> AuthorizedProjectContext
```

Private:

```python
_require_staff_scope(tx: PortalTransaction, actor: StaffActorContext, project_id: UUID) -> None
_require_viewer_grant(tx: PortalTransaction, actor: ViewerActorContext, project_id: UUID) -> None
_require_capability(actor_kind: ActorKind, role: StaffRole | None, source_type: ProducerSourceType | None, capability: Capability) -> None
_authorize_project_operation(store: PortalStore, request: ProjectAuthorizationRequest) -> AuthorizedProjectContext
_context_from_validation(actor_kind: ActorKind, actor_id: UUID, key_version: int | None, capability: Capability, validation: ProjectValidationResult) -> AuthorizedProjectContext
```

`_require_capability` uses nullable independent fields keyed by ActorKind, the
already adopted closed-choice encoding; it is not an untagged union.

### `registry_gateway`

```python
list_active_projects() -> list[ProjectReference]
validate_project_reference(project_id: UUID) -> ProjectValidationResult
get_project_context(project_id: UUID) -> ProjectContext
```

Private:

```python
_registry_url(path: str) -> str
_translate_registry_failure(project_id: UUID, failure: RegistryFailureKind) -> RegistryBoundaryError
_validate_reference_identity(requested_id: UUID, result: ProjectValidationResult) -> ProjectValidationResult
_validate_context_identity(requested_id: UUID, context: ProjectContext) -> ProjectContext
```

### `email_delivery_gateway`

```python
deliver_email_message(store: PortalStore, request: EmailDeliveryRequest) -> EmailDeliveryRecord
```

Private:

```python
_send_delivery_request(request: EmailDeliveryRequest) -> str
_record_delivery_failure(store: PortalStore, delivery_id: UUID) -> EmailDeliveryRecord
```

### `binary_storage`

```python
read_binary(reference: AuthorizedBinaryReference) -> BinaryPayload
```

Private:

```python
_resolve_safe_object_path(file_ref: str) -> str
_validate_binary_size(content_length: int) -> None
_read_object_bytes(object_path: str) -> bytes
```

The safe path is adapter-internal and is never returned to another module.

### `snapshot_import`

```python
import_snapshot(store: PortalStore, actor: ServiceActorContext, publication: SnapshotPublication) -> SnapshotImportRecord
get_snapshot_import_result(store: PortalStore, actor: ServiceActorContext, import_id: UUID) -> SnapshotImportRecord
```

Private:

```python
_validate_snapshot_publication(publication: SnapshotPublication) -> None
_canonical_snapshot_fingerprint(publication: SnapshotPublication) -> str
_classify_snapshot_replay(existing: ApprovedEstimateSnapshot, fingerprint: str) -> ImportOutcome
_build_approved_snapshot(publication: SnapshotPublication, actor: ServiceActorContext, fingerprint: str, received_at: datetime) -> ApprovedEstimateSnapshot
_build_import_record(publication: SnapshotPublication, actor: ServiceActorContext, outcome: ImportOutcome, reject_reason: ImportRejectReason | None, fingerprint: str, snapshot_id: UUID | None, occurred_at: datetime) -> SnapshotImportRecord
```

### `budget_management`

```python
ensure_manual_budget(store: PortalStore, context: AuthorizedProjectContext) -> BudgetVersionDetail
upsert_manual_section_plan(store: PortalStore, context: AuthorizedProjectContext, section_id: UUID | None, display_name: str, sort_order: int, material_planned: Decimal, work_planned: Decimal) -> BudgetVersionDetail
get_budget_version(store: PortalStore, context: AuthorizedProjectContext, version_id: UUID) -> BudgetVersionDetail
activate_budget_version(store: PortalStore, context: AuthorizedProjectContext, version_id: UUID) -> BudgetActivationResult
validate_project_section(store: PortalStore, project_id: UUID, section_id: UUID) -> PortalSection
```

Private:

```python
_link_snapshot_sections(existing_sections: list[PortalSection], snapshot_sections: list[SnapshotSectionData], actor_id: UUID, created_at: datetime) -> list[PortalSection]
_build_imported_plans(version: BudgetVersion, sections: list[PortalSection], snapshot_sections: list[SnapshotSectionData], created_at: datetime) -> list[SectionPlan]
_find_unresolved_allocation_count(active_section_ids: list[UUID], allocations: list[ExpenseAllocation]) -> int
_ordered_plans(plans: list[SectionPlan]) -> list[SectionPlan]
```

### `expense_intake`

```python
create_expense_from_recognition(store: PortalStore, context: AuthorizedProjectContext, publication: ConfirmedRecognitionPublication, allocations: list[AllocationInstruction]) -> ExpenseAggregate
```

Private:

```python
_project_expense_intake(context: AuthorizedProjectContext, publication: ConfirmedRecognitionPublication, allocations: list[AllocationInstruction]) -> ExpenseIntake
_canonical_intake_fingerprint(intake: ExpenseIntake) -> str
_validate_initial_allocations(store: PortalStore, intake: ExpenseIntake) -> None
_build_expense_aggregate(intake: ExpenseIntake, fingerprint: str, created_at: datetime) -> ExpenseAggregate
_classify_expense_replay(existing: ExpenseAggregate, fingerprint: str) -> ExpenseAggregate
```

### `expense_management`

```python
correct_expense(store: PortalStore, context: AuthorizedProjectContext, expense_id: UUID, supplier: str, document_date: date, total_amount: Decimal, included: bool, allocations: list[AllocationInstruction]) -> ExpenseAggregate
set_expense_inclusion(store: PortalStore, context: AuthorizedProjectContext, expense_id: UUID, included: bool) -> ExpenseAggregate
replace_expense_allocations(store: PortalStore, context: AuthorizedProjectContext, expense_id: UUID, allocations: list[AllocationInstruction]) -> ExpenseAggregate
update_expense_document(store: PortalStore, context: AuthorizedProjectContext, document_id: UUID, description: str | None, client_visible: bool) -> ExpenseDocument
read_expense_document(store: PortalStore, context: AuthorizedProjectContext, document_id: UUID) -> BinaryPayload
```

Private:

```python
_validate_allocation_sum(total_amount: Decimal, allocations: list[AllocationInstruction]) -> None
_build_replacement_allocations(expense: Expense, instructions: list[AllocationInstruction], actor_id: UUID, changed_at: datetime) -> list[ExpenseAllocation]
_authorize_document_reference(store: PortalStore, context: AuthorizedProjectContext, document_id: UUID) -> AuthorizedBinaryReference
```

### `project_tracking`

```python
set_section_progress(store: PortalStore, context: AuthorizedProjectContext, section_id: UUID, completion_percent: int) -> SectionProgress
register_work_payment(store: PortalStore, context: AuthorizedProjectContext, payment_id: UUID, amount: Decimal, payment_date: date, description: str) -> WorkPayment
list_project_progress(store: PortalStore, context: AuthorizedProjectContext) -> list[SectionProgress]
list_project_payments(store: PortalStore, context: AuthorizedProjectContext) -> list[WorkPayment]
```

Private:

```python
_validate_completion_percent(completion_percent: int) -> None
_classify_payment_replay(existing: WorkPayment, amount: Decimal, payment_date: date, description: str) -> WorkPayment
```

### `photo_management`

```python
publish_progress_photo(store: PortalStore, context: AuthorizedProjectContext, publication: PhotoPublication) -> PhotoMutationResult
update_progress_photo(store: PortalStore, context: AuthorizedProjectContext, photo_id: UUID, caption: str | None, section_id: UUID | None, client_visible: bool) -> PhotoMutationResult
list_progress_photos(store: PortalStore, context: AuthorizedProjectContext) -> list[ProgressPhoto]
read_progress_photo(store: PortalStore, context: AuthorizedProjectContext, photo_id: UUID) -> BinaryPayload
```

Private:

```python
_classify_photo_replay(existing: ProgressPhoto, publication: PhotoPublication) -> ProgressPhoto
_authorize_photo_reference(store: PortalStore, context: AuthorizedProjectContext, photo_id: UUID) -> AuthorizedBinaryReference
_ordered_photos(photos: list[ProgressPhoto]) -> list[ProgressPhoto]
_photo_mutation_result(photo: ProgressPhoto, replayed: bool) -> PhotoMutationResult
```

### `financial_policy`

```python
validate_eur_amount(currency: str, amount: Decimal, strictly_positive: bool = False) -> Decimal
calculate_completed_work(work_planned: Decimal, completion_percent: int) -> Decimal
calculate_overall_progress(sections: list[ProgressSectionView]) -> Decimal | None
calculate_material_balance(material_planned: Decimal, material_actual: Decimal) -> Decimal
calculate_work_balance(completed_work_total: Decimal, payments_total: Decimal) -> WorkBalanceResult
```

Private:

```python
_quantize_money(amount: Decimal) -> Decimal
```

### `derived_views`

```python
list_viewer_projects(store: PortalStore, actor: ViewerActorContext) -> list[ProjectListItem]
build_project_overview(store: PortalStore, context: AuthorizedProjectContext) -> ProjectOverview
build_budget_view(store: PortalStore, context: AuthorizedProjectContext, version_id: UUID | None = None) -> BudgetView
build_expense_view(store: PortalStore, context: AuthorizedProjectContext) -> ExpenseSummaryView
build_progress_view(store: PortalStore, context: AuthorizedProjectContext) -> ProgressView
build_payment_view(store: PortalStore, context: AuthorizedProjectContext) -> PaymentSummaryView
```

Private:

```python
_project_budget_sections(detail: BudgetVersionDetail, expenses: list[ExpenseAggregate], progress: list[SectionProgress]) -> list[BudgetSectionView]
_project_expense_summary(expenses: list[ExpenseAggregate], active_section_ids: list[UUID]) -> ExpenseSummaryView
_project_progress(detail: BudgetVersionDetail, progress: list[SectionProgress]) -> ProgressView
_project_payments(payments: list[WorkPayment], completed_work_total: Decimal) -> PaymentSummaryView
_project_photos(photos: list[ProgressPhoto], sections: list[PortalSection]) -> list[PhotoView]
_ordered_project_items(items: list[ProjectListItem]) -> list[ProjectListItem]
```

### `audit_writer`

```python
append_audit(tx: PortalTransaction, intent: AuditIntent) -> AuditRecord
```

Private:

```python
_validate_audit_intent(intent: AuditIntent) -> None
_build_audit_record(intent: AuditIntent, occurred_at: datetime) -> AuditRecord
```

### `portal_store`

Concrete typed transaction facade:

```python
PortalStore.__init__(self, database_url: str) -> None
PortalStore.begin(self) -> PortalTransaction

PortalTransaction.commit(self) -> None
PortalTransaction.rollback(self) -> None

PortalTransaction.get_staff_by_email(self, normalized_email: str) -> StaffAccount | None
PortalTransaction.get_staff(self, staff_id: UUID) -> StaffAccount | None
PortalTransaction.get_staff_session(self, session_id: UUID) -> StaffSession | None
PortalTransaction.list_staff_sessions(self, staff_id: UUID) -> list[StaffSession]
PortalTransaction.get_staff_assignment(self, staff_id: UUID, project_id: UUID) -> StaffProjectAssignment | None
PortalTransaction.get_staff_assignment_by_id(self, assignment_id: UUID) -> StaffProjectAssignment | None
PortalTransaction.insert_staff_account(self, account: StaffAccount) -> None
PortalTransaction.update_staff_account(self, account: StaffAccount) -> None
PortalTransaction.insert_staff_session(self, session: StaffSession) -> None
PortalTransaction.update_staff_sessions(self, sessions: list[StaffSession]) -> None
PortalTransaction.insert_staff_assignment(self, assignment: StaffProjectAssignment) -> None
PortalTransaction.update_staff_assignment(self, assignment: StaffProjectAssignment) -> None
PortalTransaction.list_email_verifications(self, staff_id: UUID) -> list[EmailVerificationChallenge]
PortalTransaction.get_email_verification(self, challenge_id: UUID) -> EmailVerificationChallenge | None
PortalTransaction.list_email_changes(self, staff_id: UUID) -> list[PendingEmailChange]
PortalTransaction.get_email_change(self, change_id: UUID) -> PendingEmailChange | None
PortalTransaction.list_password_resets(self, staff_id: UUID) -> list[PasswordResetToken]
PortalTransaction.get_password_reset(self, token_id: UUID) -> PasswordResetToken | None
PortalTransaction.insert_email_verification(self, challenge: EmailVerificationChallenge) -> None
PortalTransaction.update_email_verifications(self, challenges: list[EmailVerificationChallenge]) -> None
PortalTransaction.insert_email_change(self, change: PendingEmailChange) -> None
PortalTransaction.update_email_changes(self, changes: list[PendingEmailChange]) -> None
PortalTransaction.insert_password_reset(self, token: PasswordResetToken) -> None
PortalTransaction.update_password_resets(self, tokens: list[PasswordResetToken]) -> None
PortalTransaction.get_email_delivery(self, delivery_id: UUID) -> EmailDeliveryRecord | None
PortalTransaction.insert_email_delivery(self, record: EmailDeliveryRecord) -> None
PortalTransaction.update_email_delivery(self, record: EmailDeliveryRecord) -> None

PortalTransaction.get_viewer(self, viewer_id: UUID) -> ClientViewer | None
PortalTransaction.get_viewer_credential(self, credential_id: UUID) -> ViewerAccessCredential | None
PortalTransaction.get_viewer_session(self, session_id: UUID) -> ViewerSession | None
PortalTransaction.list_viewer_sessions(self, viewer_id: UUID) -> list[ViewerSession]
PortalTransaction.list_viewer_credentials(self, viewer_id: UUID) -> list[ViewerAccessCredential]
PortalTransaction.get_viewer_grant(self, viewer_id: UUID, project_id: UUID) -> ProjectViewerGrant | None
PortalTransaction.get_viewer_grant_by_id(self, grant_id: UUID) -> ProjectViewerGrant | None
PortalTransaction.list_viewer_grants(self, viewer_id: UUID) -> list[ProjectViewerGrant]
PortalTransaction.insert_viewer(self, viewer: ClientViewer) -> None
PortalTransaction.update_viewer(self, viewer: ClientViewer) -> None
PortalTransaction.insert_viewer_credential(self, credential: ViewerAccessCredential) -> None
PortalTransaction.update_viewer_credentials(self, credentials: list[ViewerAccessCredential]) -> None
PortalTransaction.insert_viewer_session(self, session: ViewerSession) -> None
PortalTransaction.update_viewer_sessions(self, sessions: list[ViewerSession]) -> None
PortalTransaction.insert_viewer_grant(self, grant: ProjectViewerGrant) -> None
PortalTransaction.update_viewer_grant(self, grant: ProjectViewerGrant) -> None

PortalTransaction.get_service_principal(self, principal_id: UUID) -> ServicePrincipal | None
PortalTransaction.get_service_credential(self, credential_id: UUID) -> ServiceCredential | None
PortalTransaction.list_service_credentials(self, principal_id: UUID) -> list[ServiceCredential]
PortalTransaction.get_producer_grant(self, principal_id: UUID, project_id: UUID) -> ProducerProjectGrant | None
PortalTransaction.get_producer_grant_by_id(self, grant_id: UUID) -> ProducerProjectGrant | None
PortalTransaction.insert_service_principal(self, principal: ServicePrincipal) -> None
PortalTransaction.update_service_principal(self, principal: ServicePrincipal) -> None
PortalTransaction.insert_service_credential(self, credential: ServiceCredential) -> None
PortalTransaction.update_service_credential(self, credential: ServiceCredential) -> None
PortalTransaction.insert_producer_grant(self, grant: ProducerProjectGrant) -> None
PortalTransaction.update_producer_grant(self, grant: ProducerProjectGrant) -> None

PortalTransaction.get_snapshot_by_identity(self, project_id: UUID, estimate_id: UUID, estimate_version: int) -> ApprovedEstimateSnapshot | None
PortalTransaction.get_snapshot_import(self, import_id: UUID) -> SnapshotImportRecord | None
PortalTransaction.insert_snapshot(self, snapshot: ApprovedEstimateSnapshot) -> None
PortalTransaction.insert_snapshot_import(self, record: SnapshotImportRecord) -> None

PortalTransaction.get_budget_version(self, version_id: UUID) -> BudgetVersion | None
PortalTransaction.get_active_budget_version(self, project_id: UUID) -> BudgetVersion | None
PortalTransaction.get_manual_budget_version(self, project_id: UUID) -> BudgetVersion | None
PortalTransaction.list_budget_plans(self, version_id: UUID) -> list[SectionPlan]
PortalTransaction.list_project_sections(self, project_id: UUID) -> list[PortalSection]
PortalTransaction.get_project_section(self, project_id: UUID, section_id: UUID) -> PortalSection | None
PortalTransaction.insert_budget_version(self, version: BudgetVersion) -> None
PortalTransaction.update_budget_versions(self, versions: list[BudgetVersion]) -> None
PortalTransaction.insert_project_sections(self, sections: list[PortalSection]) -> None
PortalTransaction.upsert_section_plan(self, plan: SectionPlan) -> None
PortalTransaction.insert_section_plans(self, plans: list[SectionPlan]) -> None

PortalTransaction.get_expense_aggregate(self, expense_id: UUID) -> ExpenseAggregate | None
PortalTransaction.get_expense_by_recognition_id(self, recognized_document_id: str) -> ExpenseAggregate | None
PortalTransaction.get_expense_document(self, document_id: UUID) -> ExpenseDocument | None
PortalTransaction.list_project_expenses(self, project_id: UUID) -> list[ExpenseAggregate]
PortalTransaction.insert_expense_aggregate(self, aggregate: ExpenseAggregate) -> None
PortalTransaction.update_expense_aggregate(self, aggregate: ExpenseAggregate) -> None
PortalTransaction.update_expense(self, expense: Expense) -> None
PortalTransaction.update_expense_document(self, document: ExpenseDocument) -> None

PortalTransaction.get_section_progress(self, project_id: UUID, section_id: UUID) -> SectionProgress | None
PortalTransaction.list_project_progress(self, project_id: UUID) -> list[SectionProgress]
PortalTransaction.get_work_payment(self, payment_id: UUID) -> WorkPayment | None
PortalTransaction.list_project_payments(self, project_id: UUID) -> list[WorkPayment]
PortalTransaction.upsert_section_progress(self, progress: SectionProgress) -> None
PortalTransaction.insert_work_payment(self, payment: WorkPayment) -> None

PortalTransaction.get_progress_photo(self, photo_id: UUID) -> ProgressPhoto | None
PortalTransaction.get_progress_photo_by_intake_id(self, intake_id: str) -> ProgressPhoto | None
PortalTransaction.list_project_photos(self, project_id: UUID) -> list[ProgressPhoto]
PortalTransaction.insert_progress_photo(self, photo: ProgressPhoto) -> None
PortalTransaction.update_progress_photo(self, photo: ProgressPhoto) -> None

PortalTransaction.insert_audit(self, record: AuditRecord) -> None
```

Every insert/update remains domain-specific and typed. `PortalTransaction`
cannot be imported by `api`; it is consumed only inside semantic modules and
`audit_writer`.

Private storage helpers:

```python
PortalTransaction._translate_persistence_error(self, error: BaseException) -> PersistenceError
PortalTransaction._assert_open(self) -> None
```

### `api`

```python
create_app(store: PortalStore) -> FastAPI
PortalApi.__init__(self, store: PortalStore) -> None
PortalApi.register_routes(self, app: FastAPI) -> None

PortalApi.staff_login(self, email: str, password: str) -> StaffSessionGrant
PortalApi.staff_logout(self, session_token: str) -> None
PortalApi.confirm_staff_email(self, token: str) -> StaffAccountView
PortalApi.request_password_reset(self, email: str) -> None
PortalApi.complete_password_reset(self, token: str, new_password: str) -> StaffAccountView
PortalApi.request_email_change(self, session_token: str, new_email: str) -> ChallengeIssueView
PortalApi.issue_staff_email_verification(self, administrator_token: str, staff_id: UUID) -> ChallengeIssueView
PortalApi.confirm_email_change(self, token: str) -> StaffAccountView

PortalApi.create_staff(self, administrator_token: str, email: str, initial_password: str, role: StaffRole) -> StaffAccountView
PortalApi.change_staff_status(self, administrator_token: str, staff_id: UUID, new_status: StaffStatus) -> StaffAccountView
PortalApi.assign_staff_project(self, administrator_token: str, operator_id: UUID, project_id: UUID) -> StaffProjectAssignment
PortalApi.revoke_staff_assignment(self, administrator_token: str, assignment_id: UUID) -> StaffProjectAssignment
PortalApi.revoke_staff_sessions(self, administrator_token: str, staff_id: UUID) -> SessionRevocationResult

PortalApi.create_viewer(self, administrator_token: str, display_name: str) -> ClientViewerView
PortalApi.revoke_viewer(self, administrator_token: str, viewer_id: UUID) -> ClientViewerView
PortalApi.issue_viewer_credential(self, administrator_token: str, viewer_id: UUID) -> ViewerCredentialIssueResponse
PortalApi.revoke_viewer_credential(self, administrator_token: str, credential_id: UUID) -> None
PortalApi.grant_viewer_project(self, administrator_token: str, viewer_id: UUID, project_id: UUID) -> ProjectViewerGrant
PortalApi.revoke_viewer_project(self, administrator_token: str, grant_id: UUID) -> ProjectViewerGrant
PortalApi.viewer_enter(self, capability_secret: str) -> ViewerSessionGrant
PortalApi.list_viewer_projects(self, viewer_session_token: str) -> list[ProjectListItem]
PortalApi.viewer_project_overview(self, viewer_session_token: str, project_id: UUID) -> ProjectOverview

PortalApi.create_service_principal(self, administrator_token: str, name: str, source_type: ProducerSourceType, scope_mode: ProducerScopeMode) -> ServicePrincipalView
PortalApi.change_service_principal_status(self, administrator_token: str, principal_id: UUID, new_status: PrincipalStatus) -> ServicePrincipalView
PortalApi.issue_service_credential(self, administrator_token: str, principal_id: UUID, expires_at: datetime | None = None) -> ServiceCredentialIssueResponse
PortalApi.revoke_service_credential(self, administrator_token: str, credential_id: UUID) -> None
PortalApi.grant_producer_project(self, administrator_token: str, principal_id: UUID, project_id: UUID) -> ProducerProjectGrant
PortalApi.revoke_producer_project(self, administrator_token: str, grant_id: UUID) -> ProducerProjectGrant
PortalApi.publish_snapshot(self, service_secret: str, publication: SnapshotPublication) -> SnapshotImportRecord
PortalApi.get_snapshot_import(self, service_secret: str, import_id: UUID) -> SnapshotImportRecord

PortalApi.ensure_manual_budget(self, staff_session_token: str, project_id: UUID) -> BudgetVersionDetail
PortalApi.upsert_manual_section_plan(self, staff_session_token: str, project_id: UUID, section_id: UUID | None, display_name: str, sort_order: int, material_planned: Decimal, work_planned: Decimal) -> BudgetVersionDetail
PortalApi.activate_budget_version(self, staff_session_token: str, project_id: UUID, version_id: UUID) -> BudgetActivationResult
PortalApi.staff_project_overview(self, staff_session_token: str, project_id: UUID) -> ProjectOverview

PortalApi.create_expense_from_recognition(self, staff_session_token: str, project_id: UUID, publication: ConfirmedRecognitionPublication, allocations: list[AllocationInstruction]) -> ExpenseMutationResult
PortalApi.correct_expense(self, staff_session_token: str, project_id: UUID, expense_id: UUID, supplier: str, document_date: date, total_amount: Decimal, included: bool, allocations: list[AllocationInstruction]) -> ExpenseMutationResult
PortalApi.set_expense_inclusion(self, staff_session_token: str, project_id: UUID, expense_id: UUID, included: bool) -> ExpenseMutationResult
PortalApi.replace_expense_allocations(self, staff_session_token: str, project_id: UUID, expense_id: UUID, allocations: list[AllocationInstruction]) -> ExpenseMutationResult
PortalApi.update_expense_document(self, staff_session_token: str, project_id: UUID, document_id: UUID, description: str | None, client_visible: bool) -> DocumentMutationResult
PortalApi.staff_read_expense_document(self, staff_session_token: str, project_id: UUID, document_id: UUID) -> BinaryPayload
PortalApi.viewer_read_expense_document(self, viewer_session_token: str, project_id: UUID, document_id: UUID) -> BinaryPayload

PortalApi.set_section_progress(self, staff_session_token: str, project_id: UUID, section_id: UUID, completion_percent: int) -> SectionProgress
PortalApi.register_work_payment(self, staff_session_token: str, project_id: UUID, payment_id: UUID, amount: Decimal, payment_date: date, description: str) -> WorkPayment
PortalApi.publish_progress_photo(self, staff_session_token: str, project_id: UUID, publication: PhotoPublication) -> PhotoMutationResult
PortalApi.update_progress_photo(self, staff_session_token: str, project_id: UUID, photo_id: UUID, caption: str | None, section_id: UUID | None, client_visible: bool) -> PhotoMutationResult
PortalApi.staff_read_progress_photo(self, staff_session_token: str, project_id: UUID, photo_id: UUID) -> BinaryPayload
PortalApi.viewer_read_progress_photo(self, viewer_session_token: str, project_id: UUID, photo_id: UUID) -> BinaryPayload

PortalApi._staff_account_view(self, account: StaffAccount) -> StaffAccountView
PortalApi._viewer_view(self, viewer: ClientViewer) -> ClientViewerView
PortalApi._service_principal_view(self, principal: ServicePrincipal) -> ServicePrincipalView
PortalApi._viewer_credential_response(self, issue: ViewerCredentialIssue) -> ViewerCredentialIssueResponse
PortalApi._service_credential_response(self, issue: ServiceCredentialIssue) -> ServiceCredentialIssueResponse
PortalApi._expense_mutation_result(self, aggregate: ExpenseAggregate) -> ExpenseMutationResult
PortalApi._document_mutation_result(self, document: ExpenseDocument) -> DocumentMutationResult
PortalApi._session_revocation_result(self, staff_id: UUID, sessions: list[StaffSession]) -> SessionRevocationResult
```

Separate staff/viewer binary methods prevent a request boolean from selecting
an authentication contour. Both return BinaryPayload only after their typed
session resolver and guard succeed. `register_routes` binds these exact
methods; no additional endpoint function may own behavior.

## `module_functions` draft

Each module contains its public functions, the private helpers listed directly
under it, and its owned exception classes. Class ownership:

```text
portal_store → PortalStore, PortalTransaction, PersistenceError
authorization_guard → AuthenticationRejected, AuthorizationRejected,
                      ArchivedProjectRejected, ScopedNotFoundError
staff_identity → ChallengeRejected, ChallengeRateLimited,
                 IdentityInputRejected
registry_gateway → RegistryBoundaryError
email_delivery_gateway → EmailDeliveryError
binary_storage → BinaryStorageError
budget_management → BudgetValidationError, BudgetConflictError
expense_management → ExpenseValidationError, ExpenseConflictError,
                     BinaryAccessRejected
project_tracking → TrackingValidationError, TrackingConflictError
photo_management → PhotoValidationError, PhotoConflictError
financial_policy → FinancialValidationError
```

`models` contains all models/enums from State 1. No model symbol is duplicated
in a semantic module.

`api` contains `PortalApi`, all listed methods, and `create_app`; it exports
only `create_app` through `imports.internal`.

## Exact `imports.module_internal` edges

```text
credential_security → models
staff_identity → models, credential_security, authorization_guard,
                 registry_gateway, email_delivery_gateway, audit_writer,
                 portal_store
viewer_access → models, credential_security, authorization_guard,
                registry_gateway, audit_writer, portal_store
service_identity → models, credential_security, authorization_guard,
                   registry_gateway, audit_writer, portal_store
authorization_guard → models, registry_gateway, portal_store
registry_gateway → models
email_delivery_gateway → models, portal_store
binary_storage → models
snapshot_import → models, authorization_guard, service_identity,
                  financial_policy, audit_writer, portal_store
budget_management → models, financial_policy, audit_writer, portal_store
expense_intake → models, financial_policy, budget_management, audit_writer,
                 portal_store
expense_management → models, financial_policy, budget_management,
                     binary_storage, audit_writer, portal_store
project_tracking → models, financial_policy, budget_management,
                   audit_writer, portal_store
photo_management → models, budget_management, binary_storage,
                   audit_writer, portal_store
financial_policy → models
derived_views → models, viewer_access, registry_gateway, financial_policy,
                project_tracking, photo_management, portal_store
audit_writer → models, portal_store
api → models, staff_identity, viewer_access, service_identity,
      authorization_guard, snapshot_import, budget_management,
      expense_intake, expense_management, project_tracking,
      photo_management, derived_views, portal_store
```

The earlier cycle is gone: `authorization_guard` must not depend on identity
modules; it checks trusted contexts plus persistence state. Identity modules
may use its exception/policy surface.

## Function order

Global assembly order is module order from State 3, with `staff_identity`
replacing the former pair. Within each module:

```text
owned exceptions/classes
→ pure validation/canonicalization helpers
→ record builders/projections
→ private I/O translators
→ public read operations
→ public mutation/orchestration operations
→ create_app last
```

For `portal_store`: `PortalStore` then `PortalTransaction`; getters/list
methods precede inserts/updates, `insert_audit` follows business persistence
methods, and commit/rollback are last in the class source even though they are
declared near the top of this document for readability.

## Placeholder-resistance review

- No public or private signature contains `dict`, `Any`, `object`, Callable,
  raw ORM/session types, or unknown model names.
- Each input has a known source: API primitive/model, trusted context, config,
  clock-owned helper value, or typed persistence record.
- Each output has a concrete caller; `None` is used only for explicit
  no-content commands or typed optional lookup internals.
- Private helpers hide meaningful policy/canonicalization; no helper merely
  renames or forwards arguments.
- Typed PortalTransaction makes audit/business atomicity possible without
  leaking SQLAlchemy or giving transaction access to HTTP handlers.
- Actor-specific guards avoid unsupported named/untagged union pressure.

## State 6 readiness assessment

Public and private functions now have exact signatures, one module owner, and
known dependency edges. All runtime type names are closed over builtins,
declared models, explicit imports, or exported module-owned classes. State 7
can now write classified notes/properties and assign exact invariant-ledger
owner functions without inventing behavior or contracts.
