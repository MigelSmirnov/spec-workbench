# State 7 — Classified notes, properties, and invariant landing

## Status

**State 7 authoring pass.** Contracts and ownership from `60_contracts.md`
remain unchanged. The strings below are assembly-ready classified notes. Each
exact contract has either a function note below or an explicitly named
module-wide persistence rule plus its own operation-specific note. Properties
use only the closed expression subset from `SPEC_STANDARD.md`; determinism is
declared separately. No transaction, exception, clock, random, secret, I/O,
or authorization requirement is represented as a property.

The three product-owner decisions listed in `HANDOFF.md` were explicitly
confirmed on 2026-07-19. Notes address their final config keys.

## Stable rule keys for assembly

```text
R1  -> rules.capability_catalog
R2  -> rules.principal_capability_sets
R3  -> rules.status_transitions
R4  -> rules.project_guard_sequence
R5  -> rules.registry_status_policy
R6  -> rules.registry_failure_translation
R7  -> rules.supported_external_contract_versions
R8  -> rules.idempotency_identities
R9  -> rules.money_policy
R10 -> rules.email_challenge_policy
R11 -> rules.revocation_cascades
R12 -> rules.producer_scope_policy
R13 -> rules.audit_action_catalog
R14 -> rules.binary_delivery_policy
R15 -> rules.project_list_ordering
R16 -> rules.staff_identity_input_policy
R17 -> rules.verification_envelope_policy
```

## Assembly-ready classified notes

### Owned exceptions

```text
AuthenticationRejected.__init__: [SECURITY_BOUNDARY] MUST carry no account, principal, project, selector, or failure-detail attributes.
AuthorizationRejected.__init__: [SECURITY_BOUNDARY] MUST carry no inaccessible entity or project detail.
ArchivedProjectRejected.__init__: [VALIDATION_ERROR] MUST represent the closed inactive-project rejection without exposing Registry response data.
ChallengeRejected.__init__: [SECURITY_BOUNDARY] MUST carry no account, selector, token-purpose, or lifecycle detail.
ChallengeRateLimited.__init__: [VALIDATION_ERROR] MUST identify the closed challenge-rate-limit rejection without address-existence evidence.
IdentityInputRejected.__init__: [VALIDATION_ERROR] MUST represent an R16 input rejection without retaining password plaintext.
ScopedNotFoundError.__init__: [SECURITY_BOUNDARY] MUST conceal whether the inaccessible scoped object exists.
RegistryBoundaryError.__init__: [FIELD_ASSIGNMENT] MUST expose exactly the supplied RegistryFailureKind as kind and no raw HTTP body or transport exception.
BudgetValidationError.__init__: [VALIDATION_ERROR] MUST carry no untyped payload or persistence detail.
BudgetConflictError.__init__: [VALIDATION_ERROR] MUST carry no untyped payload or persistence detail.
ExpenseValidationError.__init__: [VALIDATION_ERROR] MUST carry no recognition raw response, provider field, or file_ref.
ExpenseConflictError.__init__: [VALIDATION_ERROR] MUST carry no recognition raw response, provider field, or file_ref.
TrackingValidationError.__init__: [VALIDATION_ERROR] MUST carry no untyped payload or persistence detail.
TrackingConflictError.__init__: [VALIDATION_ERROR] MUST carry no untyped payload or persistence detail.
PhotoValidationError.__init__: [VALIDATION_ERROR] MUST carry no file_ref, path, or storage-provider detail.
PhotoConflictError.__init__: [VALIDATION_ERROR] MUST carry no file_ref, path, or storage-provider detail.
FinancialValidationError.__init__: [VALIDATION_ERROR] MUST represent an R9 rejection without implicit conversion or replacement values.
BinaryAccessRejected.__init__: [SECURITY_BOUNDARY] MUST conceal file_ref and whether an inaccessible binary record or object exists.
BinaryStorageError.__init__: [PATH_OR_ARTIFACT_POLICY] MUST carry no raw path, bucket, provider URL, credential, or file_ref.
EmailDeliveryError.__init__: [SECURITY_BOUNDARY] MUST carry no token plaintext or address-ownership evidence.
PersistenceError.__init__: [VALIDATION_ERROR] MUST expose no raw driver exception, SQL text, database URL, or stored secret.
```

### `credential_security`

```text
hash_password: [CONFIG_REFERENCE] MUST hash the exact supplied plaintext using = config.credential_hash_scheme and MUST NOT trim, casefold, normalize, log, or persist plaintext.
verify_password: [SECURITY_BOUNDARY] MUST verify against the supplied password_hash with the configured password algorithm and return only the comparison result.
issue_verification_secret: [RULE_REFERENCE] MUST implement = rules.verification_envelope_policy using entropy_bytes of cryptographically secure randomness and return plaintext once plus a salted verification_hash.
parse_verification_secret: [VALIDATION_ERROR] MUST reject a malformed envelope without treating its selector as authority or deriving a hash lookup key.
verify_secret: [SECURITY_BOUNDARY] MUST compare the supplied random secret to verification_hash in constant time and MUST NOT query storage or log either value.
_hash_secret: [SECURITY_BOUNDARY] MUST produce a salted verification hash; equal plaintext inputs MUST NOT be required to produce equal hashes.
_constant_time_verify: [SECURITY_BOUNDARY] MUST return only whether secret verifies against verification_hash and MUST NOT reveal mismatch position or hash metadata.
_encode_secret_envelope: [FIELD_PROJECTION] MUST encode record_id as the public selector and secret as the independent authority component according to = rules.verification_envelope_policy.
```

### `staff_identity`

```text
create_staff_account: [ORCHESTRATION] MUST authorize access management, enforce R16 normalized-email uniqueness, hash initial_password exactly as supplied, insert the pending-verification account, and append staff.create in the same transaction.
authenticate_staff: [SECURITY_BOUNDARY] MUST normalize email, accept only an active verified account with a matching password, issue a hashed fixed-expiry session, audit success or concealed failure, and never reveal which check failed.
resolve_staff_session: [SECURITY_BOUNDARY] MUST parse the R17 selector, verify its secret hash, fixed expiry, revocation, active account, and verified email before returning StaffActorContext; any failure raises AuthenticationRejected.
resolve_staff_session: [RETURN_SHAPE] MUST return exactly one StaffActorContext from the selected persisted session/account or raise AuthenticationRejected; it MUST never return None.
sign_out_staff: [ORCHESTRATION] MUST revoke the actor's selected active session and append staff.logout atomically; an already unusable session is rejected through the concealed auth boundary.
revoke_staff_sessions: [ORCHESTRATION] MUST authorize access management, revoke every active session for staff_id at one revoked_at, and append staff.sessions_revoke in the same transaction.
change_staff_status: [RULE_REFERENCE] MUST enforce = rules.status_transitions and = rules.revocation_cascades; suspension or disabling revokes sessions/challenges and commits the status change plus one catalog audit atomically.
change_staff_password: [SECURITY_BOUNDARY] MUST verify current_password, enforce R16 on new_password, replace password_hash, revoke other active sessions, and never persist or audit either plaintext.
assign_staff_project: [ORCHESTRATION] MUST authorize access management, validate the Registry UUID server-side before opening the mutation transaction, reject duplicate active assignment, and append staff_assignment.create atomically.
revoke_staff_project_assignment: [ORCHESTRATION] MUST authorize access management, revoke the addressed active assignment, and append staff_assignment.revoke atomically so the next guard observes revocation.
issue_email_verification: [ORCHESTRATION] MUST authorize access management, commit the R10 challenge and audit before delivery, then return a hash-free ChallengeIssueView whose delivery outcome does not change validity.
confirm_email_verification: [SECURITY_BOUNDARY] MUST consume only an unexpired unused unrevoked email-verification token, mark email_verified, and append staff.email_verified atomically without revealing other challenge states.
request_email_change: [ORCHESTRATION] MUST enforce R16 normalized-email uniqueness, commit the purpose-bound challenge and staff.email_change_request audit before delivery, and never change the login email at request time.
confirm_email_change: [ORCHESTRATION] MUST consume only the matching email-change token, atomically replace the login email and append staff.email_changed, then notify the previous address after commit.
request_password_reset: [SECURITY_BOUNDARY] MUST return None for both known and unknown normalized email; for a known eligible account it commits the R10 challenge and audit before delivery without exposing existence.
complete_password_reset: [ORCHESTRATION] MUST consume only the matching reset token, enforce R16, replace password_hash, revoke every active session and outstanding reset token atomically, append staff.password_reset_complete, then send password_changed_notice after commit.
perform_recovery_override: [SECURITY_BOUNDARY] MUST be administrator-only, enforce R16 on replacement_email, append enhanced staff.recovery_override audit atomically with the replacement, and MUST NOT serve as the normal email-change path.
_normalize_staff_email: [RULE_REFERENCE] MUST strip, syntax-validate, and Unicode-casefold according to = rules.staff_identity_input_policy while preserving dots and plus tags and performing no provider-specific rewrite.
_validate_new_password: [RULE_REFERENCE] MUST enforce = rules.staff_identity_input_policy and MUST NOT trim, casefold, Unicode-normalize, log, or perform an undeclared network check.
_build_staff_session: [FIELD_ASSIGNMENT] MUST copy staff_id and role, store issued.verification_hash rather than issued.plaintext, and assign exactly created_at and expires_at.
_build_email_delivery_request: [FIELD_PROJECTION] MUST project recipient and message kind from record, include token only for token-bearing R10 kinds, and MUST NOT include any verification hash.
_build_challenge_issue_view: [FIELD_PROJECTION] MUST set challenge_ref, expires_at, delivery_id, delivery_outcome, and message_kind from the committed challenge/delivery evidence and expose no token or hash.
_issue_challenge: [RULE_REFERENCE] MUST enforce = rules.email_challenge_policy by rate-limiting per account, revoking outstanding same-purpose records, persisting one new hashed challenge, and returning its delivery request without sending inside tx.
_consume_email_verification: [SECURITY_BOUNDARY] MUST verify selector, secret, email-verification purpose, expiry, revocation, and single-use state before marking consumed; first failure raises ChallengeRejected.
_consume_email_change: [SECURITY_BOUNDARY] MUST verify selector, secret, email-change purpose, expiry, revocation, single-use state, and normalized-email uniqueness before changing the account and marking consumed.
_consume_password_reset: [SECURITY_BOUNDARY] MUST verify selector, secret, reset purpose, expiry, revocation, and single-use state before storing new_password_hash and revoking all outstanding resets and sessions.
_deliver_after_commit: [ORCHESTRATION] MUST call the email gateway only after the owning transaction committed and return the persisted delivery result without changing challenge validity.
```

### `viewer_access` and `service_identity`

```text
create_viewer: [PROVENANCE] MUST create portal-owned display_name independently of Registry customer_ref and append viewer.create atomically after access-management authorization.
create_viewer: [ORCHESTRATION] MUST persist exactly one new ClientViewer and exactly one viewer.create AuditRecord in the same transaction.
revoke_viewer: [RULE_REFERENCE] MUST apply = rules.revocation_cascades, revoke viewer sessions atomically with status change, and append viewer.revoke.
issue_viewer_access: [ORCHESTRATION] MUST revoke every non-revoked prior credential, persist exactly one new verification_hash, revoke active sessions, append viewer.credential_issue, and return plaintext only in ViewerCredentialIssue.
revoke_viewer_access: [ORCHESTRATION] MUST revoke the addressed credential and all viewer sessions atomically and append viewer.credential_revoke.
enter_viewer_access: [SECURITY_BOUNDARY] MUST parse and verify the selected active credential plus viewer status, create a fixed-expiry hashed session, and conceal unknown selector, wrong secret, and revoked state.
resolve_viewer_session: [SECURITY_BOUNDARY] MUST verify token hash, expiry, revocation, viewer status, and credential usability before returning ViewerActorContext; any failure raises AuthenticationRejected.
resolve_viewer_session: [RETURN_SHAPE] MUST return exactly one ViewerActorContext from the selected persisted session/viewer or raise AuthenticationRejected; it MUST never return None.
grant_viewer_project: [ORCHESTRATION] MUST authorize access management, validate the same active Registry UUID before the transaction, reject an existing active pair, and append grant.create atomically.
revoke_viewer_project: [ORCHESTRATION] MUST revoke only the addressed active grant and append grant.revoke atomically so the next guard observes it.
list_viewer_project_grants: [SECURITY_BOUNDARY] MUST return all active grants for actor.viewer_id only and MUST NOT accept viewer_id from request data.
list_viewer_project_grants: [RETURN_SHAPE] MUST return every active ProjectViewerGrant for actor.viewer_id and no revoked or differently owned grant.
_build_viewer_session: [FIELD_ASSIGNMENT] MUST copy viewer_id, store issued.verification_hash rather than issued.plaintext, and assign exactly created_at and expires_at.
_revoke_viewer_sessions: [BEHAVIOR] MUST return every session newly revoked for viewer_id with the supplied revoked_at and leave already revoked sessions unchanged.
create_service_principal: [ORCHESTRATION] MUST authorize access management, persist the closed source_type/scope_mode principal, and append principal.create atomically.
change_service_principal_status: [RULE_REFERENCE] MUST enforce = rules.status_transitions and = rules.revocation_cascades and append principal.disable or principal.enable atomically.
issue_service_credential: [SECURITY_BOUNDARY] MUST allocate the next key_version, persist only verification_hash, append principal.credential_issue atomically, and expose plaintext exactly once in ServiceCredentialIssue.
revoke_service_credential: [ORCHESTRATION] MUST revoke the addressed credential without revoking overlapping credentials and append principal.credential_revoke atomically.
grant_producer_project: [ORCHESTRATION] MUST authorize access management, validate the same active Registry UUID before the transaction, reject an existing active pair, and append producer_grant.create atomically.
revoke_producer_project: [ORCHESTRATION] MUST revoke only the addressed active grant and append producer_grant.revoke atomically.
authenticate_service_principal: [SECURITY_BOUNDARY] MUST verify the selected credential secret, expiry, revocation, and active principal before returning trusted source_type, scope_mode, and key_version; failures reveal no selector state.
authorize_producer_scope: [RULE_REFERENCE] MUST return the decision from = rules.producer_scope_policy using trusted actor scope and active persisted grants only.
_next_key_version: [BEHAVIOR] MUST return one greater than the greatest persisted key_version for principal_id, or 1 when none exist, within the issuing transaction.
_credential_is_usable: [BEHAVIOR] MUST be true only when credential and principal are active, the credential is unrevoked, and checked_at is before expires_at when present.
```

### `authorization_guard` and `registry_gateway`

```text
conceal_authentication_failure: [SECURITY_BOUNDARY] MUST return a fresh parameterless AuthenticationRejected carrying no existence or project evidence.
authorize_staff_project_read: [ORCHESTRATION] MUST construct the staff/read closed-choice request and delegate the complete decision to _authorize_project_operation without duplicating policy.
authorize_viewer_project_read: [ORCHESTRATION] MUST construct the viewer/read closed-choice request and delegate the complete decision to _authorize_project_operation without accepting role or capability claims.
authorize_staff_project_mutation: [ORCHESTRATION] MUST construct the staff/mutation closed-choice request and delegate the complete decision to _authorize_project_operation without duplicating policy.
authorize_access_management: [RULE_REFERENCE] MUST resolve the current staff session/account and enforce the access-management capability from = rules.principal_capability_sets, never request role data.
authorize_snapshot_import: [ORCHESTRATION] MUST enforce producer scope before publication validation and delegate active Registry lifecycle and capability checks to _authorize_project_operation.
_require_staff_scope: [SECURITY_BOUNDARY] MUST accept administrators only under the single-area policy and operators only with an active StaffProjectAssignment for the same project_id.
_require_viewer_grant: [SECURITY_BOUNDARY] MUST require an active ProjectViewerGrant for actor.viewer_id and project_id and reject through the scoped concealment boundary.
_require_capability: [RULE_REFERENCE] MUST derive the closed capability set only from actor_kind plus trusted role/source_type using = rules.capability_catalog and = rules.principal_capability_sets.
_authorize_project_operation: [ORCHESTRATION] MUST execute = rules.project_guard_sequence in order with first failure winning; it MUST resolve persisted revocation/current-principal state, ignore client Registry context, validate the same UUID server-side, and reject inactive mutation targets.
_context_from_validation: [FIELD_PROJECTION] MUST project actor kind/id/key_version, requested capability, validation.project_id, and accepted Registry status into AuthorizedProjectContext only after successful validation.
list_active_projects: [DETERMINISM_OR_ORDERING] MUST decode only typed active ProjectReference values and sort by project_id ascending according to = rules.project_list_ordering regardless of upstream order.
validate_project_reference: [PROVENANCE] MUST resolve the Registry endpoint from the environment variable named by = config.registry_endpoint_env_name and use = config.registry_timeout_seconds; it MUST never create a project_id or access Registry storage directly.
validate_project_reference: [VALIDATION_ERROR] MUST return a typed ProjectValidationResult for a decoded response and raise RegistryBoundaryError for timeout, transport, HTTP, schema, or identity failure.
get_project_context: [PROVENANCE] MUST fetch live typed Registry context, accept active or archived status for reads, validate response identity, and MUST NOT persist or treat it as portal-owned current truth.
get_project_context: [RETURN_SHAPE] MUST return the exact live ProjectContext whose project.project_id matches project_id or raise RegistryBoundaryError; it MUST never return None.
_registry_url: [CONFIG_REFERENCE] MUST join only the supplied relative path to the deployment URL loaded from the environment variable named by = config.registry_endpoint_env_name without embedding credentials or accepting an absolute override.
_translate_registry_failure: [RULE_REFERENCE] MUST map the closed failure through = rules.registry_failure_translation and MUST NOT fall back to cached, client-supplied, or fabricated context.
_validate_reference_identity: [VALIDATION_ERROR] MUST reject schema/identity mismatch unless result.project_id equals requested_id.
_validate_context_identity: [VALIDATION_ERROR] MUST reject schema/identity mismatch unless context.project.project_id equals requested_id.
```

### Gateways and binary storage

```text
deliver_email_message: [ORCHESTRATION] MUST persist the delivery attempt/outcome around the provider call, translate provider failure to EmailDeliveryError, and MUST NOT mark any challenge valid, consumed, or verified.
_send_delivery_request: [SECURITY_BOUNDARY] MUST send only the typed request through the configured provider and return provider_message_id without logging token or inferring address ownership.
_record_delivery_failure: [BEHAVIOR] MUST persist failed outcome for delivery_id in a new store transaction and return that EmailDeliveryRecord without changing its challenge.
read_binary: [PATH_OR_ARTIFACT_POLICY] MUST accept only AuthorizedBinaryReference, safely resolve file_ref, enforce the positive integer loaded from the environment variable named by = config.binary_read_limit_env_name, return exact bytes/metadata, and expose no path, file_ref, provider URL, or credential.
_resolve_safe_object_path: [PATH_OR_ARTIFACT_POLICY] MUST resolve only opaque refs inside the configured storage root and reject traversal, absolute paths, URLs, and root escape.
_validate_binary_size: [VALIDATION_ERROR] MUST reject negative content_length or a value greater than the positive integer loaded from the environment variable named by = config.binary_read_limit_env_name before response emission.
_read_object_bytes: [PATH_OR_ARTIFACT_POLICY] MUST read only the already validated internal object_path and raise BinaryStorageError on missing or short/failed read rather than return empty fabricated bytes.
```

### Snapshot, budget, and expense domains

```text
import_snapshot: [ORCHESTRATION] MUST authorize producer scope and active Registry identity before validating content; equal replay returns the existing import result, conflict stores no snapshot, and every accepted/rejected catalog outcome appends one immutable import record plus audit atomically.
get_snapshot_import_result: [SECURITY_BOUNDARY] MUST return the addressed immutable record only when its service_principal_id matches actor and MUST otherwise raise ScopedNotFoundError.
get_snapshot_import_result: [RETURN_SHAPE] MUST return exactly one immutable SnapshotImportRecord matching import_id and actor.service_principal_id, never an empty record.
_validate_snapshot_publication: [VALIDATION_ERROR] MUST enforce = rules.supported_external_contract_versions, EUR/R9 values, complete closed DTO fields, and project identity without consulting mutable PresuPro state.
_canonical_snapshot_fingerprint: [DETERMINISM_OR_ORDERING] MUST hash the complete canonical publication content independent of input collection/hash iteration order and exclude receipt clock or actor credentials.
_classify_snapshot_replay: [RULE_REFERENCE] MUST return idempotent_replay only for equal content_fingerprint and integrity_conflict otherwise according to = rules.idempotency_identities.
_build_approved_snapshot: [PROVENANCE] MUST copy publication identity/content, actor service principal and key_version, fingerprint, and received_at into a new immutable snapshot without Registry name/address fields.
_build_import_record: [FIELD_ASSIGNMENT] MUST record publication identity, actor/key_version, outcome, reject_reason, fingerprint, snapshot_id, and occurred_at without token secret or mutable provider state.
ensure_manual_budget: [ORCHESTRATION] MUST return the existing single manual version or atomically create one with empty plans plus budget.manual_version_create audit; it MUST NOT activate it implicitly.
upsert_manual_section_plan: [ORCHESTRATION] MUST require an active project and the single manual version, create/rename the stable PortalSection when needed, validate R9 amounts, upsert its plan, and append budget.section_plan_edit atomically without changing imported plans.
get_budget_version: [SECURITY_BOUNDARY] MUST return the exact project-scoped version with deterministically ordered plans or raise ScopedNotFoundError without revealing another project.
get_budget_version: [RETURN_SHAPE] MUST return BudgetVersionDetail with version.version_id equal to version_id and every persisted plan ordered by sort_order then section_id.
activate_budget_version: [ORCHESTRATION] MUST validate version ownership and unresolved-allocation policy, atomically deactivate the prior active version, activate exactly the requested version, and append snapshot.activate without granting producers this operation.
validate_project_section: [SECURITY_BOUNDARY] MUST return only a section whose project_id equals project_id and raise BudgetValidationError for missing or cross-project identity without revealing another project.
_link_snapshot_sections: [RULE_REFERENCE] MUST reuse sections only by exact source_key, create stable new identities otherwise, preserve existing identities across rename, and MUST NOT match display_name.
_build_imported_plans: [PROVENANCE] MUST create one immutable SectionPlan per snapshot section using its linked section, exact snapshot amounts, version_id, and created_at; it MUST NOT derive values from expenses.
_find_unresolved_allocation_count: [BEHAVIOR] MUST count allocations whose section target is absent from active_section_ids and MUST NOT count other_expenses targets.
_ordered_plans: [DETERMINISM_OR_ORDERING] MUST return every input plan exactly once ordered by sort_order then section_id.
create_expense_from_recognition: [ORCHESTRATION] MUST accept only confirmed complete supported-version normalized input, validate explicit allocations, apply R8 replay before mutation, and atomically insert one Expense plus one ExpenseDocument plus allocations and expense.create audit.
_project_expense_intake: [FIELD_PROJECTION] MUST project only confirmed normalized business fields, recognized_document_id, intake_fingerprint inputs, file_ref, and explicit allocations; it MUST NOT project confidence, provider fields, or raw responses.
_canonical_intake_fingerprint: [DETERMINISM_OR_ORDERING] MUST hash the complete canonical intake independent of input/hash order and exclude clock, actor session, and storage path.
_validate_initial_allocations: [VALIDATION_ERROR] MUST require every section target to belong to intake.project_id and enforce exact allocation sum with no proportional or residual allocation.
_build_expense_aggregate: [FIELD_ASSIGNMENT] MUST create exactly one ExpenseDocument for the new Expense, keep binary content outside records behind intake.file_ref, and create one allocation per explicit instruction.
_classify_expense_replay: [RULE_REFERENCE] MUST return existing only for equal intake_fingerprint and otherwise raise ExpenseConflictError without mutation according to = rules.idempotency_identities.
correct_expense: [ORCHESTRATION] MUST validate EUR total and explicit project-scoped allocations, then atomically replace editable expense fields and all allocations plus one expense.correct audit; no intermediate invalid sum may commit.
set_expense_inclusion: [ORCHESTRATION] MUST change only included and updated_at on the project-scoped Expense and append exactly expense.include or expense.exclude atomically.
replace_expense_allocations: [ORCHESTRATION] MUST replace all allocations with explicit operator instructions whose sum equals the unchanged total_amount and append expense.allocate atomically.
update_expense_document: [ORCHESTRATION] MUST change only description, client_visible, and updated_at on the project-scoped document and append document.update atomically; file_ref is unchanged.
read_expense_document: [SECURITY_BOUNDARY] MUST authorize the document project and client_visible rule for the actor context before constructing AuthorizedBinaryReference and calling read_binary.
_validate_allocation_sum: [VALIDATION_ERROR] MUST require the quantized sum of instruction amounts to equal total_amount exactly and reject empty/residual/proportional repair.
_build_replacement_allocations: [FORBIDDEN_ACTION] MUST create exactly one allocation per instruction with supplied amount/target, expense project provenance, actor_id, and changed_at; MUST NOT proportion, split, or invent a remainder.
_authorize_document_reference: [SECURITY_BOUNDARY] MUST require document and expense project_id to equal context.project_id and client visibility for viewer context, then return the sole trusted file_ref carrier.
```

### Tracking, photos, financial policy, and derived views

```text
set_section_progress: [BEHAVIOR] MUST validate the project section and integer range 0..100, upsert the manual value, and append progress.update atomically; photographs MUST NOT alter it.
register_work_payment: [RULE_REFERENCE] MUST enforce EUR/R9 and = rules.idempotency_identities; equal payment_id/content returns existing, conflict changes nothing, and a new payment plus payment.register audit commits atomically without creating an invoice/accounting posting.
list_project_progress: [SECURITY_BOUNDARY] MUST return every persisted progress record for context.project_id only in active-budget plan order, with stable section_id ties.
list_project_progress: [RETURN_SHAPE] MUST return all and only SectionProgress records whose project_id equals context.project_id; an empty list means no recorded progress.
list_project_payments: [SECURITY_BOUNDARY] MUST return every payment for context.project_id only ordered by payment_date descending then payment_id descending.
list_project_payments: [DETERMINISM_OR_ORDERING] MUST return all and only project payments in `(payment_date, payment_id)` descending order; an empty list means no recorded payments.
_validate_completion_percent: [VALIDATION_ERROR] MUST reject bool, non-integer, negative, and greater-than-100 values rather than clamp.
_classify_payment_replay: [RULE_REFERENCE] MUST return existing only when amount, payment_date, and description all match; otherwise raise TrackingConflictError without mutation per = rules.idempotency_identities.
publish_progress_photo: [ORCHESTRATION] MUST apply intake_id replay, validate optional section project scope, persist one file_ref-backed photo, and append photo.publish atomically; it MUST NOT set progress or financial values.
update_progress_photo: [ORCHESTRATION] MUST validate optional section project scope, change only caption/section/client_visible/updated_at, and append photo.update atomically without changing file_ref, progress, or finance.
list_progress_photos: [SECURITY_BOUNDARY] MUST return project-scoped photos only, exclude non-client-visible items for viewer context, and order chronologically by photo_date then photo_id.
list_progress_photos: [DETERMINISM_OR_ORDERING] MUST return all eligible ProgressPhoto records in `(photo_date, photo_id)` ascending order; an empty list means no eligible photos.
read_progress_photo: [SECURITY_BOUNDARY] MUST authorize photo project and client_visible rule before constructing AuthorizedBinaryReference and calling read_binary.
_classify_photo_replay: [RULE_REFERENCE] MUST return existing only when the same intake_id publication content agrees; conflict raises PhotoConflictError without mutation according to = rules.idempotency_identities.
_authorize_photo_reference: [SECURITY_BOUNDARY] MUST require photo.project_id equals context.project_id and client visibility for viewer context, then return the sole trusted file_ref carrier.
_ordered_photos: [DETERMINISM_OR_ORDERING] MUST return every input photo exactly once ordered by photo_date ascending then photo_id ascending.
_photo_mutation_result: [FIELD_PROJECTION] MUST copy photo_id, client_visible, updated_at and set replayed exactly from the argument; it MUST omit file_ref.
validate_eur_amount: [RULE_REFERENCE] MUST enforce = rules.money_policy, reject non-EUR and invalid sign, and return ROUND_HALF_UP two-digit Decimal without currency conversion.
calculate_completed_work: [RULE_REFERENCE] MUST compute the per-section rounded result from = rules.money_policy and MUST NOT use float arithmetic.
calculate_overall_progress: [RULE_REFERENCE] MUST use the weighted R9 formula over positive work_planned and return None when its denominator is zero; MUST NOT use arithmetic mean or fabricate zero.
calculate_material_balance: [BEHAVIOR] MUST return quantized material_planned minus material_actual, preserving a negative overspend result without clamping.
calculate_work_balance: [RULE_REFERENCE] MUST return quantized completed_work_total minus payments_total and the closed sign-derived WorkBalanceLabel from = rules.money_policy.
_quantize_money: [RULE_REFERENCE] MUST round Decimal to two fraction digits with ROUND_HALF_UP according to = rules.money_policy and MUST NOT convert through float.
list_viewer_projects: [ORCHESTRATION] MUST resolve only active persisted grants for actor.viewer_id, fetch each live Registry context server-side, omit no accessible item silently, and order display_name.casefold() then project_id per = rules.project_list_ordering without changing display_name.
build_project_overview: [RETURN_SHAPE] MUST independently derive all five availability/value pairs from owning records and live project context; available values are populated, unavailable values are None, and failures MUST NOT fabricate zeros.
build_project_overview: [FIELD_ASSIGNMENT] MUST assign budget_availability, expenses_availability, progress_availability, payments_availability, and photos_availability with each corresponding value field.
build_budget_view: [PROVENANCE] MUST derive all section and total fields at read time from the selected/active BudgetVersion, plans, included expenses, and progress; it MUST NOT persist totals.
build_budget_view: [RETURN_SHAPE] MUST populate version_id, sections, material_planned_total, material_actual_total, work_planned_total, completed_work_total, other_expenses_total, and unresolved_allocation_count.
build_expense_view: [RETURN_SHAPE] MUST include every confirmed project expense, keep excluded expenses visible, derive included/excluded/other totals at read time, omit file_ref, and apply documented expense/allocation ordering.
build_progress_view: [RETURN_SHAPE] MUST project active-budget sections, manual completion values, per-section completed work, total, and weighted overall progress; missing progress remains None and is not zero-filled.
build_progress_view: [FIELD_ASSIGNMENT] MUST populate sections, completed_work_total, and overall_progress_percent; a zero R9 denominator assigns overall_progress_percent=None.
build_payment_view: [RETURN_SHAPE] MUST project every payment in stable descending order and derive payments_total plus WorkBalanceResult at read time.
_project_budget_sections: [FIELD_PROJECTION] MUST emit one BudgetSectionView per plan with stable section identity/name/order, included material actuals, unclamped remaining, progress, completed work, and unresolved flag.
_project_expense_summary: [BEHAVIOR] MUST include only included=true amounts in included_total/other_expenses_total, keep excluded expenses in result.expenses and excluded_total, and never persist totals.
_project_progress: [FIELD_PROJECTION] MUST emit sections in detail plan order, preserve absent progress as None, and derive completed_work_total and weighted overall_progress_percent through financial_policy.
_project_payments: [FIELD_PROJECTION] MUST project every payment, derive payments_total, preserve completed_work_total, and use calculate_work_balance for balance/label.
_project_photos: [FIELD_PROJECTION] MUST project client-visible photo fields and section display names in chronological order and MUST omit file_ref.
_ordered_project_items: [DETERMINISM_OR_ORDERING] MUST return every item exactly once ordered by display_name.casefold() ascending without changing display_name, then project_id ascending as the stable tie.
append_audit: [ORCHESTRATION] MUST validate the closed catalog intent and insert exactly one immutable AuditRecord into the caller's open transaction; service actors MUST retain key_version and no secret/file_ref may enter details.
_validate_audit_intent: [RULE_REFERENCE] MUST reject action/result/reason combinations outside = rules.audit_action_catalog, including rejected significant mutations without a closed reason_code.
_build_audit_record: [FIELD_PROJECTION] MUST copy actor kind/id/key_version, action, result, reason, project/entity provenance and assign occurred_at without session token, secret, hash, or file_ref.
```

### `portal_store`

Module-wide rules below are intentionally load-bearing and apply to every
method, while each contract also has an exact operation note.

```text
portal_store: [SCHEMA_CONSTRAINT] Every get/list/insert/update method MUST serialize exactly its declared model type; get returns None only when the complete declared identity/scope has no match, list returns all matches, and no method returns raw rows or ORM objects.
portal_store: [SECURITY_BOUNDARY] Query methods MUST use every identity/scope argument in the predicate; stored password/token/secret hashes and file_ref never appear in logs, error text, or generic projections.
portal_store: [VALIDATION_ERROR] Duplicate insert, missing update target, constraint violation, driver failure, and use after close MUST translate to PersistenceError without leaking SQL or driver detail.
PortalStore.__init__: [CONFIG_REFERENCE] MUST bind only the supplied database_url, configure no global mutable store, and retain no credentials in loggable representation.
PortalStore.begin: [RETURN_SHAPE] MUST return a new open PortalTransaction with independent commit/rollback state; it MUST NOT share an active transaction implicitly.
PortalTransaction.commit: [ORCHESTRATION] MUST atomically persist the complete write set or none, enforce at most one active viewer and producer grant per respective pair, preserve exact expense allocation sums and section reference restrictions, and forbid update/delete of AuditRecord, SnapshotImportRecord, and ApprovedEstimateSnapshot.
PortalTransaction.rollback: [ORCHESTRATION] MUST discard the complete uncommitted write set and close the transaction without emitting audit, delivery, Registry, or storage I/O.
PortalTransaction.get_staff_by_email: [RETURN_SHAPE] MUST select by the complete normalized_email unique key and return its StaffAccount or None.
PortalTransaction.get_staff: [RETURN_SHAPE] MUST select only staff_id and return its StaffAccount or None.
PortalTransaction.get_staff_session: [RETURN_SHAPE] MUST select only session_id and return its StaffSession or None.
PortalTransaction.list_staff_sessions: [RETURN_SHAPE] MUST return all StaffSession records for staff_id in created_at then session_id order.
PortalTransaction.get_staff_assignment: [RETURN_SHAPE] MUST select the staff_id/project_id pair and return its StaffProjectAssignment or None.
PortalTransaction.get_staff_assignment_by_id: [RETURN_SHAPE] MUST select only assignment_id and return its StaffProjectAssignment or None.
PortalTransaction.insert_staff_account: [SCHEMA_CONSTRAINT] MUST insert exactly account and reject duplicate staff_id or normalized email.
PortalTransaction.update_staff_account: [SCHEMA_CONSTRAINT] MUST replace exactly the existing account with matching staff_id and preserve normalized-email uniqueness.
PortalTransaction.insert_staff_session: [SCHEMA_CONSTRAINT] MUST insert exactly session and reject duplicate session_id; token plaintext is never accepted.
PortalTransaction.update_staff_sessions: [SCHEMA_CONSTRAINT] MUST update every supplied session by session_id in the current transaction or fail the whole batch.
PortalTransaction.insert_staff_assignment: [SCHEMA_CONSTRAINT] MUST insert exactly assignment and reject duplicate assignment_id or active staff/project pair.
PortalTransaction.update_staff_assignment: [SCHEMA_CONSTRAINT] MUST update exactly the record matching assignment_id and never create on missing.
PortalTransaction.list_email_verifications: [RETURN_SHAPE] MUST return all EmailVerificationChallenge records for staff_id ordered by issued_at then challenge_id.
PortalTransaction.get_email_verification: [RETURN_SHAPE] MUST select only challenge_id and return its EmailVerificationChallenge or None.
PortalTransaction.list_email_changes: [RETURN_SHAPE] MUST return all PendingEmailChange records for staff_id ordered by issued_at then change_id.
PortalTransaction.get_email_change: [RETURN_SHAPE] MUST select only change_id and return its PendingEmailChange or None.
PortalTransaction.list_password_resets: [RETURN_SHAPE] MUST return all PasswordResetToken records for staff_id ordered by issued_at then token_id.
PortalTransaction.get_password_reset: [RETURN_SHAPE] MUST select only token_id and return its PasswordResetToken or None.
PortalTransaction.insert_email_verification: [SCHEMA_CONSTRAINT] MUST insert exactly challenge and reject duplicate challenge_id; plaintext is never accepted.
PortalTransaction.update_email_verifications: [SCHEMA_CONSTRAINT] MUST update every supplied challenge by challenge_id atomically and never create on missing.
PortalTransaction.insert_email_change: [SCHEMA_CONSTRAINT] MUST insert exactly change and reject duplicate change_id; plaintext is never accepted.
PortalTransaction.update_email_changes: [SCHEMA_CONSTRAINT] MUST update every supplied change by change_id atomically and never create on missing.
PortalTransaction.insert_password_reset: [SCHEMA_CONSTRAINT] MUST insert exactly token and reject duplicate token_id; plaintext is never accepted.
PortalTransaction.update_password_resets: [SCHEMA_CONSTRAINT] MUST update every supplied token by token_id atomically and never create on missing.
PortalTransaction.get_email_delivery: [RETURN_SHAPE] MUST select only delivery_id and return its EmailDeliveryRecord or None.
PortalTransaction.insert_email_delivery: [SCHEMA_CONSTRAINT] MUST insert exactly record and reject duplicate delivery_id.
PortalTransaction.update_email_delivery: [SCHEMA_CONSTRAINT] MUST update exactly the record matching delivery_id and never create on missing.
PortalTransaction.get_viewer: [RETURN_SHAPE] MUST select only viewer_id and return its ClientViewer or None.
PortalTransaction.get_viewer_credential: [RETURN_SHAPE] MUST select only credential_id and return its ViewerAccessCredential or None.
PortalTransaction.get_viewer_session: [RETURN_SHAPE] MUST select only session_id and return its ViewerSession or None.
PortalTransaction.list_viewer_sessions: [RETURN_SHAPE] MUST return all ViewerSession records for viewer_id ordered by created_at then session_id.
PortalTransaction.list_viewer_credentials: [RETURN_SHAPE] MUST return all ViewerAccessCredential records for viewer_id ordered by created_at then credential_id.
PortalTransaction.get_viewer_grant: [RETURN_SHAPE] MUST select the viewer_id/project_id pair and return its ProjectViewerGrant or None.
PortalTransaction.get_viewer_grant_by_id: [RETURN_SHAPE] MUST select only grant_id and return its ProjectViewerGrant or None.
PortalTransaction.list_viewer_grants: [RETURN_SHAPE] MUST return all ProjectViewerGrant records for viewer_id ordered by created_at then grant_id.
PortalTransaction.insert_viewer: [SCHEMA_CONSTRAINT] MUST insert exactly viewer and reject duplicate viewer_id.
PortalTransaction.update_viewer: [SCHEMA_CONSTRAINT] MUST update exactly the record matching viewer_id and never create on missing.
PortalTransaction.insert_viewer_credential: [SCHEMA_CONSTRAINT] MUST insert exactly credential, reject duplicate credential_id, and accept no plaintext secret.
PortalTransaction.update_viewer_credentials: [SCHEMA_CONSTRAINT] MUST update every supplied credential by credential_id atomically and enforce at most one non-revoked credential per viewer.
PortalTransaction.insert_viewer_session: [SCHEMA_CONSTRAINT] MUST insert exactly session, reject duplicate session_id, and accept no plaintext token.
PortalTransaction.update_viewer_sessions: [SCHEMA_CONSTRAINT] MUST update every supplied session by session_id atomically and never create on missing.
PortalTransaction.insert_viewer_grant: [SCHEMA_CONSTRAINT] MUST insert exactly grant and reject duplicate grant_id or active viewer/project pair.
PortalTransaction.update_viewer_grant: [SCHEMA_CONSTRAINT] MUST update exactly the record matching grant_id and never create on missing.
PortalTransaction.get_service_principal: [RETURN_SHAPE] MUST select only principal_id and return its ServicePrincipal or None.
PortalTransaction.get_service_credential: [RETURN_SHAPE] MUST select only credential_id and return its ServiceCredential or None.
PortalTransaction.list_service_credentials: [RETURN_SHAPE] MUST return all ServiceCredential records for principal_id ordered by key_version then credential_id.
PortalTransaction.get_producer_grant: [RETURN_SHAPE] MUST select the principal_id/project_id pair and return its ProducerProjectGrant or None.
PortalTransaction.get_producer_grant_by_id: [RETURN_SHAPE] MUST select only grant_id and return its ProducerProjectGrant or None.
PortalTransaction.insert_service_principal: [SCHEMA_CONSTRAINT] MUST insert exactly principal and reject duplicate service_principal_id.
PortalTransaction.update_service_principal: [SCHEMA_CONSTRAINT] MUST update exactly the record matching service_principal_id and never create on missing.
PortalTransaction.insert_service_credential: [SCHEMA_CONSTRAINT] MUST insert exactly credential, reject duplicate credential_id or principal/key_version, and accept no plaintext secret.
PortalTransaction.update_service_credential: [SCHEMA_CONSTRAINT] MUST update exactly the record matching credential_id and never create on missing.
PortalTransaction.insert_producer_grant: [SCHEMA_CONSTRAINT] MUST insert exactly grant and reject duplicate grant_id or active principal/project pair.
PortalTransaction.update_producer_grant: [SCHEMA_CONSTRAINT] MUST update exactly the record matching grant_id and never create on missing.
PortalTransaction.get_snapshot_by_identity: [RETURN_SHAPE] MUST select the complete project_id/estimate_id/estimate_version identity and return its immutable ApprovedEstimateSnapshot or None.
PortalTransaction.get_snapshot_import: [RETURN_SHAPE] MUST select only import_id and return its immutable SnapshotImportRecord or None.
PortalTransaction.insert_snapshot: [SCHEMA_CONSTRAINT] MUST append exactly snapshot and reject duplicate snapshot_id or publication identity; no update/delete operation exists.
PortalTransaction.insert_snapshot_import: [SCHEMA_CONSTRAINT] MUST append exactly record and reject duplicate import_id; no update/delete operation exists.
PortalTransaction.get_budget_version: [RETURN_SHAPE] MUST select only version_id and return its BudgetVersion or None.
PortalTransaction.get_active_budget_version: [RETURN_SHAPE] MUST return the sole active BudgetVersion for project_id or None and raise PersistenceError if stored state violates uniqueness.
PortalTransaction.get_manual_budget_version: [RETURN_SHAPE] MUST return the sole manual BudgetVersion for project_id or None and raise PersistenceError if stored state violates uniqueness.
PortalTransaction.list_budget_plans: [RETURN_SHAPE] MUST return every SectionPlan for version_id ordered by sort_order then section_id.
PortalTransaction.list_project_sections: [RETURN_SHAPE] MUST return every PortalSection for project_id ordered by created_at then section_id.
PortalTransaction.get_project_section: [RETURN_SHAPE] MUST select the project_id/section_id pair and return its PortalSection or None.
PortalTransaction.insert_budget_version: [SCHEMA_CONSTRAINT] MUST insert exactly version and reject duplicate version_id, a second manual version, or a second active version for its project.
PortalTransaction.update_budget_versions: [SCHEMA_CONSTRAINT] MUST update every supplied version atomically and preserve at most one active version and one manual version per project.
PortalTransaction.insert_project_sections: [SCHEMA_CONSTRAINT] MUST insert every supplied section atomically and reject duplicate section_id or duplicate non-null project/source_key.
PortalTransaction.upsert_section_plan: [SCHEMA_CONSTRAINT] MUST replace only the manual plan matching version_id/section_id or insert it; imported plans are never updated.
PortalTransaction.insert_section_plans: [SCHEMA_CONSTRAINT] MUST insert every supplied imported plan atomically and reject duplicate version_id/section_id.
PortalTransaction.get_expense_aggregate: [RETURN_SHAPE] MUST select only expense_id and return the complete ExpenseAggregate or None.
PortalTransaction.get_expense_by_recognition_id: [RETURN_SHAPE] MUST select only recognized_document_id and return the complete unique ExpenseAggregate or None.
PortalTransaction.get_expense_document: [RETURN_SHAPE] MUST select only document_id and return its ExpenseDocument or None.
PortalTransaction.list_project_expenses: [RETURN_SHAPE] MUST return every ExpenseAggregate for project_id ordered by document_date descending then expense_id descending.
PortalTransaction.insert_expense_aggregate: [SCHEMA_CONSTRAINT] MUST atomically insert exactly one expense, its one document, and all allocations while enforcing unique recognized_document_id and exact allocation sum.
PortalTransaction.update_expense_aggregate: [SCHEMA_CONSTRAINT] MUST atomically replace the existing expense/document/allocation aggregate by expense_id and enforce exact allocation sum.
PortalTransaction.update_expense: [SCHEMA_CONSTRAINT] MUST update exactly the existing expense by expense_id without changing recognized_document_id or intake_fingerprint.
PortalTransaction.update_expense_document: [SCHEMA_CONSTRAINT] MUST update exactly the existing document by document_id without changing expense_id or file_ref.
PortalTransaction.get_section_progress: [RETURN_SHAPE] MUST select the project_id/section_id pair and return its SectionProgress or None.
PortalTransaction.list_project_progress: [RETURN_SHAPE] MUST return every SectionProgress for project_id ordered by section_id.
PortalTransaction.get_work_payment: [RETURN_SHAPE] MUST select only payment_id and return its WorkPayment or None.
PortalTransaction.list_project_payments: [RETURN_SHAPE] MUST return every WorkPayment for project_id ordered by payment_date descending then payment_id descending.
PortalTransaction.upsert_section_progress: [SCHEMA_CONSTRAINT] MUST replace only the project_id/section_id record or insert it and preserve integer 0..100.
PortalTransaction.insert_work_payment: [SCHEMA_CONSTRAINT] MUST insert exactly payment and reject duplicate payment_id.
PortalTransaction.get_progress_photo: [RETURN_SHAPE] MUST select only photo_id and return its ProgressPhoto or None.
PortalTransaction.get_progress_photo_by_intake_id: [RETURN_SHAPE] MUST select only intake_id and return its unique ProgressPhoto or None.
PortalTransaction.list_project_photos: [RETURN_SHAPE] MUST return every ProgressPhoto for project_id ordered by photo_date then photo_id.
PortalTransaction.insert_progress_photo: [SCHEMA_CONSTRAINT] MUST insert exactly photo and reject duplicate photo_id or intake_id.
PortalTransaction.update_progress_photo: [SCHEMA_CONSTRAINT] MUST update exactly the existing photo by photo_id without changing intake_id or file_ref.
PortalTransaction.insert_audit: [SCHEMA_CONSTRAINT] MUST append exactly record and reject duplicate audit_id; no update/delete operation exists.
PortalTransaction._translate_persistence_error: [VALIDATION_ERROR] MUST return PersistenceError without SQL, driver, URL, secret, hash, file_ref, or raw record data.
PortalTransaction._assert_open: [VALIDATION_ERROR] MUST raise PersistenceError after commit or rollback and before any query or mutation can observe/use the closed transaction.
```

### `api`

```text
api: [DEPENDENCY_BOUNDARY] HTTP methods MUST remain thin typed orchestration, never import PortalTransaction, implement policy, read Registry/storage directly, or construct trusted actor/project contexts from request claims.
api: [SECURITY_BOUNDARY] Persisted IAM records containing password_hash, token_hash, or secret_hash and records containing file_ref MUST NOT be returned; only declared safe DTO projections or BinaryPayload may cross HTTP.
create_app: [ORCHESTRATION] MUST construct FastAPI, instantiate PortalApi with store, register the exact declared routes once, and return that app without opening a transaction.
PortalApi.__init__: [FIELD_ASSIGNMENT] MUST retain exactly store as the application dependency and MUST NOT begin a transaction or copy credentials.
PortalApi.register_routes: [ORCHESTRATION] MUST bind every declared PortalApi public method to exactly one authenticated JSON or binary route and MUST NOT add endpoint-local business operations.
PortalApi.staff_login: [ORCHESTRATION] MUST delegate only to authenticate_staff and return its StaffSessionGrant; AuthenticationRejected maps to the uniform authentication response.
PortalApi.staff_logout: [ORCHESTRATION] MUST resolve session_token, delegate to sign_out_staff, and return no persisted StaffSession body.
PortalApi.confirm_staff_email: [ORCHESTRATION] MUST delegate token consumption to confirm_email_verification and return only _staff_account_view.
PortalApi.request_password_reset: [SECURITY_BOUNDARY] MUST delegate to request_password_reset and return the same no-content response for known and unknown email.
PortalApi.complete_password_reset: [ORCHESTRATION] MUST delegate to complete_password_reset and return only _staff_account_view.
PortalApi.request_email_change: [ORCHESTRATION] MUST resolve the staff session, delegate to request_email_change, and return its hash-free ChallengeIssueView.
PortalApi.issue_staff_email_verification: [ORCHESTRATION] MUST resolve/authorize the administrator, delegate issuance, and return its hash-free ChallengeIssueView.
PortalApi.confirm_email_change: [ORCHESTRATION] MUST delegate token consumption to confirm_email_change and return only _staff_account_view.
PortalApi.create_staff: [ORCHESTRATION] MUST resolve/authorize administrator, delegate creation, and return only _staff_account_view.
PortalApi.change_staff_status: [ORCHESTRATION] MUST resolve/authorize administrator, delegate the status transition, and return only _staff_account_view.
PortalApi.assign_staff_project: [ORCHESTRATION] MUST resolve/authorize administrator and delegate the complete Registry-linked assignment use case without accepting project context fields.
PortalApi.revoke_staff_assignment: [ORCHESTRATION] MUST resolve/authorize administrator and delegate revocation without probing assignment existence in the router.
PortalApi.revoke_staff_sessions: [ORCHESTRATION] MUST resolve/authorize administrator, delegate revocation, and return only _session_revocation_result.
PortalApi.create_viewer: [ORCHESTRATION] MUST resolve/authorize administrator, delegate creation, and return only _viewer_view.
PortalApi.revoke_viewer: [ORCHESTRATION] MUST resolve/authorize administrator, delegate revocation, and return only _viewer_view.
PortalApi.issue_viewer_credential: [SECURITY_BOUNDARY] MUST resolve/authorize administrator, delegate issuance, and return _viewer_credential_response with plaintext once and no secret_hash.
PortalApi.revoke_viewer_credential: [ORCHESTRATION] MUST resolve/authorize administrator, delegate revocation, and return no ViewerAccessCredential body.
PortalApi.grant_viewer_project: [ORCHESTRATION] MUST resolve/authorize administrator and delegate server-side Registry validation plus grant creation without client context.
PortalApi.revoke_viewer_project: [ORCHESTRATION] MUST resolve/authorize administrator and delegate revocation without probing grant existence in the router.
PortalApi.viewer_enter: [SECURITY_BOUNDARY] MUST delegate capability_secret authentication and return the issued session plaintext once without logging it.
PortalApi.list_viewer_projects: [ORCHESTRATION] MUST resolve viewer_session_token and delegate list_viewer_projects; it MUST NOT accept viewer_id, grant, sort, or Registry facts from the request.
PortalApi.viewer_project_overview: [ORCHESTRATION] MUST resolve the viewer session, authorize viewer project read, and delegate build_project_overview without weakening archived-read or visibility policy.
PortalApi.create_service_principal: [ORCHESTRATION] MUST resolve/authorize administrator, delegate creation, and return only _service_principal_view.
PortalApi.change_service_principal_status: [ORCHESTRATION] MUST resolve/authorize administrator, delegate transition, and return only _service_principal_view.
PortalApi.issue_service_credential: [SECURITY_BOUNDARY] MUST resolve/authorize administrator, delegate issuance, and return _service_credential_response with plaintext once and no secret_hash.
PortalApi.revoke_service_credential: [ORCHESTRATION] MUST resolve/authorize administrator, delegate revocation, and return no ServiceCredential body.
PortalApi.grant_producer_project: [ORCHESTRATION] MUST resolve/authorize administrator and delegate server-side Registry validation plus grant creation without client context.
PortalApi.revoke_producer_project: [ORCHESTRATION] MUST resolve/authorize administrator and delegate revocation without probing grant existence in the router.
PortalApi.publish_snapshot: [ORCHESTRATION] MUST authenticate service_secret, authorize producer scope before content validation, and delegate import_snapshot without opening or controlling its transaction.
PortalApi.get_snapshot_import: [ORCHESTRATION] MUST authenticate service_secret and delegate scoped immutable result lookup without accepting principal_id from the request.
PortalApi.ensure_manual_budget: [ORCHESTRATION] MUST resolve staff, authorize budget mutation for project_id, and delegate ensure_manual_budget without constructing context from claims.
PortalApi.upsert_manual_section_plan: [ORCHESTRATION] MUST resolve staff, authorize budget mutation, and delegate exact plan inputs; it MUST NOT compute totals or link sections by display name.
PortalApi.activate_budget_version: [ORCHESTRATION] MUST resolve staff, authorize budget activation, and delegate activation; no service credential contour reaches this method.
PortalApi.staff_project_overview: [ORCHESTRATION] MUST resolve staff, authorize project read, and delegate build_project_overview without computing component values.
PortalApi.create_expense_from_recognition: [ORCHESTRATION] MUST resolve staff, authorize expense mutation, delegate the typed publication/allocations, and return only _expense_mutation_result.
PortalApi.correct_expense: [ORCHESTRATION] MUST resolve staff, authorize expense mutation, delegate all correction fields atomically, and return only _expense_mutation_result.
PortalApi.set_expense_inclusion: [ORCHESTRATION] MUST resolve staff, authorize expense mutation, delegate inclusion, and return only _expense_mutation_result.
PortalApi.replace_expense_allocations: [ORCHESTRATION] MUST resolve staff, authorize expense mutation, delegate explicit allocations, and return only _expense_mutation_result.
PortalApi.update_expense_document: [ORCHESTRATION] MUST resolve staff, authorize document mutation, delegate metadata fields, and return only _document_mutation_result without file_ref.
PortalApi.staff_read_expense_document: [SECURITY_BOUNDARY] MUST resolve/authorize the staff contour then delegate read_expense_document and stream only BinaryPayload metadata/bytes.
PortalApi.viewer_read_expense_document: [SECURITY_BOUNDARY] MUST resolve/authorize the viewer contour then delegate read_expense_document, preserving client_visible enforcement and exposing no file_ref.
PortalApi.set_section_progress: [ORCHESTRATION] MUST resolve staff, authorize tracking mutation, and delegate the manual completion value without deriving it from photos.
PortalApi.register_work_payment: [ORCHESTRATION] MUST resolve staff, authorize tracking mutation, and delegate the idempotent payment without treating it as an invoice.
PortalApi.publish_progress_photo: [ORCHESTRATION] MUST resolve staff, authorize photo mutation, and delegate publication without reading file_ref or changing progress.
PortalApi.update_progress_photo: [ORCHESTRATION] MUST resolve staff, authorize photo mutation, and delegate only mutable photo metadata.
PortalApi.staff_read_progress_photo: [SECURITY_BOUNDARY] MUST resolve/authorize the staff contour then delegate read_progress_photo and stream only BinaryPayload metadata/bytes.
PortalApi.viewer_read_progress_photo: [SECURITY_BOUNDARY] MUST resolve/authorize the viewer contour then delegate read_progress_photo, preserving client_visible enforcement and exposing no file_ref.
PortalApi._staff_account_view: [FIELD_PROJECTION] MUST allow-list staff_id, email, email_verified, role, status, created_at, and updated_at exactly and MUST omit password_hash.
PortalApi._viewer_view: [FIELD_PROJECTION] MUST allow-list viewer_id, display_name, status, created_at, and revoked_at exactly and MUST omit credentials, grants, sessions, and hashes.
PortalApi._service_principal_view: [FIELD_PROJECTION] MUST allow-list service_principal_id, name, source_type, status, scope_mode, created_at, and disabled_at exactly and MUST omit credentials and hashes.
PortalApi._viewer_credential_response: [FIELD_PROJECTION] MUST copy credential_id, viewer_id, created_at and one-time issue.secret and MUST omit secret_hash, revoked_at, and internal record fields.
PortalApi._service_credential_response: [FIELD_PROJECTION] MUST copy credential_id, service_principal_id, key_version, created_at, expires_at and one-time issue.secret and MUST omit secret_hash and revoked_at.
PortalApi._expense_mutation_result: [FIELD_PROJECTION] MUST copy expense_id and document_id from aggregate and set replayed from the aggregate outcome without supplier, allocations, or file_ref.
PortalApi._document_mutation_result: [FIELD_PROJECTION] MUST copy document_id, client_visible, and updated_at and MUST omit expense_id and file_ref.
PortalApi._session_revocation_result: [FIELD_PROJECTION] MUST set staff_id, revoked_session_count to len(sessions), and revoked_at to the common revocation timestamp; an empty list MUST use the operation timestamp rather than fabricate session data.
```

## Properties draft

Each key is an exact contract name and each expression is total over valid
contract inputs. Ordering predicates compare `str(UUID)` so their execution
does not depend on a backend-specific UUID ordering implementation.

```json
{
  "_validate_reference_identity": [
    "result.project_id == requested_id"
  ],
  "_validate_context_identity": [
    "result.project.project_id == requested_id"
  ],
  "_context_from_validation": [
    "result.actor_kind == actor_kind and result.actor_id == actor_id and result.key_version == key_version and result.capability == capability and result.project_id == validation.project_id"
  ],
  "_find_unresolved_allocation_count": [
    "result == sum(1 for allocation in allocations if allocation.section_id != None and allocation.section_id not in active_section_ids)"
  ],
  "_ordered_plans": [
    "len(result) == len(plans)",
    "all(plan in result for plan in plans)",
    "all((result[i].sort_order, str(result[i].section_id)) <= (result[i + 1].sort_order, str(result[i + 1].section_id)) for i in range(len(result) - 1))"
  ],
  "_ordered_photos": [
    "len(result) == len(photos)",
    "all(photo in result for photo in photos)",
    "all((result[i].photo_date, str(result[i].photo_id)) <= (result[i + 1].photo_date, str(result[i + 1].photo_id)) for i in range(len(result) - 1))"
  ],
  "_photo_mutation_result": [
    "result.photo_id == photo.photo_id and result.replayed == replayed and result.client_visible == photo.client_visible and result.updated_at == photo.updated_at"
  ],
  "calculate_completed_work": [
    "completion_percent == 0 implies result == 0",
    "completion_percent == 100 implies result == work_planned"
  ],
  "calculate_overall_progress": [
    "sum(section.work_planned for section in sections) == 0 implies result == None",
    "sum(section.work_planned for section in sections) > 0 implies result != None"
  ],
  "calculate_material_balance": [
    "result == material_planned - material_actual"
  ],
  "calculate_work_balance": [
    "result.balance == completed_work_total - payments_total"
  ],
  "list_active_projects": [
    "all(item.status == 'active' for item in result)",
    "all(str(result[i].project_id) <= str(result[i + 1].project_id) for i in range(len(result) - 1))"
  ],
  "read_binary": [
    "result.content_length == len(result.content)"
  ],
  "PortalApi._staff_account_view": [
    "result.staff_id == account.staff_id and result.email == account.email and result.email_verified == account.email_verified and result.role == account.role and result.status == account.status and result.created_at == account.created_at and result.updated_at == account.updated_at"
  ],
  "PortalApi._viewer_view": [
    "result.viewer_id == viewer.viewer_id and result.display_name == viewer.display_name and result.status == viewer.status and result.created_at == viewer.created_at and result.revoked_at == viewer.revoked_at"
  ],
  "PortalApi._service_principal_view": [
    "result.service_principal_id == principal.service_principal_id and result.name == principal.name and result.source_type == principal.source_type and result.status == principal.status and result.scope_mode == principal.scope_mode and result.created_at == principal.created_at and result.disabled_at == principal.disabled_at"
  ],
  "PortalApi._viewer_credential_response": [
    "result.credential_id == issue.credential.credential_id and result.viewer_id == issue.credential.viewer_id and result.secret == issue.secret and result.created_at == issue.credential.created_at"
  ],
  "PortalApi._service_credential_response": [
    "result.credential_id == issue.credential.credential_id and result.service_principal_id == issue.credential.service_principal_id and result.key_version == issue.credential.key_version and result.secret == issue.secret and result.created_at == issue.credential.created_at and result.expires_at == issue.credential.expires_at"
  ],
  "PortalApi._expense_mutation_result": [
    "result.expense_id == aggregate.expense.expense_id and result.document_id == aggregate.document.document_id and result.replayed == aggregate.replayed"
  ],
  "PortalApi._document_mutation_result": [
    "result.document_id == document.document_id and result.client_visible == document.client_visible and result.updated_at == document.updated_at"
  ],
  "PortalApi._session_revocation_result": [
    "result.staff_id == staff_id and result.revoked_session_count == len(sessions)",
    "len(sessions) > 0 implies all(session.revoked_at == result.revoked_at for session in sessions)"
  ]
}
```

`calculate_material_balance` assumes the valid-input guarantee of R9: stored
amounts entering this pure function are already exact two-digit Decimals.
Consequently subtraction is already the quantized result; no hidden rounding
precondition is needed.

## Determinism draft

```json
{
  "issue_verification_secret": false,
  "_hash_secret": false,
  "_normalize_staff_email": true,
  "_validate_new_password": true,
  "_build_email_delivery_request": true,
  "_build_challenge_issue_view": true,
  "_credential_is_usable": true,
  "_require_capability": true,
  "_context_from_validation": true,
  "_registry_url": true,
  "_validate_reference_identity": true,
  "_validate_context_identity": true,
  "_validate_snapshot_publication": true,
  "_canonical_snapshot_fingerprint": true,
  "_classify_snapshot_replay": true,
  "_find_unresolved_allocation_count": true,
  "_ordered_plans": true,
  "_project_expense_intake": true,
  "_canonical_intake_fingerprint": true,
  "_classify_expense_replay": true,
  "_validate_allocation_sum": true,
  "_validate_completion_percent": true,
  "_classify_payment_replay": true,
  "_classify_photo_replay": true,
  "_ordered_photos": true,
  "_photo_mutation_result": true,
  "validate_eur_amount": true,
  "calculate_completed_work": true,
  "calculate_overall_progress": true,
  "calculate_material_balance": true,
  "calculate_work_balance": true,
  "_quantize_money": true,
  "_project_budget_sections": true,
  "_project_expense_summary": true,
  "_project_progress": true,
  "_project_payments": true,
  "_project_photos": true,
  "_ordered_project_items": true,
  "_validate_audit_intent": true,
  "PortalApi._staff_account_view": true,
  "PortalApi._viewer_view": true,
  "PortalApi._service_principal_view": true,
  "PortalApi._viewer_credential_response": true,
  "PortalApi._service_credential_response": true,
  "PortalApi._expense_mutation_result": true,
  "PortalApi._document_mutation_result": true,
  "PortalApi._session_revocation_result": true
}
```

## Invariant owner and primary landing map

The ledger is authoritative; this compact map makes the State 7 review
readable. `note` entries identify the exact note prefix/class above. Each
invariant has one primary landing only; supporting notes/properties do not
create a second landing.

| ID | Exact owner function | Primary landing |
| --- | --- | --- |
| INV-001 | `_authorize_project_operation` | note `[ORCHESTRATION]` |
| INV-002 | `_require_capability` | `rules.capability_catalog` |
| INV-003 | `issue_verification_secret` | note `[RULE_REFERENCE]` |
| INV-004 | `conceal_authentication_failure` | note `[SECURITY_BOUNDARY]` |
| INV-005 | `_authorize_project_operation` | `rules.revocation_cascades` |
| INV-006 | `_authorize_project_operation` | `rules.revocation_cascades` |
| INV-007 | `_require_capability` | `rules.principal_capability_sets` |
| INV-008 | `issue_viewer_access` | note `[ORCHESTRATION]` |
| INV-009 | `PortalTransaction.commit` | note `[ORCHESTRATION]` |
| INV-010 | `_issue_challenge` | `rules.email_challenge_policy` |
| INV-011 | `complete_password_reset` | note `[ORCHESTRATION]` |
| INV-012 | `confirm_email_change` | note `[ORCHESTRATION]` |
| INV-013 | `deliver_email_message` | note `[ORCHESTRATION]` |
| INV-014 | `authenticate_staff` | note `[SECURITY_BOUNDARY]` |
| INV-015 | `perform_recovery_override` | note `[SECURITY_BOUNDARY]` |
| INV-016 | `_issue_challenge` | `rules.email_challenge_policy` |
| INV-017 | `_require_staff_scope` | note `[SECURITY_BOUNDARY]` |
| INV-018 | `_normalize_staff_email` | `rules.staff_identity_input_policy` |
| INV-019 | `_validate_new_password` | `rules.staff_identity_input_policy` |
| PLAT-REG-001 | `validate_project_reference` | note `[PROVENANCE]` |
| PLAT-REG-002 | `_validate_reference_identity` | property `result.project_id == requested_id` |
| PLAT-REG-003 | `_authorize_project_operation` | note `[ORCHESTRATION]` |
| PLAT-REG-004 | `_authorize_project_operation` | note `[ORCHESTRATION]` |
| PLAT-REG-005 | `_translate_registry_failure` | note `[RULE_REFERENCE]` |
| PLAT-REG-006 | `get_project_context` | note `[PROVENANCE]` |
| PLAT-REG-007 | `create_viewer` | note `[PROVENANCE]` |
| INV-020 | `import_snapshot` | note `[ORCHESTRATION]` |
| INV-021 | `_classify_snapshot_replay` | `rules.idempotency_identities` |
| INV-022 | `activate_budget_version` | note `[ORCHESTRATION]` |
| INV-023 | `activate_budget_version` | note `[ORCHESTRATION]` |
| INV-024 | `upsert_manual_section_plan` | note `[ORCHESTRATION]` |
| INV-025 | `_link_snapshot_sections` | note `[RULE_REFERENCE]` |
| INV-026 | `import_snapshot` | note `[ORCHESTRATION]` |
| INV-027 | `build_budget_view` | note `[PROVENANCE]` |
| INV-028 | `PortalTransaction.commit` | note `[ORCHESTRATION]` |
| INV-029 | `authorize_snapshot_import` | note `[ORCHESTRATION]` |
| INV-030 | `create_expense_from_recognition` | note `[ORCHESTRATION]` |
| INV-031 | `_project_expense_intake` | note `[FIELD_PROJECTION]` |
| INV-032 | `PortalTransaction.commit` | note `[ORCHESTRATION]` |
| INV-033 | `_build_replacement_allocations` | note `[FORBIDDEN_ACTION]` |
| INV-034 | `_build_expense_aggregate` | note `[FIELD_ASSIGNMENT]` |
| INV-035 | `_project_expense_summary` | note `[BEHAVIOR]` |
| INV-036 | `validate_project_section` | note `[SECURITY_BOUNDARY]` |
| INV-037 | `validate_eur_amount` | `rules.money_policy` |
| INV-040 | `set_section_progress` | note `[BEHAVIOR]` |
| INV-041 | `calculate_overall_progress` | `rules.money_policy` |
| INV-042 | `register_work_payment` | note `[RULE_REFERENCE]` |
| INV-043 | `publish_progress_photo` | note `[ORCHESTRATION]` |
| INV-044 | `calculate_material_balance` | property `result == material_planned - material_actual` |
| INV-050 | `build_project_overview` | note `[RETURN_SHAPE]` |
| INV-051 | `append_audit` | note `[ORCHESTRATION]` |
| INV-052 | `PortalTransaction.commit` | note `[ORCHESTRATION]` |
| INV-053 | `append_audit` | note `[ORCHESTRATION]` |
| INV-054 | `list_active_projects` | property UUID ascending expression |
| INV-055 | `_ordered_project_items` | note `[DETERMINISM_OR_ORDERING]` |

## Placeholder-resistance review

- Exact contract prefixes in this document match all 319 signatures in
  `60_contracts.md`; module notes add constraints but are not used as a
  substitute for operation notes.
- Every reader states its source, scope, missing behavior, and ordering where
  observable. Every mutator states its atomic effect/audit boundary. Every
  builder states mandatory projections or provenance. Validators state the
  rejection condition rather than permitting an always-success result.
- `return None`, empty collections/models, constant success, blind forwarding,
  hash/file_ref leakage, partial commit, client-authoritative Registry data,
  proportional allocation, fabricated zeros, and endpoint-owned policy each
  contradict at least one exact note or property.
- Safe API projection helpers have both allow-list notes and pure equality
  properties. DTO schema absence remains the primary protection against hash
  and file_ref fields; the notes forbid reflection/generic serialization.
- UUID/random/clock creation and all I/O/transaction/exception requirements
  remain notes. Only total relations over arguments/result are properties.

## State 7 readiness assessment

Classified behavior, pure properties, determinism decisions, and one exact
owner/primary landing for every ledger invariant are stable. The confirmed
authentication/challenge defaults are ready for State 8 serialization.
